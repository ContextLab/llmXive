"""
T034: Generate results/summary.csv with mean deltas, std, p-values, and significance flags.

This script reads the statistical analysis results produced by T032/T033 (typically
stored in results/statistical_analysis.json or similar) and aggregates them into
a single CSV file: results/summary.csv.

Input: results/statistical_analysis.json (produced by main_benchmark.py/stats pipeline)
Output: results/summary.csv
"""

import json
import csv
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging to match project standards
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

logger = get_logger(__name__)

# Constants for file paths
RESULTS_DIR = Path("results")
STAT_ANALYSIS_FILE = RESULTS_DIR / "statistical_analysis.json"
SUMMARY_CSV_FILE = RESULTS_DIR / "summary.csv"


def load_statistical_results(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load the statistical analysis results from the JSON file.

    Expects a list of dictionaries where each dictionary represents the
    analysis for a specific function pair (original vs simplified).

    Returns:
        List[Dict[str, Any]]: The loaded analysis data.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Statistical analysis file not found: {filepath}")

    logger.info(f"Loading statistical results from {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of results in {filepath}, got {type(data)}")

    return data


def generate_summary_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate the summary CSV file with the required columns:
    - function_id
    - stratum
    - mean_original (ms)
    - mean_simplified (ms)
    - mean_delta (ms) (simplified - original)
    - std_original (ms)
    - std_simplified (ms)
    - p_value
    - is_significant (bool: p < 0.05)
    - test_type (str: 't-test' or 'wilcoxon')

    Args:
        results: List of statistical analysis dictionaries.
        output_path: Path to write the CSV file.
    """
    if not results:
        logger.warning("No results to write to summary CSV.")
        # Write empty CSV with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "function_id", "stratum", "mean_original", "mean_simplified",
                "mean_delta", "std_original", "std_simplified", "p_value",
                "is_significant", "test_type"
            ])
        return

    fieldnames = [
        "function_id", "stratum", "mean_original", "mean_simplified",
        "mean_delta", "std_original", "std_simplified", "p_value",
        "is_significant", "test_type"
    ]

    logger.info(f"Writing summary CSV to {output_path}")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            # Extract data safely with defaults
            func_id = result.get("function_id", "unknown")
            stratum = result.get("stratum", "unknown")
            
            # Performance metrics (in milliseconds as per benchmark convention)
            mean_orig = result.get("mean_original_ms", 0.0)
            mean_simp = result.get("mean_simplified_ms", 0.0)
            mean_delta = result.get("mean_delta_ms", 0.0)
            std_orig = result.get("std_original_ms", 0.0)
            std_simp = result.get("std_simplified_ms", 0.0)
            
            # Statistical metrics
            p_value = result.get("p_value", 1.0)
            test_type = result.get("test_type", "unknown")
            
            # Significance flag (FR-004: p < 0.05)
            is_sig = p_value < 0.05

            row = {
                "function_id": func_id,
                "stratum": stratum,
                "mean_original": f"{mean_orig:.6f}",
                "mean_simplified": f"{mean_simp:.6f}",
                "mean_delta": f"{mean_delta:.6f}",
                "std_original": f"{std_orig:.6f}",
                "std_simplified": f"{std_simp:.6f}",
                "p_value": f"{p_value:.6e}",
                "is_significant": str(is_sig).lower(),
                "test_type": test_type
            }
            writer.writerow(row)

    logger.info(f"Successfully wrote {len(results)} rows to {output_path}")


def run_summary_generation() -> bool:
    """
    Main entry point for T034.

    Returns:
        bool: True if successful, False otherwise.
    """
    log_stage_start(logger, "T034", "Generating summary CSV")

    try:
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        # Load data
        data = load_statistical_results(STAT_ANALYSIS_FILE)

        # Generate CSV
        generate_summary_csv(data, SUMMARY_CSV_FILE)

        log_stage_complete(logger, "T034", f"Generated {SUMMARY_CSV_FILE}")
        return True

    except FileNotFoundError as e:
        log_stage_error(logger, "T034", str(e))
        return False
    except Exception as e:
        log_stage_error(logger, "T034", f"Unexpected error: {str(e)}")
        return False


def main() -> int:
    """CLI entry point."""
    success = run_summary_generation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())