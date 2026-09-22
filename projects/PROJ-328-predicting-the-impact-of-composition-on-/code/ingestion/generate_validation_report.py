"""
T016b: Generate Validation Report Script.
Reads ingestion status and validation metrics to produce validation_report.yaml.
"""
import os
import sys
import json
import yaml
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = get_data_processed_dir()
STATUS_FILE = PROCESSED_DIR / ".ingestion_status.json"
METRICS_FILE = PROCESSED_DIR / "validation_metrics.yaml"
REPORT_FILE = PROCESSED_DIR / "validation_report.yaml"

def load_ingestion_status() -> Dict[str, Any]:
    if not STATUS_FILE.exists():
        raise FileNotFoundError(f"Ingestion status file not found: {STATUS_FILE}")
    with open(STATUS_FILE, 'r') as f:
        return json.load(f)

def load_validation_metrics() -> Dict[str, Any]:
    if not METRICS_FILE.exists():
        logger.warning(f"Validation metrics file not found: {METRICS_FILE}. "
                       "Using defaults.")
        return {
            "total_raw_records": 0,
            "passed_threshold_count": 0,
            "failed_threshold_count": 0,
            "pass_rate_percentage": 0.0
        }
    with open(METRICS_FILE, 'r') as f:
        return yaml.safe_load(f)

def generate_validation_report(status: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    report = {
        "status": status.get("threshold_status", "unknown"),
        "count": status.get("exact_N", 0),
        "excluded_count": status.get("excluded_count", 0),
        "pass_rate_percentage": metrics.get("pass_rate_percentage", 0.0),
        "metadata": {
            "source": "T016b",
            "generated_at": "pipeline_run"
        }
    }
    
    if "power_limitation_warning" in status:
        report["power_limitation_warning"] = status["power_limitation_warning"]
    
    return report

def save_report(report: Dict[str, Any]):
    with open(REPORT_FILE, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)
    logger.info(f"Saved validation report to {REPORT_FILE}")

def main():
    logger.info("Starting T016b: Generate Validation Report")
    try:
        status = load_ingestion_status()
        metrics = load_validation_metrics()
        report = generate_validation_report(status, metrics)
        save_report(report)
        logger.info("T016b completed.")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()