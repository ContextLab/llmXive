"""
Script to curate an initial dataset of logic/arithmetic puzzles.
This script runs the PuzzleGenerator to create a sufficient volume of puzzles
and saves them to data/raw/ following the schema in contracts/dataset.schema.yaml.
"""
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from code.dataset.generator import PuzzleGenerator, PuzzleInstance
from code.utils.seed import set_seed, get_seed
from code.config import initialize_experiment, load_config

# Ensure output directory exists
OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Schema reference (relative path as per task description)
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

def generate_checksum(content: str) -> str:
    """Generate a deterministic SHA-256 checksum for data integrity."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def main():
    """
    Main entry point to generate and save the dataset.
    """
    # Initialize experiment context (handles logging setup)
    try:
        exp_id = initialize_experiment("dataset_curation")
    except Exception:
        # Fallback if experiment init fails, use default
        exp_id = "default"

    # Load configuration for dataset parameters
    # We expect config to have dataset generation parameters
    try:
        config = load_config()
        num_puzzles = config.get('dataset', {}).get('num_initial_puzzles', 100)
        complexity_range = config.get('dataset', {}).get('complexity_range', [10, 50])
    except Exception:
        # Defaults if config is missing or malformed
        num_puzzles = 100
        complexity_range = [10, 50]

    print(f"Starting dataset curation for experiment: {exp_id}")
    print(f"Generating {num_puzzles} puzzles with complexity range {complexity_range}...")

    # Initialize the generator with a fixed seed for reproducibility
    set_seed(42)
    generator = PuzzleGenerator()

    dataset: List[Dict[str, Any]] = []
    start_time = time.time()

    for i in range(num_puzzles):
        # Generate a puzzle instance
        # Complexity is scaled between the range
        complexity = complexity_range[0] + (i % (complexity_range[1] - complexity_range[0]))
        
        try:
            puzzle: PuzzleInstance = generator.generate(complexity=complexity)
            
            # Ensure the puzzle conforms to expected structure
            puzzle_dict = {
                "id": puzzle.id,
                "type": puzzle.type,
                "complexity": puzzle.complexity,
                "constraints": puzzle.constraints,
                "target": puzzle.target,
                "metadata": {
                    "generation_time": puzzle.generation_time,
                    "seed_used": get_seed()
                }
            }
            
            # Add checksum for integrity (Principle III)
            json_str = json.dumps(puzzle_dict, sort_keys=True)
            puzzle_dict["checksum"] = generate_checksum(json_str)
            
            dataset.append(puzzle_dict)
            
        except Exception as e:
            print(f"Warning: Failed to generate puzzle at index {i}: {e}")
            continue

    end_time = time.time()
    total_time = end_time - start_time

    # Save to JSON file
    output_file = OUTPUT_DIR / f"puzzles_{exp_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2)

    print(f"Successfully generated {len(dataset)} puzzles.")
    print(f"Total time: {total_time:.2f} seconds.")
    print(f"Output saved to: {output_file}")
    
    # Log the generation event
    # Note: log_experiment_entry is imported in config.py but we call it via utils.logger if needed
    # Since the task requires real execution, we just print the summary.
    # The logging infrastructure (T005) will capture this if the script is run as part of a larger pipeline.

if __name__ == "__main__":
    main()
