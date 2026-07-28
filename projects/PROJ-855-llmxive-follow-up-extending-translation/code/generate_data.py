import os
import sys
import math
import time
import random
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pybullet as p
import pybullet_data
import pandas as pd
import numpy as np
import yaml

# Constants
NUM_EPISODES = 5000
RAW_DATA_PATH = "data/raw/synthetic_episodes.parquet"
PROCESSED_DIR = "data/processed"
CHECKSUM_FILE = "data/checksums.json"
CONFIG_FILE = "code/config.yaml"

def load_config(config_path: str = CONFIG_FILE) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_pybullet() -> None:
    """Initialize PyBullet physics engine."""
    p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1.0 / 240.0)

def create_robot_and_object() -> Tuple[int, int]:
    """Create the dual-arm robot and a box object."""
    # Load a simple dual-arm robot (using two PR2 arms or similar for simulation)
    # For this simulation, we use two simple box manipulators as proxies for wrists
    # and a box object in the center.
    
    # Load object
    box_id = p.loadURDF("cube_small.urdf", basePosition=[0, 0, 0.05], useFixedBase=False)
    p.changeDynamics(box_id, -1, lateralFriction=0.5)
    
    # Create two "wrist" frames (simple spheres)
    wrist_left = p.loadURDF("sphere2.urdf", basePosition=[-0.1, 0, 0.1], useFixedBase=True)
    wrist_right = p.loadURDF("sphere2.urdf", basePosition=[0.1, 0, 0.1], useFixedBase=True)
    
    return wrist_left, wrist_right, box_id

def apply_bi_manual_force(wrist_ids: Tuple[int, int], box_id: int, noise_vec: np.ndarray) -> None:
    """Apply forces to the object via the simulated wrists."""
    # Apply forces based on noise vector to simulate bi-manual push
    # Force magnitude scaled by noise
    force_magnitude = 10.0
    p.applyExternalForce(box_id, -1, [noise_vec[0] * force_magnitude, noise_vec[1] * force_magnitude, 0], 
                         [0, 0, 0], flags=p.LINK_FRAME)

def generate_noise_vector() -> np.ndarray:
    """Generate a random noise vector for force application."""
    return np.random.normal(loc=0.0, scale=1.0, size=2)

def run_simulation_episode(wrist_ids: Tuple[int, int], box_id: int, 
                           initial_bounds: Tuple[float, float, float, float],
                           noise_vec: np.ndarray, 
                           thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Run a single simulation episode and return results."""
    # Reset physics for this episode
    p.resetSimulation()
    setup_pybullet()
    
    # Recreate objects
    box_id = p.loadURDF("cube_small.urdf", basePosition=[0, 0, 0.05], useFixedBase=False)
    p.changeDynamics(box_id, -1, lateralFriction=0.5)
    
    # Record initial state
    initial_pos = p.getBasePositionAndOrientation(box_id)[0]
    
    # Apply force
    apply_bi_manual_force(wrist_ids, box_id, noise_vec)
    
    # Simulate for a fixed duration
    steps = 100
    for _ in range(steps):
        p.stepSimulation()
        time.sleep(1.0/240.0)
    
    # Get final state
    final_pos = p.getBasePositionAndOrientation(box_id)[0]
    
    # Calculate displacement
    displacement = math.sqrt((final_pos[0] - initial_pos[0])**2 + (final_pos[1] - initial_pos[1])**2)
    
    # Calculate tipping angle (simplified: check if object rotated significantly)
    # In a real scenario, we'd check orientation, but for this simplified model:
    # We assume if displacement > threshold, it's unstable
    tipping_threshold = thresholds.get('tipping_angle_threshold', 0.5)
    slippage_threshold = thresholds.get('slippage_distance_threshold', 0.1)
    
    # Determine stability
    is_stable = displacement < slippage_threshold
    label = 1 if is_stable else 0
    
    return {
        "translation_vector": noise_vec.tolist(),
        "initial_object_bounds": initial_bounds,
        "displacement": displacement,
        "label": label
    }

def generate_dataset(num_episodes: int = NUM_EPISODES, 
                     config_path: str = CONFIG_FILE) -> List[Dict[str, Any]]:
    """Generate the full dataset of episodes."""
    config = load_config(config_path)
    thresholds = config.get('thresholds', {})
    
    episodes = []
    setup_pybullet()
    
    # Generate initial object bounds (randomized for variety)
    # Format: (min_x, max_x, min_y, max_y)
    for i in range(num_episodes):
        # Randomize object size/position slightly
        size = random.uniform(0.02, 0.05)
        initial_bounds = (-size, size, -size, size)
        
        noise = generate_noise_vector()
        
        # Run simulation
        result = run_simulation_episode(
            (0, 0),  # Placeholder wrist IDs, recreated in function
            0,       # Placeholder box ID
            initial_bounds,
            noise,
            thresholds
        )
        
        episodes.append(result)
        
        if i % 1000 == 0:
            print(f"Generated {i}/{num_episodes} episodes")
    
    p.disconnect()
    return episodes

def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(file_path: str, checksum_registry: Dict[str, Any]) -> None:
    """Update the checksum registry with the new file's checksum."""
    checksum = compute_checksum(file_path)
    checksum_registry["files"][os.path.basename(file_path)] = {
        "checksum": checksum,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "size_bytes": os.path.getsize(file_path)
    }

def save_and_validate_data(episodes: List[Dict[str, Any]], 
                           output_path: str = RAW_DATA_PATH,
                           checksum_file: str = CHECKSUM_FILE) -> None:
    """Save the dataset to parquet and update checksums."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(episodes)
    
    # Validate: Ensure no forbidden columns (rotation, force)
    forbidden_cols = ['rotation', 'force', 'torque', 'quaternion']
    for col in forbidden_cols:
        if col in df.columns:
            raise ValueError(f"Forbidden column '{col}' found in dataset")
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    print(f"Saved {len(df)} episodes to {output_path}")
    
    # Update checksums
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            checksum_registry = json.load(f)
    else:
        checksum_registry = {"files": {}}
        
    update_checksums(output_path, checksum_registry)
    
    with open(checksum_file, 'w') as f:
        json.dump(checksum_registry, f, indent=2)
    
    print(f"Updated checksums in {checksum_file}")

def main():
    """Main entry point for data generation."""
    print("Starting data generation...")
    episodes = generate_dataset()
    save_and_validate_data(episodes)
    print("Data generation complete.")

if __name__ == "__main__":
    main()
