"""
Data loading and processing utilities for the llmXive memory optimization project.

This module handles:
1. Fetching the LoCoMo benchmark dataset from HuggingFace
2. Extracting knowledge triples from context text
3. Building memory graphs from triples
4. Injecting noise into graphs (edge replacement)
5. Saving/loading graph data
"""

import os
import json
import logging
import hashlib
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

import networkx as nx
import numpy as np
from datasets import load_dataset
import spacy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Output directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GRAPHS_DIR = PROCESSED_DIR / "graphs"

# Ensure output directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

def fetch_locomo_dataset(subset: str = "test") -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    
    Args:
        subset: Dataset split to fetch (default: "test")
    
    Returns:
        List of task dictionaries with keys: question, context, answer
    
    Raises:
        ValueError: If dataset cannot be fetched or schema is invalid
    """
    ensure_output_dirs()
    
    # Try multiple known dataset IDs for LoCoMo
    dataset_ids = [
        "locomo/locomo-benchmark",  # Primary source
        "mlabonne/locomo",           # Alternative mirror
    ]
    
    last_error = None
    
    for dataset_id in dataset_ids:
        try:
            logger.info(f"Attempting to fetch dataset: {dataset_id}")
            
            # Load dataset with streaming to handle large sizes
            ds = load_dataset(dataset_id, split=subset, trust_remote_code=True)
            
            # Convert to list
            tasks = list(ds)
            
            if not tasks:
                logger.warning(f"Dataset {dataset_id} returned empty list")
                continue
            
            # Validate schema
            required_cols = {"question", "context", "answer"}
            actual_cols = set(tasks[0].keys())
            
            if not required_cols.issubset(actual_cols):
                missing = required_cols - actual_cols
                logger.warning(f"Dataset {dataset_id} missing columns: {missing}")
                continue
            
            logger.info(f"Successfully fetched {len(tasks)} tasks from {dataset_id}")
            
            # Save raw data
            output_path = RAW_DATA_DIR / "locomo.jsonl"
            with open(output_path, 'w', encoding='utf-8') as f:
                for task in tasks:
                    f.write(json.dumps(task) + '\n')
            
            logger.info(f"Saved raw data to {output_path}")
            return tasks
            
        except Exception as e:
            last_error = e
            logger.warning(f"Failed to fetch {dataset_id}: {e}")
            continue
    
    # If we get here, all attempts failed
    error_msg = f"Dataset fetch failed for all sources. Last error: {last_error}"
    logger.error(error_msg)
    raise ValueError(error_msg)

def save_raw_data(tasks: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """Save raw dataset tasks to a JSONL file."""
    if output_path is None:
        output_path = RAW_DATA_DIR / "locomo.jsonl"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def extract_traces_from_context(context: str) -> List[Tuple[str, str, str]]:
    """
    Extract subject-verb-object triples from context text using spaCy.
    
    Args:
        context: Input text to parse
    
    Returns:
        List of (subject, verb, object) triples
    """
    if not context or not context.strip():
        return []
    
    try:
        # Load spaCy model (en_core_web_sm must be installed)
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(context)
        
        triples = []
        
        # Extract triples based on dependency parsing
        for token in doc:
            # Look for subject-object relationships
            if token.dep_ in ("nsubj", "nsubjpass"):
                subject = token.text
                # Find the head verb
                head = token.head
                verb = head.text
                # Find object (dobj, pobj, etc.)
                for child in head.children:
                    if child.dep_ in ("dobj", "pobj", "attr"):
                        obj = child.text
                        triples.append((subject, verb, obj))
                        break
        
        # Also try to extract from named entities
        # This is a simplified approach; real implementation would be more sophisticated
        if not triples:
            # Fallback: simple pattern matching
            words = context.split()
            for i in range(len(words) - 2):
                # Look for noun-verb-noun patterns
                triples.append((words[i], words[i+1], words[i+2]))
        
        return triples
        
    except OSError:
        logger.error("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
        raise
    except Exception as e:
        logger.error(f"Error extracting triples: {e}")
        return []

def build_memory_graph(triples: List[Tuple[str, str, str]]) -> Dict[str, Any]:
    """
    Build a memory graph from a list of triples.
    
    Args:
        triples: List of (subject, verb, object) tuples
    
    Returns:
        Graph dictionary with 'nodes' and 'edges' keys
    """
    nodes = set()
    edges = []
    
    for subj, verb, obj in triples:
        nodes.add(subj)
        nodes.add(obj)
        
        edges.append({
            "source": subj,
            "target": obj,
            "relation": verb
        })
    
    return {
        "nodes": list(nodes),
        "edges": edges
    }

def save_graphs(graphs: Dict[str, Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save graphs to a JSON file.
    
    Args:
        graphs: Dictionary mapping task_id to graph dict
        output_path: Output file path (default: data/intermediate/graphs_raw.json)
    """
    if output_path is None:
        output_path = INTERMEDIATE_DIR / "graphs_raw.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graphs, f, indent=2)
    
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")

def load_graphs(input_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load graphs from a JSON file.
    
    Args:
        input_path: Input file path (default: data/intermediate/graphs_raw.json)
    
    Returns:
        Dictionary mapping task_id to graph dict
    """
    if input_path is None:
        input_path = INTERMEDIATE_DIR / "graphs_raw.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def inject_noise(graph: Dict[str, Any], ratio: float, seed: int) -> Dict[str, Any]:
    """
    Inject noise into a graph by replacing edges.
    
    This function replaces a proportion of existing edges with random edges,
    maintaining the total edge count. It does NOT add edges.
    
    Args:
        graph: Input graph dict with 'nodes' and 'edges'
        ratio: Proportion of edges to replace (0.0 to 1.0)
        seed: Random seed for reproducibility
    
    Returns:
        Noisy graph dict with same structure
    """
    random.seed(seed)
    np.random.seed(seed)
    
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    if not edges or len(nodes) < 2:
        # Degenerate case: no edges or not enough nodes
        return {
            "nodes": nodes,
            "edges": []
        }
    
    num_edges = len(edges)
    num_to_replace = int(num_edges * ratio)
    
    # Create a set of existing edge tuples for quick lookup
    existing_edges = {(e["source"], e["target"]) for e in edges}
    
    # Select edges to replace
    replace_indices = random.sample(range(num_edges), num_to_replace)
    
    # Create new edges
    new_edges = edges.copy()
    
    for idx in replace_indices:
        old_edge = new_edges[idx]
        
        # Select random source and target (excluding self-loops and existing edges)
        max_attempts = 100
        for _ in range(max_attempts):
            new_source = random.choice(nodes)
            new_target = random.choice(nodes)
            
            # Avoid self-loops
            if new_source == new_target:
                continue
            
            # Avoid existing edges (unless we're replacing it)
            if (new_source, new_target) in existing_edges and (new_source, new_target) != (old_edge["source"], old_edge["target"]):
                continue
            
            # Create new edge
            new_edges[idx] = {
                "source": new_source,
                "target": new_target,
                "relation": old_edge["relation"]  # Preserve relation or randomize?
            }
            break
    
    return {
        "nodes": nodes,
        "edges": new_edges
    }

def generate_noisy_graphs(clean_graphs: Dict[str, Dict[str, Any]], ratio: float = 0.1, seed: int = 42) -> Dict[str, Dict[str, Any]]:
    """
    Generate noisy versions of all graphs in the input dictionary.
    
    Args:
        clean_graphs: Dictionary mapping task_id to clean graph
        ratio: Noise ratio (default: 0.1)
        seed: Random seed (default: 42)
    
    Returns:
        Dictionary mapping task_id to noisy graph
    """
    noisy_graphs = {}
    
    for task_id, graph in clean_graphs.items():
        noisy_graphs[task_id] = inject_noise(graph, ratio=ratio, seed=seed)
    
    return noisy_graphs

def save_noisy_graphs(noisy_graphs: Dict[str, Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save noisy graphs to a JSON file.
    
    Args:
        noisy_graphs: Dictionary mapping task_id to noisy graph
        output_path: Output file path (default: data/processed/graphs/graph_noise_42.json)
    """
    if output_path is None:
        output_path = GRAPHS_DIR / "graph_noise_42.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(noisy_graphs, f, indent=2)
    
    logger.info(f"Saved {len(noisy_graphs)} noisy graphs to {output_path}")

def load_noisy_graphs(input_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load noisy graphs from a JSON file.
    
    Args:
        input_path: Input file path (default: data/processed/graphs/graph_noise_42.json)
    
    Returns:
        Dictionary mapping task_id to noisy graph
    """
    if input_path is None:
        input_path = GRAPHS_DIR / "graph_noise_42.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Noisy graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def stream_locomo_tasks(chunk_size: int = 10) -> Iterator[Dict[str, Any]]:
    """
    Stream LoCoMo tasks in chunks to avoid memory overload.
    
    Args:
        chunk_size: Number of tasks per chunk
    
    Yields:
        Task dictionaries one by one
    """
    try:
        # Try streaming mode first
        ds = load_dataset("locomo/locomo-benchmark", split="test", streaming=True, trust_remote_code=True)
        
        chunk = []
        for task in ds:
            chunk.append(task)
            if len(chunk) >= chunk_size:
                yield from chunk
                chunk = []
        
        # Yield remaining tasks
        if chunk:
            yield from chunk
            
    except Exception as e:
        logger.warning(f"Streaming failed, falling back to chunked loading: {e}")
        # Fallback: load in chunks from file
        tasks = fetch_locomo_dataset("test")
        for i in range(0, len(tasks), chunk_size):
            yield from tasks[i:i+chunk_size]

def process_in_chunks(tasks: List[Dict[str, Any]], processor, chunk_size: int = 100):
    """
    Process tasks in chunks.
    
    Args:
        tasks: List of tasks to process
        processor: Function to apply to each task
        chunk_size: Number of tasks per chunk
    
    Returns:
        List of processed results
    """
    results = []
    
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        chunk_results = [processor(task) for task in chunk]
        results.extend(chunk_results)
    
    return results

def estimate_dataset_size(dataset_id: str, split: str = "test") -> int:
    """
    Estimate the size of a dataset in bytes.
    
    Args:
        dataset_id: HuggingFace dataset ID
        split: Dataset split
    
    Returns:
        Estimated size in bytes
    """
    try:
        ds = load_dataset(dataset_id, split=split, streaming=True)
        # Get first few items to estimate size
        sample = list(ds)[:10]
        avg_size = sum(len(json.dumps(item).encode()) for item in sample) / len(sample)
        
        # Get total count
        total = len(list(load_dataset(dataset_id, split=split)))
        
        return int(avg_size * total)
    except Exception as e:
        logger.warning(f"Could not estimate size: {e}")
        return 0

def main():
    """
    Main entry point for data loading and graph generation.
    
    This function:
    1. Fetches the LoCoMo dataset
    2. Extracts triples and builds graphs
    3. Saves clean graphs to intermediate storage
    4. Injects noise and saves noisy graphs
    """
    logger.info("Starting data loading and graph generation pipeline")
    
    # Step 1: Fetch dataset
    logger.info("Fetching LoCoMo dataset...")
    try:
        tasks = fetch_locomo_dataset("test")
    except ValueError as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise
    
    logger.info(f"Fetched {len(tasks)} tasks")
    
    # Step 2: Extract triples and build graphs
    logger.info("Extracting triples and building graphs...")
    clean_graphs = {}
    
    for task in tasks:
        task_id = task.get("question", f"task_{hash(task['context']) % 10000}")[:50]
        triples = extract_traces_from_context(task["context"])
        graph = build_memory_graph(triples)
        clean_graphs[task_id] = graph
    
    logger.info(f"Built {len(clean_graphs)} graphs")
    
    # Step 3: Save clean graphs
    logger.info("Saving clean graphs...")
    save_graphs(clean_graphs)
    
    # Step 4: Generate noisy graphs
    logger.info("Generating noisy graphs (ratio=0.1, seed=42)...")
    noisy_graphs = generate_noisy_graphs(clean_graphs, ratio=0.1, seed=42)
    
    # Step 5: Save noisy graphs
    logger.info("Saving noisy graphs...")
    save_noisy_graphs(noisy_graphs)
    
    logger.info("Pipeline completed successfully")
    
    # Verification
    output_path = GRAPHS_DIR / "graph_noise_42.json"
    if output_path.exists():
        size = output_path.stat().st_size
        logger.info(f"Output file {output_path} created with size {size} bytes")
    else:
        logger.error(f"Output file {output_path} was not created!")
        raise RuntimeError("Failed to create noisy graph output file")

if __name__ == "__main__":
    main()
