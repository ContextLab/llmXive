"""
Main entry point for the BCC Yield Strength prediction pipeline.
Orchestrates data ingestion and feature engineering steps to produce
the required deliverables:
  - data/raw/mpea_raw.csv
  - data/processed/bcc_filtered.csv
  - data/processed/features_engineered.csv
"""
import sys
from importlib import import_module

def run_module(module_name: str) -> int:
    """Import the module and execute its main function."""
    try:
        mod = import_module(module_name)
    except Exception as e:
        print(f"Failed to import {module_name}: {e}", file=sys.stderr)
        return 1
    if not hasattr(mod, "main"):
        print(f"Module {module_name} has no main()", file=sys.stderr)
        return 1
    try:
        # Most pipeline modules call sys.exit internally on failure,
        # but we also guard against unexpected returns.
        result = mod.main()
        if result is None:
            return 0
        return int(result)
    except SystemExit as se:
        # Propagate explicit exit codes
        return se.code if isinstance(se.code, int) else 1
    except Exception as e:
        print(f"Error running {module_name}.main(): {e}", file=sys.stderr)
        return 1

def main() -> int:
    """
    Execute the pipeline in order:
    1. data_ingestion – downloads the MPEA dataset, filters BCC alloys,
       and writes `data/processed/bcc_filtered.csv`.
    2. feature_engineering – computes scalar and ILR descriptors and
       writes `data/processed/features_engineered.csv`.
    """
    steps = [
        "code.data_ingestion",
        "code.feature_engineering",
    ]

    for step in steps:
        rc = run_module(step)
        if rc != 0:
            print(f"Step {step} failed with exit code {rc}", file=sys.stderr)
            return rc

    print("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
