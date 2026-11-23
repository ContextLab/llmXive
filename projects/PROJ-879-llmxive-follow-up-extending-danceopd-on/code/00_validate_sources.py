import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

def load_dataset(path: str) -> pd.DataFrame:
    """Load a parquet dataset from the given path."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    return pd.read_parquet(path)

def validate_sources(df: pd.DataFrame) -> Tuple[bool, str, Dict[str, int]]:
    """
    Validate that the dataset contains samples from both ImageNet-1K and LAION-400M.
    
    Returns:
        Tuple of (is_valid, message, source_counts)
    """
    if 'source' not in df.columns:
        return False, "Dataset missing 'source' column", {}
    
    source_counts = df['source'].value_counts().to_dict()
    
    # Check for required sources
    required_sources = {'imagenet-1k', 'laion-400m'}
    found_sources = set(source_counts.keys())
    
    missing_sources = required_sources - found_sources
    
    if missing_sources:
        return False, f"Missing required sources: {missing_sources}. Found: {found_sources}", source_counts
    
    if len(found_sources) < 2:
        return False, f"Dataset must contain samples from both ImageNet-1K and LAION-400M. Found only: {found_sources}", source_counts
    
    return True, f"Validation passed. Found sources: {found_sources} with counts: {source_counts}", source_counts

def run_validation(args: argparse.Namespace) -> int:
    """
    Run source validation on the teacher routing dataset.
    
    Returns:
        0 if validation passes, 1 otherwise.
    """
    dataset_path = args.dataset_path
    report_path = args.report_path if args.report_path else str(Path(dataset_path).parent / 'validation_report.json')
    
    print(f"Validating sources in: {dataset_path}")
    
    try:
        df = load_dataset(dataset_path)
        print(f"Loaded dataset with {len(df)} rows.")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return 1
    
    is_valid, message, source_counts = validate_sources(df)
    print(message)
    
    # Save validation report
    report = {
        "dataset_path": str(dataset_path),
        "is_valid": is_valid,
        "message": message,
        "source_counts": source_counts,
        "total_rows": len(df)
    }
    
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Validation report saved to: {report_path}")
    
    return 0 if is_valid else 1

def main():
    parser = argparse.ArgumentParser(description="Validate data sources in teacher routing dataset")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to teacher_routing_dataset.parquet")
    parser.add_argument("--report_path", type=str, default=None, help="Path to save validation report (default: auto-generated)")
    
    args = parser.parse_args()
    sys.exit(run_validation(args))

if __name__ == "__main__":
    main()
