import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
CODE_ROOT = PROJECT_ROOT / "code"

# Solvent List
DEFAULT_SOLVENTS = ["acetonitrile", "chloroform", "dichloromethane", "dcm"]

# Simulated Mode Flag
SIMULATED_MODE_FLAG = False

def get_path(*args) -> Path:
    """Get path relative to project root."""
    return PROJECT_ROOT / Path(*args)

def get_data_path(*args) -> Path:
    """Get path relative to data root."""
    return DATA_ROOT / Path(*args)

def get_code_path(*args) -> Path:
    """Get path relative to code root."""
    return CODE_ROOT / Path(*args)

def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If numpy/pandas are used, set their seeds too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_solvent_list() -> List[str]:
    """Return the list of allowed solvents."""
    return DEFAULT_SOLVENTS.copy()

def is_simulated_mode() -> bool:
    """Check if the project is running in simulated data mode."""
    state_file = get_data_path("simulated/state.json")
    if state_file.exists():
        import json
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            return state.get("SIMULATED_MODE", False)
        except Exception:
            return False
    return SIMULATED_MODE_FLAG

def set_simulated_mode(mode: bool):
    """Set the simulated mode flag."""
    global SIMULATED_MODE_FLAG
    SIMULATED_MODE_FLAG = mode
    # Persist to state file
    state_file = get_data_path("simulated/state.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(state_file, 'w') as f:
        json.dump({"SIMULATED_MODE": mode}, f)
