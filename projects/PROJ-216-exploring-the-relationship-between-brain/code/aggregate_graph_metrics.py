import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from graph_metrics import compute_graph_metrics
from config import get_sample_limit, get_dataset_ids

def load_preprocessed_subjects() -> List[Dict[str, Any]]:
    """
    Scans data/processed/ for preprocessed subject directories.
    Returns a list of dicts containing subject_id and the path to the preprocessed NIfTI file.
    Assumes the directory structure established by T015/T017.
    """
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        raise FileNotFoundError(f"Preprocessed data directory not found: {processed_dir}")
    
    subjects = []
    # Expected pattern: data/processed/sub-<id>/sub-<id>_preprocessed_bold.nii.gz
    # or similar structure based on T015 output
    for item in processed_dir.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            subject_id = item.name
            # Look for the preprocessed file inside
            nifti_files = list(item.glob("*preprocessed*.nii.gz"))
            if not nifti_files:
                nifti_files = list(item.glob("*.nii.gz"))
            
            if nifti_files:
                subjects.append({
                    "subject_id": subject_id,
                    "path": str(nifti_files[0])
                })
            else:
                print(f"Warning: No preprocessed NIfTI found for {subject_id}, skipping.")
    
    return subjects

def aggregate_metrics_to_csv(subjects: List[Dict[str, Any]], output_path: str) -> None:
    """
    Computes graph metrics for each subject and aggregates them into a CSV file.
    Columns: subject_id, metric_name, value
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = []
    
    # Header
    fieldnames = ["subject_id", "metric_name", "value"]

    with open(output_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for subject in subjects:
            sub_id = subject["subject_id"]
            nifti_path = subject["path"]
            
            print(f"Processing {sub_id} from {nifti_path}...")
            
            try:
                # Compute metrics using the existing graph_metrics module
                # compute_graph_metrics returns a dict of {metric_name: value}
                metrics = compute_graph_metrics(nifti_path)
                
                if not metrics:
                    print(f"Warning: No metrics computed for {sub_id}")
                    continue

                for metric_name, value in metrics.items():
                    writer.writerow({
                        "subject_id": sub_id,
                        "metric_name": metric_name,
                        "value": f"{value:.6f}"
                    })
                    results.append((sub_id, metric_name, value))
                    
            except Exception as e:
                print(f"Error processing {sub_id}: {e}")
                # Continue to next subject, but log error
                continue

    print(f"Aggregation complete. Wrote {len(results)} rows to {output_path}")

def main():
    """
    Main entry point for T025: Aggregate graph metrics to CSV.
    """
    print("Starting T025: Aggregating graph metrics...")
    
    # Load subjects (respects sample limit from config if needed, though loading is file-system based)
    # Note: The config limit usually applies to downloading. Here we just process what exists.
    # If we need to enforce the N=10 limit strictly here:
    limit = get_sample_limit()
    subjects = load_preprocessed_subjects()
    
    if not subjects:
        print("ERROR: No preprocessed subjects found in data/processed/.")
        print("Ensure T015 (preprocessing) has been run successfully.")
        sys.exit(1)

    if limit and len(subjects) > limit:
        print(f"Limiting processing to first {limit} subjects (Config N={limit}).")
        subjects = subjects[:limit]

    output_path = "data/processed/graph_metrics.csv"
    aggregate_metrics_to_csv(subjects, output_path)
    
    print("T025 completed successfully.")

if __name__ == "__main__":
    main()
