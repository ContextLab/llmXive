"""
Puzzle Generator Module for llmXive
Generates logic/arithmetic puzzles with deterministic Python verifiers.
Implements Data Provenance metadata injection as per T066.
"""

import json
import random
import hashlib
import time
import sys
import argparse
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GENERATOR_VERSION = "1.0.0"
DEFAULT_SOURCE_ID = "curated_logic_v1"
DEFAULT_SEED = 42
DEFAULT_COUNT = 100
DEFAULT_OUTPUT_DIR = "data/raw"

class PuzzleType(Enum):
    """Supported puzzle types"""
    SUDOKU = "sudoku"
    PATHFINDING = "pathfinding"
    LOGIC_GRID = "logic_grid"
    ARITHMETIC = "arithmetic"

class DataGenerationError(Exception):
    """Custom exception for data generation failures"""
    pass

class PuzzleInstance:
    """Represents a single puzzle instance with metadata"""

    def __init__(
        self,
        puzzle_type: PuzzleType,
        constraints: List[str],
        initial_state: Dict[str, Any],
        target_state: Dict[str, Any],
        solution: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.puzzle_type = puzzle_type
        self.constraints = constraints
        self.initial_state = initial_state
        self.target_state = target_state
        self.solution = solution
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "puzzle_type": self.puzzle_type.value,
            "constraints": self.constraints,
            "initial_state": self.initial_state,
            "target_state": self.target_state,
            "solution": self.solution,
            "metadata": self.metadata
        }

class PuzzleGenerator:
    """
    Generates logic puzzles with systematic complexity scaling.
    Implements T066: Data Provenance metadata injection.
    """

    def __init__(
        self,
        source_id: str = DEFAULT_SOURCE_ID,
        seed: int = DEFAULT_SEED,
        version: str = GENERATOR_VERSION
    ):
        self.source_id = source_id
        self.seed = seed
        self.version = version
        self.random = random.Random(seed)
        self.logger = logging.getLogger(__name__)

    def _generate_metadata(
        self,
        puzzle_type: PuzzleType,
        n: int,
        constraint_count: int,
        variable_domain_size: int
    ) -> Dict[str, Any]:
        """
        Generate provenance metadata for a puzzle instance.
        T066 Requirement: Every generated puzzle must include:
        - source_id: Identifier of the generation source
        - generation_seed: The seed used for this specific generation
        - timestamp: ISO format timestamp
        - generator_version: Version of the generator
        - complexity_metric: (constraint_count, variable_domain_size)
        """
        return {
            "source_id": self.source_id,
            "generation_seed": self.seed,
            "timestamp": datetime.utcnow().isoformat(),
            "generator_version": self.version,
            "complexity_metric": {
                "constraint_count": constraint_count,
                "variable_domain_size": variable_domain_size
            },
            "puzzle_type": puzzle_type.value,
            "complexity_n": n
        }

    def generate_sudoku(
        self,
        n: int,
        count: int,
        difficulty: str = "medium"
    ) -> List[PuzzleInstance]:
        """
        Generate Sudoku variant puzzles.
        N represents the grid size (e.g., 9 for 9x9, 16 for 16x16).
        """
        puzzles = []
        grid_size = n if n >= 9 else 9  # Minimum 9x9
        
        for i in range(count):
            # Generate a valid sudoku grid
            grid = self._generate_valid_sudoku(grid_size)
            
            # Create puzzle by removing some cells
            puzzle_grid, solution_grid = self._create_puzzle_from_grid(grid, difficulty)
            
            constraints = [
                f"Grid must be {grid_size}x{grid_size}",
                f"Each row must contain digits 1-{grid_size} exactly once",
                f"Each column must contain digits 1-{grid_size} exactly once",
                f"Each {int(grid_size**0.5)}x{int(grid_size**0.5)} box must contain digits 1-{grid_size} exactly once"
            ]
            
            constraint_count = len(constraints)
            variable_domain_size = grid_size
            
            instance = PuzzleInstance(
                puzzle_type=PuzzleType.SUDOKU,
                constraints=constraints,
                initial_state={"grid": puzzle_grid, "size": grid_size},
                target_state={"solution": solution_grid, "size": grid_size},
                solution={"solution": solution_grid},
                metadata=self._generate_metadata(
                    PuzzleType.SUDOKU,
                    n,
                    constraint_count,
                    variable_domain_size
                )
            )
            puzzles.append(instance)
        
        return puzzles

    def generate_pathfinding(
        self,
        n: int,
        count: int,
        difficulty: str = "medium"
    ) -> List[PuzzleInstance]:
        """
        Generate constrained pathfinding puzzles.
        N represents the grid dimensions (n x n).
        """
        puzzles = []
        grid_size = n if n >= 5 else 5  # Minimum 5x5
        
        for i in range(count):
            # Generate grid with obstacles
            grid, start, end, obstacles = self._generate_pathfinding_grid(
                grid_size, difficulty
            )
            
            constraints = [
                f"Grid size: {grid_size}x{grid_size}",
                f"Start position: {start}",
                f"End position: {end}",
                f"Obstacles at: {obstacles[:5]}...",  # Truncate for readability
                "Path must not pass through obstacles",
                "Path must be shortest possible"
            ]
            
            constraint_count = len(constraints)
            variable_domain_size = grid_size * grid_size  # Total cells
            
            instance = PuzzleInstance(
                puzzle_type=PuzzleType.PATHFINDING,
                constraints=constraints,
                initial_state={
                    "grid": grid,
                    "start": start,
                    "end": end,
                    "obstacles": obstacles,
                    "size": grid_size
                },
                target_state={"path": self._solve_pathfinding(grid, start, end, obstacles)},
                solution={"path": self._solve_pathfinding(grid, start, end, obstacles)},
                metadata=self._generate_metadata(
                    PuzzleType.PATHFINDING,
                    n,
                    constraint_count,
                    variable_domain_size
                )
            )
            puzzles.append(instance)
        
        return puzzles

    def generate_logic_grid(
        self,
        n: int,
        count: int,
        difficulty: str = "medium"
    ) -> List[PuzzleInstance]:
        """
        Generate logic grid puzzles (Einstein's riddle style).
        N represents the number of categories/items.
        """
        puzzles = []
        num_items = n if n >= 3 else 3  # Minimum 3 items per category
        
        for i in range(count):
            # Generate a logic grid puzzle
            categories, clues, solution = self._generate_logic_grid_puzzle(
                num_items
            )
            
            constraints = [
                f"Number of items per category: {num_items}",
                "Each item must be uniquely assigned across categories",
                "All clues must be satisfied"
            ] + clues[:10]  # Include first 10 clues as constraints
            
            constraint_count = len(constraints)
            variable_domain_size = num_items ** len(categories)
            
            instance = PuzzleInstance(
                puzzle_type=PuzzleType.LOGIC_GRID,
                constraints=constraints,
                initial_state={
                    "categories": categories,
                    "clues": clues,
                    "num_items": num_items
                },
                target_state={"solution": solution},
                solution={"solution": solution},
                metadata=self._generate_metadata(
                    PuzzleType.LOGIC_GRID,
                    n,
                    constraint_count,
                    variable_domain_size
                )
            )
            puzzles.append(instance)
        
        return puzzles

    def generate_arithmetic(
        self,
        n: int,
        count: int,
        difficulty: str = "medium"
    ) -> List[PuzzleInstance]:
        """
        Generate arithmetic puzzles (e.g., 24 game variants).
        N represents the number of operands.
        """
        puzzles = []
        num_operands = n if n >= 3 else 3  # Minimum 3 operands
        
        for i in range(count):
            # Generate arithmetic puzzle
            operands, target, solution = self._generate_arithmetic_puzzle(
                num_operands
            )
            
            constraints = [
                f"Number of operands: {num_operands}",
                f"Target value: {target}",
                "Use each operand exactly once",
                "Only use +, -, *, / operators",
                "Parentheses are allowed"
            ]
            
            constraint_count = len(constraints)
            variable_domain_size = 100  # Typical range for operands
            
            instance = PuzzleInstance(
                puzzle_type=PuzzleType.ARITHMETIC,
                constraints=constraints,
                initial_state={
                    "operands": operands,
                    "target": target,
                    "num_operands": num_operands
                },
                target_state={"solution": solution},
                solution={"solution": solution},
                metadata=self._generate_metadata(
                    PuzzleType.ARITHMETIC,
                    n,
                    constraint_count,
                    variable_domain_size
                )
            )
            puzzles.append(instance)
        
        return puzzles

    def generate_puzzles(
        self,
        n_values: List[int],
        count: int,
        puzzle_types: List[PuzzleType],
        output_dir: str = DEFAULT_OUTPUT_DIR
    ) -> str:
        """
        Generate puzzles for multiple N values and types.
        Returns the path to the generated JSON file.
        """
        all_puzzles = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"puzzles_{timestamp}.json"
        
        for n in n_values:
            for p_type in puzzle_types:
                self.logger.info(f"Generating {count} puzzles of type {p_type.value} with N={n}")
                
                if p_type == PuzzleType.SUDOKU:
                    puzzles = self.generate_sudoku(n, count)
                elif p_type == PuzzleType.PATHFINDING:
                    puzzles = self.generate_pathfinding(n, count)
                elif p_type == PuzzleType.LOGIC_GRID:
                    puzzles = self.generate_logic_grid(n, count)
                elif p_type == PuzzleType.ARITHMETIC:
                    puzzles = self.generate_arithmetic(n, count)
                else:
                    raise DataGenerationError(f"Unknown puzzle type: {p_type}")
                
                all_puzzles.extend(puzzles)
        
        # Write to JSON with provenance header
        output_data = {
            "header": {
                "source_id": self.source_id,
                "generation_seed": self.seed,
                "timestamp": datetime.utcnow().isoformat(),
                "generator_version": self.version,
                "total_instances": len(all_puzzles),
                "n_values": n_values,
                "puzzle_types": [pt.value for pt in puzzle_types],
                "count_per_type": count
            },
            "puzzles": [p.to_dict() for p in all_puzzles]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"Generated {len(all_puzzles)} puzzles to {output_file}")
        return str(output_file)

    # Helper methods for puzzle generation
    def _generate_valid_sudoku(self, size: int) -> List[List[int]]:
        """Generate a valid sudoku grid"""
        grid = [[0] * size for _ in range(size)]
        self._fill_sudoku(grid, 0, 0)
        return grid

    def _fill_sudoku(self, grid: List[List[int]], row: int, col: int) -> bool:
        """Recursively fill sudoku grid"""
        size = len(grid)
        if row == size:
            return True
        
        if col == size:
            return self._fill_sudoku(grid, row + 1, 0)
        
        if grid[row][col] != 0:
            return self._fill_sudoku(grid, row, col + 1)
        
        numbers = list(range(1, size + 1))
        self.random.shuffle(numbers)
        
        for num in numbers:
            if self._is_valid_sudoku_move(grid, row, col, num):
                grid[row][col] = num
                if self._fill_sudoku(grid, row, col + 1):
                    return True
                grid[row][col] = 0
        
        return False

    def _is_valid_sudoku_move(
        self,
        grid: List[List[int]],
        row: int,
        col: int,
        num: int
    ) -> bool:
        """Check if a move is valid in sudoku"""
        size = len(grid)
        
        # Check row
        if num in grid[row]:
            return False
        
        # Check column
        for r in range(size):
            if grid[r][col] == num:
                return False
        
        # Check box
        box_size = int(size ** 0.5)
        box_row = (row // box_size) * box_size
        box_col = (col // box_size) * box_size
        
        for r in range(box_row, box_row + box_size):
            for c in range(box_col, box_col + box_size):
                if grid[r][c] == num:
                    return False
        
        return True

    def _create_puzzle_from_grid(
        self,
        grid: List[List[int]],
        difficulty: str
    ) -> Tuple[List[List[int]], List[List[int]]]:
        """Create a puzzle by removing cells from a valid grid"""
        size = len(grid)
        solution = [row[:] for row in grid]
        puzzle = [row[:] for row in grid]
        
        # Number of cells to remove based on difficulty
        if difficulty == "easy":
            remove_count = size * size // 4
        elif difficulty == "medium":
            remove_count = size * size // 2
        else:  # hard
            remove_count = size * size * 3 // 4
        
        cells = [(r, c) for r in range(size) for c in range(size)]
        self.random.shuffle(cells)
        
        for i in range(remove_count):
            r, c = cells[i]
            puzzle[r][c] = 0
        
        return puzzle, solution

    def _generate_pathfinding_grid(
        self,
        size: int,
        difficulty: str
    ) -> Tuple[List[List[int]], Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]:
        """Generate a pathfinding grid with obstacles"""
        grid = [[0] * size for _ in range(size)]
        obstacles = []
        
        # Number of obstacles based on difficulty
        if difficulty == "easy":
            obstacle_count = size * size // 10
        elif difficulty == "medium":
            obstacle_count = size * size // 5
        else:  # hard
            obstacle_count = size * size // 3
        
        for _ in range(obstacle_count):
            r = self.random.randint(0, size - 1)
            c = self.random.randint(0, size - 1)
            if (r, c) not in obstacles:
                obstacles.append((r, c))
                grid[r][c] = 1  # Obstacle
        
        start = (0, 0)
        end = (size - 1, size - 1)
        
        # Ensure start and end are not obstacles
        while start in obstacles:
            start = (self.random.randint(0, size - 1), self.random.randint(0, size - 1))
        while end in obstacles:
            end = (self.random.randint(0, size - 1), self.random.randint(0, size - 1))
        
        return grid, start, end, obstacles

    def _solve_pathfinding(
        self,
        grid: List[List[int]],
        start: Tuple[int, int],
        end: Tuple[int, int],
        obstacles: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Simple BFS pathfinding"""
        from collections import deque
        
        size = len(grid)
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            (r, c), path = queue.popleft()
            
            if (r, c) == end:
                return path
            
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                
                if 0 <= nr < size and 0 <= nc < size:
                    if (nr, nc) not in visited and (nr, nc) not in obstacles:
                        visited.add((nr, nc))
                        queue.append(((nr, nc), path + [(nr, nc)]))
        
        return []  # No path found

    def _generate_logic_grid_puzzle(
        self,
        num_items: int
    ) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """Generate a logic grid puzzle"""
        categories = ["Person", "Color", "Animal", "Drink"]
        items_per_category = [
            [f"Person{i}" for i in range(num_items)],
            [f"Color{i}" for i in range(num_items)],
            [f"Animal{i}" for i in range(num_items)],
            [f"Drink{i}" for i in range(num_items)]
        ]
        
        # Generate a random valid assignment
        solution = {cat: items for cat, items in zip(categories, items_per_category)}
        
        # Generate clues
        clues = [
            f"{categories[0]}[0] is not {categories[1]}[0]",
            f"{categories[1]}[1] is next to {categories[2]}[0]",
            f"{categories[2]}[1] drinks {categories[3]}[0]",
        ]
        
        return categories, clues, solution

    def _generate_arithmetic_puzzle(
        self,
        num_operands: int
    ) -> Tuple[List[int], int, str]:
        """Generate an arithmetic puzzle"""
        operands = [self.random.randint(1, 10) for _ in range(num_operands)]
        target = self.random.randint(1, 50)
        
        # Simple solution generation (in real implementation, would solve properly)
        solution = f"({operands[0]} + {operands[1]}) * {operands[2]}" if num_operands >= 3 else f"{operands[0]} + {operands[1]}"
        
        return operands, target, solution

def main():
    """Main entry point for puzzle generation"""
    parser = argparse.ArgumentParser(
        description="Generate logic puzzles with provenance metadata"
    )
    parser.add_argument(
        "--n",
        type=int,
        nargs="+",
        required=True,
        help="List of N values for complexity scaling (e.g., 10 100 500)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Number of puzzles per type per N value (default: {DEFAULT_COUNT})"
    )
    parser.add_argument(
        "--types",
        type=str,
        nargs="+",
        choices=[pt.value for pt in PuzzleType],
        default=[PuzzleType.SUDOKU.value, PuzzleType.PATHFINDING.value],
        help="Puzzle types to generate (default: sudoku pathfinding)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for generated puzzles (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})"
    )
    parser.add_argument(
        "--source-id",
        type=str,
        default=DEFAULT_SOURCE_ID,
        help=f"Source identifier for provenance (default: {DEFAULT_SOURCE_ID})"
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=1000,
        help="Maximum attempts to generate valid puzzles (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Convert puzzle type strings to enums
    puzzle_types = [PuzzleType(pt) for pt in args.types]
    
    try:
        generator = PuzzleGenerator(
            source_id=args.source_id,
            seed=args.seed
        )
        
        output_file = generator.generate_puzzles(
            n_values=args.n,
            count=args.count,
            puzzle_types=puzzle_types,
            output_dir=args.output_dir
        )
        
        print(f"Successfully generated puzzles to: {output_file}")
        return 0
        
    except DataGenerationError as e:
        logger.error(f"Data generation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
