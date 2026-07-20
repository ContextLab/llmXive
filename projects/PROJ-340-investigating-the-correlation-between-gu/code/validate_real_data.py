"""
Real Data Validation Script (T048b).

This script validates the pipeline's readiness for real-world data ingestion.
It attempts to load real data (if available) or simulates a fetch failure
to ensure the pipeline halts correctly without fabricating data.

Output: data/results/real_data_validation_report.json
"""
import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

# Project imports (matching API surface)
from config import get_config, load_config
from ingest import load_schema, validate_variables, load_data

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
REPORT_PATH = DATA_RESULTS_DIR / "real_data_validation_report.json"

# Ensure output directory exists
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json_file(path: Path) -> dict:
    """Load a JSON file if it exists."""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(path: Path, data: dict) -> None:
    """Save data to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def run_validation_pipeline(mode: str = "real_data", config_path: str = None) -> dict:
    """
    Run the validation pipeline against real data or a simulated failure.

    Args:
        mode: "real_data" (attempt fetch) or "simulated_failure" (force error).
        config_path: Optional path to config file.

    Returns:
        Dictionary containing the validation report.
    """
    start_time = time.time()
    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "metrics": {},
        "execution_time_seconds": 0.0,
        "attempting_real_data": mode == "real_data",
        "data_source": None,
        "data_path": None,
        "sample_size": None,
        "variables_loaded": [],
        "missing_variables": []
    }

    try:
        # Load configuration
        config = load_config(config_path) if config_path else get_config()
        schema_path = PROJECT_ROOT / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "dataset.schema.yaml"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema = load_schema(schema_path)

        if mode == "simulated_failure":
            # Simulate a missing data scenario
            raise FileNotFoundError(
                "Real data file not found at data/raw/real_data.csv. "
                "Real data fetch failed. Execution halted to prevent fabrication."
            )

        # Attempt to find real data
        # In a real scenario, this would be a specific file or a fetch call
        # For T048b, we check for a generic placeholder or specific expected file
        possible_files = list(DATA_RAW_DIR.glob("*.csv")) + list(DATA_RAW_DIR.glob("*.tsv"))

        if not possible_files:
            raise FileNotFoundError(
                "No real data files found in data/raw/. "
                "The pipeline is configured for real data but no source is present. "
                "This validates the 'fail loud' constraint (T043)."
            )

        # Assume the first valid file for this validation run
        data_path = possible_files[0]
        report["data_path"] = str(data_path)
        report["data_source"] = "Local file: " + data_path.name

        # Validate variables
        # Note: This is a validation step, not a full analysis run
        # We check if the file can be loaded and if it meets schema requirements
        try:
            df = load_data(data_path)
            report["sample_size"] = len(df)
            
            # Validate variables against schema
            missing_vars = validate_variables(df, schema)
            report["variables_loaded"] = list(df.columns)
            report["missing_variables"] = missing_vars

            if missing_vars:
                report["warnings"].append({
                    "type": "PartialVariableMatch",
                    "message": f"Missing required variables: {missing_vars}",
                    "recommendation": "Check data source completeness or update schema."
                })
                report["status"] = "warning_partial_match"
            else:
                report["status"] = "success"

        except Exception as e:
            # If load_data fails (e.g., bad format), capture it
            report["errors"].append({
                "type": type(e).__name__,
                "message": str(e),
                "recommendation": "Verify data format and encoding."
            })
            report["status"] = "failed_load_error"

    except FileNotFoundError as e:
        # This is the expected path for "no real data" scenarios
        report["errors"].append({
            "type": "MissingDataError",
            "message": str(e),
            "recommendation": "No verified real dataset found. Consider T048a (multi-cohort strategy) or T049-T054 (data sourcing)."
        })
        report["status"] = "failed_no_real_data"

    except Exception as e:
        report["errors"].append({
            "type": type(e).__name__,
            "message": str(e),
            "recommendation": "Unexpected error during validation."
        })
        report["status"] = "failed_unexpected_error"

    finally:
        end_time = time.time()
        report["execution_time_seconds"] = round(end_time - start_time, 3)

    return report


def main():
    parser = argparse.ArgumentParser(description="Validate real data pipeline readiness (T048b)")
    parser.add_argument(
        "--mode",
        choices=["real_data", "simulated_failure"],
        default="real_data",
        help="Mode: 'real_data' to check for actual files, 'simulated_failure' to test error handling."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional)."
    )
    args = parser.parse_args()

    print(f"Starting real data validation (Mode: {args.mode})...")
    
    report = run_validation_pipeline(mode=args.mode, config_path=args.config)
    
    # Save report
    save_json_file(REPORT_PATH, report)
    
    print(f"Validation complete. Status: {report['status']}")
    print(f"Report saved to: {REPORT_PATH}")
    
    # Print summary
    if report["errors"]:
        print("\nErrors encountered:")
        for err in report["errors"]:
            print(f"  - [{err['type']}] {err['message']}")
    
    if report["warnings"]:
        print("\nWarnings:")
        for warn in report["warnings"]:
            print(f"  - [{warn['type']}] {warn['message']}")

    # Exit with error code if critical failure
    if report["status"].startswith("failed"):
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
