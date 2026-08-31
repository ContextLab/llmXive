"""Statistical analysis for comparative evaluation."""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from config import get_data_path, get_processed_path, get_results_path, setup_logging
from helpers import calculate_statistics

logger = setup_logging(__name__)


def load_static_baseline(filepath: str) -> pd.DataFrame:
    """Load static baseline data.

    Args:
        filepath: Path to CSV.

    Returns:
        DataFrame.
    """
    return pd.read_csv(filepath)


def load_semantic_results(filepath: str) -> List[Dict[str, Any]]:
    """Load semantic results.

    Args:
        filepath: Path to JSON.

    Returns:
        List of dictionaries.
    """
    with open(filepath, "r") as f:
        return json.load(f)


def merge_datasets(static_df: pd.DataFrame, semantic_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Merge static and semantic datasets.

    Args:
        static_df: Static baseline DataFrame.
        semantic_results: Semantic results list.

    Returns:
        Merged DataFrame.
    """
    semantic_df = pd.DataFrame(semantic_results)
    merged = pd.merge(static_df, semantic_df, on="id", how="inner")
    return merged


def validate_merged_dataset(df: pd.DataFrame) -> bool:
    """Validate the merged dataset.

    Args:
        df: Merged DataFrame.

    Returns:
        True if valid.
    """
    required_cols = ["code", "loc", "cyclomatic_complexity", "static_smell_labels", "llm_labels"]
    return all(col in df.columns for col in required_cols)


def parse_smell_labels(labels: Any) -> List[str]:
    """Parse smell labels from string or list.

    Args:
        labels: Labels data.

    Returns:
        List of smell names.
    """
    if isinstance(labels, list):
        return labels
    if isinstance(labels, str):
        # Assume JSON string
        try:
            return json.loads(labels)
        except:
            return [labels]
    return []


def create_detection_matrix(df: pd.DataFrame, smell: str) -> Tuple[int, int, int, int]:
    """Create a 2x2 contingency matrix for a specific smell.

    Args:
        df: Merged DataFrame.
        smell: Smell name to analyze.

    Returns:
        Tuple (a, b, c, d) where:
          a: Both detected
          b: Static only
          c: LLM only
          d: Neither
    """
    a = b = c = d = 0
    for _, row in df.iterrows():
        static_has = smell in parse_smell_labels(row["static_smell_labels"])
        llm_has = smell in parse_smell_labels(row["llm_labels"])

        if static_has and llm_has:
            a += 1
        elif static_has and not llm_has:
            b += 1
        elif not static_has and llm_has:
            c += 1
        else:
            d += 1
    return a, b, c, d


def run_mcnemar_test(df: pd.DataFrame, smells: List[str]) -> Dict[str, float]:
    """Run McNemar's test for each smell.

    Args:
        df: Merged DataFrame.
        smells: List of smell names.

    Returns:
        Dictionary of p-values.
    """
    from statsmodels.stats.contingency_tables import mcnemar
    results = {}
    for smell in smells:
        a, b, c, d = create_detection_matrix(df, smell)
        if b + c > 0:
            table = [[a, b], [c, d]]
            res = mcnemar(table, exact=False)
            results[smell] = float(res.pvalue)
        else:
            results[smell] = None
    return results


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors.

    Args:
        df: DataFrame with predictors.
        predictors: List of predictor column names.

    Returns:
        Dictionary of VIF scores.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    X = df[predictors].values
    vif_scores = {}
    for i, col in enumerate(predictors):
        vif = variance_inflation_factor(X, i)
        vif_scores[col] = float(vif)
    return vif_scores


def fit_logistic_regression(df: pd.DataFrame, target_col: str, predictors: List[str]) -> Dict[str, Any]:
    """Fit logistic regression model.

    Args:
        df: DataFrame.
        target_col: Target column name.
        predictors: List of predictor column names.

    Returns:
        Dictionary of coefficients and stats.
    """
    import statsmodels.api as sm
    X = df[predictors]
    y = df[target_col]
    X = sm.add_constant(X)
    model = sm.Logit(y, X).fit(disp=0)
    return {
        "coefficients": model.params.to_dict(),
        "pvalues": model.pvalues.to_dict(),
    }


def run_sensitivity_analysis(df: pd.DataFrame, loc_thresholds: List[int]) -> Dict[str, Any]:
    """Run sensitivity analysis on LOC thresholds.

    Args:
        df: DataFrame.
        loc_thresholds: List of LOC thresholds.

    Returns:
        Dictionary of sensitivity metrics.
    """
    results = {}
    for thresh in loc_thresholds:
        # Define static smell as high LOC
        df["static_high_loc"] = df["loc"] > thresh
        # Assume LLM is ground truth for simplicity in this demo
        # In reality, you'd have a gold standard
        df["llm_detected"] = df["llm_labels"].apply(lambda x: len(parse_smell_labels(x)) > 0)

        tp = ((df["static_high_loc"]) & (df["llm_detected"])).sum()
        fp = ((df["static_high_loc"]) & (~df["llm_detected"])).sum()
        fn = ((~df["static_high_loc"]) & (df["llm_detected"])).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        results[thresh] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": fp / (fp + tp) if (fp + tp) > 0 else 0,
            "false_negative_rate": fn / (fn + tp) if (fn + tp) > 0 else 0,
        }
    return results


def generate_sensitivity_report(sensitivity_results: Dict[int, Dict[str, float]]) -> str:
    """Generate a markdown report for sensitivity analysis.

    Args:
        sensitivity_results: Results from run_sensitivity_analysis.

    Returns:
        Markdown string.
    """
    lines = ["# Sensitivity Analysis Report", ""]
    lines.append("## LOC Thresholds Analysis")
    lines.append("")
    lines.append("| Threshold | Precision | Recall | F1 | FP Rate | FN Rate |")
    lines.append("|---|---|---|---|---|---|")
    for thresh, metrics in sensitivity_results.items():
        lines.append(
            f"| {thresh} | {metrics['precision']:.3f} | {metrics['recall']:.3f} | "
            f"{metrics['f1']:.3f} | {metrics['false_positive_rate']:.3f} | {metrics['false_negative_rate']:.3f} |"
        )
    return "\n".join(lines)


def run_statistical_analysis() -> None:
    """Run the full statistical analysis pipeline."""
    # Load data
    static_df = load_static_baseline(get_data_path("static_baseline.csv"))
    semantic_results = load_semantic_results(get_processed_path("semantic_results.json"))
    merged = merge_datasets(static_df, semantic_results)

    if not validate_merged_dataset(merged):
        logger.error("Merged dataset validation failed.")
        return

    # Smell categories
    smells = ["NamingConvention", "LongMethod", "ComplexCondition"] # Example list

    # McNemar
    mcnemar_results = run_mcnemar_test(merged, smells)
    with open(get_results_path("statistical_significance.json"), "w") as f:
        json.dump(mcnemar_results, f, indent=2)

    # VIF and Regression
    predictors = ["loc", "cyclomatic_complexity"]
    vif_scores = calculate_vif(merged, predictors)
    # Filter high VIF
    safe_predictors = [p for p, v in vif_scores.items() if v < 5]
    reg_results = fit_logistic_regression(merged, "llm_detected", safe_predictors) if safe_predictors else {}

    with open(get_results_path("logistic_regression.json"), "w") as f:
        json.dump({
            "vif_scores": vif_scores,
            "high_vif_predictors": [p for p, v in vif_scores.items() if v >= 5],
            "regression": reg_results,
        }, f, indent=2)

    # Sensitivity
    loc_thresholds = [50, 100, 150]
    sens_results = run_sensitivity_analysis(merged, loc_thresholds)
    report = generate_sensitivity_report(sens_results)
    with open(get_results_path("sensitivity_report.md"), "w") as f:
        f.write(report)

    logger.info("Statistical analysis complete.")


if __name__ == "__main__":
    run_statistical_analysis()
