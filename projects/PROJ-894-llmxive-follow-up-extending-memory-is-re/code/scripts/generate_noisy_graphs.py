"""
Script to generate noisy graph datasets for robustness testing.

This script reads the clean memory graphs from `data/intermediate/graphs_raw.json`,
applies noise injection (edge addition) using `code/graph_utils.inject_noise`,
and saves the resulting noisy graphs to `data/processed/graphs/graph_noise_42.json`.

Dependencies:
- T083: inject_noise logic (edge addition)
- T011a-1b-serialize: clean graph serialization
"""
import os
import json
import logging
import argparse
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from graph_utils import inject_noise
from data_loader import load_graphs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_noisy_graphs(
    input_path: str,
    output_path: str,
    noise_density: float = 0.2,
    seed: int = 42
) -> None:
    """
    Generate noisy graphs by adding random edges to clean graphs.

    Args:
        input_path: Path to the clean graphs JSON file.
        output_path: Path to save the noisy graphs JSON file.
        noise_density: Fraction of original edge count to add (e.g., 0.2 = 20% increase).
        seed: Random seed for reproducibility.
    """
    logger.info(f"Loading clean graphs from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T011a-1b-serialize has been completed."
        )

    with open(input_path, 'r') as f:
        clean_graphs = json.load(f)

    logger.info(f"Loaded {len(clean_graphs)} clean graphs")
    
    if not clean_graphs:
        raise ValueError("Input graphs file is empty. Cannot generate noisy graphs.")

    noisy_graphs = {}
    total_edges_original = 0
    total_edges_noisy = 0

    for task_id, edges in clean_graphs.items():
        logger.debug(f"Processing task: {task_id}")
        
        # Convert list of edges to a format suitable for inject_noise
        # inject_noise expects a graph object or a list of edges depending on implementation
        # Based on T083, it accepts graph and returns a graph. 
        # We assume the input 'edges' is a list of (src, dest) tuples or dicts.
        # We need to reconstruct the graph object to apply noise.
        
        # Reconstruct a simple graph structure for the noise injector
        # Assuming edges are list of dicts or tuples
        import networkx as nx
        G = nx.DiGraph()
        
        for edge in edges:
            if isinstance(edge, dict):
                G.add_edge(edge.get('source', edge.get('src')), edge.get('target', edge.get('dst')))
            else:
                # Assume tuple/list
                G.add_edge(edge[0], edge[1])
        
        original_edges = G.number_of_edges()
        total_edges_original += original_edges

        # Apply noise (adds edges)
        noisy_G = inject_noise(G, density=noise_density, seed=seed)
        
        noisy_edges = list(noisy_G.edges())
        total_edges_noisy += len(noisy_edges)
        
        # Convert back to serializable format (list of dicts)
        noisy_graphs[task_id] = [
            {"source": src, "target": dst} for src, dst in noisy_edges
        ]

    logger.info(f"Generated noisy graphs. Original edges: {total_edges_original}, Noisy edges: {total_edges_noisy}")
    logger.info(f"Edge increase: {total_edges_noisy - total_edges_original} ({((total_edges_noisy - total_edges_original) / total_edges_original * 100):.1f}%)")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(noisy_graphs, f, indent=2)

    logger.info(f"Noisy graphs saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate noisy graph dataset")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/intermediate/graphs_raw.json",
        help="Path to clean graphs JSON file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/graphs/graph_noise_42.json",
        help="Path to save noisy graphs JSON file"
    )
    parser.add_argument(
        "--density", 
        type=float, 
        default=0.2,
        help="Noise density (fraction of original edges to add)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    generate_noisy_graphs(
        input_path=args.input,
        output_path=args.output,
        noise_density=args.density,
        seed=args.seed
    )


if __name__ == "__main__":
    main()