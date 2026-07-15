"""
Task T016b: Validate that teacher_routing_dataset.parquet contains samples from
both ImageNet-1K and LAION-400M sources.

This script loads the processed dataset and verifies the presence of source
identifiers for both required datasets. It exits with code 0 if validation
passes, or code 1 if the dataset is missing or incomplete.
"""
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd

# Import config utilities
from utils.config import get_config


def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the teacher routing dataset from Parquet."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {dataset_path}")
    
    try:
        df = pd.read_parquet(dataset_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset: {e}") from e


def validate_sources(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset contains samples from both ImageNet-1K and LAION-400M.
    
    Returns:
        Tuple of (is_valid, metadata_dict)
    """
    required_sources = config.get("data", {}).get("expected_sources", ["imagenet", "laion"])
    source_column = config.get("data", {}).get("source_column", "source")
    
    if source_column not in df.columns:
        return False, {
            "error": f"Required source column '{source_column}' not found in dataset",
            "found_columns": list(df.columns),
            "required_sources": required_sources
        }
    
    found_sources = df[source_column].unique().tolist()
    missing_sources = [s for s in required_sources if s not in found_sources]
    
    stats = {
        "total_samples": len(df),
        "unique_sources": found_sources,
        "required_sources": required_sources,
        "missing_sources": missing_sources,
        "source_counts": df[source_column].value_counts().to_dict()
    }
    
    is_valid = len(missing_sources) == 0
    
    return is_valid, stats


def run_validation(args: argparse.Namespace) -> int:
    """
    Main validation logic.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = get_config()
    dataset_path = Path(args.dataset_path) if args.dataset_path else get_config().get("paths", {}).get("processed_dataset")
    
    if not dataset_path:
        print("ERROR: No dataset path provided and no default found in config.")
        return 1
    
    dataset_path = Path(dataset_path)
    
    try:
        print(f"Loading dataset from: {dataset_path}")
        df = load_dataset(dataset_path)
        print(f"Loaded {len(df)} samples.")
        
        print("Validating data sources...")
        is_valid, stats = validate_sources(df, config)
        
        # Output stats to stdout as JSON for logging
        print(json.dumps(stats, indent=2))
        
        if not is_valid:
            print(f"VALIDATION FAILED: Missing sources: {stats['missing_sources']}")
            return 1
        
        print("VALIDATION PASSED: Dataset contains samples from all required sources.")
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during validation: {e}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate data sources in teacher routing dataset")
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=None,
        help="Path to the teacher_routing_dataset.parquet file. If not provided, uses config default."
    )
    
    args = parser.parse_args()
    exit_code = run_validation(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()