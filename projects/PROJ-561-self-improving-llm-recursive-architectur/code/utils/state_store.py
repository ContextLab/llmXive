import os
import json
import time
from typing import Dict, Any, List, Optional
from config import get_config

STATE_FILE_RELATIVE = "results/state.json"

def _get_state_path() -> str:
    config = get_config()
    base = config.get("results_dir", "results")
    return os.path.join(base, "state.json")

def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def load_state() -> Dict[str, Any]:
    """
    Load state from results/state.json.
    Returns the default state schema if the file does not exist.
    Schema: {'cycle_number': int, 'retry_count': int, 'mod_history': list, 'degradation_flag': bool}
    """
    path = _get_state_path()
    if not os.path.exists(path):
        return {
            "cycle_number": 0,
            "retry_count": 0,
            "mod_history": [],
            "degradation_flag": False
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure schema completeness
        defaults = {
            "cycle_number": 0,
            "retry_count": 0,
            "mod_history": [],
            "degradation_flag": False
        }
        for key, val in defaults.items():
            if key not in data:
                data[key] = val
        return data
    except (json.JSONDecodeError, IOError):
        # Corrupt or unreadable file -> return fresh state
        return {
            "cycle_number": 0,
            "retry_count": 0,
            "mod_history": [],
            "degradation_flag": False
        }

def save_state(state: Dict[str, Any]) -> None:
    """
    Persist state to results/state.json.
    """
    path = _get_state_path()
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def update_retry_count(mod_id: str, increment: int = 1) -> int:
    """
    Update retry count for a specific modification ID.
    If mod_id is not in history, initialize it.
    Returns the new retry count.
    """
    state = load_state()
    history = state.get("mod_history", [])
    found = False
    for entry in history:
        if entry.get("mod_id") == mod_id:
            entry["retry_count"] = entry.get("retry_count", 0) + increment
            found = True
            break
    
    if not found:
        history.append({
            "mod_id": mod_id,
            "retry_count": increment,
            "timestamp": time.time()
        })
    
    state["mod_history"] = history
    # Global retry count (for the current cycle context)
    state["retry_count"] = state.get("retry_count", 0) + increment
    save_state(state)
    return state["retry_count"]

def get_retry_count(mod_id: Optional[str] = None) -> int:
    """
    Get retry count. If mod_id is provided, return count for that mod.
    Otherwise return global cycle retry count.
    """
    state = load_state()
    if mod_id:
        history = state.get("mod_history", [])
        for entry in history:
            if entry.get("mod_id") == mod_id:
                return entry.get("retry_count", 0)
        return 0
    return state.get("retry_count", 0)

def update_mod_history(mod_id: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Append or update a modification proposal in the history.
    """
    state = load_state()
    history = state.get("mod_history", [])
    
    # Check if exists
    exists = False
    for entry in history:
        if entry.get("mod_id") == mod_id:
            entry.update(details or {})
            entry["updated_at"] = time.time()
            exists = True
            break
    
    if not exists:
        new_entry = {
            "mod_id": mod_id,
            "created_at": time.time(),
            "details": details or {}
        }
        history.append(new_entry)
    
    state["mod_history"] = history
    save_state(state)

def get_modification_history() -> List[Dict[str, Any]]:
    """
    Return the full modification history.
    """
    state = load_state()
    return state.get("mod_history", [])

def update_degradation_flag(flag: bool, cycle_number: Optional[int] = None) -> None:
    """
    Update the global degradation flag and optionally record the cycle number.
    """
    state = load_state()
    state["degradation_flag"] = flag
    if cycle_number is not None:
        state["degradation_cycle"] = cycle_number
    save_state(state)

def is_degradation_detected() -> bool:
    """
    Check if degradation flag is set.
    """
    state = load_state()
    return state.get("degradation_flag", False)

def get_degradation_cycle() -> Optional[int]:
    """
    Get the cycle number where degradation was detected, if any.
    """
    state = load_state()
    return state.get("degradation_cycle")

def reset_state() -> None:
    """
    Reset state to defaults (useful for testing or starting fresh).
    """
    path = _get_state_path()
    if os.path.exists(path):
        os.remove(path)