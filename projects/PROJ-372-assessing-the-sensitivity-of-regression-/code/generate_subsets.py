"""
Task T047: Generate N subsets per tier (N=200) and save subset indices.

This script generates random observation subsets for each sample size tier
defined in the configuration (T007a) and saves the subset indices to
artifacts/stability/subsets_*.json.

Dependencies:
- T023 (Resampling Engine logic)
- T007a (Sample size tiers configuration)
- T009 (Checkpointing schema)
"""

import json
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to import local modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import load_sample_tiers, load_config
from src.utils.checkpoint import save_checkpoint, CheckpointState

# Constants
SUBSETS_PER_TIER = 200
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "stability"
DATASET_NAME = "auto"  # Default dataset name for output file naming
SEED = 42  # Fixed seed for reproducibility

def generate_subset_indices(n_total: int, n_subset: int, seed_offset: int) -> List[int]:
    """
    Generate a random subset of indices.

    Args:
        n_total: Total number of observations in the dataset.
        n_subset: Number of observations to select.
        seed_offset: Offset to ensure different subsets per iteration.

    Returns:
        List of selected indices.
    """
    if n_subset > n_total:
        raise ValueError(f"Requested subset size {n_subset} exceeds total {n_total}")
    
    # Use a local random instance to avoid global state interference
    rng = random.Random(SEED + seed_offset)
    return sorted(rng.sample(range(n_total), n_subset))

def main():
    """
    Main entry point for generating subset indices.
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load configuration
    # We assume the dataset size is known or loaded from a previous profile step.
    # For this task, we will attempt to load a profile if available, 
    # otherwise we expect the dataset size to be passed or default to a known value.
    # In a real pipeline, this would come from the ingestion profile (T020).
    
    profile_path = PROJECT_ROOT / "artifacts" / "profiles" / f"{DATASET_NAME}_profile.json"
    n_observations = 0

    if profile_path.exists():
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            n_observations = profile.get("n_observations", 0)
        print(f"Loaded dataset size {n_observations} from profile.")
    else:
        # Fallback for standalone execution if profile is missing
        # In a real scenario, this should fail loudly or be passed as an argument
        # For the purpose of this script generation, we assume a reasonable default 
        # or require the profile to exist. 
        # Let's assume the user must run the ingestion first.
        print(f"Warning: Profile not found at {profile_path}. "
              "Please ensure T020 has run or provide a dataset size argument.")
        # We cannot proceed without n_observations. 
        # In a strict pipeline, we would exit.
        # For this task implementation, we will raise an error if not found.
        raise FileNotFoundError(
            f"Dataset profile not found at {profile_path}. "
            "Run ingestion (T020) first to generate this file."
        )

    if n_observations == 0:
        raise ValueError("Dataset size is 0. Cannot generate subsets.")

    # Load sample size tiers from config (T007a)
    # The config should return a list of percentages or absolute sizes.
    # Based on T007a, these are percentages: [10, 25, 50, 75, 90]
    try:
        config = load_config()
        tiers = load_sample_tiers(config)
    except Exception as e:
        print(f"Error loading sample size tiers: {e}")
        raise

    print(f"Generating {SUBSETS_PER_TIER} subsets per tier for dataset with {n_observations} observations.")
    print(f"Tiers (percentages): {tiers}")

    all_subsets: Dict[str, List[List[int]]] = {}

    # Initialize checkpoint
    checkpoint_state = CheckpointState(
        task_id="T047",
        status="running",
        progress=0,
        details="Initializing subset generation"
    )
    save_checkpoint(checkpoint_state, OUTPUT_DIR / "subsets_checkpoint.json")

    total_tiers = len(tiers)
    processed_tiers = 0

    for tier_idx, tier_pct in enumerate(tiers):
        tier_name = f"tier_{tier_pct}pct"
        n_subset = int(n_observations * (tier_pct / 100.0))
        
        # Enforce minimum subset size constraint (e.g., >= 10 predictors)
        # Assuming a reasonable number of predictors, we enforce a minimum of 10.
        if n_subset < 10:
            print(f"Skipping tier {tier_pct}%: subset size {n_subset} < 10 (minimum).")
            all_subsets[tier_name] = []
            continue

        print(f"Generating subsets for {tier_name} (size={n_subset})...")
        
        subsets_for_tier = []
        for i in range(SUBSETS_PER_TIER):
            try:
                indices = generate_subset_indices(n_observations, n_subset, seed_offset=i)
                subsets_for_tier.append(indices)
                
                # Periodic checkpoint update
                if (i + 1) % 50 == 0:
                    checkpoint_state.progress = (processed_tiers + (i + 1) / SUBSETS_PER_TIER) / total_tiers * 100
                    checkpoint_state.details = f"Generated {i+1}/{SUBSETS_PER_TIER} subsets for {tier_name}"
                    save_checkpoint(checkpoint_state, OUTPUT_DIR / "subsets_checkpoint.json")
                    
            except Exception as e:
                print(f"Error generating subset {i} for {tier_name}: {e}")
                # In a real pipeline, we might want to retry or log and continue
                # For now, we raise to fail loudly
                raise

        all_subsets[tier_name] = subsets_for_tier
        processed_tiers += 1

        # Save intermediate results for this tier
        output_file = OUTPUT_DIR / f"subsets_{tier_name}.json"
        with open(output_file, 'w') as f:
            json.dump(subsets_for_tier, f)
        print(f"Saved {len(subsets_for_tier)} subsets to {output_file}")

    # Final checkpoint
    checkpoint_state.status = "completed"
    checkpoint_state.progress = 100
    checkpoint_state.details = "All subsets generated successfully"
    save_checkpoint(checkpoint_state, OUTPUT_DIR / "subsets_checkpoint.json")

    # Save aggregate summary
    summary = {
        "dataset": DATASET_NAME,
        "total_observations": n_observations,
        "subsets_per_tier": SUBSETS_PER_TIER,
        "tiers": tiers,
        "output_files": [f"subsets_{t}.json" for t in all_subsets.keys()]
    }
    summary_file = OUTPUT_DIR / "subsets_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_file}")

    print("Task T047 completed successfully.")

if __name__ == "__main__":
    main()
