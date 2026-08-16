"""
Puzzle Generator Module for llmXive.

Generates logic and arithmetic puzzles with deterministic verification capabilities.
Supports Sudoku variants, constrained pathfinding, and arithmetic grids.
"""
import json
import random
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

class PuzzleType(Enum):
    SUDOKU_VARIANT = "sudoku_variant"
    CONSTRAINED_PATHFINDING = "constrained_pathfinding"
    ARITHMETIC_GRID = "arithmetic_grid"

@dataclass
class PuzzleInstance:
    id: str
    type: str
    difficulty: str
    parameters: Dict[str, Any]
    constraints: List[str]
    solution_path: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "difficulty": self.difficulty,
            "parameters": self.parameters,
            "constraints": self.constraints,
            "solution_path": self.solution_path,
            "metadata": self.metadata
        }

class PuzzleGenerator:
    """Generates logic puzzles with varying complexity."""

    def __init__(self):
        self.puzzle_counter = 0
        self.difficulty_params = {
            "easy": {"grid_size": 4, "clues": 6, "steps": 3},
            "medium": {"grid_size": 6, "clues": 10, "steps": 5},
            "hard": {"grid_size": 9, "clues": 15, "steps": 8}
        }

    def _generate_id(self) -> str:
        """Generate a unique puzzle ID."""
        self.puzzle_counter += 1
        timestamp = int(time.time() * 1000)
        hash_input = f"{self.puzzle_counter}-{timestamp}-{random.random()}"
        return f"PZ-{hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()}"

    def _generate_sudoku_variant(self, difficulty: str) -> PuzzleInstance:
        """Generate a Sudoku variant puzzle."""
        params = self.difficulty_params[difficulty]
        size = params["grid_size"]
        clues = params["clues"]
        
        # Generate a simple valid grid (1..size)
        grid = [[(i + j) % size + 1 for j in range(size)] for i in range(size)]
        
        # Remove clues to create puzzle
        puzzle_grid = [row[:] for row in grid]
        cells_to_remove = size * size - clues
        removed_cells = []
        
        attempts = 0
        while cells_to_remove > 0 and attempts < 1000:
            r, c = random.randint(0, size - 1), random.randint(0, size - 1)
            if puzzle_grid[r][c] != 0:
                puzzle_grid[r][c] = 0
                removed_cells.append((r, c))
                cells_to_remove -= 1
            attempts += 1

        # Construct solution path
        solution_path = [
            {
                "step": i + 1,
                "action": "fill_cell",
                "row": r,
                "col": c,
                "value": grid[r][c]
            }
            for i, (r, c) in enumerate(removed_cells)
        ]
        
        constraints = [
            f"Grid size: {size}x{size}",
            "Each row must contain unique numbers 1 to N",
            "Each column must contain unique numbers 1 to N",
            f"Initial clues provided: {clues}"
        ]

        return PuzzleInstance(
            id=self._generate_id(),
            type=PuzzleType.SUDOKU_VARIANT.value,
            difficulty=difficulty,
            parameters={
                "grid": puzzle_grid,
                "size": size,
                "clues_count": clues
            },
            constraints=constraints,
            solution_path=solution_path,
            metadata={
                "complexity_score": size * 2.5 + clues * 0.5
            }
        )

    def _generate_arithmetic_grid(self, difficulty: str) -> PuzzleInstance:
        """Generate an arithmetic grid puzzle."""
        params = self.difficulty_params[difficulty]
        size = params["grid_size"]
        steps = params["steps"]
        
        # Generate target sums
        targets = [random.randint(10, 50) for _ in range(size)]
        grid = [[random.randint(1, 9) for _ in range(size)] for _ in range(size)]
        
        # Adjust grid to meet targets (simplified)
        for i in range(size):
            current_sum = sum(grid[i])
            diff = targets[i] - current_sum
            if abs(diff) < 20:
                grid[i][0] += diff
        
        constraints = [
            f"Grid size: {size}x{size}",
            f"Row sums must match target: {targets}",
            "Each cell contains a number 1-9"
        ]

        solution_path = [
            {
                "step": i + 1,
                "action": "adjust_row",
                "row": i,
                "target": targets[i]
            }
            for i in range(steps)
        ]

        return PuzzleInstance(
            id=self._generate_id(),
            type=PuzzleType.ARITHMETIC_GRID.value,
            difficulty=difficulty,
            parameters={
                "grid": grid,
                "targets": targets,
                "size": size
            },
            constraints=constraints,
            solution_path=solution_path,
            metadata={
                "complexity_score": size * 3.0 + steps * 1.5
            }
        )

    def _generate_pathfinding(self, difficulty: str) -> PuzzleInstance:
        """Generate a constrained pathfinding puzzle."""
        params = self.difficulty_params[difficulty]
        size = params["grid_size"]
        
        # Create a simple grid with obstacles
        grid = [[0 for _ in range(size)] for _ in range(size)]
        num_obstacles = int(size * 1.5)
        
        obstacles = []
        while len(obstacles) < num_obstacles:
            r, c = random.randint(0, size - 1), random.randint(0, size - 1)
            if (r, c) != (0, 0) and (r, c) != (size-1, size-1):
                grid[r][c] = 1
                obstacles.append((r, c))
        
        start = (0, 0)
        end = (size - 1, size - 1)
        
        # Generate a valid path (simplified BFS-like)
        path = []
        curr = start
        while curr != end:
            r, c = curr
            if r < size - 1 and grid[r+1][c] == 0:
                curr = (r + 1, c)
            elif c < size - 1 and grid[r][c+1] == 0:
                curr = (r, c + 1)
            else:
                break
            path.append(curr)
        
        constraints = [
            f"Grid size: {size}x{size}",
            f"Start: {start}, End: {end}",
            f"Obstacles: {num_obstacles}",
            "Move only down or right"
        ]

        solution_path = [
            {"step": i + 1, "action": "move", "pos": p}
            for i, p in enumerate(path)
        ]

        return PuzzleInstance(
            id=self._generate_id(),
            type=PuzzleType.CONSTRAINED_PATHFINDING.value,
            difficulty=difficulty,
            parameters={
                "grid": grid,
                "start": start,
                "end": end,
                "obstacles": obstacles,
                "size": size
            },
            constraints=constraints,
            solution_path=solution_path,
            metadata={
                "complexity_score": size * 4.0 + num_obstacles * 0.8
            }
        )

    def generate(self, difficulty: str = "medium") -> PuzzleInstance:
        """Generate a single puzzle instance of the specified difficulty."""
        if difficulty not in self.difficulty_params:
            raise ValueError(f"Unknown difficulty: {difficulty}")
        
        r = random.random()
        if r < 0.33:
            return self._generate_sudoku_variant(difficulty)
        elif r < 0.66:
            return self._generate_arithmetic_grid(difficulty)
        else:
            return self._generate_pathfinding(difficulty)
