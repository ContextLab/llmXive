"""
Data Loader module for fetching and processing LoCoMo benchmark data.
"""

import os
import json
import logging
import hashlib
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("datasets library not available. Some functionality will be disabled.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RAW_DATA_PATH = Path("data/raw/locomo.jsonl")
INTERMEDIATE_PATH = Path("data/intermediate/graphs_raw.json")
PROCESSED_PATH = Path("data/processed/graphs")

def ensure_output_dirs():
    """Create output directories if they don't exist."""
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

def fetch_locomo_dataset(subset: str = "test") -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.

    Args:
        subset: The subset to fetch (e.g., 'test').

    Returns:
        List of task dictionaries.

    Raises:
        ValueError: If the dataset cannot be fetched or has incorrect schema.
    """
    if not DATASETS_AVAILABLE:
        raise ImportError("datasets library is required to fetch LoCoMo dataset")

    logger.info(f"Fetching LoCoMo dataset (subset: {subset})...")
    
    try:
        # Use the canonical dataset name
        dataset = load_dataset("locomo/locomo-benchmark", split=subset, trust_remote_code=True)
    except Exception as e:
        # Fallback to a known working dataset if the original fails
        logger.warning(f"Failed to fetch 'locomo/locomo-benchmark': {e}")
        logger.info("Trying alternative source: 'mlabonne/locomo'")
        try:
            dataset = load_dataset("mlabonne/locomo", split=subset, trust_remote_code=False)
        except Exception as e2:
            logger.error(f"Alternative source also failed: {e2}")
            raise ValueError(f"Dataset fetch failed for both sources: {e} and {e2}") from e2

    # Convert to list of dicts
    tasks = dataset.to_list()

    # Verify schema
    required_columns = ['question', 'context', 'answer']
    if tasks:
        missing_cols = [col for col in required_columns if col not in tasks[0]]
        if missing_cols:
            raise ValueError(f"Dataset schema mismatch: missing columns {missing_cols}")

    logger.info(f"Fetched {len(tasks)} tasks from LoCoMo dataset.")
    return tasks

def save_raw_data(tasks: List[Dict[str, Any]], output_path: Path = RAW_DATA_PATH):
    """
    Save raw tasks to a JSONL file.

    Args:
        tasks: List of task dictionaries.
        output_path: Path to the output file.
    """
    ensure_output_dirs()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def load_raw_data(input_path: Path = RAW_DATA_PATH) -> List[Dict[str, Any]]:
    """
    Load raw tasks from a JSONL file.

    Args:
        input_path: Path to the input file.

    Returns:
        List of task dictionaries.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {input_path}")

    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    return tasks

def extract_traces_from_context(context: str) -> List[Dict[str, str]]:
    """
    Extract subject-verb-object triples from context text.

    Args:
        context: The context text.

    Returns:
        List of triple dictionaries.
    """
    # Simplified extraction (real implementation would use spaCy)
    # This is a placeholder for the actual NER/dependency parsing logic
    triples = []
    
    # Example: split by sentences and extract simple patterns
    sentences = context.split('.')
    for sent in sentences:
        words = sent.strip().split()
        if len(words) >= 3:
            triples.append({
                'subject': words[0],
                'verb': words[1] if len(words) > 1 else '',
                'object': ' '.join(words[2:]) if len(words) > 2 else ''
            })
    
    return triples

def build_memory_graph(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a memory graph from tasks.

    Args:
        tasks: List of task dictionaries.

    Returns:
        Dictionary mapping task_id to graph data.
    """
    graphs = {}
    
    for task in tasks:
        task_id = task.get('task_id', f"task_{len(graphs)}")
        context = task.get('context', '')
        
        # Extract triples
        triples = extract_traces_from_context(context)
        
        # Build graph
        edges = []
        for i, triple in enumerate(triples):
            source = f"{triple['subject']}_{i}"
            target = f"{triple['object']}_{i}"
            edges.append({
                'source': source,
                'target': target,
                'relation_string': triple['verb']
            })
        
        graphs[task_id] = {
            'edges': edges,
            'nodes': list(set([e['source'] for e in edges] + [e['target'] for e in edges]))
        }
    
    return graphs

def save_graphs(graphs: Dict[str, Any], output_path: Path = INTERMEDIATE_PATH):
    """
    Save graphs to a JSON file.

    Args:
        graphs: Dictionary of task_id to graph data.
        output_path: Path to the output file.
    """
    ensure_output_dirs()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graphs, f, indent=2)
    
    logger.info(f"Saved graphs for {len(graphs)} tasks to {output_path}")

def load_graphs(input_path: Path = INTERMEDIATE_PATH) -> Dict[str, Any]:
    """
    Load graphs from a JSON file.

    Args:
        input_path: Path to the input file.

    Returns:
        Dictionary of task_id to graph data.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def inject_noise(graph: Dict[str, Any], ratio: float = 0.1, seed: int = 42) -> Dict[str, Any]:
    """
    Inject noise into a graph by replacing edges.

    Args:
        graph: The graph data dictionary.
        ratio: The ratio of edges to replace.
        seed: Random seed for reproducibility.

    Returns:
        Noisy graph data dictionary.
    """
    random.seed(seed)
    
    edges = graph.get('edges', [])
    if not edges:
        return graph
    
    num_to_replace = int(len(edges) * ratio)
    indices_to_replace = random.sample(range(len(edges)), min(num_to_replace, len(edges)))
    
    noisy_edges = edges.copy()
    all_nodes = graph.get('nodes', [])
    
    for idx in indices_to_replace:
        # Create a random edge
        if len(all_nodes) >= 2:
            source = random.choice(all_nodes)
            target = random.choice([n for n in all_nodes if n != source])
            noisy_edges[idx] = {
                'source': source,
                'target': target,
                'relation_string': 'noise'
            }
    
    return {
        'edges': noisy_edges,
        'nodes': all_nodes
    }

def generate_noisy_graphs(graphs: Dict[str, Any], ratio: float = 0.1, seed: int = 42) -> Dict[str, Any]:
    """
    Generate noisy versions of all graphs.

    Args:
        graphs: Dictionary of task_id to graph data.
        ratio: The ratio of edges to replace.
        seed: Random seed.

    Returns:
        Dictionary of task_id to noisy graph data.
    """
    noisy_graphs = {}
    for task_id, graph in graphs.items():
        noisy_graphs[task_id] = inject_noise(graph, ratio, seed)
    return noisy_graphs

def save_noisy_graphs(noisy_graphs: Dict[str, Any], output_path: Path = PROCESSED_PATH / "graph_noise_42.json"):
    """
    Save noisy graphs to a JSON file.

    Args:
        noisy_graphs: Dictionary of task_id to noisy graph data.
        output_path: Path to the output file.
    """
    ensure_output_dirs()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(noisy_graphs, f, indent=2)
    
    logger.info(f"Saved noisy graphs for {len(noisy_graphs)} tasks to {output_path}")

def load_noisy_graphs(input_path: Path = PROCESSED_PATH / "graph_noise_42.json") -> Dict[str, Any]:
    """
    Load noisy graphs from a JSON file.

    Args:
        input_path: Path to the input file.

    Returns:
        Dictionary of task_id to noisy graph data.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Noisy graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_in_chunks(tasks: List[Dict[str, Any]], chunk_size: int = 100):
    """
    Process tasks in chunks.

    Args:
        tasks: List of task dictionaries.
        chunk_size: Number of tasks per chunk.
    """
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        # Process chunk
        logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} tasks)")

def estimate_dataset_size(dataset_name: str) -> int:
    """
    Estimate the size of a dataset in bytes.

    Args:
        dataset_name: The name of the dataset.

    Returns:
        Estimated size in bytes.
    """
    # Placeholder implementation
    return 1000000  # 1 MB

def main():
    """Main entry point for data loading."""
    import argparse

    parser = argparse.ArgumentParser(description="Load and process LoCoMo dataset.")
    parser.add_argument('--download', action='store_true', help="Download the dataset")
    parser.add_argument('--subset', type=str, default="test", help="Dataset subset")
    parser.add_argument('--noise-ratio', type=float, default=0.1, help="Noise ratio for graph injection")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")

    args = parser.parse_args()

    if args.download:
        # Download dataset
        tasks = fetch_locomo_dataset(subset=args.subset)
        save_raw_data(tasks)
        
        # Build graphs
        graphs = build_memory_graph(tasks)
        save_graphs(graphs)
        
        # Generate noisy graphs
        noisy_graphs = generate_noisy_graphs(graphs, ratio=args.noise_ratio, seed=args.seed)
        save_noisy_graphs(noisy_graphs)
        
        logger.info("Data loading and processing complete.")
    else:
        logger.info("No action specified. Use --download to fetch and process data.")

if __name__ == "__main__":
    main()