"""
Feasibility Check Module: Validates dataset schema and variable presence.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml
from datasets import load_dataset

from logging_config import setup_logging, get_logger
from config import DATA_ROOT

def load_schema_contract(path: str) -> Dict[str, Any]:
    """Load the schema contract YAML."""
    with open(path, "r") as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any], data_headers: List[str]) -> bool:
    """Check if data headers match schema keys."""
    required_keys = list(schema.keys())
    return all(k in data_headers for k in required_keys)

def check_dataset_feasibility(candidate_ids: List[str], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stream a 1-row peek from candidate datasets to verify variables.
    """
    logger = get_logger("feasibility_check")
    results = {
        "status": "FAIL",
        "dataset_id": None,
        "message": "No viable dataset found.",
        "proxy_used": False,
        "merged_datasets": []
    }

    for ds_id in candidate_ids:
        try:
            logger.info(f"Checking candidate dataset: {ds_id}")
            ds = load_dataset(ds_id, split="train", streaming=True)
            first_row = next(iter(ds))
            headers = list(first_row.keys())

            # Check required variables
            required = list(schema.keys())
            missing = [r for r in required if r not in headers]

            if not missing:
                results["status"] = "PASS"
                results["dataset_id"] = ds_id
                results["message"] = f"Dataset {ds_id} passed feasibility check."
                logger.info(f"Feasibility PASS for {ds_id}")
                return results
            else:
                logger.warning(f"Missing variables in {ds_id}: {missing}")
        except Exception as e:
            logger.error(f"Failed to check {ds_id}: {e}")

    return results

def write_feasibility_report(report: Dict[str, Any], output_path: str) -> None:
    """Write the feasibility report to JSON."""
    import json
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

def write_schema_validation_log(log_path: str, message: str) -> None:
    """Write schema validation log."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"[{datetime.now()}] {message}\n")

def main() -> int:
    """Main entry point for feasibility check."""
    setup_logging()
    logger = get_logger("feasibility_check")
    logger.info("Starting feasibility check.")

    schema_path = "contracts/dataset.schema.yaml"
    if not os.path.exists(schema_path):
        logger.error(f"Schema contract not found: {schema_path}")
        return 1

    schema = load_schema_contract(schema_path)
    candidates = ["nrc/addhealth_wave4", "hilda/hilda_2023", "ess/ess_round10"]

    report = check_dataset_feasibility(candidates, schema)

    output_path = "results/feasibility_status.json"
    write_feasibility_report(report, output_path)

    if report["status"] == "FAIL":
        logger.error("Data Gap: No viable dataset found. Project cannot proceed.")
        return 1

    logger.info(f"Feasibility check passed for {report['dataset_id']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
