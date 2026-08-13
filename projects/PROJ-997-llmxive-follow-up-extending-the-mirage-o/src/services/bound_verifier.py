"""
Bound verification service for T031.

Verifies the theoretical bound |predicted - actual| < 0.1 separately for
INT4, INT8, and FP8 quantization levels.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.config.logging_config import setup_logger
from src.config.env_config import load_config

logger = setup_logger("bound_verifier")

BOUND_THRESHOLD = 0.1
OUTPUT_PATH = Path("data/processed/consistency_report.json")

def verify_bound_for_level(df: pd.DataFrame, level: str) -> Dict[str, Any]:
    """
    Verify the bound |predicted - actual| < 0.1 for a specific quantization level.

    Args:
        df: DataFrame containing the dataset with columns 'predicted_gap' and 'actual_gap'.
        level: The quantization level to filter by (e.g., 'INT4', 'INT8', 'FP8').

    Returns:
        Dictionary with statistics for this level.
    """
    if level not in df['quantization_level'].values:
        logger.warning(f"Level '{level}' not found in dataset. Skipping.")
        return {
            "level": level,
            "total_samples": 0,
            "samples_satisfying_bound": 0,
            "percentage_satisfying": 0.0,
            "mean_absolute_error": None,
            "status": "skipped"
        }

    subset = df[df['quantization_level'] == level]
    total_samples = len(subset)

    if total_samples == 0:
        return {
            "level": level,
            "total_samples": 0,
            "samples_satisfying_bound": 0,
            "percentage_satisfying": 0.0,
            "mean_absolute_error": None,
            "status": "empty"
        }

    # Calculate absolute difference
    abs_diff = np.abs(subset['predicted_gap'] - subset['actual_gap'])
    satisfies_bound = abs_diff < BOUND_THRESHOLD
    count_satisfying = satisfies_bound.sum()
    percentage = (count_satisfying / total_samples) * 100.0

    mae = abs_diff.mean()

    logger.info(f"Level {level}: {count_satisfying}/{total_samples} samples satisfy bound "
                f"(threshold={BOUND_THRESHOLD}), MAE={mae:.4f}")

    return {
        "level": level,
        "total_samples": int(total_samples),
        "samples_satisfying_bound": int(count_satisfying),
        "percentage_satisfying": float(percentage),
        "mean_absolute_error": float(mae),
        "status": "verified"
    }

def run_bound_verification(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point to run bound verification.

    Loads the processed dataset, verifies bounds per level, aggregates results,
    and writes the consistency report.

    Args:
        input_path: Path to the input parquet file (defaults to data/processed/training_sample.parquet).
        output_path: Path to write the JSON report (defaults to data/processed/consistency_report.json).

    Returns:
        The generated report dictionary.
    """
    if input_path is None:
        input_path = Path("data/processed/training_sample.parquet")
    if output_path is None:
        output_path = OUTPUT_PATH

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T015 (generate_dataset.py) has been run successfully."
        )

    logger.info(f"Loading dataset from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

    # Ensure required columns exist
    required_cols = ['predicted_gap', 'actual_gap', 'quantization_level']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    levels = ["INT4", "INT8", "FP8"]
    level_results = []
    total_satisfying = 0
    total_samples = 0

    for level in levels:
        result = verify_bound_for_level(df, level)
        level_results.append(result)
        if result['status'] != 'skipped':
            total_satisfying += result['samples_satisfying_bound']
            total_samples += result['total_samples']

    overall_percentage = 0.0
    if total_samples > 0:
        overall_percentage = (total_satisfying / total_samples) * 100.0

    report = {
        "bound_threshold": BOUND_THRESHOLD,
        "total_samples_analyzed": total_samples,
        "total_samples_satisfying_bound": total_satisfying,
        "overall_percentage_satisfying": float(overall_percentage),
        "level_breakdown": level_results,
        "status": "completed"
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing consistency report to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Bound verification complete. Overall satisfaction: {overall_percentage:.2f}%")
    return report

def main():
    """CLI entry point for bound verification."""
    logger.info("Starting bound verification (T031)...")
    try:
        report = run_bound_verification()
        print(json.dumps(report, indent=2))
    except Exception as e:
        logger.error(f"Bound verification failed: {e}")
        raise

if __name__ == "__main__":
    main()
