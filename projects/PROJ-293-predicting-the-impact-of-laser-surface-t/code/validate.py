import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import logging utilities from existing project files
from logging_config import get_logger, raise_on_missing_data
from seed import set_seed, ensure_seed_set

# Constants
ALPHA = 0.05
TARGET_POWER = 0.8
MIN_NORMALIZED_COUNT = 100
CRITICAL_THRESHOLD = 100  # Exit code 1 if below this
WARNING_THRESHOLD = 300   # Scope warning if below this

logger = get_logger(__name__)

def calculate_effect_size_f2(r_squared: float) -> float:
    """
    Calculate Cohen's f^2 effect size from R-squared.
    f^2 = R^2 / (1 - R^2)
    """
    if r_squared >= 1.0:
        return 1.0  # Cap to avoid division by zero
    if r_squared <= 0:
        return 0.0
    return r_squared / (1 - r_squared)

def estimate_predictors_from_data(df) -> int:
    """
    Estimate the number of predictors (features) in the dataset.
    Excludes target columns and metadata flags.
    """
    # Define columns to exclude (targets and flags)
    exclude_cols = {
        'wear_rate', 'wear_coefficient', 'normalization_method',
        'contact_load', 'sliding_speed'
    }
    
    # Count columns that are not in the exclude set
    predictors = [col for col in df.columns if col not in exclude_cols]
    # Ensure we have at least one predictor if the dataframe is not empty
    return max(len(predictors), 1)

def calculate_power_regression(n: int, k: int, f2: float = 0.15, alpha: float = ALPHA) -> float:
    """
    Approximate statistical power for multiple regression.
    Uses the non-centrality parameter lambda = f^2 * N.
    Power is approximated using the non-central F-distribution.
    
    Since scipy.stats might not be available in all environments without explicit install,
    we use a simplified approximation or require scipy.
    Given the project context, we assume scipy is available for statistical analysis.
    
    Args:
        n: Sample size (number of observations)
        k: Number of predictors
        f2: Effect size (Cohen's f^2)
        alpha: Significance level
        
    Returns:
        Power (probability of rejecting null hypothesis)
    """
    try:
        from scipy.stats import ncf, f
    except ImportError:
        raise ImportError("scipy is required for statistical power analysis. Install via: pip install scipy")

    # Degrees of freedom
    df1 = k + 1  # Numerator df (including intercept)
    df2 = n - k - 1  # Denominator df
    
    if df2 <= 0:
        return 0.0

    # Non-centrality parameter
    ncp = f2 * n
    
    # Critical F value
    f_crit = f.ppf(1 - alpha, df1, df2)
    
    # Power: Probability that F > f_crit under the alternative hypothesis
    # Power = 1 - CDF of non-central F at f_crit
    power = 1 - ncf.cdf(f_crit, df1, df2, ncp)
    
    return float(power)

def run_power_analysis(record_counts_path: str, data_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute statistical power analysis as per FR-014.
    
    1. Load record counts from T016a output.
    2. Estimate predictors (k) from data or use a default if data path is missing.
    3. Calculate power for expected effect size (default f^2 = 0.15, medium).
    4. If power < 0.8, set fallback flag.
    5. If normalized_count < 100, trigger critical halt.
    
    Args:
        record_counts_path: Path to data/processed/record_counts.json
        data_path: Optional path to the processed data to count predictors dynamically.
        
    Returns:
        Dictionary containing analysis results.
    """
    # Ensure seed is set for reproducibility if needed
    ensure_seed_set()
    
    # Load record counts
    counts_file = Path(record_counts_path)
    if not counts_file.exists():
        raise FileNotFoundError(f"Record counts file not found: {record_counts_path}")
        
    with open(counts_file, 'r') as f:
        counts_data = json.load(f)
        
    normalized_count = counts_data.get('normalized_count', 0)
    raw_count = counts_data.get('raw_count', 0)
    total_count = counts_data.get('total_count', 0)
    
    logger.info(f"Power Analysis: Total={total_count}, Normalized={normalized_count}, Raw={raw_count}")
    
    # Critical Check: SC-006 (from T016b logic, but power analysis might re-verify or add nuance)
    if normalized_count < MIN_NORMALIZED_COUNT:
        logger.critical(f"CRITICAL: Normalized count ({normalized_count}) is below minimum threshold ({MIN_NORMALIZED_COUNT}).")
        return {
            "status": "critical_failure",
            "normalized_count": normalized_count,
            "power": 0.0,
            "message": f"Data insufficient for power analysis. Count {normalized_count} < {MIN_NORMALIZED_COUNT}.",
            "exit_code": 1,
            "fallback_model": None
        }

    # Estimate predictors
    k = 0
    if data_path and Path(data_path).exists():
        import pandas as pd
        df = pd.read_csv(data_path)
        k = estimate_predictors_from_data(df)
    else:
        # Default assumption if data path not provided (e.g., standard LST features)
        # Pulse, Power, Speed, Pattern, Hardness, Modulus = 6 predictors
        k = 6
        logger.warning(f"Data path not provided for predictor estimation. Assuming k={k}.")

    # Expected effect size (Medium effect size f^2 = 0.15 is standard for social sciences/engineering explorations)
    # We can also derive this from a pilot R2 if available, but spec says "expected effect size".
    expected_f2 = 0.15 
    
    # Calculate power
    power = calculate_power_regression(
        n=normalized_count,
        k=k,
        f2=expected_f2,
        alpha=ALPHA
    )
    
    logger.info(f"Calculated Power: {power:.4f} (n={normalized_count}, k={k}, f2={expected_f2})")
    
    result = {
        "normalized_count": normalized_count,
        "raw_count": raw_count,
        "total_count": total_count,
        "num_predictors": k,
        "effect_size_f2": expected_f2,
        "alpha": ALPHA,
        "calculated_power": power,
        "power_adequate": power >= TARGET_POWER,
        "study_scope": "full_study" if normalized_count >= WARNING_THRESHOLD else "pilot_study",
        "fallback_model": None,
        "status": "success"
    }
    
    # Power Insufficiency Logic
    if power < TARGET_POWER:
        result["status"] = "power_insufficiency"
        result["message"] = f"Statistical power ({power:.4f}) is below target ({TARGET_POWER})."
        
        # Decision: Switch to Linear Regression only if power is low
        # Rationale: Complex models (RF, GBM) require more data to avoid overfitting.
        # Linear Regression is more robust with lower power/small samples.
        result["fallback_model"] = "linear_regression"
        result["recommendation"] = "Switch to Linear Regression only for this analysis due to low statistical power."
        
        logger.warning(f"Power insufficiency detected. Fallback to Linear Regression recommended.")
        
        # If power is extremely low, we might consider halting, but the spec says "switch" or "trigger warning".
        # We will trigger the warning and set the flag. The actual model training (T017a) should respect this.
        # The spec says "HALT (exit code 1) if critical". We treat < 0.8 as a warning/fallback trigger, 
        # but if it's critically low (e.g. < 0.2), we might halt. Let's stick to the spec: "switch ... OR trigger warning and HALT if critical".
        # We'll define "critical" as power < 0.2 for this implementation.
        if power < 0.2:
            result["status"] = "critical_failure"
            result["exit_code"] = 1
            result["message"] = f"Critical power insufficiency ({power:.4f}). Halting pipeline."
            return result

    return result

def main():
    """
    Main entry point for T040.
    Reads T016c output (record_counts.json) and writes reports/power_analysis.json.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    counts_path = project_root / "data" / "processed" / "record_counts.json"
    data_path = project_root / "data" / "processed" / "aggregated_clean.csv"
    output_path = project_root / "reports" / "power_analysis.json"
    
    # Ensure reports directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        result = run_power_analysis(
            record_counts_path=str(counts_path),
            data_path=str(data_path)
        )
        
        # Write output
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"Power analysis complete. Results written to {output_path}")
        
        # Handle exit codes if critical
        if result.get("exit_code") == 1:
            logger.error("Pipeline halted due to critical power insufficiency.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        # Write error result
        error_result = {
            "status": "failed",
            "error": str(e),
            "exit_code": 1
        }
        with open(output_path, 'w') as f:
            json.dump(error_result, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()