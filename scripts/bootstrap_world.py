#!/usr/bin/env python3
"""Create the clean three-persona base simulation from config/npcs.json."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
STORAGE = ROOT / "environment" / "frontend_server" / "storage"
LOCATIONS = [(72, 14), (126, 46), (123, 57)]
SPATIAL_MEMORY = {
    "the Ville": {
        "Hobbs Cafe": {"cafe": ["cafe customer seating", "behind the cafe counter", "piano"]},
        "The Rose and Crown Pub": {"pub": ["bar customer seating", "behind the bar counter"]},
        "The Willows Market and Pharmacy": {"store": ["grocery store shelf", "pharmacy store counter"]},
        "Johnson Park": {"park": ["park garden"]},
        "Dorm for Oak Hill College": {"common room": ["common room sofa", "common room table"]}
    }
}

def relationship_context(npc_id, dynamics, names_by_id):
    lines = []
    for dynamic in dynamics:
        participants = dynamic["participants"]
        if npc_id not in participants:
            continue
        other = next(person for person in participants if person != npc_id)
        identity = dynamic.get("relationship_identity", {})
        communication = dynamic.get("communication", {})
        lines.append(
            f"Relationship with {names_by_id.get(other, other)}: {identity.get('relationship_label', 'unknown connection')}; "
            f"stage {identity.get('relationship_stage', 'unknown')}; communication openness {communication.get('openness', 'unspecified')}."
        )
    return " ".join(lines) or "No relationship dynamics are defined yet."

def dynamic_context(npc_id, dynamics, names_by_id):
    """Compact prompt context derived from the complete persisted dynamic objects."""
    contexts = []
    for dynamic in dynamics:
        if npc_id not in dynamic["participants"]:
            continue
        other_id = next(person for person in dynamic["participants"] if person != npc_id)
        identity = dynamic["relationship_identity"]
        trust = dynamic["trust_and_vulnerability"]
        communication = dynamic["communication"]
        boundaries = dynamic["boundaries"]
        contexts.append(
            f"{names_by_id.get(other_id, other_id)}: {identity['relationship_stage']} {identity['relationship_type']}; "
            f"trust={trust['mutual_trust']}; openness={communication['openness']}; "
            f"shared boundaries={', '.join(boundaries['mutually_accepted_boundaries'])}."
        )
    return "Relationship runtime context: " + " ".join(contexts)

def scratch(npc, dynamics, names_by_id, authored_profile):
    identity = npc["identity"]
    name = identity["name"]
    first, *rest = name.split()
    return {
        "vision_r": 8, "att_bandwidth": 8, "retention": 8, "curr_time": None, "curr_tile": None,
        "daily_plan_req": npc["goals"]["immediate"], "name": name, "first_name": first,
        "last_name": " ".join(rest), "age": identity["age"], "innate": npc["personality"],
        "learned": f"{npc['background']} Occupation: {npc['occupation']}. Values: {', '.join(npc['values'])}. "
                   + relationship_context(npc["id"], dynamics, names_by_id),
        "currently": f"{name} is {npc['world_state']['current_activity']}. Immediate goal: {npc['goals']['immediate']}",
        "lifestyle": f"{name} keeps a flexible placeholder schedule and sleeps around 11pm to 7am.",
        "living_area": npc["world_state"]["location"], "concept_forget": 100,
        "daily_reflection_time": 180, "daily_reflection_size": 5, "overlap_reflect_th": 4,
        "kw_strg_event_reflect_th": 10, "kw_strg_thought_reflect_th": 9, "recency_w": 1,
        "relevance_w": 1, "importance_w": 1, "recency_decay": 0.995,
        "importance_trigger_max": 150, "importance_trigger_curr": 150, "importance_ele_n": 0,
        "thought_count": 5, "daily_schedule_seed": npc["daily_schedule_seed"],
        "dynamic_context": dynamic_context(npc["id"], dynamics, names_by_id),
        "authored_profile": authored_profile,
        "daily_req": [], "f_daily_schedule": [], "f_daily_schedule_hourly_org": [],
        "act_address": None, "act_start_time": None, "act_duration": None, "act_description": None,
        "act_pronunciatio": None, "act_event": [name, None, None], "act_obj_description": None,
        "act_obj_pronunciatio": None, "act_obj_event": [None, None, None], "chatting_with": None,
        "chat": None, "chatting_with_buffer": {}, "chatting_end_time": None,
        "act_path_set": False, "planned_path": []
    }

def dump(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="base_life_sim_ultra")
    parser.add_argument("--force", action="store_true", help="replace only this generated base world")
    args = parser.parse_args()
    destination = STORAGE / args.name
    if destination.exists() and not args.force:
        raise SystemExit(f"{destination} already exists; choose --name or use --force.")
    if destination.exists():
        import shutil
        shutil.rmtree(destination)
    npcs = json.loads((CONFIG / "npcs.json").read_text(encoding="utf-8"))["npcs"]
    dynamics = json.loads((CONFIG / "dynamics.json").read_text(encoding="utf-8"))["dynamics"]
    if len(npcs) != 3:
        raise SystemExit("npcs.json must contain exactly three NPC placeholders for this base world.")
    names = [npc["identity"]["name"] for npc in npcs]
    names_by_id = {npc["id"]: npc["identity"]["name"] for npc in npcs}
    dump(destination / "reverie" / "meta.json", {
        "fork_sim_code": args.name, "start_date": "February 13, 2023",
        "curr_time": "February 13, 2023, 00:00:00", "sec_per_step": 10,
        "maze_name": "the_ville", "persona_names": names, "step": 0
    })
    dump(destination / "environment" / "0.json", {
        name: {"maze": "the_ville", "x": x, "y": y} for name, (x, y) in zip(names, LOCATIONS)
    })
    dump(destination / "reverie" / "dynamics.json", {"dynamics": dynamics})
    for npc in npcs:
        memory = destination / "personas" / npc["identity"]["name"] / "bootstrap_memory"
        profile_path = CONFIG / npc["profile_file"]
        authored_profile = profile_path.read_text(encoding="utf-8")
        dump(memory / "scratch.json", scratch(npc, dynamics, names_by_id, authored_profile))
        dump(memory / "spatial_memory.json", SPATIAL_MEMORY)
        dump(memory / "associative_memory" / "nodes.json", {})
        dump(memory / "associative_memory" / "embeddings.json", {})
        dump(memory / "associative_memory" / "kw_strength.json", {"kw_strength_event": {}, "kw_strength_thought": {}})
        (memory / "authored_profile.txt").write_text(authored_profile, encoding="utf-8")
    print(f"Created {destination.relative_to(ROOT)} with: {', '.join(names)}")

if __name__ == "__main__":
    main()
