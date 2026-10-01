"""Runtime paths for the local-only Life Sim Ultra backend."""
import os
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parents[1]
_FRONTEND_DIR = _PROJECT_ROOT / "environment" / "frontend_server"

maze_assets_loc = str(_FRONTEND_DIR / "static_dirs" / "assets")
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"
fs_storage = str(_FRONTEND_DIR / "storage")
fs_temp_storage = str(_FRONTEND_DIR / "temp_storage")
collision_block_id = "32125"
debug = os.environ.get("LIFE_SIM_DEBUG", "1") == "1"

