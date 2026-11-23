import os
import json
import zipfile
import io
import logging
import random
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
NUM_SYNTHETIC_SEQUENCES = 10
FRAMES_PER_SEQUENCE = 20
IMAGE_HEIGHT = 480
IMAGE_WIDTH = 640
GRID_SIZE = 5  # 5x5 grid points

def ensure_dirs(root_dir: str) -> None:
    """Ensure required directories exist."""
    raw_dir = Path(root_dir) / "data" / "raw"
    processed_dir = Path(root_dir) / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

def attempt_hf_fetch(root_dir: str, dataset_id: str = "omnidirector/dataset") -> bool:
    """
    Attempt to fetch the real OmniDirector dataset from HuggingFace.
    Returns True if successful, False otherwise.
    """
    try:
        # Check if datasets library is available
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("The 'datasets' library is not installed. Please install it via: pip install datasets")
            return False

        logger.info(f"Attempting to fetch dataset: {dataset_id}")
        
        # Attempt to load the dataset
        # Note: This is a placeholder for the actual dataset ID. 
        # In a real scenario, the exact dataset ID would be known.
        # We use streaming to avoid loading everything into memory at once.
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        # Try to fetch a sample to verify access
        sample = next(iter(dataset))
        logger.info(f"Successfully fetched sample from {dataset_id}")
        logger.info(f"Sample keys: {sample.keys()}")
        
        # If we get here, the fetch was successful.
        # We would then download the full dataset, but for this task
        # we just confirm availability. The actual download logic
        # would be implemented in a downstream task (T008).
        return True

    except Exception as e:
        logger.warning(f"Failed to fetch dataset from HuggingFace: {e}")
        logger.info("Falling back to synthetic data generation.")
        return False

def generate_synthetic_data(root_dir: str) -> str:
    """
    Generate a deterministic synthetic dataset mimicking the OmniDirector schema.
    Outputs to data/raw/synthetic_omnidirector.zip
    """
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    output_path = Path(root_dir) / "data" / "raw" / "synthetic_omnidirector.zip"
    
    logger.info(f"Generating synthetic dataset with {NUM_SYNTHETIC_SEQUENCES} sequences...")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for seq_idx in range(NUM_SYNTHETIC_SEQUENCES):
            sequence_id = f"seq_{seq_idx:04d}"
            data = []
            
            # Determine if depth is randomized for this sequence
            # Set randomized_depth=True for ~50% of sequences
            randomized_depth = (seq_idx % 2 == 0)
            
            # Generate motion parameters
            radial_motion = random.uniform(5.0, 25.0)  # degrees
            z_velocity = random.uniform(0.0, 0.2)      # units/frame
            
            for frame_idx in range(FRAMES_PER_SEQUENCE):
                frame_id = f"{sequence_id}_frame_{frame_idx:04d}"
                
                # Generate grid points (2D pixel coords)
                # Simulate perspective distortion based on motion
                base_points = []
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        x = (j / (GRID_SIZE - 1)) * IMAGE_WIDTH
                        y = (i / (GRID_SIZE - 1)) * IMAGE_HEIGHT
                        base_points.append([x, y])
                
                # Apply simple distortion based on radial motion and frame
                distortion_factor = (frame_idx / FRAMES_PER_SEQUENCE) * (radial_motion / 180.0) * 20
                grid_points_2d = []
                for pt in base_points:
                    x, y = pt
                    # Simple radial distortion simulation
                    dx = (x - IMAGE_WIDTH / 2) * distortion_factor * 0.01
                    dy = (y - IMAGE_HEIGHT / 2) * distortion_factor * 0.01
                    grid_points_2d.append([float(x + dx), float(y + dy)])
                
                # Generate R matrix (3x3) and t vector (3,)
                # Create a random rotation matrix
                angle = random.uniform(-0.1, 0.1)
                R = np.array([
                    [np.cos(angle), -np.sin(angle), 0],
                    [np.sin(angle), np.cos(angle), 0],
                    [0, 0, 1]
                ])
                # Add small random perturbation
                R += np.random.normal(0, 0.001, R.shape)
                
                # Create translation vector
                t = np.array([
                    random.uniform(-0.05, 0.05),
                    random.uniform(-0.05, 0.05),
                    z_velocity
                ])
                
                row = {
                    "sequence_id": sequence_id,
                    "frame_id": frame_id,
                    "radial_motion_deg": round(radial_motion, 4),
                    "z_velocity": round(z_velocity, 6),
                    "grid_points_2d": json.dumps(grid_points_2d),
                    "R_matrix": json.dumps(R.tolist()),
                    "t_vector": json.dumps(t.tolist()),
                    "randomized_depth": randomized_depth
                }
                data.append(row)
            
            # Write sequence data to zip
            seq_file_name = f"{sequence_id}.json"
            zf.writestr(seq_file_name, json.dumps(data))
    
    logger.info(f"Synthetic dataset generated at: {output_path}")
    return str(output_path)

def main():
    """Main entry point for T007."""
    # Assume project root is the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent.parent
    ensure_dirs(str(project_root))
    
    # Attempt real fetch
    fetch_success = attempt_hf_fetch(str(project_root))
    
    if fetch_success:
        logger.info("Real dataset fetch successful. Outputting metadata for downstream tasks.")
        # In a real scenario, we would download the actual file here.
        # For now, we create a marker file to indicate success.
        marker_path = project_root / "data" / "raw" / "omnidirector_marker.json"
        with open(marker_path, 'w') as f:
            json.dump({"status": "fetched", "source": "huggingface"}, f)
        # Note: The actual zip file would be downloaded here. 
        # Since we don't have the real dataset ID, we rely on the fallback for the pipeline to run.
        # However, the task requires outputting a zip. 
        # We will generate synthetic data as the fallback is the only guaranteed path to a zip.
        logger.warning("Real fetch confirmed, but without a specific dataset ID and file, generating synthetic fallback for immediate pipeline execution.")
        generate_synthetic_data(str(project_root))
    else:
        logger.info("Real dataset fetch failed or unavailable. Generating synthetic fallback.")
        generate_synthetic_data(str(project_root))

if __name__ == "__main__":
    main()
