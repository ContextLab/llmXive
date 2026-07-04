"""
Scaling Plot Generator for User Story 3.
Generates scaling_plot.pdf with fitted power-law curves and explicit reliability notes.
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
import pandas as pd

# Try to import plotting libraries; if missing, we will still compute but warn
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for serverless/headless
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Local imports from existing API surface
from analysis.scaling import fit_power_law, load_scaling_data

def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Compute power law: y = a * x^b"""
    return a * (x ** b)

def load_scaling_data_real(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load scaling data from CSV.
    If no path provided, looks for default location.
    """
    if input_path:
        path = Path(input_path)
    else:
        # Default path based on project structure
        path = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_data.csv")
    
    if not path.exists():
        raise FileNotFoundError(f"Scaling data not found at {path}")
    
    df = pd.read_csv(path)
    return df

def generate_scaling_plot_with_notes(
    input_csv: str,
    output_pdf: str,
    agent_counts: List[int] = [3, 5, 7]
) -> Dict[str, Any]:
    """
    Generate scaling plot with power-law fits and reliability notes.
    
    Args:
        input_csv: Path to scaling data CSV
        output_pdf: Path to output PDF
        agent_counts: List of agent counts to plot (default: 3, 5, 7)
    
    Returns:
        Dictionary with plot metadata and fit results
    """
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib is required to generate plots. "
            "Install with: pip install matplotlib"
        )

    # Load data
    df = load_scaling_data_real(input_csv)
    
    # Validate required columns
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Filter for specified agent counts
    df_plot = df[df['agent_count'].isin(agent_counts)].copy()
    
    if len(df_plot) == 0:
        raise ValueError(f"No data found for agent counts: {agent_counts}")
    
    # Aggregate by agent_count (mean and std)
    agg_df = df_plot.groupby('agent_count').agg({
        'specialization_index': ['mean', 'std'],
        'retrieval_efficiency': ['mean', 'std']
    }).reset_index()
    agg_df.columns = ['agent_count', 'spec_mean', 'spec_std', 'ret_mean', 'ret_std']
    agg_df = agg_df.sort_values('agent_count')
    
    # Prepare arrays for fitting
    x = np.array(agg_df['agent_count'].values, dtype=float)
    y_spec = np.array(agg_df['spec_mean'].values, dtype=float)
    y_ret = np.array(agg_df['ret_mean'].values, dtype=float)
    
    # Fit power laws
    fit_results = {}
    
    # Fit specialization index
    try:
        popt_spec, perr_spec = fit_power_law(x, y_spec)
        fit_results['specialization'] = {
            'params': popt_spec,
            'error': perr_spec,
            'exponent': popt_spec[1] if len(popt_spec) > 1 else 0
        }
    except Exception as e:
        warnings.warn(f"Could not fit specialization power law: {e}")
        fit_results['specialization'] = {'params': None, 'error': None, 'exponent': None}
    
    # Fit retrieval efficiency
    try:
        popt_ret, perr_ret = fit_power_law(x, y_ret)
        fit_results['retrieval'] = {
            'params': popt_ret,
            'error': perr_ret,
            'exponent': popt_ret[1] if len(popt_ret) > 1 else 0
        }
    except Exception as e:
        warnings.warn(f"Could not fit retrieval power law: {e}")
        fit_results['retrieval'] = {'params': None, 'error': None, 'exponent': None}
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot specialization index
    ax1.errorbar(
        x, y_spec, 
        yerr=agg_df['spec_std'].values,
        fmt='o', 
        capsize=5, 
        label='Measured',
        color='blue',
        alpha=0.7
    )
    
    # Plot fitted curve
    if fit_results['specialization']['params'] is not None:
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = power_law(x_fit, *fit_results['specialization']['params'])
        ax1.plot(x_fit, y_fit, '--', color='blue', 
                label=f'Power-law fit (β={fit_results["specialization"]["exponent"]:.3f})')
    
    ax1.set_xlabel('Number of Agents (N)')
    ax1.set_ylabel('Specialization Index')
    ax1.set_title('Specialization Index vs. Agent Count')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot retrieval efficiency
    ax2.errorbar(
        x, y_ret,
        yerr=agg_df['ret_std'].values,
        fmt='s',
        capsize=5,
        label='Measured',
        color='green',
        alpha=0.7
    )
    
    # Plot fitted curve
    if fit_results['retrieval']['params'] is not None:
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = power_law(x_fit, *fit_results['retrieval']['params'])
        ax2.plot(x_fit, y_fit, '--', color='green',
                label=f'Power-law fit (β={fit_results["retrieval"]["exponent"]:.3f})')
    
    ax2.set_xlabel('Number of Agents (N)')
    ax2.set_ylabel('Retrieval Efficiency')
    ax2.set_title('Retrieval Efficiency vs. Agent Count')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # Add explicit reliability note (as requested in task)
    note_text = (
        "NOTE: 3 data points limit power-law reliability.\n"
        "Exponents should be interpreted with caution."
    )
    fig.text(
        0.5, 0.02, 
        note_text,
        ha='center', 
        va='bottom', 
        fontsize=9, 
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Adjust layout to make room for note
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    
    # Save to PDF
    plt.savefig(output_pdf, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return {
        'output_path': output_pdf,
        'data_points': len(x),
        'agent_counts': list(x),
        'fit_results': fit_results,
        'note_included': True
    }

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling plot generation."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability notes'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_data.csv',
        help='Input CSV file with scaling data'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf',
        help='Output PDF file path'
    )
    parser.add_argument(
        '--agents',
        type=str,
        default='3,5,7',
        help='Comma-separated list of agent counts to include'
    )
    return parser

def main():
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agent counts
    agent_counts = [int(x.strip()) for x in args.agents.split(',')]
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating scaling plot...")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Agent counts: {agent_counts}")
    
    try:
        result = generate_scaling_plot_with_notes(
            input_csv=args.input,
            output_pdf=str(output_path),
            agent_counts=agent_counts
        )
        
        print(f"✓ Plot generated successfully")
        print(f"  Data points: {result['data_points']}")
        print(f"  Note included: {result['note_included']}")
        
        if result['fit_results']['specialization']['exponent'] is not None:
            print(f"  Specialization exponent: {result['fit_results']['specialization']['exponent']:.3f}")
        if result['fit_results']['retrieval']['exponent'] is not None:
            print(f"  Retrieval exponent: {result['fit_results']['retrieval']['exponent']:.3f}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        print("  Make sure scaling_data.csv exists. Run the scaling experiment first.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Error generating plot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
