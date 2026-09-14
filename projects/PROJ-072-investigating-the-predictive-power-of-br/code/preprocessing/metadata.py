import os
import sys
import csv
import json
import logging
from pathlib import Path
import pandas as pd

def load_exclusion_log(log_path: str) -> list:
    """Loads exclusion reasons from a log file."""
    exclusions = []
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            for line in f:
                exclusions.append(line.strip())
    return exclusions

def load_subject_status(status_path: str) -> pd.DataFrame:
    """Loads subject status from a CSV file."""
    try:
        df = pd.read_csv(status_path)
        return df
    except FileNotFoundError:
        logging.error(f"Subject status file not found: {status_path}")
        return pd.DataFrame()

def parse_diagnostic_label(label: str) -> str:
    """Parses and standardizes diagnostic labels."""
    if label is None:
        return "Unknown"
    label = label.strip().lower()
    if "schizophrenia" in label or "sz" in label:
        return "Schizophrenia"
    elif "control" in label or "hc" in label:
        return "Control"
    else:
        return "Other"

def get_diagnostic_labels_from_participants(metadata_dir: str) -> dict:
    """Extracts diagnostic labels from participant JSON sidecar files."""
    labels = {}
    metadata_dir = Path(metadata_dir)
    for file in metadata_dir.glob("*.json"):
        try:
            with open(file, "r") as f:
                data = json.load(f)
                subject_id = data.get("task-rest", {}).get("subject_id")
                if subject_id:
                    label = data.get("diagnosis")
                    labels[subject_id] = parse_diagnostic_label(label)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error processing metadata file {file}: {e}")
    return labels

def generate_subject_labels_mapping(metadata_dir: str) -> dict:
    """Generates a mapping of subject IDs to diagnostic labels."""
    labels = get_diagnostic_labels_from_participants(metadata_dir)
    return labels

def save_subject_labels(labels: dict, output_path: str) -> None:
    """Saves the subject labels mapping to a CSV file."""
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["SubjectID", "Label"])
        for subject_id, label in labels.items():
            writer.writerow([subject_id, label])

def run_metadata_pipeline(metadata_dir: str, output_path: str) -> None:
    """Runs the complete metadata pipeline."""
    labels = generate_subject_labels_mapping(metadata_dir)
    save_subject_labels(labels, output_path)

def main():
    """Main function to run the metadata pipeline."""
    metadata_dir = "data/metadata"
    output_path = "data/metadata/subject_labels.csv"
    run_metadata_pipeline(metadata_dir, output_path)

if __name__ == "__main__":
    main()
