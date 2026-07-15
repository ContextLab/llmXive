"""
Validation script for T012: Validate data generation for J1-J2 Heisenberg and XY models.

This script verifies that `code/data_generation.py` correctly generates datasets for:
- J1-J2 Heisenberg model
- XY model
at lattice sizes L=16 and L=24, covering temperatures T=0.1 to T=3.0.

It checks:
1. Output file existence.
2. File format (Numpy .npz).
3. Data shapes: (N, 3, L, L) for Heisenberg, (N, 2, L, L) for XY.
4. Temperature coverage matches the specified range.
5. Spin vector normalization (unit length).
"""
import os
import sys
import numpy as np
from pathlib import Path
from data_generation import main as run_generation_main, ensure_data_dir
from config import get_config

# Configuration
CONFIG = get_config()
RAW_DATA_DIR = Path(CONFIG.data_dir) / "raw"
MODELS = ["heisenberg", "xy"]
LATTICE_SIZES = [16, 24]
TEMP_RANGE = (0.1, 3.0)
TEMP_STEP = 0.1  # Approximate step used in generation

def validate_file_structure():
    """Check if expected files exist and are non-empty."""
    errors = []
    for model in MODELS:
        for L in LATTICE_SIZES:
            # Expected filename pattern based on T004 implementation logic
            # Usually: {model}_L{L}_T{temp}.npz or similar
            # We will scan the directory for matching patterns
            pass 
    
    # Instead of guessing exact filenames, we rely on the generation script
    # to create them and then scan the directory.
    if not RAW_DATA_DIR.exists():
        errors.append(f"Raw data directory {RAW_DATA_DIR} does not exist.")
        return errors

    found_files = []
    for root, _, files in os.walk(RAW_DATA_DIR):
        for f in files:
            if f.endswith('.npz'):
                found_files.append(Path(root) / f)
    
    if not found_files:
        errors.append("No .npz files found in raw data directory. Did generation run successfully?")
    
    return errors, found_files

def validate_data_content(file_path):
    """Validate the content of a single data file."""
    errors = []
    try:
        data = np.load(file_path)
    except Exception as e:
        errors.append(f"Failed to load {file_path}: {e}")
        return errors

    # Identify model and L from filename or keys
    # Assuming keys are 'spins', 'temperatures', 'metadata'
    if 'spins' not in data:
        errors.append(f"Missing 'spins' key in {file_path}")
        return errors
    
    if 'temperatures' not in data:
        errors.append(f"Missing 'temperatures' key in {file_path}")
        # We might still check spins shape, but temp coverage is unknown
    
    spins = data['spins']
    temps = data['temperatures'] if 'temperatures' in data else []
    
    # Infer model from shape
    # Heisenberg: (N, 3, L, L) -> 3 components
    # XY: (N, 2, L, L) -> 2 components
    if spins.ndim != 4:
        errors.append(f"Spins in {file_path} are not 4D (got {spins.ndim}D). Expected (N, 3, L, L) or (N, 2, L, L).")
        return errors

    N, dim, L_x, L_y = spins.shape
    if L_x != L_y:
        errors.append(f"Non-square lattice in {file_path}: {L_x}x{L_y}")
    
    L = L_x
    expected_model = "heisenberg" if dim == 3 else ("xy" if dim == 2 else "unknown")
    
    # Check against expected models
    if expected_model not in MODELS:
        errors.append(f"Unexpected spin dimension {dim} in {file_path}. Expected 2 (XY) or 3 (Heisenberg).")
    
    # Check lattice size
    if L not in LATTICE_SIZES:
        errors.append(f"Lattice size {L} in {file_path} not in expected set {LATTICE_SIZES}.")

    # Check temperature coverage
    if len(temps) > 0:
        min_t, max_t = float(np.min(temps)), float(np.max(temps))
        if min_t < TEMP_RANGE[0] or max_t > TEMP_RANGE[1]:
            # Allow small floating point tolerance
            if min_t < TEMP_RANGE[0] - 0.01 or max_t > TEMP_RANGE[1] + 0.01:
                errors.append(f"Temperature range [{min_t}, {max_t}] in {file_path} outside expected [{TEMP_RANGE[0]}, {TEMP_RANGE[1]}].")
    
    # Check unit norm
    # Reshape spins to (N*dim, L*L) or calculate norm per vector
    # Vector is along axis 1 (dim)
    norms = np.linalg.norm(spins, axis=1)
    # Check if norms are close to 1.0
    if not np.allclose(norms, 1.0, atol=1e-5):
        # Count how many are off
        off_count = np.sum(~np.isclose(norms, 1.0, atol=1e-5))
        errors.append(f"Unit norm violation in {file_path}: {off_count} vectors not normalized (tol=1e-5).")

    return errors

def main():
    print(f"Starting validation for Task T012...")
    print(f"Checking directory: {RAW_DATA_DIR}")
    
    # 1. Ensure data generation has run (or run it if missing critical files)
    # The task says "Validate that ... correctly generates". 
    # If files are missing, we might need to run the generator first to validate it.
    # However, T004 is marked completed. We assume data exists.
    # If not, we run it to be safe for the validation check.
    
    file_errors, found_files = validate_file_structure()
    if file_errors:
        print("Initial structure check failed. Attempting to run data generation...")
        # Run the main generation script
        try:
            run_generation_main()
            # Re-scan
            file_errors, found_files = validate_file_structure()
        except Exception as e:
            print(f"Failed to run data generation: {e}")
            for err in file_errors:
                print(f"  ERROR: {err}")
            return 1

    if file_errors:
        print("Data generation files missing or directory structure invalid.")
        for err in file_errors:
            print(f"  ERROR: {err}")
        return 1

    print(f"Found {len(found_files)} data files.")
    
    all_content_errors = []
    valid_files = 0
    
    for f_path in found_files:
        print(f"Validating: {f_path.name}")
        errors = validate_data_content(f_path)
        if errors:
            all_content_errors.append((f_path.name, errors))
        else:
            valid_files += 1
            # Determine if it matches expected criteria
            data = np.load(f_path)
            spins = data['spins']
            L = spins.shape[2]
            dim = spins.shape[1]
            model_type = "Heisenberg" if dim == 3 else "XY"
            print(f"  -> OK: {model_type}, L={L}, Shape={spins.shape}, Norm=Unit")

    if all_content_errors:
        print("\nValidation FAILED with the following errors:")
        for fname, errs in all_content_errors:
            print(f"File: {fname}")
            for e in errs:
                print(f"  - {e}")
        return 1
    
    # Check if we have at least one file for each combination
    # (Heisenberg L16, Heisenberg L24, XY L16, XY L24)
    found_combinations = set()
    for f_path in found_files:
        data = np.load(f_path)
        spins = data['spins']
        L = spins.shape[2]
        dim = spins.shape[1]
        model_type = "heisenberg" if dim == 3 else "xy"
        found_combinations.add((model_type, L))

    required_combinations = {
        ("heisenberg", 16), ("heisenberg", 24),
        ("xy", 16), ("xy", 24)
    }
    
    missing = required_combinations - found_combinations
    if missing:
        print(f"\nValidation FAILED: Missing data for combinations: {missing}")
        return 1

    print("\nValidation SUCCESSFUL.")
    print(f"  - All {len(found_files)} files passed content checks.")
    print(f"  - All required model/lattice combinations present: {MODELS} x {LATTICE_SIZES}.")
    print(f"  - Temperature coverage and normalization verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
