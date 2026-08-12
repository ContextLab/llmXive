"""
Puzzle Generator Module.

Implements logic for generating Sudoku variants, constrained pathfinding,
and arithmetic puzzles with systematic complexity scaling.
"""
import json
import random
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

class PuzzleType(Enum):
    SUDOKU_VARIANT = "sudoku_variant"
    CONSTRAINED_PATHFINDING = "constrained_pathfinding"
    ARITHMETIC_GRID = "arithmetic_grid"
    LOGIC_GRID = "logic_grid"

@dataclass
class PuzzleInstance:
    id: str
    type: str
    difficulty: int
    problem: Dict[str, Any]
    constraints: List[Dict[str, Any]]
    solution_hint: Optional[Dict[str, Any]]
    solution_path: Optional[List[Dict[str, Any]]]
    checksum: str
    created_at: str
    complexity_metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PuzzleGenerator:
    """
    Generates logic puzzles with deterministic complexity scaling.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.counter = 0

    def _generate_id(self) -> str:
        self.counter += 1
        timestamp = int(time.time() * 1000000)
        rand_suffix = self.rng.randint(0, 0xFFFFFFFF)
        return f"puzzle-{timestamp:08d}-{rand_suffix:08x}"

    def _generate_sudoku_variant(self, difficulty: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates a Sudoku variant puzzle.
        Difficulty scales grid size (3x3 to 9x9) and removal rate.
        """
        # Map difficulty to grid size (N)
        # 1 -> 3x3, 2 -> 4x4, 3 -> 6x6, 4 -> 8x8, 5 -> 9x9
        sizes = [3, 4, 6, 8, 9]
        grid_size = sizes[min(difficulty - 1, len(sizes) - 1)]
        
        # Generate a solved grid (simplified for demonstration)
        # In a full implementation, this would use a backtracking solver
        grid = [[self.rng.randint(1, grid_size) for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Create the puzzle by removing numbers based on difficulty
        removal_rate = 0.2 + (difficulty * 0.1)
        puzzle_grid = []
        for row in grid:
            new_row = []
            for cell in row:
                if self.rng.random() < removal_rate:
                    new_row.append(0)
                else:
                    new_row.append(cell)
            puzzle_grid.append(new_row)

        problem = {
            "grid_size": grid_size,
            "initial_grid": puzzle_grid,
            "rule": "Fill the grid such that each row, column, and subgrid contains unique numbers from 1 to N."
        }

        constraints = [
            {
                "type": "row_unique",
                "description": f"Each row must contain unique numbers 1-{grid_size}",
                "parameters": {"size": grid_size}
            },
            {
                "type": "column_unique",
                "description": f"Each column must contain unique numbers 1-{grid_size}",
                "parameters": {"size": grid_size}
            },
            {
                "type": "subgrid_unique",
                "description": f"Each subgrid must contain unique numbers 1-{grid_size}",
                "parameters": {"size": grid_size}
            }
        ]

        solution_hint = {
            "filled_cells": sum(1 for row in puzzle_grid for cell in row if cell != 0),
            "empty_cells": sum(1 for row in puzzle_grid for cell in row if cell == 0)
        }

        return problem, constraints

    def _generate_pathfinding(self, difficulty: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates a constrained pathfinding puzzle.
        """
        size = 5 + difficulty  # 6x6 to 10x10
        start = (0, 0)
        end = (size - 1, size - 1)
        
        # Generate obstacles
        obstacle_count = int(size * size * (0.1 + difficulty * 0.05))
        obstacles = set()
        while len(obstacles) < obstacle_count:
            r = self.rng.randint(0, size - 1)
            c = self.rng.randint(0, size - 1)
            if (r, c) != start and (r, c) != end:
                obstacles.add((r, c))

        problem = {
            "grid_size": size,
            "start": start,
            "end": end,
            "obstacles": list(obstacles),
            "rule": "Find a path from start to end avoiding obstacles and constraints."
        }

        constraints = [
            {
                "type": "obstacle_avoidance",
                "description": "Path cannot pass through obstacle cells",
                "parameters": {"obstacles": list(obstacles)}
            },
            {
                "type": "boundary",
                "description": "Path must stay within grid boundaries",
                "parameters": {"size": size}
            }
        ]

        return problem, constraints

    def _generate_arithmetic_grid(self, difficulty: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates an arithmetic grid puzzle (e.g., Kakuro-like).
        """
        size = 3 + difficulty  # 4x4 to 8x8
        target_sum = 10 + difficulty * 5
        
        # Generate a simple grid with some pre-filled values
        grid = [[0] * size for _ in range(size)]
        
        # Fill some cells to create constraints
        num_filled = 2 + difficulty
        for _ in range(num_filled):
            r = self.rng.randint(0, size - 1)
            c = self.rng.randint(0, size - 1)
            grid[r][c] = self.rng.randint(1, 9)

        problem = {
            "grid": grid,
            "target_sum": target_sum,
            "rule": "Fill empty cells with digits 1-9 such that row/column sums match targets."
        }

        constraints = [
            {
                "type": "digit_range",
                "description": "All cells must contain digits 1-9",
                "parameters": {"min": 1, "max": 9}
            },
            {
                "type": "row_sum",
                "description": f"Row sums must equal {target_sum}",
                "parameters": {"target": target_sum}
            }
        ]

        return problem, constraints

    def generate(self, difficulty: int) -> PuzzleInstance:
        """
        Generates a single puzzle instance.
        Difficulty: 1 (easy) to 5 (hard).
        """
        if difficulty < 1 or difficulty > 5:
            raise ValueError("Difficulty must be between 1 and 5")

        # Select puzzle type based on difficulty
        # Even difficulties favor pathfinding, odd favor sudoku/arithmetic
        if difficulty % 2 == 1:
            puzzle_type = PuzzleType.SUDOKU_VARIANT
            problem, constraints = self._generate_sudoku_variant(difficulty)
        else:
            puzzle_type = PuzzleType.CONSTRAINED_PATHFINDING
            problem, constraints = self._generate_pathfinding(difficulty)

        # Generate ID and checksum
        puzzle_id = self._generate_id()
        
        # Create a canonical representation for checksum
        canonical_data = {
            "id": puzzle_id,
            "type": puzzle_type.value,
            "difficulty": difficulty,
            "problem": problem,
            "constraints": constraints
        }
        canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        checksum = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

        complexity_metrics = {
            "variable_count": problem.get("grid_size", 0) ** 2 if "grid_size" in problem else 0,
            "constraint_count": len(constraints),
            "search_space_estimate": float('inf')  # Placeholder for complex estimation
        }

        return PuzzleInstance(
            id=puzzle_id,
            type=puzzle_type.value,
            difficulty=difficulty,
            problem=problem,
            constraints=constraints,
            solution_hint=None,
            solution_path=None,
            checksum=checksum,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            complexity_metrics=complexity_metrics
        )

    def main():
        """CLI entry point for testing generator."""
        import sys
        gen = PuzzleGenerator(seed=42)
        for i in range(5):
            p = gen.generate(difficulty=(i % 5) + 1)
            print(f"Generated: {p.id}, Type: {p.type}, Diff: {p.difficulty}")

if __name__ == "__main__":
    main()