"""
Grid-world navigation generator using networkx.
Creates solvable grids with non-overlapping rule sets and retry logic.
"""
import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import networkx as nx


class GridGenerationError(Exception):
    """Raised when grid generation fails after retries."""
    pass


class GridWorldGenerator:
    """
    Generates solvable grid-world navigation tasks with distinct rule sets.
    
    Rules include:
    - Avoid red cells
    - Allow diagonal paths
    - Avoid specific obstacles
    - Target collection requirements
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        self.rule_sets = self._define_rule_sets()
    
    def _define_rule_sets(self) -> List[Dict[str, Any]]:
        """Define distinct, non-overlapping rule sets for different grid domains."""
        return [
            {
                "id": "avoid_red",
                "name": "Avoid Red Cells",
                "constraints": {
                    "forbidden_colors": ["red"],
                    "allow_diagonal": False
                },
                "description": "Navigate without stepping on red cells, only cardinal moves"
            },
            {
                "id": "diagonal_paths",
                "name": "Diagonal Paths Allowed",
                "constraints": {
                    "forbidden_colors": [],
                    "allow_diagonal": True
                },
                "description": "Can move diagonally, no color restrictions"
            },
            {
                "id": "avoid_obstacles",
                "name": "Avoid Fixed Obstacles",
                "constraints": {
                    "forbidden_colors": [],
                    "allow_diagonal": False,
                    "fixed_obstacles": True
                },
                "description": "Navigate around pre-defined obstacle positions"
            },
            {
                "id": "multi_target",
                "name": "Multi-Target Collection",
                "constraints": {
                    "forbidden_colors": [],
                    "allow_diagonal": True,
                    "require_multiple_targets": True
                },
                "description": "Must visit multiple target cells in any order"
            }
        ]
    
    def _create_grid_graph(
        self,
        size: int,
        rule_set: Dict[str, Any]
    ) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Create a grid graph with obstacles and special cells based on rule set.
        
        Returns:
            Tuple of (networkx graph, grid metadata)
        """
        constraints = rule_set["constraints"]
        
        # Create grid graph
        G = nx.grid_2d_graph(size, size)
        
        # Add metadata to nodes
        grid_metadata = {
            "size": size,
            "rule_set_id": rule_set["id"],
            "start": None,
            "end": None,
            "obstacles": [],
            "targets": [],
            "red_cells": [],
            "diagonal_allowed": constraints.get("allow_diagonal", False)
        }
        
        # Randomly place obstacles if required
        if constraints.get("fixed_obstacles", False):
            num_obstacles = max(1, size * size // 10)
            obstacle_positions = set()
            while len(obstacle_positions) < num_obstacles:
                pos = (random.randint(0, size - 1), random.randint(0, size - 1))
                # Don't place obstacles on potential start/end
                if pos not in obstacle_positions:
                    obstacle_positions.add(pos)
            
            for pos in obstacle_positions:
                G.remove_node(pos)
                grid_metadata["obstacles"].append(pos)
        
        # Place start and end positions
        available_nodes = list(G.nodes())
        if len(available_nodes) < 2:
            raise GridGenerationError("Not enough available nodes for start and end")
        
        grid_metadata["start"] = random.choice(available_nodes)
        available_nodes.remove(grid_metadata["start"])
        grid_metadata["end"] = random.choice(available_nodes)
        available_nodes.remove(grid_metadata["end"])
        
        # Add red cells if forbidden_colors includes red
        if "red" in constraints.get("forbidden_colors", []):
            num_red = max(1, size * size // 8)
            red_positions = random.sample(available_nodes, min(num_red, len(available_nodes)))
            grid_metadata["red_cells"] = red_positions
            # Remove red cells from graph if we must avoid them
            for pos in red_positions:
                if G.has_node(pos):
                    G.remove_node(pos)
        
        # Add target cells if required
        if constraints.get("require_multiple_targets", False):
            num_targets = min(3, len(available_nodes) // 2)
            if num_targets > 0:
                target_positions = random.sample(available_nodes, num_targets)
                grid_metadata["targets"] = target_positions
                # Remove targets from graph temporarily to ensure path exists
                for pos in target_positions:
                    if G.has_node(pos):
                        G.remove_node(pos)
        
        return G, grid_metadata
    
    def _add_diagonal_edges(self, G: nx.Graph, grid_size: int) -> None:
        """Add diagonal edges to the grid graph if allowed."""
        for i in range(grid_size):
            for j in range(grid_size):
                node = (i, j)
                if not G.has_node(node):
                    continue
                
                # Add diagonal neighbors
                diagonals = [
                    (i - 1, j - 1), (i - 1, j + 1),
                    (i + 1, j - 1), (i + 1, j + 1)
                ]
                
                for diag in diagonals:
                    if 0 <= diag[0] < grid_size and 0 <= diag[1] < grid_size:
                        if G.has_node(diag) and not G.has_edge(node, diag):
                            G.add_edge(node, diag, weight=1.414)  # Diagonal cost
    
    def _verify_solvability(
        self,
        G: nx.Graph,
        start: Tuple[int, int],
        end: Tuple[int, int],
        grid_metadata: Dict[str, Any]
    ) -> bool:
        """Verify that a valid path exists from start to end."""
        if not G.has_node(start) or not G.has_node(end):
            return False
        
        try:
            path = nx.shortest_path(G, source=start, target=end)
            return len(path) > 0
        except nx.NetworkXNoPath:
            return False
    
    def generate_grid(
        self,
        size: int = 5,
        rule_set_index: Optional[int] = None,
        max_retries: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a single solvable grid world with the given parameters.
        
        Args:
            size: Grid dimension (size x size)
            rule_set_index: Index of rule set to use (random if None)
            max_retries: Maximum retry attempts for invalid generations
        
        Returns:
            Dictionary containing grid graph data and metadata
        
        Raises:
            GridGenerationError: If generation fails after max retries
        """
        if rule_set_index is None:
            rule_set = random.choice(self.rule_sets)
        else:
            if rule_set_index < 0 or rule_set_index >= len(self.rule_sets):
                raise GridGenerationError(f"Invalid rule_set_index: {rule_set_index}")
            rule_set = self.rule_sets[rule_set_index]
        
        for attempt in range(max_retries):
            try:
                G, grid_metadata = self._create_grid_graph(size, rule_set)
                
                # Add diagonal edges if allowed
                if grid_metadata["diagonal_allowed"]:
                    self._add_diagonal_edges(G, size)
                
                # Verify solvability
                if not self._verify_solvability(
                    G,
                    grid_metadata["start"],
                    grid_metadata["end"],
                    grid_metadata
                ):
                    continue  # Retry
                
                # Convert graph to serializable format
                nodes = [{"id": list(node), "type": self._get_node_type(node, grid_metadata)}
                        for node in G.nodes()]
                edges = [{"source": list(u), "target": list(v), "weight": data.get("weight", 1.0)}
                        for u, v, data in G.edges(data=True)]
                
                return {
                    "graph": {
                        "nodes": nodes,
                        "edges": edges
                    },
                    "metadata": grid_metadata,
                    "rule_set": rule_set,
                    "generation_attempt": attempt + 1
                }
            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise GridGenerationError(
                        f"Failed to generate solvable grid after {max_retries} attempts: {str(e)}"
                    )
        
        raise GridGenerationError(
            f"Failed to generate solvable grid after {max_retries} attempts"
        )
    
    def _get_node_type(
        self,
        node: Tuple[int, int],
        grid_metadata: Dict[str, Any]
    ) -> str:
        """Determine the type of a grid node."""
        if node == grid_metadata["start"]:
            return "start"
        elif node == grid_metadata["end"]:
            return "end"
        elif node in grid_metadata["obstacles"]:
            return "obstacle"
        elif node in grid_metadata["targets"]:
            return "target"
        elif node in grid_metadata["red_cells"]:
            return "red"
        else:
            return "normal"
    
    def generate_batch(
        self,
        count: int,
        size: int = 5,
        output_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of solvable grid worlds.
        
        Args:
            count: Number of grids to generate
            size: Grid dimension for all grids
            output_path: Optional path to save results as JSON
        
        Returns:
            List of generated grid world dictionaries
        """
        grids = []
        for i in range(count):
            rule_set_index = i % len(self.rule_sets)
            grid = self.generate_grid(size=size, rule_set_index=rule_set_index)
            grid["instance_id"] = i
            grids.append(grid)
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(grids, f, indent=2)
        
        return grids


def main():
    """Main entry point for grid generation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate grid-world navigation tasks")
    parser.add_argument("--count", type=int, default=10, help="Number of grids to generate")
    parser.add_argument("--size", type=int, default=5, help="Grid size (size x size)")
    parser.add_argument("--output", type=str, default="data/generated_grids.json",
                      help="Output file path")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    generator = GridWorldGenerator(seed=args.seed)
    grids = generator.generate_batch(
        count=args.count,
        size=args.size,
        output_path=args.output
    )
    
    print(f"Generated {len(grids)} solvable grid worlds")
    print(f"Output saved to: {args.output}")
    
    # Verify a sample
    if grids:
        sample = grids[0]
        print(f"\nSample grid metadata:")
        print(f"  Rule set: {sample['rule_set']['name']}")
        print(f"  Start: {sample['metadata']['start']}")
        print(f"  End: {sample['metadata']['end']}")
        print(f"  Obstacles: {len(sample['metadata']['obstacles'])}")
        print(f"  Generation attempts: {sample['generation_attempt']}")


if __name__ == "__main__":
    main()