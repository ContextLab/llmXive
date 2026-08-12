"""
Dataset Curation Script for T013.

This script curates an initial dataset of logic/arithmetic puzzles
by running the PuzzleGenerator and saving the output to data/raw/
in JSON format compliant with the schema in contracts/dataset.schema.yaml.
"""
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Import from project API surface
from code.dataset.generator import PuzzleGenerator, PuzzleInstance
from code.utils.seed import set_seed, get_seed
from code.config import load_config, initialize_experiment

def generate_checksum(data: Dict[str, Any]) -> str:
    """Generate a SHA-256 checksum for a puzzle instance."""
    # Canonicalize by sorting keys and removing dynamic fields
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def main():
    """
    Main entry point for dataset generation.
    Reads config, generates puzzles, validates against schema, and saves.
    """
    # Load configuration
    config = load_config()
    seed = config.get('seed', 42)
    num_puzzles = config.get('dataset_size', 100)
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize experiment and seed
    initialize_experiment(config)
    set_seed(seed)

    print(f"Generating {num_puzzles} puzzles with seed {seed}...")

    generator = PuzzleGenerator(seed=seed)
    puzzles: List[PuzzleInstance] = []

    # Generate puzzles with varying difficulty
    for i in range(num_puzzles):
        # Cycle through difficulties 1-5
        difficulty = (i % 5) + 1
        
        # Generate a puzzle instance
        puzzle = generator.generate(difficulty=difficulty)
        
        # Ensure checksum is computed
        if not puzzle.checksum:
            puzzle.checksum = generate_checksum(puzzle.to_dict())
        
        puzzles.append(puzzle)
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_puzzles} puzzles...")

    # Construct the dataset document
    dataset_doc = {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "metadata": {
            "generator_version": "1.0.0",
            "seed": seed,
            "total_count": len(puzzles),
            "difficulty_distribution": {
                str(d): sum(1 for p in puzzles if p.difficulty == d) 
                for d in range(1, 6)
            }
        },
        "puzzles": [p.to_dict() for p in puzzles]
    }

    # Validate basic structure (schema validation would require jsonschema lib)
    assert "puzzles" in dataset_doc
    assert len(dataset_doc["puzzles"]) == num_puzzles
    for p in dataset_doc["puzzles"]:
        assert "id" in p
        assert "checksum" in p
        assert len(p["checksum"]) == 64

    # Write to file
    output_file = output_dir / "puzzles_v1.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset_doc, f, indent=2)

    print(f"Successfully wrote {num_puzzles} puzzles to {output_file}")
    print(f"Checksum validation ready. Run 'python code/dataset/validate_checksums.py' to verify.")

if __name__ == "__main__":
    main()
