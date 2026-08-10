"""
code/analysis/trends.py

Implements Modified Mann-Kendall test, Theil-Sen slope estimation,
Benjamini-Hochberg correction, and trend classification for tag frequency time series.
"""
import os
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/processed/trends_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ALPHA = 0.05
MIN_DATA_POINTS = 12
SEED = 42

def calculate_mann_kendall_statistic(series: List[float]) -> Tuple[float, float]:
    """
    Calculate the Mann-Kendall statistic S and the variance of S.
    
    Args:
        series: List of time series values.
        
    Returns:
        Tuple of (S, var_S)
    """
    n = len(series)
    S = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = series[j] - series[i]
            if diff > 0:
                S += 1
            elif diff < 0:
                S -= 1
    
    # Calculate variance with tie correction
    var_S = 0
    ties = defaultdict(int)
    for val in series:
        ties[val] += 1
    
    sum_ties = 0
    for count in ties.values():
        if count > 1:
            sum_ties += count * (count - 1) * (2 * count + 5)
    
    var_S = (n * (n - 1) * (2 * n + 5) - sum_ties) / 18
    
    return S, var_S

def prewhiten_series(series: List[float]) -> List[float]:
    """
    Pre-whiten the series to remove autocorrelation.
    Uses lag-1 autocorrelation to remove trend.
    
    Args:
        series: List of time series values.
        
    Returns:
        Pre-whitened series.
    """
    n = len(series)
    if n < 2:
        return series
    
    # Calculate lag-1 autocorrelation
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / n
    if var == 0:
        return series
    
    cov_lag1 = sum((series[i] - mean) * (series[i+1] - mean) for i in range(n-1)) / n
    rho1 = cov_lag1 / var
    
    if abs(rho1) < 1e-6:
        return series
    
    # Remove trend
    prewhitened = []
    for i in range(n):
        if i == 0:
            prewhitened.append(series[i])
        else:
            prewhitened.append(series[i] - rho1 * (series[i-1] - mean))
    
    return prewhitened

def modified_mann_kendall(series: List[float]) -> Tuple[float, float]:
    """
    Perform Modified Mann-Kendall test with pre-whitening.
    
    Args:
        series: List of time series values.
        
    Returns:
        Tuple of (S, p_value)
    """
    # Pre-whiten the series
    prewhitened = prewhiten_series(series)
    
    # Calculate S and variance
    S, var_S = calculate_mann_kendall_statistic(prewhitened)
    
    if var_S == 0:
        return S, 1.0
    
    # Calculate Z statistic
    if S > 0:
        Z = (S - 1) / math.sqrt(var_S)
    elif S < 0:
        Z = (S + 1) / math.sqrt(var_S)
    else:
        Z = 0
    
    # Calculate p-value (two-tailed)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(Z) / math.sqrt(2))))
    
    return S, p_value

def theil_sen_slope(series: List[float]) -> float:
    """
    Calculate Theil-Sen slope estimator.
    
    Args:
        series: List of time series values.
        
    Returns:
        Slope estimate.
    """
    n = len(series)
    slopes = []
    
    for i in range(n - 1):
        for j in range(i + 1, n):
            if j != i:
                slope = (series[j] - series[i]) / (j - i)
                slopes.append(slope)
    
    if not slopes:
        return 0.0
    
    # Sort and find median
    slopes.sort()
    mid = len(slopes) // 2
    if len(slopes) % 2 == 0:
        return (slopes[mid - 1] + slopes[mid]) / 2
    else:
        return slopes[mid]

def calculate_power_and_mdes(slopes: List[float], series_length: int, 
                             alpha: float = 0.05, power_target: float = 0.8,
                             n_iterations: int = 1000) -> Tuple[float, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES) via Monte Carlo.
    
    Args:
        slopes: List of observed slopes for reference.
        series_length: Length of the time series.
        alpha: Significance level.
        power_target: Target power (default 0.8).
        n_iterations: Number of Monte Carlo iterations.
        
    Returns:
        Tuple of (estimated_power, mdes)
    """
    if not slopes:
        return 0.0, float('inf')
    
    # Estimate variance from residuals (simplified)
    mean_slope = sum(slopes) / len(slopes)
    variance = sum((s - mean_slope) ** 2 for s in slopes) / len(slopes)
    if variance == 0:
        variance = 1e-6
    
    std_dev = math.sqrt(variance)
    
    # Find MDES: smallest slope detectable with target power
    # Using simplified power calculation for linear trend
    # Power = 1 - beta, where beta is Type II error rate
    # For a given slope, we simulate and count rejections
    
    # Binary search for MDES
    low, high = 0.0, abs(mean_slope) * 10 if mean_slope != 0 else 1.0
    mdes = high
    
    for _ in range(20):  # Binary search iterations
        mid = (low + high) / 2
        if mid == 0:
            mid = 1e-6
        
        # Simulate power at this slope
        rejections = 0
        for _ in range(n_iterations):
            # Generate synthetic series with this slope
            synthetic_series = []
            for t in range(series_length):
                noise = std_dev * (2 * (hash(str(_) + str(t)) % 1000) / 1000 - 1)
                synthetic_series.append(mid * t + noise)
            
            # Test if we can detect this slope
            _, p_val = modified_mann_kendall(synthetic_series)
            if p_val < alpha:
                rejections += 1
        
        observed_power = rejections / n_iterations
        
        if observed_power >= power_target:
            mdes = mid
            high = mid
        else:
            low = mid
    
    # Calculate actual power at observed mean slope
    rejections = 0
    for _ in range(n_iterations):
        synthetic_series = []
        for t in range(series_length):
            noise = std_dev * (2 * (hash(str(_) + str(t)) % 1000) / 1000 - 1)
            synthetic_series.append(mean_slope * t + noise)
        
        _, p_val = modified_mann_kendall(synthetic_series)
        if p_val < alpha:
            rejections += 1
    
    actual_power = rejections / n_iterations
    
    return actual_power, mdes

def benjamini_hochberg_correction(p_values: List[float], tag_names: List[str]) -> List[Tuple[str, float, float]]:
    """
    Apply Benjamini-Hochberg correction to control False Discovery Rate.
    
    MUST: Log raw p-values vs adjusted q-values for the first 5 tags.
    
    Args:
        p_values: List of raw p-values.
        tag_names: List of corresponding tag names.
        
    Returns:
        List of tuples (tag_name, raw_p, adjusted_q)
    """
    if not p_values:
        return []
    
    n = len(p_values)
    indexed_p = sorted([(i, p) for i, p in enumerate(p_values)], key=lambda x: x[1])
    
    adjusted_q = [0.0] * n
    min_q = 1.0
    
    # Calculate adjusted q-values (working backwards)
    for rank in range(n - 1, -1, -1):
        i, p = indexed_p[rank]
        q = p * n / (rank + 1)
        min_q = min(min_q, q)
        adjusted_q[i] = min_q
    
    # Ensure q-values don't exceed 1.0
    adjusted_q = [min(q, 1.0) for q in adjusted_q]
    
    # Log the first 5 tags for verification (as required by T052)
    logger.info("=" * 60)
    logger.info("BENJAMINI-HOCHBERG CORRECTION VERIFICATION (First 5 Tags)")
    logger.info("=" * 60)
    logger.info(f"{'Tag Name':<20} {'Raw P-value':<15} {'Adjusted Q-value':<15}")
    logger.info("-" * 60)
    
    for i in range(min(5, len(tag_names))):
        tag = tag_names[i]
        raw_p = p_values[i]
        adj_q = adjusted_q[i]
        logger.info(f"{tag:<20} {raw_p:<15.6f} {adj_q:<15.6f}")
    
    logger.info("=" * 60)
    
    # Return results
    results = []
    for i, tag in enumerate(tag_names):
        results.append((tag, p_values[i], adjusted_q[i]))
    
    return results

def classify_trend(raw_p: float, adjusted_q: float, power: float, alpha: float = 0.05) -> str:
    """
    Classify trend based on p-value, adjusted q-value, and power.
    
    CRITICAL: The threshold of 0.05 MUST be applied to the *adjusted* p-values (q-values).
    
    Args:
        raw_p: Raw p-value from Mann-Kendall test.
        adjusted_q: Adjusted q-value from Benjamini-Hochberg correction.
        power: Statistical power estimate.
        alpha: Significance level (default 0.05).
        
    Returns:
        Classification string: "Growth", "Decline", "Stable", or "Insufficient Data"
    """
    if adjusted_q >= alpha:
        if power < 0.8:
            return "Insufficient Data"
        else:
            return "Stable"
    else:
        # Significant trend - need direction from Theil-Sen slope
        # This function is called after slope calculation in main flow
        return "Significant"  # Direction determined by slope sign

def analyze_trends(processed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to analyze trends for all tags.
    
    Args:
        processed_data: Dictionary containing tag time series data.
        
    Returns:
        Dictionary containing trend analysis results.
    """
    results = {
        "tags": [],
        "summary": {
            "total_tags": 0,
            "growth": 0,
            "decline": 0,
            "stable": 0,
            "insufficient_data": 0
        }
    }
    
    tag_names = []
    p_values = []
    slopes = []
    trend_data = []
    
    logger.info("Starting trend analysis for all tags...")
    
    for tag_name, data in processed_data.items():
        series = data.get("monthly_frequencies", [])
        
        if len(series) < MIN_DATA_POINTS:
            logger.warning(f"Tag '{tag_name}' has insufficient data points ({len(series)} < {MIN_DATA_POINTS})")
            trend_data.append({
                "tag": tag_name,
                "classification": "Insufficient Data",
                "reason": "Less than 12 months of data"
            })
            continue
        
        # Perform Mann-Kendall test
        S, p_val = modified_mann_kendall(series)
        
        # Calculate Theil-Sen slope
        slope = theil_sen_slope(series)
        
        # Calculate power and MDES
        power, mdes = calculate_power_and_mdes([slope], len(series))
        
        tag_names.append(tag_name)
        p_values.append(p_val)
        slopes.append(slope)
        
        trend_data.append({
            "tag": tag_name,
            "raw_p_value": p_val,
            "slope": slope,
            "series_length": len(series),
            "power": power,
            "mdes": mdes
        })
    
    # Apply Benjamini-Hochberg correction
    logger.info("Applying Benjamini-Hochberg correction...")
    corrected_results = benjamini_hochberg_correction(p_values, tag_names)
    
    # Final classification
    for i, (tag, raw_p, adjusted_q) in enumerate(corrected_results):
        slope = slopes[i]
        power = trend_data[i]["power"]
        mdes = trend_data[i]["mdes"]
        
        if adjusted_q >= ALPHA:
            if power < 0.8:
                classification = "Insufficient Data"
                results["summary"]["insufficient_data"] += 1
            else:
                classification = "Stable"
                results["summary"]["stable"] += 1
        else:
            if slope > 0:
                classification = "Growth"
                results["summary"]["growth"] += 1
            else:
                classification = "Decline"
                results["summary"]["decline"] += 1
        
        results["tags"].append({
            "tag": tag,
            "classification": classification,
            "raw_p_value": raw_p,
            "adjusted_q_value": adjusted_q,
            "theil_sen_slope": slope,
            "power": power,
            "mdes": mdes,
            "series_length": trend_data[i]["series_length"]
        })
    
    results["summary"]["total_tags"] = len(results["tags"])
    
    logger.info(f"Trend analysis complete. Processed {results['summary']['total_tags']} tags.")
    logger.info(f"Growth: {results['summary']['growth']}, Decline: {results['summary']['decline']}, "
               f"Stable: {results['summary']['stable']}, Insufficient Data: {results['summary']['insufficient_data']}")
    
    return results

def load_processed_data(input_path: str) -> Dict[str, Any]:
    """
    Load processed tag frequency data.
    
    Args:
        input_path: Path to the processed data JSON file.
        
    Returns:
        Dictionary containing tag time series data.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save trend analysis results to JSON file.
    
    Args:
        results: Dictionary containing trend analysis results.
        output_path: Path to save the results.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for trend analysis.
    """
    # Define paths
    input_path = "data/processed/tag_frequency_data.json"
    output_path = "data/processed/trend_intermediate.json"
    
    try:
        # Load processed data
        logger.info(f"Loading processed data from {input_path}")
        processed_data = load_processed_data(input_path)
        
        # Perform trend analysis
        logger.info("Starting trend analysis...")
        results = analyze_trends(processed_data)
        
        # Save results
        save_results(results, output_path)
        
        logger.info("Trend analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()