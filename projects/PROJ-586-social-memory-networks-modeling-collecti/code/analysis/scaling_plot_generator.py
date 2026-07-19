"""
Scaling Plot Generator for Social Memory Networks.

Generates the scaling_plot.pdf with fitted power-law curves for specialization
index and retrieval efficiency, including a text note about the limitation of
having only 3 data points.

This module implements Task T030: Generate scaling_plot.pdf with fitted power-law
curves and an explicit text note stating that "3 data points limit power-law reliability".
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Import from existing project modules
try:
    from analysis.scaling import load_scaling_data, aggregate_by_agent_count, fit_power_law
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis.scaling import load_scaling_data, aggregate_by_agent_count, fit_power_law


def generate_scaling_plot_with_notes(
    results_path: str,
    output_path: str,
    agent_counts: Optional[List[int]] = None,
    note_text: str = "3 data points limit power-law reliability"
) -> Dict[str, Any]:
    """
    Generate the scaling plot with power-law fits and reliability notes.
    
    Args:
        results_path: Path to the scaling results JSON file.
        output_path: Path for the output PDF file.
        agent_counts: Optional list of agent counts to plot.
        note_text: Text note to include about data point limitations.
        
    Returns:
        Dictionary with plot metadata and fit results.
    """
    # Load scaling data
    data = load_scaling_data(results_path)
    
    if not data:
        raise ValueError(f"No scaling data found at {results_path}")
    
    # Aggregate by agent count
    aggregated = aggregate_by_agent_count(data)
    
    if not aggregated:
        raise ValueError("Aggregated scaling data is empty")
    
    # Extract agent counts and metrics
    agent_counts_list = sorted(aggregated.keys())
    
    if agent_counts is None:
        agent_counts = agent_counts_list
    
    # Filter to requested agent counts
    available_counts = [c for c in agent_counts if c in aggregated]
    
    if len(available_counts) < 2:
        raise ValueError(f"Need at least 2 agent counts for scaling analysis, got {len(available_counts)}")
    
    # Prepare data for plotting
    x_values = np.array(available_counts)
    y_spec = np.array([aggregated[c]['specialization_index'] for c in available_counts])
    y_retrieval = np.array([aggregated[c]['retrieval_efficiency'] for c in available_counts])
    
    # Fit power-law curves
    spec_fit = fit_power_law(x_values, y_spec)
    retrieval_fit = fit_power_law(x_values, y_retrieval)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot specialization index
    ax.scatter(x_values, y_spec, color='blue', label='Specialization Index', s=100, zorder=5)
    if spec_fit['r_squared'] > 0:
        x_fit = np.linspace(min(x_values), max(x_values), 100)
        y_fit_spec = spec_fit['coefficient'] * np.power(x_fit, spec_fit['exponent'])
        ax.plot(x_fit, y_fit_spec, 'b--', label=f'Specialization Fit (β={spec_fit["exponent"]:.3f})', linewidth=2)
    
    # Plot retrieval efficiency (right axis)
    ax2 = ax.twinx()
    ax2.scatter(x_values, y_retrieval, color='red', label='Retrieval Efficiency', s=100, zorder=5, marker='s')
    if retrieval_fit['r_squared'] > 0:
        y_fit_retrieval = retrieval_fit['coefficient'] * np.power(x_fit, retrieval_fit['exponent'])
        ax2.plot(x_fit, y_fit_retrieval, 'r--', label=f'Retrieval Fit (β={retrieval_fit["exponent"]:.3f})', linewidth=2)
    
    # Labels and title
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Specialization Index', color='blue', fontsize=12)
    ax2.set_ylabel('Retrieval Efficiency', color='red', fontsize=12)
    ax.set_title('Scaling Analysis: Collective Memory Metrics vs. Agent Count', fontsize=14)
    
    # Add reliability note as text on the plot
    note_position = (0.02, 0.02)  # Bottom-left corner
    ax.text(note_position[0], note_position[1], 
            note_text, 
            transform=ax.transAxes,
            fontsize=10, 
            verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Legends
    lines_1, labels_1 = ax.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Save to PDF
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight', dpi=150)
    plt.close()
    
    # Return metadata
    return {
        'output_path': str(output_file),
        'agent_counts': available_counts,
        'specialization_fit': spec_fit,
        'retrieval_fit': retrieval_fit,
        'note': note_text,
        'data_points': len(available_counts),
        'note_on_limitation': len(available_counts) <= 3
    }


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability notes.'
    )
    parser.add_argument(
        '--results',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_results.json',
        help='Path to scaling results JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf',
        help='Path for output PDF file'
    )
    parser.add_argument(
        '--agent-counts',
        type=str,
        default=None,
        help='Comma-separated list of agent counts to include (e.g., 3,5,7)'
    )
    parser.add_argument(
        '--note',
        type=str,
        default='3 data points limit power-law reliability',
        help='Text note to include about data point limitations'
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the scaling plot generator."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)
    
    # Parse agent counts if provided
    agent_counts = None
    if parsed_args.agent_counts:
        agent_counts = [int(x.strip()) for x in parsed_args.agent_counts.split(',')]
    
    try:
        result = generate_scaling_plot_with_notes(
            results_path=parsed_args.results,
            output_path=parsed_args.output,
            agent_counts=agent_counts,
            note_text=parsed_args.note
        )
        
        print(f"Scaling plot generated: {result['output_path']}")
        print(f"Agent counts: {result['agent_counts']}")
        print(f"Specialization fit exponent: {result['specialization_fit']['exponent']:.4f}")
        print(f"Retrieval fit exponent: {result['retrieval_fit']['exponent']:.4f}")
        print(f"Note: {result['note']}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())