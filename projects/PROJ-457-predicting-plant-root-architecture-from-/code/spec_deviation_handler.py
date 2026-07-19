import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from config import get_config, setup_logging

def get_deviations_path() -> Path:
    """Get the path to the deviations.json file."""
    config = get_config()
    base_path = config.get("PROJECT_ROOT", Path.cwd())
    return Path(base_path) / "artifacts" / "deviations.json"

def load_deviations() -> List[Dict[str, Any]]:
    """Load existing deviations from the JSON file."""
    path = get_deviations_path()
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Could not load deviations file: {e}. Starting fresh.")
        return []

def save_deviations(deviations: List[Dict[str, Any]]) -> None:
    """Save the deviations list back to the JSON file."""
    path = get_deviations_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(deviations, f, indent=2)

def record_spec_deviation_fr002() -> None:
    """Record the FR-002 spec deviation (ISRIC Merge Exclusion)."""
    deviation = {
        "fr_id": "FR-002",
        "deviation": "ISRIC merge excluded due to lack of verified source; proceeding with PlantPheno only.",
        "impact": "SC-001 metric redefined as P/N Availability Rate"
    }
    deviations = load_deviations()
    # Avoid duplicates
    if not any(d["fr_id"] == deviation["fr_id"] for d in deviations):
        deviations.append(deviation)
        save_deviations(deviations)
        logging.info(f"Recorded deviation FR-002: {deviation['deviation']}")
    else:
        logging.info("FR-002 deviation already recorded.")

def record_spec_deviation_fr003() -> None:
    """Record the FR-003 spec deviation (KNN Imputation Exclusion)."""
    deviation = {
        "fr_id": "FR-003",
        "deviation": "KNN imputation excluded to preserve statistical validity; missing nutrients are excluded.",
        "impact": "Data reduction, not imputation"
    }
    deviations = load_deviations()
    # Avoid duplicates
    if not any(d["fr_id"] == deviation["fr_id"] for d in deviations):
        deviations.append(deviation)
        save_deviations(deviations)
        logging.info(f"Recorded deviation FR-003: {deviation['deviation']}")
    else:
        logging.info("FR-003 deviation already recorded.")

def main() -> None:
    """Main entry point to record FR-003 deviation."""
    setup_logging()
    logging.info("Starting Spec Deviation Handler (FR-003)")
    record_spec_deviation_fr003()
    logging.info("Spec Deviation Handler completed.")

if __name__ == "__main__":
    main()