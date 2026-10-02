import os
import sys
import logging
import json
import yaml
import pandas as pd
from pathlib import Path

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

def main():
    """Main schema validation."""
    logger.info("Starting schema validation.")
    
    # 1. Read Feasibility
    feasibility_path = Path(RESULTS_ROOT) / "feasibility_status.json"
    if not feasibility_path.exists():
        raise FileNotFoundError(f"Feasibility status missing: {feasibility_path}")
        
    with open(feasibility_path, 'r') as f:
        feasibility = json.load(f)
        
    if feasibility.get('status') != 'PASS':
        raise RuntimeError("Feasibility check did not pass. Cannot proceed.")
        
    dataset_id = feasibility.get('dataset_id')
    if not dataset_id:
        raise RuntimeError("No dataset ID in feasibility status.")
        
    # 2. Fetch Sample (reuse logic or read from disk if downloaded)
    # Assuming ingestion downloaded it to data/raw
    raw_path = Path(DATA_ROOT) / "raw" / f"{dataset_id}_raw.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data not found: {raw_path}")
        
    sample_df = pd.read_csv(raw_path, nrows=1000)
    
    # 3. Validate
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract missing: {schema_path}")
    schema = load_schema_contract(str(schema_path))
    
    required_columns = schema.get('required_columns', [])
    data_cols = set(sample_df.columns)
    missing = [col for col in required_columns if isinstance(col, str) and col not in data_cols]
    
    if missing:
        status = "FAIL"
        details = f"Data Gap: Downloaded data schema mismatch. Missing: {missing}"
    else:
        status = "PASS"
        details = "Schema matches."
        
    # 4. Output
    output_path = Path(RESULTS_ROOT) / "schema_validation_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"status": status, "details": details}, f, indent=2)
        
    logger.info(f"Schema validation {status}.")
    if status == "FAIL":
        raise ValueError(details)

if __name__ == "__main__":
    main()
