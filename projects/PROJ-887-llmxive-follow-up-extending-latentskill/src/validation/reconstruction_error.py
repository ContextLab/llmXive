"""
Reconstruction Error Calculator (Task T022b).

Calculates the cosine distance (reconstruction error) between synthesized
LoRA weights and the true weights of a known composite task.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from src.utils.config import get_project_root, get_config

# Configuration
PROJECT_ROOT = get_project_root()
CONFIG = get_config()
SYNTHESIZED_DIR = PROJECT_ROOT / "artifacts" / "synthesized_adapters"
TRUE_WEIGHTS_DIR = PROJECT_ROOT / "artifacts" / "true_weights"  # Assumed location for ground truth
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "reconstruction_error.json"

# Ensure output directory exists
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_lora_weights(path: Path) -> Dict[str, np.ndarray]:
    """
    Loads LoRA A/B matrices from a .npz file.
    Expected structure: {'layer_name_A': array, 'layer_name_B': array}
    """
    if not path.exists():
        raise FileNotFoundError(f"Weight file not found: {path}")

    data = np.load(path)
    weights = {}
    for key in data.files:
        weights[key] = data[key]
    return weights


def flatten_weights(weights: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Flattens all A and B matrices into a single 1D vector for comparison.
    """
    vectors = []
    for key in sorted(weights.keys()):
        vec = weights[key].flatten()
        vectors.append(vec)
    return np.concatenate(vectors)


def calculate_cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculates cosine distance: 1 - cosine_similarity.
    """
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 1.0  # Maximum distance if one vector is zero

    similarity = np.dot(v1, v2) / (norm_v1 * norm_v2)
    # Clip to avoid numerical errors
    similarity = np.clip(similarity, -1.0, 1.0)
    return float(1.0 - similarity)


def run_reconstruction_error_analysis():
    """
    Main execution function for T022b.
    1. Loads synthesized weights from artifacts/synthesized_adapters/
    2. Loads corresponding true weights from artifacts/true_weights/
    3. Calculates cosine distance.
    4. Saves result to data/results/reconstruction_error.json.
    """
    start_time = time.time()
    results = []

    # Identify pairs to compare
    # We assume naming convention: <task_id>_synthesized.npz and <task_id>_true.npz
    synthesized_files = list(SYNTHESIZED_DIR.glob("*_synthesized.npz"))

    if not synthesized_files:
        print(f"Warning: No synthesized weights found in {SYNTHESIZED_DIR}")
        # Write empty result to indicate no data processed
        result_data = {
            "status": "no_data",
            "message": "No synthesized weights found to compare.",
            "results": [],
            "execution_time_seconds": 0.0
        }
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(result_data, f, indent=2)
        return

    for syn_file in synthesized_files:
        task_id = syn_file.stem.replace("_synthesized", "")
        true_file = PROJECT_ROOT / "artifacts" / "true_weights" / f"{task_id}_true.npz"

        if not true_file.exists():
            print(f"Warning: True weights not found for {task_id} at {true_file}. Skipping.")
            continue

        try:
            # Load weights
            syn_weights = load_lora_weights(syn_file)
            true_weights = load_lora_weights(true_file)

            # Flatten
            syn_vec = flatten_weights(syn_weights)
            true_vec = flatten_weights(true_weights)

            # Ensure dimensions match
            if syn_vec.shape != true_vec.shape:
                raise ValueError(f"Dimension mismatch for {task_id}: "
                                 f"syn={syn_vec.shape}, true={true_vec.shape}")

            # Calculate error
            error = calculate_cosine_distance(syn_vec, true_vec)

            results.append({
                "task_id": task_id,
                "synthesized_file": str(syn_file.relative_to(PROJECT_ROOT)),
                "true_file": str(true_file.relative_to(PROJECT_ROOT)),
                "reconstruction_error_cosine_distance": error,
                "vector_dimension": int(syn_vec.shape[0])
            })
            print(f"Computed error for {task_id}: {error:.6f}")

        except Exception as e:
            print(f"Error processing {task_id}: {e}")
            results.append({
                "task_id": task_id,
                "status": "failed",
                "error_message": str(e)
            })

    end_time = time.time()
    execution_time = end_time - start_time

    # Aggregate result
    final_output = {
        "status": "completed",
        "execution_time_seconds": round(execution_time, 3),
        "results": results,
        "summary": {
            "total_tasks_processed": len(results),
            "successful_calculations": sum(1 for r in results if "reconstruction_error_cosine_distance" in r),
            "failed_calculations": sum(1 for r in results if r.get("status") == "failed")
        }
    }

    # Calculate mean error if possible
    errors = [r["reconstruction_error_cosine_distance"] for r in results if "reconstruction_error_cosine_distance" in r]
    if errors:
        final_output["summary"]["mean_reconstruction_error"] = round(np.mean(errors), 6)

    # Write to disk
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(final_output, f, indent=2)

    print(f"Reconstruction error analysis complete. Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_reconstruction_error_analysis()
