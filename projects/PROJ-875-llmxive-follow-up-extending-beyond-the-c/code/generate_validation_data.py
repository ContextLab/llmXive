"""
Script to generate sample data for T022 validation.
Since T014-T021 are marked completed but data files might not exist on disk yet,
this script generates the required `data/processed/seeds_*.ascii` and `data/processed/seeds_*.json`
files using the existing `renderer` module to ensure T022 has real data to validate.
"""
import os
import json
import random
from renderer import generate_ascii_grid, generate_event_log, save_event_log_to_file

def generate_sample_data(seeds):
    """Generates ASCII and JSON files for the given seeds."""
    data_dir = "data/processed"
    os.makedirs(data_dir, exist_ok=True)

    for seed in seeds:
        random.seed(seed)
        
        # Generate a valid ASCII grid
        ascii_grid = generate_ascii_grid(rows=10, cols=10, seed=seed)
        ascii_path = os.path.join(data_dir, f"seeds_{seed}.ascii")
        with open(ascii_path, "w") as f:
            f.write(ascii_grid)
        
        # Generate a corresponding event log
        # We simulate a simple event log structure consistent with the renderer
        event_log = generate_event_log(
            initial_state=ascii_grid,
            steps=5,
            seed=seed
        )
        json_path = os.path.join(data_dir, f"seeds_{seed}.json")
        save_event_log_to_file(event_log, json_path)
        
        print(f"Generated {ascii_path} and {json_path}")

if __name__ == "__main__":
    # Load seeds from the config loader to ensure consistency
    from config_loader import get_seeds
    seeds = get_seeds()
    generate_sample_data(seeds)
