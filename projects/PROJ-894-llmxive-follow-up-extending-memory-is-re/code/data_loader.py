"""
Data Loader Module.
Handles fetching the LoCoMo benchmark and generating synthetic noisy graphs.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import random

# Try to import datasets, if not available, we might need to handle it
# For this implementation, we assume datasets is installed as per requirements.txt
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install it via pip.")

logger = logging.getLogger(__name__)

RAW_DATA_PATH = Path("data/raw/locomo_raw.json")
NOISY_DATA_PATH = Path("data/raw/noisy_graphs.json")

def ensure_output_dirs():
    """Create necessary output directories."""
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

def fetch_locomo_dataset(split: str = "test", subset: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    
    Args:
        split: The dataset split to load (e.g., 'test').
        subset: Number of samples to fetch (for testing/development).
    
    Returns:
        List of dictionaries containing 'question', 'context', 'answer'.
    """
    logger.info(f"Fetching LoCoMo dataset (split={split}, subset={subset})...")
    
    try:
        # Using the actual dataset name if known, otherwise a placeholder
        # The task description mentions 'locomo/locomo-benchmark'.
        # If this specific dataset ID is incorrect, the fetch will fail loudly.
        dataset = load_dataset("locomo/locomo-benchmark", split=split, trust_remote_code=True)
        
        # Limit to subset for performance if needed
        if subset < len(dataset):
            dataset = dataset.select(range(subset))
        
        tasks = []
        for item in dataset:
            tasks.append({
                "task_id": f"locomo_{item.get('id', random.randint(0, 99999))}",
                "question": item.get("question", ""),
                "context": item.get("context", ""),
                "answer": item.get("answer", ""),
                "metadata": item
            })
        logger.info(f"Fetched {len(tasks)} tasks.")
        return tasks
    except Exception as e:
        logger.error(f"Failed to fetch LoCoMo dataset: {e}")
        # Fail loudly as per constraints
        raise RuntimeError(f"Cannot proceed without real data. Fetch failed: {e}")

def save_raw_data(tasks: List[Dict[str, Any]], path: Path = RAW_DATA_PATH):
    """Save raw tasks to JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw data to {path}")

def build_memory_graph(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a memory graph from a task's context.
    This is a simplified version for demonstration.
    In a real scenario, this would parse the context and build a complex graph.
    
    Returns a dict with 'nodes' and 'edges' for JSON serialization.
    """
    # Simple heuristic: create nodes from words/entities and edges from co-occurrence
    # This is a placeholder for the actual graph construction logic which might be in graph_utils
    context = task.get("context", "")
    words = context.split()
    
    nodes = list(set(words))
    edges = []
    
    # Create edges between consecutive words
    for i in range(len(words) - 1):
        edges.append((words[i], words[i+1]))
    
    # Add some random edges to simulate a graph structure
    for i in range(len(words) - 1):
        if random.random() < 0.1:
            j = random.randint(i+1, len(words)-1)
            edges.append((words[i], words[j]))
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def inject_noise(graph_data: Dict[str, Any], noise_ratio: float = 0.1) -> Dict[str, Any]:
    """
    Inject noise into the graph by adding random edges.
    
    Args:
        graph_data: Dictionary with 'nodes' and 'edges'.
        noise_ratio: Fraction of total possible edges to add as noise.
    
    Returns:
        Noisy graph data.
    """
    nodes = graph_data['nodes']
    existing_edges = set(tuple(sorted(e)) for e in graph_data['edges'])
    
    num_nodes = len(nodes)
    max_possible_edges = (num_nodes * (num_nodes - 1)) // 2
    num_noise_edges = int(max_possible_edges * noise_ratio)
    
    noise_edges = []
    attempts = 0
    while len(noise_edges) < num_noise_edges and attempts < num_noise_edges * 10:
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v:
            edge = tuple(sorted((u, v)))
            if edge not in existing_edges:
                noise_edges.append(edge)
                existing_edges.add(edge)
        attempts += 1
    
    return {
        "nodes": nodes,
        "edges": list(existing_edges)
    }

def generate_noisy_graphs(tasks: List[Dict[str, Any]], noise_ratio: float = 0.1, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate noisy graphs for all tasks.
    
    Args:
        tasks: List of raw tasks.
        noise_ratio: Ratio of noise to inject.
        seed: Random seed for reproducibility.
    
    Returns:
        List of tasks with noisy graph data attached.
    """
    random.seed(seed)
    noisy_tasks = []
    
    for task in tasks:
        graph = build_memory_graph(task)
        noisy_graph = inject_noise(graph, noise_ratio)
        
        noisy_task = task.copy()
        noisy_task['graph'] = noisy_graph
        noisy_task['noise_ratio'] = noise_ratio
        noisy_tasks.append(noisy_task)
    
    return noisy_tasks

def save_noisy_graphs(noisy_tasks: List[Dict[str, Any]], path: Path = NOISY_DATA_PATH):
    """Save noisy tasks to JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(noisy_tasks, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved noisy graphs to {path}")

def load_noisy_graphs(path: Path = NOISY_DATA_PATH) -> List[Dict[str, Any]]:
    """Load noisy graphs from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Noisy graphs not found at {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """Main entry point to fetch data and generate noisy graphs."""
    logging.basicConfig(level=logging.INFO)
    ensure_output_dirs()
    
    # Fetch real data
    tasks = fetch_locomo_dataset(subset=5) # Small subset for testing
    
    # Save raw
    save_raw_data(tasks)
    
    # Generate noisy
    noisy_tasks = generate_noisy_graphs(tasks, noise_ratio=0.1)
    save_noisy_graphs(noisy_tasks)
    
    logger.info("Data loading and noise generation complete.")

if __name__ == "__main__":
    main()