# Life Sim Ultra

Life Sim Ultra is a local-only Generative Agents simulation. It retains the original Smallville map, Django frontend, associative-memory stream, retrieval, reflection, planning, and execution logic, while routing all generation through the locally installed Ollama model `qwen3:4b`.

The initial world has only three intentionally sparse personas: `Imouto-chan`, `Onee-chan`, and `Haha-hue`. Edit their placeholder instances in `config/npcs.json` and relationship placeholders in `config/dynamics.json`, then regenerate the base world before a new simulation.

## Setup

1. Ensure Ollama is running and `ollama list` includes `qwen3:4b`.
2. Create and activate a Python 3.10+ virtual environment, then run `pip install -r requirements.txt`.
3. Generate the clean base simulation with `python scripts/bootstrap_world.py --force`.

## Run

Use two terminals, as in the original project.

Terminal 1: `cd environment/frontend_server && python manage.py runserver`

Terminal 2: `cd reverie/backend_server && python reverie.py`

At the backend prompts, enter `base_life_sim_ultra` as the forked simulation and a new name such as `first-run` as the new simulation. Open `http://localhost:8000/simulator_home`, then use `run <step-count>` at the backend prompt.

## Model configuration

Defaults are local and require no API key: `OLLAMA_MODEL=qwen3:4b`, `OLLAMA_HOST=http://127.0.0.1:11434`, and `OLLAMA_TIMEOUT=180`. The adapter uses Ollama embeddings when supported and falls back to deterministic local hash embeddings so associative retrieval remains local.

## NPC data

`config/npcs.json` is valid JSON derived from the top-level NPC schema, and `config/dynamics.json` is a valid JSON subset derived from the Dynamics schema. They are deliberately simple placeholders for you to flesh out.
# Life_sim-_Ultra
