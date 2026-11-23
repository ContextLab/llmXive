"""
Validate that the teacher routing dataset contains samples from both ImageNet-1K and LAION-400M sources.

This script inspects the `data/processed/teacher_routing_dataset.parquet` file,
verifies the existence of source identifiers, and ensures that both ImageNet and LAION
are represented in the final dataset.

It writes a validation report to `data/results/source_validation.json`.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

# Import from project utils
from utils.config import get_config


def load_dataset(config: Any) -> pd.DataFrame:
    """Load the teacher routing dataset from the configured path."""
    dataset_path = get_path(config, "TEACHER_ROUTING_DATASET_PATH")
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    try:
        df = pd.read_parquet(dataset_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet dataset: {e}")


def validate_sources(df: pd.DataFrame, config: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset contains samples from both ImageNet-1K and LAION-400M.
    
    Args:
        df: The loaded pandas DataFrame.
        config: The configuration object.
        
    Returns:
        A tuple of (is_valid, report_dict).
        is_valid is True if both sources are present and meet minimum counts.
        report_dict contains detailed statistics.
    """
    # Determine the column name for source identification
    # Based on T012/T014, the combined dataset should have a 'source' column
    # or similar indicator. We check for common variations.
    possible_source_cols = ['source', 'dataset_source', 'origin', 'source_dataset']
    source_col = None
    
    for col in possible_source_cols:
        if col in df.columns:
            source_col = col
            break
    
    if source_col is None:
        # Fallback: check if we can infer from image paths or other columns
        # For now, we assume the column 'source' exists as per T012 design.
        # If missing, we fail loudly.
        raise KeyError(
            f"Could not find source identifier column. "
            f"Expected one of {possible_source_cols}, but columns are: {list(df.columns)}"
        )
    
    source_counts = df[source_col].value_counts().to_dict()
    
    # Define expected source identifiers
    # These should match the values written by T012 (_data_streaming.py)
    expected_sources = ["imagenet", "laion"]
    found_sources = [s.lower() for s in source_counts.keys()]
    
    missing_sources = [s for s in expected_sources if s not in found_sources]
    
    # Minimum count threshold (can be configured, default 10)
    min_count = config.get("MIN_SOURCE_COUNT", 10)
    
    valid_counts = {}
    for source in expected_sources:
        count = source_counts.get(source, 0)
        valid_counts[source] = {
            "count": count,
            "meets_minimum": count >= min_count
        }
    
    is_valid = len(missing_sources) == 0 and all(v["meets_minimum"] for v in valid_counts.values())
    
    report = {
        "total_rows": len(df),
        "source_counts": source_counts,
        "valid_sources": valid_counts,
        "missing_sources": missing_sources,
        "is_valid": is_valid,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    return is_valid, report


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)


def run_validation() -> bool:
    """
    Main validation routine.
    
    Returns:
        True if validation passes, False otherwise.
    """
    config = get_config()
    
    output_path = Path(get_path(config, "SOURCE_VALIDATION_REPORT_PATH"))
    
    try:
        print(f"Loading dataset from {get_path(config, 'TEACHER_ROUTING_DATASET_PATH')}...")
        df = load_dataset(config)
        
        print(f"Dataset loaded with {len(df)} rows.")
        print(f"Columns: {list(df.columns)}")
        
        print("Validating source distribution...")
        is_valid, report = validate_sources(df, config)
        
        print(f"Validation result: {'PASSED' if is_valid else 'FAILED'}")
        if not is_valid:
            print(f"Missing sources: {report['missing_sources']}")
            print(f"Counts: {report['source_counts']}")
        
        save_report(report, output_path)
        print(f"Report saved to {output_path}")
        
        return is_valid
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during validation: {e}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that teacher_routing_dataset.parquet contains samples from both ImageNet and LAION."
    )
    parser.parse_args()
    
    success = run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()