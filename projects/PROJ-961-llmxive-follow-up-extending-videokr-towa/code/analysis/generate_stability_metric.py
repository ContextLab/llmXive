"""
Generate stability metric for sensitivity analysis.

This script calculates the count of significant thresholds from the sensitivity
analysis results and determines the robustness status.

Logic:
1. Load sensitivity results from data/processed/sensitivity_thresholds.csv
2. Count thresholds where p_value < 0.05
3. If count >= 2, robustness_status is 'PASS', else 'FAIL'
4. Write results to data/processed/stability_metric.json
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sensitivity_results(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load sensitivity analysis results from CSV file.

    Args:
        csv_path: Path to sensitivity_thresholds.csv

    Returns:
        List of dictionaries containing threshold analysis results
    """
    results = []
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    'threshold_hop': int(row['threshold_hop']),
                    'p_value': float(row['p_value']),
                    'effect_size': float(row['effect_size']),
                    'is_significant': row['is_significant'].lower() == 'true'
                })
        logger.info(f"Loaded {len(results)} sensitivity results from {csv_path}")
        return results
    except FileNotFoundError:
        logger.error(f"Sensitivity results file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading sensitivity results: {e}")
        raise


def calculate_robustness(results: List[Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate robustness status based on significant threshold count.

    Args:
        results: List of sensitivity analysis results
        alpha: Significance threshold (default 0.05)

    Returns:
        Dictionary with robustness metrics
    """
    significant_count = sum(1 for r in results if r['p_value'] < alpha)
    robustness_status = 'PASS' if significant_count >= 2 else 'FAIL'

    logger.info(f"Significant thresholds: {significant_count}/{len(results)}")
    logger.info(f"Robustness status: {robustness_status}")

    return {
        'significant_threshold_count': significant_count,
        'total_thresholds_tested': len(results),
        'alpha': alpha,
        'robustness_status': robustness_status,
        'thresholds': results
    }


def save_stability_metric(metric: Dict[str, Any], output_path: Path) -> None:
    """
    Save stability metric to JSON file.

    Args:
        metric: Stability metric dictionary
        output_path: Path to output JSON file
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metric, f, indent=2)
    logger.info(f"Saved stability metric to {output_path}")


def main() -> int:
    """
    Main entry point for stability metric generation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        project_root = get_project_root()
        sensitivity_csv = get_path(project_root, 'data/processed/sensitivity_thresholds.csv')
        output_json = get_path(project_root, 'data/processed/stability_metric.json')

        logger.info(f"Loading sensitivity results from {sensitivity_csv}")
        results = load_sensitivity_results(sensitivity_csv)

        if not results:
            logger.error("No sensitivity results found. Cannot calculate stability metric.")
            return 1

        logger.info("Calculating robustness metrics...")
        metric = calculate_robustness(results)

        logger.info(f"Saving stability metric to {output_json}")
        save_stability_metric(metric, output_json)

        logger.info(f"Stability metric generated successfully. Status: {metric['robustness_status']}")
        return 0

    except Exception as e:
        logger.error(f"Failed to generate stability metric: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())