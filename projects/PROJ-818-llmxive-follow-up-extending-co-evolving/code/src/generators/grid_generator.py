"""
Grid-world navigation generator using networkx.
Creates solvable grids with non-overlapping rule sets (e.g., "avoid red", "diagonal paths").
Includes bounded retry logic for invalid generations.
"""

import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import networkx as nx


class GridGenerationError(Exception):
    """Raised when grid generation fails after max retries."""
    pass


class GridWorldGenerator:
    """
    Generates solvable grid-world navigation tasks with distinct rule sets.
    """

    # Rule types that can be applied to grids
    RULE_TYPES = [
        "avoid_red",          # Cannot traverse cells marked as red
        "avoid_blue",         # Cannot traverse cells marked as blue
        "diagonal_paths",     # Diagonal movement allowed (8-connectivity)
        "no_diagonal_paths",  # Only 4-connectivity (Manhattan)
        "avoid_corners",      # Cannot start or end in corners
        "require_center",     # Path must pass through center cell
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator with optional seed for reproducibility.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    def _create_grid_graph(self, size: int, connectivity: int = 4) -> nx.Graph:
        """
        Create a grid graph of given size.

        Args:
            size: Grid dimension (size x size)
            connectivity: 4 for Manhattan, 8 for including diagonals

        Returns:
            networkx Graph representing the grid
        """
        G = nx.grid_2d_graph(size, size)

        if connectivity == 8:
            # Add diagonal edges
            for i in range(size):
                for j in range(size):
                    # Diagonal neighbors
                    for di, dj in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < size and 0 <= nj < size:
                            G.add_edge((i, j), (ni, nj))

        return G

    def _assign_obstacles(self, G: nx.Graph, size: int, obstacle_rate: float, rule: str) -> Dict[Tuple[int, int], str]:
        """
        Assign obstacles to grid cells based on the rule.

        Args:
            G: Grid graph
            size: Grid dimension
            obstacle_rate: Fraction of cells to mark as obstacles
            rule: The rule type determining obstacle placement

        Returns:
            Dictionary mapping obstacle cells to their type
        """
        obstacles = {}
        cells = list(G.nodes())

        if "red" in rule:
            # Mark cells as red obstacles
            num_obstacles = int(len(cells) * obstacle_rate)
            obstacle_cells = random.sample(cells, num_obstacles)
            for cell in obstacle_cells:
                obstacles[cell] = "red"

        elif "blue" in rule:
            num_obstacles = int(len(cells) * obstacle_rate)
            obstacle_cells = random.sample(cells, num_obstacles)
            for cell in obstacle_cells:
                obstacles[cell] = "blue"

        elif "corners" in rule:
            # Mark corners as obstacles
            corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)]
            for corner in corners:
                obstacles[corner] = "corner"

        return obstacles

    def _select_start_end(self, G: nx.Graph, size: int, obstacles: Dict[Tuple[int, int], str], rule: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Select start and end nodes that respect the rule constraints.

        Args:
            G: Grid graph
            size: Grid dimension
            obstacles: Dictionary of obstacle cells
            rule: The rule type

        Returns:
            Tuple of (start_node, end_node)
        """
        available_nodes = [n for n in G.nodes() if n not in obstacles]

        # Filter based on rule
        if "corners" in rule:
            corners = {(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)}
            available_nodes = [n for n in available_nodes if n not in corners]

        if len(available_nodes) < 2:
            raise ValueError("Not enough valid nodes for start and end")

        start, end = random.sample(available_nodes, 2)

        # Ensure "require_center" rule is satisfied if applicable
        if "center" in rule:
            center = (size // 2, size // 2)
            if center in obstacles:
                raise ValueError("Center is blocked, cannot satisfy 'require_center' rule")
            # Re-select if neither start nor end is center (we'll check path later)
            if start != center and end != center:
                # Force one of them to be center
                if random.random() < 0.5:
                    start = center
                else:
                    end = center

        return start, end

    def _find_path(self, G: nx.Graph, start: Tuple[int, int], end: Tuple[int, int], obstacles: Dict[Tuple[int, int], str]) -> Optional[List[Tuple[int, int]]]:
        """
        Find a path from start to end avoiding obstacles.

        Args:
            G: Grid graph
            start: Start node
            end: End node
            obstacles: Dictionary of obstacle cells

        Returns:
            Path as list of nodes, or None if no path exists
        """
        # Create a subgraph without obstacle nodes
        H = G.copy()
        H.remove_nodes_from(obstacles.keys())

        try:
            path = nx.shortest_path(H, source=start, target=end)
            return path
        except nx.NetworkXNoPath:
            return None

    def generate_grid(
        self,
        size: int = 10,
        rule: str = "avoid_red",
        obstacle_rate: float = 0.15,
        connectivity: int = 4,
        max_retries: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a single solvable grid-world instance.

        Args:
            size: Grid dimension (size x size)
            rule: The rule type to apply
            obstacle_rate: Fraction of cells to mark as obstacles
            connectivity: 4 for Manhattan, 8 for including diagonals
            max_retries: Maximum number of retry attempts for valid generation

        Returns:
            Dictionary containing grid configuration and metadata

        Raises:
            GridGenerationError: If no valid grid can be generated after max_retries
        """
        if rule not in self.RULE_TYPES:
            raise ValueError(f"Unknown rule type: {rule}. Valid options: {self.RULE_TYPES}")

        # Adjust connectivity based on rule
        if "diagonal" in rule:
            connectivity = 8 if rule == "diagonal_paths" else 4

        for attempt in range(max_retries):
            try:
                # Create grid graph
                G = self._create_grid_graph(size, connectivity)

                # Assign obstacles based on rule
                obstacles = self._assign_obstacles(G, size, obstacle_rate, rule)

                # Select start and end points
                start, end = self._select_start_end(G, size, obstacles, rule)

                # Find path
                path = self._find_path(G, start, end, obstacles)

                if path is None:
                    # No valid path, retry
                    continue

                # Generate the grid instance
                grid_data = {
                    "size": size,
                    "rule": rule,
                    "connectivity": connectivity,
                    "obstacle_rate": obstacle_rate,
                    "start": list(start),
                    "end": list(end),
                    "path": [list(node) for node in path],
                    "obstacles": {f"{k[0]},{k[1]}": v for k, v in obstacles.items()},
                    "path_length": len(path),
                    "seed": self.seed,
                }

                return grid_data

            except (ValueError, nx.NetworkXError) as e:
                # Retry on failure
                continue

        raise GridGenerationError(
            f"Failed to generate valid grid after {max_retries} retries. "
            f"Last attempt: size={size}, rule={rule}, obstacle_rate={obstacle_rate}"
        )

    def generate_dataset(
        self,
        num_grids: int = 100,
        size: int = 10,
        rules: Optional[List[str]] = None,
        obstacle_rate: float = 0.15,
        output_path: Optional[str] = None,
        max_retries: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate a dataset of grid-world instances.

        Args:
            num_grids: Number of grid instances to generate
            size: Grid dimension
            rules: List of rule types to use (randomly selected if None)
            obstacle_rate: Fraction of cells to mark as obstacles
            output_path: Optional path to save the dataset as JSON
            max_retries: Maximum retries per grid generation

        Returns:
            List of grid instance dictionaries
        """
        if rules is None:
            rules = self.RULE_TYPES

        grids = []
        for i in range(num_grids):
            # Select a random rule for this grid
            rule = random.choice(rules)

            # Generate with local seed for reproducibility
            local_seed = random.randint(0, 2**32 - 1)
            grid_gen = GridWorldGenerator(seed=local_seed)

            grid_data = grid_gen.generate_grid(
                size=size,
                rule=rule,
                obstacle_rate=obstacle_rate,
                max_retries=max_retries
            )
            grid_data["instance_id"] = i
            grids.append(grid_data)

        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(grids, f, indent=2)

        return grids


def main():
    """
    Main entry point for standalone grid generation.
    Generates a training dataset and saves it to data/grid_world_training.json.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate grid-world navigation datasets")
    parser.add_argument("--num-grids", type=int, default=100, help="Number of grids to generate")
    parser.add_argument("--size", type=int, default=10, help="Grid dimension")
    parser.add_argument("--obstacle-rate", type=float, default=0.15, help="Fraction of obstacle cells")
    parser.add_argument("--output", type=str, default="data/grid_world_training.json", help="Output file path")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    generator = GridWorldGenerator(seed=args.seed)

    print(f"Generating {args.num_grids} grid-world instances...")
    grids = generator.generate_dataset(
        num_grids=args.num_grids,
        size=args.size,
        obstacle_rate=args.obstacle_rate,
        output_path=args.output,
        max_retries=20
    )

    print(f"Generated {len(grids)} valid grid instances")
    print(f"Saved to: {args.output}")

    # Print summary statistics
    rule_counts = {}
    for grid in grids:
        rule = grid["rule"]
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    print("\nDistribution by rule:")
    for rule, count in sorted(rule_counts.items()):
        print(f"  {rule}: {count} ({100*count/len(grids):.1f}%)")


if __name__ == "__main__":
    main()