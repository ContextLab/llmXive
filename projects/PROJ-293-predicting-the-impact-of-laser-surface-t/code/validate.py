import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import existing utilities
from seed import set_seed
from logging_config import get_logger, raise_on_missing_data

# Configure logger
logger = get_logger(__name__)

def calculate_effect_size_f2(predictors: int, r_squared: float = 0.15) -> float:
    """
    Calculate Cohen's f^2 effect size.
    
    Args:
        predictors: Number of predictor variables in the model.
        r_squared: Expected R-squared value (default 0.15 for medium effect).
        
    Returns:
        f2: Cohen's f^2 effect size.
    """
    if r_squared >= 1.0:
        raise ValueError("R-squared must be less than 1.0")
    f2 = r_squared / (1 - r_squared)
    return f2

def calculate_power_regression(
    sample_size: int,
    predictors: int,
    f2: float,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for a multiple regression F-test.
    
    Uses the non-central F-distribution to approximate power.
    
    Args:
        sample_size: Number of observations (n).
        predictors: Number of predictors (k).
        f2: Cohen's f^2 effect size.
        alpha: Significance level (default 0.05).
        
    Returns:
        power: Statistical power (probability of rejecting null hypothesis).
    """
    if sample_size <= predictors:
        logger.warning(f"Sample size ({sample_size}) must be greater than predictors ({predictors}). Returning 0.0 power.")
        return 0.0
    
    df1 = predictors
    df2 = sample_size - predictors - 1
    if df2 <= 0:
        logger.warning(f"Degrees of freedom for error (df2) is non-positive. Returning 0.0 power.")
        return 0.0
    
    # Non-centrality parameter lambda = f^2 * N
    ncp = f2 * sample_size
    
    # Critical F value
    f_crit = stats.f.ppf(1 - alpha, df1, df2)
    
    # Power is the probability that the non-central F statistic exceeds f_crit
    power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
    
    return float(power)

def estimate_predictors_from_data(df: pd.DataFrame, target_col: str = 'wear_rate') -> int:
    """
    Estimate the number of predictors to be used in the model.
    
    Counts numeric columns excluding the target and known normalization flags.
    
    Args:
        df: The processed DataFrame.
        target_col: The name of the target variable column.
        
    Returns:
        num_predictors: Estimated count of predictor features.
    """
    # Define columns to exclude from feature count
    exclude_cols = {target_col, 'normalization_method', 'source_id', 'material_class'}
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    predictors = [c for c in numeric_cols if c not in exclude_cols]
    
    # If we have categorical columns that will be one-hot encoded, estimate expansion
    # For simplicity in this count, we assume the pipeline will handle encoding,
    # but for power analysis we need the final count.
    # We'll conservatively count numeric + unique categories for string columns.
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    for col in categorical_cols:
        if col in exclude_cols:
            continue
        unique_count = df[col].nunique()
        # One-hot encoding adds (unique - 1) features usually
        predictors.append(f"cat_{col}_{unique_count-1}")
    
    return len(predictors)

def run_power_analysis(
    data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    expected_r_squared: float = 0.15,
    alpha: float = 0.05,
    min_power_threshold: float = 0.80
) -> Dict[str, Any]:
    """
    Execute statistical power analysis for the regression model.
    
    Reads the normalized dataset, estimates predictors, calculates power,
    and determines if the study scope is sufficient.
    
    Args:
        data_path: Path to the normalized dataset (default: data/processed/normalized_only.csv).
        output_path: Path for the output JSON (default: reports/power_analysis.json).
        expected_r_squared: Expected R-squared for effect size calculation.
        alpha: Significance level.
        min_power_threshold: Minimum acceptable power.
        
    Returns:
        result: Dictionary containing analysis results and flags.
    """
    # Set seed for reproducibility
    set_seed()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent
    if data_path is None:
        data_path = project_root / "data" / "processed" / "normalized_only.csv"
    else:
        data_path = Path(data_path)
        
    if output_path is None:
        output_path = project_root / "reports" / "power_analysis.json"
    else:
        output_path = Path(output_path)
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {data_path} for power analysis...")
    if not data_path.exists():
        raise FileNotFoundError(f"Required data file not found: {data_path}. "
                                "Ensure T014 (split_dataset) has run successfully.")
        
    df = pd.read_csv(data_path)
    
    # Estimate predictors
    num_predictors = estimate_predictors_from_data(df)
    sample_size = len(df)
    
    logger.info(f"Sample size: {sample_size}, Estimated predictors: {num_predictors}")
    
    if sample_size <= num_predictors:
        logger.error(f"Sample size ({sample_size}) is not greater than predictors ({num_predictors}). "
                     "Power analysis cannot be performed.")
        result = {
            "status": "failed",
            "reason": "sample_size_too_small",
            "sample_size": sample_size,
            "predictors": num_predictors
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)
    
    # Calculate effect size
    f2 = calculate_effect_size_f2(num_predictors, expected_r_squared)
    
    # Calculate power
    power = calculate_power_regression(sample_size, num_predictors, f2, alpha)
    
    logger.info(f"Calculated power: {power:.4f} (Threshold: {min_power_threshold})")
    
    # Determine status
    is_sufficient = power >= min_power_threshold
    status = "sufficient" if is_sufficient else "insufficient"
    
    # Determine action
    action = "proceed"
    if not is_sufficient:
        # Per task description: if power < 0.8, switch to Linear Regression only or HALT
        # We flag for the pipeline to handle this decision
        action = "switch_to_linear_regression_or_halt"
        
    result = {
        "status": status,
        "power": power,
        "alpha": alpha,
        "expected_r_squared": expected_r_squared,
        "effect_size_f2": f2,
        "sample_size": sample_size,
        "num_predictors": num_predictors,
        "min_power_threshold": min_power_threshold,
        "action_required": action,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis results written to {output_path}")
    
    # If power is insufficient and critical, we might halt
    # The task says: "trigger power_insufficiency warning and HALT (exit code 1) if critical"
    # We assume power < 0.5 is critical for this implementation
    if power < 0.5:
        logger.critical(f"Power is critically low ({power:.4f}). Halting execution.")
        sys.exit(1)
        
    return result

def main():
    """Entry point for the power analysis script."""
    try:
        result = run_power_analysis()
        logger.info(f"Power analysis completed. Status: {result['status']}")
        if result['status'] == 'insufficient':
            logger.warning(f"Power insufficiency detected. Action: {result['action_required']}")
            # We do not exit here unless critical, allowing the pipeline to decide
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
