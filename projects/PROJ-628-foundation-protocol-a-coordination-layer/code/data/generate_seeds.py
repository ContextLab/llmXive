"""
Generate deterministic seed configurations for Hanabi and Resource Allocation tasks.

This script produces a JSON file containing multiple random seeds used to initialize
the simulation environments. The seeds are derived from a master seed to ensure
reproducibility while providing variation across runs.

Output:
    data/seed_configurations.json: A JSON file containing a list of seed configurations.
"""

import json
import os
import random
from pathlib import Path

# Ensure imports from project structure
# We use the utils module for logging if needed, but primarily rely on standard library
from foundation_protocol.utils import log_seed

# Configuration
MASTER_SEED = 42
NUM_SEEDS = 30
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "seed_configurations.json"

# Task-specific seed ranges (to ensure different seeds for different tasks if needed)
# In this implementation, we generate a pool of seeds and assign them to tasks.
TASKS = ["hanabi", "resource_allocation"]


def generate_seed_pool(master_seed: int, count: int) -> list[int]:
    """
    Generate a list of deterministic seeds based on a master seed.

    Args:
        master_seed: The initial seed for the random number generator.
        count: The number of seeds to generate.

    Returns:
        A list of unique integer seeds.
    """
    rng = random.Random(master_seed)
    seeds = set()
    while len(seeds) < count:
        # Generate a seed in a reasonable range (e.g., 0 to 2^31 - 1)
        seed = rng.randint(0, 2**31 - 1)
        seeds.add(seed)
    return sorted(list(seeds))


def create_seed_configurations(seeds: list[int], tasks: list[str]) -> list[dict]:
    """
    Create a list of seed configuration dictionaries.

    Each configuration includes the seed, the task it is intended for, and
    a derived run ID.

    Args:
        seeds: List of integer seeds.
        tasks: List of task names.

    Returns:
        A list of dictionaries representing seed configurations.
    """
    configurations = []
    # Distribute seeds across tasks. For this task, we generate 30 seeds total.
    # We will assign the first 15 to Hanabi and the next 15 to Resource Allocation,
    # or simply list all seeds for all tasks if the runner handles it.
    # The spec says "deterministic seed configurations for Hanabi and Resource Allocation".
    # A common pattern is a list of seeds, and the runner picks based on task.
    # We will generate a structure that explicitly lists seeds for each task
    # to be unambiguous.

    # Let's generate 15 seeds for Hanabi and 15 for Resource Allocation
    # to ensure we have enough for the "30 seeds" mentioned in T018 context,
    # or simply 30 seeds that can be applied to any task.
    # Given T018 mentions "30 seeds x 2 protocols", we likely need 30 distinct seeds.
    # We will create a configuration that lists 30 seeds, and indicates they are valid for both.
    
    # However, to be specific as per task description:
    # "generate deterministic seed configurations for Hanabi and Resource Allocation tasks"
    # We will create a JSON structure:
    # {
    #   "master_seed": 42,
    #   "num_seeds": 30,
    #   "seeds": [
    #     {"seed": 123, "task": "hanabi"},
    #     {"seed": 456, "task": "hanabi"},
    #     ...
    #     {"seed": 789, "task": "resource_allocation"},
    #     ...
    #   ]
    # }
    
    # Let's assign the first 15 seeds to Hanabi and the next 15 to Resource Allocation.
    hanabi_seeds = seeds[:15]
    resource_seeds = seeds[15:30]

    for i, s in enumerate(hanabi_seeds):
        configurations.append({
            "run_id": f"hanabi_{i:03d}",
            "seed": s,
            "task": "hanabi"
        })

    for i, s in enumerate(resource_seeds):
        configurations.append({
            "run_id": f"resource_{i:03d}",
            "seed": s,
            "task": "resource_allocation"
        })

    return configurations


def main():
    """Main entry point for seed generation."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Log the master seed for reproducibility tracking
    log_seed(MASTER_SEED)

    # Generate the pool of seeds
    seeds = generate_seed_pool(MASTER_SEED, NUM_SEEDS)

    # Create configurations
    configurations = create_seed_configurations(seeds, TASKS)

    # Prepare the output data
    output_data = {
        "master_seed": MASTER_SEED,
        "total_seeds": len(seeds),
        "tasks": TASKS,
        "configurations": configurations
    }

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Generated {len(configurations)} seed configurations.")
    print(f"Output written to: {OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()