import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from config import get_data_path, get_processed_path, get_results_path, setup_logging
from helpers import validate_dataset_completeness, calculate_statistics, parse_smell_labels, create_detection_matrix


def load_static_baseline(csv_path: str) -> pd.DataFrame:
    """Load the static baseline CSV."""
    logger = setup_logging(__name__)
    logger.info(f"Loading static baseline from {csv_path}...")
    return pd.read_csv(csv_path)


def load_semantic_results(json_path: str) -> List[Dict[str, Any]]:
    """Load semantic results JSON."""
    logger = setup_logging(__name__)
    logger.info(f"Loading semantic results from {json_path}...")
    with open(json_path, "r") as f:
        return json.load(f)


def merge_datasets(static_df: pd.DataFrame, semantic_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Merge static baseline and semantic results."""
    logger = setup_logging(__name__)
    semantic_df = pd.DataFrame(semantic_results)

    # Merge on code (assuming code is unique or using index)
    merged = pd.merge(static_df, semantic_df, on="code", how="inner")
    logger.info(f"Merged dataset size: {len(merged)}")
    return merged


def validate_merged_dataset(merged_df: pd.DataFrame, required_fields: List[str], min_completeness: float = 0.95) -> bool:
    """Validate merged dataset completeness."""
    logger = setup_logging(__name__)
    completeness = validate_dataset_completeness(merged_df, required_fields)
    if completeness < min_completeness:
        logger.warning(f"Completeness {completeness:.2%} below threshold {min_completeness:.2%}")
        return False
    logger.info(f"Validation passed. Completeness: {completeness:.2%}")
    return True


def run_mcnemar_test(merged_df: pd.DataFrame, smell_category: str) -> float:
    """
    Run McNemar's test for a specific smell category.
    Returns p-value.
    """
    logger = setup_logging(__name__)
    try:
        # Create detection matrix
        matrix = create_detection_matrix(merged_df, smell_category)

        # McNemar's test (simplified: chi-square approximation)
        a, b, c, d = matrix["both"], matrix["static_only"], matrix["llm_only"], matrix["neither"]

        if b + c == 0:
            logger.warning("No discordant pairs for McNemar's test.")
            return 1.0

        chi_sq = (abs(b - c) ** 2) / (b + c)
        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(chi_sq, df=1)
        return p_value

    except Exception as e:
        logger.error(f"McNemar's test failed for {smell_category}: {e}")
        return 1.0


def calculate_vif(merged_df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for predictors.
    """
    logger = setup_logging(__name__)
    vif_scores = {}

    for i, var in enumerate(predictors):
        other_vars = [v for v in predictors if v != var]
        if not other_vars:
            vif_scores[var] = 1.0
            continue

        try:
            X = merged_df[other_vars].values
            y = merged_df[var].values
            r2 = 1 - (np.var(y - np.dot(X, np.linalg.lstsq(X, y, rcond=None)[0])) / np.var(y))
            vif = 1 / (1 - r2)
            vif_scores[var] = vif
        except Exception as e:
            logger.warning(f"VIF calculation failed for {var}: {e}")
            vif_scores[var] = float('inf')

    return vif_scores


def fit_logistic_regression(merged_df: pd.DataFrame, predictors: List[str], target: str) -> Dict[str, Any]:
    """
    Fit logistic regression, excluding or residualizing high-VIF predictors.
    """
    logger = setup_logging(__name__)
    vif_scores = calculate_vif(merged_df, predictors)

    # Identify high-VIF predictors
    high_vif = [p for p, v in vif_scores.items() if v >= 5]
    flagged = {p: v for p, v in vif_scores.items() if v >= 5}

    # Exclude high-VIF predictors (simple approach)
    valid_predictors = [p for p in predictors if p not in high_vif]

    if not valid_predictors:
        logger.warning("No valid predictors remaining after VIF filtering.")
        return {"coefficients": {}, "vif_scores": vif_scores, "flagged": flagged}

    try:
        from sklearn.linear_model import LogisticRegression
        X = merged_df[valid_predictors].values
        y = merged_df[target].values

        model = LogisticRegression()
        model.fit(X, y)

        coefficients = {p: float(c) for p, c in zip(valid_predictors, model.coef_[0])}

        return {
            "coefficients": coefficients,
            "vif_scores": vif_scores,
            "flagged": flagged,
            "excluded": high_vif
        }

    except Exception as e:
        logger.error(f"Logistic regression failed: {e}")
        return {"coefficients": {}, "vif_scores": vif_scores, "flagged": flagged, "error": str(e)}


def run_sensitivity_analysis(merged_df: pd.DataFrame, loc_thresholds: List[int]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping LOC thresholds.
    """
    logger = setup_logging(__name__)
    results = []

    for threshold in loc_thresholds:
        # Detect smells based on static metrics (simplified)
        static_detected = merged_df["loc"] >= threshold
        # Compare with LLM detection (simplified: assume LLM labels are ground truth)
        llm_detected = merged_df["llm_smell_labels"].apply(lambda x: len(parse_smell_labels(x)) > 0)

        # Calculate FP and FN rates
        tp = ((static_detected) & (llm_detected)).sum()
        fp = ((static_detected) & (~llm_detected)).sum()
        fn = ((~static_detected) & (llm_detected)).sum()

        fp_rate = fp / (fp + fn) if (fp + fn) > 0 else 0.0
        fn_rate = fn / (fp + fn) if (fp + fn) > 0 else 0.0

        results.append({
            "threshold": threshold,
            "fp_rate": fp_rate,
            "fn_rate": fn_rate
        })

    return results


def generate_sensitivity_report(analysis_results: List[Dict[str, Any]], output_path: str) -> None:
    """Generate sensitivity report markdown."""
    logger = setup_logging(__name__)
    with open(output_path, "w") as f:
        f.write("# Sensitivity Analysis Report\n\n")
        f.write("| Threshold | FP Rate | FN Rate |\n")
        f.write("|-----------|---------|---------|\n")
        for res in analysis_results:
            f.write(f"| {res['threshold']} | {res['fp_rate']:.4f} | {res['fn_rate']:.4f} |\n")
    logger.info(f"Sensitivity report saved to {output_path}")


def run_statistical_analysis(
    static_baseline_path: str,
    semantic_results_path: str,
    sample_size: int,
    original_sample_size: int
) -> Dict[str, Any]:
    """
    Run full statistical analysis: merge, validate, McNemar, VIF, regression, sensitivity.
    """
    logger = setup_logging(__name__)

    # Load data
    static_df = load_static_baseline(static_baseline_path)
    semantic_results = load_semantic_results(semantic_results_path)

    # Merge
    merged_df = merge_datasets(static_df, semantic_results)

    # Validate
    required_fields = ["code", "loc", "cyclomatic_complexity", "nesting_depth", "static_smell_labels", "llm_smell_labels"]
    is_valid = validate_merged_dataset(merged_df, required_fields)

    if not is_valid:
        logger.error("Merged dataset validation failed.")
        return {}

    # Calculate drop-off rate
    drop_off_rate = 1 - (len(merged_df) / original_sample_size)
    logger.info(f"Drop-off rate: {drop_off_rate:.2%}")

    # Save drop-off report
    drop_off_report = {
        "original_sample_size": original_sample_size,
        "final_sample_size": len(merged_df),
        "drop_off_rate": drop_off_rate,
        "status": "passed" if drop_off_rate <= 0.05 else "warning"
    }
    with open(os.path.join(get_results_path(), "statistical_significance.json"), "w") as f:
        json.dump(drop_off_report, f, indent=2)

    # McNemar's test (example for one smell category)
    smell_categories = ["LongMethod", "NamingConvention"]  # Example categories
    mcnemar_results = {}
    for smell in smell_categories:
        p_val = run_mcnemar_test(merged_df, smell)
        mcnemar_results[smell] = p_val

    # Save McNemar results
    with open(os.path.join(get_results_path(), "statistical_significance.json"), "w") as f:
        json.dump({"drop_off": drop_off_report, "mcnemar_pvalues": mcnemar_results}, f, indent=2)

    # VIF and Logistic Regression
    predictors = ["loc", "cyclomatic_complexity", "semantic_mean"]  # semantic_mean would be derived
    # For simplicity, use loc and cyclomatic_complexity
    predictors = ["loc", "cyclomatic_complexity"]
    regression_results = fit_logistic_regression(merged_df, predictors, target="llm_detected")

    with open(os.path.join(get_results_path(), "logistic_regression.json"), "w") as f:
        json.dump(regression_results, f, indent=2)

    # Sensitivity Analysis
    loc_thresholds = list(range(10, 100, 10))
    sensitivity_results = run_sensitivity_analysis(merged_df, loc_thresholds)
    generate_sensitivity_report(sensitivity_results, os.path.join(get_results_path(), "sensitivity_report.md"))

    # Save sensitivity metrics
    with open(os.path.join(get_results_path(), "sensitivity_metrics.json"), "w") as f:
        json.dump(sensitivity_results, f, indent=2)

    logger.info("Statistical analysis complete.")
    return {
        "drop_off_rate": drop_off_rate,
        "mcnemar_results": mcnemar_results,
        "regression_results": regression_results,
        "sensitivity_results": sensitivity_results
    }
