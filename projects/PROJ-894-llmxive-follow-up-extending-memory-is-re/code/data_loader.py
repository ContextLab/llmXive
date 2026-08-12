"""
data_loader.py

Handles downloading the LoCoMo benchmark, constructing memory graphs,
and generating noisy graph datasets.
"""

import os
import json
import logging
import hashlib
import random
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np
import spacy
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GRAPHS_DIR = DATA_PROCESSED_DIR / "graphs"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy 'en_core_web_sm' model not found. Please run: python -m spacy download en_core_web_sm")
    raise


def ensure_output_dirs():
    """Ensure all required output directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_locomo_dataset(subset: str = "test") -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.

    Args:
        subset: The dataset split to fetch (e.g., 'test', 'validation').

    Returns:
        A list of dictionaries containing the dataset rows.

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    logger.info(f"Fetching LoCoMo dataset (subset: {subset})...")
    try:
        # Attempt to load the dataset
        # Note: The task description mentioned 'locomo/locomo-benchmark' which might be incorrect.
        # We will try the canonical name 'locomo/locomo'. If that fails, we raise an error.
        # The execution failure log indicated 'locomo/locomo-benchmark' doesn't exist.
        # We will try 'locomo/locomo' first, as it is the likely correct canonical ID.
        dataset_path = "locomo/locomo"
        
        ds = load_dataset(dataset_path, split=subset)
        
        # Convert to list of dicts
        tasks = ds.to_list()
        
        logger.info(f"Successfully fetched {len(tasks)} tasks from {dataset_path} (split: {subset}).")
        return tasks
    except Exception as e:
        logger.error(f"Failed to fetch dataset '{dataset_path}': {e}")
        # Per T035, we must fail loudly, not fallback to synthetic.
        raise RuntimeError(f"Cannot proceed without real data. Fetch failed: {e}")


def save_raw_data(tasks: List[Dict[str, Any]], output_path: Optional[str] = None):
    """
    Save the raw dataset tasks to a CSV file.

    Args:
        tasks: List of task dictionaries.
        output_path: Path to the output CSV file. Defaults to data/raw/locomo.csv.
    """
    if output_path is None:
        output_path = DATA_RAW_DIR / "locomo.csv"
    else:
        output_path = Path(output_path)

    ensure_output_dirs()

    if not tasks:
        logger.warning("No tasks to save.")
        return

    # Determine columns
    columns = list(tasks[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(tasks)

    logger.info(f"Saved raw data to {output_path}")


def load_raw_data(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load raw dataset tasks from a CSV file.

    Args:
        input_path: Path to the input CSV file. Defaults to data/raw/locomo.csv.

    Returns:
        A list of dictionaries containing the dataset rows.
    """
    if input_path is None:
        input_path = DATA_RAW_DIR / "locomo.csv"
    else:
        input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {input_path}")

    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)

    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    return tasks


def build_memory_graph(context_text: str, task_id: str) -> nx.DiGraph:
    """
    Build a memory graph from the context text using NER and dependency parsing.

    Args:
        context_text: The context string from the task.
        task_id: Unique identifier for the task.

    Returns:
        A networkx DiGraph representing the memory graph.
    """
    G = nx.DiGraph()
    G.graph['task_id'] = task_id

    if not context_text or not context_text.strip():
        logger.warning(f"Empty context for task {task_id}. Returning empty graph.")
        return G

    try:
        doc = nlp(context_text)
    except Exception as e:
        logger.error(f"spaCy parsing failed for task {task_id}: {e}")
        return G

    # Simple rule-based extraction: Subject-Verb-Object triples
    # This is a simplified version. Real implementation might be more complex.
    for sent in doc.sents:
        for token in sent:
            if token.dep_ in ("nsubj", "nsubjpass"):
                subj = token
                verb = token.head
                obj = None
                for child in verb.children:
                    if child.dep_ in ("dobj", "attr", "oprd"):
                        obj = child
                        break
                
                if obj:
                    source_node = subj.text.lower().strip()
                    target_node = obj.text.lower().strip()
                    relation = verb.text.lower().strip()
                    
                    if source_node and target_node:
                        G.add_node(source_node)
                        G.add_node(target_node)
                        G.add_edge(source_node, target_node, relation=relation)
    
    logger.debug(f"Built graph for task {task_id} with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G


def save_graphs(graphs: Dict[str, nx.DiGraph], output_path: Optional[str] = None):
    """
    Save a dictionary of graphs to a JSON file.

    Args:
        graphs: Dictionary mapping task_id to nx.DiGraph.
        output_path: Path to the output JSON file.
    """
    if output_path is None:
        output_path = DATA_INTERMEDIATE_DIR / "graphs_raw.json"
    else:
        output_path = Path(output_path)

    ensure_output_dirs()

    # Convert graphs to serializable format
    serializable_graphs = {}
    for task_id, G in graphs.items():
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": str(u),
                "target": str(v),
                "relation_string": data.get("relation", "")
            })
        serializable_graphs[task_id] = edges

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_graphs, f, indent=2)

    logger.info(f"Saved {len(graphs)} graphs to {output_path}")


def load_graphs(input_path: Optional[str] = None) -> Dict[str, nx.DiGraph]:
    """
    Load graphs from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dictionary mapping task_id to nx.DiGraph.
    """
    if input_path is None:
        input_path = DATA_INTERMEDIATE_DIR / "graphs_raw.json"
    else:
        input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        serializable_graphs = json.load(f)

    graphs = {}
    for task_id, edges in serializable_graphs.items():
        G = nx.DiGraph()
        G.graph['task_id'] = task_id
        for edge in edges:
            G.add_edge(edge["source"], edge["target"], relation=edge["relation_string"])
        graphs[task_id] = G

    logger.info(f"Loaded {len(graphs)} graphs from {input_path}")
    return graphs


def inject_noise(graph: nx.DiGraph, ratio: float, seed: int) -> nx.DiGraph:
    """
    Inject noise into a graph by replacing a proportion of edges with random edges.

    Args:
        graph: The input nx.DiGraph.
        ratio: The proportion of edges to replace (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        A new nx.DiGraph with injected noise.

    Raises:
        ValueError: If ratio is not between 0 and 1.
    """
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"Ratio must be between 0 and 1, got {ratio}")

    random.seed(seed)
    np.random.seed(seed)

    # Create a copy to avoid modifying the original
    noisy_G = graph.copy()
    
    edges = list(noisy_G.edges())
    if not edges:
        return noisy_G

    num_edges_to_replace = max(1, int(len(edges) * ratio))
    if num_edges_to_replace == 0:
        return noisy_G

    # Select edges to remove
    edges_to_remove = random.sample(edges, num_edges_to_replace)
    
    # Remove selected edges
    for u, v in edges_to_remove:
        noisy_G.remove_edge(u, v)

    # Generate new random edges
    nodes = list(noisy_G.nodes())
    if len(nodes) < 2:
        return noisy_G

    # Potential new edges: all pairs (u, v) where u != v and (u, v) is not in graph
    current_edges_set = set(noisy_G.edges())
    potential_edges = []
    for u in nodes:
        for v in nodes:
            if u != v and (u, v) not in current_edges_set:
                potential_edges.append((u, v))
    
    if not potential_edges:
        # Graph is fully connected (or close to), can't add more without self-loops or duplicates
        logger.warning("Cannot add more edges without self-loops or duplicates.")
        return noisy_G

    # Select random edges to add
    num_to_add = min(num_edges_to_replace, len(potential_edges))
    edges_to_add = random.sample(potential_edges, num_to_add)

    for u, v in edges_to_add:
        noisy_G.add_edge(u, v, relation="NOISE_INJECTED")

    return noisy_G


def generate_noisy_graphs(raw_graphs: Dict[str, nx.DiGraph], ratio: float, seed: int, output_path: Optional[str] = None) -> Dict[str, nx.DiGraph]:
    """
    Generate noisy versions of the input graphs.

    Args:
        raw_graphs: Dictionary mapping task_id to original nx.DiGraph.
        ratio: Noise injection ratio.
        seed: Random seed.
        output_path: Path to save the noisy graphs.

    Returns:
        Dictionary mapping task_id to noisy nx.DiGraph.
    """
    noisy_graphs = {}
    for task_id, G in raw_graphs.items():
        noisy_G = inject_noise(G, ratio, seed)
        noisy_graphs[task_id] = noisy_G
        logger.debug(f"Generated noisy graph for task {task_id} (seed={seed}, ratio={ratio})")

    if output_path:
        save_noisy_graphs(noisy_graphs, output_path)

    return noisy_graphs


def save_noisy_graphs(noisy_graphs: Dict[str, nx.DiGraph], output_path: Optional[str] = None):
    """
    Save noisy graphs to a JSON file.

    Args:
        noisy_graphs: Dictionary mapping task_id to noisy nx.DiGraph.
        output_path: Path to the output JSON file.
    """
    if output_path is None:
        output_path = GRAPHS_DIR / "graph_noise_42.json"
    else:
        output_path = Path(output_path)

    ensure_output_dirs()

    # Convert graphs to serializable format
    serializable_graphs = {}
    for task_id, G in noisy_graphs.items():
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": str(u),
                "target": str(v),
                "relation_string": data.get("relation", "")
            })
        serializable_graphs[task_id] = edges

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_graphs, f, indent=2)

    logger.info(f"Saved {len(noisy_graphs)} noisy graphs to {output_path}")


def load_noisy_graphs(input_path: Optional[str] = None) -> Dict[str, nx.DiGraph]:
    """
    Load noisy graphs from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dictionary mapping task_id to noisy nx.DiGraph.
    """
    if input_path is None:
        input_path = GRAPHS_DIR / "graph_noise_42.json"
    else:
        input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Noisy graphs file not found at {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        serializable_graphs = json.load(f)

    graphs = {}
    for task_id, edges in serializable_graphs.items():
        G = nx.DiGraph()
        G.graph['task_id'] = task_id
        for edge in edges:
            G.add_edge(edge["source"], edge["target"], relation=edge["relation_string"])
        graphs[task_id] = G

    logger.info(f"Loaded {len(graphs)} noisy graphs from {input_path}")
    return graphs


def process_in_chunks(tasks: List[Dict[str, Any]], chunk_size: int = 100):
    """
    Process tasks in chunks to manage memory.

    Args:
        tasks: List of tasks.
        chunk_size: Number of tasks per chunk.

    Yields:
        Chunks of tasks.
    """
    for i in range(0, len(tasks), chunk_size):
        yield tasks[i:i + chunk_size]


def main():
    """
    Main entry point for the data loader script.
    
    Usage:
        python code/data_loader.py --download --generate-graphs --seed 42
    """
    parser = argparse.ArgumentParser(description="Data loader for LoCoMo benchmark")
    parser.add_argument("--download", action="store_true", help="Download the LoCoMo dataset")
    parser.add_argument("--generate-graphs", action="store_true", help="Build memory graphs from raw data")
    parser.add_argument("--generate-noisy", action="store_true", help="Generate noisy graphs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for noise injection")
    parser.add_argument("--noise-ratio", type=float, default=0.1, help="Noise injection ratio (0.0 to 1.0)")
    parser.add_argument("--subset", type=str, default="test", help="Dataset split to fetch")
    parser.add_argument("--chunk-size", type=int, default=100, help="Chunk size for processing")

    args = parser.parse_args()

    if args.download:
        logger.info("Starting download...")
        tasks = fetch_locomo_dataset(subset=args.subset)
        save_raw_data(tasks)
        logger.info("Download complete.")
    
    if args.generate_graphs:
        logger.info("Starting graph generation...")
        tasks = load_raw_data()
        all_graphs = {}
        
        for chunk in process_in_chunks(tasks, args.chunk_size):
            for task in chunk:
                task_id = task.get("id", task.get("task_id", str(hash(task.get("question", "")))))
                context = task.get("context", "")
                G = build_memory_graph(context, str(task_id))
                all_graphs[str(task_id)] = G
        
        save_graphs(all_graphs)
        logger.info("Graph generation complete.")

    if args.generate_noisy:
        logger.info("Starting noisy graph generation...")
        raw_graphs = load_graphs()
        noisy_graphs = generate_noisy_graphs(
            raw_graphs, 
            ratio=args.noise_ratio, 
            seed=args.seed,
            output_path=GRAPHS_DIR / f"graph_noise_{args.seed}.json"
        )
        logger.info(f"Noisy graph generation complete. Output: {GRAPHS_DIR / f'graph_noise_{args.seed}.json'}")


if __name__ == "__main__":
    main()
