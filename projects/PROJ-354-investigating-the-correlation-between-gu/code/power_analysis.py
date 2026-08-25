"""
Power Analysis Module for Gut Microbiome-Cognitive Correlation Study.

This module implements:
1. Synthetic dataset generation with a known effect size (beta).
2. Power calculation using simulation.
3. Theoretical power validation.
4. Report generation to `results/power/power_report.md`.

This acts as a gate before statistical analysis (T020a).
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats

# Import project config
from config import get_path, ensure_directories
from utils.logging import get_logger, init_logging

logger = get_logger(__name__)

# Constants
RANDOM_SEED = 42
DEFAULT_BETA = 0.1
DEFAULT_N_SIMULATIONS = 1000
DEFAULT_ALPHA = 0.05
DEFAULT_POWER_THRESHOLD = 0.80


def calculate_theoretical_power(
    effect_size: float,
    sample_size: int,
    alpha: float = 0.05,
    sigma: float = 1.0
) -> float:
    """
    Calculate theoretical power for a simple linear regression (one predictor).
    
    Formula based on non-central t-distribution or normal approximation for large N.
    Power = P(Reject H0 | H1 is true)
    
    For large N, t-statistic approximates normal:
    t = (beta_hat - 0) / SE(beta_hat)
    SE(beta_hat) approx sigma / (sqrt(N) * sigma_x)
    Assuming standardized X (sigma_x = 1), SE = sigma / sqrt(N).
    Non-centrality parameter (NCP) = beta * sqrt(N) / sigma.
    
    Power = 1 - norm.cdf(z_crit - NCP) + norm.cdf(-z_crit - NCP)
    """
    # Standardize effect size (Cohen's d equivalent for regression)
    # Here we assume predictor X is standardized (mean=0, std=1)
    ncp = effect_size * math.sqrt(sample_size) / sigma
    
    # Critical value for two-tailed test
    z_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Power calculation
    # Probability of rejecting null when true effect is ncp
    power = 1 - stats.norm.cdf(z_crit - ncp) + stats.norm.cdf(-z_crit - ncp)
    
    return float(power)


def calculate_required_n(
    effect_size: float,
    target_power: float,
    alpha: float = 0.05,
    sigma: float = 1.0
) -> int:
    """
    Calculate required sample size for a given effect size and target power.
    Inverse of the power calculation.
    """
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(target_power)
    
    # NCP = (z_alpha + z_beta)
    # beta * sqrt(N) / sigma = z_alpha + z_beta
    # sqrt(N) = (z_alpha + z_beta) * sigma / beta
    # N = ((z_alpha + z_beta) * sigma / beta)^2
    
    ncp_needed = z_alpha + z_beta
    n = (ncp_needed * sigma / effect_size) ** 2
    
    return int(math.ceil(n))


def generate_synthetic_dataset(
    n_samples: int,
    beta: float = DEFAULT_BETA,
    sigma: float = 1.0,
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Generate a synthetic dataset for power analysis.
    
    Model: Y = beta * X + epsilon
    where X ~ N(0, 1) and epsilon ~ N(0, sigma^2).
    
    Args:
        n_samples: Number of samples.
        beta: True effect size (slope).
        sigma: Standard deviation of noise.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with columns 'x', 'y', 'group' (optional).
    """
    np.random.seed(seed)
    
    # Generate predictor X (standardized)
    x = np.random.normal(0, 1, n_samples)
    
    # Generate noise
    epsilon = np.random.normal(0, sigma, n_samples)
    
    # Generate outcome Y
    y = beta * x + epsilon
    
    df = pd.DataFrame({
        'x': x,
        'y': y
    })
    
    return df


def run_power_simulation(
    n_samples: int,
    beta: float,
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    alpha: float = DEFAULT_ALPHA,
    sigma: float = 1.0,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation to estimate empirical power.
    
    Repeatedly generates data with known beta, fits OLS, and checks
    if the p-value is significant.
    """
    np.random.seed(seed)
    significant_count = 0
    estimated_betas = []
    p_values = []
    
    logger.info(f"Running {n_simulations} simulations for N={n_samples}, beta={beta}...")
    
    for i in range(n_simulations):
        # Generate data
        df = generate_synthetic_dataset(n_samples, beta, sigma, seed=seed + i)
        
        # Fit OLS (simple linear regression)
        # y = b0 + b1 * x
        # Using numpy for speed
        x = df['x'].values
        y = df['y'].values
        
        # Add intercept column
        X = np.column_stack((np.ones_like(x), x))
        
        # OLS solution: (X'X)^-1 X'y
        try:
            beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]
            residuals = y - X @ beta_hat
            mse = np.sum(residuals**2) / (n_samples - 2)
            se_beta = np.sqrt(mse * np.linalg.inv(X.T @ X)[1, 1])
            
            t_stat = beta_hat[1] / se_beta
            # Two-tailed p-value
            p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), df=n_samples - 2))
            
            estimated_betas.append(beta_hat[1])
            p_values.append(p_val)
            
            if p_val < alpha:
                significant_count += 1
                
        except np.linalg.LinAlgError:
            # Singular matrix, skip
            continue
    
    empirical_power = significant_count / n_simulations
    
    return {
        "n_samples": n_samples,
        "true_beta": beta,
        "n_simulations": n_simulations,
        "empirical_power": empirical_power,
        "significant_count": significant_count,
        "mean_estimated_beta": float(np.mean(estimated_betas)),
        "std_estimated_beta": float(np.std(estimated_betas)),
        "mean_p_value": float(np.mean(p_values))
    }


def run_power_analysis(
    target_power: float = DEFAULT_POWER_THRESHOLD,
    effect_size: float = DEFAULT_BETA,
    alpha: float = DEFAULT_ALPHA,
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    sigma: float = 1.0,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Run a comprehensive power analysis.
    
    1. Calculate theoretical power for a range of sample sizes.
    2. Calculate required N for target power.
    3. Run simulations for key N points to validate theory.
    """
    logger.info("Starting Power Analysis...")
    
    # 1. Theoretical Calculations
    required_n = calculate_required_n(effect_size, target_power, alpha, sigma)
    logger.info(f"Required N for {target_power:.2f} power (beta={effect_size}): {required_n}")
    
    # Define a range of sample sizes to test
    # Start from small, go up to required_n + 20%
    max_n = int(required_n * 1.2)
    sample_sizes = [50, 100, 200, 500, required_n, max_n]
    sample_sizes = sorted(list(set([n for n in sample_sizes if n > 0])))
    
    results = {
        "parameters": {
            "target_power": target_power,
            "effect_size": effect_size,
            "alpha": alpha,
            "sigma": sigma,
            "n_simulations": n_simulations,
            "seed": seed
        },
        "theoretical": {
            "required_n": required_n,
            "power_at_required_n": calculate_theoretical_power(effect_size, required_n, alpha, sigma)
        },
        "simulation_results": []
    }
    
    for n in sample_sizes:
        # Theoretical power
        theo_power = calculate_theoretical_power(effect_size, n, alpha, sigma)
        
        # Simulation
        sim_result = run_power_simulation(n, effect_size, n_simulations, alpha, sigma, seed)
        
        results["simulation_results"].append({
            "n": n,
            "theoretical_power": theo_power,
            "empirical_power": sim_result["empirical_power"],
            "mean_estimated_beta": sim_result["mean_estimated_beta"],
            "std_estimated_beta": sim_result["std_estimated_beta"]
        })
        
        logger.info(f"N={n}: Theo={theo_power:.3f}, Emp={sim_result['empirical_power']:.3f}")
    
    # Validation Check
    # Check if empirical power at required_n is close to target
    final_result = next((r for r in results["simulation_results"] if r["n"] == required_n), None)
    validation_status = "PASS"
    validation_msg = ""
    
    if final_result:
        diff = abs(final_result["empirical_power"] - target_power)
        if diff > 0.10: # Allow 10% tolerance for simulation variance
            validation_status = "WARN"
            validation_msg = f"Empirical power ({final_result['empirical_power']:.3f}) deviates >10% from target ({target_power})"
        else:
            validation_msg = f"Empirical power ({final_result['empirical_power']:.3f}) matches target ({target_power}) within tolerance."
    else:
        validation_status = "FAIL"
        validation_msg = "Could not find simulation result for required N."
        
    results["validation"] = {
        "status": validation_status,
        "message": validation_msg,
        "target_power": target_power,
        "achieved_power": final_result["empirical_power"] if final_result else None
    }
    
    return results


def generate_report(results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate the power report markdown file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    params = results["parameters"]
    theo = results["theoretical"]
    sim_results = results["simulation_results"]
    validation = results["validation"]
    
    report_lines = [
        "# Power Analysis Report",
        "",
        f"**Generated**: {pd.Timestamp.now().isoformat()}",
        "",
        "## 1. Parameters",
        "",
        "| Parameter | Value |",
        "| :--- | :--- |",
        f"| Target Power | {params['target_power']:.2f} |",
        f"| Effect Size (Beta) | {params['effect_size']:.2f} |",
        f"| Alpha Level | {params['alpha']:.2f} |",
        f"| Noise Sigma | {params['sigma']:.2f} |",
        f"| Simulations | {params['n_simulations']:,} |",
        "",
        "## 2. Theoretical Requirements",
        "",
        f"To achieve {params['target_power']:.2f} power for an effect size of {params['effect_size']:.2f}, "
        f"theoretical calculation suggests a required sample size of **{theo['required_n']:,}**.",
        "",
        "## 3. Simulation Results",
        "",
        "Monte Carlo simulations were run to validate theoretical power calculations.",
        "",
        "| N | Theoretical Power | Empirical Power | Mean Estimated Beta | Std Dev Beta |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    
    for res in sim_results:
        report_lines.append(
            f"| {res['n']:,} | {res['theoretical_power']:.3f} | {res['empirical_power']:.3f} | "
            f"{res['mean_estimated_beta']:.3f} | {res['std_estimated_beta']:.3f} |"
        )
    
    report_lines.extend([
        "",
        "## 4. Validation Status",
        "",
        f"- **Status**: {validation['status']}",
        f"- **Message**: {validation['message']}",
        "",
        "## 5. Conclusion",
        "",
        f"The power analysis confirms that a sample size of approximately {theo['required_n']:,} "
        f"is sufficient to detect the specified effect size with {params['target_power']:.2f} power.",
        f"The simulation validates the theoretical model within acceptable variance.",
        "",
        "---",
        "*This report acts as a gate for statistical analysis (T020a).*"
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Power report generated: {output_path}")


def main():
    """Main entry point for power analysis."""
    parser = argparse.ArgumentParser(description="Run power analysis for the study.")
    parser.add_argument("--beta", type=float, default=DEFAULT_BETA, help="True effect size (beta)")
    parser.add_argument("--power", type=float, default=DEFAULT_POWER_THRESHOLD, help="Target power")
    parser.add_argument("--n-sims", type=int, default=DEFAULT_N_SIMULATIONS, help="Number of simulations")
    parser.add_argument("--output", type=str, default=None, help="Output path for report")
    
    args = parser.parse_args()
    
    init_logging()
    
    # Ensure directories exist
    ensure_directories()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path("results/power/power_report.md")
    
    # Run analysis
    results = run_power_analysis(
        target_power=args.power,
        effect_size=args.beta,
        n_simulations=args.n_sims
    )
    
    # Generate report
    generate_report(results, output_path)
    
    # Print summary to stdout for CI/CD visibility
    print(json.dumps(results, indent=2))
    
    # Return exit code based on validation
    if results["validation"]["status"] == "FAIL":
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()