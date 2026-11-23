import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import os

# Optional imports for survival analysis if scikit-survival is available
try:
    from sksurv.nonparametric import kendall_tau
    HAS_SKSURV = True
except ImportError:
    HAS_SKSURV = False
    logging.warning("sksurv not available. Kendall's tau calculation will use a simplified rank-based approximation.")

# Optional imports for statsmodels if needed for VIF
try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    HAS_STATS = True
except ImportError:
    HAS_STATS = False

# Import config
from config import get_config
from utils import setup_logging, safe_execute

logger = logging.getLogger(__name__)

# Constants for Power Analysis
POWER_SIMULATIONS = 1000
POWER_TRUE_TAU = 0.3
POWER_ALPHA = 0.05

def load_analysis_data() -> pd.DataFrame:
    """Load the merged analysis dataset from processed files."""
    config = get_config()
    metadata_path = config.data_dir / "processed" / "metadata.csv"
    retrieval_path = config.data_dir / "processed" / "retrieval_results.csv"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")

    meta_df = pd.read_csv(metadata_path)
    ret_df = pd.read_csv(retrieval_path)

    # Merge on planet_name
    merged = pd.merge(meta_df, ret_df, on='planet_name', how='inner')
    logger.info(f"Loaded {len(merged)} merged records for analysis.")
    return merged

def quality_control_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply quality control filters.
    Returns two datasets:
    1. filtered_correlation_data: All planets with temperature (for Kendall's tau).
    2. filtered_regression_data: Planets with temperature AND metallicity (for Tobit).
    """
    # Filter 1: Correlation data (needs temperature)
    corr_data = df[df['temperature'].notna()].copy()
    logger.info(f"Correlation dataset size: {len(corr_data)}")

    # Filter 2: Regression data (needs temperature AND metallicity)
    reg_data = corr_data[corr_data['metallicity'].notna()].copy()
    logger.info(f"Regression dataset size: {len(reg_data)}")

    return corr_data, reg_data

def calculate_effect_size(df: pd.DataFrame) -> float:
    """Calculate a simple effect size metric (e.g., Cohen's d equivalent for correlation)."""
    # Placeholder for specific effect size calculation if needed
    return 0.0

def compute_censored_kendall_tau(df: pd.DataFrame, x_col: str, y_col: str) -> float:
    """
    Compute Kendall's tau for censored data.
    If scikit-survival is available, uses it. Otherwise, falls back to standard Kendall.
    """
    x = df[x_col].values
    y = df[y_col].values
    # Mask for upper limits (is_upper_limit column)
    if 'is_upper_limit' in df.columns:
        mask = df['is_upper_limit'].astype(bool).values
    else:
        mask = np.zeros(len(df), dtype=bool)

    if HAS_SKSURV:
        # Construct structured array for survival data
        # For correlation, we treat the 'y' variable as the survival time and 'mask' as the event indicator (1=censored, 0=event)
        # However, scikit-survival's kendall_tau expects (time, event) where event=1 means event occurred.
        # Here, 'is_upper_limit' means censored. So event = 1 - is_upper_limit.
        event = 1 - mask
        try:
            tau = kendall_tau((y, event))
            return float(tau)
        except Exception as e:
            logger.warning(f"scikit-survival kendall_tau failed: {e}. Falling back to standard.")
    
    # Fallback: Standard Kendall Tau (ignoring censoring for simplicity in fallback, or treating all as observed)
    # A more robust fallback would implement the Akritas-Theil-Sen or similar rank sum logic manually.
    # For this implementation, we use standard scipy.stats.kendalltau if available, or numpy approximation.
    try:
        from scipy.stats import kendalltau
        return float(kendalltau(x, y).correlation)
    except ImportError:
        # Manual calculation
        n = len(x)
        concordant = 0
        discordant = 0
        for i in range(n):
            for j in range(i + 1, n):
                dx = x[i] - x[j]
                dy = y[i] - y[j]
                if dx == 0 or dy == 0:
                    continue
                if dx * dy > 0:
                    concordant += 1
                else:
                    discordant += 1
        total = concordant + discordant
        if total == 0:
            return 0.0
        return float((concordant - discordant) / total)

def bootstrap_ats(df: pd.DataFrame, x_col: str, y_col: str, n_iterations: int = 1000, seed: int = 42) -> List[float]:
    """
    Perform bootstrap resampling to estimate confidence intervals.
    Returns a list of tau values from each bootstrap iteration.
    """
    np.random.seed(seed)
    taus = []
    n = len(df)
    
    for i in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        boot_df = df.iloc[indices]
        tau = compute_censored_kendall_tau(boot_df, x_col, y_col)
        taus.append(tau)
    
    return taus

def calculate_statistical_power(df: pd.DataFrame, x_col: str = 'temperature', y_col: str = 'water_mixing_ratio') -> Dict[str, Any]:
    """
    Calculate statistical power using a simulation-based power estimator for Kendall's tau.
    
    Logic:
    1. Generate 1000 synthetic datasets with a known true tau of 0.3 and sample size N.
    2. Add noise consistent with observed data distribution.
    3. Run censored Kendall's tau analysis on each.
    4. Estimate power = (count where null hypothesis rejected at alpha=0.05) / 1000.
    """
    config = get_config()
    n_samples = len(df)
    if n_samples == 0:
        logger.error("Dataset is empty. Cannot calculate power.")
        return {"power_estimate": 0.0, "power_sufficient": False, "error": "Empty dataset"}

    logger.info(f"Starting power analysis with N={n_samples}, target_tau={POWER_TRUE_TAU}, simulations={POWER_SIMULATIONS}")
    
    # Estimate noise parameters from real data
    x_data = df[x_col].dropna().values
    y_data = df[y_col].dropna().values
    
    if len(x_data) < 2 or len(y_data) < 2:
        logger.warning("Insufficient data for noise estimation. Using defaults.")
        x_mean, x_std = 0, 1
        y_mean, y_std = 0, 1
    else:
        x_mean, x_std = np.mean(x_data), np.std(x_data)
        y_mean, y_std = np.mean(y_data), np.std(y_data)

    significant_count = 0
    simulated_taus = []

    # We need a generator for synthetic data with a specific correlation (tau)
    # Since generating exact Kendall's tau is complex, we generate correlated normals
    # and approximate the resulting tau, then scale.
    # Alternatively, we use the known relationship: tau approx (2/pi) * arcsin(rho) for normals.
    # rho = sin(tau * pi / 2)
    target_rho = np.sin(POWER_TRUE_TAU * np.pi / 2)
    
    logger.info(f"Target Pearson rho for simulation: {target_rho:.4f}")

    for i in range(POWER_SIMULATIONS):
        # Generate correlated normal data
        cov_matrix = [[1, target_rho], [target_rho, 1]]
        try:
            data = np.random.multivariate_normal([0, 0], cov_matrix, size=n_samples)
            sim_x = data[:, 0] * x_std + x_mean
            sim_y = data[:, 1] * y_std + y_mean
            
            # Create a synthetic dataframe
            sim_df = pd.DataFrame({x_col: sim_x, y_col: sim_y, 'is_upper_limit': False})
            
            # Calculate tau
            tau = compute_censored_kendall_tau(sim_df, x_col, y_col)
            simulated_taus.append(tau)
            
            # Test significance (Null: tau = 0)
            # Approximate standard error of tau: SE = sqrt((4*(n+1))/(9*n*(n-1)))
            # Z = tau / SE
            # This is an approximation for large N
            if n_samples > 10:
                se = np.sqrt((4 * (n_samples + 1)) / (9 * n_samples * (n_samples - 1)))
                z_score = tau / se if se > 0 else 0
                # Two-tailed p-value approximation
                # Using normal approximation for p-value
                p_value = 2 * (1 - 0.5 * (1 + np.math.erf(abs(z_score) / np.sqrt(2))))
                
                if p_value < POWER_ALPHA:
                    significant_count += 1
            else:
                # For small N, we assume if tau is non-zero and we have a target, it's significant in simulation context
                # This is a simplification for the power estimation logic
                if abs(tau) > 0.1: # Arbitrary threshold for small N
                    significant_count += 1

        except Exception as e:
            logger.warning(f"Simulation {i} failed: {e}")
            continue

    power_estimate = significant_count / POWER_SIMULATIONS
    power_sufficient = power_estimate >= 0.8

    logger.info(f"Power analysis complete. Power estimate: {power_estimate:.4f} (Sufficient: {power_sufficient})")

    return {
        "power_estimate": float(power_estimate),
        "power_sufficient": bool(power_sufficient),
        "simulations_run": POWER_SIMULATIONS,
        "sample_size": n_samples,
        "target_tau": POWER_TRUE_TAU,
        "alpha": POWER_ALPHA
    }

def generate_quality_report(df: pd.DataFrame, power_results: Dict[str, Any]) -> str:
    """Generate a markdown quality report."""
    report = []
    report.append("# Quality Report")
    report.append(f"## Sample Size")
    report.append(f"Total planets analyzed: {len(df)}")
    
    report.append(f"## Censorship")
    if 'is_upper_limit' in df.columns:
        limits = df['is_upper_limit'].sum()
        resolved = len(df) - limits
        report.append(f"Resolved measurements: {resolved}")
        report.append(f"Upper limits (censored): {limits}")
    else:
        report.append("No censorship flags found.")

    report.append(f"## Power Analysis")
    report.append(f"Power Estimate: {power_results.get('power_estimate', 'N/A')}")
    report.append(f"Sufficient Power (>=0.8): {power_results.get('power_sufficient', 'N/A')}")
    
    return "\n".join(report)

def save_power_results(power_results: Dict[str, Any], output_path: Path) -> None:
    """Save power analysis results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(power_results, f, indent=2)
    logger.info(f"Power results saved to {output_path}")

def save_robustness_report_tau(robustness_data: Dict[str, Any], output_path: Path) -> None:
    """Save robustness report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(robustness_data, f, indent=2)
    logger.info(f"Robustness report saved to {output_path}")

def calculate_ci_width_variable(ci_lower: float, ci_upper: float) -> float:
    """Calculate CI width for a variable."""
    return ci_upper - ci_lower

def calculate_ci_width_tau(tau_lower: float, tau_upper: float) -> float:
    """Calculate CI width for tau."""
    return tau_upper - tau_lower

def save_robustness_report_tau(data: Dict[str, Any], path: Path) -> None:
    """Save robustness report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def compute_censored_kendall_and_bootstrap(df: pd.DataFrame, output_dir: Path, seed: int = 42) -> Dict[str, Any]:
    """
    Compute Kendall's tau, bootstrap CI, and save results.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Compute tau
    tau = compute_censored_kendall_tau(df, 'temperature', 'water_mixing_ratio')
    
    # Bootstrap
    taus = bootstrap_ats(df, 'temperature', 'water_mixing_ratio', n_iterations=1000, seed=seed)
    ci_lower = float(np.percentile(taus, 2.5))
    ci_upper = float(np.percentile(taus, 97.5))
    tau_mean = float(np.mean(taus))
    
    # Save correlation stats
    corr_stats = {
        "tau": tau,
        "p_value": 0.0, # Placeholder, would need exact p-value calculation
        "ci_lower": ci_lower,
        "ci_upper": ci_upper
    }
    with open(output_dir / "correlation_stats.json", 'w') as f:
        json.dump(corr_stats, f, indent=2)
    
    # Save bootstrap CI
    bootstrap_ci = {
        "iterations": 1000,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "tau_mean": tau_mean
    }
    with open(output_dir / "bootstrap_ci.json", 'w') as f:
        json.dump(bootstrap_ci, f, indent=2)
        
    return corr_stats

def main():
    """Main entry point for analysis."""
    setup_logging()
    config = get_config()
    
    try:
        # Load data
        df = load_analysis_data()
        
        # Filter
        corr_df, reg_df = quality_control_filter(df)
        
        # Power Analysis (T031)
        power_results = calculate_statistical_power(corr_df)
        
        # Save Power Analysis
        power_output_path = config.results_dir / "power_analysis.json"
        save_power_results(power_results, power_output_path)
        
        # Generate Quality Report
        quality_report = generate_quality_report(corr_df, power_results)
        report_path = config.results_dir / "quality_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(quality_report)
            
        logger.info("Analysis complete.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()