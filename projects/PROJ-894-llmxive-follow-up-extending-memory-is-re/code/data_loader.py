"""
Data loader for the LLMXive project.
Handles downloading, extracting, and processing the LoCoMo benchmark dataset.
"""
import os
import json
import logging
import hashlib
import csv
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import numpy as np
import spacy
from datasets import load_dataset
from tqdm import tqdm

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

# Ensure output directories exist
def ensure_output_dirs():
    """Create necessary output directories if they don't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

def fetch_locomo_dataset(split: str = "test") -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    
    Args:
        split: The dataset split to load (e.g., 'test', 'train').
        
    Returns:
        List of dataset records.
        
    Raises:
        ValueError: If the dataset cannot be fetched or schema is invalid.
    """
    # The correct dataset ID for LoCoMo benchmark
    # Based on the error log, 'mlabonne/locomo' was tried and failed.
    # The task description mentions 'locomo/locomo-benchmark'.
    # We will try the canonical ID mentioned in the task first.
    dataset_id = "locomo/locomo-benchmark"
    
    logger.info(f"Attempting to fetch dataset: {dataset_id} (split: {split})")
    
    try:
        # Load the dataset
        # trust_remote_code=True is often required for custom dataset scripts
        ds = load_dataset(dataset_id, split=split, trust_remote_code=True)
        
        # Verify columns
        expected_columns = {'question', 'context', 'answer'}
        actual_columns = set(ds.column_names)
        
        if not expected_columns.issubset(actual_columns):
            missing = expected_columns - actual_columns
            raise ValueError(
                f"Dataset schema mismatch. Missing columns: {missing}. "
                f"Found columns: {actual_columns}"
            )
        
        # Convert to list of dicts
        tasks = ds.to_list()
        logger.info(f"Successfully fetched {len(tasks)} tasks from {dataset_id}")
        return tasks
        
    except Exception as e:
        error_msg = f"Dataset fetch failed for all sources. Last error: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def save_raw_data(tasks: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save raw dataset tasks to a JSONL file.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Path to save the file. Defaults to data/raw/locomo.jsonl.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = DATA_RAW_DIR / "locomo.jsonl"
    
    ensure_output_dirs()
    
    Args:
        tasks: List of dataset records.
        filename: Output filename.
    """
    output_path = RAW_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")
    return output_path

def extract_traces_from_context(context: str, nlp) -> List[Dict[str, Any]]:
    """
    Extract subject-verb-object triples from a context string using spaCy.
    
    Args:
        context: The text to parse.
        nlp: The spaCy NLP pipeline.
        
    Returns:
        List of extracted triples.
    """
    logger.info(f"Streaming load of {split} split")
    dataset_id = "locomo/locomo-benchmark"
    
    doc = nlp(context)
    triples = []
    
    for sent in doc.sents:
        for token in sent:
            # Look for subjects (nsubj)
            if token.dep_ == "nsubj":
                subject = token.text
                head = token.head
                # Check if head is a verb
                if head.pos_ == "VERB":
                    verb = head.text
                    # Look for direct objects (dobj) of this verb
                    for child in head.children:
                        if child.dep_ == "dobj":
                            obj = child.text
                            triples.append({
                                "subject": subject,
                                "verb": verb,
                                "object": obj,
                                "sentence": sent.text
                            })
    
    return triples

def build_memory_graph(triples: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    """
    Build a memory graph from extracted triples.
    
    Args:
        triples: List of extracted triples.
        task_id: Unique identifier for the task.
        
    Returns:
        Graph representation as a dictionary.
    """
    edges = []
    nodes = set()
    
    for i, triple in enumerate(triples):
        source = triple['subject']
        target = triple['object']
        relation = triple['verb']
        
        nodes.add(source)
        nodes.add(target)
        
        edges.append({
            "source": source,
            "target": target,
            "relation_string": relation,
            "edge_id": f"{task_id}_edge_{i}"
        })
    
    return {
        "task_id": task_id,
        "nodes": list(nodes),
        "edges": edges,
        "num_nodes": len(nodes),
        "num_edges": len(edges)
    }

def save_graphs(graphs: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save graph structures to a JSON file.
    
    Args:
        graphs: List of graph dictionaries.
        output_path: Path to save the file. Defaults to data/intermediate/graphs_raw.json.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = DATA_INTERMEDIATE_DIR / "graphs_raw.json"
    
    ensure_output_dirs()
    
    # Convert to dictionary keyed by task_id
    graph_dict = {g['task_id']: g['edges'] for g in graphs}
    
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
        json.dump(graph_dict, f, indent=2)
    
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")
    return output_path

def load_graphs(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load graph structures from a JSON file.
    
    Args:
        input_path: Path to the file. Defaults to data/intermediate/graphs_raw.json.
        
    Returns:
        Dictionary of graphs keyed by task_id.
    """
    if input_path is None:
        input_path = DATA_INTERMEDIATE_DIR / "graphs_raw.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_noisy_graphs(noisy_graphs: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save noisy graph structures to a JSON file.
    
    Args:
        noisy_graphs: Dictionary of noisy graphs.
        output_path: Path to save the file. Defaults to data/processed/graphs/graph_noise_42.json.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = GRAPHS_DIR / "graph_noise_42.json"
    
    ensure_output_dirs()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(noisy_graphs, f, indent=2)
    
    logger.info(f"Saved noisy graphs to {output_path}")
    return output_path

def load_noisy_graphs(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load noisy graph structures from a JSON file.
    
    Args:
        input_path: Path to the file. Defaults to data/processed/graphs/graph_noise_42.json.
        
    Returns:
        Dictionary of noisy graphs keyed by task_id.
    """
    if input_path is None:
        input_path = GRAPHS_DIR / "graph_noise_42.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Noisy graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_triples_to_jsonl(triples_list: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save extracted triples to a JSONL file.
    
    Args:
        triples_list: List of triples dictionaries.
        output_path: Path to save the file. Defaults to data/intermediate/triples_raw.jsonl.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = DATA_INTERMEDIATE_DIR / "triples_raw.jsonl"
    
    ensure_output_dirs()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in triples_list:
            f.write(json.dumps(item) + '\n')
    
    logger.info(f"Saved {len(triples_list)} triples to {output_path}")
    return output_path

def stream_locomo_tasks(split: str = "test") -> Iterator[Dict[str, Any]]:
    """
    Stream LoCoMo tasks from HuggingFace without loading all into memory.
    
    Args:
        split: The dataset split to stream.
        
    Yields:
        Individual task dictionaries.
    """
    dataset_id = "locomo/locomo-benchmark"
    logger.info(f"Streaming dataset: {dataset_id} (split: {split})")
    
    try:
        ds = load_dataset(dataset_id, split=split, trust_remote_code=True, streaming=True)
        for task in ds:
            yield task
    except Exception as e:
        logger.error(f"Failed to stream dataset: {e}")
        raise

def process_in_chunks(tasks: List[Dict[str, Any]], chunk_size: int = 100) -> Iterator[List[Dict[str, Any]]]:
    """
    Process tasks in chunks.
    
    Args:
        tasks: List of tasks.
        chunk_size: Number of tasks per chunk.
        
    Yields:
        Chunks of tasks.
    """
    for i in range(0, len(tasks), chunk_size):
        yield tasks[i:i + chunk_size]

def estimate_dataset_size(dataset_id: str, split: str = "test") -> int:
    """
    Estimate the size of a dataset.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        split: Dataset split.
        
    Returns:
        Estimated number of rows.
    """
    try:
        ds = load_dataset(dataset_id, split=split, trust_remote_code=True, streaming=True)
        count = 0
        for _ in ds:
            count += 1
        return count
    except Exception as e:
        logger.warning(f"Could not estimate dataset size: {e}")
        return -1

def main():
    """Main entry point for data loading and processing."""
    parser = argparse.ArgumentParser(description="Data loader for LLMXive project")
    parser.add_argument("--download", action="store_true", help="Download and process LoCoMo dataset")
    parser.add_argument("--split", type=str, default="test", help="Dataset split to use")
    parser.add_argument("--chunk-size", type=int, default=100, help="Chunk size for processing")
    
    args = parser.parse_args()
    
    if args.download:
        logger.info("Starting data download and processing...")
        
        # Ensure spaCy model is available
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
            raise
        
        # Fetch dataset
        try:
            tasks = fetch_locomo_dataset(args.split)
        except ValueError as e:
            logger.critical(f"Failed to fetch dataset: {e}")
            raise
        
        # Save raw data
        raw_path = save_raw_data(tasks)
        
        # Extract triples and build graphs
        all_triples = []
        graphs = []
        
        for task in tqdm(tasks, desc="Processing tasks"):
            task_id = task.get('id', f"task_{hashlib.md5(task['question'].encode()).hexdigest()[:8]}")
            
            # Extract triples
            triples = extract_traces_from_context(task['context'], nlp)
            
            # Save triples with task_id
            for triple in triples:
                triple['task_id'] = task_id
                all_triples.append(triple)
            
            # Build graph
            if triples:
                graph = build_memory_graph(triples, task_id)
                graphs.append(graph)
            else:
                logger.warning(f"No triples found for task {task_id}, skipping graph construction")
        
        # Save triples
        if all_triples:
            save_triples_to_jsonl(all_triples)
        else:
            logger.warning("No triples extracted. Skipping triples save.")
        
        # Save graphs
        if graphs:
            save_graphs(graphs)
        else:
            logger.warning("No graphs built. Skipping graphs save.")
        
        logger.info("Data download and processing complete.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()