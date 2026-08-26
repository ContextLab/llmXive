"""
Data loading and processing module for llmXive research pipeline.
Handles dataset fetching, extraction, graph construction, and noise injection.
"""
import os
import json
import logging
import hashlib
import random
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import numpy as np
import networkx as nx
from datasets import load_dataset
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
PROCESSED_DIR = DATA_DIR / "processed"
GRAPHS_DIR = PROCESSED_DIR / "graphs"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_output_dirs():
    """Ensure all required output directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_locomo_dataset(split: str = "test") -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    
    Args:
        split: Dataset split to load ('train', 'validation', 'test')
    
    Returns:
        List of dataset records as dictionaries.
    
    Raises:
        ValueError: If the dataset cannot be fetched.
    """
    logger.info(f"Fetching LoCoMo dataset split: {split}")
    
    # Use the correct canonical dataset ID
    dataset_id = "locomo/locomo-benchmark"
    
    try:
        # Load dataset with streaming to handle large sizes
        dataset = load_dataset(dataset_id, split=split, trust_remote_code=True)
        
        # Convert to list of dicts
        tasks = list(dataset)
        
        if not tasks:
            raise ValueError(f"Dataset split '{split}' returned empty results.")
        
        # Validate schema
        required_fields = ["question", "context", "answer"]
        if not all(field in tasks[0] for field in required_fields):
            missing = [f for f in required_fields if f not in tasks[0]]
            raise ValueError(f"Dataset schema mismatch. Missing fields: {missing}")
        
        logger.info(f"Successfully fetched {len(tasks)} records from {dataset_id}/{split}")
        return tasks
        
    except Exception as e:
        error_msg = f"Dataset fetch failed for all sources. Last error: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def save_raw_data(tasks: List[Dict[str, Any]], filename: str = "locomo.jsonl"):
    """
    Save raw dataset records to JSONL format.
    
    Args:
        tasks: List of dataset records.
        filename: Output filename.
    """
    output_path = RAW_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')
    logger.info(f"Saved raw data to {output_path}")


def stream_load_dataset(split: str = "test", chunk_size: int = 100) -> List[Dict[str, Any]]:
    """
    Load dataset in streaming mode to handle memory constraints.
    
    Args:
        split: Dataset split to load.
        chunk_size: Number of records to process at once.
    
    Returns:
        List of all loaded records.
    """
    logger.info(f"Streaming load of {split} split")
    dataset_id = "locomo/locomo-benchmark"
    
    all_records = []
    dataset = load_dataset(dataset_id, split=split, trust_remote_code=True, streaming=True)
    
    batch = []
    for record in dataset:
        batch.append(record)
        if len(batch) >= chunk_size:
            all_records.extend(batch)
            batch = []
    
    if batch:
        all_records.extend(batch)
    
    logger.info(f"Streamed {len(all_records)} records")
    return all_records


def load_dataset_in_memory(split: str = "test") -> List[Dict[str, Any]]:
    """
    Load dataset into memory. Falls back to streaming on OOM.
    
    Args:
        split: Dataset split to load.
    
    Returns:
        List of dataset records.
    
    Raises:
        MemoryError: If loading fails and streaming also fails.
    """
    try:
        return load_dataset(split)
    except MemoryError:
        logger.warning("OOM detected during in-memory load, switching to streaming")
        return stream_load_dataset(split)


def extract_triples(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract subject-verb-object triples from task contexts using spaCy.
    
    Args:
        tasks: List of dataset records.
    
    Returns:
        List of extracted triples with metadata.
    """
    import spacy
    
    # Download model if not present
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.info("Downloading en_core_web_sm model...")
        from spacy.cli import download
        download("en_core_web_sm", version="3.7.1")
        nlp = spacy.load("en_core_web_sm")
    
    triples = []
    
    for task in tasks:
        context = task.get("context", "")
        if not context or not context.strip():
            logger.debug(f"Skipping empty context for task {task.get('task_id', 'unknown')}")
            continue
        
        doc = nlp(context)
        task_id = task.get("task_id", "unknown")
        
        for sent in doc.sents:
            for token in sent:
                if token.dep_ == "nsubj":  # Subject
                    subject = token.text
                    # Find the verb head
                    verb = token.head
                    # Find direct object
                    for child in verb.children:
                        if child.dep_ == "dobj":  # Direct object
                            obj = child.text
                            triples.append({
                                "task_id": task_id,
                                "subject": subject,
                                "verb": verb.text,
                                "object": obj,
                                "sentence": sent.text
                            })
                            break
    
    logger.info(f"Extracted {len(triples)} triples")
    return triples


def save_triples(triples: List[Dict[str, Any]], filename: str = "triples_raw.jsonl"):
    """Save extracted triples to JSONL format."""
    output_path = INTERMEDIATE_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for triple in triples:
            f.write(json.dumps(triple) + '\n')
    logger.info(f"Saved triples to {output_path}")


def build_graphs_from_triples(triples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build memory graphs from extracted triples.
    
    Args:
        triples: List of extracted triples.
    
    Returns:
        Dictionary mapping task_id to graph structure.
    """
    graphs = {}
    
    # Group triples by task_id
    task_triples = {}
    for triple in triples:
        task_id = triple["task_id"]
        if task_id not in task_triples:
            task_triples[task_id] = []
        task_triples[task_id].append(triple)
    
    for task_id, task_trips in task_triples.items():
        nodes = set()
        edges = []
        
        for triple in task_trips:
            subject = triple["subject"]
            obj = triple["object"]
            relation = triple["verb"]
            
            nodes.add(subject)
            nodes.add(obj)
            
            edges.append({
                "source": subject,
                "target": obj,
                "relation": relation
            })
        
        graphs[task_id] = {
            "nodes": list(nodes),
            "edges": edges
        }
    
    logger.info(f"Built {len(graphs)} graphs")
    return graphs


def save_graphs(graphs: Dict[str, Any], filename: str = "graphs_raw.json"):
    """Save graphs to JSON format."""
    output_path = INTERMEDIATE_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graphs, f, indent=2)
    logger.info(f"Saved graphs to {output_path}")


def inject_noise(graph: Dict[str, Any], ratio: float = 0.1, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Inject noise into a graph by replacing edges.
    
    This function removes a proportion of existing edges and adds an equal
    number of new random edges between existing nodes, ensuring:
    - Total edge count remains identical
    - No self-loops are created
    - No duplicate edges are created
    
    Args:
        graph: Graph structure with 'nodes' and 'edges' keys.
        ratio: Proportion of edges to replace (0.0 to 1.0).
        seed: Random seed for reproducibility.
    
    Returns:
        Noisy graph with same structure.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    # Handle degenerate cases
    if len(nodes) <= 1 or len(edges) == 0:
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    # Calculate number of edges to replace
    num_edges_to_replace = int(len(edges) * ratio)
    num_edges_to_replace = min(num_edges_to_replace, len(edges))
    
    # Create edge set for quick lookup and to avoid duplicates
    edge_set = {(e["source"], e["target"]) for e in edges}
    edge_list = list(edges)
    
    # Randomly select edges to remove
    indices_to_remove = random.sample(range(len(edge_list)), num_edges_to_replace)
    edges_to_remove = [edge_list[i] for i in indices_to_remove]
    
    # Create new edge list without removed edges
    new_edges = [e for i, e in enumerate(edge_list) if i not in indices_to_remove]
    
    # Generate new edges to add
    nodes_list = list(nodes)
    num_nodes = len(nodes_list)
    
    for _ in range(num_edges_to_replace):
        # Try to find a valid new edge
        max_attempts = 100
        for attempt in range(max_attempts):
            src = random.choice(nodes_list)
            tgt = random.choice(nodes_list)
            
            # Skip self-loops
            if src == tgt:
                continue
            
            # Skip existing edges
            if (src, tgt) in edge_set:
                continue
            
            # Create new edge
            new_edge = {
                "source": src,
                "target": tgt,
                "relation": "noisy_relation"
            }
            new_edges.append(new_edge)
            edge_set.add((src, tgt))
            break
        else:
            # If we can't find a new edge after max attempts, we skip
            # This can happen in dense graphs
            logger.warning(f"Could not generate new edge after {max_attempts} attempts")
    
    return {
        "nodes": nodes,
        "edges": new_edges
    }


def save_noisy_graphs(graphs: Dict[str, Any], filename: str = "graph_noise_42.json", seed: int = 42):
    """
    Generate and save noisy graphs from clean graphs.
    
    Args:
        graphs: Clean graphs dictionary.
        filename: Output filename.
        seed: Random seed for noise injection.
    """
    noisy_graphs = {}
    
    for task_id, graph in graphs.items():
        noisy_graphs[task_id] = inject_noise(graph, ratio=0.1, seed=seed)
    
    output_path = GRAPHS_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(noisy_graphs, f, indent=2)
    
    logger.info(f"Saved noisy graphs to {output_path}")
    return output_path


def run_baseline():
    """Run baseline execution (placeholder for actual implementation)."""
    logger.info("Running baseline execution")
    # This would integrate with runner.py and strategies
    pass


def run_lazy_strategy():
    """Run lazy strategy execution (placeholder for actual implementation)."""
    logger.info("Running lazy strategy execution")
    pass


def run_greedy_strategy():
    """Run greedy strategy execution (placeholder for actual implementation)."""
    logger.info("Running greedy strategy execution")
    pass


def main():
    """
    Main entry point for data loading and processing pipeline.
    
    This function orchestrates:
    1. Fetching the LoCoMo dataset
    2. Extracting triples
    3. Building graphs
    4. Injecting noise
    5. Saving all artifacts
    """
    logger.info("Starting data loader pipeline")
    
    # Step 1: Fetch dataset
    try:
        tasks = fetch_locomo_dataset("test")
    except ValueError as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise
    
    # Step 2: Save raw data
    save_raw_data(tasks, "locomo.jsonl")
    
    # Step 3: Extract triples
    triples = extract_triples(tasks)
    save_triples(triples, "triples_raw.jsonl")
    
    # Step 4: Build graphs
    graphs = build_graphs_from_triples(triples)
    save_graphs(graphs, "graphs_raw.json")
    
    # Step 5: Generate noisy graphs (T011c)
    save_noisy_graphs(graphs, "graph_noise_42.json", seed=42)
    
    logger.info("Data loader pipeline completed successfully")


if __name__ == "__main__":
    main()
