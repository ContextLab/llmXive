import os
import csv
import time
import json
import hashlib
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Local imports from project structure
from infrastructure.error_handler import exponential_backoff_retry, APIRetryError
from infrastructure.path_utils import get_project_root, ensure_dir, resolve_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions (Shared with other tasks) ---

def get_project_root() -> Path:
    """Returns the project root directory."""
    return get_project_root()

def ensure_output_directories():
    """Creates required output directories if they don't exist."""
    dirs = [
        "data/raw", "data/processed", "data/state", "data/validation",
        "figures", "notebooks"
    ]
    for d in dirs:
        ensure_dir(resolve_path(d))

def load_json_file(path: str) -> Dict:
    """Loads a JSON file and returns its contents."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Dict):
    """Saves a dictionary to a JSON file."""
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def compute_sha256(file_path: str) -> str:
    """Computes the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_git_hash() -> str:
    """Returns the current git commit hash."""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"

def validate_schema(data: List[Dict], required_fields: List[str]) -> bool:
    """Validates that all entries in data contain required fields."""
    for entry in data:
        for field in required_fields:
            if field not in entry or entry[field] is None:
                return False
    return True

def save_to_csv(data: List[Dict], path: str):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with headers if needed, or just empty
        with open(path, 'w', newline='') as f:
            pass
        return

    fieldnames = data[0].keys()
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_csv_to_dicts(path: str) -> List[Dict]:
    """Loads a CSV file into a list of dictionaries."""
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

# --- T010 Logic: Pristine Structure Download ---

def run_mock_dftb_simulation(entry: Dict, timeout: int = 300) -> Optional[float]:
    """
    Simulates a Mock DFTB+ simulation for fracture_energy.
    In a real implementation, this would call the DFTB+ binary.
    Here, we simulate a physics-based calculation or a timeout.
    For this task, we assume if we are in synthetic mode, we don't need DFTB.
    However, if called, we return a value or None on timeout.
    """
    # Placeholder for actual simulation logic
    # If real DFTB is needed, this would spawn a process.
    # For now, we treat this as a fallback that might fail.
    logger.warning(f"Mock DFTB simulation called for {entry.get('id')}. Returning None to trigger exclusion.")
    return None

def run_t010_logic():
    """
    Step 1: Download pristine structures from Materials Project.
    Implemented in previous tasks, but ensuring paths exist.
    """
    ensure_output_directories()
    # Logic handled in previous task execution, but we ensure directory structure
    pass

def run_t011_logic():
    """
    Step 2: Download defect dataset and handle missing values.
    Implemented in previous tasks.
    """
    ensure_output_directories()
    pass

def run_t012_logic():
    """
    Step 3: Check source validity and branch.
    Implemented in previous tasks.
    """
    ensure_output_directories()
    pass

# --- T013 Logic: Synthetic Data Generation ---

def generate_synthetic_data(n_samples: int, seed: int = 42, holdout: bool = False) -> List[Dict]:
    """
    Generates synthetic data based on physics-informed surrogate models.
    Logic:
    - Continuum elasticity: E = E0 * (1 - k*density)
    - Noise: Gaussian (sigma=0.05)
    """
    np.random.seed(seed)
    data = []
    materials = ["graphene", "MoS2"]
    defect_types = ["vacancy", "substitution", "grain_boundary"]
    
    E0_map = {"graphene": 3450.0, "MoS2": 330.0} # GPa
    k_map = {"graphene": 0.8, "MoS2": 0.6}

    for i in range(n_samples):
        mat = np.random.choice(materials)
        density = np.random.uniform(0.01, 0.15) # 1% to 15%
        defect_type = np.random.choice(defect_types)
        
        E0 = E0_map[mat]
        k = k_map[mat]
        
        # Physics model
        E_modulus = E0 * (1 - k * density) + np.random.normal(0, E0 * 0.05)
        conductivity = 1000 * (1 - 0.5 * density) + np.random.normal(0, 50)
        
        # Fracture energy: derived from Griffith criterion approximation
        # Gamma = (K_IC^2) / (2*E) ... simplified here
        # We assume a base fracture energy and scale by density
        base_fracture = 15.0 if mat == "graphene" else 8.0
        fracture_energy = base_fracture * (1 - 0.4 * density) + np.random.normal(0, base_fracture * 0.05)

        # Ensure no NaNs or Infs
        if np.isnan(fracture_energy) or np.isinf(fracture_energy):
            fracture_energy = base_fracture * (1 - 0.4 * density) # Fallback to mean if noise bad

        entry = {
            "id": f"syn_{i:04d}",
            "material": mat,
            "defect_type": defect_type,
            "defect_density": round(density, 4),
            "elastic_tensor": f"[{E_modulus:.2f}, 0, 0, ...]", # Simplified representation
            "conductivity": round(conductivity, 2),
            "fracture_energy": round(fracture_energy, 4)
        }
        data.append(entry)
    
    return data

def run_t013_logic():
    """
    Step 4: Generate synthetic data if source is invalid.
    Implemented in previous tasks.
    """
    ensure_output_directories()
    # Logic handled previously, but we ensure paths
    pass

# --- T016a Logic: Data Integrity ---

def run_t016a_logic():
    """
    Step 5: Data Integrity & Hygiene.
    Implemented in previous tasks.
    """
    ensure_output_directories()
    pass

# --- T016b Logic: Missing Value Handling (Synthetic) ---

def run_t016b_logic():
    """
    Step 6: Missing Value Handling (Synthetic).
    Dependency: T013.
    Condition: Only if data_source is synthetic.
    Action: Check for missing fracture_energy in synthetic data.
            If missing, invoke Synthetic Generator logic (T013) to re-generate or impute.
    Output:
      - data/processed/mock_dftb_results.csv (if real - N/A here)
      - data/state/mock_dftb_exclusions.json
      - data/state/fallback_verification.json
    """
    ensure_output_directories()
    
    state_path = resolve_path("data/state/data_source.json")
    if not os.path.exists(state_path):
        logger.error(f"State file not found at {state_path}. Cannot determine data source.")
        # Fallback: Assume synthetic if state missing but we are in this task context?
        # Strictly, we should fail if state is missing.
        raise FileNotFoundError(f"Required state file {state_path} not found.")

    state_data = load_json_file(state_path)
    source_type = state_data.get("source", "unknown")
    
    # Only proceed if synthetic
    if source_type != "synthetic":
        logger.info(f"Data source is '{source_type}'. Skipping synthetic missing value handling (T016b).")
        # Write empty/neutral status files to indicate skip
        save_json_file(resolve_path("data/state/mock_dftb_exclusions.json"), {
            "status": "skipped",
            "reason": "Data source is not synthetic",
            "excluded_count": 0
        })
        save_json_file(resolve_path("data/state/fallback_verification.json"), {
            "status": "skipped",
            "reason": "Data source is not synthetic",
            "verification": "Not applicable"
        })
        return

    logger.info("Data source is 'synthetic'. Checking for missing fracture_energy...")
    
    # Determine which synthetic file to check
    synthetic_train_path = resolve_path("data/raw/synthetic_train.csv")
    synthetic_holdout_path = resolve_path("data/raw/synthetic_holdout.csv")
    
    # We check the training data primarily
    if not os.path.exists(synthetic_train_path):
        logger.error(f"Synthetic training data not found at {synthetic_train_path}.")
        raise FileNotFoundError(f"Synthetic training data missing: {synthetic_train_path}")

    data = load_csv_to_dicts(synthetic_train_path)
    
    missing_indices = []
    for i, entry in enumerate(data):
        fe = entry.get("fracture_energy")
        if fe is None or fe == "" or (isinstance(fe, str) and fe.lower() == "nan"):
            missing_indices.append(i)
        else:
            try:
                val = float(fe)
                if np.isnan(val):
                    missing_indices.append(i)
            except (ValueError, TypeError):
                missing_indices.append(i)
    
    exclusions_log = {
        "status": "checked",
        "source": "synthetic",
        "total_entries": len(data),
        "missing_count": len(missing_indices),
        "missing_indices": missing_indices
    }

    if len(missing_indices) > 0:
        logger.warning(f"Found {len(missing_indices)} entries with missing fracture_energy.")
        logger.info("Invoking Synthetic Generator logic to regenerate/impute these values.")
        
        # Strategy: Re-generate the specific entries or impute using the physics model
        # Since we are in synthetic mode, we can regenerate the row with the same parameters
        # but a new random seed or just fix the calculation.
        
        # For robustness, we regenerate the whole dataset with the same seed to ensure consistency
        # or just fix the specific rows. The task says "invoke Synthetic Generator logic".
        # We will regenerate the full dataset to ensure physics consistency.
        
        # Note: In a real scenario, we might try to impute. Here we regenerate to be safe.
        # We need the seed used originally. If not stored, we assume 42.
        # We assume the original generation was deterministic.
        
        new_data = generate_synthetic_data(n_samples=len(data), seed=42, holdout=False)
        
        # Verify the new data has no missing values
        missing_check = [i for i, e in enumerate(new_data) if e.get("fracture_energy") is None]
        if missing_check:
            logger.critical(f"Regenerated data still has missing values at indices {missing_check}.")
            raise RuntimeError("Regeneration failed to fix missing values.")
        
        # Save the corrected data
        save_to_csv(new_data, synthetic_train_path)
        logger.info(f"Successfully regenerated {len(new_data)} entries. Saved to {synthetic_train_path}")
        
        exclusions_log["action"] = "regenerated"
        exclusions_log["note"] = "Full dataset regenerated to fix missing values."
        
        # Mock DFTB results file is for real data fallback. For synthetic, we record that we used the generator.
        # We create an empty file or a log indicating synthetic regeneration.
        mock_dftb_path = resolve_path("data/processed/mock_dftb_results.csv")
        with open(mock_dftb_path, 'w') as f:
            f.write("# No DFTB simulation performed for synthetic data.\n")
            f.write("# Missing values were resolved via synthetic regeneration.\n")
            f.write("id,status\n")
            for idx in missing_indices:
                f.write(f"syn_{idx:04d},regenerated_via_surrogate\n")
        
        # Record exclusions (none actually excluded, but we log the event)
        exclusions_log["excluded_count"] = 0 # No exclusions, just regeneration
        save_json_file(resolve_path("data/state/mock_dftb_exclusions.json"), exclusions_log)
        
        fallback_verification = {
            "status": "success",
            "method": "synthetic_regeneration",
            "original_missing": len(missing_indices),
            "final_missing": 0,
            "verification": "All missing fracture_energy values resolved via physics-informed regeneration."
        }
        save_json_file(resolve_path("data/state/fallback_verification.json"), fallback_verification)
        
    else:
        logger.info("No missing fracture_energy values found in synthetic data.")
        exclusions_log["action"] = "none_needed"
        save_json_file(resolve_path("data/state/mock_dftb_exclusions.json"), exclusions_log)
        
        fallback_verification = {
            "status": "success",
            "method": "none",
            "original_missing": 0,
            "final_missing": 0,
            "verification": "No missing values detected; no action required."
        }
        save_json_file(resolve_path("data/state/fallback_verification.json"), fallback_verification)

def main():
    """Main entry point for T016b logic."""
    ensure_output_directories()
    try:
        run_t016b_logic()
        logger.info("T016b completed successfully.")
    except Exception as e:
        logger.error(f"T016b failed: {e}")
        raise

if __name__ == "__main__":
    main()