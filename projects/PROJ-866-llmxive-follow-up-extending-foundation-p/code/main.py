"""
code.main
------------

Orchestrator script for the llmXive follow-up project.

This script implements the full simulation and analysis pipeline.
It coordinates the generation of synthetic workflows, their execution
under full and compressed context regimes, and the subsequent 
statistical analysis to identify the trade-off curve and the 
safe-operating-zone threshold.

Usage:
    python code/main.py --generate --compress --analyze
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

# Import the real analysis implementation
try:
    from analysis.tradeoff_model import main as run_analysis_pipeline
except ImportError:
    # Fallback for different project structures if necessary
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from analysis.tradeoff_model import main as run_analysis_pipeline

def _run_command(cmd: List[str], description: str) -> None:
    """Helper to run a shell command and fail loudly on error."""
    print(f"Running: {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error during {description}:")
        print(result.stderr)
        sys.exit(result.returncode)
    print(f"Successfully completed: {description}")

def main(argv: list = None) -> None:
    """
    Main entry point for the simulation orchestrator.

    Supported flags:
    * --generate: Generate synthetic workflows.
    * --compress: Execute workflows with full and compressed contexts.
    * --analyze: Run the analysis pipeline to produce result artifacts.
    """
    parser = argparse.ArgumentParser(
        description="llmXive Foundation Protocol Simulation Orchestrator"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate synthetic workflows (T012).",
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Execute full and compressed context variants (T014, T021).",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run analysis to produce tradeoff_curve.csv and threshold_report.json (T070).",
    )
    
    args = parser.parse_args(argv)

    # 1. Workflow Generation
    if args.generate:
        _run_command([
            sys.executable, "code/generators/synthetic_workflow.py",
            "--count", "500",
            "--seed", "42",
            "--output", "data/raw/workflows.json"
        ], "Workflow Generation")

    # 2. Execution (Full and Compressed)
    if args.compress:
        # Full Context Baseline
        _run_command([
            sys.executable, "code/engines/full_context.py",
            "--workflow", "data/raw/workflows.json",
            "--output", "data/processed/full_context_logs.json"
        ], "Full Context Execution")

        # Compressed Context Variants
        # Using the depth sequence specified in the project's quickstart/plan
        _run_command([
            sys.executable, "code/engines/compressed_context.py",
            "--workflow", "data/raw/workflows.json",
            "--depths", "1 2 4 6 8 10 12 14 16 18 20",
            "--output", "data/processed/compressed_context_logs.json"
        ], "Compressed Context Execution")

    # 3. Statistical Analysis
    if args.analyze:
        print("Running Analysis Pipeline...")
        # Call the real analysis implementation instead of using synthetic formulas
        run_analysis_pipeline()
        print("Analysis complete. Artifacts generated in data/results/")

    if not any([args.generate, args.compress, args.analyze]):
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()