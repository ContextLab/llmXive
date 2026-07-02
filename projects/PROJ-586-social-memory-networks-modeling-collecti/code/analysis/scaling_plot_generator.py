import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

# Import existing functions from sibling modules
from analysis.scaling import fit_power_law, aggregate_metrics_by_agent_count, load_scaling_data

@dataclass
class ScalingPlotResult:
    """Result of scaling plot generation."""
    success: bool
    output_path: str
    message: str
    exponent: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    is_sublinear: Optional[bool] = None

def generate_scaling_plot_with_notes(
    results_dir: Path,
    agent_counts: List[int] = [3, 5, 7],
    games_per_config: int = 800
) -> ScalingPlotResult:
    """
    Generate scaling_plot.pdf with fitted power-law curves and explicit note
    that 3 data points limit power-law reliability.

    This function:
    1. Loads aggregated metrics from results files (results_scaling_*.csv)
    2. Fits power-law models to specialization_index and retrieval_efficiency
    3. Generates a PDF plot with fitted curves
    4. Includes an explicit note about the limitation of 3 data points
    """
    try:
        # Ensure results directory exists
        results_dir.mkdir(parents=True, exist_ok=True)

        # Load scaling data
        data_path = results_dir / "scaling_metrics.csv"
        if not data_path.exists():
            # Try to aggregate from individual result files
            scaling_data = aggregate_metrics_by_agent_count(results_dir, agent_counts)
            if scaling_data.empty:
                return ScalingPlotResult(
                    success=False,
                    output_path=str(results_dir / "scaling_plot.pdf"),
                    message="No scaling data found. Run scaling experiment first."
                )
            scaling_data.to_csv(data_path, index=False)
        else:
            scaling_data = pd.read_csv(data_path)

        # Prepare data for plotting
        agent_counts_data = scaling_data['agent_count'].values
        specialization_mean = scaling_data['specialization_index_mean'].values
        specialization_std = scaling_data['specialization_index_std'].values
        retrieval_mean = scaling_data['retrieval_efficiency_mean'].values
        retrieval_std = scaling_data['retrieval_efficiency_std'].values

        # Fit power-law models
        spec_fit = fit_power_law(agent_counts_data, specialization_mean)
        retrieval_fit = fit_power_law(agent_counts_data, retrieval_mean)

        # Generate plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot specialization index
        ax1.errorbar(
            agent_counts_data,
            specialization_mean,
            yerr=specialization_std,
            fmt='o',
            label='Observed',
            capsize=5,
            color='blue'
        )
        
        # Generate fitted curve
        x_fit = np.linspace(min(agent_counts_data), max(agent_counts_data), 100)
        y_fit_spec = spec_fit['a'] * (x_fit ** spec_fit['beta'])
        ax1.plot(x_fit, y_fit_spec, 'r-', label=f'Power-law fit (β={spec_fit["beta"]:.3f})')
        ax1.set_xlabel('Number of Agents (N)')
        ax1.set_ylabel('Specialization Index')
        ax1.set_title('Specialization Index vs Agent Count')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot retrieval efficiency
        ax2.errorbar(
            agent_counts_data,
            retrieval_mean,
            yerr=retrieval_std,
            fmt='o',
            label='Observed',
            capsize=5,
            color='green'
        )
        
        y_fit_retrieval = retrieval_fit['a'] * (x_fit ** retrieval_fit['beta'])
        ax2.plot(x_fit, y_fit_retrieval, 'r-', label=f'Power-law fit (β={retrieval_fit["beta"]:.3f})')
        ax2.set_xlabel('Number of Agents (N)')
        ax2.set_ylabel('Retrieval Efficiency')
        ax2.set_title('Retrieval Efficiency vs Agent Count')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Add explicit note about 3 data points limitation
        note_text = (
            "Note: Power-law fitting performed with only 3 data points (N=3,5,7).\n"
            "This limited sample size reduces statistical power for reliable\n"
            "power-law exponent estimation. Results should be interpreted with\n"
            "caution and validated with additional agent counts."
        )
        fig.text(
            0.5, 0.02,
            note_text,
            ha='center',
            va='bottom',
            fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

        # Adjust layout to accommodate note
        plt.tight_layout(rect=[0, 0.15, 1, 1])

        # Save PDF
        output_path = results_dir / "scaling_plot.pdf"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        # Determine sublinearity
        is_sublinear_spec = spec_fit['beta'] < 1.0
        is_sublinear_retrieval = retrieval_fit['beta'] < 1.0

        return ScalingPlotResult(
            success=True,
            output_path=str(output_path),
            message=f"Successfully generated scaling plot at {output_path}",
            exponent=spec_fit['beta'],
            ci_lower=spec_fit.get('ci_lower'),
            ci_upper=spec_fit.get('ci_upper'),
            is_sublinear=is_sublinear_spec
        )

    except Exception as e:
        return ScalingPlotResult(
            success=False,
            output_path=str(results_dir / "scaling_plot.pdf"),
            message=f"Failed to generate plot: {str(e)}"
        )

def main():
    """Main entry point for scaling plot generation."""
    parser = argparse.ArgumentParser(description='Generate scaling plot with power-law fits')
    parser.add_argument('--results-dir', type=str, default='projects/PROJ-586-social-memory-networks-modeling-collecti/results',
                      help='Directory containing experiment results')
    parser.add_argument('--agent-counts', type=int, nargs='+', default=[3, 5, 7],
                      help='Agent counts to include in scaling analysis')
    parser.add_argument('--games-per-config', type=int, default=800,
                      help='Number of games per configuration')
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    result = generate_scaling_plot_with_notes(
        results_dir,
        agent_counts=args.agent_counts,
        games_per_config=args.games_per_config
    )
    
    print(result.message)
    if result.success:
        print(f"Output: {result.output_path}")
        if result.exponent is not None:
            print(f"Power-law exponent (β): {result.exponent:.4f}")
            if result.is_sublinear is not None:
                print(f"Sub-linear scaling (β < 1): {result.is_sublinear}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
