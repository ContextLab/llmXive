"""
Metric Aggregation Module (US2)

Aggregates extracted metrics per group (Human vs LLM) and writes
CSV files to data/metrics/ containing mean, median, and variance.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from logging_config import setup_logger, get_logger
from data_model import MetricResult, validate_metric_result
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

# Initialize logger
logger = setup_logger("metric_aggregation", "data/logs/metric_aggregation.log")


def load_metrics_for_group(group_name: str, metrics_dir: Path) -> pd.DataFrame:
    """
    Load the metric CSV file for a specific group from data/metrics/.
    Expects files named like: data/metrics/{group_name}_metrics.csv
    """
    file_path = metrics_dir / f"{group_name}_metrics.csv"
    if not file_path.exists():
        logger.error(f"Metric file not found for group {group_name}: {file_path}")
        raise FileNotFoundError(f"Metric file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} metrics for group {group_name} from {file_path}")
    return df


def aggregate_metrics(df: pd.DataFrame, metric_columns: list) -> dict:
    """
    Compute aggregate statistics (mean, median, variance) for specified metric columns.
    
    Args:
        df: DataFrame containing the raw metrics.
        metric_columns: List of column names to aggregate.
        
    Returns:
        Dictionary with aggregated values.
    """
    aggregates = {}
    for col in metric_columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in dataframe, skipping.")
            continue
        
        # Ensure numeric
        series = pd.to_numeric(df[col], errors='coerce')
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            logger.warning(f"No valid data for column {col}")
            aggregates[col] = {
                "mean": None,
                "median": None,
                "variance": None,
                "count": 0
            }
        else:
            aggregates[col] = {
                "mean": float(clean_series.mean()),
                "median": float(clean_series.median()),
                "variance": float(clean_series.var()),
                "count": len(clean_series)
            }
    return aggregates


def write_aggregate_csv(group_name: str, aggregates: dict, output_dir: Path):
    """
    Write the aggregated metrics to a CSV file.
    Format: metric_name, mean, median, variance, count
    """
    output_path = output_dir / f"{group_name}_aggregates.csv"
    
    rows = []
    for metric_name, stats in aggregates.items():
        rows.append({
            "metric_name": metric_name,
            "mean": stats["mean"],
            "median": stats["median"],
            "variance": stats["variance"],
            "count": stats["count"]
        })
    
    if not rows:
        logger.warning(f"No aggregates to write for {group_name}")
        return
    
    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_path, index=False)
    logger.info(f"Wrote aggregate metrics to {output_path}")
    return output_path


def run_aggregation(project_root: Path = None):
    """
    Main workflow to aggregate metrics for all defined groups.
    Groups are typically 'human' and 'llm'.
    """
    if project_root is None:
        project_root = Path.cwd().parent # Assuming code/ is a subdir, or adjust as needed
        # Fallback if running from root
        if not (project_root / "data").exists():
            project_root = Path.cwd()

    metrics_dir = project_root / "data" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Define groups based on project spec (Human vs LLM)
    groups = ["human", "llm"]
    
    # Define expected metric columns based on metric_extraction.py output
    # These correspond to radon (cc, loc, mi) and pylint (bugs, conventions, refactor, warnings, info)
    # We aggregate whatever numeric columns exist in the source files to be robust
    metric_columns = [
        "cyclomatic_complexity", "lines_of_code", "maintainability_index",
        "bug_count", "convention_count", "refactor_count", "warning_count", "info_count"
    ]
    
    all_outputs = []
    
    for group in groups:
        try:
            df = load_metrics_for_group(group, metrics_dir)
            
            # Filter columns that actually exist in the dataframe
            existing_cols = [c for c in metric_columns if c in df.columns]
            if not existing_cols:
                logger.warning(f"No known metric columns found in {group}_metrics.csv. Attempting to aggregate all numeric columns.")
                existing_cols = list(df.select_dtypes(include=[np.number]).columns)
            
            if not existing_cols:
                logger.error(f"No numeric columns to aggregate for group {group}.")
                continue

            aggregates = aggregate_metrics(df, existing_cols)
            output_file = write_aggregate_csv(group, aggregates, metrics_dir)
            all_outputs.append(output_file)
            
        except FileNotFoundError:
            logger.error(f"Skipping aggregation for {group} due to missing source file.")
        except Exception as e:
            logger.error(f"Error processing group {group}: {e}", exc_info=True)
    
    if all_outputs:
        # Update state tracker
        state_file = project_root / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
        if state_file.exists():
            try:
                update_state_with_artifact(
                    state_file, 
                    "metric_aggregation", 
                    [str(p) for p in all_outputs],
                    datetime.now().isoformat()
                )
            except Exception as e:
                logger.warning(f"Failed to update state file: {e}")
    
    return all_outputs


def main():
    """Entry point for CLI execution."""
    logger.info("Starting Metric Aggregation Pipeline (T023)")
    try:
        outputs = run_aggregation()
        if outputs:
            logger.info(f"Aggregation complete. Generated {len(outputs)} files.")
            for f in outputs:
                logger.info(f"  - {f}")
        else:
            logger.warning("Aggregation produced no output files. Check logs.")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
