"""Runner script for T030: Generate scaling plot with power-law fits and reliability note.

This script orchestrates the generation of scaling_plot.pdf from scaling data
produced by run_scaling_experiment.py.
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main as scaling_plot_main


def build_parser():
    """Build argument parser for scaling plot runner."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Run scaling plot generation (T030)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=code_dir / ".." / "data" / "scaling_results.csv",
        help="Path to input scaling data CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=code_dir / ".." / "results" / "scaling_plot.pdf",
        help="Path to output PDF.",
    )
    parser.add_argument(
        "--note",
        type=str,
        default="Note: 3 data points limit power-law reliability.",
        help="Custom note text about data limitations.",
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Resolve paths relative to project root
    project_root = code_dir.parent
    input_path = args.input if args.input.is_absolute() else project_root / args.input
    output_path = args.output if args.output.is_absolute() else project_root / args.output

    # Ensure input file exists
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Run scaling plot generation
    return scaling_plot_main()


if __name__ == "__main__":
    sys.exit(main())
