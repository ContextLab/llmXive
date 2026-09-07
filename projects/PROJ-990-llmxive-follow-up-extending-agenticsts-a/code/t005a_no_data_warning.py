import os
import logging
from pathlib import Path
import json
from datetime import datetime

def ensure_directories():
    """Ensure the processed data directory exists."""
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def write_warning_log(processed_dir: Path, message: str):
    """
    Write an error log entry to edge_case_warnings.log.
    
    Args:
        processed_dir: Path to the processed data directory.
        message: The error message to log.
    """
    log_file = processed_dir / "edge_case_warnings.log"
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = {
        "level": "ERROR",
        "message": message,
        "timestamp": timestamp
    }
    
    # Append as a single JSON line per entry
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logging.error(f"Logged warning to {log_file}: {message}")

def update_config_state(processed_dir: Path):
    """
    Update config_state.json to set PIPELINE_BLOCKED=true.
    
    Args:
        processed_dir: Path to the processed data directory.
    """
    config_file = processed_dir / "config_state.json"
    
    # Load existing state if it exists, otherwise start fresh
    state = {}
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read existing config_state.json: {e}. Starting fresh.")
    
    # Update the state
    state["PIPELINE_BLOCKED"] = True
    state["reason"] = "Real data missing; pipeline blocked."
    state["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # Write back
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    
    logging.info(f"Updated config_state.json at {config_file}")

def main():
    """
    Main entry point for T005a: Log Data Availability Status.
    
    Logic:
    1. Check if data/raw/agenticsts_trajectories.jsonl exists.
    2. Check if data/raw/original_static_logs.jsonl exists.
    3. If EITHER is missing:
       - Write an ERROR log to data/processed/edge_case_warnings.log.
       - Set PIPELINE_BLOCKED=true in data/processed/config_state.json.
    4. If BOTH exist:
       - Optionally log a success message (though task focuses on missing case).
       - Ensure PIPELINE_BLOCKED is not set to true (or set to false if it was).
    """
    # Setup basic logging if not already configured
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    raw_dir = Path("data/raw")
    processed_dir = ensure_directories()

    trajectory_file = raw_dir / "agenticsts_trajectories.jsonl"
    static_logs_file = raw_dir / "original_static_logs.jsonl"

    traj_exists = trajectory_file.exists()
    static_exists = static_logs_file.exists()

    if not traj_exists or not static_exists:
        missing_files = []
        if not traj_exists:
            missing_files.append(str(trajectory_file))
        if not static_exists:
            missing_files.append(str(static_logs_file))
        
        message = f"Real data missing; pipeline blocked. Missing files: {', '.join(missing_files)}"
        
        write_warning_log(processed_dir, message)
        update_config_state(processed_dir)
        
        logging.critical(message)
        # Do not exit with error code here, as this is a logging task.
        # The pipeline logic downstream should check PIPELINE_BLOCKED.
    else:
        logging.info("All required real data files are present.")
        # Ensure state reflects availability if we are updating it proactively
        # (Optional, based on strict task definition which emphasizes the missing case)
        config_file = processed_dir / "config_state.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                # If we are here, data is present, so we might want to unset the block
                # unless there are other reasons. For safety, we only set it to False
                # if it was explicitly True due to missing data.
                if state.get("PIPELINE_BLOCKED") and state.get("reason") == "Real data missing; pipeline blocked.":
                    state["PIPELINE_BLOCKED"] = False
                    state["reason"] = "Data available."
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                    logging.info("Cleared PIPELINE_BLOCKED flag in config_state.json.")
            except Exception as e:
                logging.warning(f"Could not update config_state.json: {e}")

if __name__ == "__main__":
    main()