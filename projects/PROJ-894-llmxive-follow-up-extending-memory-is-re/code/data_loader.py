import os
import json
import logging
import hashlib
import random
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx
import numpy as np
from datasets import load_dataset
import spacy
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
PROCESSED_DIR = DATA_DIR / "processed"
GRAPHS_DIR = PROCESSED_DIR / "graphs"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

def fetch_locomo_dataset(subset: str = "test") -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    
    Args:
        subset: The split to fetch (e.g., 'test', 'train').
        
    Returns:
        A list of dictionaries containing the dataset rows.
        
    Raises:
        ValueError: If the dataset fetch fails.
    """
    logger.info(f"Fetching LoCoMo dataset (subset: {subset})...")
    try:
        # Attempt to load the specific dataset ID as per spec
        # Note: If the canonical ID has changed, this will raise DatasetNotFoundError
        # which we catch and re-raise as ValueError per T035/T011a requirements.
        ds = load_dataset("locomo/locomo-benchmark", split=subset)
        
        # Convert to list of dicts for easier processing
        tasks = []
        for row in ds:
            tasks.append({
                "task_id": row.get("id", f"task_{len(tasks)}"),
                "question": row.get("question", ""),
                "context": row.get("context", ""),
                "answer": row.get("answer", "")
            })
        
        logger.info(f"Successfully fetched {len(tasks)} tasks.")
        return tasks
    except Exception as e:
        # Per T035 and T011a: Fail loudly, do not fallback to synthetic
        error_msg = f"Dataset fetch failed: {e}"
        logger.error(error_msg)
        raise ValueError("Dataset fetch failed") from e

def save_raw_data(tasks: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Save raw tasks to a CSV file.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Path to the output CSV file. Defaults to data/raw/locomo.csv.
    """
    if output_path is None:
        output_path = RAW_DIR / "locomo.csv"
        
    logger.info(f"Saving raw data to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "question", "context", "answer"])
        writer.writeheader()
        writer.writerows(tasks)
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def load_raw_data(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load raw tasks from a CSV file.
    
    Args:
        input_path: Path to the input CSV file. Defaults to data/raw/locomo.csv.
        
    Returns:
        List of task dictionaries.
    """
    if input_path is None:
        input_path = RAW_DIR / "locomo.csv"
        
    tasks = []
    logger.info(f"Loading raw data from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    logger.info(f"Loaded {len(tasks)} tasks.")
    return tasks

def build_memory_graph(context: str, task_id: str) -> nx.DiGraph:
    """
    Build a memory graph from a context string using NER and dependency parsing.
    
    Args:
        context: The context string to parse.
        task_id: The ID of the task (for logging).
        
    Returns:
        A directed graph representing the memory.
    """
    # Load spaCy model (assuming 'en_core_web_sm' is installed)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.error("spaCy 'en_core_web_sm' model not found. Please install it with: python -m spacy download en_core_web_sm")
        raise

    doc = nlp(context)
    G = nx.DiGraph()
    
    # Simple rule-based extraction: Subject-Verb-Object triples
    # This is a simplified version; a robust implementation would use more complex heuristics
    for sent in doc.sents:
        for token in sent:
            if token.dep_ == "nsubj":
                subj = token.head
                obj = None
                rel = "nsubj"
                for child in token.head.children:
                    if child.dep_ == "dobj" or child.dep_ == "attr":
                        obj = child
                        break
                
                if subj and obj:
                    source = subj.text.lower()
                    target = obj.text.lower()
                    relation = rel
                    G.add_edge(source, target, relation=relation)
                    G.add_node(source)
                    G.add_node(target)
            
            # Also handle passive voice or other relations if needed
            # For now, we stick to the basic SVO pattern as per spec T011a-1

    logger.debug(f"Built graph for task {task_id} with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

def save_graphs(graphs: Dict[str, nx.DiGraph], output_path: Optional[Path] = None) -> None:
    """
    Save graphs to a JSON file.
    
    Args:
        graphs: Dictionary mapping task_id to graph.
        output_path: Path to the output JSON file. Defaults to data/intermediate/graphs_raw.json.
    """
    if output_path is None:
        output_path = INTERMEDIATE_DIR / "graphs_raw.json"
        
    logger.info(f"Saving graphs to {output_path}...")
    data = {}
    for task_id, G in graphs.items():
        edges = []
        for u, v, data_edge in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation_string": data_edge.get("relation", "unknown")
            })
        data[task_id] = edges
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")

def load_graphs(input_path: Optional[Path] = None) -> Dict[str, nx.DiGraph]:
    """
    Load graphs from a JSON file.
    
    Args:
        input_path: Path to the input JSON file. Defaults to data/intermediate/graphs_raw.json.
        
    Returns:
        Dictionary mapping task_id to graph.
    """
    if input_path is None:
        input_path = INTERMEDIATE_DIR / "graphs_raw.json"
        
    logger.info(f"Loading graphs from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    graphs = {}
    for task_id, edges in data.items():
        G = nx.DiGraph()
        for edge in edges:
            G.add_edge(edge["source"], edge["target"], relation=edge.get("relation_string", "unknown"))
        graphs[task_id] = G
        
    logger.info(f"Loaded {len(graphs)} graphs.")
    return graphs

def inject_noise(graph: nx.DiGraph, ratio: float, seed: int) -> nx.DiGraph:
    """
    Inject noise into a graph by replacing a proportion of edges with random edges.
    
    Args:
        graph: The input graph.
        ratio: The proportion of edges to replace (0.0 to 1.0).
        seed: Random seed for reproducibility.
        
    Returns:
        A new graph with injected noise.
        
    Raises:
        ValueError: If ratio is invalid.
    """
    if ratio < 0.0 or ratio > 1.0:
        raise ValueError(f"Ratio must be between 0.0 and 1.0, got {ratio}")
        
    random.seed(seed)
    np.random.seed(seed)
    
    # Create a copy to avoid modifying the original
    noisy_G = graph.copy()
    nodes = list(noisy_G.nodes())
    n_nodes = len(nodes)
    
    if n_nodes < 2:
        logger.warning(f"Graph for seed {seed} has fewer than 2 nodes, cannot inject noise.")
        return noisy_G
        
    original_edges = list(noisy_G.edges())
    n_edges = len(original_edges)
    
    if n_edges == 0:
        logger.warning(f"Graph for seed {seed} has no edges, cannot inject noise.")
        return noisy_G
        
    # Calculate number of edges to replace
    n_replace = int(n_edges * ratio)
    
    if n_replace == 0:
        logger.info(f"Ratio {ratio} results in 0 edges to replace for seed {seed}.")
        return noisy_G
        
    # Select edges to remove
    edges_to_remove = random.sample(original_edges, n_replace)
    
    # Remove selected edges
    for u, v in edges_to_remove:
        noisy_G.remove_edge(u, v)
        
    # Generate new random edges
    # We need to find potential edges that are not already in the graph and are not self-loops
    current_edges = set(noisy_G.edges())
    potential_edges = []
    
    for u in nodes:
        for v in nodes:
            if u != v and (u, v) not in current_edges:
                potential_edges.append((u, v))
    
    if not potential_edges:
        logger.warning(f"No potential edges to add for seed {seed}.")
        return noisy_G
        
    # Sample new edges to add
    n_add = min(n_replace, len(potential_edges))
    edges_to_add = random.sample(potential_edges, n_add)
    
    # Add new edges
    for u, v in edges_to_add:
        noisy_G.add_edge(u, v, relation="noisy")
        
    logger.info(f"Injected noise: removed {len(edges_to_remove)} edges, added {len(edges_to_add)} edges for seed {seed}.")
    return noisy_G

def generate_noisy_graphs(graphs: Dict[str, nx.DiGraph], ratio: float = 0.1, seed: int = 42) -> Dict[str, nx.DiGraph]:
    """
    Generate noisy versions of the input graphs.
    
    Args:
        graphs: Dictionary mapping task_id to graph.
        ratio: Noise ratio (default 0.1).
        seed: Random seed (default 42).
        
    Returns:
        Dictionary mapping task_id to noisy graph.
    """
    logger.info(f"Generating noisy graphs with ratio={ratio}, seed={seed}...")
    noisy_graphs = {}
    
    for task_id, G in tqdm(graphs.items(), desc="Injecting noise"):
        noisy_G = inject_noise(G, ratio, seed)
        noisy_graphs[task_id] = noisy_G
        
    logger.info(f"Generated {len(noisy_graphs)} noisy graphs.")
    return noisy_graphs

def save_noisy_graphs(noisy_graphs: Dict[str, nx.DiGraph], output_path: Optional[Path] = None) -> None:
    """
    Save noisy graphs to a JSON file.
    
    Args:
        noisy_graphs: Dictionary mapping task_id to noisy graph.
        output_path: Path to the output JSON file. Defaults to data/processed/graphs/graph_noise_42.json.
    """
    if output_path is None:
        output_path = GRAPHS_DIR / "graph_noise_42.json"
        
    logger.info(f"Saving noisy graphs to {output_path}...")
    data = {}
    for task_id, G in noisy_graphs.items():
        edges = []
        for u, v, data_edge in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation_string": data_edge.get("relation", "unknown")
            })
        data[task_id] = edges
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(noisy_graphs)} noisy graphs to {output_path}")

def load_noisy_graphs(input_path: Optional[Path] = None) -> Dict[str, nx.DiGraph]:
    """
    Load noisy graphs from a JSON file.
    
    Args:
        input_path: Path to the input JSON file. Defaults to data/processed/graphs/graph_noise_42.json.
        
    Returns:
        Dictionary mapping task_id to noisy graph.
    """
    if input_path is None:
        input_path = GRAPHS_DIR / "graph_noise_42.json"
        
    logger.info(f"Loading noisy graphs from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    graphs = {}
    for task_id, edges in data.items():
        G = nx.DiGraph()
        for edge in edges:
            G.add_edge(edge["source"], edge["target"], relation=edge.get("relation_string", "unknown"))
        graphs[task_id] = G
        
    logger.info(f"Loaded {len(graphs)} noisy graphs.")
    return graphs

def process_in_chunks(tasks: List[Dict[str, Any]], chunk_size: int = 100) -> List[List[Dict[str, Any]]]:
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
    Handles downloading, graph construction, and noise injection.
    """
    parser = argparse.ArgumentParser(description="LoCoMo Data Loader and Graph Generator")
    parser.add_argument("--download", action="store_true", help="Download the LoCoMo dataset")
    parser.add_argument("--generate-graphs", action="store_true", help="Build memory graphs from context")
    parser.add_argument("--inject-noise", action="store_true", help="Inject noise into graphs")
    parser.add_argument("--subset", type=str, default="test", help="Dataset subset to fetch")
    parser.add_argument("--noise-ratio", type=float, default=0.1, help="Noise injection ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for noise injection")
    
    args = parser.parse_args()
    
    tasks = []
    graphs = {}
    noisy_graphs = {}
    
    # Step 1: Download data if requested
    if args.download:
        tasks = fetch_locomo_dataset(subset=args.subset)
        save_raw_data(tasks)
        
    # Load raw data if it exists (from previous download or manual placement)
    if not tasks and (RAW_DIR / "locomo.csv").exists():
        tasks = load_raw_data()
        
    if not tasks:
        logger.error("No tasks found. Please run with --download first.")
        return
        
    # Step 2: Build graphs if requested
    if args.generate_graphs:
        logger.info("Building memory graphs...")
        for task in tqdm(tasks, desc="Building graphs"):
            task_id = task["task_id"]
            context = task["context"]
            G = build_memory_graph(context, task_id)
            graphs[task_id] = G
        save_graphs(graphs)
        
    # Load graphs if they exist (from previous run)
    if not graphs and (INTERMEDIATE_DIR / "graphs_raw.json").exists():
        graphs = load_graphs()
        
    if not graphs:
        logger.error("No graphs found. Please run with --generate-graphs first.")
        return
        
    # Step 3: Inject noise if requested
    if args.inject_noise:
        logger.info(f"Injecting noise with ratio={args.noise_ratio}, seed={args.seed}...")
        noisy_graphs = generate_noisy_graphs(graphs, ratio=args.noise_ratio, seed=args.seed)
        save_noisy_graphs(noisy_graphs, output_path=GRAPHS_DIR / f"graph_noise_{args.seed}.json")
        
    # Load noisy graphs if they exist (from previous run)
    if not noisy_graphs and (GRAPHS_DIR / f"graph_noise_{args.seed}.json").exists():
        noisy_graphs = load_noisy_graphs()
        
    logger.info("Data loading and graph generation complete.")

if __name__ == "__main__":
    main()
