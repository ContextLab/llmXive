import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_path
from utils.logging_config import get_logger
from utils.reporting import load_results, save_results

logger = get_logger("final_report")

def load_model_metrics() -> Dict[str, Any]:
    """
    Load model metrics from results.json.
    """
    results = load_results()
    return results.get("model_metrics", {})

def load_visualization_metrics() -> Dict[str, Any]:
    """
    Load visualization metrics from results.json.
    """
    results = load_results()
    return results.get("visualization_metrics", {})

def consolidate_metrics() -> Dict[str, Any]:
    """
    Consolidate all metrics into a single report.
    """
    model = load_model_metrics()
    viz = load_visualization_metrics()
    results = load_results()
    
    consolidated = {
        "model_metrics": model,
        "visualization_metrics": viz,
        "validity_check": results.get("validity_check", {}),
        "hypothesis_test": results.get("hypothesis_test", {})
    }
    return consolidated

def generate_final_report() -> Dict[str, Any]:
    """
    Generate the final report.
    """
    consolidated = consolidate_metrics()
    results = load_results()
    results["final_report"] = consolidated
    results["report_status"] = "complete"
    save_results(results)
    logger.info("Final report generated.")
    return results

def main():
    """
    Entry point for final report generation.
    """
    generate_final_report()
