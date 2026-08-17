import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
from utils.config import get_config


def load_dataset(dataset_path: str) -> pd.DataFrame:
    """
    Load the teacher routing dataset from a Parquet file.

    Args:
        dataset_path: Path to the Parquet file.

    Returns:
        A pandas DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the dataset is empty or cannot be loaded.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise ValueError(f"Failed to load dataset from {dataset_path}: {e}")

    if df.empty:
        raise ValueError(f"Dataset {dataset_path} is empty.")

    return df


def validate_sources(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset contains samples from both ImageNet-1K and LAION-400M.

    Args:
        df: The loaded DataFrame.
        config: Configuration dictionary containing expected source names.

    Returns:
        A tuple (is_valid, report_dict).
        is_valid: True if both sources are present, False otherwise.
        report_dict: A dictionary containing validation details (counts, missing sources, etc.).
    """
    required_sources = ["imagenet", "laion"]
    report = {
        "total_rows": len(df),
        "sources_found": [],
        "sources_missing": [],
        "source_counts": {},
        "is_valid": False
    }

    # Determine the column name for source. It might be 'source', 'dataset_source', or similar.
    # We check common variations or rely on the config if specified.
    source_col_candidates = ["source", "dataset_source", "origin", "data_source"]
    source_col = None

    # Check if config specifies the column name
    if "source_column" in config:
        source_col = config["source_column"]
    else:
        # Try to find a matching column
        for candidate in source_col_candidates:
            if candidate in df.columns:
                source_col = candidate
                break

    if not source_col:
        report["error"] = f"Could not find source column. Candidates: {source_col_candidates}. Columns found: {list(df.columns)}"
        return False, report

    if source_col not in df.columns:
        report["error"] = f"Source column '{source_col}' not found in dataset."
        return False, report

    # Get unique values and normalize them to lowercase for comparison
    unique_sources = df[source_col].astype(str).str.lower().unique()
    report["unique_sources_raw"] = list(unique_sources)

    for req_source in required_sources:
        # Check if the required source string is present in any of the unique values
        # This handles cases like "imagenet-1k" vs "imagenet"
        found = any(req_source in s for s in unique_sources)
        if found:
            report["sources_found"].append(req_source)
            # Count exact matches or partial matches
            count = sum(1 for s in unique_sources if req_source in s)
            # A more precise count would be:
            # count = df[source_col].astype(str).str.lower().apply(lambda x: req_source in x).sum()
            report["source_counts"][req_source] = count
        else:
            report["sources_missing"].append(req_source)

    if len(report["sources_missing"]) == 0:
        report["is_valid"] = True
        report["message"] = "Validation successful: Both ImageNet-1K and LAION-400M sources are present."
    else:
        report["message"] = f"Validation failed: Missing sources: {report['sources_missing']}"

    return report["is_valid"], report


def run_validation(dataset_path: str, output_path: str) -> int:
    """
    Main validation routine.

    Args:
        dataset_path: Path to the input Parquet file.
        output_path: Path to save the validation report JSON.

    Returns:
        Exit code: 0 for success, 1 for validation failure, 2 for runtime error.
    """
    config = get_config()
    print(f"Loading dataset from: {dataset_path}")

    try:
        df = load_dataset(dataset_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading dataset: {e}")
        return 2

    print(f"Dataset loaded successfully. Rows: {len(df)}")

    is_valid, report = validate_sources(df, config)

    # Save report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Validation report saved to: {output_path}")

    if is_valid:
        print("SUCCESS: Dataset contains samples from both required sources.")
        return 0
    else:
        print("FAILURE: Dataset is missing required data sources.")
        print(f"Details: {report['message']}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Validate source diversity in teacher routing dataset.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/teacher_routing_dataset.parquet",
        help="Path to the input Parquet dataset."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/source_validation_report.json",
        help="Path to save the validation report."
    )

    args = parser.parse_args()

    exit_code = run_validation(args.dataset, args.output)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()