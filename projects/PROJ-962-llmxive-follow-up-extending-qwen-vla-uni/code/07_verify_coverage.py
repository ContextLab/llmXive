import os
import json
import argparse
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from utils.seeds import set_global_seed
from utils.config import get_config, get_data_params

def load_assignments(assignment_path: str) -> pd.DataFrame:
    """
    Load the cluster assignments from a Parquet file.
    Expects columns: ['sample_id', 'cluster_id'] or similar.
    """
    if not os.path.exists(assignment_path):
        raise FileNotFoundError(f"Assignment file not found at {assignment_path}")
    
    # Read parquet
    df = pd.read_parquet(assignment_path)
    
    # Validate basic schema
    required_cols = ['sample_id', 'cluster_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Assignment file missing required columns: {missing_cols}")
    
    return df

def load_clusters_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load the clustering metadata (centers, stats) from a JSON file.
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)

def calculate_coverage_stats(assignments_df: pd.DataFrame, total_samples: int) -> Dict[str, Any]:
    """
    Calculate clustering coverage statistics.
    
    Returns:
        Dict containing:
            - total_samples: Total number of ingested samples
            - assigned_samples: Number of samples assigned to a cluster
            - unassigned_samples: Number of samples with no valid cluster
            - coverage_percentage: Percentage of assigned samples
            - duplicate_assignments: Number of samples with >1 cluster (should be 0)
            - coverage_status: 'PASS' if >= 98%, else 'FAIL'
    """
    total_rows = len(assignments_df)
    
    # Check for duplicates (same sample_id appearing multiple times)
    duplicates = assignments_df[assignments_df.duplicated(subset=['sample_id'], keep=False)]
    duplicate_count = len(duplicates)
    
    # Count unique assigned samples
    unique_assigned = assignments_df['sample_id'].nunique()
    
    # Calculate unassigned (total samples - unique assigned)
    # Note: total_samples might be slightly different from total_rows if there were pre-filtering,
    # but we assume total_samples is the ground truth from ingestion.
    unassigned = max(0, total_samples - unique_assigned)
    
    coverage_pct = (unique_assigned / total_samples * 100) if total_samples > 0 else 0.0
    
    status = "PASS" if coverage_pct >= 98.0 else "FAIL"
    
    return {
        "total_samples": total_samples,
        "assigned_samples": unique_assigned,
        "unassigned_samples": unassigned,
        "duplicate_assignments": duplicate_count,
        "coverage_percentage": round(coverage_pct, 4),
        "coverage_status": status
    }

def generate_report(stats: Dict[str, Any], output_path: str) -> None:
    """
    Generate a text report of the coverage statistics and save to disk.
    """
    report_lines = [
        "=" * 60,
        "CLUSTERING COVERAGE VERIFICATION REPORT",
        "=" * 60,
        f"Total Ingested Samples: {stats['total_samples']}",
        f"Samples Assigned to Cluster: {stats['assigned_samples']}",
        f"Samples Unassigned: {stats['unassigned_samples']}",
        f"Duplicate Assignments (Should be 0): {stats['duplicate_assignments']}",
        f"Coverage Percentage: {stats['coverage_percentage']}%",
        f"Threshold: 98.0%",
        f"Status: {stats['coverage_status']}",
        "=" * 60
    ]
    
    if stats['coverage_status'] == "FAIL":
        report_lines.append("WARNING: Coverage is below 98%. Check ingestion or clustering logic.")
    
    report_text = "\n".join(report_lines)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(report_text)

def main():
    parser = argparse.ArgumentParser(description="Verify clustering coverage.")
    parser.add_argument(
        "--assignments",
        type=str,
        default="data/processed/assignments.parquet",
        help="Path to the cluster assignments parquet file."
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="data/processed/clusters.json",
        help="Path to the clustering metadata JSON file."
    )
    parser.add_argument(
        "--total-samples",
        type=int,
        default=None,
        help="Total number of ingested samples (if known). If None, inferred from ingestion log or metadata."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/coverage_report.txt",
        help="Path to save the coverage report."
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility (though not strictly needed for this read-only task)
    set_global_seed(42)
    
    # Load data
    print(f"Loading assignments from {args.assignments}...")
    assignments_df = load_assignments(args.assignments)
    
    # Determine total samples
    total_samples = args.total_samples
    if total_samples is None:
        # Try to infer from metadata or a known ingestion count file
        # For now, we assume the metadata might contain 'total_samples' or we count unique IDs in assignments if we assume 100% coverage
        # However, the task requires verifying >= 98%, so we need an external ground truth.
        # Let's check if the metadata has a 'total_samples' key.
        try:
            metadata = load_clusters_metadata(args.metadata)
            total_samples = metadata.get('total_samples')
        except Exception as e:
            print(f"Warning: Could not load total_samples from metadata: {e}")
            # Fallback: If we can't find total samples, we can't calculate coverage percentage accurately.
            # We will fail loudly.
            raise RuntimeError(
                "Cannot verify coverage: Total sample count is unknown. "
                "Provide --total-samples or ensure 'total_samples' is in clusters.json."
            )
    
    if total_samples is None or total_samples <= 0:
        raise ValueError("Total sample count must be a positive integer.")
    
    print(f"Calculating coverage stats against {total_samples} total samples...")
    stats = calculate_coverage_stats(assignments_df, total_samples)
    
    print(f"Generating report to {args.output}...")
    generate_report(stats, args.output)
    
    # Exit with error code if coverage is insufficient
    if stats['coverage_status'] == "FAIL":
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
