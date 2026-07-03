import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.power as smp

from config import get_config
from utils.logging import get_logger

def get_logger_wrapper(logger_name: str = "posthoc_power"):
    return get_logger(logger_name)

def load_processed_features(config: Any) -> Optional[pd.DataFrame]:
    """
    Loads the processed features from data/processed/features.csv.
    Returns None if file does not exist or is empty.
    """
    logger = get_logger("posthoc_power")
    data_path = config.get("paths", {}).get("processed_features")
    if not data_path:
        # Fallback to standard path if config missing
        data_path = Path("data/processed/features.csv")
    else:
        data_path = Path(data_path)

    if not data_path.exists():
        logger.error(f"Processed features file not found: {data_path}")
        return None

    try:
        df = pd.read_csv(data_path)
        if df.empty:
            logger.warning("Processed features file is empty.")
            return None
        logger.info(f"Loaded {len(df)} records from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading processed features: {e}")
        return None

def calculate_posthoc_power(
    n: int,
    effect_size: float,
    alpha: float = 0.05,
    alternative: str = "two-sided"
) -> float:
    """
    Calculates post-hoc power given sample size (n), effect size (Cohen's d),
    and significance level (alpha).
    Uses TTestIndPower for independent samples or TTestPower for single sample/paired.
    Given the context of LMM, we approximate using TTestPower for the fixed effect.
    """
    logger = get_logger("posthoc_power")
    
    if n <= 0:
        logger.error("Sample size must be positive.")
        return 0.0
    if effect_size == 0:
        return alpha # Power equals alpha when effect is 0

    try:
        # Using TTestPower for a general approximation of power given d
        analysis = smp.TTestPower()
        power = analysis.solve_power(
            effect_size=effect_size,
            nobs1=n,
            alpha=alpha,
            power=None,
            alternative=alternative
        )
        return float(power)
    except Exception as e:
        logger.error(f"Error calculating power: {e}")
        return 0.0

def estimate_effect_size_from_data(df: pd.DataFrame, outcome_col: str, predictor_col: str) -> Optional[float]:
    """
    Estimates Cohen's d (effect size) from the data.
    Assumes a continuous predictor or binary grouping.
    If predictor is continuous, we calculate the correlation and convert to r, then to d,
    or perform a simple t-test if we bin the predictor (not ideal but a fallback).
    
    Better approach for continuous predictor in LMM context:
    Use the standardized beta coefficient if available, or approximate via correlation.
    Here we calculate Pearson correlation r and convert to d: d = 2r / sqrt(1-r^2).
    """
    logger = get_logger("posthoc_power")
    
    if outcome_col not in df.columns or predictor_col not in df.columns:
        logger.error(f"Columns {outcome_col} or {predictor_col} not found.")
        return None

    valid_data = df[[outcome_col, predictor_col]].dropna()
    if len(valid_data) < 3:
        logger.warning("Insufficient data to estimate effect size.")
        return None

    r, p_val = stats.pearsonr(valid_data[outcome_col], valid_data[predictor_col])
    
    # Convert r to Cohen's d
    # d = 2r / sqrt(1 - r^2)
    if abs(r) >= 1.0:
        # Edge case: perfect correlation
        d = float('inf') if r > 0 else float('-inf')
    else:
        d = (2 * r) / np.sqrt(1 - (r ** 2))
    
    logger.info(f"Estimated effect size (d) from correlation: {d:.4f} (r={r:.4f})")
    return d

def run_posthoc_power_analysis(
    config: Any,
    outcome_col: str = "detection_time",
    predictor_col: str = "fixation_ratio",
    alpha: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Runs the post-hoc power analysis.
    1. Loads processed features.
    2. Estimates effect size from the data (Cohen's d).
    3. Calculates power based on observed N and estimated d.
    4. Documents if power < 0.80.
    """
    logger = get_logger("posthoc_power")
    logger.info("Starting post-hoc power analysis.")

    df = load_processed_features(config)
    if df is None:
        logger.error("Could not load data for power analysis.")
        return {"status": "error", "message": "Data loading failed"}

    n = len(df)
    effect_size = estimate_effect_size_from_data(df, outcome_col, predictor_col)

    if effect_size is None or not np.isfinite(effect_size):
        logger.error("Could not estimate valid effect size.")
        return {"status": "error", "message": "Effect size estimation failed"}

    power = calculate_posthoc_power(n, abs(effect_size), alpha)

    result = {
        "status": "success",
        "sample_size": n,
        "estimated_effect_size_d": effect_size,
        "alpha": alpha,
        "calculated_power": power,
        "target_power": target_power,
        "power_adequate": power >= target_power,
        "note": "Power calculated based on observed effect size (r converted to d) and sample size."
    }

    if power < target_power:
        logger.warning(f"Post-hoc power ({power:.4f}) is below target ({target_power}).")
        result["warning"] = f"Power ({power:.4f}) is below the target of {target_power}. Results should be interpreted with caution."
    else:
        logger.info(f"Post-hoc power ({power:.4f}) meets the target of {target_power}.")

    return result

def save_posthoc_report(result: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the post-hoc power analysis result to a JSON file.
    """
    logger = get_logger("posthoc_power")
    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Post-hoc power report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        raise

def main():
    """
    Main entry point for the post-hoc power analysis task.
    """
    logger = get_logger("posthoc_power")
    logger.info("Executing T033: Post-hoc Power Analysis")
    
    config = get_config()
    output_dir = Path(config.get("paths", {}).get("results", "results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "posthoc_power_analysis.json"

    result = run_posthoc_power_analysis(config)
    
    if result["status"] == "success":
        save_posthoc_report(result, output_file)
        logger.info("T033 completed successfully.")
    else:
        logger.error(f"T033 failed: {result.get('message', 'Unknown error')}")
        # Write error state to file so pipeline can detect failure
        save_posthoc_report(result, output_file)
        sys.exit(1)

if __name__ == "__main__":
    main()
