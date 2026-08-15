import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

from utils.config import get_config

# Constants for source identification
IMAGENET_SOURCE_ID = "imagenet-1k"
LAION_SOURCE_ID = "laion-400m"

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """
    Load the teacher routing dataset from a Parquet file.

    Args:
        dataset_path: Path to the parquet file.

    Returns:
        DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the dataset is empty or missing required columns.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    df = pd.read_parquet(path)

    if df.empty:
        raise ValueError(f"Dataset file is empty: {dataset_path}")

    required_columns = ["source", "prompt_embedding", "noise_level", "routing_label", "velocity_vector"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    return df

def validate_sources(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset contains samples from both ImageNet-1K and LAION-400M.

    Args:
        df: The loaded dataset DataFrame.

    Returns:
        A tuple (is_valid, report_dict).
        is_valid: True if both sources are present, False otherwise.
        report_dict: Detailed statistics about the validation.
    """
    report = {
        "total_samples": len(df),
        "source_counts": {},
        "sources_present": [],
        "is_valid": False,
        "error_message": None
    }

    # Count samples per source
    source_counts = df["source"].value_counts().to_dict()
    report["source_counts"] = source_counts

    # Check for required sources
    has_imagenet = IMAGENET_SOURCE_ID in source_counts
    has_laion = LAION_SOURCE_ID in source_counts

    if has_imagenet:
        report["sources_present"].append(IMAGENET_SOURCE_ID)
    if has_laion:
        report["sources_present"].append(LAION_SOURCE_ID)

    # Validation logic
    if has_imagenet and has_laion:
        report["is_valid"] = True
        report["message"] = "Validation PASSED: Dataset contains samples from both ImageNet-1K and LAION-400M."
    else:
        missing = []
        if not has_imagenet:
            missing.append(IMAGENET_SOURCE_ID)
        if not has_laion:
            missing.append(LAION_SOURCE_ID)
        report["error_message"] = f"Validation FAILED: Missing source(s): {', '.join(missing)}"
        report["message"] = report["error_message"]

    return report["is_valid"], report

def run_validation(dataset_path: str, output_log_path: str) -> int:
    """
    Main validation routine.

    Args:
        dataset_path: Path to the input dataset.
        output_log_path: Path to write the validation report JSON.

    Returns:
        Exit code (0 for success, 1 for validation failure, 2 for runtime error).
    """
    try:
        print(f"Loading dataset from: {dataset_path}")
        df = load_dataset(dataset_path)
        print(f"Loaded {len(df)} samples.")

        print("Validating data sources...")
        is_valid, report = validate_sources(df)

        # Ensure output directory exists
        output_path = Path(output_log_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write report
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Validation report written to: {output_log_path}")

        # Print summary
        print("\n--- Validation Summary ---")
        print(f"Total Samples: {report['total_samples']}")
        print(f"Sources Found: {', '.join(report['sources_present']) if report['sources_present'] else 'None'}")
        print(f"Status: {'PASSED' if is_valid else 'FAILED'}")
        if report.get('error_message'):
            print(f"Error: {report['error_message']}")
        print("--------------------------\n")

        if not is_valid:
            return 1
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

def main():
    """Entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate that teacher_routing_dataset.parquet contains samples from both ImageNet-1K and LAION-400M."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to the teacher routing dataset parquet file. Defaults to config path."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output validation report JSON. Defaults to config path."
    )

    args = parser.parse_args()
    config = get_config()

    dataset_path = args.dataset or get_path(config, "teacher_routing_dataset_path")
    output_log_path = args.output or str(Path(get_path(config, "results_dir")) / "source_validation_report.json")

    exit_code = run_validation(dataset_path, output_log_path)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()