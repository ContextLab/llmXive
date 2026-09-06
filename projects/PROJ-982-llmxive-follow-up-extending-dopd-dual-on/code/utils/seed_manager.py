"""
Seed Manager for llmXive project.
Defines and generates distinct seed ranges for Train, Eval, and Baseline configurations.
"""
import numpy as np
import json
import os
from typing import Dict, List, Any

# Master seed for deterministic generation
MASTER_SEED = 42

# Seed Range Definitions (inclusive start, exclusive end for ranges, or specific sets)
# Train: 0-49 (50 seeds)
TRAIN_START = 0
TRAIN_END = 50  # exclusive

# Eval: 50-99 (50 seeds)
EVAL_START = 50
EVAL_END = 100  # exclusive

# Baseline: 1000-1099 (100 seeds)
BASELINE_START = 1000
BASELINE_END = 1100  # exclusive

def get_seed_ranges() -> Dict[str, List[int]]:
    """
    Generates distinct seed ranges deterministically using a master seed.
    Returns a dictionary with keys: 'train', 'eval', 'baseline'.
    """
    # Initialize RNG with master seed
    rng = np.random.RandomState(MASTER_SEED)

    # Generate the ranges explicitly as defined in the spec
    # We use the ranges directly as they are defined by the task requirements
    # The rng is used to ensure that if we ever needed to shuffle or sample from these,
    # it would be deterministic. Here we simply return the defined integer sets.
    train_seeds = list(range(TRAIN_START, TRAIN_END))
    eval_seeds = list(range(EVAL_START, EVAL_END))
    baseline_seeds = list(range(BASELINE_START, BASELINE_END))

    # Verify disjointness
    train_set = set(train_seeds)
    eval_set = set(eval_seeds)
    baseline_set = set(baseline_seeds)

    assert len(train_set & eval_set) == 0, "Train and Eval seed sets must be disjoint"
    assert len(train_set & baseline_set) == 0, "Train and Baseline seed sets must be disjoint"
    assert len(eval_set & baseline_set) == 0, "Eval and Baseline seed sets must be disjoint"

    return {
        "train": train_seeds,
        "eval": eval_seeds,
        "baseline": baseline_seeds
    }

def save_seed_manifest(output_path: str) -> Dict[str, Any]:
    """
    Generates seed ranges and saves them to a JSON manifest file.
    Args:
        output_path: Path to the output JSON file.
    Returns:
        The generated manifest dictionary.
    """
    ranges = get_seed_ranges()

    manifest = {
        "master_seed": MASTER_SEED,
        "ranges": {
            "train": {
                "start": TRAIN_START,
                "end": TRAIN_END,
                "count": len(ranges["train"]),
                "seeds": ranges["train"]
            },
            "eval": {
                "start": EVAL_START,
                "end": EVAL_END,
                "count": len(ranges["eval"]),
                "seeds": ranges["eval"]
            },
            "baseline": {
                "start": BASELINE_START,
                "end": BASELINE_END,
                "count": len(ranges["baseline"]),
                "seeds": ranges["baseline"]
            }
        },
        "disjoint_check": {
            "train_eval": len(set(ranges["train"]) & set(ranges["eval"])) == 0,
            "train_baseline": len(set(ranges["train"]) & set(ranges["baseline"])) == 0,
            "eval_baseline": len(set(ranges["eval"]) & set(ranges["baseline"])) == 0
        }
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest

def get_seed_range_for_purpose(purpose: str) -> List[int]:
    """
    Helper to get a specific seed list by purpose string.
    Args:
        purpose: One of 'train', 'eval', 'baseline'.
    Returns:
        List of seeds for that purpose.
    """
    ranges = get_seed_ranges()
    if purpose not in ranges:
        raise ValueError(f"Unknown purpose: {purpose}. Must be one of {list(ranges.keys())}")
    return ranges[purpose]

if __name__ == "__main__":
    # Default output path relative to project root
    output_path = "data/processed/seed_manifest.json"
    print(f"Generating seed manifest at {output_path}...")
    manifest = save_seed_manifest(output_path)
    print(f"Success. Train seeds: {len(manifest['ranges']['train']['seeds'])}, "
          f"Eval seeds: {len(manifest['ranges']['eval']['seeds'])}, "
          f"Baseline seeds: {len(manifest['ranges']['baseline']['seeds'])}")
    print(f"Disjoint check passed: {all(manifest['disjoint_check'].values())}")
