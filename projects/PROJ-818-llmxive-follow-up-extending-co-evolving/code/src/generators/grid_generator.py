import random
import json
import os
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import networkx as nx

logger = logging.getLogger(__name__)

class GridGenerationError(Exception):
    """Exception raised for grid generation failures."""
    pass

class GridWorldGenerator:
    """
    Generates solvable grid-world navigation tasks with distinct rule sets.
    Uses NetworkX to ensure connectivity and solvability.
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.rule_sets = {
            "avoid_red": {"type": "avoid_red", "description": "Avoid red cells"},
            "diagonal_paths": {"type": "diagonal_paths", "description": "Allow diagonal movement"},
            "no_backtrack": {"type": "no_backtrack", "description": "Cannot return to previous cell"},
            "checkpoint_mandatory": {"type": "checkpoint_mandatory", "description": "Must visit checkpoint"}
        }

    def _generate_grid_graph(self, width: int, height: int, rule_type: str) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Generates a grid graph based on the rule type.
        Returns the graph and metadata.
        """
        G = nx.Graph()
        
        # Create grid nodes
        for r in range(height):
            for c in range(width):
                G.add_node((r, c))
        
        # Add edges based on rules
        if rule_type == "avoid_red":
            # Standard grid, but mark some cells as red (obstacles)
            # We'll mark them as node attributes, edges remain valid but traversal logic handles it
            for r in range(height):
                for c in range(width):
                    # 20% chance of red cell
                    if self.rng.random() < 0.2:
                        G.nodes[(r, c)]["color"] = "red"
                    else:
                        G.nodes[(r, c)]["color"] = "green"
            
            # Remove edges connected to red cells for the "avoid" logic to be structural
            # Actually, for the generator, we keep the graph connected but mark obstacles.
            # The solver (agent) must avoid them. To ensure solvability, we ensure a path exists
            # that avoids red cells.
            # Strategy: Generate full grid, then remove red nodes and check connectivity.
            pass
        
        elif rule_type == "diagonal_paths":
            # Allow 8-connectivity
            for r in range(height):
                for c in range(width):
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < height and 0 <= nc < width:
                                G.add_edge((r, c), (nr, nc))
        elif rule_type == "no_backtrack":
            # Standard 4-connectivity, backtracking is a constraint on the path, not the graph
            for r in range(height):
                for c in range(width):
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < height and 0 <= nc < width:
                            G.add_edge((r, c), (nr, nc))
        elif rule_type == "checkpoint_mandatory":
            # Standard 4-connectivity
            for r in range(height):
                for c in range(width):
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < height and 0 <= nc < width:
                            G.add_edge((r, c), (nr, nc))
            # Mark a random checkpoint
            checkpoint = self.rng.choice(list(G.nodes))
            G.nodes[checkpoint]["is_checkpoint"] = True
        
        return G

    def _ensure_solvable(self, G: nx.Graph, rule_type: str, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """
        Checks if a path exists from start to end given the rules.
        For 'avoid_red', we must ensure a path exists that doesn't touch red nodes.
        """
        if rule_type == "avoid_red":
            # Create a subgraph without red nodes
            H = G.copy()
            red_nodes = [n for n, d in H.nodes(data=True) if d.get("color") == "red"]
            H.remove_nodes_from(red_nodes)
            try:
                nx.shortest_path(H, start, end)
                return True
            except nx.NetworkXNoPath:
                return False
        else:
            try:
                nx.shortest_path(G, start, end)
                return True
            except nx.NetworkXNoPath:
                return False

    def generate_instance(self, width: int, height: int, rule_set_id: str) -> Optional[Dict[str, Any]]:
        """
        Generates a single grid instance with bounded retry logic.
        Returns None if generation fails after max attempts.
        """
        max_attempts = 3
        rule_type = self.rule_sets[rule_set_id]["type"]
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Generate graph
                G = self._generate_grid_graph(width, height, rule_type)
                
                # Pick start and end
                nodes = list(G.nodes())
                start = self.rng.choice(nodes)
                end = self.rng.choice([n for n in nodes if n != start])
                
                # Ensure solvability
                if not self._ensure_solvable(G, rule_type, start, end):
                    if attempt == max_attempts:
                        logger.warning(f"Retry limit reached for instance with rule {rule_set_id} (Attempt {attempt})")
                        return None
                    continue
                
                # Build instance data
                grid_data = {
                    "width": width,
                    "height": height,
                    "start": list(start),
                    "end": list(end),
                    "rule_set_id": rule_set_id,
                    "nodes": {},
                    "edges": []
                }
                
                for node, data in G.nodes(data=True):
                    grid_data["nodes"][f"{node[0]},{node[1]}"] = data
                
                for u, v in G.edges():
                    grid_data["edges"].append([list(u), list(v)])
                
                return {
                    "id": f"grid_{self.rng.randint(10000, 99999)}",
                    "domain": "grid_world",
                    "rule_set_id": rule_set_id,
                    "instance_data": grid_data
                }
                
            except Exception as e:
                if attempt == max_attempts:
                    logger.error(f"Failed to generate grid after {max_attempts} attempts: {e}")
                    return None
                continue

        return None

    def generate_dataset(self, count: int, width: int, height: int, rule_set_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Generates a dataset of grid instances.
        """
        instances = []
        for _ in range(count):
            rule_id = self.rng.choice(rule_set_ids)
            instance = self.generate_instance(width, height, rule_id)
            if instance:
                instances.append(instance)
        return instances

def main():
    """Main entry point for the grid generator."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate grid-world navigation tasks")
    parser.add_argument("--count", type=int, default=10, help="Number of instances to generate")
    parser.add_argument("--width", type=int, default=5, help="Grid width")
    parser.add_argument("--height", type=int, default=5, help="Grid height")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/generated_grids.json", help="Output file path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    generator = GridWorldGenerator(seed=args.seed)
    instances = generator.generate_dataset(
        count=args.count,
        width=args.width,
        height=args.height,
        rule_set_ids=["avoid_red", "diagonal_paths", "no_backtrack", "checkpoint_mandatory"]
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(instances, f, indent=2)
    
    logger.info(f"Generated {len(instances)} grid instances to {output_path}")

if __name__ == "__main__":
    main()
