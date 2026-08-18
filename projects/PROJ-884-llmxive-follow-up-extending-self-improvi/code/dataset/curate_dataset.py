import json
import hashlib
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.dataset.generator import PuzzleGenerator, PuzzleInstance
from code.dataset.verifier import PuzzleVerifier, SolutionResult
from code.utils.seed import set_seed

def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_puzzles(
    output_dir: Path,
    count: int = 100,
    min_size: int = 10,
    max_size: int = 50,
    seed: int = 42,
    complexity_levels: List[int] = None
) -> List[Path]:
    """
    Generate a dataset of logic puzzles using the generator and verifier.
    
    This function:
    1. Initializes the PuzzleGenerator with a deterministic seed.
    2. Generates puzzle instances of varying complexity.
    3. Validates each instance using the PuzzleVerifier.
    4. Writes valid puzzles to JSON files in the output directory.
    5. Computes and records checksums for data integrity.
    
    Args:
        output_dir: Directory to write puzzle files.
        count: Number of puzzles to generate.
        min_size: Minimum puzzle size parameter.
        max_size: Maximum puzzle size parameter.
        seed: Random seed for reproducibility.
        complexity_levels: Optional list of specific complexity levels to use.
        
    Returns:
        List of paths to generated puzzle files.
    """
    set_seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = PuzzleGenerator(seed=seed)
    verifier = PuzzleVerifier()
    
    generated_files = []
    valid_count = 0
    invalid_count = 0
    start_time = time.time()
    
    print(f"Starting puzzle generation: {count} puzzles, size range [{min_size}, {max_size}]")
    
    while valid_count < count:
        # Determine complexity for this puzzle
        if complexity_levels:
            complexity = complexity_levels[valid_count % len(complexity_levels)]
        else:
            complexity = random.randint(min_size, max_size)
        
        try:
            # Generate a puzzle instance
            puzzle: PuzzleInstance = generator.generate_puzzle(complexity)
            
            if puzzle is None:
                invalid_count += 1
                continue
            
            # Validate the puzzle using the verifier
            # The verifier checks that the puzzle is well-formed and solvable
            # We pass the puzzle's initial state and constraints
            verification_result: SolutionResult = verifier.validate_puzzle_structure(puzzle)
            
            if verification_result.is_valid:
                # Prepare the puzzle data for JSON serialization
                puzzle_data = {
                    "id": puzzle.id,
                    "type": puzzle.type.value,
                    "size": puzzle.size,
                    "complexity": puzzle.complexity,
                    "initial_state": puzzle.initial_state,
                    "constraints": puzzle.constraints,
                    "target_state": puzzle.target_state,
                    "generated_at": datetime.now().isoformat(),
                    "seed": seed
                }
                
                # Write to file
                filename = f"puzzle_{valid_count:04d}_n{complexity}.json"
                file_path = output_dir / filename
                
                with open(file_path, "w") as f:
                    json.dump(puzzle_data, f, indent=2)
                
                # Compute and store checksum
                checksum = compute_checksum(file_path)
                puzzle_data["checksum"] = checksum
                
                # Rewrite with checksum included
                with open(file_path, "w") as f:
                    json.dump(puzzle_data, f, indent=2)
                
                generated_files.append(file_path)
                valid_count += 1
                
                if valid_count % 10 == 0:
                    print(f"Generated {valid_count} valid puzzles (invalid: {invalid_count})")
            else:
                invalid_count += 1
                # Log validation error for debugging
                if valid_count < 5:  # Log first few failures
                    print(f"Validation failed for complexity {complexity}: {verification_result.error_code}")
                    
        except Exception as e:
            invalid_count += 1
            if valid_count < 5:
                print(f"Generation error for complexity {complexity}: {str(e)}")
            continue
    
    elapsed_time = time.time() - start_time
    print(f"Completed generation in {elapsed_time:.2f}s")
    print(f"Valid puzzles: {valid_count}, Invalid/Failed: {invalid_count}")
    
    # Write a manifest file
    manifest_path = output_dir / "manifest.json"
    manifest_data = {
        "total_puzzles": valid_count,
        "generation_seed": seed,
        "min_size": min_size,
        "max_size": max_size,
        "generated_at": datetime.now().isoformat(),
        "elapsed_seconds": elapsed_time,
        "files": [str(f.relative_to(output_dir)) for f in generated_files]
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    return generated_files

def main():
    """Main entry point for dataset curation."""
    # Define output directory based on project structure
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    
    # Configuration
    NUM_PUZZLES = 100
    MIN_SIZE = 10
    MAX_SIZE = 50
    SEED = 42
    
    # Generate puzzles
    files = generate_puzzles(
        output_dir=output_dir,
        count=NUM_PUZZLES,
        min_size=MIN_SIZE,
        max_size=MAX_SIZE,
        seed=SEED
    )
    
    print(f"Dataset curation complete. Generated {len(files)} puzzles in {output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
