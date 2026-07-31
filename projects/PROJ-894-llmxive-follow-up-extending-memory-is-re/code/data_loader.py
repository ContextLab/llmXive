"""
Data loading module for llmXive project.
Handles fetching the LoCoMo benchmark dataset from HuggingFace and processing it.
"""
import os
import json
import logging
import hashlib
import random
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

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

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GRAPHS_DIR = PROCESSED_DATA_DIR / "graphs"

# Constants
DATASET_ID = "locomo/locomo-benchmark"
DEFAULT_SEED = 42

def ensure_output_dirs():
    """Create necessary output directories if they don't exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directories exist: {RAW_DATA_DIR}, {PROCESSED_DATA_DIR}, {GRAPHS_DIR}")

def fetch_locomo_dataset(subset: Optional[int] = None, streaming: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    
    Args:
        subset: Optional number of tasks to fetch. If None, fetches all.
        streaming: If True, streams the dataset instead of loading it all into memory.
        
    Returns:
        List of dictionaries containing 'question', 'context', 'answer', and 'task_id'.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    ensure_output_dirs()
    logger.info(f"Fetching LoCoMo dataset: {DATASET_ID}")
    
    try:
        if streaming:
            logger.info("Using streaming mode for dataset loading")
            ds = load_dataset(DATASET_ID, split="test", streaming=True)
            # Convert to list for the subset, but only if subset is specified
            if subset is not None:
                tasks = list(ds.take(subset))
            else:
                # For streaming without subset, we iterate and process on the fly
                # For this function, we return an iterator or a limited list
                tasks = list(ds)
        else:
            logger.info("Loading dataset into memory")
            ds = load_dataset(DATASET_ID, split="test")
            if subset is not None:
                tasks = ds.select(range(min(subset, len(ds)))).to_list()
            else:
                tasks = ds.to_list()
        
        # Ensure we have the required columns
        required_cols = ['question', 'context', 'answer']
        for task in tasks:
            if not all(col in task for col in required_cols):
                missing = [col for col in required_cols if col not in task]
                raise ValueError(f"Task missing required columns: {missing}")
            # Add task_id if not present
            if 'task_id' not in task:
                task['task_id'] = f"locomo_{hashlib.md5(task['question'].encode()).hexdigest()[:8]}"
        
        logger.info(f"Fetched {len(tasks)} tasks from LoCoMo dataset")
        return tasks
        
    except Exception as e:
        logger.error(f"Failed to fetch LoCoMo dataset: {e}")
        # Re-raise to fail loudly as per T035 requirement
        raise RuntimeError(f"Cannot proceed without real data. Fetch failed: {e}")

def save_raw_data(tasks: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save raw task data to a CSV file.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Optional path to save the CSV. Defaults to data/raw/locomo.csv.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "locomo.csv"
    
    ensure_output_dirs()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if not tasks:
            logger.warning("No tasks to save")
            return
        
        fieldnames = ['task_id', 'question', 'context', 'answer']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in tasks:
            # Ensure all fields are present and strings
            row = {
                'task_id': task.get('task_id', ''),
                'question': task.get('question', ''),
                'context': task.get('context', ''),
                'answer': task.get('answer', '')
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def build_memory_graph(tasks: List[Dict[str, Any]], seed: int = DEFAULT_SEED) -> nx.DiGraph:
    """
    Build a memory graph from the tasks.
    This is a simplified version for demonstration; in a real scenario,
    the graph construction would be based on entity relationships in the context.
    
    Args:
        tasks: List of task dictionaries.
        seed: Random seed for reproducibility.
        
    Returns:
        A directed graph representing the memory structure.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    G = nx.DiGraph()
    
    # Create nodes for each task's entities (simplified: use task_id as node)
    for task in tasks:
        task_id = task.get('task_id', '')
        G.add_node(task_id, type='task', question=task['question'], answer=task['answer'])
        
        # Extract entities from context (simplified: split by space and filter)
        context = task.get('context', '')
        entities = [e for e in context.split() if len(e) > 2]
        
        for entity in entities:
            entity_node = f"entity_{hashlib.md5(entity.encode()).hexdigest()[:8]}"
            if entity_node not in G:
                G.add_node(entity_node, type='entity', name=entity)
            G.add_edge(entity_node, task_id, type='mentions')
        
        # Connect entities within the same context
        for i in range(len(entities) - 1):
            entity1 = f"entity_{hashlib.md5(entities[i].encode()).hexdigest()[:8]}"
            entity2 = f"entity_{hashlib.md5(entities[i+1].encode()).hexdigest()[:8]}"
            if G.has_node(entity1) and G.has_node(entity2):
                G.add_edge(entity1, entity2, type='co_occurrence')
    
    logger.info(f"Built memory graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def inject_noise(graph: nx.DiGraph, ratio: float = 0.1, seed: int = DEFAULT_SEED) -> nx.DiGraph:
    """
    Inject noise into the graph by replacing a proportion of edges with random edges.
    
    Args:
        graph: The input graph.
        ratio: The proportion of edges to replace.
        seed: Random seed for reproducibility.
        
    Returns:
        A new graph with injected noise.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    G = graph.copy()
    nodes = list(G.nodes())
    if len(nodes) < 2:
        logger.warning("Graph has too few nodes to inject noise")
        return G
    
    edges = list(G.edges())
    num_edges_to_replace = int(len(edges) * ratio)
    
    if num_edges_to_replace == 0:
        logger.info("No edges to replace (ratio too low or graph too small)")
        return G
    
    # Select edges to remove
    edges_to_remove = random.sample(edges, num_edges_to_replace)
    
    # Create new random edges
    new_edges = []
    for _ in range(num_edges_to_replace):
        # Ensure we don't create self-loops or duplicate edges
        while True:
            src = random.choice(nodes)
            dst = random.choice(nodes)
            if src != dst and not G.has_edge(src, dst):
                # Avoid creating edges that were just removed to maintain randomness
                if (src, dst) not in edges_to_remove:
                    new_edges.append((src, dst))
                    break
    
    # Remove old edges and add new ones
    G.remove_edges_from(edges_to_remove)
    G.add_edges_from(new_edges)
    
    logger.info(f"Injected noise: removed {len(edges_to_remove)} edges, added {len(new_edges)} edges")
    return G

def generate_noisy_graphs(graph: nx.DiGraph, noise_ratios: List[float] = [0.1], seed: int = DEFAULT_SEED) -> Dict[float, nx.DiGraph]:
    """
    Generate multiple noisy versions of the graph with different noise ratios.
    
    Args:
        graph: The input graph.
        noise_ratios: List of noise ratios to apply.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary mapping noise ratio to noisy graph.
    """
    noisy_graphs = {}
    for ratio in noise_ratios:
        noisy_graph = inject_noise(graph, ratio=ratio, seed=seed)
        noisy_graphs[ratio] = noisy_graph
        logger.info(f"Generated noisy graph with ratio {ratio}")
    return noisy_graphs

def save_noisy_graphs(noisy_graphs: Dict[float, nx.DiGraph], output_dir: Optional[Path] = None):
    """
    Save noisy graphs to JSON files.
    
    Args:
        noisy_graphs: Dictionary mapping noise ratio to graph.
        output_dir: Optional output directory. Defaults to data/processed/graphs/.
    """
    if output_dir is None:
        output_dir = GRAPHS_DIR
    
    ensure_output_dirs()
    
    for ratio, graph in noisy_graphs.items():
        output_path = output_dir / f"graph_noise_{int(ratio * 100)}.json"
        
        # Convert graph to serializable format
        data = nx.node_link_data(graph)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved noisy graph (ratio={ratio}) to {output_path}")

def load_noisy_graphs(input_dir: Optional[Path] = None) -> Dict[float, nx.DiGraph]:
    """
    Load noisy graphs from JSON files.
    
    Args:
        input_dir: Optional input directory. Defaults to data/processed/graphs/.
        
    Returns:
        Dictionary mapping noise ratio to graph.
    """
    if input_dir is None:
        input_dir = GRAPHS_DIR
    
    noisy_graphs = {}
    
    for file_path in input_dir.glob("graph_noise_*.json"):
        # Extract ratio from filename
        filename = file_path.stem
        # Expected format: graph_noise_XX where XX is ratio * 100
        try:
            ratio_str = filename.split('_')[-1]
            ratio = int(ratio_str) / 100.0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            graph = nx.node_link_graph(data)
            noisy_graphs[ratio] = graph
            logger.info(f"Loaded noisy graph (ratio={ratio}) from {file_path}")
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    return noisy_graphs

def main():
    """
    Main function to download LoCoMo dataset and generate noisy graphs.
    Usage: python code/data_loader.py --download --generate-graphs --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download LoCoMo benchmark and generate noisy graphs")
    parser.add_argument('--download', action='store_true', help="Download the LoCoMo dataset")
    parser.add_argument('--generate-graphs', action='store_true', help="Generate noisy graphs")
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument('--subset', type=int, default=None, help="Number of tasks to fetch (for testing)")
    parser.add_argument('--noise-ratios', type=float, nargs='+', default=[0.1], help="Noise ratios to apply")
    
    args = parser.parse_args()
    
    tasks = []
    graph = None
    
    if args.download:
        logger.info("Downloading LoCoMo dataset...")
        tasks = fetch_locomo_dataset(subset=args.subset)
        save_raw_data(tasks)
        logger.info("Dataset downloaded and saved.")
    
    if args.generate_graphs:
        if not tasks:
            # Load from CSV if tasks not fetched yet
            csv_path = RAW_DATA_DIR / "locomo.csv"
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    tasks = list(reader)
                logger.info(f"Loaded {len(tasks)} tasks from CSV.")
            else:
                logger.error("No tasks found. Please download the dataset first.")
                return
        
        logger.info("Building memory graph...")
        graph = build_memory_graph(tasks, seed=args.seed)
        
        logger.info("Generating noisy graphs...")
        noisy_graphs = generate_noisy_graphs(graph, noise_ratios=args.noise_ratios, seed=args.seed)
        save_noisy_graphs(noisy_graphs)
        logger.info("Noisy graphs generated and saved.")

if __name__ == "__main__":
    main()