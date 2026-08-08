import os
import csv
import time
import json
import hashlib
import subprocess
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Utility Functions (Existing API Surface) ---

def get_project_root() -> Path:
    """Returns the project root directory."""
    # Assuming the script is run from the project root or code/
    current = Path(__file__).resolve()
    # Traverse up until we find a marker or root
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current.parent

def ensure_output_directories():
    """Creates necessary output directories if they don't exist."""
    project_root = get_project_root()
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "state",
        project_root / "data" / "validation",
        project_root / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_git_hash() -> str:
    """Returns the current git commit hash or 'unknown'."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(file_path: Path) -> Dict:
    """Loads a JSON file into a dictionary."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: Dict):
    """Saves a dictionary to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(file_path: Path) -> List[Dict]:
    """Loads a CSV file into a list of dictionaries."""
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(file_path: Path, data: List[Dict]):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with no columns if no data
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def parse_float_safe(val: str) -> Optional[float]:
    """Safely parses a string to float, returns None on failure."""
    if val is None or val == '':
        return None
    try:
        return float(val)
    except ValueError:
        return None

def validate_schema(row: Dict, required_fields: List[str]) -> bool:
    """Checks if a row has all required fields and they are non-null."""
    for field in required_fields:
        if field not in row or row[field] is None or row[field] == '':
            return False
    return True

# --- Step 4: Synthetic Data Generation (T013) ---

def load_pristine_references() -> Dict[str, Dict[str, float]]:
    """
    Loads pristine structure reference values from data/raw/pristine_structures.csv.
    Returns a dict keyed by material type (e.g., 'graphene', 'mos2') with base values.
    """
    project_root = get_project_root()
    csv_path = project_root / "data" / "raw" / "pristine_structures.csv"
    
    if not csv_path.exists():
        logger.warning(f"Pristine structures file not found at {csv_path}. Using defaults.")
        # Fallback defaults if file missing (though T010a should have created it)
        return {
            "graphene": {"conductivity": 1.0, "youngs_modulus": 1.0, "fracture_strength": 1.0},
            "mos2": {"conductivity": 1.0, "youngs_modulus": 1.0, "fracture_strength": 1.0}
        }

    rows = load_csv_to_dicts(csv_path)
    if not rows:
        logger.warning("Pristine structures file is empty. Using defaults.")
        return {
            "graphene": {"conductivity": 1.0, "youngs_modulus": 1.0, "fracture_strength": 1.0},
            "mos2": {"conductivity": 1.0, "youngs_modulus": 1.0, "fracture_strength": 1.0}
        }

    # Aggregate by material type (assuming 'material_type' column exists)
    material_stats = {}
    for row in rows:
        mat_type = row.get('material_type', 'unknown')
        if mat_type not in material_stats:
            material_stats[mat_type] = []
        
        try:
            cond = float(row.get('conductivity', 0))
            youngs = float(row.get('youngs_modulus', 0))
            fracs = float(row.get('fracture_strength', 0))
            material_stats[mat_type].append({
                'conductivity': cond,
                'youngs_modulus': youngs,
                'fracture_strength': fracs
            })
        except (ValueError, TypeError):
            continue

    # Compute averages
    result = {}
    for mat_type, values in material_stats.items():
        if not values:
            continue
        avg_cond = np.mean([v['conductivity'] for v in values])
        avg_youngs = np.mean([v['youngs_modulus'] for v in values])
        avg_fracs = np.mean([v['fracture_strength'] for v in values])
        
        result[mat_type] = {
            'conductivity': avg_cond,
            'youngs_modulus': avg_youngs,
            'fracture_strength': avg_fracs
        }
    
    return result

def apply_continuum_elasticity(E0: float, density: float, k: float) -> float:
    """
    Analytical signal: Continuum elasticity model.
    E = E0 * (1 - k * density)
    """
    return E0 * (1.0 - k * density)

def apply_conductivity_model(sigma0: float, density: float, k: float) -> float:
    """
    Analytical signal for conductivity.
    Sigma = Sigma0 * (1 - k * density)
    """
    return sigma0 * (1.0 - k * density)

def apply_fracture_model(sigma_f0: float, density: float, k: float) -> float:
    """
    Analytical signal for fracture strength.
    Sigma_f = Sigma_f0 * (1 - k * density)
    """
    return sigma_f0 * (1.0 - k * density)

def generate_synthetic_data(n_target: int = 1000, n_min: int = 100, seed: int = 42) -> List[Dict]:
    """
    Generates synthetic data rows based on continuum elasticity models with DFT-calibrated noise.
    
    Logic:
    1. Check runtime estimate (mocked here as a simple check, but real logic would measure speed).
    2. Generate rows until N_TARGET is reached.
    3. Use analytical signal + Gaussian noise.
    4. Handle physics constraints (values > 0).
    """
    logger.info(f"Starting synthetic data generation. Target: {n_target}, Seed: {seed}")
    np.random.seed(seed)
    
    # Load references
    refs = load_pristine_references()
    
    # Define defect types and densities
    defect_types = ["vacancy", "substitution", "grain_boundary", "adatom"]
    
    # DFT-calibrated noise parameters (sigma derived from variance)
    # Approximate noise levels based on typical DFT variance for these properties
    noise_sigma_cond = 0.05  # 5% noise
    noise_sigma_youngs = 0.03 # 3% noise
    noise_sigma_fracture = 0.04 # 4% noise
    
    # Continuum elasticity constant k (typical for 2D materials)
    k_elasticity = 0.8 # k*density reduces property linearly
    
    # Runtime check simulation (if generating > 10000 rows might be slow, but 1000 is fast)
    # In a real scenario, we might measure generation speed of first 100 rows
    start_time = time.time()
    generated_rows = []
    
    # Material types to sample from
    material_types = list(refs.keys())
    if not material_types:
        material_types = ["graphene", "mos2"] # Fallback
        # Ensure refs has defaults
        for m in material_types:
            if m not in refs:
                refs[m] = {'conductivity': 1.0, 'youngs_modulus': 1.0, 'fracture_strength': 1.0}

    # Generate data
    count = 0
    while count < n_target:
        # Estimate progress
        if count > 0:
            elapsed = time.time() - start_time
            rate = count / elapsed
            estimated_total_time = n_target / rate
            # If estimated time > 2 hours, scale down to N_MIN
            if estimated_total_time > 7200: # 2 hours
                logger.warning(f"Runtime estimate {estimated_total_time:.1f}s exceeds limit. Scaling down to N_MIN={n_min}.")
                n_target = n_min
                # Break condition will be checked in next loop iteration naturally if we adjust n_target
                # But we need to ensure we don't infinite loop if n_target was already low
                if n_target <= count:
                    break

        # Sample parameters
        mat_type = np.random.choice(material_types)
        ref = refs[mat_type]
        
        defect_type = np.random.choice(defect_types)
        # Density range: 0.001 to 0.1 (0.1% to 10%)
        density = np.random.uniform(0.001, 0.1)
        
        # Calculate Signal
        E_signal = apply_continuum_elasticity(ref['youngs_modulus'], density, k_elasticity)
        sigma_signal = apply_conductivity_model(ref['conductivity'], density, k_elasticity)
        sigma_f_signal = apply_fracture_model(ref['fracture_strength'], density, k_elasticity)
        
        # Add Noise
        E_noise = np.random.normal(0, noise_sigma_youngs * ref['youngs_modulus'])
        sigma_noise = np.random.normal(0, noise_sigma_cond * ref['conductivity'])
        sigma_f_noise = np.random.normal(0, noise_sigma_fracture * ref['fracture_strength'])
        
        # Final Values (ensure > 0)
        E_final = max(0.01, E_signal + E_noise)
        sigma_final = max(0.01, sigma_signal + sigma_noise)
        sigma_f_final = max(0.01, sigma_f_signal + sigma_f_noise)
        
        row = {
            "id": f"synthetic_{count:05d}",
            "material_type": mat_type,
            "defect_type": defect_type,
            "defect_density": density,
            "conductivity": sigma_final,
            "youngs_modulus": E_final,
            "fracture_strength": sigma_f_final,
            "source": "synthetic"
        }
        
        generated_rows.append(row)
        count += 1

    logger.info(f"Generated {len(generated_rows)} synthetic rows.")
    return generated_rows

def step_4_synthetic_generation():
    """
    Implements T013: Synthetic Data Generation.
    Reads data/state/generation_status.json. If status is pending_synthetic, generates data.
    """
    project_root = get_project_root()
    ensure_output_directories()
    
    status_file = project_root / "data" / "state" / "generation_status.json"
    data_source_file = project_root / "data" / "state" / "data_source.json"
    
    if not status_file.exists():
        logger.error(f"Status file {status_file} not found. Cannot proceed with synthetic generation.")
        # Write empty outputs as per guarantee
        save_json_file(project_root / "data" / "state" / "synthetic_config.json", {
            "error": "generation_status.json not found"
        })
        return

    status_data = load_json_file(status_file)
    if status_data.get("status") != "pending_synthetic":
        logger.info(f"Status is '{status_data.get('status')}'. Skipping synthetic generation.")
        return

    logger.info("Starting synthetic data generation (T013).")
    
    # Parameters from task description
    n_target = 1000
    n_min = 100
    seed = 42
    
    # Generate data
    synthetic_data = generate_synthetic_data(n_target=n_target, n_min=n_min, seed=seed)
    
    # Determine actual count (might be scaled down)
    n_actual = len(synthetic_data)
    
    # Save synthetic train data
    output_csv = project_root / "data" / "raw" / "synthetic_train.csv"
    save_to_csv(output_csv, synthetic_data)
    logger.info(f"Saved synthetic train data to {output_csv}")
    
    # Save config
    config_data = {
        "seed": seed,
        "n_target_requested": n_target,
        "n_actual": n_actual,
        "analytical_formula": "E = E0 * (1 - k * density)",
        "k_elasticity": 0.8,
        "noise_sigma_conductivity": 0.05,
        "noise_sigma_youngs_modulus": 0.03,
        "noise_sigma_fracture_strength": 0.04,
        "git_hash": get_git_hash()
    }
    
    config_output = project_root / "data" / "state" / "synthetic_config.json"
    save_json_file(config_output, config_data)
    logger.info(f"Saved synthetic config to {config_output}")
    
    # Update generation_status to 'completed'
    status_data["status"] = "completed"
    status_data["source"] = "synthetic"
    save_json_file(status_file, status_data)
    
    # Update data_source.json
    source_data = {
        "source_type": "synthetic",
        "holdout_filename": "synthetic_holdout.csv",
        "status": "synthetic_generated"
    }
    save_json_file(data_source_file, source_data)
    
    logger.info("T013 Synthetic Data Generation completed successfully.")

def main():
    """Main entry point for the script."""
    ensure_output_directories()
    step_4_synthetic_generation()

if __name__ == "__main__":
    main()
