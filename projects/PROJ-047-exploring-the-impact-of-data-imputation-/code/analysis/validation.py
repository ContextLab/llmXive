"""
Validation module for schema rigor (T053).
Uses Pydantic models to enforce strict schema compliance.
"""
import os
import pandas as pd
import sys
from typing import List, Set
from .schemas import validate_simulation_summary_csv, SimulationSummaryRow


def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validates that the DataFrame contains all required columns and types
    as defined in the SimulationSummaryRow Pydantic model.
    
    Returns True if valid, raises ValueError if invalid.
    """
    try:
        validate_simulation_summary_csv(df)
        return True
    except ValueError as e:
        # Re-raise with clearer context for the CLI
        raise ValueError(f"Schema validation failed: {e}")


def main():
    """
    CLI entry point for schema validation.
    Usage: python code/analysis.py --validate-schema --input data/results/simulation_summary.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate simulation summary schema")
    parser.add_argument("--input", required=True, help="Path to simulation_summary.csv")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(args.input)
        validate_schema(df)
        print(f"Schema validation PASSED for {args.input}")
        sys.exit(0)
    except Exception as e:
        print(f"Schema validation FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
