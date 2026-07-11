import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from src.config import load_config
from src.models.schemas import CorrelationResult

logger = logging.getLogger(__name__)

def calculate_spearman_correlation(
    diversity_df: pd.DataFrame,
    sleep_metrics: List[str]
) -> pd.DataFrame:
    """
    Calculate Spearman rank correlation between diversity indices and sleep metrics.

    Args:
        diversity_df: DataFrame with diversity indices and sleep metrics.
        sleep_metrics: List of sleep metric column names to correlate.

    Returns:
        DataFrame with correlation results (r, p-value).
    """
    diversity_cols = [col for col in diversity_df.columns if col not in sleep_metrics]
    results = []

    for div_col in diversity_cols:
        for sleep_col in sleep_metrics:
            if diversity_df[div_col].notna().sum() < 3 or diversity_df[sleep_col].notna().sum() < 3:
                logger.warning(f"Insufficient data for {div_col} vs {sleep_col}")
                continue

            r, p = spearmanr(diversity_df[div_col], diversity_df[sleep_col])
            results.append({
                "diversity_metric": div_col,
                "sleep_metric": sleep_col,
                "r": r,
                "p_value": p
            })

    return pd.DataFrame(results)

def apply_benjamini_hochberg(
    df: pd.DataFrame,
    p_value_col: str = "p_value"
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        df: DataFrame with p-values.
        p_value_col: Name of the p-value column.

    Returns:
        DataFrame with added 'q_value' column.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to Benjamini-Hochberg correction.")
        df["q_value"] = []
        return df

    p_values = df[p_value_col].values
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    q_values = np.zeros(n)
    for i in range(n):
        rank = i + 1
        q_values[sorted_indices[i]] = sorted_p_values[i] * n / rank

    q_values = np.minimum.accumulate(q_values[::-1])[::-1]
    q_values = np.clip(q_values, 0, 1)

    df = df.copy()
    df["q_value"] = q_values
    return df

def flag_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag correlations as moderate or meaningful.

    Args:
        df: DataFrame with r and q_value columns.

    Returns:
        DataFrame with 'is_moderate' and 'is_meaningful' columns.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to flag_correlations.")
        df["is_moderate"] = []
        df["is_meaningful"] = []
        return df

    df = df.copy()
    df["is_moderate"] = df["r"].abs() > 0.3
    df["is_meaningful"] = (df["q_value"] < 0.05) & df["is_moderate"]
    return df

def handle_no_significant_associations(
    results_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Handle the case where no significant associations are found.

    Args:
        results_df: DataFrame of correlation results.
        output_path: Optional path to write a report file.

    Returns:
        Dictionary with analysis summary.
    """
    if results_df.empty:
        logger.warning("No correlation results to analyze.")
        summary = {
            "status": "no_data",
            "message": "No correlation data was available to analyze.",
            "significant_count": 0,
            "moderate_count": 0,
            "total_count": 0
        }
        if output_path:
            summary["report_path"] = str(output_path)
            with open(output_path, 'w') as f:
                f.write(f"Analysis Report: {summary['message']}\n")
        return summary

    meaningful_count = results_df["is_meaningful"].sum()
    moderate_count = results_df["is_moderate"].sum()
    total_count = len(results_df)

    if meaningful_count == 0:
        logger.info("No significant associations found (q < 0.05 and |r| > 0.3).")
        status = "no_significant_associations"
        message = (
            "No statistically significant associations were found between "
            "gut microbiome diversity indices and sleep quality metrics "
            "after Benjamini-Hochberg correction."
        )
    else:
        status = "associations_found"
        message = f"Found {meaningful_count} significant association(s)."

    summary = {
        "status": status,
        "message": message,
        "significant_count": int(meaningful_count),
        "moderate_count": int(moderate_count),
        "total_count": int(total_count)
    }

    if output_path:
        summary["report_path"] = str(output_path)
        summary_str = (
            f"Analysis Report\n"
            f"Status: {status}\n"
            f"Message: {message}\n"
            f"Total correlations tested: {total_count}\n"
            f"Moderate correlations (|r| > 0.3): {moderate_count}\n"
            f"Significant associations (q < 0.05, |r| > 0.3): {meaningful_count}\n"
        )
        with open(output_path, 'w') as f:
            f.write(summary_str)

    return summary

def run_correlation_analysis(
    input_path: Path,
    output_csv_path: Path,
    output_report_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.

    Args:
        input_path: Path to cleaned data CSV.
        output_csv_path: Path to save correlation results.
        output_report_path: Path to save analysis summary report.

    Returns:
        Summary dictionary of the analysis.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    sleep_metrics = ["sleep_efficiency", "sleep_duration_hours", "sleep_latency_minutes"]
    sleep_metrics = [m for m in sleep_metrics if m in df.columns]

    if not sleep_metrics:
        logger.error("No valid sleep metrics found in the dataset.")
        return handle_no_significant_associations(pd.DataFrame(), output_report_path)

    logger.info("Calculating Spearman correlations...")
    corr_df = calculate_spearman_correlation(df, sleep_metrics)

    if corr_df.empty:
        logger.warning("No correlations could be calculated.")
        return handle_no_significant_associations(pd.DataFrame(), output_report_path)

    logger.info("Applying Benjamini-Hochberg correction...")
    corr_df = apply_benjamini_hochberg(corr_df)

    logger.info("Flagging correlations...")
    corr_df = flag_correlations(corr_df)

    logger.info(f"Saving results to {output_csv_path}")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    corr_df.to_csv(output_csv_path, index=False)

    logger.info("Handling results summary...")
    summary = handle_no_significant_associations(corr_df, output_report_path)

    return summary

def main():
    """Entry point for the correlation analysis script."""
    config = load_config()
    input_path = Path(config.get("CLEANED_DATA_PATH", "data/processed/cleaned_microbiome_sleep.csv"))
    output_csv_path = Path(config.get("CORRELATION_RESULTS_PATH", "data/processed/correlation_results.csv"))
    output_report_path = Path(config.get("CORRELATION_REPORT_PATH", "data/processed/correlation_summary.txt"))

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T016 (cleaned dataset) has been completed.")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    summary = run_correlation_analysis(input_path, output_csv_path, output_report_path)
    logger.info(f"Analysis complete. Status: {summary['status']}")
    logger.info(summary['message'])

    if output_report_path.exists():
        logger.info(f"Report saved to: {output_report_path}")

if __name__ == "__main__":
    main()