import sys
import argparse
import json
from pathlib import Path

# Import the existing sensitivity module from the API surface
from src.analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_report
from src.analysis.stratify import stratify_dataframe
import pandas as pd

def main():
    """
    Execute sensitivity analysis sweep (p-values {0.01, 0.05, 0.1}) on stratified data.
    This script depends on T022 (stratify.py) and T024 (sensitivity.py).
    """
    parser = argparse.ArgumentParser(description="Execute sensitivity analysis sweep")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the stratified CSV file (output of T022)")
    parser.add_argument("--output", type=str, default="data/results/sensitivity_analysis.json",
                        help="Path to output JSON file")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load stratified data
    df = pd.read_csv(input_path)

    if 'chemistry_class' not in df.columns:
        print("Error: 'chemistry_class' column not found in input data.")
        print("Ensure T022 (stratify.py) has been run to generate this column.")
        sys.exit(1)

    # Prepare p-values for sweep
    p_values = [0.01, 0.05, 0.1]

    print(f"Running sensitivity analysis on {len(df)} records...")
    print(f"Thresholds: {p_values}")

    # Run sensitivity analysis
    # The sensitivity module is expected to accept the dataframe and p-values
    # and return a dictionary keyed by string thresholds
    results = run_sensitivity_analysis(df, p_values=p_values, seed=args.seed)

    # Save results
    save_sensitivity_report(results, output_path)

    print(f"Sensitivity analysis complete. Results saved to: {output_path}")

if __name__ == "__main__":
    main()