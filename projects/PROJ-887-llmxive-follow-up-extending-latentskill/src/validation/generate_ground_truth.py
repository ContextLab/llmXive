"""
T022c: Generate synthetic composite adapters (ground truth) from real base LoRA adapters.

This script loads real base LoRA adapters from data/raw/, pairs the first two
adapters alphabetically by task ID, and generates a synthetic composite adapter
by linear interpolation. It outputs the composite weights and a pairs.yaml file
with metadata required for downstream correlation checks (T030).

Constraints:
- MUST use REAL base adapters from data/raw/ (produced by T012).
- MUST fail loudly if real adapters are not found.
- Selection rule: Pair first two adapters alphabetically by task ID.
- Output: data/processed/composite_ground_truth.npz and data/processed/pairs.yaml.
- Validate: Interpolated weights must be non-NaN and non-zero.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_NPZ_PATH = DATA_PROCESSED_DIR / "composite_ground_truth.npz"
OUTPUT_PAIRS_YAML_PATH = DATA_PROCESSED_DIR / "pairs.yaml"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_real_adapter_weights(raw_dir: Path) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Load real base LoRA adapters from data/raw/.
    
    Expects files named: <task_id>_weights.npz (from T012).
    Returns a dict mapping task_id -> { 'A': array, 'B': array, 'desc': str }.
    
    Raises FileNotFoundError if no real adapters are found.
    """
    adapters = {}
    npz_files = list(raw_dir.glob("*_weights.npz"))
    
    if not npz_files:
        raise FileNotFoundError(
            f"No real base adapters found in {raw_dir}. "
            f"Expected files matching '*_weights.npz'. "
            f"Ensure T012 (download_weights.py) has been executed successfully."
        )
    
    logger.info(f"Found {len(npz_files)} adapter files in {raw_dir}")
    
    for file_path in npz_files:
        # Extract task_id from filename (e.g., "alfworld_weights.npz" -> "alfworld")
        task_id = file_path.stem.replace("_weights", "")
        
        try:
            data = np.load(file_path)
            # T012 saves as 'A' and 'B' matrices
            if 'A' not in data or 'B' not in data:
                logger.warning(f"Skipping {file_path}: Missing 'A' or 'B' keys.")
                continue
            
            A = data['A']
            B = data['B']
            
            # Validate dimensions (optional, but good practice)
            if A.ndim != 2 or B.ndim != 2:
                logger.warning(f"Skipping {file_path}: Matrices must be 2D.")
                continue
            
            # Generate a deterministic description for the task
            # In a real scenario, this might come from a metadata file, 
            # but for this task, we derive it from the task_id to satisfy FR-007.
            desc = f"Task: {task_id.replace('_', ' ').title()}"
            
            adapters[task_id] = {
                'A': A,
                'B': B,
                'desc': desc,
                'file_path': str(file_path)
            }
            logger.info(f"Loaded adapter: {task_id} (A: {A.shape}, B: {B.shape})")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            continue
    
    if not adapters:
        raise FileNotFoundError(
            f"No valid real adapters loaded from {raw_dir}. "
            f"Check the contents of the directory and the output of T012."
        )
    
    return adapters

def interpolate_adapters(
    adapter_a: Dict[str, np.ndarray], 
    adapter_b: Dict[str, np.ndarray], 
    alpha: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic composite adapter by linearly interpolating two base adapters.
    
    Formula: Composite_A = (1-alpha)*A_a + alpha*A_b
             Composite_B = (1-alpha)*B_a + alpha*B_b
    
    Args:
        adapter_a: Dict with 'A', 'B' keys.
        adapter_b: Dict with 'A', 'B' keys.
        alpha: Interpolation weight (0.0 to 1.0). Default 0.5 (midpoint).
    
    Returns:
        Tuple (Composite_A, Composite_B)
    """
    A_a = adapter_a['A']
    B_a = adapter_a['B']
    A_b = adapter_b['A']
    B_b = adapter_b['B']
    
    # Validate shapes match
    if A_a.shape != A_b.shape or B_a.shape != B_b.shape:
        raise ValueError(
            f"Shape mismatch for interpolation. "
            f"A: {A_a.shape} vs {A_b.shape}, B: {B_a.shape} vs {B_b.shape}"
        )
    
    comp_A = (1 - alpha) * A_a + alpha * A_b
    comp_B = (1 - alpha) * B_a + alpha * B_b
    
    return comp_A, comp_B

def validate_weights(A: np.ndarray, B: np.ndarray) -> bool:
    """
    Validate that interpolated weights are non-NaN and non-zero.
    """
    if np.any(np.isnan(A)) or np.any(np.isnan(B)):
        logger.error("Interpolated weights contain NaN values.")
        return False
    
    if np.allclose(A, 0) or np.allclose(B, 0):
        logger.error("Interpolated weights are effectively zero.")
        return False
    
    return True

def generate_composite_task_desc(task_a_desc: str, task_b_desc: str) -> str:
    """
    Generate a composite task description for FR-007 correlation checks.
    """
    # Simple semantic combination for the description
    return f"Composite of: {task_a_desc} AND {task_b_desc}"

def main():
    """
    Main entry point for T022c.
    """
    logger.info("Starting T022c: Generate Ground Truth Composite Adapters")
    
    # 1. Load real adapters
    try:
        adapters = load_real_adapter_weights(DATA_RAW_DIR)
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # 2. Select first two adapters alphabetically by task ID
    sorted_ids = sorted(adapters.keys())
    if len(sorted_ids) < 2:
        logger.error("Need at least 2 adapters to generate a composite. Found: %s", sorted_ids)
        sys.exit(1)
    
    id_a = sorted_ids[0]
    id_b = sorted_ids[1]
    
    logger.info(f"Selected pair for interpolation: {id_a} and {id_b}")
    
    adapter_a = adapters[id_a]
    adapter_b = adapters[id_b]
    
    # 3. Interpolate (alpha=0.5 for midpoint)
    logger.info(f"Interpolating with alpha=0.5...")
    comp_A, comp_B = interpolate_adapters(adapter_a, adapter_b, alpha=0.5)
    
    # 4. Validate
    if not validate_weights(comp_A, comp_B):
        logger.critical("Validation failed: Interpolated weights are invalid.")
        sys.exit(1)
    
    logger.info("Validation passed: Weights are non-NaN and non-zero.")
    
    # 5. Generate metadata for pairs.yaml
    task_a_desc = adapter_a['desc']
    task_b_desc = adapter_b['desc']
    composite_task_desc = generate_composite_task_desc(task_a_desc, task_b_desc)
    composite_task_id = f"composite_{id_a}_plus_{id_b}"
    
    # Expected correlation is a placeholder as we don't have ground truth text-space distances yet.
    # This field is required by the schema but will be used in T030 to compare against actual measurements.
    expected_correlation = 1.0 # Placeholder; T030 will compute the actual value.
    
    pairs_entry = {
        "task_a_id": id_a,
        "task_b_id": id_b,
        "composite_task_id": composite_task_id,
        "task_a_desc": task_a_desc,
        "task_b_desc": task_b_desc,
        "composite_task_desc": composite_task_desc,
        "expected_correlation": expected_correlation
    }
    
    # 6. Save outputs
    # Save NPZ
    logger.info(f"Saving composite weights to {OUTPUT_NPZ_PATH}")
    np.savez(
        OUTPUT_NPZ_PATH,
        A=comp_A,
        B=comp_B,
        task_a_id=id_a,
        task_b_id=id_b,
        composite_task_id=composite_task_id
    )
    
    # Save YAML
    logger.info(f"Saving pairs metadata to {OUTPUT_PAIRS_YAML_PATH}")
    # Ensure the file is a list of dicts as per schema requirement
    pairs_data = [pairs_entry]
    with open(OUTPUT_PAIRS_YAML_PATH, 'w') as f:
        yaml.dump(pairs_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info("T022c completed successfully.")
    logger.info(f"Output files: {OUTPUT_NPZ_PATH}, {OUTPUT_PAIRS_YAML_PATH}")

if __name__ == "__main__":
    main()
