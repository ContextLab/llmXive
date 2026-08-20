"""
Standalone script to validate that teacher_routing_dataset.parquet contains 
samples from both ImageNet-1K and LAION-400M sources.
"""
import argparse
import sys
import json
from pathlib import Path
import pandas as pd

def main():
    parser = argparse.ArgumentParser(
        description="Validate that teacher_routing_dataset.parquet contains samples from both ImageNet-1K and LAION-400M."
    )
    parser.add_argument(
        "--dataset_path", 
        type=str, 
        default="data/processed/teacher_routing_dataset.parquet",
        help="Path to the teacher routing dataset"
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default="data/results/source_validation_report.json",
        help="Path to save the validation report"
    )
    
    args = parser.parse_args()
    dataset_path = Path(args.dataset_path)
    output_report = Path(args.output_report)
    
    if not dataset_path.exists():
        print(f"ERROR: Dataset file not found: {dataset_path}")
        print("This task depends on T013b and T014 completion.")
        sys.exit(1)
    
    print(f"Loading dataset from: {dataset_path}")
    try:
        df = pd.read_parquet(dataset_path)
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(df)} rows.")
    
    if 'source' not in df.columns:
        print("ERROR: Dataset is missing the 'source' column.")
        print("The dataset must contain a 'source' column indicating the origin (imagenet-1k or laion-400m).")
        sys.exit(1)
    
    source_counts = df['source'].value_counts().to_dict()
    print(f"Source distribution: {source_counts}")
    
    required_sources = {'imagenet-1k', 'laion-400m'}
    found_sources = set(source_counts.keys())
    missing_sources = required_sources - found_sources
    
    if missing_sources:
        print(f"VALIDATION FAILED: Missing required sources: {missing_sources}")
        print(f"Found sources: {found_sources}")
        print("The dataset must contain samples from BOTH ImageNet-1K and LAION-400M.")
        
        report = {
            "status": "failed",
            "dataset_path": str(dataset_path),
            "total_rows": len(df),
            "source_counts": source_counts,
            "missing_sources": list(missing_sources),
            "found_sources": list(found_sources),
            "message": f"Missing required sources: {missing_sources}"
        }
    else:
        print("VALIDATION PASSED: Dataset contains samples from both ImageNet-1K and LAION-400M.")
        
        report = {
            "status": "passed",
            "dataset_path": str(dataset_path),
            "total_rows": len(df),
            "source_counts": source_counts,
            "found_sources": list(found_sources),
            "message": "Dataset contains samples from both required sources."
        }
    
    # Ensure output directory exists
    output_report.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_report, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Validation report saved to: {output_report}")
    
    if report["status"] == "failed":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()