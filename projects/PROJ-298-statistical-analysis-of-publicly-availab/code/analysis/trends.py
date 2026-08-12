import os
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import random

import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import acf

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Constants ---
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
INTERMEDIATE_FILE = PROCESSED_DIR / "trend_intermediate.json"
POWER_WARNINGS_LOG = PROCESSED_DIR / "power_warnings.log"

# --- Helper Functions ---

def load_processed_data() -> Dict[str, Any]:
    """Load preprocessed tag frequency data."""
    processed_file = PROCESSED_DIR / "processed_data.json"
    if not processed_file.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_file}")
    
    with open(processed_file, 'r') as f:
        return json.load(f)

def load_top_tags() -> List[str]:
    """Load the list of top 50 tags."""
    top_tags_file = PROCESSED_DIR / "top_50_tags.json"
    if not top_tags_file.exists():
        raise FileNotFoundError(f"Top 50 tags file not found: {top_tags_file}")
    
    with open(top_tags_file, 'r') as f:
        return json.load(f)

def calculate_mann_kendall_statistic(series: np.ndarray) -> Tuple[float, float]:
    """
    Calculate the Mann-Kendall statistic (S) and its variance.
    
    Returns:
        Tuple of (S, variance)
    """
    n = len(series)
    if n < 2:
        return 0.0, 0.0
    
    S = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = series[j] - series[i]
            if diff > 0:
                S += 1
            elif diff < 0:
                S -= 1
    
    # Variance calculation with tie correction
    ties = {}
    for val in series:
        ties[val] = ties.get(val, 0) + 1
    
    tie_correction = 0
    for count in ties.values():
        if count > 1:
            tie_correction += count * (count - 1) * (2 * count + 5)
    
    var_s = (n * (n - 1) * (2 * n + 5) - tie_correction) / 18.0
    
    return S, var_s

def prewhiten_series(series: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Pre-whiten the series to remove autocorrelation.
    
    Returns:
        Tuple of (prewhitened_series, lag_1_autocorrelation)
    """
    n = len(series)
    if n < 2:
        return series, 0.0
    
    # Calculate lag-1 autocorrelation
    mean = np.mean(series)
    var = np.var(series)
    if var == 0:
        return series, 0.0
    
    lag_1_acf = np.sum((series[:-1] - mean) * (series[1:] - mean)) / ((n - 1) * var)
    
    # Pre-whiten: X_t' = X_t - rho * X_{t-1}
    # We need to handle the first element specially or drop it
    if abs(lag_1_acf) < 1e-6:
        return series, lag_1_acf
    
    prewhitened = np.zeros(n - 1)
    for t in range(1, n):
        prewhitened[t - 1] = series[t] - lag_1_acf * series[t - 1]
    
    return prewhitened, lag_1_acf

def modified_mann_kendall(series: np.ndarray) -> Tuple[float, float, float]:
    """
    Perform Modified Mann-Kendall test with pre-whitening.
    
    Returns:
        Tuple of (S, p_value, tau)
    """
    # Pre-whiten
    prewhitened, rho = prewhiten_series(series)
    
    if len(prewhitened) < 2:
        return 0.0, 1.0, 0.0
    
    # Calculate S and variance on prewhitened series
    S, var_s = calculate_mann_kendall_statistic(prewhitened)
    
    if var_s == 0:
        return S, 1.0, 0.0
    
    # Standardize S
    if S > 0:
        Z = (S - 1) / math.sqrt(var_s)
    elif S < 0:
        Z = (S + 1) / math.sqrt(var_s)
    else:
        Z = 0
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(Z)))
    
    # Calculate Kendall's Tau
    n = len(prewhitened)
    tau = S / (n * (n - 1) / 2)
    
    return S, p_value, tau

def theil_sen_slope(series: np.ndarray) -> float:
    """
    Calculate Theil-Sen slope estimator.
    
    Returns:
        Slope value
    """
    n = len(series)
    if n < 2:
        return 0.0
    
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            if j != i:
                slope = (series[j] - series[i]) / (j - i)
                slopes.append(slope)
    
    if not slopes:
        return 0.0
    
    return np.median(slopes)

def benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of adjusted q-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    
    # Calculate adjusted q-values
    q_values = [0.0] * n
    rank = 0
    prev_q = 0.0
    
    # Process in reverse order to ensure monotonicity
    for i in range(n - 1, -1, -1):
        orig_idx, p_val = sorted_p[i]
        rank = i + 1
        q = p_val * n / rank
        
        # Ensure monotonicity (q-values should be non-decreasing with rank)
        q = min(q, prev_q)
        prev_q = q
        
        q_values[orig_idx] = q
    
    # Ensure q-values are in [0, 1]
    q_values = [max(0.0, min(1.0, q)) for q in q_values]
    
    return q_values

def calculate_power_and_mdes(
    series: np.ndarray,
    slope: float,
    alpha: float = 0.05,
    target_power: float = 0.8,
    n_iterations: int = 1000,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Calculate post-hoc power and Minimum Detectable Effect Size (MDES) via Monte Carlo.
    
    This function:
    1. Estimates variance from pre-whitened residuals
    2. Injects linear trends of varying slopes into residuals
    3. Runs MK test on each synthetic series
    4. Determines slope magnitude detectable at target_power (80%) with alpha=0.05
    
    Args:
        series: Original time series
        slope: Observed Theil-Sen slope
        alpha: Significance level (default 0.05)
        target_power: Target power (default 0.8)
        n_iterations: Number of Monte Carlo iterations (default 1000)
        seed: Random seed for reproducibility (default 42)
        
    Returns:
        Tuple of (power_estimate, mdes)
    """
    random.seed(seed)
    np.random.seed(seed)
    
    if len(series) < 12:
        # Not enough data for meaningful power analysis
        return 0.0, float('inf')
    
    # Step 1: Pre-whiten and get residuals
    prewhitened, rho = prewhiten_series(series)
    
    if len(prewhitened) < 10:
        return 0.0, float('inf')
    
    # Calculate residuals (difference from mean of prewhitened series)
    mean_prewhitened = np.mean(prewhitened)
    residuals = prewhitened - mean_prewhitened
    
    # Estimate variance from residuals
    residual_variance = np.var(residuals)
    if residual_variance == 0:
        residual_variance = 1e-6  # Avoid division by zero
    
    n_points = len(prewhitened)
    time_indices = np.arange(n_points)
    
    # Step 2: Determine MDES via binary search
    # We want to find the slope magnitude where power >= target_power
    
    # Test a range of slopes
    test_slopes = np.linspace(0.0, abs(slope) * 2.0, 50)
    if abs(slope) < 1e-6:
        # If observed slope is near zero, test a reasonable range
        test_slopes = np.linspace(0.0, 1.0, 50)
    
    detected_count = 0
    powers = []
    
    for test_slope in test_slopes:
        detected = 0
        for _ in range(n_iterations):
            # Inject linear trend with this slope
            synthetic_trend = test_slope * time_indices
            # Add noise based on residual variance
            noise = np.random.normal(0, math.sqrt(residual_variance), n_points)
            synthetic_series = mean_prewhitened + synthetic_trend + noise
            
            # Run MK test on synthetic series
            _, p_val, _ = modified_mann_kendall(synthetic_series)
            
            if p_val < alpha:
                detected += 1
        
        power = detected / n_iterations
        powers.append(power)
        
        if power >= target_power:
            detected_count += 1
            break
    
    # Calculate MDES (minimum slope where power >= target_power)
    if detected_count > 0:
        # Find the first slope where power >= target_power
        mdes = test_slopes[np.argmax(np.array(powers) >= target_power)]
    else:
        # If no slope achieved target power, estimate based on extrapolation
        # Use the last tested slope as a lower bound
        mdes = test_slopes[-1]
        # Estimate how much larger it would need to be
        if powers[-1] > 0:
            # Linear extrapolation (rough estimate)
            mdes = test_slopes[-1] * (target_power / powers[-1])
        else:
            mdes = float('inf')
    
    # Step 3: Calculate power for the OBSERVED slope
    observed_power = 0.0
    detected = 0
    for _ in range(n_iterations):
        # Inject observed slope
        synthetic_trend = slope * time_indices
        noise = np.random.normal(0, math.sqrt(residual_variance), n_points)
        synthetic_series = mean_prewhitened + synthetic_trend + noise
        
        # Run MK test
        _, p_val, _ = modified_mann_kendall(synthetic_series)
        
        if p_val < alpha:
            detected += 1
    
    observed_power = detected / n_iterations
    
    return observed_power, mdes

def classify_trend(
    p_value: float,
    q_value: float,
    power: float,
    alpha: float = 0.05
) -> str:
    """
    Classify trend based on adjusted p-value (q-value) and power.
    
    Classification logic (per T014a and T014c):
    - If q_value >= alpha AND power < 0.8: "Insufficient Data"
    - If q_value >= alpha AND power >= 0.8: "Stable"
    - If q_value < alpha: "Growth" (positive slope) or "Decline" (negative slope)
    
    CRITICAL: Threshold of 0.05 applies to ADJUSTED q-values, not raw p-values.
    
    Args:
        p_value: Raw p-value from MK test
        q_value: Adjusted q-value from Benjamini-Hochberg correction
        power: Post-hoc power estimate
        alpha: Significance threshold (default 0.05)
        
    Returns:
        Classification string
    """
    # Apply Benjamini-Hochberg corrected threshold
    if q_value < alpha:
        # Significant trend - need to check slope sign
        # Note: slope sign is determined separately, this function just classifies significance
        return "Significant"
    else:
        # Not significant - check power
        if power < 0.8:
            return "Insufficient Data"
        else:
            return "Stable"

def analyze_trends() -> Dict[str, Any]:
    """
    Main function to analyze trends for all top tags.
    
    Returns:
        Dictionary containing trend analysis results
    """
    logger.info("Loading processed data...")
    data = load_processed_data()
    top_tags = load_top_tags()
    
    results = []
    warnings = []
    raw_p_values = []
    
    logger.info(f"Analyzing {len(top_tags)} top tags...")
    
    for tag in top_tags:
        if tag not in data:
            logger.warning(f"Tag {tag} not found in processed data, skipping.")
            continue
        
        series = np.array(data[tag])
        
        if len(series) < 12:
            logger.warning(f"Tag {tag} has less than 12 months of data, skipping.")
            continue
        
        # Perform Modified Mann-Kendall test
        S, p_value, tau = modified_mann_kendall(series)
        raw_p_values.append(p_value)
        
        # Calculate Theil-Sen slope
        slope = theil_sen_slope(series)
        
        # Store for later classification
        results.append({
            "tag": tag,
            "slope": slope,
            "tau": tau,
            "raw_p_value": p_value,
            "S": S,
            "series_length": len(series)
        })
    
    # Apply Benjamini-Hochberg correction
    logger.info("Applying Benjamini-Hochberg correction...")
    if raw_p_values:
        q_values = benjamini_hochberg_correction(raw_p_values)
    else:
        q_values = []
    
    # Log raw vs adjusted for first 5 tags (per T052 requirement)
    logger.info("Benjamini-Hochberg correction debug (first 5 tags):")
    for i in range(min(5, len(results))):
        logger.info(f"  Tag: {results[i]['tag']}, Raw p: {results[i]['raw_p_value']:.4f}, Adjusted q: {q_values[i]:.4f}")
    
    # Calculate power and MDES for each tag, then classify
    logger.info("Calculating power and MDES...")
    for i, result in enumerate(results):
        tag = result["tag"]
        slope = result["slope"]
        p_value = result["raw_p_value"]
        q_value = q_values[i] if i < len(q_values) else 1.0
        
        # Calculate power and MDES
        power, mdes = calculate_power_and_mdes(
            np.array(data[tag]),
            slope,
            alpha=0.05,
            target_power=0.8,
            n_iterations=1000,
            seed=42
        )
        
        result["power"] = power
        result["mDES"] = mdes
        result["q_value"] = q_value
        
        # Classify trend
        classification = classify_trend(p_value, q_value, power)
        
        # CRITICAL: If power < 0.5, flag and re-classify as "Insufficient Data"
        # regardless of p-value (per T014c requirement)
        if power < 0.5:
            classification = "Insufficient Data"
            warnings.append({
                "tag": tag,
                "power": power,
                "reason": "Post-hoc power < 0.5"
            })
            logger.warning(f"Tag {tag} has low power ({power:.2f}), re-classified as 'Insufficient Data'")
        
        # If significant, determine growth/decline based on slope sign
        if classification == "Significant":
            if slope > 0:
                classification = "Growth"
            elif slope < 0:
                classification = "Decline"
            else:
                classification = "Stable"  # Zero slope but significant (rare)
        
        result["classification"] = classification
    
    # Write power warnings to log file
    if warnings:
        with open(POWER_WARNINGS_LOG, 'w') as f:
            for warning in warnings:
                f.write(json.dumps(warning) + '\n')
        logger.info(f"Wrote {len(warnings)} power warnings to {POWER_WARNINGS_LOG}")
    
    # Prepare final results
    final_results = {
        "analysis_date": str(Path.cwd()),
        "total_tags_analyzed": len(results),
        "tags_with_insufficient_power": len([r for r in results if r.get("power", 0) < 0.5]),
        "results": results
    }
    
    return final_results

def save_results(results: Dict[str, Any], output_path: Path = INTERMEDIATE_FILE):
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for trend analysis."""
    logger.info("Starting trend analysis with post-hoc power analysis...")
    
    try:
        results = analyze_trends()
        save_results(results)
        
        # Summary
        classifications = {}
        for r in results["results"]:
            cls = r["classification"]
            classifications[cls] = classifications.get(cls, 0) + 1
        
        logger.info("Analysis complete. Summary:")
        for cls, count in classifications.items():
            logger.info(f"  {cls}: {count}")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()