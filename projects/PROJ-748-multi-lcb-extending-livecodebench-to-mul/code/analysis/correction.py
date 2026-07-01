"""
Bonferroni correction and significance flagging for hypothesis tests.

This module implements the Bonferroni correction method to adjust p-values
for multiple hypothesis testing, preventing inflated Type I error rates.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from config import get_config, get_results_path


def setup_logging() -> logging.Logger:
    """Configure logging for the correction module."""
    logger = logging.getLogger("correction")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)
    return logger


def load_p_values(p_value_file: Path) -> List[float]:
    """
    Load p-values from a JSON file.

    Expected format: {"p_values": [0.01, 0.05, 0.12, ...]}
    or a flat list of p-values.

    Args:
        p_value_file: Path to the JSON file containing p-values.

    Returns:
        List of p-values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    logger = logging.getLogger("correction")
    
    if not p_value_file.exists():
        raise FileNotFoundError(f"P-value file not found: {p_value_file}")

    with open(p_value_file, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        p_values = data
    elif isinstance(data, dict) and "p_values" in data:
        p_values = data["p_values"]
    else:
        raise ValueError("Invalid p-value format. Expected list or {'p_values': [...]}")

    logger.info(f"Loaded {len(p_values)} p-values from {p_value_file}")
    return p_values


def load_correlation_results(results_file: Path) -> Dict[str, Any]:
    """
    Load correlation results that contain hypothesis test information.

    Args:
        results_file: Path to the correlation results JSON file.

    Returns:
        Dictionary containing correlation results.
    """
    logger = logging.getLogger("correction")
    
    if not results_file.exists():
        raise FileNotFoundError(f"Correlation results file not found: {results_file}")

    with open(p_value_file, "r") as f:
        data = json.load(f)

    logger.info(f"Loaded correlation results from {results_file}")
    return data


def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.

    The Bonferroni correction adjusts the significance threshold by dividing
    alpha by the number of tests (m). Alternatively, p-values can be multiplied
    by m and capped at 1.0.

    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level (default: 0.05).

    Returns:
        Tuple of (adjusted_p_values, significant_flags) where:
        - adjusted_p_values: P-values multiplied by number of tests (capped at 1.0)
        - significant_flags: Boolean list indicating if adjusted p-value < alpha
    """
    logger = logging.getLogger("correction")
    m = len(p_values)

    if m == 0:
        logger.warning("No p-values to correct")
        return [], []

    # Bonferroni correction: multiply p-values by number of tests
    adjusted_p_values = [min(p * m, 1.0) for p in p_values]

    # Flag significant results after correction
    significant_flags = [p < alpha for p in adjusted_p_values]

    logger.info(f"Applied Bonferroni correction: {sum(significant_flags)}/{m} tests significant at alpha={alpha}")

    return adjusted_p_values, significant_flags


def flag_significance(
    p_values: List[float],
    adjusted_p_values: List[float],
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Create a detailed significance report for each test.

    Args:
        p_values: Original p-values.
        adjusted_p_values: Bonferroni-corrected p-values.
        alpha: Significance threshold.

    Returns:
        List of dictionaries with test details and significance status.
    """
    logger = logging.getLogger("correction")
    results = []

    for i, (p, adj_p) in enumerate(zip(p_values, adjusted_p_values)):
        is_significant = adj_p < alpha
        results.append({
            "test_id": i,
            "raw_p_value": p,
            "adjusted_p_value": adj_p,
            "significant_after_correction": is_significant,
            "alpha_threshold": alpha,
            "bonferroni_threshold": alpha / len(p_values)
        })

    logger.info(f"Generated significance flags for {len(results)} tests")
    return results


def compute_effect_sizes(
    correlation_data: Dict[str, Any],
    p_value_flags: List[bool]
) -> List[Dict[str, Any]]:
    """
    Compute and attach effect size information to significant results.

    Args:
        correlation_data: Dictionary containing correlation coefficients.
        p_value_flags: List of significance flags corresponding to tests.

    Returns:
        List of results with effect size annotations.
    """
    logger = logging.getLogger("correction")
    enhanced_results = []

    correlations = correlation_data.get("correlation_coefficients", [])
    
    for i, (corr, is_significant) in enumerate(zip(correlations, p_value_flags)):
        result = {
            "test_id": i,
            "correlation_coefficient": corr,
            "significant": is_significant,
            "effect_size_category": _categorize_effect_size(corr)
        }
        enhanced_results.append(result)

    return enhanced_results


def _categorize_effect_size(r: float) -> str:
    """
    Categorize correlation effect size using Cohen's conventions.

    Args:
        r: Pearson correlation coefficient.

    Returns:
        String category: "small", "medium", "large", or "negligible".
    """
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"


def save_correction_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save Bonferroni correction results to a JSON file.

    Args:
        results: Dictionary containing all correction results.
        output_path: Path to the output JSON file.
    """
    logger = logging.getLogger("correction")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved correction results to {output_path}")


def run_correction_pipeline(
    p_value_file: Path,
    correlation_file: Optional[Path] = None,
    alpha: float = 0.05,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the complete Bonferroni correction pipeline.

    Args:
        p_value_file: Path to JSON file containing p-values.
        correlation_file: Optional path to correlation results for effect sizes.
        alpha: Significance threshold (default: 0.05).
        output_dir: Directory to save results (default: results/artifacts/).

    Returns:
        Dictionary containing all correction results.
    """
    logger = setup_logging()
    
    if output_dir is None:
        output_dir = get_results_path() / "artifacts"

    # Load p-values
    p_values = load_p_values(p_value_file)
    
    # Apply Bonferroni correction
    adjusted_p_values, significant_flags = apply_bonferroni_correction(
        p_values, alpha
    )

    # Generate detailed significance report
    significance_report = flag_significance(
        p_values, adjusted_p_values, alpha
    )

    # Build results dictionary
    results = {
        "method": "bonferroni",
        "alpha": alpha,
        "num_tests": len(p_values),
        "num_significant": sum(significant_flags),
        "num_insignificant": len(p_values) - sum(significant_flags),
        "bonferroni_threshold": alpha / len(p_values) if len(p_values) > 0 else 0,
        "raw_p_values": p_values,
        "adjusted_p_values": adjusted_p_values,
        "significant_flags": significant_flags,
        "significance_report": significance_report,
        "correlation_data": None
    }

    # Optionally include correlation data for effect sizes
    if correlation_file and correlation_file.exists():
        try:
            with open(correlation_file, "r") as f:
                correlation_data = json.load(f)
            enhanced_results = compute_effect_sizes(
                correlation_data, significant_flags
            )
            results["correlation_data"] = {
                "original": correlation_data,
                "enhanced_with_effect_sizes": enhanced_results
            }
        except Exception as e:
            logger.warning(f"Could not load correlation data: {e}")

    # Save results
    output_file = output_dir / "bonferroni_correction_results.json"
    save_correction_results(results, output_file)

    logger.info("Bonferroni correction pipeline completed successfully")
    return results


def main() -> int:
    """
    Main entry point for the Bonferroni correction script.

    Usage:
        python -m code.analysis.correction [--p-values FILE] [--correlation FILE] [--alpha VALUE]

    Returns:
        0 on success, 1 on error.
    """
    logger = setup_logging()
    
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply Bonferroni correction to hypothesis test p-values"
    )
    parser.add_argument(
        "--p-values",
        type=str,
        default=None,
        help="Path to JSON file containing p-values"
    )
    parser.add_argument(
        "--correlation",
        type=str,
        default=None,
        help="Optional path to correlation results JSON"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default: 0.05)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results"
    )

    args = parser.parse_args()

    # Determine p-value file path
    if args.p_values:
        p_value_file = Path(args.p_values)
    else:
        # Default location based on project structure
        config = get_config()
        # Try to find the correlation results file which contains p-values
        results_path = get_results_path() / "artifacts"
        # Look for correlation results that would have been generated by T019
        default_p_value_file = results_path / "correlation_results.json"
        
        if default_p_value_file.exists():
            p_value_file = default_p_value_file
            logger.info(f"Using default p-value file: {p_value_file}")
        else:
            logger.error(
                "No p-value file specified and default not found. "
                "Please provide --p-values path."
            )
            return 1

    # Determine correlation file path
    correlation_file = None
    if args.correlation:
        correlation_file = Path(args.correlation)
    elif p_value_file.name == "correlation_results.json":
        correlation_file = p_value_file

    # Determine output directory
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)

    try:
        results = run_correction_pipeline(
            p_value_file=p_value_file,
            correlation_file=correlation_file,
            alpha=args.alpha,
            output_dir=output_dir
        )

        logger.info(f"Results saved. Significant tests: {results['num_significant']}/{results['num_tests']}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())