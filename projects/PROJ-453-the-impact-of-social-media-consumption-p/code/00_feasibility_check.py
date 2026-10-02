import os
import sys
import logging
import json
import yaml
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from config import DATA_ROOT, RESULTS_ROOT
from logging_config import setup_logging, get_logger

logger = setup_logging() if 'setup_logging' in dir() else logging.getLogger(__name__)
try:
    logger = get_logger(__name__)
except Exception:
    pass

def load_schema_contract(schema_path: str) -> Dict[str, Any]:
    """Load the schema contract from a YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(data: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate that the DataFrame columns match the schema requirements."""
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Data must be a pandas DataFrame")
    required_columns = schema.get('required_columns', [])
    data_cols = set(data.columns)
    missing = [col for col in required_columns if isinstance(col, str) and col not in data_cols]
    if missing:
        raise ValueError(f"Schema mismatch: Missing columns {missing}")
    return True

def check_dataset_feasibility(dataset_id: str) -> Optional[str]:
    """
    Check if a dataset ID exists and is accessible.
    Returns the URL if accessible, None otherwise.
    """
    base_url = "https://huggingface.co/datasets"
    card_url = f"{base_url}/{dataset_id}"
    
    try:
        response = requests.head(card_url, timeout=10)
        if response.status_code == 200:
            return card_url
    except Exception:
        pass
    return None

def write_feasibility_report(status: str, dataset_id: Optional[str], message: str, 
                             proxy_used: bool = False, merged_datasets: List[str] = None) -> None:
    """Write the feasibility status to a JSON file."""
    report = {
        "status": status,
        "dataset_id": dataset_id,
        "message": message,
        "proxy_used": proxy_used,
        "merged_datasets": merged_datasets or []
    }
    output_path = Path(RESULTS_ROOT) / "feasibility_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Feasibility report written to {output_path}")

def write_schema_validation_log(status: str, details: str) -> None:
    """Write schema validation log."""
    output_path = Path(RESULTS_ROOT) / "schema_validation_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"status": status, "details": details}, f, indent=2)

def main():
    """Main feasibility check."""
    logger.info("Starting feasibility check.")
    
    candidates = ["nrc/addhealth_wave4", "hilda/hilda_2023", "ess/ess_round10"]
    required_vars = ["self_reported_switching_frequency", "cognitive_flexibility_score"]
    
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract missing: {schema_path}")
    schema = load_schema_contract(str(schema_path))
    
    for candidate in candidates:
        url = check_dataset_feasibility(candidate)
        if url:
            logger.info(f"Found candidate: {candidate} at {url}")
            # Try to fetch sample (first 1000 rows)
            try:
                # Attempt to download a sample
                sample_df = pd.read_csv(f"{url}/data.csv", nrows=1000)
                # Validate schema
                if validate_schema_structure(sample_df, schema):
                    write_feasibility_report("PASS", candidate, "Dataset feasible.", 
                                           proxy_used=False, merged_datasets=[])
                    logger.info("Feasibility check passed.")
                    return
            except Exception as e:
                logger.warning(f"Failed to validate sample from {candidate}: {e}")
                continue
                
    write_feasibility_report("FAIL", None, "No feasible dataset found.")
    logger.error("Feasibility check failed for all candidates.")

if __name__ == "__main__":
    main()
