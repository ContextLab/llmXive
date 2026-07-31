"""
Statistical power analysis for the polymer degradation dataset.
Reads the processed graph dataset, counts records, and determines
if data augmentation is required based on sample size thresholds.
"""
import logging
import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from utils import get_logger, get_project_paths

# Constants for power analysis thresholds
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 150

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    Returns a float representing the effect size.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)
    
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def interpret_effect_size(d: float) -> str:
    """
    Interpret the magnitude of Cohen's d.
    Returns a string description: 'negligible', 'small', 'medium', 'large', 'very large'.
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    elif abs_d < 1.2:
        return "large"
    else:
        return "very large"

def check_dataset_power(n: int) -> Dict[str, Any]:
    """
    Determine the required action based on dataset size n.
    
    Logic:
    - If n > 150: action = "none"
    - If 50 <= n <= 150: action = "augment"
    - If n < 50: action = "augment_aggressive"
    
    Returns a dictionary with the analysis result.
    """
    if n > MAX_SAMPLE_SIZE:
        return {
            "n": n,
            "action": "none",
            "power_warning": False,
            "message": f"Dataset size ({n}) is sufficient. No augmentation needed."
        }
    elif n >= MIN_SAMPLE_SIZE:
        return {
            "n": n,
            "action": "augment",
            "power_warning": True,
            "message": f"Dataset size ({n}) is moderate. Augmentation recommended."
        }
    else:
        return {
            "n": n,
            "action": "augment_aggressive",
            "power_warning": True,
            "message": f"Dataset size ({n}) is critically small. Aggressive augmentation required."
        }

def run_power_analysis_from_csv(
    input_path: str,
    trigger_path: str,
    report_path: str,
    warning_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform statistical power analysis on the processed graph dataset.
    
    Args:
        input_path: Path to the input CSV file (data/processed/processed_graph_dataset.csv)
        trigger_path: Path to write the augmentation trigger JSON
        report_path: Path to write the power analysis report JSON
        warning_path: Optional path to write a human-readable warning text
    
    Returns:
        A dictionary containing the analysis results.
    
    Raises:
        FileNotFoundError: If the input CSV does not exist.
        ValueError: If the input file is empty or malformed.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting power analysis on {input_path}")
    
    # Verify input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the dataset
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise ValueError(f"Failed to load CSV: {e}")
    
    if df.empty:
        raise ValueError("Input dataset is empty.")
    
    n = len(df)
    logger.info(f"Loaded {n} records from dataset.")
    
    # Perform power analysis
    result = check_dataset_power(n)
    
    # Prepare report content
    report_content = {
        "n": result["n"],
        "action": result["action"],
        "power_warning": result["power_warning"],
        "message": result["message"]
    }
    
    if result["action"] == "augment_aggressive":
        report_content["power_warning"] = True
    
    # Ensure output directories exist
    Path(trigger_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    if warning_path:
        Path(warning_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write trigger file
    with open(trigger_path, 'w') as f:
        json.dump({"n": result["n"], "action": result["action"]}, f, indent=2)
    logger.info(f"Written trigger file: {trigger_path}")
    
    # Write report file
    with open(report_path, 'w') as f:
        json.dump(report_content, f, indent=2)
    logger.info(f"Written report file: {report_path}")
    
    # Write warning file if applicable
    if result["power_warning"]:
        warning_text = (
            f"POWER ANALYSIS WARNING\n"
            f"======================\n"
            f"Dataset size: {n} records\n"
            f"Action required: {result['action']}\n"
            f"Message: {result['message']}\n"
        )
        if result["action"] == "augment_aggressive":
            warning_text += (
                f"\nCRITICAL: Dataset is too small (< 50 records).\n"
                f"The pipeline will proceed with aggressive augmentation,\n"
                f"but manual intervention or dataset expansion is strongly recommended.\n"
            )
        
        if warning_path:
            with open(warning_path, 'w') as f:
                f.write(warning_text)
            logger.info(f"Written warning file: {warning_path}")
    
    logger.info(f"Power analysis complete. Action: {result['action']}")
    return result

def main():
    """
    Main entry point for the power analysis script.
    """
    logger = get_logger(__name__)
    paths = get_project_paths()
    
    input_file = paths["data_processed"] / "processed_graph_dataset.csv"
    trigger_file = paths["state"] / "augmentation_trigger.json"
    report_file = paths["data_reports"] / "power_analysis_report.json"
    warning_file = paths["data_reports"] / "power_analysis_warning.txt"
    
    try:
        result = run_power_analysis_from_csv(
            input_path=str(input_file),
            trigger_path=str(trigger_file),
            report_path=str(report_file),
            warning_path=str(warning_file)
        )
        
        # If action is augment_aggressive, log a critical message
        # but do not exit here; the pipeline logic (or a wrapper) 
        # should handle the exit code if needed.
        if result["action"] == "augment_aggressive":
            logger.critical("CRITICAL: Dataset size is too small. Aggressive augmentation triggered.")
            # Note: The task description says "HALT the pipeline (exit code 1)".
            # However, typically the script itself might exit, or the orchestrator handles it.
            # To be safe and strictly follow "HALT the pipeline", we exit with code 1.
            import sys
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        raise

if __name__ == "__main__":
    main()