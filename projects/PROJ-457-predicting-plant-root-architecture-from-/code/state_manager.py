import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import get_config, setup_logging


def initialize_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Initialize the state file with an empty structure if it does not exist.
    If it exists, load it and return the content.
    """
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        initial_state = {
            "project_id": "PROJ-457-predicting-plant-root-architecture-from-",
            "p_n_available": None,
            "deviations": [],
            "metrics": {},
            "last_updated": None
        }
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(initial_state, f, indent=2)
        logging.info(f"Initialized state file at {state_path}")
        return initial_state
    else:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        logging.info(f"Loaded existing state file from {state_path}")
        return state


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the state file from disk.
    Raises FileNotFoundError if the file does not exist.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found at {state_path}. Initialize first.")
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_state_flag(state_path: Path, flag_name: str, value: Any) -> Dict[str, Any]:
    """
    Update a specific flag in the state file and write it back to disk.
    Returns the updated state dictionary.
    """
    state = load_state(state_path)
    state[flag_name] = value
    state["last_updated"] = str(Path(state_path).parent.name) + "_updated" # Simple timestamp placeholder or use datetime
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    logging.info(f"Updated state flag '{flag_name}' to {value} in {state_path}")
    return state


def main():
    """
    Entry point for T014b: Update State File.
    Reads the p_n_available flag (expected to be set by T014 logic in memory or args)
    and writes it to artifacts/state.json.
    
    For this specific task implementation, we assume the caller (T014) has determined
    the value. In a real pipeline, this function would be called with the determined value.
    Since T014 is the prerequisite and likely runs in the same process or passes the value,
    we implement the writer logic here.
    
    However, to make this script runnable as a standalone task (T014b) as requested,
    it needs to know the value. In the context of the pipeline described:
    T014 checks the data -> T014b writes the result.
    
    We will assume T014 writes the value to a temporary file or we check the data_ingestion
    result if available. But strictly, T014b's job is the write.
    
    To satisfy the "runnable" constraint for T014b specifically, we will:
    1. Check if artifacts/state.json exists.
    2. If not, initialize it.
    3. We need the value. Since T014 is the prerequisite, we will assume the value
       is passed via environment variable or a temporary file created by T014.
       Let's use a temporary file approach for robustness in the pipeline.
       T014 writes to data/tmp/p_n_check.json, T014b reads it and updates state.
    """
    config = get_config()
    logger = setup_logging()
    
    state_path = config.get("STATE_PATH", Path("artifacts/state.json"))
    temp_check_path = Path("data/tmp/p_n_check.json")
    
    # Initialize if missing (T014a might have done this, but idempotent is good)
    if not state_path.exists():
        initialize_state_file(state_path)
    
    # Determine p_n_available value
    p_n_available = None
    
    if temp_check_path.exists():
        try:
            with open(temp_check_path, 'r', encoding='utf-8') as f:
                temp_data = json.load(f)
            p_n_available = temp_data.get("p_n_available")
            logger.info(f"Read p_n_available={p_n_available} from temp file")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not read p_n_available from temp file: {e}. Defaulting to False.")
            p_n_available = False
    else:
        # Fallback if T014 didn't write temp file (should not happen in correct flow)
        # We must fail loudly or default? The task says "Write the flag".
        # If we can't find the flag, we can't write it.
        logger.error("Temp file data/tmp/p_n_check.json not found. T014 prerequisite may not have run.")
        # In a real strict pipeline, we might raise. Here we assume the task context implies
        # we are running after T014. If T014 failed, this fails too.
        # Let's try to infer from data_ingestion if possible, but that's complex.
        # We will raise an error to indicate missing prerequisite data.
        raise FileNotFoundError("Prerequisite data file (data/tmp/p_n_check.json) not found. T014 must run first.")
    
    if p_n_available is None:
        raise ValueError("p_n_available value is None. Cannot update state with None.")
        
    update_state_flag(state_path, "p_n_available", p_n_available)
    logger.info("T014b completed: State file updated with p_n_available flag.")


if __name__ == "__main__":
    main()
