"""
Synthetic Workflow Generator for llmXive Project.

Generates a collection of deterministic Directed Acyclic Graphs (DAGs)
representing workflows with varying depths (1-20) and complexities (1-10).
Implements FR-001: Deterministic seeding for reproducibility.

Output:
    Saves JSON files containing workflow definitions to data/raw/.
    Each file contains metadata (depth, complexity, seed) and the graph structure.
"""
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure code directory is in path for imports if run as script
_code_path = Path(__file__).resolve().parent.parent
if str(_code_path) not in sys.path:
    sys.path.insert(0, str(_code_path))

from utils.token_counter import count_tokens

# Constants
MIN_DEPTH = 1
MAX_DEPTH = 20
MIN_COMPLEXITY = 1
MAX_COMPLEXITY = 10
WORKFLOWS_PER_DEPTH = 25
OUTPUT_DIR = Path("data/raw")

class SyntheticWorkflowGenerator:
    """
    Generates synthetic DAG workflows with controlled depth and complexity.
    Uses deterministic seeding to ensure reproducibility across runs.
    """

    def __init__(self, base_seed: int = 42):
        """
        Initialize the generator with a base seed.

        Args:
            base_seed: The integer seed for the random number generator.
        """
        self.base_seed = base_seed
        self.workflows: List[Dict[str, Any]] = []

    def _generate_dag(self, depth: int, complexity: int, seed: int) -> Dict[str, Any]:
        """
        Generate a single DAG with the specified depth and complexity.

        Args:
            depth: The maximum path length in the DAG (number of layers).
            complexity: The average number of edges per node (branching factor).
            seed: The specific seed for this workflow instance.

        Returns:
            A dictionary representing the workflow graph and metadata.
        """
        rng = random.Random(seed)
        nodes: List[Dict[str, Any]] = []
        edges: List[Tuple[int, int]] = []

        # Calculate node count based on depth and complexity
        # Complexity roughly maps to branching factor, ensuring at least 1 edge per node where possible
        # We ensure a linear backbone for the depth requirement, then add complexity edges
        num_layers = depth
        nodes_per_layer = max(1, int(complexity * 1.5)) # Ensure enough nodes to support branching

        node_id_counter = 0
        layer_nodes: List[List[int]] = []

        # Create layers
        for layer_idx in range(num_layers):
            current_layer_nodes = []
            for _ in range(nodes_per_layer):
                nid = node_id_counter
                node_id_counter += 1
                # Assign a random "policy type" to simulate real workflow steps
                policy_types = ["data_fetch", "transform", "validate", "aggregate", "report"]
                policy_type = rng.choice(policy_types)
                
                nodes.append({
                    "id": nid,
                    "layer": layer_idx,
                    "policy_type": policy_type,
                    "token_cost": rng.randint(10, 500) # Simulated token cost per node
                })
                current_layer_nodes.append(nid)
            layer_nodes.append(current_layer_nodes)

        # Create edges to ensure connectivity and depth
        # 1. Ensure a backbone path through the layers to guarantee depth
        for layer_idx in range(num_layers - 1):
            # Connect a random node in current layer to a random node in next layer
            # To ensure full depth, we connect at least one path
            src_node = layer_nodes[layer_idx][0]
            dst_node = layer_nodes[layer_idx + 1][0]
            edges.append((src_node, dst_node))

        # 2. Add complexity edges
        # Total potential edges between layers
        total_potential_edges = 0
        for layer_idx in range(num_layers - 1):
            total_potential_edges += len(layer_nodes[layer_idx]) * len(layer_nodes[layer_idx + 1])
        
        # Target edges based on complexity (scaled)
        # Complexity 1 = minimal, Complexity 10 = dense
        target_edges = int(total_potential_edges * (complexity / (MAX_COMPLEXITY * 2)))
        
        # Ensure we have at least the backbone edges
        target_edges = max(target_edges, num_layers - 1)

        added_edges = set()
        while len(edges) < target_edges:
            layer_idx = rng.randint(0, num_layers - 2)
            src_node = rng.choice(layer_nodes[layer_idx])
            dst_node = rng.choice(layer_nodes[layer_idx + 1])
            
            if (src_node, dst_node) not in added_edges:
                edges.append((src_node, dst_node))
                added_edges.add((src_node, dst_node))

        # Calculate total token cost
        total_tokens = sum(n["token_cost"] for n in nodes)
        # Add a small buffer for graph overhead simulation
        overhead = count_tokens(json.dumps({"nodes": nodes, "edges": edges}))
        total_tokens += overhead

        return {
            "id": f"wf_{depth}_{complexity}_{seed}",
            "depth": depth,
            "complexity": complexity,
            "seed": seed,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_token_cost": total_tokens,
            "nodes": nodes,
            "edges": edges
        }

    def generate_all(self) -> List[Dict[str, Any]]:
        """
        Generate the full set of workflows: depths 1-20, 25 instances each.
        Uses deterministic seeding derived from the base seed.

        Returns:
            List of generated workflow dictionaries.
        """
        self.workflows = []
        current_seed = self.base_seed

        for depth in range(MIN_DEPTH, MAX_DEPTH + 1):
            for i in range(WORKFLOWS_PER_DEPTH):
                # Complexity varies 1-10, cycling or random per instance
                # To ensure coverage, we distribute complexities evenly or randomly
                # Let's vary complexity randomly for each instance to get a mix
                complexity = random.Random(current_seed).randint(MIN_COMPLEXITY, MAX_COMPLEXITY)
                
                workflow = self._generate_dag(depth, complexity, current_seed)
                self.workflows.append(workflow)
                current_seed += 1

        return self.workflows

    def save_to_disk(self, output_path: Path) -> None:
        """
        Save the generated workflows to a JSON file.

        Args:
            output_path: The path where the JSON file will be saved.
        """
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / "synthetic_workflows.json"
        
        # Prepare data for saving
        export_data = {
            "metadata": {
                "generator": "SyntheticWorkflowGenerator",
                "base_seed": self.base_seed,
                "total_workflows": len(self.workflows),
                "depth_range": [MIN_DEPTH, MAX_DEPTH],
                "complexity_range": [MIN_COMPLEXITY, MAX_COMPLEXITY],
                "workflows_per_depth": WORKFLOWS_PER_DEPTH
            },
            "workflows": self.workflows
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Successfully generated {len(self.workflows)} workflows to {output_file}")


def main():
    """
    Entry point for the synthetic workflow generation.
    """
    print("Starting Synthetic Workflow Generation...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator with a fixed seed for reproducibility
    generator = SyntheticWorkflowGenerator(base_seed=42)
    
    # Generate workflows
    workflows = generator.generate_all()
    
    # Save to disk
    generator.save_to_disk(OUTPUT_DIR)
    
    print("Generation complete.")


if __name__ == "__main__":
    main()
