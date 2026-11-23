"""
Task T033: Generate sensitivity summary CSV.

Generates data/results/sensitivity_summary.csv with columns:
feature_set, accuracy, meets_threshold.

Reads sensitivity results from data/results/sensitivity_results.json (produced by T029/T030 logic).
Reads baseline threshold from data/results/baseline_score.json (produced by T031a).
"""
import json
import csv
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging import get_logger
from evaluation.sensitivity_minimal_set import load_baseline_score, calculate_dynamic_threshold

logger = get_logger(__name__)

RESULTS_DIR = Path("data/results")
SENSITIVITY_RESULTS_FILE = RESULTS_DIR / "sensitivity_results.json"
BASELINE_SCORE_FILE = RESULTS_DIR / "baseline_score.json"
OUTPUT_FILE = RESULTS_DIR / "sensitivity_summary.csv"


def load_sensitivity_results(filepath: Path) -> List[Dict[str, Any]]:
    """Load sensitivity analysis results from JSON."""
    if not filepath.exists():
        raise FileNotFoundError(f"Sensitivity results file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expected structure: {"results": [...]} or a flat list
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected sensitivity results format in {filepath}")


def generate_summary_csv(
    sensitivity_results: List[Dict[str, Any]],
    threshold: float
) -> List[Dict[str, Any]]:
    """
    Generate summary rows from sensitivity results.
    
    Args:
        sensitivity_results: List of dicts with keys: feature_set, accuracy (or score)
        threshold: The accuracy threshold (80% of baseline)
    
    Returns:
        List of dicts with keys: feature_set, accuracy, meets_threshold
    """
    summary_rows = []
    
    for result in sensitivity_results:
        feature_set = result.get("feature_set") or result.get("subset_name")
        accuracy = result.get("accuracy") or result.get("score")
        
        if feature_set is None or accuracy is None:
            logger.warning(f"Skipping result with missing fields: {result}")
            continue
        
        meets_threshold = float(accuracy) >= float(threshold)
        
        summary_rows.append({
            "feature_set": str(feature_set),
            "accuracy": float(accuracy),
            "meets_threshold": meets_threshold
        })
    
    return summary_rows


def save_summary_csv(rows: List[Dict[str, Any]], filepath: Path) -> None:
    """Save summary rows to CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["feature_set", "accuracy", "meets_threshold"]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Saved sensitivity summary to {filepath} ({len(rows)} rows)")


def run_summary_generation(
    sensitivity_results_path: Optional[Path] = None,
    baseline_score_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Main entry point to generate the sensitivity summary CSV.
    
    Args:
        sensitivity_results_path: Path to sensitivity_results.json
        baseline_score_path: Path to baseline_score.json
        output_path: Path for output CSV
    
    Returns:
        Path to the generated CSV file
    """
    sens_path = sensitivity_results_path or SENSITIVITY_RESULTS_FILE
    base_path = baseline_score_path or BASELINE_SCORE_FILE
    out_path = output_path or OUTPUT_FILE
    
    logger.info(f"Loading sensitivity results from {sens_path}")
    results = load_sensitivity_results(sens_path)
    
    logger.info(f"Loading baseline score from {base_path}")
    baseline_score = load_baseline_score(base_path)
    threshold = calculate_dynamic_threshold(baseline_score, threshold_ratio=0.8)
    logger.info(f"Calculated threshold (80% of baseline {baseline_score:.4f}): {threshold:.4f}")
    
    summary_rows = generate_summary_csv(results, threshold)
    save_summary_csv(summary_rows, out_path)
    
    return out_path


def main() -> None:
    """CLI entry point for T033."""
    setup_logging = get_logger()
    logger.info("Starting sensitivity summary generation (T033)")
    
    try:
        output_file = run_summary_generation()
        logger.info(f"Successfully generated: {output_file}")
        
        # Verify file exists and is non-empty
        if output_file.exists() and output_file.stat().st_size > 0:
            logger.info("Verification passed: Output file exists and is non-empty")
        else:
            logger.error("Verification failed: Output file is missing or empty")
            raise RuntimeError("Output file verification failed")
            
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating sensitivity summary: {e}")
        raise


if __name__ == "__main__":
    main()
