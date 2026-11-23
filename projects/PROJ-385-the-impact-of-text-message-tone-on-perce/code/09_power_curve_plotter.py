"""
Power Curve Visualization Script.

Generates a power curve visualization (Power vs. Sample Size) based on the
results from the power analysis (T009). The script reads the target sample
size and parameters from `data/processed/power_analysis_results.json` and
plots the power curve to verify N sufficiency.

Output: `data/processed/power_curve.png`
"""
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script execution
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from config import get_processed_data_dir, get_figures_dir
from logging_config import get_logger

logger = get_logger(__name__)


def load_power_analysis_results() -> dict:
    """
    Loads the power analysis results from the processed data directory.

    Returns:
        dict: The JSON content containing target_N, effect_size, alpha, etc.

    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    processed_dir = get_processed_data_dir()
    results_path = processed_dir / "power_analysis_results.json"

    if not results_path.exists():
        raise FileNotFoundError(
            f"Power analysis results file not found at {results_path}. "
            "Please run T009 first to generate this file."
        )

    with open(results_path, 'r') as f:
        return json.load(f)


def generate_power_curve_plot() -> Path:
    """
    Generates a power curve visualization based on the loaded results.

    The plot visualizes Power (y-axis) vs. Sample Size (x-axis) to verify
    that the target N provides sufficient power (>= 0.80).

    Returns:
        Path: The absolute path to the generated PNG file.
    """
    results = load_power_analysis_results()

    # Extract parameters
    target_n = results.get('target_N')
    if not target_n:
        raise ValueError("Target N not found in power analysis results.")

    effect_size = results.get('effect_size', 0.5)
    alpha = results.get('alpha', 0.05)
    power = results.get('power', 0.80)

    logger.info(f"Generating power curve for N={target_n}, effect_size={effect_size}")

    # Generate a range of sample sizes for the curve
    # Start from a small N up to a reasonable upper bound (e.g., 2x target or fixed max)
    max_n = max(target_n * 2, 100)
    sample_sizes = np.linspace(10, max_n, 100).astype(int)

    # Calculate power for each sample size
    # Using a simplified approximation for power in a two-group t-test or similar
    # Power = 1 - beta
    # For a two-tailed test:
    # z_beta = (delta * sqrt(N/2) / sigma) - z_alpha/2
    # We assume sigma=1 for effect size d = delta/sigma
    # So delta = effect_size * sigma = effect_size
    # Standard error for difference of means = sqrt(2 * sigma^2 / N) = sqrt(2/N)
    # t-stat = effect_size / sqrt(2/N) = effect_size * sqrt(N/2)
    
    # Approximation using normal distribution (valid for larger N)
    z_alpha = np.abs(norm.ppf(alpha / 2))
    powers = []
    
    for n in sample_sizes:
        # Non-centrality parameter approximation
        ncp = effect_size * np.sqrt(n / 2)
        # Power is the probability that the test statistic exceeds the critical value
        # under the alternative hypothesis.
        # Power = P(Z > z_alpha - ncp) + P(Z < -z_alpha - ncp)
        # For positive effect size, the second term is negligible.
        # Power ≈ 1 - Φ(z_alpha - ncp) = Φ(ncp - z_alpha)
        p = norm.cdf(ncp - z_alpha)
        powers.append(p)

    powers = np.array(powers)

    # Setup Plot
    plt.figure(figsize=(10, 6))
    plt.plot(sample_sizes, powers, 'b-', linewidth=2, label=f'Power Curve (d={effect_size})')
    
    # Add reference lines
    plt.axhline(y=power, color='r', linestyle='--', label=f'Target Power ({power})')
    plt.axvline(x=target_n, color='g', linestyle=':', label=f'Target N ({target_n})')
    
    # Highlight the target point
    target_power_at_n = norm.cdf(effect_size * np.sqrt(target_n / 2) - z_alpha)
    plt.plot(target_n, target_power_at_n, 'go', markersize=10, label=f'Actual Power at N={target_n} ({target_power_at_n:.3f})')

    plt.title(f'Power Analysis Curve\nEffect Size (d) = {effect_size}, Alpha = {alpha}', fontsize=14)
    plt.xlabel('Sample Size (N)', fontsize=12)
    plt.ylabel('Statistical Power (1 - β)', fontsize=12)
    plt.legend(loc='lower right')
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.ylim(0, 1.05)
    plt.xlim(0, max_n)

    # Save the figure
    figures_dir = get_figures_dir()
    figures_dir.mkdir(parents=True, exist_ok=True)
    output_path = figures_dir / "power_curve.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Power curve saved to {output_path}")
    return output_path


def main():
    """Main entry point for the power curve generation script."""
    try:
        output_path = generate_power_curve_plot()
        print(f"Successfully generated power curve: {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Missing input data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating power curve: {e}")
        raise


if __name__ == "__main__":
    main()
