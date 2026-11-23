"""
Data loader module for the llmXive project.
Handles downloading, loading, and processing of the LoCoMo benchmark dataset.
Implements strict data fetching and streaming capabilities.
"""

import os
import sys
import json
import logging
import hashlib
import csv
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Iterator, Generator
from dataclasses import dataclass

import psutil
import numpy as np
import spacy
from spacy.tokens import Doc
import networkx as nx
from datasets import load_dataset, DatasetDict
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_GRAPHS_DIR = DATA_PROCESSED_DIR / "graphs"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class MemoryWarning(Exception):
    """Raised when memory pressure is detected."""
    pass

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json if it exists."""
    config_path = PROJECT_ROOT / "code" / "config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {
        "dataset_name": "locomo/locomo",
        "split": "test",
        "config": "default",
        "trust_remote_code": True,
        "chunk_size": 100
    }

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

def check_memory_pressure(threshold_percent: float = 80.0) -> bool:
    """Check if current memory usage exceeds threshold."""
    memory = psutil.virtual_memory()
    return memory.percent > threshold_percent

def estimate_dataset_size(dataset_name: str, split: str) -> int:
    """Estimate the size of a dataset in bytes."""
    try:
        ds = load_dataset(dataset_name, split=split, streaming=True)
        # Sample a few rows to estimate size
        sample_size = 0
        count = 0
        for i, row in enumerate(ds):
            if i >= 100:
                break
            sample_size += sys.getsizeof(json.dumps(row))
            count += 1
        avg_size = sample_size / count if count > 0 else 0
        # Estimate total size (assuming 1000 rows for estimation)
        return int(avg_size * 1000)
    except Exception as e:
        logger.warning(f"Could not estimate dataset size: {e}")
        return 0

def load_locomo_strict() -> List[Dict[str, Any]]:
    """
    Load LoCoMo dataset strictly. Raises FileNotFoundError if download fails.
    No synthetic fallback allowed.
    """
    config = load_config()
    try:
        logger.info(f"Loading LoCoMo dataset: {config['dataset_name']}")
        ds = load_dataset(
            config['dataset_name'],
            split=config['split'],
            trust_remote_code=config['trust_remote_code']
        )
        data = list(ds)
        logger.info(f"Successfully loaded {len(data)} samples")
        return data
    except Exception as e:
        error_msg = f"Failed to load LoCoMo dataset: {e}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e

def fetch_locomo_dataset() -> List[Dict[str, Any]]:
    """Fetch LoCoMo dataset with memory check and fallback to streaming."""
    config = load_config()
    
    # Check memory pressure
    if check_memory_pressure():
        logger.warning("Memory pressure detected, using streaming loader")
        return list(load_locomo_streaming())
    
    try:
        return load_locomo_strict()
    except MemoryWarning:
        logger.warning("MemoryWarning raised, falling back to streaming")
        return list(load_locomo_streaming())

def load_locomo_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Load LoCoMo dataset in streaming mode to handle large datasets.
    Yields individual samples.
    """
    config = load_config()
    try:
        logger.info("Loading LoCoMo dataset in streaming mode")
        ds = load_dataset(
            config['dataset_name'],
            split=config['split'],
            trust_remote_code=config['trust_remote_code'],
            streaming=True
        )
        for item in ds:
            yield item
    except Exception as e:
        error_msg = f"Failed to load LoCoMo dataset in streaming mode: {e}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e

def stream_load_locomo(chunk_size: int = 100) -> Generator[Tuple[List[Dict[str, Any]], Dict[str, Any]], None, None]:
    """
    Stream LoCoMo dataset in chunks, yielding triples and updating stats incrementally.
    
    Args:
        chunk_size: Number of samples to process in each chunk
        
    Yields:
      Tuple of (list of triples for the chunk, updated stats dict)
      
    The streaming logic accumulates statistics online without holding the full 
    dataset in memory. Stats include: total_samples, total_triples, avg_triples_per_sample.
    """
    config = load_config()
    nlp = spacy.load("en_core_web_sm")
    
    stats = {
        "total_samples": 0,
        "total_triples": 0,
        "avg_triples_per_sample": 0.0
    }
    
    buffer = []
    
    for sample in load_locomo_streaming():
        buffer.append(sample)
        
        if len(buffer) >= chunk_size:
            # Process the buffer
            triples_chunk = []
            for item in buffer:
                task_id = item.get('task_id', f"unknown_{stats['total_samples']}")
                context = item.get('context', '')
                
                # Extract triples from context
                doc = nlp(context)
                triples = extract_triples_from_context(doc, task_id)
                triples_chunk.extend(triples)
                stats['total_triples'] += len(triples)
                
                stats['total_samples'] += 1
                stats['avg_triples_per_sample'] = (
                    stats['total_triples'] / stats['total_samples']
                    if stats['total_samples'] > 0 else 0.0
                )
            
            yield triples_chunk, stats.copy()
            buffer = []
    
    # Process remaining samples
    if buffer:
        triples_chunk = []
        for item in buffer:
            task_id = item.get('task_id', f"unknown_{stats['total_samples']}")
            context = item.get('context', '')
            
            doc = nlp(context)
            triples = extract_triples_from_context(doc, task_id)
            triples_chunk.extend(triples)
            stats['total_triples'] += len(triples)
            
            stats['total_samples'] += 1
            stats['avg_triples_per_sample'] = (
                stats['total_triples'] / stats['total_samples']
                if stats['total_samples'] > 0 else 0.0
            )
        
        if triples_chunk:
            yield triples_chunk, stats.copy()

def extract_triples_from_context(doc: Doc, task_id: str) -> List[Dict[str, str]]:
    """
    Extract subject-verb-object triples from a spaCy document.
    
    Args:
        doc: spaCy Doc object
        task_id: Identifier for the task
        
    Returns:
        List of dictionaries with 'subject', 'verb', 'object', 'task_id' keys
    """
    triples = []
    
    for token in doc:
        # Look for verbs with subject and object dependencies
        if token.pos_ == "VERB" or token.pos_ == "AUX":
            subj = None
            obj = None
            
            for child in token.children:
                if child.dep_ in ("nsubj", "nsubjpass"):
                    subj = child.text
                elif child.dep_ in ("dobj", "attr", "oprd"):
                    obj = child.text
            
            if subj and obj:
                triples.append({
                    "task_id": task_id,
                    "subject": subj,
                    "verb": token.text,
                    "object": obj
                })
    
    return triples

def save_raw_data(data: List[Dict[str, Any]], filename: str = "locomo.jsonl"):
    """Save raw data to JSONL file."""
    output_path = DATA_RAW_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    logger.info(f"Saved raw data to {output_path}")

def save_triples_to_jsonl(triples: List[Dict[str, str]], filename: str = "triples_raw.jsonl"):
    """Save extracted triples to JSONL file."""
    output_path = DATA_INTERMEDIATE_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for triple in triples:
            f.write(json.dumps(triple) + '\n')
    logger.info(f"Saved triples to {output_path}")

def build_memory_graph(triples: List[Dict[str, str]]) -> nx.DiGraph:
    """
    Build a directed graph from extracted triples.
    
    Args:
        triples: List of triple dictionaries
        
    Returns:
        networkx DiGraph with nodes and edges from triples
    """
    G = nx.DiGraph()
    
    for triple in triples:
        subject = triple['subject']
        verb = triple['verb']
        obj = triple['object']
        
        # Add nodes
        G.add_node(subject)
        G.add_node(obj)
        
        # Add edge with verb as attribute
        G.add_edge(subject, obj, verb=verb)
    
    return G

def save_graphs(graphs: Dict[str, nx.DiGraph], filename: str = "graphs_raw.json"):
    """
    Save graphs to JSON file.
    
    Args:
        graphs: Dictionary mapping task_id to DiGraph
        filename: Output filename
    """
    output_path = DATA_INTERMEDIATE_DIR / filename
    
    # Convert graphs to serializable format
    serializable_graphs = {}
    for task_id, G in graphs.items():
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "verb": data.get('verb', '')
            })
        serializable_graphs[task_id] = edges
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_graphs, f, indent=2)
    
    logger.info(f"Saved graphs to {output_path}")

def load_graphs(filename: str = "graphs_raw.json") -> Dict[str, nx.DiGraph]:
    """
    Load graphs from JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        Dictionary mapping task_id to DiGraph
    """
    input_path = DATA_INTERMEDIATE_DIR / filename
    
    with open(input_path, 'r', encoding='utf-8') as f:
        serializable_graphs = json.load(f)
    
    graphs = {}
    for task_id, edges in serializable_graphs.items():
        G = nx.DiGraph()
        for edge in edges:
            G.add_edge(
                edge['source'],
                edge['target'],
                verb=edge.get('verb', '')
            )
        graphs[task_id] = G
    
    logger.info(f"Loaded graphs from {input_path}")
    return graphs

def save_noisy_graphs(graphs: Dict[str, nx.DiGraph], filename: str):
    """Save noisy graphs to processed directory."""
    output_path = DATA_PROCESSED_GRAPHS_DIR / filename
    
    serializable_graphs = {}
    for task_id, G in graphs.items():
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "verb": data.get('verb', '')
            })
        serializable_graphs[task_id] = edges
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_graphs, f, indent=2)
    
    logger.info(f"Saved noisy graphs to {output_path}")

def load_noisy_graphs(filename: str) -> Dict[str, nx.DiGraph]:
    """Load noisy graphs from processed directory."""
    input_path = DATA_PROCESSED_GRAPHS_DIR / filename
    
    with open(input_path, 'r', encoding='utf-8') as f:
        serializable_graphs = json.load(f)
    
    graphs = {}
    for task_id, edges in serializable_graphs.items():
        G = nx.DiGraph()
        for edge in edges:
            G.add_edge(
                edge['source'],
                edge['target'],
                verb=edge.get('verb', '')
            )
        graphs[task_id] = G
    
    logger.info(f"Loaded noisy graphs from {input_path}")
    return graphs

def download_spacy_model():
    """Download the required spaCy model."""
    logger.info("Downloading spaCy model...")
    spacy.cli.download("en_core_web_sm")
    logger.info("spaCy model downloaded successfully")

def process_in_chunks(data: List[Dict[str, Any]], chunk_size: int, processor_func):
    """
    Process data in chunks.
    
    Args:
        data: Input data list
        chunk_size: Number of items per chunk
        processor_func: Function to process each chunk
        
    Returns:
        List of processed chunks
    """
    results = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        result = processor_func(chunk)
        results.append(result)
    return results

def load_locomo() -> List[Dict[str, Any]]:
    """
    Load LoCoMo dataset with memory pressure check.
    Falls back to streaming if memory pressure is detected.
    """
    config = load_config()
    
    # Check memory pressure
    if check_memory_pressure():
        logger.warning("Memory pressure detected, using streaming loader")
        return list(load_locomo_streaming())
    
    try:
        return load_locomo_strict()
    except MemoryWarning:
        logger.warning("MemoryWarning raised, falling back to streaming")
        return list(load_locomo_streaming())

def generate_noisy_graph_dataset(clean_graphs: Dict[str, nx.DiGraph], noise_density: float = 0.1, seed: int = 42) -> Dict[str, nx.DiGraph]:
    """
    Generate noisy graphs by adding random edges.
    
    Args:
        clean_graphs: Dictionary of clean graphs
        noise_density: Fraction of edges to add relative to original
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary of noisy graphs
    """
    import random
    random.seed(seed)
    np.random.seed(seed)
    
    noisy_graphs = {}
    
    for task_id, G in clean_graphs.items():
        noisy_G = G.copy()
        nodes = list(noisy_G.nodes())
        n_nodes = len(nodes)
        n_edges = noisy_G.number_of_edges()
        
        # Add random edges
        n_new_edges = int(n_edges * noise_density) if n_edges > 0 else 1
        
        added = 0
        attempts = 0
        max_attempts = n_new_edges * 10
        
        while added < n_new_edges and attempts < max_attempts:
            u = random.choice(nodes)
            v = random.choice(nodes)
            
            if u != v and not noisy_G.has_edge(u, v):
                noisy_G.add_edge(u, v, verb="noise")
                added += 1
            
            attempts += 1
        
        noisy_graphs[task_id] = noisy_G
    
    return noisy_graphs

def main():
    """Main entry point for data loader script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data loader for LoCoMo benchmark")
    parser.add_argument("--download", action="store_true", help="Download LoCoMo dataset")
    parser.add_argument("--streaming", action="store_true", help="Use streaming mode")
    parser.add_argument("--chunk-size", type=int, default=100, help="Chunk size for streaming")
    parser.add_argument("--extract-triples", action="store_true", help="Extract triples from context")
    parser.add_argument("--build-graphs", action="store_true", help="Build memory graphs from triples")
    
    args = parser.parse_args()
    
    if args.download:
        logger.info("Downloading LoCoMo dataset...")
        data = load_locomo_strict() if not args.streaming else list(load_locomo_streaming())
        save_raw_data(data)
        logger.info(f"Downloaded {len(data)} samples")
    
    if args.extract_triples:
        logger.info("Extracting triples...")
        data = load_locomo()
        nlp = spacy.load("en_core_web_sm")
        all_triples = []
        
        for item in data:
            task_id = item.get('task_id', 'unknown')
            context = item.get('context', '')
            doc = nlp(context)
            triples = extract_triples_from_context(doc, task_id)
            all_triples.extend(triples)
        
        save_triples_to_jsonl(all_triples)
        logger.info(f"Extracted {len(all_triples)} triples")
    
    if args.build_graphs:
        logger.info("Building memory graphs...")
        triples_data = []
        with open(DATA_INTERMEDIATE_DIR / "triples_raw.jsonl", 'r') as f:
            for line in f:
                triples_data.append(json.loads(line))
        
        graphs = {}
        current_task_id = None
        current_triples = []
        
        for triple in triples_data:
            if triple['task_id'] != current_task_id:
                if current_task_id is not None and current_triples:
                    graphs[current_task_id] = build_memory_graph(current_triples)
                current_task_id = triple['task_id']
                current_triples = []
            current_triples.append(triple)
        
        if current_task_id is not None and current_triples:
            graphs[current_task_id] = build_memory_graph(current_triples)
        
        save_graphs(graphs)
        logger.info(f"Built {len(graphs)} graphs")

if __name__ == "__main__":
    main()