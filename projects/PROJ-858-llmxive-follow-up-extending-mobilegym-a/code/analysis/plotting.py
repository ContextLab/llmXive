import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np

from utils.logging import get_logger, log_with_context

logger = get_logger(__name__)


def load_convergence_results(path: str) -> Dict[str, Any]:
    """Load convergence analysis results from JSON file."""
    full_path = Path(path)
    if not full_path.exists():
        raise FileNotFoundError(f"Convergence results not found at {path}")
    
    with open(full_path, 'r') as f:
        return json.load(f)


def extract_plot_data(results: Dict[str, Any]) -> Tuple[List[float], List[float], List[float], List[float]]:
    """
    Extract step and success rate data for both baseline and experimental runs.
    
    Returns:
        Tuple of (baseline_steps, baseline_rates, experimental_steps, experimental_rates)
    """
    baseline_steps = []
    baseline_rates = []
    experimental_steps = []
    experimental_rates = []

    # Extract baseline (Static Random) data
    if 'baseline' in results and 'runs' in results['baseline']:
        for run in results['baseline']['runs']:
            steps = run.get('steps_to_target', 0)
            success_rate = run.get('final_success_rate', 0.0)
            baseline_steps.append(steps)
            baseline_rates.append(success_rate)

    # Extract experimental (State-Guided) data
    if 'experimental' in results and 'runs' in results['experimental']:
        for run in results['experimental']['runs']:
            steps = run.get('steps_to_target', 0)
            success_rate = run.get('final_success_rate', 0.0)
            experimental_steps.append(steps)
            experimental_rates.append(success_rate)

    return baseline_steps, baseline_rates, experimental_steps, experimental_rates


def create_success_rate_vs_steps_plot(
    baseline_steps: List[float],
    baseline_rates: List[float],
    experimental_steps: List[float],
    experimental_rates: List[float],
    output_path: str,
    title: str = "Success Rate vs. Steps to Target"
) -> str:
    """
    Create a scatter plot comparing Success Rate vs. Steps for Baseline and Experimental runs.
    
    Args:
        baseline_steps: Steps to target for baseline runs
        baseline_rates: Success rates for baseline runs
        experimental_steps: Steps to target for experimental runs
        experimental_rates: Success rates for experimental runs
        output_path: Path to save the plot
        title: Plot title
    
    Returns:
        Path to the saved plot file
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot baseline data
    if baseline_steps and baseline_rates:
        ax.scatter(
            baseline_steps, 
            baseline_rates, 
            color='gray', 
            alpha=0.6, 
            edgecolors='black', 
            s=100, 
            label='Static Random Baseline'
        )
        # Add trend line for baseline
        if len(baseline_steps) > 1:
            z = np.polyfit(baseline_steps, baseline_rates, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(baseline_steps), max(baseline_steps), 100)
            ax.plot(x_line, p(x_line), 'g--', alpha=0.5, linewidth=1, label='Baseline Trend')

    # Plot experimental data
    if experimental_steps and experimental_rates:
        ax.scatter(
            experimental_steps, 
            experimental_rates, 
            color='blue', 
            alpha=0.7, 
            edgecolors='darkblue', 
            s=100, 
            label='State-Guided Experimental'
        )
        # Add trend line for experimental
        if len(experimental_steps) > 1:
            z = np.polyfit(experimental_steps, experimental_rates, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(experimental_steps), max(experimental_steps), 100)
            ax.plot(x_line, p(x_line), 'r--', alpha=0.5, linewidth=1, label='Experimental Trend')

    # Configuration
    ax.set_xlabel('Steps to Target', fontsize=12)
    ax.set_ylabel('Final Success Rate', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Set axis limits with padding
    if baseline_steps or experimental_steps:
      all_steps = baseline_steps + experimental_steps
      min_step = min(all_steps) if all_steps else 0
      max_step = max(all_steps) if all_steps else 100
      ax.set_xlim(left=0, right=max_step * 1.1)
      
    if baseline_rates or experimental_rates:
      all_rates = baseline_rates + experimental_rates
      min_rate = min(all_rates) if all_rates else 0
      max_rate = max(all_rates) if all_rates else 1
      ax.set_ylim(bottom=0, top=max(1.0, max_rate * 1.1))

    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Plot saved to {output_path}")
    return output_path


def generate_convergence_plot(
    results_path: str = "data/processed/convergence_results.json",
    output_path: str = "data/processed/success_rate_vs_steps.png"
) -> str:
    """
    Main function to generate the Success Rate vs. Steps plot from convergence results.
    
    Args:
        results_path: Path to the convergence results JSON file
        output_path: Path where the plot will be saved
    
    Returns:
        Path to the generated plot file
    """
    logger.info(f"Loading convergence results from {results_path}")
    results = load_convergence_results(results_path)
    
    logger.info("Extracting plot data")
    baseline_steps, baseline_rates, experimental_steps, experimental_rates = extract_plot_data(results)
    
    logger.info(f"Baseline runs: {len(baseline_steps)}, Experimental runs: {len(experimental_steps)}")
    
    if not baseline_steps and not experimental_steps:
        raise ValueError("No data found in convergence results to generate plot.")
    
    logger.info(f"Generating plot and saving to {output_path}")
    create_success_rate_vs_steps_plot(
        baseline_steps, 
        baseline_rates, 
        experimental_steps, 
        experimental_rates, 
        output_path
    )
    
    return output_path


def main():
    """Entry point for script execution."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    results_path = project_root / "data" / "processed" / "convergence_results.json"
    output_path = project_root / "data" / "processed" / "success_rate_vs_steps.png"
    
    try:
        result_path = generate_convergence_plot(
            results_path=str(results_path),
            output_path=str(output_path)
        )
        print(f"Successfully generated plot: {result_path}")
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
