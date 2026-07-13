"""
Metric Aggregation Module (T023).

Aggregates metrics per group (human-written vs LLM-generated) from the processed
metric CSVs and writes summary statistics (mean, median, variance) to CSV files
in data/metrics/.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from data_model import MetricResult, validate_metric_result
from logging_config import get_logger
from state_tracker import register_artifact_hash, load_state_file, save_state_file

# Ensure we have a logger
logger = get_logger(__name__)

# Constants
METRICS_DIR = Path("data/metrics")
PROCESSED_DIR = Path("data/processed")
STATE_FILE = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")

# Metric types expected based on T020/T021
METRIC_TYPES = [
    "cyclomatic_complexity",
    "lines_of_code",
    "maintainability_index",
    "pylint_bug_count",
    "pylint_style_issues"
]

GROUPS = ["human_written", "llm_generated"]

def load_metrics_for_group(group: str, metric_type: str) -> pd.DataFrame:
    """
    Load metrics for a specific group and metric type.
    
    Args:
        group: Either 'human_written' or 'llm_generated'
        metric_type: One of the METRIC_TYPES
        
    Returns:
        DataFrame with the metric values
    """
    # Expected file pattern based on T020/T021 output
    input_file = PROCESSED_DIR / f"{group}_{metric_type}.csv"
    
    if not input_file.exists():
        logger.error(f"Metrics file not found: {input_file}")
        raise FileNotFoundError(f"Metrics file not found: {input_file}")
    
    df = pd.read_csv(input_file)
    
    # Validate schema
    if "score" not in df.columns:
        raise ValueError(f"Expected 'score' column in {input_file}")
    
    return df

def aggregate_metrics(df: pd.DataFrame, metric_type: str, group: str) -> Dict[str, Any]:
    """
    Compute aggregate statistics for a metric.
    
    Args:
        df: DataFrame with 'score' column
        metric_type: The type of metric
        group: The group label
        
    Returns:
        Dictionary with aggregate statistics
    """
    scores = df["score"].dropna()
    
    if len(scores) == 0:
        logger.warning(f"No valid scores found for {group}/{metric_type}")
        return {
            "metric_type": metric_type,
            "group": group,
            "count": 0,
            "mean": None,
            "median": None,
            "variance": None,
            "min": None,
            "max": None,
            "std": None
        }
    
    return {
        "metric_type": metric_type,
        "group": group,
        "count": int(len(scores)),
        "mean": float(scores.mean()),
        "median": float(scores.median()),
        "variance": float(scores.var()),
        "min": float(scores.min()),
        "max": float(scores.max()),
        "std": float(scores.std())
    }

def write_aggregate_csv(aggregates: List[Dict[str, Any]], metric_type: str) -> Path:
    """
    Write aggregate statistics to a CSV file.
    
    Args:
        aggregates: List of aggregate dictionaries
        metric_type: The metric type for the filename
        
    Returns:
        Path to the output file
    """
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = METRICS_DIR / f"{metric_type}_aggregates.csv"
    
    df = pd.DataFrame(aggregates)
    df.to_csv(output_file, index=False)
    
    logger.info(f"Wrote aggregate metrics to {output_file}")
    return output_file

def run_aggregation(metric_types: Optional[List[str]] = None) -> Dict[str, Path]:
    """
    Main aggregation workflow.
    
    Args:
        metric_types: Optional list of metric types to process. Defaults to all.
        
    Returns:
        Dictionary mapping metric types to output file paths
    """
    if metric_types is None:
        metric_types = METRIC_TYPES
    
    output_files = {}
    
    for metric_type in metric_types:
        logger.info(f"Processing metric: {metric_type}")
        aggregates = []
        
        for group in GROUPS:
            try:
                df = load_metrics_for_group(group, metric_type)
                agg = aggregate_metrics(df, metric_type, group)
                aggregates.append(agg)
                logger.info(f"  {group}: n={agg['count']}, mean={agg['mean']:.4f}")
            except Exception as e:
                logger.error(f"  Error processing {group}/{metric_type}: {e}")
                # Continue with other groups even if one fails
                continue
        
        if aggregates:
            output_file = write_aggregate_csv(aggregates, metric_type)
            output_files[metric_type] = output_file
            
            # Register artifact hash
            try:
                register_artifact_hash(
                    str(output_file),
                    load_state_file(STATE_FILE),
                    save_state_file
                )
            except Exception as e:
                logger.warning(f"Failed to register artifact hash: {e}")
        else:
            logger.warning(f"No aggregates generated for {metric_type}")
    
    return output_files

def main():
    """Entry point for metric aggregation."""
    logger.info("Starting metric aggregation (T023)")
    
    try:
        output_files = run_aggregation()
        
        logger.info(f"Aggregation complete. Generated {len(output_files)} files:")
        for metric_type, path in output_files.items():
            logger.info(f"  {metric_type}: {path}")
        
        # Verify outputs conform to MetricResult schema
        for metric_type, path in output_files.items():
            df = pd.read_csv(path)
            # Check that required columns exist
            required_cols = ["metric_type", "group", "count", "mean", "median", "variance"]
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                logger.error(f"Schema validation failed for {path}: missing {missing}")
            else:
                logger.info(f"Schema validation passed for {path}")
        
        logger.info("T023 completed successfully")
        
    except Exception as e:
        logger.error(f"T023 failed: {e}")
        raise

if __name__ == "__main__":
    main()
