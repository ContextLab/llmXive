"""
Statistical analysis module for evaluating prompt engineering effectiveness.

Performs Chi-square tests for functional correctness and ANOVA for quality metrics,
including Bonferroni correction for multiple comparisons.

Dependencies:
- T028 (run_node_tests): Provides correctness results (pass/fail)
- T029 (compute_quality): Provides quality metrics (complexity, LOC)
- T025b (generate_translations_log): Provides aggregated logs for correlation
"""
import os
import sys
import csv
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

# Statistical libraries (standard scipy/numpy usage)
try:
    from scipy import stats
    import numpy as np
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logging.warning("scipy or numpy not installed. Statistical functions will fail at runtime.")

from src.utils.logging import get_logger

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EVAL_DIR = DATA_DIR / "evaluation"
QUALITY_METRICS_FILE = EVAL_DIR / "quality_metrics.csv"
CORRECTNESS_RESULTS_FILE = EVAL_DIR / "correctness_results.csv"
TRANSLATIONS_LOG_FILE = EVAL_DIR / "raw_translations_log.csv"
SUMMARY_OUTPUT_FILE = EVAL_DIR / "statistical_analysis_results.csv"

logger = get_logger(__name__)


def load_quality_metrics(filepath: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load quality metrics from CSV.

    Returns a dictionary mapping prompt_condition -> list of metric dicts.
    Expected columns: input_id, prompt_condition, complexity, loc, ...
    """
    if not filepath.exists():
        logger.error(f"Quality metrics file not found: {filepath}")
        return {}

    data = defaultdict(list)
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            condition = row.get('prompt_condition')
            if condition:
                # Convert numeric fields
                try:
                    row['complexity'] = float(row.get('complexity', 0))
                    row['loc'] = int(row.get('loc', 0))
                except ValueError:
                    row['complexity'] = 0.0
                    row['loc'] = 0
                data[condition].append(row)

    return dict(data)


def load_correctness_results(filepath: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load correctness results from CSV.

    Returns a dictionary mapping prompt_condition -> list of result dicts.
    Expected columns: input_id, prompt_condition, passed (bool/int), ...
    """
    if not filepath.exists():
        logger.error(f"Correctness results file not found: {filepath}")
        return {}

    data = defaultdict(list)
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            condition = row.get('prompt_condition')
            if condition:
                # Normalize passed to 1 (True) or 0 (False)
                passed_val = row.get('passed', 0)
                if isinstance(passed_val, str):
                    passed_val = 1 if passed_val.lower() in ('true', '1', 'yes') else 0
                else:
                    passed_val = int(passed_val) if passed_val else 0
                row['passed'] = passed_val
                data[condition].append(row)

    return dict(data)


def chi_square_test(correctness_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Perform Chi-square test for independence on correctness rates across conditions.

    Returns:
        Dictionary with test statistic, p-value, and contingency table.
    """
    if not HAS_SCIPY:
        raise ImportError("scipy is required for chi-square test")

    conditions = list(correctness_data.keys())
    if len(conditions) < 2:
        logger.warning("Need at least 2 conditions for Chi-square test")
        return {"error": "Insufficient conditions"}

    # Build contingency table: rows = conditions, cols = [failed, passed]
    contingency_table = []
    for condition in conditions:
        entries = correctness_data[condition]
        passed_count = sum(1 for e in entries if e.get('passed', 0) == 1)
        failed_count = len(entries) - passed_count
        contingency_table.append([failed_count, passed_count])

    if len(contingency_table) == 0:
        return {"error": "No data"}

    chi2, p, dof, expected = stats.chi2_contingency(contingency_table)

    return {
        "statistic": chi2,
        "p_value": p,
        "degrees_of_freedom": dof,
        "contingency_table": contingency_table,
        "expected_frequencies": expected.tolist() if hasattr(expected, 'tolist') else list(expected)
    }


def anova_test(quality_data: Dict[str, List[Dict[str, Any]]], metric: str = 'complexity') -> Dict[str, Any]:
    """
    Perform One-way ANOVA on a quality metric across conditions.

    Args:
        quality_data: Dict mapping condition -> list of metric dicts
        metric: The metric to test (e.g., 'complexity', 'loc')

    Returns:
        Dictionary with F-statistic, p-value, and group means.
    """
    if not HAS_SCIPY:
        raise ImportError("scipy is required for ANOVA test")

    conditions = list(quality_data.keys())
    if len(conditions) < 2:
        logger.warning("Need at least 2 conditions for ANOVA test")
        return {"error": "Insufficient conditions"}

    # Extract values for each condition
    groups = []
    group_means = {}
    for condition in conditions:
        values = []
        for entry in quality_data[condition]:
            val = entry.get(metric, 0)
            if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                values.append(val)
        if values:
            groups.append(values)
            group_means[condition] = float(np.mean(values))

    if len(groups) < 2:
        return {"error": "Insufficient data points across conditions"}

    f_stat, p_val = stats.f_oneway(*groups)

    return {
        "metric": metric,
        "f_statistic": f_stat,
        "p_value": p_val,
        "group_means": group_means,
        "sample_sizes": {cond: len(vals) for cond, vals in zip(conditions, groups)}
    }


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.

    Args:
        p_values: List of raw p-values
        alpha: Significance level

    Returns:
        Dictionary with corrected p-values, significance flags, and adjusted alpha.
    """
    if not p_values:
        return {"error": "No p-values provided"}

    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < adjusted_alpha for p in corrected_p_values]

    return {
        "raw_p_values": p_values,
        "corrected_p_values": corrected_p_values,
        "adjusted_alpha": adjusted_alpha,
        "significant": significant,
        "num_tests": n_tests
    }


def run_statistical_analysis(
    quality_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    correctness_data: Optional[Dict[str, List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """
    Orchestrate the full statistical analysis pipeline.

    Args:
        quality_data: Pre-loaded quality metrics (optional)
        correctness_data: Pre-loaded correctness results (optional)

    Returns:
        Comprehensive analysis results dictionary.
    """
    if not HAS_SCIPY:
        raise ImportError("scipy and numpy are required. Install with: pip install scipy numpy")

    # Load data if not provided
    if quality_data is None:
        logger.info(f"Loading quality metrics from {QUALITY_METRICS_FILE}")
        quality_data = load_quality_metrics(QUALITY_METRICS_FILE)
    
    if correctness_data is None:
        logger.info(f"Loading correctness results from {CORRECTNESS_RESULTS_FILE}")
        correctness_data = load_correctness_results(CORRECTNESS_RESULTS_FILE)

    if not quality_data and not correctness_data:
        raise FileNotFoundError("No data found for statistical analysis")

    results = {
        "chi_square": {},
        "anova_complexity": {},
        "anova_loc": {},
        "bonferroni": {},
        "summary": {}
    }

    # Chi-square for correctness
    if correctness_data:
        logger.info("Performing Chi-square test for correctness...")
        try:
            results["chi_square"] = chi_square_test(correctness_data)
        except Exception as e:
            logger.error(f"Chi-square test failed: {e}")
            results["chi_square"]["error"] = str(e)

    # ANOVA for quality metrics
    if quality_data:
        logger.info("Performing ANOVA for complexity...")
        try:
            results["anova_complexity"] = anova_test(quality_data, 'complexity')
        except Exception as e:
            logger.error(f"ANOVA for complexity failed: {e}")
            results["anova_complexity"]["error"] = str(e)

        logger.info("Performing ANOVA for LOC...")
        try:
            results["anova_loc"] = anova_test(quality_data, 'loc')
        except Exception as e:
            logger.error(f"ANOVA for LOC failed: {e}")
            results["anova_loc"]["error"] = str(e)

    # Bonferroni correction on all p-values
    p_values = []
    p_sources = []
    if results["chi_square"].get("p_value") is not None:
        p_values.append(results["chi_square"]["p_value"])
        p_sources.append("chi_square")
    if results["anova_complexity"].get("p_value") is not None:
        p_values.append(results["anova_complexity"]["p_value"])
        p_sources.append("anova_complexity")
    if results["anova_loc"].get("p_value") is not None:
        p_values.append(results["anova_loc"]["p_value"])
        p_sources.append("anova_loc")

    if p_values:
        logger.info("Applying Bonferroni correction...")
        results["bonferroni"] = bonferroni_correction(p_values)
        results["bonferroni"]["sources"] = p_sources

    # Generate summary
    conditions = set(quality_data.keys()) if quality_data else set()
    conditions.update(correctness_data.keys()) if correctness_data else None
    
    results["summary"] = {
        "conditions_tested": list(conditions),
        "chi_square_significant": results["chi_square"].get("p_value", 1.0) < 0.05,
        "complexity_significant": results["anova_complexity"].get("p_value", 1.0) < 0.05,
        "loc_significant": results["anova_loc"].get("p_value", 1.0) < 0.05,
        "bonferroni_adjusted_alpha": results["bonferroni"].get("adjusted_alpha", 0.05)
    }

    return results


def save_analysis_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save statistical analysis results to CSV.

    Flattens the nested results dictionary into a summary CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    
    # Chi-square row
    if results.get("chi_square"):
        chi = results["chi_square"]
        rows.append({
            "test_type": "chi_square",
            "p_value": chi.get("p_value"),
            "statistic": chi.get("statistic"),
            "degrees_of_freedom": chi.get("degrees_of_freedom"),
            "significant_bonferroni": None,
            "metric": "correctness"
        })

    # ANOVA rows
    for metric in ["complexity", "loc"]:
        key = f"anova_{metric}"
        if results.get(key):
          anova = results[key]
          # Find if this p-value was significant after Bonferroni
          sig_status = None
          if results.get("bonferroni") and anova.get("p_value") is not None:
              p_val = anova["p_value"]
              corrected = p_val * results["bonferroni"]["num_tests"]
              adjusted_alpha = results["bonferroni"]["adjusted_alpha"]
              sig_status = "significant" if corrected < adjusted_alpha else "not_significant"

          rows.append({
              "test_type": "anova",
              "p_value": anova.get("p_value"),
              "statistic": anova.get("f_statistic"),
              "degrees_of_freedom": None, # ANOVA df is complex, omit for simplicity or compute
              "significant_bonferroni": sig_status,
              "metric": metric
          })

    if not rows:
        logger.warning("No results to save")
        return

    # Write CSV
    fieldnames = ["test_type", "p_value", "statistic", "degrees_of_freedom", "significant_bonferroni", "metric"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Saved statistical analysis results to {output_path}")


def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting statistical analysis pipeline...")
    
    try:
        results = run_statistical_analysis()
        save_analysis_results(results, SUMMARY_OUTPUT_FILE)
        logger.info("Statistical analysis completed successfully.")
        
        # Log summary
        summary = results.get("summary", {})
        logger.info(f"Chi-square significant: {summary.get('chi_square_significant')}")
        logger.info(f"Complexity significant: {summary.get('complexity_significant')}")
        logger.info(f"LOC significant: {summary.get('loc_significant')}")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
