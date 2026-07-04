"""
Run scaling experiment pipeline for User Story 3.
Generates scaling data and creates the scaling plot with reliability notes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data.generate_scaling_data import build_parser as scaling_data_parser, main as scaling_data_main
from analysis.scaling_plot import build_parser as plot_parser, main as plot_main

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for full scaling experiment."""
    parser = argparse.ArgumentParser(
        description='Run full scaling experiment: generate data and plot'
    )
    parser.add_argument(
        '--agents',
        type=str,
        default='3,5,7',
        help='Comma-separated list of agent counts (default: 3,5,7)'
    )
    parser.add_argument(
        '--games',
        type=int,
        default=800,
        help='Number of games per agent count (default: 800)'
    )
    parser.add_argument(
        '--context',
        type=str,
        choices=['full', 'limited'],
        default='full',
        help='Context condition (default: full)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results',
        help='Output directory for data and plots'
    )
    parser.add_argument(
        '--skip-data',
        action='store_true',
        help='Skip data generation, only generate plot'
    )
    parser.add_argument(
        '--skip-plot',
        action='store_true',
        help='Skip plot generation, only generate data'
    )
    return parser

def main():
    """Main entry point for scaling experiment."""
    parser = build_parser()
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data_path = output_dir / 'scaling_data.csv'
    plot_path = output_dir / 'scaling_plot.pdf'
    
    exit_code = 0
    
    # Step 1: Generate scaling data
    if not args.skip_data:
        print("=" * 60)
        print("STEP 1: Generating scaling data...")
        print("=" * 60)
        
        data_args = [
            'generate_scaling_data',
            '--agents', args.agents,
            '--games', str(args.games),
            '--context', args.context,
            '--seed', str(args.seed),
            '--output', str(data_path)
        ]
        
        # Override sys.argv for the scaling data script
        old_argv = sys.argv
        sys.argv = data_args
        
        try:
            exit_code = scaling_data_main()
            if exit_code != 0:
                print("✗ Data generation failed", file=sys.stderr)
                sys.argv = old_argv
                return exit_code
        finally:
            sys.argv = old_argv
    
    # Step 2: Generate scaling plot
    if not args.skip_plot:
        print("=" * 60)
        print("STEP 2: Generating scaling plot...")
        print("=" * 60)
        
        plot_args = [
            'scaling_plot',
            '--input', str(data_path),
            '--output', str(plot_path),
            '--agents', args.agents
        ]
        
        old_argv = sys.argv
        sys.argv = plot_args
        
        try:
            exit_code = plot_main()
            if exit_code != 0:
                print("✗ Plot generation failed", file=sys.stderr)
                sys.argv = old_argv
                return exit_code
        finally:
            sys.argv = old_argv
    
    print("=" * 60)
    print("✓ Scaling experiment complete!")
    print(f"  Data: {data_path}")
    print(f"  Plot: {plot_path}")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())