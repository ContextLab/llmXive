import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

from src.utils.config import get_data_path, ensure_directories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Loads a JSON file safely."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return None

def aggregate_results() -> Dict[str, Any]:
    """
    Aggregates all result files into a single report.
    """
    base_path = get_data_path("results")
    
    # Load various reports
    stats_report = load_json_safe(base_path / "stats_report.json")
    linearity = load_json_safe(base_path / "linearity_validation.json")
    latency = load_json_safe(base_path / "latency_metrics.json")
    reconstruction = load_json_safe(base_path / "reconstruction_error.json")
    
    report = {
        "status": "complete",
        "linearity_valid": linearity.get("linearity_valid", False) if linearity else False,
        "max_error": linearity.get("max_error", 0.0) if linearity else 0.0,
        "correlation_coefficient": linearity.get("correlation_coefficient", 0.0) if linearity else 0.0,
        "reconstruction_error": reconstruction,
        "latency_metrics": latency,
        "stats_report": stats_report,
        "warnings": []
    }
    
    # Add warnings if any
    if not report["linearity_valid"]:
        report["warnings"].append("Linearity validation failed (SC-005)")
    
    return report

def main():
    """
    Generates the final stats_report.json.
    """
    logger.info("Generating stats report")
    
    report = aggregate_results()
    
    output_path = get_data_path("results") / "stats_report.json"
    ensure_directories([output_path.parent])
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Stats report saved to {output_path}")

if __name__ == "__main__":
    main()
