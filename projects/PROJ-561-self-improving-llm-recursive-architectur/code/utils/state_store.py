import os
import json
import time
from typing import Dict, Any, List, Optional
from config import get_config

_STATE_FILE_PATH: Optional[str] = None

def _get_state_path() -> str:
    """Lazy initialization of the state file path."""
    global _STATE_FILE_PATH
    if _STATE_FILE_PATH is None:
        cfg = get_config()
        _STATE_FILE_PATH = cfg.trajectory_path.replace("trajectory.json", "state.json")
        # Ensure the directory exists
        os.makedirs(os.path.dirname(_STATE_FILE_PATH), exist_ok=True)
    return _STATE_FILE_PATH

def load_state() -> Dict[str, Any]:
    """
    Load the persistent state from disk.
    If the file does not exist or is empty, returns a fresh default state.
    """
    path = _get_state_path()
    if not os.path.exists(path):
        return {
            "retry_counts": {},
            "modification_history": [],
            "degradation_flag": False,
            "degradation_cycle": None,
            "last_updated": None
        }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {
                    "retry_counts": {},
                    "modification_history": [],
                    "degradation_flag": False,
                    "degradation_cycle": None,
                    "last_updated": None
                }
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        # If corrupted, return fresh state to avoid crash, but log could be added
        return {
            "retry_counts": {},
            "modification_history": [],
            "degradation_flag": False,
            "degradation_cycle": None,
            "last_updated": None
        }

def save_state(state: Dict[str, Any]) -> None:
    """
    Persist the state to disk atomically (write to temp, then rename).
    """
    path = _get_state_path()
    temp_path = path + ".tmp"
    
    state["last_updated"] = time.time()
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    
    os.replace(temp_path, path)

def update_retry_count(mod_id: str, increment: int = 1) -> int:
    """
    Update the retry count for a specific modification ID.
    Returns the new retry count.
    """
    state = load_state()
    current = state.get("retry_counts", {}).get(mod_id, 0)
    new_count = current + increment
    
    if "retry_counts" not in state:
        state["retry_counts"] = {}
    state["retry_counts"][mod_id] = new_count
    
    save_state(state)
    return new_count

def get_retry_count(mod_id: str) -> int:
    """
    Get the current retry count for a modification ID.
    Returns 0 if not found.
    """
    state = load_state()
    return state.get("retry_counts", {}).get(mod_id, 0)

def update_mod_history(mod_id: str, modification_type: str, magnitude: float) -> None:
    """
    Append a new entry to the modification history.
    """
    state = load_state()
    if "modification_history" not in state:
        state["modification_history"] = []
    
    entry = {
        "mod_id": mod_id,
        "modification_type": modification_type,
        "magnitude": magnitude,
        "timestamp": time.time()
    }
    state["modification_history"].append(entry)
    save_state(state)

def get_modification_history() -> List[Dict[str, Any]]:
    """
    Retrieve the full modification history.
    """
    state = load_state()
    return state.get("modification_history", [])

def update_degradation_flag(is_degraded: bool, cycle_number: Optional[int] = None) -> None:
    """
    Update the global degradation flag and optionally record the cycle number.
    """
    state = load_state()
    state["degradation_flag"] = is_degraded
    if is_degraded and cycle_number is not None:
        state["degradation_cycle"] = cycle_number
    save_state(state)

def is_degradation_detected() -> bool:
    """
    Check if a degradation flag has been set.
    """
    state = load_state()
    return state.get("degradation_flag", False)

def get_degradation_cycle() -> Optional[int]:
    """
    Get the cycle number where degradation was detected.
    """
    state = load_state()
    return state.get("degradation_cycle")

def reset_state() -> None:
    """
    Clear all persistent state (useful for testing or restarting a run).
    """
    path = _get_state_path()
    if os.path.exists(path):
        os.remove(path)