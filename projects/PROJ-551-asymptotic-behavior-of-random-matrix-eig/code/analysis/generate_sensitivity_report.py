import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_project_paths

logger = logging.getLogger(__name__)

def load_sensitivity_variation_csv(path: Path) -> List[Dict[str, Any]]:
    """Load the sensitivity variation CSV data."""
    import csv
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'density': float(row['density']),
                'theta_c': float(row['theta_c']),
                'std_dev': float(row['std_dev'])
            })
    return data

def load_sensitivity_statistics(path: Path) -> Optional[Dict[str, Any]]:
    """Load the sensitivity statistics JSON if it exists."""
    if not path.exists():
        logger.warning(f"Statistics file not found at {path}. Generating report without statistical validation.")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load statistics file {path}: {e}. Generating report without statistical validation.")
        return None

def load_sensitivity_density_sweep(path: Path) -> List[Dict[str, Any]]:
    """Load the raw sensitivity density sweep data."""
    import csv
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse numeric fields
            parsed = {}
            for key, value in row.items():
                try:
                    parsed[key] = float(value)
                except (ValueError, TypeError):
                    parsed[key] = value
            data.append(parsed)
    return data

def generate_report_content(
    variation_data: List[Dict[str, Any]],
    stats_data: Optional[Dict[str, Any]],
    sweep_data: List[Dict[str, Any]]
) -> str:
    """Generate the Markdown content for the sensitivity report."""

    # Calculate overall statistics
    if not variation_data:
        return "# Sensitivity Report\n\nNo variation data available."

    theta_c_values = [d['theta_c'] for d in variation_data]
    std_devs = [d['std_dev'] for d in variation_data]
    densities = [d['density'] for d in variation_data]

    mean_theta_c = sum(theta_c_values) / len(theta_c_values)
    max_theta_c = max(theta_c_values)
    min_theta_c = min(theta_c_values)
    range_theta_c = max_theta_c - min_theta_c
    avg_std_dev = sum(std_devs) / len(std_devs)

    # Determine stability
    stability_threshold = 0.05  # 5%
    is_stable = range_theta_c / mean_theta_c < stability_threshold if mean_theta_c > 0 else True

    report_lines = [
        "# Sensitivity Analysis Report: Sparsity Thresholds",
        "",
        "## Executive Summary",
        "",
        f"This report summarizes the sensitivity analysis of the critical threshold $\\theta_c$ "
        f"with respect to the support density of sparse perturbations. The analysis covers "
        f"densities ranging from {min(densities)} to {max(densities)}.",
        "",
        "## Key Findings",
        "",
        f"- **Mean Critical Threshold ($\\bar{{\\theta_c}}$)**: {mean_theta_c:.6f}",
        f"- **Range of $\\theta_c$**: [{min_theta_c:.6f}, {max_theta_c:.6f}] (Span: {range_theta_c:.6f})",
        f"- **Average Standard Deviation**: {avg_std_dev:.6f}",
        f"- **Stability Assessment**: {'STABLE' if is_stable else 'UNSTABLE'}",
        "",
        f"The critical threshold $\\theta_c$ {'remains stable' if is_stable else 'shows significant variation'} "
        f"across the tested density range. The relative shift is "
        f"{(range_theta_c / mean_theta_c * 100):.2f}%, which is "
        f"{'below' if is_stable else 'above'} the 5% stability threshold.",
        "",
        "## Detailed Results",
        "",
        "### Variation by Density",
        "",
        "| Density | $\\theta_c$ | Std Dev |",
        "|---------|-------------|---------|"
    ]

    for row in variation_data:
        report_lines.append(
            f"| {row['density']:.2f} | {row['theta_c']:.6f} | {row['std_dev']:.6f} |"
        )

    report_lines.extend([
        "",
        "### Raw Sweep Data Summary",
        "",
        f"Total data points analyzed: {len(sweep_data)}",
        "",
        "## Statistical Validation",
        ""
    ])

    if stats_data:
        report_lines.append("The following statistical validation metrics were computed:")
        report_lines.append("")
        for key, value in stats_data.items():
            if isinstance(value, float):
                report_lines.append(f"- **{key}**: {value:.6f}")
            else:
                report_lines.append(f"- **{key}**: {value}")
        report_lines.append("")
    else:
        report_lines.append("*Statistical validation data was not available or could not be loaded.*")
        report_lines.append("")

    report_lines.extend([
        "## Methodology",
        "",
        "The sensitivity analysis was performed by:",
        "",
        "1. Generating random Wigner matrices of size $N$.",
        "2. Applying sparse perturbations with fixed rank but varying support density $p \\in \\{0.1, 0.2, 0.3\\}$.",
        "3. Computing the critical threshold $\\theta_c$ for each density using logistic regression on outlier emergence.",
        "4. Calculating the standard deviation of $\\theta_c$ across Monte Carlo iterations.",
        "",
        "## Conclusion",
        "",
        f"The study confirms that the BBP phase transition threshold $\\theta_c$ is "
        f"{'robust' if is_stable else 'sensitive'} to variations in the sparsity density of the perturbation. "
        f"This suggests that {'the theoretical prediction is insensitive to the specific support density ' if is_stable else 'the specific support density plays a significant role in determining'} "
        f"the location of the spectral outlier transition in the asymptotic limit.",
        "",
        "---",
        f"*Report generated automatically from sensitivity analysis artifacts.*"
    ])

    return "\n".join(report_lines)

def main():
    """Main entry point to generate the sensitivity report."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    paths = get_project_paths()
    variation_path = paths['data_processed'] / 'sensitivity_variation.csv'
    stats_path = paths['data_processed'] / 'sensitivity_statistics.json'
    sweep_path = paths['data_processed'] / 'sensitivity_density_sweep.csv'
    output_path = paths['data_processed'] / 'sensitivity_report.md'

    logger.info(f"Loading sensitivity variation data from {variation_path}...")
    if not variation_path.exists():
        logger.error(f"Required input file not found: {variation_path}")
        sys.exit(1)

    variation_data = load_sensitivity_variation_csv(variation_path)
    logger.info(f"Loaded {len(variation_data)} variation records.")

    logger.info(f"Loading sensitivity statistics from {stats_path}...")
    stats_data = load_sensitivity_statistics(stats_path)

    logger.info(f"Loading raw sweep data from {sweep_path}...")
    if not sweep_path.exists():
        logger.warning(f"Raw sweep data not found at {sweep_path}. Proceeding without it.")
        sweep_data = []
    else:
        sweep_data = load_sensitivity_density_sweep(sweep_path)
        logger.info(f"Loaded {len(sweep_data)} raw sweep records.")

    logger.info("Generating report content...")
    report_content = generate_report_content(variation_data, stats_data, sweep_data)

    logger.info(f"Writing report to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Sensitivity report successfully generated at {output_path}")

if __name__ == '__main__':
    main()
