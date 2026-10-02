"""
Generates the data gap report when no verified task-switching dataset is found.
This module is triggered by T012 if both API search and fallback fail.
"""
import json
import os
from pathlib import Path
from datetime import datetime

# Import the tolerant logger from the shared module
from synchrony import get_logger

logger = get_logger("data_gap_report_generator")

SCHEMA_PATH = Path("contracts/data_gap_report.schema.yaml")
REPORT_PATH = Path("data/data_gap_report.json")
LOG_PATH = Path("logs/processing.log")

def load_schema():
    """Loads the schema definition. Currently returns a dict structure as the schema is YAML."""
    # In a real implementation, we would parse the YAML.
    # For this task, we rely on the contract definition in the prompt:
    # Keys: dataset_id, reason, timestamp, fallback_id (optional/nullable)
    return {
        "type": "object",
        "properties": {
            "dataset_id": {"type": ["string", "null"]},
            "reason": {"type": "string"},
            "timestamp": {"type": "string"},
            "fallback_id": {"type": ["string", "null"]}
        },
        "required": ["dataset_id", "reason", "timestamp", "fallback_id"]
    }

def generate_data_gap_report(dataset_id=None, fallback_id=None, reason="No verified task-switching dataset found via API search or fallback"):
    """
    Generates the data gap report JSON artifact.

    Args:
        dataset_id: The ID that was searched for (usually null if search failed entirely).
        fallback_id: The fallback ID that was attempted (or null if not attempted/failed).
        reason: The specific reason for the gap.
    """
    logger.log("generate_data_gap_report", dataset_id=dataset_id, fallback_id=fallback_id, reason=reason)

    report = {
        "dataset_id": dataset_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "fallback_id": fallback_id
    }

    # Ensure data directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write the report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.log("data_gap_report_written", path=str(REPORT_PATH))
    return report

def main():
    """
    Entry point for T012b.
    Generates the report with fallback_id: null as per task requirements.
    """
    logger.log("main", task="T012b")
    
    # As per T012b description:
    # "with `fallback_id: null` if no fallback was attempted or failed"
    # Since this task is triggered when T012 fails (API + fallback failed),
    # we set fallback_id to null in the report to indicate the failure state.
    generate_data_gap_report(
        dataset_id=None,
        fallback_id=None,
        reason="No verified task-switching dataset found via API search or fallback"
    )
    
    # Log to processing log as required
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.utcnow().isoformat()}] ERROR: No verified task-switching dataset found via API search or fallback\n")

    print("Data gap report generated successfully.")

if __name__ == "__main__":
    main()