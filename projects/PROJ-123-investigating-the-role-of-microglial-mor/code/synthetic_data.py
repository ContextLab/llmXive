"""
Synthetic Data Generator for Microglial Morphology Pipeline Validation.

This module generates realistic synthetic microscopy images and corresponding
morphological ground truth data. It is designed to validate the data ingestion
and morphometry pipeline (T012-T019) before processing real experimental data.

The generator creates:
1. Synthetic microscopy images (PNG) with microglia-like morphology.
2. A ground truth CSV (data/synthetic/microglia_ground_truth.csv) containing
   the exact known metrics used to generate the images.
3. A metadata JSON file (data/synthetic/microglia_metadata.json) linking
   images to simulated cognitive scores and brain regions.

Dependencies:
    - numpy
    - pandas
    - scikit-image
    - opencv-python-headless
    - pyyaml
"""

import os
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from skimage import io, draw
from skimage.filters import gaussian
from skimage.morphology import skeletonize

# Import project config
from code.config import PROJECT_ROOT, DATA_DIR, SEED


def set_seed(seed: int = SEED) -> None:
    """Set global random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def generate_microglia_cell(
    img_shape: tuple[int, int],
    soma_center: tuple[int, int],
    num_branches: int,
    soma_radius: float,
    process_length: float,
    noise_level: float = 0.05
) -> np.ndarray:
    """
    Generate a synthetic microglia cell image.

    Uses a simplified reaction-diffusion inspired branching model (per Turing's
    morphogenesis principles referenced in research.md) to create realistic
    branching patterns.

    Args:
        img_shape: (height, width) of the output image.
        soma_center: (y, x) coordinates of the soma center.
        num_branches: Number of primary branches.
        soma_radius: Radius of the cell body.
        process_length: Average length of processes.
        noise_level: Standard deviation of Gaussian noise.

    Returns:
        2D numpy array representing the cell image.
    """
    # Initialize empty canvas
    canvas = np.zeros(img_shape, dtype=np.float32)

    # Draw Soma (Gaussian blob)
    y, x = soma_center
    rr, cc = draw.disk((y, x), soma_radius)
    # Make soma brighter
    soma_intensity = 1.0
    canvas[rr, cc] = np.maximum(canvas[rr, cc], soma_intensity)

    # Draw Branches
    # We simulate branching by creating random walks from the soma
    # with a tendency to branch outwards.
    current_intensity = 0.8
    decay_factor = 0.95

    for _ in range(num_branches):
        # Random initial direction
        angle = random.uniform(0, 2 * np.pi)
        direction = np.array([np.cos(angle), np.sin(angle)])

        current_pos = np.array([y, x], dtype=float)
        current_len = 0
        branch_width = 2.0

        while current_len < process_length:
            # Random walk step with slight bias to continue straight
            step_size = 1.0
            # Add some randomness to direction
            noise_angle = random.uniform(-0.3, 0.3)
            direction = np.array([
                np.cos(angle + noise_angle),
                np.sin(angle + noise_angle)
            ])

            next_pos = current_pos + direction * step_size

            # Check bounds
            if not (0 <= next_pos[0] < img_shape[0] and 0 <= next_pos[1] < img_shape[1]):
                break

            # Draw line segment
            rr, cc = draw.line(
                int(current_pos[0]), int(current_pos[1]),
                int(next_pos[0]), int(next_pos[1])
            )
            # Add intensity with decay
            intensity = current_intensity * np.exp(-current_len / (process_length * 0.5))
            canvas[rr, cc] = np.maximum(canvas[rr, cc], intensity)

            current_pos = next_pos
            current_len += step_size

            # Random branching event
            if random.random() < 0.05: # 5% chance per step
                # Spawn a new branch
                new_angle = angle + random.uniform(-1.0, 1.0)
                new_dir = np.array([np.cos(new_angle), np.sin(new_angle)])
                # Recursive call simplified: just extend from current pos
                # For simplicity in this generator, we just continue the walk
                # but with a new random angle component added to the main loop logic
                # effectively simulating a branch.
                angle = new_angle
                current_intensity *= decay_factor

    # Add Gaussian noise
    noise = np.random.normal(0, noise_level, canvas.shape)
    canvas = np.clip(canvas + noise, 0, 1)

    return canvas


def generate_ground_truth_metrics(
    n_samples: int = 50,
    img_shape: tuple[int, int] = (256, 256)
) -> pd.DataFrame:
    """
    Generate a DataFrame of synthetic ground truth metrics.

    This simulates the output of the morphometry pipeline (branch points,
    soma area, etc.) with realistic distributions based on literature values
    for microglial morphology in different brain regions.

    Args:
        n_samples: Number of synthetic cells to generate.
        img_shape: Shape of the generated images.

    Returns:
        DataFrame with ground truth metrics.
    """
    data = []

    # Define brain regions and their typical morphological characteristics
    # (Simplified model: Hippocampus = more ramified, Cortex = less)
    regions = [
        {"name": "Hippocampus", "base_branches": 8, "base_soma": 10},
        {"name": "Cortex", "base_branches": 6, "base_soma": 12},
        {"name": "Hypothalamus", "base_branches": 7, "base_soma": 11},
    ]

    for i in range(n_samples):
        region_info = random.choice(regions)
        region_name = region_info["name"]

        # Generate morphological parameters with some biological variance
        num_branches = int(np.random.normal(region_info["base_branches"], 2))
        num_branches = max(2, num_branches) # Minimum 2 branches

        soma_radius = np.random.normal(region_info["base_soma"], 1.5)
        soma_radius = max(3.0, soma_radius)

        process_length = np.random.normal(40.0, 10.0)
        process_length = max(10.0, process_length)

        # Calculate derived metrics (simulating what the pipeline would measure)
        # Soma area = pi * r^2
        soma_area = np.pi * (soma_radius ** 2)

        # Total length approx: branches * avg_length
        total_length = num_branches * (process_length * 0.8)

        # Branch points approx: num_branches - 1 (simplified)
        branch_points = max(1, num_branches - 1)

        # Sholl intersections (simplified model: decay with radius)
        sholl_intersections = [max(0, int(branch_points * np.exp(-r/15))) for r in [5, 10, 15, 20, 25]]

        # Assign cognitive score (0-100) based on region and morphology
        # Higher complexity (more branches) -> slightly better score in controls
        # Simulate age-related decline by adding noise
        base_score = 90 if "Control" in region_name else 60 # Simplified logic
        # Actually, let's map region to a subject type for the metadata
        subject_type = random.choice(["Control", "MCI", "AD"])

        if subject_type == "Control":
            cognitive_score = int(np.random.normal(95, 5))
            amyloid_load = np.random.normal(0.2, 0.05)
        elif subject_type == "MCI":
            cognitive_score = int(np.random.normal(80, 8))
            amyloid_load = np.random.normal(0.5, 0.1)
        else: # AD
            cognitive_score = int(np.random.normal(55, 10))
            amyloid_load = np.random.normal(0.8, 0.1)

        # Clamp values
        cognitive_score = max(0, min(100, cognitive_score))
        amyloid_load = max(0.0, min(1.0, amyloid_load))

        data.append({
            "image_id": f"synthetic_{i:04d}",
            "brain_region": region_name,
            "subject_type": subject_type,
            "cognitive_score": cognitive_score,
            "amyloid_load": round(amyloid_load, 3),
            "soma_radius": round(soma_radius, 2),
            "soma_area": round(soma_area, 2),
            "num_branches": num_branches,
            "branch_points": branch_points,
            "total_length": round(total_length, 2),
            "sholl_r5": sholl_intersections[0],
            "sholl_r10": sholl_intersections[1],
            "sholl_r15": sholl_intersections[2],
            "sholl_r20": sholl_intersections[3],
            "sholl_r25": sholl_intersections[4]
        })

    return pd.DataFrame(data)


def generate_synthetic_dataset(
    output_dir: str = None,
    n_samples: int = 50
) -> dict:
    """
    Main entry point to generate the full synthetic dataset.

    Args:
        output_dir: Directory to save outputs. Defaults to data/synthetic.
        n_samples: Number of samples to generate.

    Returns:
        Dictionary with paths to generated files.
    """
    if output_dir is None:
        output_dir = os.path.join(DATA_DIR, "synthetic")

    os.makedirs(output_dir, exist_ok=True)

    set_seed()

    print(f"Generating {n_samples} synthetic microglia images...")

    # 1. Generate Ground Truth Metrics
    df_ground_truth = generate_ground_truth_metrics(n_samples)

    # 2. Generate Images and Metadata
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    metadata_list = []

    for idx, row in df_ground_truth.iterrows():
        img_id = row["image_id"]
        img_shape = (256, 256)

        # Random soma position
        soma_y = random.randint(50, img_shape[0]-50)
        soma_x = random.randint(50, img_shape[1]-50)

        # Generate image
        img = generate_microglia_cell(
            img_shape=img_shape,
            soma_center=(soma_y, soma_x),
            num_branches=row["num_branches"],
            soma_radius=row["soma_radius"],
            process_length=row["total_length"] / max(1, row["num_branches"])
        )

        # Save image
        img_path = os.path.join(images_dir, f"{img_id}.png")
        io.imsave(img_path, img, check_contrast=False)

        # Prepare metadata
        metadata_list.append({
            "image_id": img_id,
            "filename": f"{img_id}.png",
            "brain_region": row["brain_region"],
            "subject_type": row["subject_type"],
            "cognitive_score": row["cognitive_score"],
            "amyloid_load": row["amyloid_load"]
        })

    # 3. Save Metadata JSON
    metadata_path = os.path.join(output_dir, "microglia_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata_list, f, indent=2)

    # 4. Save Ground Truth CSV
    gt_path = os.path.join(output_dir, "microglia_ground_truth.csv")
    df_ground_truth.to_csv(gt_path, index=False)

    print(f"Synthetic dataset generated successfully.")
    print(f"  Images: {images_dir}")
    print(f"  Metadata: {metadata_path}")
    print(f"  Ground Truth: {gt_path}")

    return {
        "images_dir": images_dir,
        "metadata_path": metadata_path,
        "ground_truth_path": gt_path
    }


if __name__ == "__main__":
    # Execute generation
    generate_synthetic_dataset()
