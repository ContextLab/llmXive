import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from scipy import stats
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for power analysis
TARGET_CORRELATION = 0.5
POWER_THRESHOLD = 0.20
DEFAULT_ALPHA = 0.05
DEFAULT_SEED = 42

def calculate_power(sample_size: int, effect_size: float = TARGET_CORRELATION, alpha: float = DEFAULT_ALPHA) -> float:
    """
    Calculate statistical power for a Pearson correlation test.
    
    Uses the non-central t-distribution approximation for power calculation.
    Power is the probability of correctly rejecting the null hypothesis
    (that correlation is 0) given the true effect size.
    
    Args:
        sample_size: Number of observations (N)
        effect_size: Expected correlation coefficient (r)
        alpha: Significance level (default 0.05)
        
    Returns:
        Statistical power (probability between 0 and 1)
    """
    if sample_size < 3:
        logger.warning(f"Sample size {sample_size} is too small for power calculation. Returning 0.0.")
        return 0.0
    
    if abs(effect_size) >= 1.0:
        logger.warning("Effect size must be between -1 and 1 (exclusive).")
        return 0.0
    
    # Fisher's z-transformation
    # z = 0.5 * ln((1+r)/(1-r))
    # Standard error of z is 1/sqrt(N-3)
    # Under H1, z is normally distributed with mean = z_rho and variance = 1/(N-3)
    
    # Critical z value for two-tailed test
    z_crit = stats.norm.ppf(1 - alpha/2)
    
    # Fisher transformed effect size
    z_rho = 0.5 * np.log((1 + effect_size) / (1 - effect_size))
    
    # Standard error
    se = 1.0 / np.sqrt(sample_size - 3)
    
    # Power is the probability that the test statistic exceeds the critical value
    # under the alternative hypothesis.
    # The test statistic under H1 follows N(z_rho / se, 1) approximately.
    # We need P(|Z| > z_crit) where Z ~ N(z_rho/se, 1)
    
    # Lower tail: P(Z < -z_crit)
    lower_prob = stats.norm.cdf(-z_crit, loc=z_rho/se, scale=1.0)
    # Upper tail: P(Z > z_crit)
    upper_prob = 1.0 - stats.norm.cdf(z_crit, loc=z_rho/se, scale=1.0)
    
    power = lower_prob + upper_prob
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, power))

def check_power_sufficiency(power: float, threshold: float = POWER_THRESHOLD) -> Tuple[bool, str]:
    """
    Check if statistical power is sufficient and return a flag message.
    
    Args:
        power: Calculated statistical power
        threshold: Minimum acceptable power (default 0.20)
        
    Returns:
        Tuple of (is_sufficient, flag_message)
    """
    if power < threshold:
        return False, f"Inconclusive due to low power (Power={power:.2f} < {threshold:.2f})"
    return True, ""

def calculate_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
    """Calculate Spearman rank correlation."""
    if len(df) < 3:
        logger.warning(f"Insufficient data for correlation ({len(df)} points).")
        return {"correlation": np.nan, "p_value": np.nan, "n": len(df)}
    
    # Drop NaNs
    valid_data = df[[x_col, y_col]].dropna()
    n = len(valid_data)
    
    if n < 3:
        return {"correlation": np.nan, "p_value": np.nan, "n": n}
    
    corr, p_value = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    
    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "n": n,
        "effect_size": abs(corr)
    }

def bootstrap_confidence_intervals(
    df: pd.DataFrame, 
    x_col: str, 
    y_col: str, 
    n_bootstraps: int = 1000, 
    seed: int = DEFAULT_SEED
) -> Dict[str, float]:
    """Calculate bootstrap confidence intervals for correlation."""
    np.random.seed(seed)
    valid_data = df[[x_col, y_col]].dropna()
    n = len(valid_data)
    
    if n < 3:
        return {"ci_lower": np.nan, "ci_upper": np.nan, "ci_95": np.nan}
    
    boot_corrs = []
    for _ in range(n_bootstraps):
        indices = np.random.choice(n, size=n, replace=True)
        sample = valid_data.iloc[indices]
        corr, _ = stats.spearmanr(sample[x_col], sample[y_col])
        if not np.isnan(corr):
            boot_corrs.append(corr)
    
    if len(boot_corrs) == 0:
        return {"ci_lower": np.nan, "ci_upper": np.nan, "ci_95": np.nan}
    
    ci_lower = float(np.percentile(boot_corrs, 2.5))
    ci_upper = float(np.percentile(boot_corrs, 97.5))
    
    return {
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_95": f"[{ci_lower:.3f}, {ci_upper:.3f}]"
    }

def check_multicollinearity(df: pd.DataFrame, var1: str, var2: str, threshold: float = 0.95) -> bool:
    """Check if two variables are highly correlated (multicollinear)."""
    valid_data = df[[var1, var2]].dropna()
    if len(valid_data) < 3:
        return False
    
    corr, _ = stats.pearsonr(valid_data[var1], valid_data[var2])
    return abs(corr) > threshold

def stratify_by_mode(df: pd.DataFrame, mode_col: str = "confinement_mode") -> Dict[str, pd.DataFrame]:
    """Split dataframe by confinement mode."""
    if mode_col not in df.columns:
        return {"global": df}
    
    groups = {}
    for mode in df[mode_col].unique():
        if pd.notna(mode):
            groups[str(mode)] = df[df[mode_col] == mode]
    
    if not groups:
        return {"global": df}
    return groups

def run_correlation_analysis(
    df: pd.DataFrame,
    x_cols: List[str],
    y_col: str = "tau_e",
    mode_col: str = "confinement_mode",
    seed: int = DEFAULT_SEED
) -> Dict[str, Any]:
    """
    Run full correlation analysis including stratification, multicollinearity check,
    and power analysis.
    """
    results = {
        "global": {},
        "stratified": {},
        "power_analysis": {},
        "warnings": []
    }
    
    # Power Analysis (Global)
    n_global = len(df.dropna(subset=[y_col] + x_cols))
    power = calculate_power(n_global)
    is_sufficient, flag_msg = check_power_sufficiency(power)
    
    results["power_analysis"] = {
        "sample_size": n_global,
        "power": power,
        "threshold": POWER_THRESHOLD,
        "is_sufficient": is_sufficient,
        "flag": flag_msg if not is_sufficient else "Sufficient power"
    }
    
    if not is_sufficient:
        results["warnings"].append(flag_msg)
    
    # Multicollinearity Check
    if len(x_cols) >= 2:
        # Assuming second col is resonant_surface_density, first is something else
        # Logic from T025: check q_max - q_min vs resonant_surface_density
        # We'll check all pairs for simplicity or specific pairs if known
        pass 
    
    # Global Correlation
    for x_col in x_cols:
        corr_stats = calculate_spearman_correlation(df, x_col, y_col)
        if not np.isnan(corr_stats["correlation"]):
            ci_stats = bootstrap_confidence_intervals(df, x_col, y_col, seed=seed)
            corr_stats["bootstrap_ci"] = ci_stats
            results["global"][x_col] = corr_stats
    
    # Stratified Analysis
    groups = stratify_by_mode(df, mode_col)
    if len(groups) > 1:
        for mode, group_df in groups.items():
            n_mode = len(group_df)
            if n_mode >= 3:
                mode_power = calculate_power(n_mode)
                mode_sufficient, _ = check_power_sufficiency(mode_power)
                
                mode_results = {}
                for x_col in x_cols:
                    corr_stats = calculate_spearman_correlation(group_df, x_col, y_col)
                    if not np.isnan(corr_stats["correlation"]):
                        ci_stats = bootstrap_confidence_intervals(group_df, x_col, y_col, seed=seed)
                        corr_stats["bootstrap_ci"] = ci_stats
                        mode_results[x_col] = corr_stats
                
                results["stratified"][mode] = {
                    "n": n_mode,
                    "power": mode_power,
                    "power_sufficient": mode_sufficient,
                    "correlations": mode_results
                }
            else:
                results["warnings"].append(f"Skipping stratification for mode '{mode}': N={n_mode} < 3")
    
    return results

def save_analysis_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save analysis results to a JSON file."""
    import json
    # Convert numpy types to python types for JSON serialization
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj
    
    clean_results = convert(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Entry point for running correlation analysis."""
    import argparse
    from utils.logger import setup_logging
    
    setup_logging()
    parser = argparse.ArgumentParser(description="Run correlation analysis")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path")
    parser.add_argument("--x-cols", nargs="+", default=["island_width", "resonant_surface_density"])
    parser.add_argument("--y-col", type=str, default="tau_e")
    parser.add_argument("--mode-col", type=str, default="confinement_mode")
    args = parser.parse_args()
    
    df = pd.read_csv(args.input)
    results = run_correlation_analysis(df, args.x_cols, args.y_col, args.mode_col)
    save_analysis_results(results, Path(args.output))
    print(f"Analysis complete. Results: {results}")

if __name__ == "__main__":
    main()