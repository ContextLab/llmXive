import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import get_sample_limit
from graph_metrics import compute_graph_metrics
from utils import ResourceMonitor

def load_preprocessed_subjects(
    data_dir: Path, subject_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Load preprocessed NIfTI file paths for a list of subject IDs.
    Assumes T015 has placed preprocessed files in data/processed/<subject_id>/preprocessed.nii.gz
    """
    subjects = []
    for sub_id in subject_ids:
        sub_dir = data_dir / sub_id
        nifti_path = sub_dir / "preprocessed.nii.gz"
        if nifti_path.exists():
            subjects.append(
                {"subject_id": sub_id, "nifti_path": str(nifti_path)}
            )
        else:
            # Log missing file but continue to allow partial aggregation
            print(f"Warning: Preprocessed file not found for {sub_id}: {nifti_path}")
    return subjects

def aggregate_metrics_to_csv(
    subjects: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Compute graph metrics for each subject and aggregate into a CSV file.
    Columns: subject_id, metric_name, value
    """
    rows = []
    resource_monitor = ResourceMonitor()

    for sub_data in subjects:
        sub_id = sub_data["subject_id"]
        nifti_path = Path(sub_data["nifti_path"])

        print(f"Processing subject: {sub_id}")
        resource_monitor.start_subject(sub_id)

        try:
            # Compute metrics using existing graph_metrics functions
            # compute_graph_metrics returns a dict of metric_name -> value
            metrics = compute_graph_metrics(nifti_path)

            for metric_name, value in metrics.items():
                rows.append(
                    {
                        "subject_id": sub_id,
                        "metric_name": metric_name,
                        "value": value,
                    }
                )
        except Exception as e:
            print(f"Error processing {sub_id}: {e}")
            # Optionally log error to a file, but do not halt the whole pipeline
        finally:
            resource_monitor.end_subject(sub_id)

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id", "metric_name", "value"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Aggregated metrics written to {output_path}")

def main():
    """
    Main entry point for aggregating graph metrics into CSV.
    Reads subject list from config, loads preprocessed data, computes metrics,
    and writes to data/processed/graph_metrics.csv.
    """
    config = get_sample_limit()
    sample_limit = config.get("n", 10)

    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    output_path = project_root / "data" / "processed" / "graph_metrics.csv"

    # Get subject IDs (assuming they are subdirectories in data/processed)
    # In a real scenario, this might come from a manifest or config
    # For now, we infer from directory names that look like subject IDs
    all_sub_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    subject_ids = sorted([d.name for d in all_sub_dirs])[:sample_limit]

    if not subject_ids:
        print("No preprocessed subject data found. Exiting.")
        sys.exit(1)

    subjects = load_preprocessed_subjects(data_dir, subject_ids)

    if not subjects:
        print("No valid subject data with preprocessed files found. Exiting.")
        sys.exit(1)

    aggregate_metrics_to_csv(subjects, output_path)

if __name__ == "__main__":
    main()
