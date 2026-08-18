"""
Puzzle Generator Module for llmXive.

Generates logic and arithmetic puzzles with deterministic complexity scaling.
Implements strict "Fail Loudly" semantics: any failure in generation raises
an exception immediately. No synthetic fallbacks are permitted.
"""

import json
import random
import hashlib
import time
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, asdict

# Import custom exceptions from the project's exceptions module
from code.exceptions import BaseResearchException, PARSE_FAILURE

class DataGenerationError(BaseResearchException):
    """
    Raised when puzzle generation fails due to internal logic errors,
    constraint violations, or inability to construct a valid instance.
    This exception halts execution immediately; no fallback is attempted.
    """
    pass

class PuzzleType(Enum):
    """Supported puzzle types for generation."""
    SUDOKU = "sudoku"
    PATHFINDING = "pathfinding"

@dataclass
class PuzzleInstance:
    """
    Represents a single puzzle instance with its constraints, initial state,
    and target state.
    """
    puzzle_id: str
    puzzle_type: str
    complexity_n: int
    constraints: Dict[str, Any]
    initial_state: Dict[str, Any]
    target_state: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary for JSON serialization."""
        return {
            "puzzle_id": self.puzzle_id,
            "puzzle_type": self.puzzle_type,
            "complexity_n": self.complexity_n,
            "constraints": self.constraints,
            "initial_state": self.initial_state,
            "target_state": self.target_state,
            "metadata": self.metadata
        }

class PuzzleGenerator:
    """
    Generates puzzle instances for the llmXive dataset.
    Implements strict fail-loudly logic: if a puzzle cannot be generated
    within reasonable attempts or constraints are violated, an exception
    is raised immediately.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator with an optional random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    def _generate_puzzle_id(self, puzzle_type: str, complexity_n: int, index: int) -> str:
        """Generate a unique ID for a puzzle instance."""
        timestamp = int(time.time() * 1000000)
        unique_str = f"{puzzle_type}_{complexity_n}_{index}_{timestamp}_{random.randint(0, 999999)}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def generate_sudoku(self, n: int, max_attempts: int = 100) -> PuzzleInstance:
        """
        Generate a Sudoku variant puzzle.
        n defines the grid size (n x n). For standard Sudoku, n should be a square number (e.g., 9).
        For this implementation, we support n=4 (2x2 blocks) and n=9 (3x3 blocks).
        
        Strict Fail-Loudly: If a valid Sudoku cannot be generated within max_attempts,
        raises DataGenerationError. No synthetic fallback.
        """
        if n not in [4, 9]:
            raise DataGenerationError(f"Unsupported Sudoku size: {n}. Only 4 and 9 are supported.")

        grid_size = n
        block_size = int(n ** 0.5)
        
        # Initialize empty grid
        grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Helper to check if placing a number is valid
        def is_valid(row: int, col: int, num: int) -> bool:
            # Check row
            if num in grid[row]:
                return False
            # Check column
            if any(grid[r][col] == num for r in range(grid_size)):
                return False
            # Check block
            start_row, start_col = (row // block_size) * block_size, (col // block_size) * block_size
            for r in range(start_row, start_row + block_size):
                for c in range(start_col, start_col + block_size):
                    if grid[r][c] == num:
                        return False
            return True

        # Helper to fill the grid using backtracking
        def fill_grid(r: int = 0, c: int = 0) -> bool:
            if r == grid_size:
                return True
            next_r, next_c = (r, c + 1) if c + 1 < grid_size else (r + 1, 0)
            
            # Find numbers to try
            numbers = list(range(1, grid_size + 1))
            random.shuffle(numbers)
            
            for num in numbers:
                if is_valid(r, c, num):
                    grid[r][c] = num
                    if fill_grid(next_r, next_c):
                        return True
                    grid[r][c] = 0
            return False

        # Attempt to generate a full grid
        for attempt in range(max_attempts):
            # Reset grid
            grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
            if fill_grid():
                break
        else:
            # Failed to generate a valid grid after max_attempts
            raise DataGenerationError(f"Failed to generate valid Sudoku grid of size {n} after {max_attempts} attempts.")

        # Create initial state by removing some numbers
        # Number of clues to keep is roughly 1/3 to 1/2 of the grid
        num_clues = (grid_size * grid_size) // 3
        clues_positions = set()
        while len(clues_positions) < num_clues:
            r, c = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)
            clues_positions.add((r, c))

        initial_grid = [row[:] for row in grid]
        for r in range(grid_size):
            for c in range(grid_size):
                if (r, c) not in clues_positions:
                    initial_grid[r][c] = 0

        puzzle_id = self._generate_puzzle_id("sudoku", n, attempt)
        
        instance = PuzzleInstance(
            puzzle_id=puzzle_id,
            puzzle_type="sudoku",
            complexity_n=n,
            constraints={
                "grid_size": grid_size,
                "block_size": block_size,
                "rule": "Each row, column, and block must contain unique numbers from 1 to grid_size"
            },
            initial_state={"grid": initial_grid},
            target_state={"grid": grid},
            metadata={
                "generation_time_ms": 0,
                "seed": self.seed,
                "attempts": attempt + 1
            }
        )
        return instance

    def generate_pathfinding(self, n: int, max_attempts: int = 100) -> PuzzleInstance:
        """
        Generate a constrained pathfinding puzzle on an n x n grid.
        The puzzle involves finding a path from a start node to a target node
        avoiding obstacles, with additional constraints (e.g., must pass through checkpoints).
        
        Strict Fail-Loudly: If a valid path cannot be found or constraints cannot be satisfied,
        raises DataGenerationError.
        """
        if n < 3:
            raise DataGenerationError(f"Pathfinding grid size {n} is too small. Minimum is 3.")

        grid_size = n
        
        # Generate a random grid with obstacles
        # Obstacle density: ~20%
        obstacle_density = 0.2
        grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        
        for r in range(grid_size):
            for c in range(grid_size):
                if random.random() < obstacle_density:
                    grid[r][c] = 1  # Obstacle

        # Ensure start (0,0) and end (n-1, n-1) are not obstacles
        grid[0][0] = 0
        grid[grid_size-1][grid_size-1] = 0

        # Generate checkpoints
        num_checkpoints = max(1, n // 4)
        checkpoints = []
        while len(checkpoints) < num_checkpoints:
            cp_r, cp_c = random.randint(1, grid_size-2), random.randint(1, grid_size-2)
            if grid[cp_r][cp_c] == 0:
                checkpoints.append((cp_r, cp_c))

        # Simple BFS to check connectivity and find a path
        from collections import deque
        def bfs_find_path(start, end, obstacles):
            queue = deque([(start, [start])])
            visited = {start}
            while queue:
                (r, c), path = queue.popleft()
                if (r, c) == end:
                    return path
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < grid_size and 0 <= nc < grid_size and grid[nr][nc] == 0 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append(((nr, nc), path + [(nr, nc)]))
            return None

        # Attempt to generate a solvable puzzle
        for attempt in range(max_attempts):
            # Reset grid
            grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
            for r in range(grid_size):
                for c in range(grid_size):
                    if random.random() < obstacle_density:
                        grid[r][c] = 1
            grid[0][0] = 0
            grid[grid_size-1][grid_size-1] = 0

            # Re-generate checkpoints
            checkpoints = []
            while len(checkpoints) < num_checkpoints:
                cp_r, cp_c = random.randint(1, grid_size-2), random.randint(1, grid_size-2)
                if grid[cp_r][cp_c] == 0:
                    checkpoints.append((cp_r, cp_c))

            # Check if path exists from start to end
            path = bfs_find_path((0, 0), (grid_size-1, grid_size-1), set())
            if path is None:
                continue

            # Check if path visits all checkpoints (or generate a path that does)
            # For simplicity, we just check if a path exists that visits checkpoints in order
            # If not, we regenerate. This is a simplified approach.
            current_pos = (0, 0)
            full_path = [current_pos]
            valid_path = True
            for cp in checkpoints:
                sub_path = bfs_find_path(current_pos, cp, set())
                if sub_path is None:
                    valid_path = False
                    break
                full_path.extend(sub_path[1:])
                current_pos = cp
            
            # Finally, path from last checkpoint to end
            final_path = bfs_find_path(current_pos, (grid_size-1, grid_size-1), set())
            if final_path is None:
                valid_path = False
            else:
                full_path.extend(final_path[1:])

            if valid_path:
                break
        else:
            raise DataGenerationError(f"Failed to generate solvable pathfinding puzzle of size {n} after {max_attempts} attempts.")

        puzzle_id = self._generate_puzzle_id("pathfinding", n, attempt)

        instance = PuzzleInstance(
            puzzle_id=puzzle_id,
            puzzle_type="pathfinding",
            complexity_n=n,
            constraints={
                "grid_size": grid_size,
                "obstacle_density": obstacle_density,
                "rule": "Find a path from (0,0) to (n-1,n-1) avoiding obstacles and visiting all checkpoints",
                "checkpoints": checkpoints
            },
            initial_state={
                "grid": grid,
                "start": [0, 0],
                "end": [grid_size-1, grid_size-1]
            },
            target_state={
                "path": full_path
            },
            metadata={
                "generation_time_ms": 0,
                "seed": self.seed,
                "attempts": attempt + 1
            }
        )
        return instance

    def generate_puzzle(self, puzzle_type: PuzzleType, n: int) -> PuzzleInstance:
        """
        Generate a puzzle of the specified type and complexity.
        
        Args:
            puzzle_type: The type of puzzle to generate.
            n: The complexity parameter (e.g., grid size).
        
        Returns:
            A valid PuzzleInstance.
        
        Raises:
            DataGenerationError: If generation fails.
        """
        if puzzle_type == PuzzleType.SUDOKU:
            return self.generate_sudoku(n)
        elif puzzle_type == PuzzleType.PATHFINDING:
            return self.generate_pathfinding(n)
        else:
            raise DataGenerationError(f"Unsupported puzzle type: {puzzle_type}")

def main():
    """
    Command-line entry point for generating puzzles.
    
    Usage:
        python -m code.dataset.generator --n 10 50 100 --count 5 --types sudoku,pathfinding
    
    This script generates puzzles and writes them to data/raw/.
    It implements strict fail-loudly logic: any generation failure raises an exception.
    """
    import argparse
    import os
    from code.utils.logger import setup_logging
    from code.utils.seed import set_seed

    parser = argparse.ArgumentParser(description="Generate logic puzzles for llmXive.")
    parser.add_argument("--n", type=int, nargs="+", required=True, help="Complexity levels (e.g., 10 50 100)")
    parser.add_argument("--count", type=int, required=True, help="Number of puzzles per complexity level")
    parser.add_argument("--types", type=str, nargs="+", default=["sudoku"], help="Puzzle types (sudoku, pathfinding)")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--max-attempts", type=int, default=100, help="Max generation attempts before failing")

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Set seed
    if args.seed is not None:
        set_seed(args.seed)
        logger.info(f"Random seed set to {args.seed}")

    # Prepare output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Map string types to enum
    type_map = {
        "sudoku": PuzzleType.SUDOKU,
        "pathfinding": PuzzleType.PATHFINDING
    }
    selected_types = []
    for t in args.types:
        if t not in type_map:
            raise ValueError(f"Invalid puzzle type: {t}. Supported: {list(type_map.keys())}")
        selected_types.append(type_map[t])

    generator = PuzzleGenerator(seed=args.seed)

    total_generated = 0
    start_time = time.time()

    for n in args.n:
        for p_type in selected_types:
            for i in range(args.count):
                try:
                    instance = generator.generate_puzzle(p_type, n)
                    # Write to file
                    filename = f"{p_type.value}_n{n}_{i}.json"
                    filepath = output_dir / filename
                    with open(filepath, 'w') as f:
                        json.dump(instance.to_dict(), f, indent=2)
                    total_generated += 1
                    logger.info(f"Generated {filename}")
                except DataGenerationError as e:
                    # Fail loudly: do not catch, let it propagate
                    logger.error(f"CRITICAL: Generation failed for {p_type.value} n={n} count={i}: {e}")
                    raise  # Re-raise to halt execution
                except Exception as e:
                    logger.error(f"CRITICAL: Unexpected error during generation: {e}")
                    raise

    elapsed = time.time() - start_time
    logger.info(f"Successfully generated {total_generated} puzzles in {elapsed:.2f}s")

if __name__ == "__main__":
    main()
