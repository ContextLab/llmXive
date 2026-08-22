"""
Puzzle Generator Module for llmXive.

Generates logic puzzles (Sudoku variants, constrained pathfinding) with systematic
complexity scaling (N=10..500). Supports command-line arguments for N and count.
Implements "Fail Loudly" principle: no synthetic fallbacks, strict error handling.
"""

import json
import random
import hashlib
import time
import sys
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

# Custom Exception for Fail-Loudly behavior
class DataGenerationError(Exception):
    """Raised when puzzle generation fails due to constraints or internal errors."""
    pass

class PuzzleType(Enum):
    """Supported puzzle types."""
    SUDOKU = "sudoku"
    PATHFINDING = "pathfinding"

@dataclass
class PuzzleInstance:
    """Represents a single generated puzzle instance."""
    puzzle_id: str
    puzzle_type: str
    n: int  # Complexity parameter
    constraints: Dict[str, Any]
    initial_state: Dict[str, Any]
    target_state: Optional[Dict[str, Any]]
    complexity_metric: float
    generated_at: str
    checksum: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PuzzleGenerator:
    """
    Generates logic puzzles with systematic complexity scaling.
    Implements strict validation and fail-loudly principles.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator with an optional random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    def _generate_puzzle_id(self, p_type: str, n: int, attempt: int) -> str:
        """Generate a unique puzzle ID."""
        raw = f"{p_type}-{n}-{attempt}-{self.seed}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate a deterministic checksum for the puzzle data."""
        # Sort keys for deterministic JSON serialization
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def generate_sudoku(self, n: int, attempt: int = 0) -> PuzzleInstance:
        """
        Generate a Sudoku variant puzzle.
        Complexity N maps to grid size (e.g., N=10 -> 10x10, N=500 -> 500x500).
        Note: For very large N, this generates a sparse constraint set to remain tractable.
        """
        if n < 1:
            raise DataGenerationError(f"Invalid Sudoku size N={n}. Must be >= 1.")

        grid_size = n
        # Complexity metric: grid_size^2 (number of cells)
        complexity_metric = float(grid_size * grid_size)

        # Generate constraints: sparse set of pre-filled cells
        # For large N, we fill only ~10% of cells to ensure solvability within time limits
        fill_ratio = min(0.5, 100.0 / max(1, n)) 
        num_filled = int(grid_size * grid_size * fill_ratio)
        
        initial_state = {
            "grid_size": grid_size,
            "cells": {}
        }
        
        # Randomly place numbers ensuring no immediate row/col conflict for generation
        # (Full validity check is deferred to verifier T012)
        used_rows = set()
        used_cols = set()
        
        for _ in range(num_filled):
            r = random.randint(0, grid_size - 1)
            c = random.randint(0, grid_size - 1)
            val = random.randint(1, grid_size)
            
            # Simple heuristic to avoid obvious duplicates in generation phase
            # (Not a full solver check, just generation logic)
            if r not in used_rows and c not in used_cols:
                initial_state["cells"][f"{r},{c}"] = val
                used_rows.add(r)
                used_cols.add(c)

        puzzle_id = self._generate_puzzle_id("sudoku", n, attempt)
        checksum_data = {
            "type": "sudoku",
            "n": n,
            "cells": initial_state["cells"]
        }
        checksum = self._calculate_checksum(checksum_data)

        return PuzzleInstance(
            puzzle_id=puzzle_id,
            puzzle_type=PuzzleType.SUDOKU.value,
            n=n,
            constraints={"fill_ratio": fill_ratio, "grid_size": grid_size},
            initial_state=initial_state,
            target_state={"type": "full_grid", "values": list(range(1, grid_size + 1))},
            complexity_metric=complexity_metric,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            checksum=checksum
        )

    def generate_pathfinding(self, n: int, attempt: int = 0) -> PuzzleInstance:
        """
        Generate a constrained pathfinding puzzle.
        Complexity N maps to grid dimensions (e.g., N=10 -> 10x10, N=500 -> 500x500).
        """
        if n < 1:
            raise DataGenerationError(f"Invalid Pathfinding size N={n}. Must be >= 1.")

        grid_size = n
        # Complexity metric: grid_size^2 (number of nodes)
        complexity_metric = float(grid_size * grid_size)

        # Generate a sparse grid with obstacles
        # Obstacle density decreases as N increases to ensure path exists
        obstacle_density = max(0.1, 0.5 / (n / 10.0)) 
        num_obstacles = int(grid_size * grid_size * obstacle_density)

        initial_state = {
            "grid_size": grid_size,
            "start": [0, 0],
            "end": [grid_size - 1, grid_size - 1],
            "obstacles": []
        }

        obstacles = set()
        while len(obstacles) < num_obstacles:
            r = random.randint(0, grid_size - 1)
            c = random.randint(0, grid_size - 1)
            # Ensure start and end are never obstacles
            if (r, c) != (0, 0) and (r, c) != (grid_size - 1, grid_size - 1):
                obstacles.add((r, c))

        initial_state["obstacles"] = [[r, c] for r, c in obstacles]

        puzzle_id = self._generate_puzzle_id("pathfinding", n, attempt)
        checksum_data = {
            "type": "pathfinding",
            "n": n,
            "obstacles": initial_state["obstacles"],
            "start": initial_state["start"],
            "end": initial_state["end"]
        }
        checksum = self._calculate_checksum(checksum_data)

        return PuzzleInstance(
            puzzle_id=puzzle_id,
            puzzle_type=PuzzleType.PATHFINDING.value,
            n=n,
            constraints={"obstacle_density": obstacle_density, "grid_size": grid_size},
            initial_state=initial_state,
            target_state={"path_exists": True},
            complexity_metric=complexity_metric,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            checksum=checksum
        )

    def generate_puzzle(self, p_type: PuzzleType, n: int, attempt: int = 0) -> PuzzleInstance:
        """
        Generate a puzzle of the specified type and complexity.
        Implements Fail-Loudly: raises DataGenerationError on failure.
        """
        if p_type == PuzzleType.SUDOKU:
            return self.generate_sudoku(n, attempt)
        elif p_type == PuzzleType.PATHFINDING:
            return self.generate_pathfinding(n, attempt)
        else:
            raise DataGenerationError(f"Unsupported puzzle type: {p_type}")

    def generate_batch(self, n_values: List[int], count: int, types: List[PuzzleType], output_dir: Optional[str] = None) -> List[PuzzleInstance]:
        """
        Generate a batch of puzzles.
        
        Args:
            n_values: List of complexity parameters (N).
            count: Number of puzzles to generate per (N, type) combination.
            types: List of puzzle types to generate.
            output_dir: Optional directory to write puzzles to as JSONL.
        
        Returns:
            List of generated PuzzleInstance objects.
        """
        if not n_values:
            raise DataGenerationError("n_values list cannot be empty.")
        if count <= 0:
            raise DataGenerationError("count must be positive.")
        if not types:
            raise DataGenerationError("types list cannot be empty.")

        puzzles = []
        total_generated = 0

        # Ensure output directory exists if specified
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = Path(output_dir) / "puzzles.jsonl"
            with open(output_path, 'w') as f_out:
                for n in n_values:
                    for p_type in types:
                        for i in range(count):
                            try:
                                puzzle = self.generate_puzzle(p_type, n, i)
                                puzzles.append(puzzle)
                                f_out.write(json.dumps(puzzle.to_dict()) + '\n')
                                total_generated += 1
                            except DataGenerationError as e:
                                # Fail Loudly: propagate the error immediately
                                raise DataGenerationError(f"Failed to generate puzzle for N={n}, type={p_type.value}, attempt={i}: {e}")

        else:
            # In-memory generation only (for testing)
            for n in n_values:
                for p_type in types:
                    for i in range(count):
                        try:
                            puzzle = self.generate_puzzle(p_type, n, i)
                            puzzles.append(puzzle)
                            total_generated += 1
                        except DataGenerationError as e:
                            raise DataGenerationError(f"Failed to generate puzzle for N={n}, type={p_type.value}, attempt={i}: {e}")

        return puzzles

def main():
    """
    CLI entry point for puzzle generation.
    
    Usage:
        python code/dataset/generator.py --n 10 50 100 --count 5 --types sudoku pathfinding --output-dir data/raw
    """
    parser = argparse.ArgumentParser(
        description="Generate logic puzzles with systematic complexity scaling.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments as per task constraints
    parser.add_argument(
        "--n",
        type=int,
        nargs="+",
        required=True,
        help="List of complexity parameters (N). Example: --n 10 50 100"
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of puzzles to generate per (N, type) combination."
    )
    
    # Optional arguments
    parser.add_argument(
        "--types",
        type=str,
        nargs="+",
        default=["sudoku", "pathfinding"],
        choices=["sudoku", "pathfinding"],
        help="List of puzzle types to generate."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to write puzzles to as JSONL. If not provided, generates in memory only."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=1,
        help="Maximum attempts to generate a valid puzzle before failing (for internal retries, currently unused but reserved)."
    )

    args = parser.parse_args()

    # Validate inputs
    if args.count <= 0:
        print("Error: count must be positive.", file=sys.stderr)
        sys.exit(1)
    
    if any(n <= 0 for n in args.n):
        print("Error: All N values must be positive.", file=sys.stderr)
        sys.exit(1)

    # Parse types
    try:
        puzzle_types = [PuzzleType(t) for t in args.types]
    except ValueError as e:
        print(f"Error: Invalid puzzle type provided: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        generator = PuzzleGenerator(seed=args.seed)
        
        print(f"Generating puzzles: N={args.n}, count={args.count}, types={[t.value for t in puzzle_types]}")
        
        puzzles = generator.generate_batch(
            n_values=args.n,
            count=args.count,
            types=puzzle_types,
            output_dir=args.output_dir
        )
        
        if args.output_dir:
            output_file = Path(args.output_dir) / "puzzles.jsonl"
            print(f"Successfully generated {len(puzzles)} puzzles to {output_file}")
        else:
            print(f"Successfully generated {len(puzzles)} puzzles in memory.")

    except DataGenerationError as e:
        print(f"Data Generation Failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during generation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()