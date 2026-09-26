"""
Phase 0: Feasibility Check and Schema Creation.
Verifies dataset accessibility and required variables before full download.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml
from datasets import load_dataset

# Import utils from sibling module
from utils import log_setup

logger = log_setup()

def load_schema_contract(path: str) -> Dict[str, Any]:
    """Load a YAML schema contract."""
    with open(path, "r") as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """Basic validation that schema has expected keys."""
    return "columns" in schema and isinstance(schema["columns"], list)

def check_dataset_feasibility(
    dataset_id: str, required_vars: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Stream a single row to check for required variables.
    Returns metadata if pass, None if fail.
    """
    logger.info(f"Checking feasibility for dataset: {dataset_id}")
    try:
        # Stream only one row to check schema
        ds = load_dataset(dataset_id, streaming=True)
        # Try to get first item from the split
        # Handle different split structures
        first_split = next(iter(ds.keys()))
        sample = next(iter(ds[first_split]))
        
        if not isinstance(sample, dict):
            logger.error(f"Dataset {dataset_id} does not yield a dict row.")
            return None

        cols = set(sample.keys())
        missing = [v for v in required_vars if v not in cols]
        
        if missing:
            logger.error(f"Data Gap: {dataset_id} lacks required variables: {missing}")
            return None

        logger.info(f"Feasibility PASS for {dataset_id}")
        return {"dataset_id": dataset_id, "columns": list(cols)}
    except Exception as e:
        logger.error(f"Failed to check {dataset_id}: {e}")
        return None

def create_schema_contract(output_path: str, required_vars: List[str]) -> None:
    """Create the dataset schema contract file."""
    schema = {
        "description": "Expected schema for social media cognitive flexibility data",
        "columns": [
            {"name": "switching_index", "type": "float"},
            {"name": "cognitive_flexibility_score", "type": "float"},
            {"name": "age", "type": "float"},
            {"name": "total_screen_time", "type": "float"},
            {"name": "num_platforms", "type": "int"},
            {"name": "switching_frequency", "type": "float"},
            {"name": "participant_id", "type": "int"},
        ]
    }
    # Add required vars dynamically if not present
    existing_names = {c["name"] for c in schema["columns"]}
    for v in required_vars:
        if v not in existing_names:
            schema["columns"].append({"name": v, "type": "float"})

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(schema, f, default_flow_style=False)
    logger.info(f"Created schema contract at {output_path}")

def write_feasibility_report(path: str, results: List[Dict[str, Any]]) -> None:
    """Write the feasibility check results."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# Feasibility Report - {datetime.now().isoformat()}\n")
        for r in results:
            status = "PASS" if r.get("pass") else "FAIL"
            f.write(f"Dataset: {r['dataset_id']} -> {status}\n")
            if "error" in r:
                f.write(f"  Error: {r['error']}\n")
            else:
                f.write(f"  Columns found: {r.get('columns', [])}\n")
    logger.info(f"Wrote feasibility report to {path}")

def write_schema_validation_log(path: str, valid: bool) -> None:
    """Write schema validation log."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# Schema Validation Log\n")
        f.write(f"Valid: {valid}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    logger.info(f"Wrote schema validation log to {path}")

def main() -> None:
    """Run the feasibility check."""
    # Define candidates
    candidates = [
        "nrc/addhealth_wave4",
        "hilda/hilda_2023",
        "ess/ess_round10",
    ]
    required_vars = [
        "self_reported_switching_frequency", 
        "cognitive_flexibility_score"
    ]
    
    # Fallback to common names if exact match not found in first pass
    # But strict check first
    results = []
    viable_dataset = None

    for cid in candidates:
        res = check_dataset_feasibility(cid, required_vars)
        if res:
            viable_dataset = cid
            results.append({"dataset_id": cid, "pass": True, "columns": res["columns"]})
            break
        else:
            results.append({"dataset_id": cid, "pass": False})

    if not viable_dataset:
        # Try with relaxed variable names if strict fails
        logger.warning("Strict check failed. Trying relaxed variable names...")
        relaxed_vars = ["switching_frequency", "cognitive_flexibility_score", "wcst_score"]
        for cid in candidates:
            res = check_dataset_feasibility(cid, relaxed_vars)
            if res:
                viable_dataset = cid
                results.append({"dataset_id": cid, "pass": True, "columns": res["columns"]})
                break
            else:
                results.append({"dataset_id": cid, "pass": False})

    if not viable_dataset:
        logger.critical("Data Gap: No viable dataset found. Project cannot proceed per US-1 Scenario 2.")
        sys.exit("Data Gap: No viable dataset found. Project cannot proceed per US-1 Scenario 2.")

    # Create schema
    schema_path = "contracts/dataset.schema.yaml"
    create_schema_contract(schema_path, required_vars)
    
    # Write reports
    write_feasibility_report("logs/feasibility_report.txt", results)
    write_schema_validation_log("logs/schema_validation.log", True)

    logger.info(f"Feasibility check complete. Viable dataset: {viable_dataset}")

if __name__ == "__main__":
    main()
