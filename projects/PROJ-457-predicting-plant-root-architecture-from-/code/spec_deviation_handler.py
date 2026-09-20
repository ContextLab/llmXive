import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from config import get_config, setup_logging

def get_deviations_path() -> Path:
    """
    Returns the path to the deviations log file.
    Per project structure, deviations are logged in logs/deviation.log.
    """
    config = get_config()
    # Ensure the log directory exists
    log_dir = Path(config.get("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "deviation.log"

def load_deviations() -> List[Dict[str, Any]]:
    """
    Loads existing deviations from the deviation log.
    Since deviation.log is text, we read lines and parse them as JSON if possible.
    If the file is empty or doesn't exist, return an empty list.
    """
    path = get_deviations_path()
    if not path.exists():
        return []
    
    deviations = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    # Try to parse as JSON object (if stored as JSON lines)
                    deviations.append(json.loads(line))
                except json.JSONDecodeError:
                    # If it's plain text, store as a text entry
                    deviations.append({"raw_text": line, "type": "text"})
    return deviations

def save_deviations(deviations: List[Dict[str, Any]]) -> None:
    """
    Saves deviations back to the deviation log.
    Writes each deviation as a JSON line for structured logging.
    """
    path = get_deviations_path()
    with open(path, "w", encoding="utf-8") as f:
        for dev in deviations:
            if "raw_text" in dev:
                f.write(dev["raw_text"] + "\n")
            else:
                f.write(json.dumps(dev) + "\n")

def record_spec_deviation_fr002() -> None:
    """
    Records FR-002 deviation: ISRIC merge excluded.
    """
    entry = {
        "id": "FR-002",
        "description": "ISRIC merge excluded due to lack of verified source",
        "type": "spec_deviation",
        "status": "recorded"
    }
    deviations = load_deviations()
    # Check if already exists
    if not any(d.get("id") == "FR-002" for d in deviations):
        deviations.append(entry)
        save_deviations(deviations)
        logging.info("Recorded FR-002 deviation")

def record_spec_deviation_fr003() -> None:
    """
    Records FR-003 deviation: KNN imputation excluded to preserve statistical validity.
    """
    entry = {
        "id": "FR-003",
        "description": "KNN imputation excluded to preserve statistical validity; missing nutrients are excluded",
        "type": "spec_deviation",
        "status": "recorded"
    }
    deviations = load_deviations()
    # Check if already exists
    if not any(d.get("id") == "FR-003" for d in deviations):
        deviations.append(entry)
        save_deviations(deviations)
        logging.info("Recorded FR-003 deviation")

def main() -> None:
    """
    Main entry point for recording spec deviations.
    This script is intended to be run to ensure deviation logs are populated.
    """
    config = get_config()
    logger = setup_logging(config)
    
    logger.info("Starting spec deviation handler")
    
    # Record FR-002 (ISRIC exclusion)
    record_spec_deviation_fr002()
    
    # Record FR-003 (KNN exclusion)
    record_spec_deviation_fr003()
    
    logger.info("Spec deviation recording complete")

if __name__ == "__main__":
    main()
