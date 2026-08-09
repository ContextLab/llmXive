import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent))

from graph_metrics import compute_graph_metrics, scan_preprocessed_directory

def load_preprocessed_subjects(
    processed_dir: Path,
    max_subjects: int = 10
) -> List[Dict[str, Any]]:
    """
    Scan the processed directory for preprocessed subjects and return metadata.
    This function identifies subjects that have been successfully preprocessed.
    
    Args:
        processed_dir: Path to the data/processed directory
        max_subjects: Maximum number of subjects to process (N=10 limit)
        
    Returns:
        List of dictionaries containing subject_id and file_path
    """
    subjects = []
    if not processed_dir.exists():
        return subjects
        
    # Look for directories named like sub-XXXX
    for item in sorted(processed_dir.iterdir()):
        if item.is_dir() and item.name.startswith("sub-"):
            # Check for preprocessed NIfTI file (e.g., sub-XXXX_desc-preproc_bold.nii.gz)
            nifti_files = list(item.glob("*_desc-preproc_bold.nii.gz"))
            if nifti_files:
                subjects.append({
                    "subject_id": item.name,
                    "file_path": str(nifti_files[0])
                })
                if len(subjects) >= max_subjects:
                    break
                    
    return subjects

def aggregate_metrics_to_csv(
    metrics_list: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Aggregate graph metrics from a list of dictionaries into a CSV file.
    
    Args:
        metrics_list: List of dictionaries with keys: subject_id, metric_name, value
        output_path: Path to write the CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['subject_id', 'metric_name', 'value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for metric in metrics_list:
            writer.writerow({
                'subject_id': metric['subject_id'],
                'metric_name': metric['metric_name'],
                'value': f"{metric['value']:.6f}"
            })

def main():
    """
    Main entry point for aggregating graph metrics.
    Reads preprocessed subjects, computes metrics, and writes to CSV.
    """
    base_dir = Path(__file__).parent.parent
    processed_dir = base_dir / "data" / "processed"
    output_path = processed_dir / "graph_metrics.csv"
    
    print(f"Scanning processed directory: {processed_dir}")
    
    # Load preprocessed subjects
    subjects = load_preprocessed_subjects(processed_dir, max_subjects=10)
    
    if not subjects:
        print("No preprocessed subjects found. Exiting.")
        sys.exit(1)
        
    print(f"Found {len(subjects)} preprocessed subjects.")
    
    all_metrics = []
    
    for subject in subjects:
        subject_id = subject['subject_id']
        file_path = subject['file_path']
        
        print(f"Processing {subject_id}...")
        
        try:
            # Compute graph metrics for this subject
            metrics = compute_graph_metrics(file_path, subject_id)
            all_metrics.extend(metrics)
        except Exception as e:
            print(f"Error processing {subject_id}: {e}")
            continue
            
    if not all_metrics:
        print("No metrics computed. Exiting.")
        sys.exit(1)
        
    # Write aggregated metrics to CSV
    aggregate_metrics_to_csv(all_metrics, output_path)
    print(f"Successfully wrote {len(all_metrics)} metric records to {output_path}")

if __name__ == "__main__":
    main()
