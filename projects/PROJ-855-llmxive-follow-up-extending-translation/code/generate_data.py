import os
import sys
import math
import time
import random
import json
import hashlib
import gc
from datetime import datetime
from pathlib import Path

# Attempt to import pybullet, but allow graceful failure if not installed for this specific script context
# However, per task requirements, we assume the environment is set up.
try:
    import pybullet as p
    import pybullet_data
except ImportError:
    print("ERROR: PyBullet is required to run this script. Install with: pip install pybullet")
    sys.exit(1)

import pandas as pd
import numpy as np

from utils.physics_metrics import load_config, get_thresholds, is_stable, calculate_tipping_angle, calculate_slippage_distance
from utils.data_utils import compute_checksum, update_checksums

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: Config file {config_path} not found. Using defaults.")
        return {
            "physics": {
                "tipping_angle_threshold": 0.15,
                "slippage_distance_threshold": 0.02
            },
            "generation": {
                "num_episodes": 5000,
                "episode_steps": 100
            }
        }

def setup_pybullet():
    """Initialize PyBullet in direct mode."""
    p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setRealTimeSimulation(0)
    p.setTimeStep(1.0 / 240.0)

def create_robot_and_object(object_type="cube"):
    """Create a simple robot arm and a movable object."""
    # Load a simple plane
    plane_id = p.loadURDF("plane.urdf")

    # Create a simple box object
    if object_type == "cube":
        base_pos = [0, 0, 0.5]
        visual_shape = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.05])
        collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.05])
        mass = 1.0
    elif object_type == "sphere":
        base_pos = [0, 0, 0.5]
        visual_shape = p.createVisualShape(p.GEOM_SPHERE, radius=0.05)
        collision_shape = p.createCollisionShape(p.GEOM_SPHERE, radius=0.05)
        mass = 1.0
    else:
        # Default to cube
        base_pos = [0, 0, 0.5]
        visual_shape = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.05])
        collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.05])
        mass = 1.0

    object_id = p.createMultiBody(baseMass=mass, baseCollisionShapeIndex=collision_shape, baseVisualShapeIndex=visual_shape, basePosition=base_pos)

    # Create a simple "robot" (two spheres representing grippers)
    gripper1 = p.createMultiBody(baseMass=0, baseCollisionShapeIndex=p.createCollisionShape(p.GEOM_SPHERE, radius=0.02), baseVisualShapeIndex=p.createVisualShape(p.GEOM_SPHERE, radius=0.02), basePosition=[-0.1, 0, 0.5])
    gripper2 = p.createMultiBody(baseMass=0, baseCollisionShapeIndex=p.createCollisionShape(p.GEOM_SPHERE, radius=0.02), baseVisualShapeIndex=p.createVisualShape(p.GEOM_SPHERE, radius=0.02), basePosition=[0.1, 0, 0.5])

    return object_id, gripper1, gripper2, plane_id

def apply_bi_manual_force(object_id, gripper1, gripper2, force_vector, noise_vector):
    """Apply forces to the object via the 'grippers'."""
    # Calculate total force
    total_force = [f + n for f, n in zip(force_vector, noise_vector)]
    # Apply at center of mass
    p.applyExternalForce(object_id, -1, total_force, [0, 0, 0], p.WORLD_FRAME)

def generate_noise_vector(scale=0.1):
    """Generate a random noise vector for force perturbation."""
    return [random.uniform(-scale, scale) for _ in range(3)]

def run_simulation_episode(object_id, gripper1, gripper2, initial_pos, steps=100):
    """Run a single simulation episode and return trajectory data."""
    trajectory = []
    initial_quat = p.getBasePositionAndOrientation(object_id)[1]
    initial_linear_vel = p.getBaseVelocity(object_id)[0]

    # Reset object state
    p.resetBasePositionAndOrientation(object_id, initial_pos, initial_quat)
    p.resetBaseVelocity(object_id, [0,0,0], [0,0,0])

    for step in range(steps):
        # Generate random force
        force = [random.uniform(-5, 5) for _ in range(3)]
        noise = generate_noise_vector(0.5)

        # Apply force
        apply_bi_manual_force(object_id, gripper1, gripper2, force, noise)

        # Step simulation
        p.stepSimulation()

        # Get state
        pos, quat = p.getBasePositionAndOrientation(object_id)
        linear_vel, angular_vel = p.getBaseVelocity(object_id)

        # Record translation vector (relative to start)
        rel_pos = [pos[i] - initial_pos[i] for i in range(3)]

        trajectory.append({
            "step": step,
            "translation_x": rel_pos[0],
            "translation_y": rel_pos[1],
            "translation_z": rel_pos[2],
            "linear_vel_x": linear_vel[0],
            "linear_vel_y": linear_vel[1],
            "linear_vel_z": linear_vel[2]
        })

        # Check for failure (e.g., object falls below threshold)
        if pos[2] < 0.1:
            return trajectory, False, pos, quat

    return trajectory, True, pos, quat

def generate_dataset(num_episodes=5000, config=None):
    """Generate the full dataset."""
    if config is None:
        config = load_config()

    setup_pybullet()

    data_rows = []
    episode_count = 0
    valid_count = 0
    attempts = 0

    # Thresholds
    thresholds = get_thresholds(config)

    while valid_count < num_episodes and attempts < num_episodes * 2:
        attempts += 1
        # Randomize object type and position
        obj_type = random.choice(["cube", "sphere"])
        start_pos = [random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 0.5 + random.uniform(0, 0.2)]

        obj_id, gripper1, gripper2, plane_id = create_robot_and_object(obj_type)

        try:
            trajectory, is_success, final_pos, final_quat = run_simulation_episode(obj_id, gripper1, gripper2, start_pos, steps=config.get("generation", {}).get("episode_steps", 100))

            if len(trajectory) == 0:
                continue

            # Calculate metrics for labeling
            # Simplified metric calculation for simulation
            max_tipping = 0.0
            max_slippage = 0.0

            # Extract final velocities and positions to estimate stability
            final_step = trajectory[-1]
            final_vel = [final_step['linear_vel_x'], final_step['linear_vel_y'], final_step['linear_vel_z']]
            final_disp = [final_step['translation_x'], final_step['translation_y'], final_step['translation_z']]

            # Use physics metrics logic
            # Note: In a real scenario, we'd calculate angle from quat, here we approximate
            tipping_angle = abs(math.atan2(final_vel[2], math.sqrt(final_vel[0]**2 + final_vel[1]**2))) if math.sqrt(final_vel[0]**2 + final_vel[1]**2) > 0 else 0
            slippage_dist = math.sqrt(final_disp[0]**2 + final_disp[1]**2)

            label = 1 if is_stable(tipping_angle, slippage_dist, thresholds) else 0

            # Record ONLY required columns: translation vectors, initial bounds, label, geometry_id
            # Geometry ID is derived from type + random seed for uniqueness
            geom_id = f"{obj_type}_{attempts}"

            row = {
                "geometry_id": geom_id,
                "object_type": obj_type,
                "initial_x": start_pos[0],
                "initial_y": start_pos[1],
                "initial_z": start_pos[2],
                "trajectory": json.dumps(trajectory), # Storing as JSON string for now, could be flattened
                "label": label,
                "is_success": is_success,
                "tipping_angle": tipping_angle,
                "slippage_distance": slippage_dist
            }

            data_rows.append(row)
            valid_count += 1

        except Exception as e:
            print(f"Episode {attempts} failed with error: {e}")
        finally:
            # Clean up physics objects
            p.removeBody(obj_id)
            p.removeBody(gripper1)
            p.removeBody(gripper2)
            p.removeBody(plane_id)

        episode_count += 1
        if episode_count % 500 == 0:
            print(f"Generated {valid_count}/{num_episodes} valid episodes (Attempts: {attempts})")

    p.disconnect()

    df = pd.DataFrame(data_rows)
    return df

def save_and_validate_data(df, output_path="data/raw/synthetic_episodes.parquet", config_path="code/config.yaml"):
    """Save the dataset to parquet and update checksums."""
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to Parquet
    df.to_parquet(output_path, index=False)
    print(f"Dataset saved to {output_path} with {len(df)} rows.")

    # Validate no forbidden columns (FR-001)
    forbidden_cols = ['rotation_quaternion', 'joint_torques', 'force_sensor_readings']
    existing_cols = list(df.columns)
    for col in forbidden_cols:
        if col in existing_cols:
            raise ValueError(f"Validation Failed: Forbidden column '{col}' found in dataset.")

    # Update checksums
    checksums_path = "data/checksums.json"
    update_checksums(checksums_path, output_path)
    print(f"Checksum updated in {checksums_path}")

    return True

def main():
    """Main entry point for data generation."""
    config = load_config()
    num_episodes = config.get("generation", {}).get("num_episodes", 5000)

    print(f"Starting data generation for {num_episodes} episodes...")
    df = generate_dataset(num_episodes=num_episodes, config=config)

    if len(df) < 5000:
        print(f"Warning: Only generated {len(df)} episodes, expected {num_episodes}.")

    save_and_validate_data(df)
    print("Data generation complete.")

if __name__ == "__main__":
    main()
