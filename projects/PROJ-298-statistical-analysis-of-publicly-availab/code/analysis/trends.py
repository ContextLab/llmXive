"""
Trend Analysis Module for Stack Overflow Tag Statistics.

Implements Modified Mann-Kendall test with pre-whitening, Theil-Sen slope estimation,
Benjamini-Hochberg FDR correction, and post-hoc power analysis (MDES) for time series data.
"""

import os
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm
from statsmodels.tsa.stattools import acf

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUT_DIR = PROJECT_ROOT / "data"

def calculate_mann_kendall_statistic(x: np.ndarray) -> Tuple[float, float, float]:
    """
    Calculate the Mann-Kendall statistic S, variance, and standardized Z-score.
    
    Args:
        x: Time series data (numpy array).
        
    Returns:
        Tuple of (S, var_S, Z).
    """
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    # Calculate S
    S = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            S += np.sign(x[j] - x[i])

    # Calculate Variance of S
    # Handling ties
    ties = 0
    unique_vals, counts = np.unique(x, return_counts=True)
    for count in counts:
        if count > 1:
            ties += count * (count - 1) * (2 * count + 5)
    
    var_S = (n * (n - 1) * (2 * n + 5) - ties) / 18.0

    if var_S <= 0:
        return 0.0, 0.0, 0.0

    # Calculate Z
    if S > 0:
        Z = (S - 1) / math.sqrt(var_S)
    elif S < 0:
        Z = (S + 1) / math.sqrt(var_S)
    else:
        Z = 0.0

    return S, var_S, Z

def prewhiten_series(x: np.ndarray) -> np.ndarray:
    """
    Pre-whiten the time series by removing lag-1 autocorrelation.
    Implements the Modified Mann-Kendall pre-whitening step.
    
    Args:
        x: Original time series.
        
    Returns:
        Pre-whitened time series.
    """
    n = len(x)
    if n < 3:
        return x

    # Estimate lag-1 autocorrelation coefficient (rho)
    # Using the formula: rho = (sum((x_t - mean)(x_{t-1} - mean))) / (sum((x_t - mean)^2))
    x_centered = x - np.mean(x)
    numerator = np.sum(x_centered[:-1] * x_centered[1:])
    denominator = np.sum(x_centered[:-1] ** 2)
    
    if denominator == 0:
        return x
        
    rho = numerator / denominator
    
    # If autocorrelation is negligible, return original
    if abs(rho) < 1e-6:
        return x

    # Pre-whiten: x'_t = (x_t - rho * x_{t-1}) / sqrt(1 - rho^2)
    # This preserves the trend while removing serial correlation
    pre_whitened = np.zeros(n)
    pre_whitened[0] = x[0] # First point remains same (or can be handled differently)
    
    for t in range(1, n):
        pre_whitened[t] = (x[t] - rho * x[t-1]) / math.sqrt(1 - rho**2)
        
    return pre_whitened

def modified_mann_kendall(x: np.ndarray) -> Tuple[float, float, float]:
    """
    Perform Modified Mann-Kendall test with pre-whitening.
    
    Args:
        x: Time series data.
        
    Returns:
        Tuple of (Z, p_value, S).
    """
    # Pre-whiten
    x_prime = prewhiten_series(x)
    
    # Calculate MK statistic on pre-whitened series
    S, var_S, Z = calculate_mann_kendall_statistic(x_prime)
    
    if var_S == 0:
        p_value = 1.0
    else:
        p_value = 2 * (1 - norm.cdf(abs(Z)))
        
    return Z, p_value, S

def theil_sen_slope(x: np.ndarray, t: np.ndarray) -> float:
    """
    Calculate Theil-Sen slope estimator.
    
    Args:
        x: Dependent variable (frequencies).
        t: Independent variable (time indices).
        
    Returns:
        Slope estimate.
    """
    n = len(x)
    if n < 2:
        return 0.0
        
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            if t[j] != t[i]:
                slope = (x[j] - x[i]) / (t[j] - t[i])
                slopes.append(slope)
                
    if not slopes:
        return 0.0
        
    return float(np.median(slopes))

def calculate_power_and_mdes(n: int, alpha: float = 0.05, effect_size: float = 0.5) -> Tuple[float, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    Uses a simplified approximation based on the Mann-Kendall variance.
    
    Args:
        n: Sample size (number of time points).
        alpha: Significance level.
        effect_size: Assumed effect size for power calculation.
        
    Returns:
        Tuple of (power, mdes).
    """
    # Approximation: Power depends on Z_alpha and Z_beta
    # Z_beta = sqrt(n) * effect_size / sigma - Z_alpha
    # We assume a standard deviation of 1 for the normalized statistic
    
    z_alpha = norm.ppf(1 - alpha/2)
    
    # Calculate Z_beta
    # For MK test, the variance of S is approx n(n-1)(2n+5)/18
    # The standardized Z is S / sqrt(var)
    # Power is P(|Z| > z_alpha | H1)
    
    # Simplified power calculation for trend detection
    # Using the relationship: Power = Phi( sqrt(n) * delta / sigma - z_alpha )
    # where delta is the true slope and sigma is the standard error
    
    # Estimate standard error of the slope
    # SE(slope) approx sigma_x / (sqrt(n) * sigma_t)
    # We use a heuristic based on sample size
    if n < 3:
        return 0.0, float('inf')
        
    # Heuristic for MDES: The smallest slope detectable with 80% power
    # MDES = (z_alpha + z_beta) * SE
    # For 80% power, z_beta = 0.84
    z_beta_80 = norm.ppf(0.80)
    
    # Approximate SE for MK trend
    # Var(S) = n(n-1)(2n+5)/18
    # SE(S) = sqrt(Var(S))
    # The slope is related to S. 
    # We use a simplified MDES formula based on n
    mdes = (z_alpha + z_beta_80) / math.sqrt(n)
    
    # Calculate actual power for a given effect size
    # Power = Phi( (effect_size / mdes) * (z_alpha + z_beta_80) - z_alpha )
    # This is a heuristic mapping
    power = norm.cdf((effect_size / mdes) * (z_alpha + z_beta_80) - z_alpha)
    
    # Ensure power is within [0, 1]
    power = max(0.0, min(1.0, power))
    
    return power, mdes

def benjamini_hochberg_correction(p_values: List[float]) -> List[Tuple[float, float]]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of p-values.
        
    Returns:
        List of (original_p, corrected_p) tuples.
    """
    n = len(p_values)
    if n == 0:
        return []
        
    # Sort p-values with original indices
    sorted_indices = sorted(range(n), key=lambda k: p_values[k])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected_p = [0.0] * n
    min_corrected = 1.0
    
    # Calculate BH adjusted p-values
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj_p = sorted_p[i] * n / rank
        if adj_p > min_corrected:
            adj_p = min_corrected
        min_corrected = adj_p
        corrected_p[sorted_indices[i]] = adj_p
        
    # Ensure monotonicity and bounds
    for i in range(1, n):
        if corrected_p[i] < corrected_p[i-1]:
            corrected_p[i] = corrected_p[i-1]
            
    for i in range(n):
        corrected_p[i] = max(0.0, min(1.0, corrected_p[i]))
        
    return list(zip(p_values, corrected_p))

def classify_trend(p_value: float, power: float, alpha: float = 0.05, power_threshold: float = 0.8) -> str:
    """
    Classify the trend based on p-value and power.
    
    Classification Logic (FR-003, FR-013):
    - If p < alpha: Significant trend (Growth/Decline determined by slope sign)
    - If p >= alpha AND power >= power_threshold: Stable
    - If p >= alpha AND power < power_threshold: Insufficient Data
    
    Args:
        p_value: Adjusted p-value.
        power: Statistical power.
        alpha: Significance level.
        power_threshold: Minimum power threshold for "Stable" classification.
        
    Returns:
        Classification string.
    """
    if p_value < alpha:
        return "Significant" # Will be refined to Growth/Decline by slope
    elif power >= power_threshold:
        return "Stable"
    else:
        return "Insufficient Data"

def analyze_trends(input_file: str, output_file: str) -> None:
    """
    Main function to analyze trends for all tags.
    
    Args:
        input_file: Path to processed monthly frequency data (JSON).
        output_file: Path to save trend results (JSON).
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    # Load data
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    results = []
    all_p_values = []
    
    # Analyze each tag
    for tag_name, time_series in data.items():
        if not time_series:
            continue
            
        # Convert to numpy array
        y = np.array([item['frequency'] for item in time_series])
        t = np.array([item['month_index'] for item in time_series])
        
        n = len(y)
        if n < 12: # Minimum months requirement
            results.append({
                "tag": tag_name,
                "classification": "Insufficient Data",
                "reason": "Less than 12 months of data",
                "slope": None,
                "p_value": None,
                "power": None,
                "mdes": None
            })
            continue
            
        # Modified Mann-Kendall
        z, p_val, s = modified_mann_kendall(y)
        all_p_values.append(p_val)
        
        # Theil-Sen Slope
        slope = theil_sen_slope(y, t)
        
        # Power Analysis
        power, mdes = calculate_power_and_mdes(n)
        
        # Store raw results for BH correction later
        results.append({
            "tag": tag_name,
            "slope": slope,
            "z_score": z,
            "p_value": p_val,
            "power": power,
            "mdes": mdes,
            "classification": None, # Will be set after BH
            "n_points": n
        })
        
    # Benjamini-Hochberg Correction
    if all_p_values:
        corrected_pairs = benjamini_hochberg_correction(all_p_values)
        for i, (orig_p, adj_p) in enumerate(corrected_pairs):
            results[i]["p_value"] = adj_p
    else:
        for r in results:
            r["p_value"] = 1.0
            
    # Final Classification
    for r in results:
        p = r["p_value"]
        power = r["power"]
        slope = r["slope"]
        
        classification = classify_trend(p, power)
        
        if classification == "Significant":
            if slope > 0:
                classification = "Growth"
            elif slope < 0:
                classification = "Decline"
            else:
                classification = "Stable" # Slope is 0 but significant? (rare)
                
        r["classification"] = classification
        
        # Add MDES only if Insufficient Data or to report generally
        if classification == "Insufficient Data":
            r["mdes_reported"] = r["mdes"]
        else:
            r["mdes_reported"] = r["mdes"] # Report for transparency
            
    # Save results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Trend analysis complete. Results saved to {output_file}")

def main():
    """Entry point for the trends analysis script."""
    # Default paths based on project structure
    input_file = DATA_PROCESSED_DIR / "monthly_tag_frequencies.json"
    output_file = DATA_PROCESSED_DIR / "trend_results_raw.json"
    
    # Allow override via arguments if needed
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    analyze_trends(input_file, output_file)

if __name__ == "__main__":
    main()
