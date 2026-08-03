import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from code.config import RESULTS_DIR, RAW_EVALUATIONS_FILE, STABILITY_METRICS_FILE, CORRELATION_RESULTS_FILE, REGRESSION_RESIDUALS_FILE, PERMUTATION_RESULTS_FILE, FINAL_REPORT_FILE

logger = logging.getLogger(__name__)

def write_raw_evaluations(records: List[Dict[str, Any]], overwrite: bool = True) -> None:
    """Write raw evaluation results to CSV."""
    if not records:
        logger.warning("No records to write for raw evaluations.")
        return

    df = pd.DataFrame(records)
    expected_cols = ["dataset_id", "model_name", "fold_id", "repeat_id", "accuracy", "f1_score"]
    if not all(col in df.columns for col in expected_cols):
        raise ValueError(f"Raw evaluation records missing expected columns. Found: {df.columns.tolist()}")
    
    df = df[expected_cols]
    output_path = RESULTS_DIR / RAW_EVALUATIONS_FILE
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} raw evaluation records to {output_path}")

def append_raw_evaluations(records: List[Dict[str, Any]]) -> None:
    """Append raw evaluation results to existing CSV."""
    if not records:
        return
    df = pd.DataFrame(records)
    output_path = RESULTS_DIR / RAW_EVALUATIONS_FILE
    if output_path.exists():
        existing = pd.read_csv(output_path)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    logger.info(f"Appended {len(df)} records to {output_path}")

def write_stability_metrics(metrics: List[Dict[str, Any]]) -> None:
    """
    Write stability metrics (mean, std, CV for accuracy and F1) to CSV.
    Expected columns: dataset_id, model_name, mean_accuracy, cv_accuracy, mean_f1, cv_f1
    """
    if not metrics:
        logger.warning("No metrics to write for stability metrics.")
        return

    df = pd.DataFrame(metrics)
    required_cols = ["dataset_id", "model_name", "mean_accuracy", "cv_accuracy", "mean_f1", "cv_f1"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Stability metrics missing expected columns. Found: {df.columns.tolist()}")
    
    df = df[required_cols]
    output_path = RESULTS_DIR / STABILITY_METRICS_FILE
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} stability metric records to {output_path}")

def write_correlation_results(correlations: List[Dict[str, Any]]) -> None:
    """
    Write correlation results (Pearson r, p-value, Spearman rho) to CSV.
    Expected columns: property_name, model_name, pearson_r, p_value, spearman_rho, significant
    """
    if not correlations:
        logger.warning("No correlations to write.")
        return

    df = pd.DataFrame(correlations)
    # Ensure primary columns exist
    required_cols = ["property_name", "model_name", "pearson_r", "p_value"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Correlation results missing expected columns. Found: {df.columns.tolist()}")
    
    # Order columns: property, model, pearson (primary), p-value, spearman (secondary), significance
    ordered_cols = ["property_name", "model_name", "pearson_r", "p_value"]
    if "spearman_rho" in df.columns:
        ordered_cols.append("spearman_rho")
    if "significant" in df.columns:
        ordered_cols.append("significant")
    
    # Add any other columns not in the list at the end
    for col in df.columns:
        if col not in ordered_cols:
            ordered_cols.append(col)
    
    df = df[ordered_cols]
    output_path = RESULTS_DIR / CORRELATION_RESULTS_FILE
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} correlation results to {output_path}")

def write_regression_residuals(residuals: List[Dict[str, Any]]) -> None:
    """
    Write regression residuals from log-log analysis.
    Expected columns: dataset_id, model_name, property_name, residual
    """
    if not residuals:
        logger.warning("No residuals to write.")
        return

    df = pd.DataFrame(residuals)
    required_cols = ["dataset_id", "model_name", "property_name", "residual"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Regression residuals missing expected columns. Found: {df.columns.tolist()}")
    
    df = df[required_cols]
    output_path = RESULTS_DIR / REGRESSION_RESIDUALS_FILE
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} regression residual records to {output_path}")

def write_permutation_results(results: List[Dict[str, Any]]) -> None:
    """
    Write permutation test results.
    Expected columns: model_pair, property_name, statistic, raw_p_value, adjusted_p_value, significant
    """
    if not results:
        logger.warning("No permutation results to write.")
        return

    df = pd.DataFrame(results)
    required_cols = ["model_pair", "property_name", "statistic", "raw_p_value", "adjusted_p_value", "significant"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Permutation results missing expected columns. Found: {df.columns.tolist()}")
    
    df = df[required_cols]
    output_path = RESULTS_DIR / PERMUTATION_RESULTS_FILE
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} permutation test results to {output_path}")

def write_final_report(report_data: Dict[str, Any]) -> None:
    """
    Write the final summary report in Markdown format.
    report_data should contain keys: significant_datasets, model_ranking, correction_methodology, achieved_fwer
    """
    if not report_data:
        logger.warning("No report data to write.")
        return

    output_path = RESULTS_DIR / FINAL_REPORT_FILE
    with open(output_path, 'w') as f:
        f.write("# Stability Analysis Final Report\n\n")
        
        f.write("## 1. Significant Variance Differences\n\n")
        if "significant_datasets" in report_data:
            if report_data["significant_datasets"]:
                for ds in report_data["significant_datasets"]:
                    f.write(f"- Dataset {ds.get('dataset_id')} ({ds.get('model_pair')}): p-adj = {ds.get('adj_p_value'):.4f}\n")
            else:
                f.write("No datasets showed statistically significant variance differences after correction.\n")
        else:
            f.write("No data available.\n")
        f.write("\n")

        f.write("## 2. Model Comparison (Ranked by Mean CV)\n\n")
        if "model_ranking" in report_data:
            for i, model in enumerate(report_data["model_ranking"], 1):
                f.write(f"{i}. {model.get('model_name')}: Mean CV = {model.get('mean_cv'):.4f}\n")
        else:
            f.write("No ranking data available.\n")
        f.write("\n")

        f.write("## 3. Correction Methodology\n\n")
        if "correction_methodology" in report_data:
            f.write(f"{report_data['correction_methodology']}\n")
        else:
            f.write("Bonferroni correction was applied to control Family-Wise Error Rate (FWER).\n")
        f.write("\n")

        f.write("## 4. Achieved FWER\n\n")
        if "achieved_fwer" in report_data:
            f.write(f"The effective alpha level (FWER) is controlled at {report_data['achieved_fwer']:.4f}.\n")
        else:
            f.write("FWER controlled via Bonferroni correction (alpha / number of tests).\n")

    logger.info(f"Wrote final report to {output_path}")
