"""Local Ollama adapter used by the generative-agent prompt pipeline.

The public functions deliberately match the original OpenAI wrapper so the
planning, reflection, retrieval, and conversation code remains unchanged.
"""
import hashlib
import json
import math
import os
import re
import time

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "180"))


def temp_sleep(seconds=0.05):
  time.sleep(seconds)


def _ollama_chat(prompt, max_tokens=350):
  """Return clean text response from local Ollama model."""
  payload = {
    "model": OLLAMA_MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "stream": False,
    "options": {
      "temperature": 0.2,
      "num_predict": max_tokens,
    },
  }
  response = requests.post(
      f"{OLLAMA_HOST}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT)
  response.raise_for_status()
  data = response.json()
  msg = data.get("message", {})
  content = (msg.get("content") or "").strip()
  if not content and "thinking" in msg:
    content = msg["thinking"].strip()
  if "</think>" in content:
    content = content.rsplit("</think>", 1)[1]
  return re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()


def ChatGPT_single_request(prompt):
  return _ollama_chat(prompt)


def GPT4_request(prompt):
  return _ollama_chat(prompt)


def ChatGPT_request(prompt):
  return _ollama_chat(prompt)


def _json_output(text):
  """Parse either direct JSON or a JSON object wrapped in a Markdown fence."""
  text = text.strip()
  text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
  start, end = text.find("{"), text.rfind("}")
  if start < 0 or end < start:
    raise ValueError("Ollama response did not include a JSON object")
  obj = json.loads(text[start:end + 1])
  if isinstance(obj, dict):
    if "output" in obj:
      return obj["output"]
    if len(obj) == 1:
      return list(obj.values())[0]
  return obj


def _safe_json_response(prompt, example_output, special_instruction, repeat,
                        fail_safe_response, func_validate, func_clean_up,
                        verbose):
  wrapped = '"""\\n' + prompt + '\\n"""\\n'
  wrapped += "Output the response to the prompt above in JSON. " + special_instruction + "\\n"
  wrapped += 'Example output JSON:\\n{"output": ' + json.dumps(str(example_output)) + "}"
  if verbose:
    print("OLLAMA PROMPT\n", wrapped)
  for attempt in range(repeat):
    try:
      value = _json_output(_ollama_chat(wrapped))
      if func_validate(value, prompt=wrapped):
        return func_clean_up(value, prompt=wrapped)
    except (requests.RequestException, KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
      if verbose:
        print("Ollama attempt", attempt + 1, "failed:", error)
  return fail_safe_response


def GPT4_safe_generate_response(prompt, example_output, special_instruction,
                                repeat=3, fail_safe_response="error",
                                func_validate=None, func_clean_up=None,
                                verbose=False):
  return _safe_json_response(prompt, example_output, special_instruction, repeat,
                             fail_safe_response, func_validate, func_clean_up, verbose)


def ChatGPT_safe_generate_response(prompt, example_output, special_instruction,
                                   repeat=3, fail_safe_response="error",
                                   func_validate=None, func_clean_up=None,
                                   verbose=False):
  return _safe_json_response(prompt, example_output, special_instruction, repeat,
                             fail_safe_response, func_validate, func_clean_up, verbose)


def ChatGPT_safe_generate_response_OLD(prompt, repeat=3, fail_safe_response="error",
                                       func_validate=None, func_clean_up=None,
                                       verbose=False):
  for attempt in range(repeat):
    try:
      value = _ollama_chat(prompt)
      if func_validate(value, prompt=prompt):
        return func_clean_up(value, prompt=prompt)
    except (requests.RequestException, KeyError, ValueError, TypeError) as error:
      if verbose:
        print("Ollama attempt", attempt + 1, "failed:", error)
  return fail_safe_response


def GPT_request(prompt, gpt_parameter):
  return _ollama_chat(prompt)


def generate_prompt(curr_input, prompt_lib_file):
  if isinstance(curr_input, str):
    curr_input = [curr_input]
  prompt = open(prompt_lib_file, "r").read()
  for count, value in enumerate(curr_input):
    prompt = prompt.replace(f"!<INPUT {count}>!", str(value))
  if "<commentblockmarker>###</commentblockmarker>" in prompt:
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>", 1)[1]
  return prompt.strip()


def safe_generate_response(prompt, gpt_parameter, repeat=5, fail_safe_response="error",
                           func_validate=None, func_clean_up=None, verbose=False):
  return ChatGPT_safe_generate_response_OLD(
      prompt, repeat, fail_safe_response, func_validate, func_clean_up, verbose)


def _hashed_embedding(text, dimensions=256):
  """Deterministic local fallback when this Ollama build lacks embeddings."""
  vector = [0.0] * dimensions
  for token in re.findall(r"[\\w']+", text.lower()):
    index = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % dimensions
    vector[index] += 1.0
  norm = math.sqrt(sum(value * value for value in vector)) or 1.0
  return [value / norm for value in vector]


def get_embedding(text, model=None):
  text = (text or "this is blank").replace("\n", " ")
  try:
    response = requests.post(f"{OLLAMA_HOST}/api/embed", json={
        "model": model or OLLAMA_MODEL, "input": text}, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()
    embeddings = response.json().get("embeddings")
    if embeddings and embeddings[0]:
      return embeddings[0]
  except (requests.RequestException, ValueError, KeyError):
    pass
  return _hashed_embedding(text)
