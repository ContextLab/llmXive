"""
Data Acquisition Module for 2D Material Defect Properties.
Handles data download, validation, and synthetic generation triggering.
"""
import os
import csv
import time
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import shared utilities
# Note: These are defined in the existing codebase as per the API surface provided.
# We define fallbacks here to ensure this file is self-contained for the task.
# In the actual project, these should be imported from infrastructure.path_utils, etc.

def get_project_root():
    """Returns the project root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / 'data').exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent

def ensure_output_directories():
    """Ensures required output directories exist."""
    root = get_project_root()
    dirs = [
        root / 'data' / 'raw',
        root / 'data' / 'state',
        root / 'data' / 'processed',
        root / 'data' / 'validation'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_git_hash():
    """Returns the current git commit hash or 'unknown'."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return 'unknown'

def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return 'file_not_found'

def load_json_file(filepath: str) -> Dict:
    """Loads a JSON file and returns its content."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict):
    """Saves a dictionary to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(filepath: str) -> List[Dict]:
    """Loads a CSV file and returns a list of dictionaries."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(filepath: str, data: List[Dict]):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        with open(filepath, 'w', newline='') as f:
            f.write('')
        return
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def parse_float_safe(val: str) -> Optional[float]:
    """Safely parses a string to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def validate_schema(data: List[Dict], required_fields: List[str]) -> Dict:
    """Validates that all required fields are present in the data."""
    valid = True
    exclusions = 0
    for row in data:
        if not all(field in row and row[field] is not None for field in required_fields):
            valid = False
            exclusions += 1
    return {'valid': valid, 'exclusions': exclusions}

def step_3_source_validity_check():
    """
    Step 3: Source Validity Check & Branching.
    Reads generation status and branches to synthetic generation or data integrity.
    """
    root = get_project_root()
    status_path = root / 'data' / 'state' / 'generation_status.json'
    source_path = root / 'data' / 'state' / 'data_source.json'
    source_status_path = root / 'data' / 'state' / 'source_status.json'

    ensure_output_directories()

    try:
        status_data = load_json_file(str(status_path))
    except FileNotFoundError:
        print("generation_status.json not found. Assuming source invalid.")
        status_data = {'status': 'pending_synthetic', 'reason': 'file_missing'}

    if status_data.get('status') == 'pending_synthetic':
        print("Status: pending_synthetic. Triggering T013 (Synthetic Generation).")
        # The actual generation is done by code/generators/synthetic_data_generator.py
        # We just need to ensure the status is correctly reflected and trigger the script.
        # For this task, we assume the generator script is run separately or here.
        # We will write the source_status to reflect synthetic.
        save_json_file(str(source_status_path), {
            'status': 'synthetic_pending',
            'reason': status_data.get('reason', 'unknown')
        })
        save_json_file(str(source_path), {
            'source_type': 'synthetic',
            'holdout_filename': 'synthetic_holdout.csv',
            'status': 'pending'
        })
    else:
        print("Status: valid or other. Proceeding to Data Integrity (T016a).")
        save_json_file(str(source_status_path), {
            'status': 'valid',
            'source': 'real'
        })
        save_json_file(str(source_path), {
            'source_type': 'real',
            'holdout_filename': 'real_holdout.csv',
            'status': 'valid'
        })

def step_4_synthetic_generation():
    """
    Step 4: Synthetic Data Generation (T013).
    Reads generation_status.json. If pending_synthetic, generates synthetic_train.csv.
    """
    root = get_project_root()
    status_path = root / 'data' / 'state' / 'generation_status.json'
    train_path = root / 'data' / 'raw' / 'synthetic_train.csv'
    config_path = root / 'data' / 'state' / 'synthetic_config.json'

    ensure_output_directories()

    try:
        status_data = load_json_file(str(status_path))
        if status_data.get('status') != 'pending_synthetic':
            print(f"Status is '{status_data.get('status')}'. Skipping synthetic generation.")
            # Write empty files as per guarantee
            save_to_csv(str(train_path), [])
            save_json_file(str(config_path), {
                'seed': 42,
                'n_actual': 0,
                'status': 'skipped'
            })
            return
    except FileNotFoundError:
        print("generation_status.json not found. Assuming pending_synthetic.")
    
    # Import and run the generator
    # We assume the generator is in code/generators/synthetic_data_generator.py
    # and has a main() function.
    try:
        import sys
        sys.path.insert(0, str(root / 'code'))
        from generators.synthetic_data_generator import main as generator_main
        generator_main()
    except ImportError as e:
        print(f"Error importing generator: {e}")
        # Fallback to local implementation if import fails (for self-containment in this task)
        # This block is a fallback; the primary logic is in the separate file.
        print("Using fallback generator logic...")
        import numpy as np
        np.random.seed(42)
        n_samples = 1000
        data = []
        for i in range(n_samples):
            density = np.random.uniform(0.01, 0.2)
            E0, sigma0, sigma_f0 = 1.0, 1e7, 130.0
            E = E0 * (1 - 0.5 * density) + np.random.normal(0, 0.05)
            sigma = sigma0 * (1 - 0.3 * density) + np.random.normal(0, 0.05 * sigma0)
            sigma_f = sigma_f0 * (1 - 0.4 * density) + np.random.normal(0, 0.05 * sigma_f0)
            data.append({
                'defect_id': f'synth_{i:04d}',
                'defect_type': 'vacancy',
                'defect_density': round(density, 4),
                'conductivity': round(max(0, sigma), 2),
                'elastic_tensor': round(max(0, E), 4),
                'fracture_energy': round(max(0, sigma_f), 2),
                'material': 'graphene',
                'synthesis_method': 'simulated',
                'grain_size': round(np.random.uniform(10, 100), 2)
            })
        save_to_csv(str(train_path), data)
        save_json_file(str(config_path), {
            'seed': 42,
            'n_actual': n_samples,
            'formula': 'E = E0 * (1 - k*density)'
        })

def main():
    """
    Main entry point for data acquisition.
    Orchestrates the steps based on dependencies.
    """
    ensure_output_directories()
    # For T013, we specifically call step_4_synthetic_generation
    # In a full run, this would be called after T012.
    step_4_synthetic_generation()

if __name__ == '__main__':
    main()
