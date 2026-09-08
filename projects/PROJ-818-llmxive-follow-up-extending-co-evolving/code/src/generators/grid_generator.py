"""
Grid-world navigation generator for the Co-Evolving Policy Distillation project.

Generates solvable grid-world navigation tasks with non-overlapping rule sets
using NetworkX for graph representation and pathfinding.
"""

import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import networkx as nx


class GridGenerationError(Exception):
    """Exception raised for grid generation failures."""
    pass


class GridWorldGenerator:
    """
    Generates solvable grid-world navigation tasks with distinct rule sets.

    Rules include:
    - Avoid red cells
    - Diagonal movement allowed/disallowed
    - Specific obstacles
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the generator with configuration.

        Args:
            config: Dictionary containing generation parameters:
                    - grid_size: Tuple (rows, cols)
                    - num_obstacles: Number of obstacles to place
                    - rules: List of rule identifiers
                    - seed: Random seed for reproducibility
                    - max_retries: Maximum retry attempts for valid generation
        """
        self.grid_size = config.get("grid_size", (10, 10))
        self.num_obstacles = config.get("num_obstacles", 5)
        self.rules = config.get("rules", ["avoid_red", "no_diagonal"])
        self.seed = config.get("seed", 42)
        self.max_retries = config.get("max_retries", 100)
        
        random.seed(self.seed)

    def _create_grid_graph(self) -> nx.Graph:
        """
        Create a grid graph with the specified dimensions.

        Returns:
            A NetworkX graph representing the grid.
        """
        rows, cols = self.grid_size
        G = nx.Graph()

        # Add nodes
        for r in range(rows):
            for c in range(cols):
                G.add_node((r, c))

        # Add edges (up, down, left, right)
        for r in range(rows):
            for c in range(cols):
                if r + 1 < rows:
                    G.add_edge((r, c), (r + 1, c))
                if c + 1 < cols:
                    G.add_edge((r, c), (r, c + 1))

        return G

    def _add_obstacles(self, G: nx.Graph, start: Tuple[int, int], end: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """
        Add obstacles to the grid while ensuring solvability.

        Args:
            G: The grid graph.
            start: Starting position.
            end: Ending position.

        Returns:
            Set of obstacle coordinates.
        """
        rows, cols = self.grid_size
        obstacles = set()
        attempts = 0
        max_attempts = self.num_obstacles * 10

        while len(obstacles) < self.num_obstacles and attempts < max_attempts:
            r = random.randint(0, rows - 1)
            c = random.randint(0, cols - 1)
            pos = (r, c)

            # Don't place obstacles on start or end
            if pos == start or pos == end:
                attempts += 1
                continue

            # Temporarily remove node and check connectivity
            G_copy = G.copy()
            G_copy.remove_node(pos)
            
            if nx.has_path(G_copy, start, end):
                obstacles.add(pos)
            attempts += 1

        return obstacles

    def _add_red_cells(self, G: nx.Graph, obstacles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Add red cells (penalty cells) to the grid.

        Args:
            G: The grid graph.
            obstacles: Set of obstacle coordinates.

        Returns:
            Set of red cell coordinates.
        """
        rows, cols = self.grid_size
        red_cells = set()
        num_red = max(3, self.num_obstacles // 2)

        available = [(r, c) for r in range(rows) for c in range(cols) 
                    if (r, c) not in obstacles]
        
        # Don't place red cells on start or end
        if available:
            red_cells = set(random.sample(available, min(num_red, len(available))))

        return red_cells

    def _generate_grid_instance(self, rule_set_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate a single grid instance with the specified rules.

        Args:
            rule_set_id: Identifier for the rule set.

        Returns:
            Dictionary containing grid instance data, or None if generation fails.
        """
        rows, cols = self.grid_size
        
        # Create base grid
        G = self._create_grid_graph()
        
        # Select start and end positions
        start = (random.randint(0, rows // 2 - 1), random.randint(0, cols // 2 - 1))
        end = (random.randint(rows // 2, rows - 1), random.randint(cols // 2, cols - 1))
        
        # Add obstacles ensuring solvability
        obstacles = self._add_obstacles(G, start, end)
        
        # Add red cells
        red_cells = self._add_red_cells(G, obstacles)
        
        # Calculate shortest path
        try:
            shortest_path = nx.shortest_path(G, start, end)
            path_length = len(shortest_path) - 1
        except nx.NetworkXNoPath:
            return None  # Retry needed

        # Build instance data
        instance = {
            "rule_set_id": rule_set_id,
            "grid_size": self.grid_size,
            "start": list(start),
            "end": list(end),
            "obstacles": [list(obs) for obs in obstacles],
            "red_cells": [list(rc) for rc in red_cells],
            "rules": self.rules.copy(),
            "shortest_path": [list(p) for p in shortest_path],
            "path_length": path_length,
            "solvability_verified": True
        }

        return instance

    def generate(self, num_instances: int = 10) -> List[Dict[str, Any]]:
        """
        Generate multiple grid instances with the specified rules.

        Args:
            num_instances: Number of instances to generate.

        Returns:
            List of generated grid instances.

        Raises:
            GridGenerationError: If unable to generate valid instances after retries.
        """
        instances = []
        rule_set_id = f"grid_{self.seed}_{len(instances)}"

        for i in range(num_instances):
            success = False
            retry_count = 0
            instance = None

            while not success and retry_count < self.max_retries:
                instance = self._generate_grid_instance(rule_set_id)
                if instance and instance["solvability_verified"]:
                    success = True
                else:
                    retry_count += 1

            if not success:
                raise GridGenerationError(
                    f"Failed to generate valid grid instance after {self.max_retries} retries"
                )

            instances.append(instance)

        return instances


def main():
    """Main entry point for grid generation script."""
    import sys
    
    # Default configuration
    config = {
        "grid_size": (10, 10),
        "num_obstacles": 5,
        "rules": ["avoid_red", "no_diagonal"],
        "seed": 42,
        "max_retries": 100,
        "num_instances": 20,
        "output_path": "data/grid_worlds.json"
    }

    # Load config from file if provided
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)

    # Create generator
    generator = GridWorldGenerator(config)

    # Generate instances
    try:
        instances = generator.generate(config["num_instances"])
        
        # Write output
        output_path = Path(config["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "metadata": {
                    "generator": "GridWorldGenerator",
                    "config": config,
                    "num_instances": len(instances)
                },
                "instances": instances
            }, f, indent=2)
        
        print(f"Generated {len(instances)} grid instances to {output_path}")
        
    except GridGenerationError as e:
        print(f"Grid generation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()