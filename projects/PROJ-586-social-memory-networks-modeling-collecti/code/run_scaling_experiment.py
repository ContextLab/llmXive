"""Run scaling experiment for US-3.

This script orchestrates the full scaling experiment:
1. Generates scaling data (data/scaling_results.csv)
2. Generates scaling plot (projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf)

Output paths match the task specification exactly.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data.generate_scaling_data import build_parser as scaling_data_build_parser, main as scaling_data_main
from analysis.scaling_plot_generator import build_parser as plot_build_parser, main as plot_main


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling experiment."""
    parser = argparse.ArgumentParser(
        description="Run full scaling experiment (data generation + plot)."
    )
    parser.add_argument(
        "--agent-counts",
        type=str,
        default="3,5,7",
        help="Comma-separated agent counts (default: 3,5,7)"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=800,
        help="Games per agent count (default: 800)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--context",
        type=str,
        default="full",
        choices=["full", "limited"],
        help="Context condition (default: full)"
    )
    parser.add_argument(
        "--data-output",
        type=str,
        default="data/scaling_results.csv",
        help="Output CSV path for scaling data (default: data/scaling_results.csv)"
    )
    parser.add_argument(
        "--plot-output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
        help="Output PDF path for scaling plot (default: projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf)"
    )
    parser.add_argument(
        "--no-note",
        action="store_true",
        help="Do not include the 3-point reliability note in plot"
    )
    return parser


def main() -> int:
    """Run full scaling experiment."""
    parser = build_parser()
    args = parser.parse_args()
    
    print("=" * 60)
    print("US-3 Scaling Experiment")
    print("=" * 60)
    
    # Step 1: Generate scaling data
    print("\n[1/2] Generating scaling data...")
    data_parser = scaling_data_build_parser()
    data_parser.set_defaults(
        agent_counts=args.agent_counts,
        games=args.games,
        seed=args.seed,
        context=args.context,
        output=args.data_output
    )
    data_args = data_parser.parse_args([])
    
    # Run data generation
    from data.generate_scaling_data import run_scaling_simulation
    data_path = Path(data_args.output)
    agent_counts = [int(x) for x in data_args.agent_counts.split(",")]
    
    results = run_scaling_simulation(
        agent_counts=agent_counts,
        games_per_count=data_args.games,
        seed=data_args.seed,
        context=data_args.context,
        output_path=data_path
    )
    
    if not results:
        print("✗ Failed to generate scaling data.", file=sys.stderr)
        return 1
    
    # Step 2: Generate scaling plot
    print("\n[2/2] Generating scaling plot...")
    plot_parser = plot_build_parser()
    plot_parser.set_defaults(
        data=data_args.output,
        output=args.plot_output,
        no_note=args.no_note
    )
    plot_args = plot_parser.parse_args([])
    
    from analysis.scaling_plot_generator import generate_scaling_plot_with_notes
    result = generate_scaling_plot_with_notes(
        data_path=Path(plot_args.data),
        output_path=Path(plot_args.output),
        include_reliability_note=not plot_args.no_note
    )
    
    if result.success:
        print(f"\n✓ Scaling experiment complete.")
        print(f"  Data: {result.output_path.parent / 'scaling_results.csv'}")
        print(f"  Plot: {result.output_path}")
        return 0
    else:
        print(f"✗ Failed to generate scaling plot.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())