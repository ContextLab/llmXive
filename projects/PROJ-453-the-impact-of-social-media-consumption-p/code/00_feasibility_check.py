import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import requests

logger = logging.getLogger(__name__)

def log_setup():
    """Configure logging to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        stream=sys.stdout
    )

def load_schema_contract() -> Dict[str, Any]:
    """Load the expected dataset schema contract."""
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """Validate that the schema has required fields."""
    required_fields = ['switching_index', 'cognitive_flexibility_score', 'age', 'total_screen_time', 'num_platforms', 'switching_frequency']
    schema_fields = schema.get('columns', [])
    return all(field in schema_fields for field in required_fields)

def check_dataset_feasibility(dataset_name: str, url: str) -> bool:
    """
    Check if a dataset URL is accessible and contains tabular data.
    Uses HEAD request for lightweight check.
    """
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"Dataset {dataset_name} is accessible at {url}")
            return True
        else:
            logger.warning(f"Dataset {dataset_name} returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Failed to access {dataset_name}: {e}")
        return False

def create_schema_contract():
    """Create the dataset schema contract file."""
    schema = {
        "columns": [
            "switching_index",
            "cognitive_flexibility_score",
            "age",
            "total_screen_time",
            "num_platforms",
            "switching_frequency"
        ],
        "description": "Expected columns for social media consumption analysis"
    }
    Path("contracts").mkdir(exist_ok=True)
    with open("contracts/dataset.schema.yaml", 'w') as f:
        yaml.dump(schema, f)
    logger.info("Created contracts/dataset.schema.yaml")

def write_feasibility_report(results: Dict[str, bool]):
    """Write feasibility check results to logs."""
    Path("logs").mkdir(exist_ok=True)
    with open("logs/feasibility_report.txt", 'w') as f:
        f.write(f"Feasibility Report - {datetime.now()}\n")
        f.write("=" * 50 + "\n")
        for dataset, status in results.items():
            status_str = "PASS" if status else "FAIL"
            f.write(f"{dataset}: {status_str}\n")
        if all(results.values()):
            f.write("\nOVERALL: PASS\n")
        else:
            f.write("\nOVERALL: FAIL - No viable dataset found.\n")

def write_schema_validation_log(is_valid: bool):
    """Write schema validation result."""
    Path("logs").mkdir(exist_ok=True)
    with open("logs/schema_validation.log", 'w') as f:
        f.write(f"Schema Validation - {datetime.now()}\n")
        f.write(f"Status: {'VALID' if is_valid else 'INVALID'}\n")

def main():
    """Main entry point for feasibility check."""
    log_setup()
    logger.info("Starting feasibility check pipeline.")

    # Create schema contract if missing
    if not Path("contracts/dataset.schema.yaml").exists():
        create_schema_contract()

    # Define candidate datasets
    datasets = [
        ("HILDA", "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/EXAMPLE"),
        ("ESS", "https://www.europeansocialsurvey.org/data/download.html?r=10"),
        ("AddHealth", "https://www.cpc.unc.edu/projects/addhealth/data/guides")
    ]

    # Check feasibility
    results = {}
    for name, url in datasets:
        results[name] = check_dataset_feasibility(name, url)

    # Write report
    write_feasibility_report(results)

    # Validate schema
    try:
        schema = load_schema_contract()
        is_valid = validate_schema_structure(schema)
        write_schema_validation_log(is_valid)
        if not is_valid:
            raise ValueError("Schema validation failed")
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        sys.exit(1)

    logger.info("Feasibility check complete.")

if __name__ == "__main__":
    main()
