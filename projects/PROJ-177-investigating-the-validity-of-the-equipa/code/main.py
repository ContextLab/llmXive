"""
Orchestration script for the Equipartition Theorem Investigation Pipeline.

This script manages the execution flow of the research pipeline, allowing users
to run specific stages or the full pipeline end-to-end.

Stages:
1. checksum_raw: Generate SHA-256 hashes for raw data in data/raw/
2. hash_artifacts: Update hashes for artifacts in state/
3. ingest: Ingest particle tracking data and compute energies (US1)
4. stats: Perform statistical deviation assessment (US2)
5. sensitivity: Perform sensitivity analysis (US3)
6. regression: Perform regression analysis (US4)
"""

import argparse
import sys
import os
from pathlib import Path

# Import sibling modules
from checksum_raw_data import main as checksum_main
from hash_artifacts import main as hash_main
from config import load_config, validate_config

# Import pipeline stages (these will be implemented in subsequent tasks)
# We use lazy imports inside the functions to avoid ImportError if modules aren't ready yet
# but for the purpose of this task, we define the entry points that will be called.

def run_ingestion():
    """Run the data ingestion and energy calculation pipeline (US1)."""
    try:
        from ingestion import run_pipeline
        print("Starting Data Ingestion and Energy Calculation (US1)...")
        # The actual implementation of run_pipeline will be in T012-T017
        # For now, we call it to demonstrate the orchestration flow.
        # In a real run, this would process data/raw/ and output data/derived/energy_samples.csv
        run_pipeline()
        print("Ingestion complete. Output written to data/derived/energy_samples.csv")
    except ImportError:
        print("Warning: ingestion module not yet implemented. Skipping ingestion stage.")
        return False
    except Exception as e:
        print(f"Error during ingestion: {e}")
        return False
    return True

def run_statistics():
    """Run statistical deviation assessment and hypothesis testing (US2)."""
    try:
        from stats import run_analysis
        print("Starting Statistical Analysis (US2)...")
        # The actual implementation of run_analysis will be in T021-T026
        run_analysis()
        print("Statistical analysis complete. Output written to artifacts/statistical_results.json")
    except ImportError:
        print("Warning: stats module not yet implemented. Skipping statistics stage.")
        return False
    except Exception as e:
        print(f"Error during statistics: {e}")
        return False
    return True

def run_sensitivity():
    """Run sensitivity analysis on decision thresholds (US3)."""
    try:
        from sensitivity import run_sweep
        print("Starting Sensitivity Analysis (US3)...")
        # The actual implementation of run_sweep will be in T029-T032
        run_sweep()
        print("Sensitivity analysis complete. Output written to artifacts/sensitivity_analysis_report.json")
    except ImportError:
        print("Warning: sensitivity module not yet implemented. Skipping sensitivity stage.")
        return False
    except Exception as e:
        print(f"Error during sensitivity: {e}")
        return False
    return True

def run_regression():
    """Run regression analysis of deviation drivers (US4)."""
    try:
        from regression import run_regression
        print("Starting Regression Analysis (US4)...")
        # The actual implementation of run_regression will be in T035-T039
        run_regression()
        print("Regression analysis complete. Output written to artifacts/regression_results.json")
    except ImportError:
        print("Warning: regression module not yet implemented. Skipping regression stage.")
        return False
    except Exception as e:
        print(f"Error during regression: {e}")
        return False
    return True

def run_checksum_raw():
    """Run checksum generation for raw data."""
    print("Generating checksums for raw data...")
    checksum_main()
    return True

def run_hash_artifacts():
    """Run hash generation for artifacts."""
    print("Updating artifact hashes...")
    hash_main()
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Equipartition Theorem Investigation Pipeline Orchestration"
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=[
            "all",
            "checksum_raw",
            "hash_artifacts",
            "ingest",
            "stats",
            "sensitivity",
            "regression"
        ],
        default="all",
        help="Pipeline stage to execute. Default is 'all'."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="data/config.yaml",
        help="Path to configuration file. Default is 'data/config.yaml'."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )

    args = parser.parse_args()

    # Validate config first
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)

    try:
        config = load_config(config_path)
        validate_config(config)
        if args.verbose:
            print(f"Configuration loaded successfully from {config_path}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    stages = []
    if args.stage == "all":
        stages = [
            ("checksum_raw", run_checksum_raw),
            ("hash_artifacts", run_hash_artifacts),
            ("ingest", run_ingestion),
            ("stats", run_statistics),
            ("sensitivity", run_sensitivity),
            ("regression", run_regression),
        ]
    else:
        stage_map = {
            "checksum_raw": run_checksum_raw,
            "hash_artifacts": run_hash_artifacts,
            "ingest": run_ingestion,
            "stats": run_statistics,
            "sensitivity": run_sensitivity,
            "regression": run_regression,
        }
        stages = [(args.stage, stage_map[args.stage])]

    success = True
    for stage_name, stage_func in stages:
        print(f"\n{'='*60}")
        print(f"Executing Stage: {stage_name.upper()}")
        print(f"{'='*60}")
        if not stage_func():
            success = False
            if not args.verbose:
                print(f"Stage {stage_name} failed or was skipped.")
            # In a strict pipeline, we might exit here, but we continue to report all failures
            # unless the failure is critical (e.g., missing dependency for next stage)
            # For now, we just flag it.

    print(f"\n{'='*60}")
    if success:
        print("Pipeline execution completed successfully.")
        sys.exit(0)
    else:
        print("Pipeline execution completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()