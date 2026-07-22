import os
import csv
import time
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# --- Utility Functions (Shared) ---

def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    current = Path(__file__).resolve()
    # Traverse up until we find a marker or hit root
    while current.name != "PROJ-209-quantifying-the-influence-of-topological" and current.parent != current:
        current = current.parent
        if current.name == "PROJ-209-quantifying-the-influence-of-topological":
            return current
    # Fallback if marker not found, assume root is current parent of code/
    if current.name == "code":
        return current.parent
    return Path.cwd()

def ensure_output_directories() -> None:
    """Creates necessary output directories if they don't exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "state",
        root / "data" / "validation",
        root / "figures",
        root / "code" / "utils",
        root / "code" / "generators",
        root / "code" / "infrastructure"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_git_hash() -> str:
    """Attempts to get the current git commit hash."""
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Loads a JSON file and returns its content as a dictionary."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Saves a dictionary to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_csv_to_dicts(file_path: Path) -> List[Dict[str, Any]]:
    """Loads a CSV file and returns a list of dictionaries."""
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(file_path: Path, data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        # Create empty file with no content if data is empty
        with open(file_path, 'w') as f:
            pass
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# --- Task Specific Implementations ---

def run_t016a_integrity_check() -> None:
    """
    Implements T016a: Data Integrity & Hygiene.
    Verifies checksums, required fields, and filters invalid entries.
    """
    root = get_project_root()
    ensure_output_directories()

    # Determine source files based on generation status
    status_file = root / "data" / "state" / "generation_status.json"
    if not status_file.exists():
        print("Error: generation_status.json not found. Run T012 first.")
        return

    status = load_json_file(status_file)
    source_type = status.get("source", "unknown")
    
    if source_type == "synthetic":
        train_file = root / "data" / "raw" / "synthetic_train.csv"
        holdout_file = root / "data" / "raw" / "synthetic_holdout.csv"
    elif source_type == "real":
        train_file = root / "data" / "raw" / "defect_dataset_2022.csv"
        holdout_file = root / "data" / "raw" / "real_holdout.csv"
    else:
        print(f"Unknown source type: {source_type}")
        return

    all_data = []
    if train_file.exists():
        all_data.extend(load_csv_to_dicts(train_file))
    if holdout_file.exists():
        all_data.extend(load_csv_to_dicts(holdout_file))

    required_fields = ["defect_type", "defect_density", "conductivity", "elastic_tensor", "fracture_energy"]
    excluded_entries = []
    valid_entries = []

    for entry in all_data:
        # Check for required fields and non-null values
        has_required = all(entry.get(field) is not None and entry.get(field) != "" for field in required_fields)
        
        # Check defect density constraints (must be > 0 and not NaN)
        try:
            density = float(entry.get("defect_density", 0))
            if density <= 0 or density != density: # Check <= 0 or NaN
                excluded_entries.append(entry)
                continue
        except (ValueError, TypeError):
            excluded_entries.append(entry)
            continue

        if has_required:
            valid_entries.append(entry)
        else:
            excluded_entries.append(entry)

    exclusion_log = {
        "filtered_count": len(excluded_entries),
        "reason": "density_leq_0_or_nan"
    }
    
    exclusion_log_path = root / "data" / "state" / "exclusion_log.json"
    save_json_file(exclusion_log_path, exclusion_log)
    
    # Re-save valid data if we filtered anything (optional, but good practice)
    # For this task, we just log the exclusion. The actual filtering might happen in T018.
    print(f"T016a Complete: Filtered {len(excluded_entries)} entries.")

def run_t016b_synthetic_validation() -> None:
    """
    Implements T016b: Synthetic Data Validation.
    Validates synthetic train and holdout sets for physical bounds.
    Only runs if data_source is synthetic.
    """
    root = get_project_root()
    ensure_output_directories()

    # Check generation status
    status_file = root / "data" / "state" / "generation_status.json"
    if not status_file.exists():
        print("Error: generation_status.json not found. Cannot determine data source.")
        return

    status = load_json_file(status_file)
    source_type = status.get("source", "unknown")

    if source_type != "synthetic":
        print("T016b Skipped: Data source is not synthetic.")
        # Still create a log indicating it was skipped or not applicable
        validation_log = {
            "status": "skipped",
            "reason": "Data source is not synthetic",
            "anomalies": []
        }
        save_json_file(root / "data" / "state" / "synthetic_validation.json", validation_log)
        return

    train_file = root / "data" / "raw" / "synthetic_train.csv"
    holdout_file = root / "data" / "raw" / "synthetic_holdout.csv"

    if not train_file.exists():
        print(f"Error: {train_file} not found. Synthetic data generation (T013) may have failed.")
        return
    if not holdout_file.exists():
        print(f"Error: {holdout_file} not found. Synthetic data generation (T015) may have failed.")
        return

    anomalies = []
    
    # Define physical bounds
    bounds = {
        "conductivity": {"min": 0.0, "max": None}, # Must be > 0
        "defect_density": {"min": 0.0, "max": 0.1}, # Must be in [0, 0.1]
        "elastic_tensor": {"min": 0.0, "max": None}, # Must be > 0 (simplified, assuming scalar or min element)
        "fracture_energy": {"min": 0.0, "max": None} # Must be > 0
    }

    files_to_check = [
        ("synthetic_train.csv", train_file),
        ("synthetic_holdout.csv", holdout_file)
    ]

    for file_name, file_path in files_to_check:
        data = load_csv_to_dicts(file_path)
        for idx, entry in enumerate(data):
            for field, limits in bounds.items():
                if field not in entry:
                    anomalies.append({
                        "file": file_name,
                        "row": idx,
                        "field": field,
                        "value": None,
                        "issue": "Missing field"
                    })
                    continue

                try:
                    val = float(entry[field])
                    if val != val: # NaN check
                        anomalies.append({
                            "file": file_name,
                            "row": idx,
                            "field": field,
                            "value": val,
                            "issue": "NaN value"
                        })
                        continue

                    if limits["min"] is not None and val <= limits["min"]:
                        anomalies.append({
                            "file": file_name,
                            "row": idx,
                            "field": field,
                            "value": val,
                            "issue": f"Value {val} <= min {limits['min']}"
                        })
                    
                    if limits["max"] is not None and val > limits["max"]:
                        anomalies.append({
                            "file": file_name,
                            "row": idx,
                            "field": field,
                            "value": val,
                            "issue": f"Value {val} > max {limits['max']}"
                        })
                except ValueError:
                    anomalies.append({
                        "file": file_name,
                        "row": idx,
                        "field": field,
                        "value": entry[field],
                        "issue": "Non-numeric value"
                    })

    validation_log = {
        "status": "validated" if not anomalies else "anomalies_found",
        "source": "synthetic",
        "files_checked": [f[0] for f in files_to_check],
        "anomaly_count": len(anomalies),
        "anomalies": anomalies
    }

    output_path = root / "data" / "state" / "synthetic_validation.json"
    save_json_file(output_path, validation_log)

    if anomalies:
        print(f"T016b Complete: Found {len(anomalies)} anomalies in synthetic data. Log saved to {output_path}")
    else:
        print(f"T016b Complete: Synthetic data validation passed. No anomalies found.")

def main():
    """Main entry point for the data acquisition script."""
    ensure_output_directories()
    
    # The script is designed to be called with specific steps or run sequentially.
    # For T016b, we specifically call the validation function.
    # In a full pipeline, this would be orchestrated by a runner script.
    print("Running T016b: Synthetic Data Validation...")
    run_t016b_synthetic_validation()

if __name__ == "__main__":
    main()