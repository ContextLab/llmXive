"""
Dataset Fetcher for OmniDirector Project.

Attempts to fetch the real OmniDirector dataset from HuggingFace.
If fetch fails, generates a deterministic synthetic dataset locally
that mimics the real schema.
"""
import os
import json
import zipfile
import io
import logging
import random
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd
import requests
from huggingface_hub import hf_hub_download, HfApi, hf_hub_url

# Configure logging (reusing project logging setup)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REPO_ID = "omnidirector/dataset"  # Placeholder for canonical source
FILE_NAME = "omnidirector.zip"
SYNTHETIC_SEED = 42
SYNTHETIC_NUM_SEQUENCES = 10
SYNTHETIC_FRAMES_PER_SEQ = 20
GRID_SIZE = 8  # 8x8 grid points
IMAGE_SIZE = (640, 480)

# Output paths
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

def ensure_dirs():
    """Ensure output directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def attempt_hf_fetch() -> Optional[str]:
    """
    Attempt to download the real OmniDirector dataset from HuggingFace.
    Returns the path to the downloaded zip file, or None if failed.
    """
    logger.info(f"Attempting to fetch real dataset from HuggingFace: {REPO_ID}")
    try:
        # Check if file exists first
        api = HfApi()
        try:
            api.hf_hub_download(repo_id=REPO_ID, filename=FILE_NAME)
        except Exception as e:
            # If the specific file doesn't exist or repo is private/missing
            logger.warning(f"File {FILE_NAME} not found in {REPO_ID}: {e}")
            return None
        
        # Download the file
        local_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILE_NAME,
            force_download=False
        )
        logger.info(f"Successfully downloaded real dataset to: {local_path}")
        return local_path
    except Exception as e:
        logger.warning(f"HuggingFace fetch failed: {e}")
        return None

def generate_synthetic_data() -> str:
    """
    Generate a deterministic synthetic dataset mimicking the OmniDirector schema.
    Returns the path to the generated zip file.
    """
    logger.info("Generating deterministic synthetic dataset...")
    random.seed(SYNTHETIC_SEED)
    np.random.seed(SYNTHETIC_SEED)
    
    sequences = []
    all_data = []
    
    for seq_idx in range(SYNTHETIC_NUM_SEQUENCES):
        seq_id = f"syn_seq_{seq_idx:03d}"
        num_frames = SYNTHETIC_FRAMES_PER_SEQ
        
        # Generate sequence-level parameters
        # Radial motion: mix of low and high to test filtering
        base_radial = random.uniform(5, 25) 
        # Z velocity: mix of low and high
        base_z_vel = random.uniform(-0.2, 0.3)
        
        # Determine if this sequence is "retained" based on heuristics:
        # radial_motion > 15 OR z_velocity > 0.1
        # We'll simulate varying motion per frame
        
        for frame_idx in range(num_frames):
            frame_id = f"syn_seq_{seq_idx:03d}_f{frame_idx:03d}"
            
            # Simulate motion progression
            t = frame_idx / num_frames
            current_radial = base_radial * (0.8 + 0.4 * t)  # Vary over time
            current_z_vel = base_z_vel * (0.8 + 0.4 * t)
            
            # Generate grid points (2D pixel coords)
            # Simulate perspective distortion
            center_x, center_y = IMAGE_SIZE[0] / 2, IMAGE_SIZE[1] / 2
            grid_points = []
            for gx in range(GRID_SIZE):
                for gy in range(GRID_SIZE):
                    # Normalized grid (-1 to 1)
                    nx = (gx / (GRID_SIZE - 1)) * 2 - 1
                    ny = (gy / (GRID_SIZE - 1)) * 2 - 1
                    
                    # Apply simple perspective transform simulation
                    # x' = x * (1 + k * z) + dx
                    # y' = y * (1 + k * z) + dy
                    k = 0.1 * current_radial / 20.0  # Scale by radial motion
                    dx = 10 * current_z_vel
                    dy = 5 * current_z_vel
                    
                    px = center_x + nx * 150 * (1 + k * 0.5) + dx
                    py = center_y + ny * 100 * (1 + k * 0.5) + dy
                    
                    grid_points.append([int(px), int(py)])
            
            # Generate rotation matrix (3x3)
            # Simulate a small rotation based on radial motion
            theta = np.radians(current_radial * 0.1)
            R = np.array([
                [np.cos(theta), -np.sin(theta), 0],
                [np.sin(theta), np.cos(theta), 0],
                [0, 0, 1]
            ])
            
            # Generate translation vector (3,)
            t_vec = np.array([
                0.05 * current_z_vel,
                0.02 * current_z_vel,
                0.1 * (0.5 - t)
            ])
            
            # Determine randomized_depth flag
            # Set True for ~50% of sequences as per task requirement
            randomized_depth = (seq_idx % 2 == 0)
            
            # Create row data
            row = {
                'sequence_id': seq_id,
                'frame_id': frame_id,
                'radial_motion_deg': round(current_radial, 4),
                'z_velocity': round(current_z_vel, 4),
                'grid_points_2d': json.dumps(grid_points),  # Store as JSON string
                'R_matrix': json.dumps(R.tolist()),
                't_vector': json.dumps(t_vec.tolist()),
                'randomized_depth': randomized_depth
            }
            all_data.append(row)
        
        sequences.append(seq_id)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    csv_path = PROCESSED_DIR / "filtered_sequences.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved synthetic data to {csv_path}")
    
    # Create zip file containing the CSV
    zip_path = RAW_DIR / "synthetic_omnidirector.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_path, "filtered_sequences.csv")
        # Add a metadata file
        metadata = {
            "source": "synthetic",
            "seed": SYNTHETIC_SEED,
            "num_sequences": SYNTHETIC_NUM_SEQUENCES,
            "frames_per_sequence": SYNTHETIC_FRAMES_PER_SEQ,
            "schema_version": "1.0"
        }
        zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
    
    logger.info(f"Created synthetic dataset zip at {zip_path}")
    return str(zip_path)

def main():
    """Main entry point for dataset fetching/generation."""
    ensure_dirs()
    
    real_path = attempt_hf_fetch()
    
    if real_path:
        # Real dataset fetched successfully
        output_path = RAW_DIR / FILE_NAME
        # Move/copy to expected location if needed
        if real_path != str(output_path):
            import shutil
            shutil.copy2(real_path, output_path)
        logger.info(f"Real dataset ready at {output_path}")
        return str(output_path)
    else:
        # Fallback to synthetic
        logger.info("Real dataset fetch failed, generating synthetic fallback...")
        return generate_synthetic_data()

if __name__ == "__main__":
    main()
