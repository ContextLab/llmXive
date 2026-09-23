"""
T016b: Generate Validation Report Script.
Reads ingestion status and validation metrics to produce validation_report.yaml.

This script reads the ingestion status (produced by T014) and validation metrics
(produced by T014a) and generates a consolidated validation report.

It depends on:
- data/processed/.ingestion_status.json (from T014)
- data/processed/validation_metrics.yaml (from T014a)

Output:
- data/processed/validation_report.yaml
"""
import os
import sys
import json
import yaml
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

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
    """Load the ingestion status JSON file."""
    if not STATUS_FILE.exists():
        raise FileNotFoundError(
            f"Ingestion status file not found: {STATUS_FILE}. "
            "Ensure T014 (validator.py) has run successfully."
        )
    with open(STATUS_FILE, 'r') as f:
        return json.load(f)

def load_validation_metrics() -> Dict[str, Any]:
    """Load the validation metrics YAML file."""
    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"Validation metrics file not found: {METRICS_FILE}. "
            "Ensure T014a (validation_metrics.py) has run successfully."
        )
    with open(METRICS_FILE, 'r') as f:
        return yaml.safe_load(f)

def generate_validation_report(status: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the validation report by combining status and metrics.
    
    Input Schema (status):
      - threshold_status (str): 'N>=100', '50<=N<100', or 'N<50'
      - exact_N (int): Total number of records
      - excluded_count (int): Number of excluded records
      - power_limitation_warning (str, optional): Warning message if N < 100
    
    Input Schema (metrics):
      - total_raw_records (int)
      - passed_threshold_count (int)
      - failed_threshold_count (int)
      - pass_rate_percentage (float)
    
    Output Schema:
      - status (str): Same as threshold_status
      - count (int): Same as exact_N
      - excluded_count (int): Same as excluded_count
      - power_limitation_warning (str, optional): Same as input
      - pass_rate_percentage (float): From metrics
      - metadata (dict): Source and generation info
    """
    report = {
        "status": status.get("threshold_status", "unknown"),
        "count": status.get("exact_N", 0),
        "excluded_count": status.get("excluded_count", 0),
        "pass_rate_percentage": metrics.get("pass_rate_percentage", 0.0),
        "metadata": {
            "source": "T016b",
            "script": "code/ingestion/generate_validation_report.py",
            "generated_at": "pipeline_run"
        }
    }
    
    # Include power limitation warning if present in status
    if "power_limitation_warning" in status and status["power_limitation_warning"]:
        report["power_limitation_warning"] = status["power_limitation_warning"]
    
    return report

def save_report(report: Dict[str, Any]):
    """Save the report to the output YAML file."""
    with open(REPORT_FILE, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Successfully saved validation report to {REPORT_FILE}")

def main():
    """Main entry point for T016b."""
    logger.info("Starting T016b: Generate Validation Report")
    
    try:
        # Load inputs
        logger.info(f"Loading ingestion status from {STATUS_FILE}")
        status = load_ingestion_status()
        
        logger.info(f"Loading validation metrics from {METRICS_FILE}")
        metrics = load_validation_metrics()
        
        # Generate report
        report = generate_validation_report(status, metrics)
        
        # Save output
        save_report(report)
        
        logger.info("T016b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        logger.error("This task depends on T014 and T014a completing successfully.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON status file: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML metrics file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
