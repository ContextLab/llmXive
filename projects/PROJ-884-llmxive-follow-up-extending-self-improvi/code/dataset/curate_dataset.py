"""
Task T013: Curate an initial dataset of logic/arithmetic puzzles.

This script generates a dataset of puzzles using the PuzzleGenerator
and saves it to data/raw/ in JSON format, adhering to the schema
defined in contracts/dataset.schema.yaml.
"""
import json
import hashlib
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import from local project structure
from code.dataset.generator import PuzzleGenerator, PuzzleType
from code.utils.seed import set_seed
from code.utils.logger import log

# Constants
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "puzzles_dataset.json"
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

# Configuration
TOTAL_PUZZLES = 100
SEED = 42
DENSITY = {
    "easy": 0.3,
    "medium": 0.4,
    "hard": 0.3
}

def compute_checksum(data: List[Dict[str, Any]]) -> str:
    """Compute SHA-256 checksum of the puzzles list."""
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()

def generate_puzzles(count: int, seed: int) -> List[Dict[str, Any]]:
    """Generate a list of puzzle instances."""
    set_seed(seed)
    generator = PuzzleGenerator()
    puzzles = []
    
    # Determine counts per difficulty
    easy_count = int(count * DENSITY["easy"])
    medium_count = int(count * DENSITY["medium"])
    hard_count = count - easy_count - medium_count
    
    difficulty_counts = {
        "easy": easy_count,
        "medium": medium_count,
        "hard": hard_count
    }
    
    for difficulty, num in difficulty_counts.items():
        for _ in range(num):
            start_time = time.time()
            try:
                # Generate a puzzle instance
                # We use a loop to ensure we get a valid puzzle if generation fails
                instance = None
                attempts = 0
                while instance is None and attempts < 5:
                    try:
                        instance = generator.generate(difficulty=difficulty)
                    except Exception as e:
                        log(f"Generation attempt failed: {e}", level="WARNING")
                        attempts += 1
                        instance = None
                
                if instance:
                    puzzle_dict = instance.to_dict()
                    generation_time = (time.time() - start_time) * 1000
                    puzzle_dict["metadata"]["generation_time_ms"] = generation_time
                    puzzles.append(puzzle_dict)
                    log(f"Generated puzzle {puzzle_dict['id']} ({difficulty})")
            except Exception as e:
                log(f"Failed to generate puzzle: {e}", level="ERROR")
                continue
    
    return puzzles

def main():
    """Main entry point for dataset curation."""
    log("Starting dataset curation (T013)...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate puzzles
    puzzles = generate_puzzles(TOTAL_PUZZLES, SEED)
    
    if not puzzles:
        log("ERROR: No puzzles were generated. Exiting.", level="CRITICAL")
        return 1
    
    # Compute checksum
    checksum = compute_checksum(puzzles)
    
    # Construct final dataset object
    dataset = {
        "metadata": {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generator_version": "1.0.0",
            "total_count": len(puzzles),
            "checksum": checksum
        },
        "puzzles": puzzles
    }
    
    # Write to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2)
        log(f"Dataset successfully written to {OUTPUT_FILE}")
        log(f"Total puzzles: {len(puzzles)}")
        log(f"Checksum: {checksum}")
        return 0
    except IOError as e:
        log(f"Failed to write dataset file: {e}", level="CRITICAL")
        return 1

if __name__ == "__main__":
    exit(main())
