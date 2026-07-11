"""
Grid-World Navigation Generator for Co-Evolving Policy Distillation.

Generates solvable grid-world navigation tasks with distinct rule sets using networkx.
"""
import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path

import networkx as nx

class GridGenerationError(Exception):
    """Raised when grid generation fails."""
    pass

class GridWorldGenerator:
    """
    Generates solvable grid-world navigation tasks with various rule sets.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the grid generator.
        
        Args:
            config: Configuration dictionary with generation parameters.
        """
        self.config = config or {}
        self.seed = self.config.get('seed', 42)
        random.seed(self.seed)
    
    def generate_grid(
        self,
        size: int = 5,
        num_obstacles: int = 3,
        num_goals: int = 1,
        rule_set: List[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a solvable grid-world navigation instance.
        
        Args:
            size: Grid size (size x size).
            num_obstacles: Number of obstacles to place.
            num_goals: Number of goal positions.
            rule_set: List of rules to apply (e.g., "avoid_red", "diagonal_paths").
            seed: Random seed for reproducibility.
            
        Returns:
            Dictionary containing the grid instance.
        """
        if seed is not None:
            random.seed(seed)
        
        rule_set = rule_set or ["avoid_red"]
        
        # Create grid graph
        G = nx.grid_2d_graph(size, size)
        
        # Place obstacles
        all_nodes = list(G.nodes())
        obstacles = random.sample(all_nodes, min(num_obstacles, len(all_nodes) - 2))
        
        # Remove obstacles from graph
        G.remove_nodes_from(obstacles)
        
        # Place start and goal positions
        remaining_nodes = list(G.nodes())
        if len(remaining_nodes) < 2:
            raise GridGenerationError("Grid too small or too many obstacles")
        
        start, goal = random.sample(remaining_nodes, 2)
        
        # Verify solvability
        try:
            path = nx.shortest_path(G, source=start, target=goal)
            if not path:
                raise GridGenerationError("No path exists between start and goal")
        except nx.NetworkXNoPath:
            # Try to regenerate if no path exists
            return self.generate_grid(size, num_obstacles, num_goals, rule_set, seed)
        
        # Apply rules
        grid_data = {
            'grid': [[1 for _ in range(size)] for _ in range(size)],  # 1 = walkable
            'start': list(start),
            'goal': list(goal),
            'obstacles': [list(obs) for obs in obstacles],
            'rules': rule_set,
            'path': [list(node) for node in path],
            'path_length': len(path),
            'size': size,
            'valid': True
        }
        
        # Apply specific rules
        if "avoid_red" in rule_set:
            # Mark some cells as "red" (higher cost)
            red_cells = random.sample(remaining_nodes, min(3, len(remaining_nodes)))
            grid_data['red_cells'] = [list(cell) for cell in red_cells]
        
        if "diagonal_paths" in rule_set:
            # Allow diagonal movement (already supported by grid_2d_graph with modifications)
            grid_data['diagonal_allowed'] = True
        
        return grid_data

    def generate_multiple_grids(
        self,
        count: int,
        seed_offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple grid instances.
        
        Args:
            count: Number of grids to generate.
            seed_offset: Offset for seed to ensure uniqueness.
            
        Returns:
            List of grid instances.
        """
        grids = []
        for i in range(count):
            seed = self.seed + seed_offset + i
            try:
                grid = self.generate_grid(seed=seed)
                grids.append(grid)
            except GridGenerationError as e:
                print(f"Warning: Failed to generate grid {i}: {e}")
        return grids


def main():
    """Main entry point for testing the grid generator."""
    print("Testing Grid World Generator...")
    
    generator = GridWorldGenerator({'seed': 42})
    
    # Generate a single grid
    grid = generator.generate_grid(size=5, num_obstacles=3, rule_set=["avoid_red"])
    print(f"Generated grid of size {grid['size']}x{grid['size']}")
    print(f"Start: {grid['start']}, Goal: {grid['goal']}")
    print(f"Path length: {grid['path_length']}")
    
    # Generate multiple grids
    grids = generator.generate_multiple_grids(count=5, seed_offset=100)
    print(f"Generated {len(grids)} grids successfully")
    
    return grids


if __name__ == "__main__":
    main()
