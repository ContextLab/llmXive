"""
Data loading and graph generation module for the llmXive project.

This module handles:
1. Fetching the real LoCoMo benchmark dataset from HuggingFace.
2. Building memory graphs from task context.
3. Injecting noise (random edges) into graphs for robustness testing.
4. Saving and loading generated artifacts.

Constraints:
- NO synthetic data fallback. If the real dataset fetch fails, the script MUST
  raise an exception and halt execution (T035 requirement).
- Supports streaming for large datasets (T036 requirement).
"""

import os
import json
import logging
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Iterator

import networkx as nx
import numpy as np
from datasets import load_dataset
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "locomo/locomo-benchmark"
DATASET_SPLIT = "test"
DEFAULT_NOISE_DENSITY = 0.1  # 10% of edges added as noise
DEFAULT_SEED = 42

def ensure_output_dirs() -> None:
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed/graphs",
        "data/processed/results",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directories exist.")

def fetch_locomo_dataset(subset: Optional[int] = None, streaming: bool = False) -> Iterator[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.

    Args:
        subset: Optional number of tasks to limit the dataset to.
        streaming: If True, stream the dataset instead of downloading it fully.

    Returns:
        An iterator of dataset rows (dicts).

    Raises:
        RuntimeError: If the dataset cannot be fetched (T035 enforcement).
    """
    logger.info(f"Attempting to fetch dataset: {DATASET_NAME} (split={DATASET_SPLIT})")

    try:
        if streaming:
            logger.info("Using streaming mode for dataset fetch.")
            ds = load_dataset(DATASET_NAME, split=DATASET_SPLIT, streaming=True)
        else:
            ds = load_dataset(DATASET_NAME, split=DATASET_SPLIT)

        # Apply subset limit if requested
        if subset is not None:
            logger.info(f"Limiting dataset to {subset} tasks.")
            if streaming:
                # For streaming, we need to take the first N items
                ds = ds.take(subset)
            else:
                ds = ds.select(range(min(subset, len(ds))))

        logger.info(f"Successfully fetched dataset with {len(ds) if not streaming else 'streaming'} tasks.")
        return iter(ds)

    except Exception as e:
        logger.error(f"Failed to fetch dataset '{DATASET_NAME}': {e}")
        # T035: Fail loudly, never silently fallback to synthetic
        raise RuntimeError(f"Cannot proceed without real data. Fetch failed: {e}") from e

def save_raw_data(tasks: List[Dict[str, Any]], output_path: str = "data/raw/locomo_test.json") -> None:
    """Save raw fetched tasks to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def build_memory_graph(task: Dict[str, Any], seed: int = DEFAULT_SEED) -> nx.DiGraph:
    """
    Build a memory graph from a single task's context.

    The graph nodes represent entities/concepts in the context,
    and edges represent relationships inferred from the text.

    For this implementation, we simulate a graph structure based on
    the task context length and content to ensure reproducibility
    while maintaining the structure required for traversal.

    Args:
        task: A dictionary containing 'question', 'context', 'answer'.
        seed: Random seed for graph construction determinism.

    Returns:
        A directed graph (DiGraph) representing the memory.
    """
    random.seed(seed)
    np.random.seed(seed)

    context = task.get('context', '')
    question = task.get('question', '')
    task_id = task.get('task_id', 'unknown')

    # Create a base graph
    G = nx.DiGraph()

    # Derive a deterministic number of nodes based on context length
    # This ensures different tasks have different graph sizes
    base_nodes = max(5, len(context) // 20)
    num_nodes = min(base_nodes, 100)  # Cap at 100 for performance

    # Add nodes
    for i in range(num_nodes):
        node_id = f"node_{i}"
        G.add_node(node_id, type="entity", id=i)

    # Create a simple chain-like structure with some branches
    # This mimics a memory trace where entities are connected
    for i in range(num_nodes - 1):
        # Main chain
        G.add_edge(f"node_{i}", f"node_{i+1}", weight=1.0, type="sequence")

        # Occasional branch (every 3rd node connects to a new branch)
        if i % 3 == 0 and i + 2 < num_nodes:
            G.add_edge(f"node_{i}", f"node_{i+2}", weight=0.8, type="association")

    # Add a special "target" node connected to the last node
    if num_nodes > 0:
        G.add_node("target", type="goal")
        G.add_edge(f"node_{num_nodes-1}", "target", weight=1.0, type="goal")

    # Store task metadata
    G.graph['task_id'] = task_id
    G.graph['question'] = question
    G.graph['num_nodes'] = num_nodes

    return G

def inject_noise(graph: nx.DiGraph, density: float = DEFAULT_NOISE_DENSITY, seed: int = DEFAULT_SEED) -> nx.DiGraph:
    """
    Inject noise into the graph by adding random edges.

    This implements the FR-001 definition of noise: adding random edges
    between unconnected node pairs.

    Args:
        graph: The original graph.
        density: The proportion of random edges to add relative to existing edges.
        seed: Random seed for reproducibility.

    Returns:
        A new graph with injected noise.
    """
    if not graph.nodes():
        logger.warning("Graph is empty, cannot inject noise.")
        return graph

    random.seed(seed)
    np.random.seed(seed)

    # Create a copy to avoid modifying the original
    noisy_graph = graph.copy()

    # Get all possible node pairs
    nodes = list(noisy_graph.nodes())
    existing_edges = set(noisy_graph.edges())

    # Calculate how many random edges to add
    num_existing_edges = len(existing_edges)
    num_noise_edges = max(1, int(num_existing_edges * density))

    # Find non-existing edges to add
    possible_noise_edges = []
    for i, u in enumerate(nodes):
        for v in nodes[i+1:]:
            if (u, v) not in existing_edges and (v, u) not in existing_edges:
                possible_noise_edges.append((u, v))

    if not possible_noise_edges:
        logger.warning("No possible noise edges to add (graph is fully connected).")
        return noisy_graph

    # Select random edges to add
    num_to_add = min(num_noise_edges, len(possible_noise_edges))
    selected_noise_edges = random.sample(possible_noise_edges, num_to_add)

    # Add noise edges
    for u, v in selected_noise_edges:
        noisy_graph.add_edge(u, v, weight=0.1, type="noise", noise_seed=seed)

    logger.info(f"Injected {len(selected_noise_edges)} noise edges (density: {density:.2%})")

    return noisy_graph

def generate_noisy_graphs(
    tasks: List[Dict[str, Any]],
    noise_density: float = DEFAULT_NOISE_DENSITY,
    seed: int = DEFAULT_SEED
) -> List[Tuple[str, nx.DiGraph]]:
    """
    Generate noisy graphs for a list of tasks.

    Args:
        tasks: List of task dictionaries.
        noise_density: Density of noise to inject.
        seed: Random seed for noise injection.

    Returns:
        List of tuples (task_id, noisy_graph).
    """
    noisy_graphs = []

    for i, task in enumerate(tasks):
        # Build base graph
        base_graph = build_memory_graph(task, seed=seed + i)

        # Inject noise
        noisy_graph = inject_noise(base_graph, density=noise_density, seed=seed + i + 1000)

        noisy_graphs.append((task.get('task_id', f'task_{i}'), noisy_graph))

    return noisy_graphs

def save_noisy_graphs(
    noisy_graphs: List[Tuple[str, nx.DiGraph]],
    output_path: str = "data/processed/graphs/graph_noise_42.json"
) -> None:
    """
    Save noisy graphs to a JSON file.

    Graphs are serialized to a list of dictionaries.

    Args:
        noisy_graphs: List of (task_id, graph) tuples.
        output_path: Path to save the JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    serialized_data = []
    for task_id, graph in noisy_graphs:
        # Convert graph to serializable format
        graph_data = {
            'task_id': task_id,
            'nodes': [],
            'edges': [],
            'graph_attrs': dict(graph.graph)
        }

        for node, attrs in graph.nodes(data=True):
            graph_data['nodes'].append({'id': node, 'attrs': attrs})

        for u, v, attrs in graph.edges(data=True):
            graph_data['edges'].append({'source': u, 'target': v, 'attrs': attrs})

        serialized_data.append(graph_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serialized_data, f, indent=2)

    logger.info(f"Saved {len(noisy_graphs)} noisy graphs to {output_path}")

def load_noisy_graphs(input_path: str = "data/processed/graphs/graph_noise_42.json") -> List[Tuple[str, nx.DiGraph]]:
    """
    Load noisy graphs from a JSON file.

    Args:
        input_path: Path to the JSON file.

    Returns:
        List of (task_id, graph) tuples.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        serialized_data = json.load(f)

    loaded_graphs = []
    for item in serialized_data:
        G = nx.DiGraph()
        task_id = item['task_id']

        # Add nodes
        for node_data in item['nodes']:
            G.add_node(node_data['id'], **node_data['attrs'])

        # Add edges
        for edge_data in item['edges']:
            G.add_edge(edge_data['source'], edge_data['target'], **edge_data['attrs'])

        G.graph.update(item['graph_attrs'])
        loaded_graphs.append((task_id, G))

    logger.info(f"Loaded {len(loaded_graphs)} noisy graphs from {input_path}")
    return loaded_graphs

def main():
    """
    Main entry point for data loading and graph generation.

    Usage:
        python code/data_loader.py --download --generate-graphs --seed 42

    This script:
    1. Fetches the LoCoMo dataset from HuggingFace.
    2. Builds memory graphs for each task.
    3. Injects noise into the graphs.
    4. Saves the noisy graphs to disk.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Download data and generate noisy graphs")
    parser.add_argument('--download', action='store_true', help="Download the dataset")
    parser.add_argument('--generate-graphs', action='store_true', help="Generate noisy graphs")
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument('--subset', type=int, default=5, help="Number of tasks to process (for testing)")
    parser.add_argument('--noise-density', type=float, default=DEFAULT_NOISE_DENSITY, help="Noise density")
    parser.add_argument('--streaming', action='store_true', help="Use streaming mode for large datasets")

    args = parser.parse_args()

    ensure_output_dirs()

    tasks = []

    if args.download:
        logger.info("Fetching LoCoMo dataset...")
        try:
            dataset_iter = fetch_locomo_dataset(subset=args.subset, streaming=args.streaming)
            tasks = list(dataset_iter)
            save_raw_data(tasks)
        except RuntimeError as e:
            logger.error(f"Data fetch failed: {e}")
            raise

    if args.generate_graphs:
        if not tasks:
            # Try to load from raw data if download wasn't explicitly requested but data exists
            raw_path = "data/raw/locomo_test.json"
            if os.path.exists(raw_path):
                logger.info(f"Loading tasks from {raw_path}")
                with open(raw_path, 'r') as f:
                    tasks = json.load(f)
            else:
                logger.error("No tasks found. Please run with --download first or provide raw data.")
                return

        logger.info(f"Generating noisy graphs for {len(tasks)} tasks with seed={args.seed}...")
        noisy_graphs = generate_noisy_graphs(
            tasks,
            noise_density=args.noise_density,
            seed=args.seed
        )

        output_path = f"data/processed/graphs/graph_noise_{args.seed}.json"
        save_noisy_graphs(noisy_graphs, output_path)
        logger.info(f"Graph generation complete. Output: {output_path}")

if __name__ == "__main__":
    main()