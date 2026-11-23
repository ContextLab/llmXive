"""
generate_data.py

Implements the core data generation pipeline for the llmXive project.
- Simulates bi‑manual manipulation episodes using PyBullet.
- Records only translation vectors and initial object bounds.
- Labels episodes as stable/unstable based on physics metrics from config.yaml.
- Saves raw data to Parquet at data/raw/synthetic_episodes.parquet and updates checksums.
"""

import os
import sys
import math
import time
import random
import json
import warnings
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Third‑party imports
import yaml
import pybullet as p
import pybullet_data
import pandas as pd
import numpy as np

# Local utilities
from utils.data_utils import compute_checksum, update_checksums
from utils.physics_metrics import get_thresholds

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # project root
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUM_FILE = PROJECT_ROOT / "data" / "checksums.json"

# Ensure output directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from ``code/config.yaml`` with sensible defaults."""
    cfg_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    # Default configuration – mirrors the structure used elsewhere in the repo
    default_cfg: Dict[str, Any] = {
        "simulation": {
            "gravity": -9.81,
            "time_step": 1.0 / 240.0,
            "max_steps_per_episode": 240,
            "num_episodes": 5000,
        },
        "data_generation": {
            "noise_amplitude": 0.01,
            "object_geometries": [
                "box_small",
                "box_medium",
                "box_large",
                "cylinder_small",
                "cylinder_large",
                "sphere_small",
                "sphere_large",
            ],
        },
        "seed": 42,
    }

    if not cfg_path.is_file():
        warnings.warn(f"Config file {cfg_path} not found – using defaults.")
        cfg = default_cfg
    else:
        with open(cfg_path, "r") as f:
            cfg = yaml.safe_load(f) or {}

        # Merge defaults for missing top‑level sections
        for top_key, sub_val in default_cfg.items():
            if isinstance(sub_val, dict):
                cfg.setdefault(top_key, {})
                for sub_k, sub_v in sub_val.items():
                    cfg[top_key].setdefault(sub_k, sub_v)
            else:
                cfg.setdefault(top_key, sub_val)

    # Back‑compatibility: map legacy ``random_seed`` to ``seed`` if needed
    if "random_seed" in cfg and "seed" not in cfg:
        cfg["seed"] = cfg["random_seed"]

    return cfg

# ----------------------------------------------------------------------
# PyBullet setup
# ----------------------------------------------------------------------
def setup_pybullet(config: Dict[str, Any]) -> int:
    """Initialize a head‑less PyBullet client."""
    physics_client = p.connect(p.DIRECT)
    data_path = pybullet_data.getDataPath()
    p.setAdditionalSearchPath(data_path)
    p.setGravity(0, 0, config["simulation"]["gravity"])
    p.setTimeStep(config["simulation"]["time_step"])
    return physics_client

# ----------------------------------------------------------------------
# Helper to load a URDF with a fallback to an absolute path
# ----------------------------------------------------------------------
def _load_urdf(file_name: str, *load_args, **load_kwargs):
    """
    Load a URDF file. First tries the regular PyBullet search path; if that fails,
    constructs an absolute path using ``pybullet_data.getDataPath()``.
    """
    try:
        return p.loadURDF(file_name, *load_args, **load_kwargs)
    except Exception as exc:
        # Construct absolute path as a fallback
        abs_path = os.path.join(pybullet_data.getDataPath(), file_name)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"URDF file not found: {file_name} (tried {abs_path})") from exc
        return p.loadURDF(abs_path, *load_args, **load_kwargs)

# ----------------------------------------------------------------------
# Scene creation
# ----------------------------------------------------------------------
def create_robot_and_object(physics_client: int, geometry_type: str) -> Tuple[int, int]:
    """
    Create a minimal “dual‑arm” robot (represented by an R2D2 model) and a
    geometric object. Returns the robot body id and the object body id.
    """
    # Load a flat ground plane
    _load_urdf("plane.urdf", physicsClientId=physics_client)

    # Dummy robot – forces are applied directly to the object.
    start_pos = [0, 0, 0]
    start_ori = p.getQuaternionFromEuler([0, 0, 0])
    robot_id = _load_urdf(
        "r2d2.urdf", start_pos, start_ori, physicsClientId=physics_client
    )

    # Map geometry identifiers to URDFs that are known to exist in
    # ``pybullet_data``. If a mapping is missing we fall back to a generic
    # small cube to keep the pipeline deterministic.
    urdf_map = {
        "box_small": "cube_small.urdf",
        "box_medium": "cube.urdf",
        "box_large": "cube.urdf",          # No native large cube; reuse medium
        "cylinder_small": "cylinder_small.urdf",
        "cylinder_large": "cylinder.urdf",
        "sphere_small": "sphere_small.urdf",
        "sphere_large": "sphere2.urdf",    # ``sphere2.urdf`` exists as a larger sphere
    }
    urdf_name = urdf_map.get(geometry_type, "cube_small.urdf")
    obj_id = _load_urdf(
        urdf_name, [0, 0, 1], physicsClientId=physics_client
    )

    # Small damping to avoid excessive jitter
    p.changeDynamics(
        obj_id,
        -1,
        linearDamping=0.01,
        angularDamping=0.01,
        physicsClientId=physics_client,
    )
    return robot_id, obj_id

# ----------------------------------------------------------------------
# Force application
# ----------------------------------------------------------------------
def apply_bi_manual_force(
    physics_client: int,
    obj_id: int,
    noise_vector: np.ndarray,
    step: int,
    total_steps: int,
) -> None:
    """
    Apply a time‑varying external force to ``obj_id``. The deterministic sinusoid
    plus a per‑episode random noise vector yields diverse trajectories while staying
    fully reproducible (seeded via ``np.random``).
    """
    base_force = 5.0
    t = step / total_steps
    fx = base_force * math.sin(2 * math.pi * t) + noise_vector[0] * 10.0
    fy = base_force * math.cos(2 * math.pi * t) + noise_vector[1] * 10.0
    fz = noise_vector[2] * 5.0
    p.applyExternalForce(
        obj_id,
        -1,
        [fx, fy, fz],
        [0, 0, 0],
        p.LINK_FRAME,
        physicsClientId=physics_client,
    )

# ----------------------------------------------------------------------
# Noise generation
# ----------------------------------------------------------------------
def generate_noise_vector(config: Dict[str, Any]) -> np.ndarray:
    """Gaussian noise with standard deviation defined in the config."""
    amp = float(config["data_generation"]["noise_amplitude"])
    return np.random.normal(0.0, amp, size=3)

# ----------------------------------------------------------------------
# Single episode simulation
# ----------------------------------------------------------------------
def run_simulation_episode(
    physics_client: int, geometry_type: str, config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Simulate one manipulation episode.

    Returns a dictionary containing only the columns required by the
    downstream pipeline:
        - geometry_id
        - initial_object_bounds
        - translation_trajectory
        - stability_label
    """
    robot_id, obj_id = create_robot_and_object(physics_client, geometry_type)

    # ------------------------------------------------------------------
    # Record initial geometry information
    # ------------------------------------------------------------------
    bounds_map = {
        "box_small": 0.05,
        "box_medium": 0.1,
        "box_large": 0.2,
        "cylinder_small": 0.05,
        "cylinder_large": 0.1,
        "sphere_small": 0.05,
        "sphere_large": 0.1,
    }
    size = bounds_map.get(geometry_type, 0.1)
    # Store as [xmin, ymin, zmin, xmax, ymax, zmax]
    initial_bounds = [-size, -size, -size, size, size, size]

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------
    max_steps = int(config["simulation"]["max_steps_per_episode"])
    noise = generate_noise_vector(config)
    start_pos, start_orn = p.getBasePositionAndOrientation(
        obj_id, physicsClientId=physics_client
    )
    translation_history: List[List[float]] = []
    stable = True

    tipping_thresh_deg, slippage_thresh_m = get_thresholds(config)

    for step in range(max_steps):
        apply_bi_manual_force(physics_client, obj_id, noise, step, max_steps)
        p.stepSimulation(physicsClientId=physics_client)

        pos, orn = p.getBasePositionAndOrientation(
            obj_id, physicsClientId=physics_client
        )

        # Record translation relative to start position
        trans_vec = [pos[i] - start_pos[i] for i in range(3)]
        translation_history.append(trans_vec)

        # Compute tipping angle (max of roll/pitch) and slippage distance
        euler = p.getEulerFromQuaternion(orn)
        roll, pitch = euler[0], euler[1]
        tip_angle_deg = math.degrees(max(abs(roll), abs(pitch)))
        slippage_dist = math.hypot(pos[0] - start_pos[0], pos[1] - start_pos[1])

        if tip_angle_deg > tipping_thresh_deg or slippage_dist > slippage_thresh_m:
            stable = False
            # Early exit – we have already violated a stability condition.
            break

    # Clean up bodies for the next episode
    p.removeBody(obj_id, physicsClientId=physics_client)
    p.removeBody(robot_id, physicsClientId=physics_client)

    episode = {
        "geometry_id": geometry_type,
        "initial_object_bounds": initial_bounds,
        "translation_trajectory": translation_history,
        "stability_label": 1 if stable else 0,
    }
    return episode

# ----------------------------------------------------------------------
# Full dataset generation
# ----------------------------------------------------------------------
def generate_dataset(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate ``config['simulation']['num_episodes']`` valid episodes.
    Episodes that raise an exception are discarded and replaced until the
    target count is reached.
    """
    target = int(config["simulation"]["num_episodes"])
    physics_client = setup_pybullet(config)

    geometries = config["data_generation"]["object_geometries"]
    rows: List[Dict[str, Any]] = []
    attempts = 0
    max_attempts = target * 3  # safety margin

    # Seed for reproducibility
    np.random.seed(int(config.get("seed", 0)))
    random.seed(int(config.get("seed", 0)))

    while len(rows) < target and attempts < max_attempts:
        attempts += 1
        geom = random.choice(geometries)
        try:
            episode = run_simulation_episode(physics_client, geom, config)
            if episode is not None:
                rows.append(episode)
        except Exception as exc:
            # Log the failure and continue – the loop will generate a replacement.
            print(
                f"[generate_data] Episode failed (attempt {attempts}): {exc}",
                file=sys.stderr,
            )
            continue

    p.disconnect(physics_client)

    if len(rows) < target:
        raise RuntimeError(
            f"Only generated {len(rows)} episodes after {attempts} attempts (target {target})."
        )

    df = pd.DataFrame(rows)
    return df

# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
def save_and_validate_data(df: pd.DataFrame, config: Dict[str, Any]) -> None:
    """
    Persist the raw dataset to ``data/raw/synthetic_episodes.parquet`` and
    update the SHA‑256 checksum registry.
    """
    output_path = RAW_DATA_DIR / "synthetic_episodes.parquet"
    # Write Parquet; requires a parquet engine (pyarrow)
    df.to_parquet(output_path, index=False)

    # Initialise a minimal checksum registry if missing
    if not CHECKSUM_FILE.is_file():
        init_registry = {"version": "1.0.0", "files": {}}
        with open(CHECKSUM_FILE, "w") as f:
            json.dump(init_registry, f, indent=2)

    # Update checksum registry (registry path is the second argument)
    update_checksums(str(output_path), str(CHECKSUM_FILE))

    print(f"Saved raw dataset ({len(df)} rows) to {output_path}")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the data‑generation pipeline."""
    parser = argparse.ArgumentParser(description="Generate synthetic manipulation episodes.")
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the YAML configuration file.",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    df = generate_dataset(cfg)
    save_and_validate_data(df, cfg)
    print("Data generation completed successfully.")

if __name__ == "__main__":
    main()
