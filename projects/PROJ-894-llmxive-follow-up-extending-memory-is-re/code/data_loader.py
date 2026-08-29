"""
Data loading and preprocessing pipeline for the llmXive research project.
Handles LoCoMo dataset download, triple extraction, graph construction,
and noisy graph generation.
"""
import os
import sys
import json
import logging
import hashlib
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import time

# Third-party imports
import networkx as nx
import numpy as np
import psutil
from datasets import load_dataset
from huggingface_hub import hf_hub_download
import spacy
from spacy.cli import download

# Import local utilities
from graph_utils import inject_noise, build_memory_graph, validate_graph, get_graph_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    if not os.path.exists(config_path):
        # Create default config if not exists
        default_config = {
            "noise": {"injection_ratio": 0.1, "seed": 42},
            "paths": {
                "raw_data": "data/raw/locomo.jsonl",
                "intermediate_triples": "data/intermediate/triples_raw.jsonl",
                "clean_graphs": "data/intermediate/graphs_raw.json",
                "noisy_graphs": "data/processed/graphs/graph_noise_42.json"
            }
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        return default_config
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/intermediate",
        "data/processed/graphs",
        "data/processed/results"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def check_memory_pressure(threshold_percent: float = 80.0) -> bool:
    """Check if system memory usage exceeds threshold."""
    mem = psutil.virtual_memory()
    return mem.percent > threshold_percent

def estimate_dataset_size(dataset_name: str, split: str) -> int:
    """Estimate dataset size in bytes (placeholder for real implementation)."""
    # In a real implementation, this would query HuggingFace metadata
    return 1024 * 1024 * 100  # Assume 100MB default

def fetch_locomo_dataset(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Download and load the LoCoMo dataset from HuggingFace.
    CRITICAL: No synthetic fallback - raises exception on failure.
    """
    try:
        logger.info(f"Fetching LoCoMo dataset: {config['dataset']['name']}")
        logger.info(f"Split: {config['dataset']['split']}, Config: {config['dataset']['config']}")
        
        # Validate config exists in dataset metadata
        dataset = load_dataset(
            config['dataset']['name'],
            config['dataset']['config'],
            split=config['dataset']['split'],
            trust_remote_code=config['dataset']['trust_remote_code']
        )
        
        # Verify schema
        required_cols = ['question', 'context', 'answer']
        if not all(col in dataset.column_names for col in required_cols):
            raise ValueError(f"Dataset schema mismatch. Expected columns: {required_cols}, got: {dataset.column_names}")
        
        logger.info(f"Successfully loaded {len(dataset)} records")
        return list(dataset)
        
    except Exception as e:
        logger.error(f"Failed to fetch LoCoMo dataset: {str(e)}")
        raise RuntimeError(f"Real data fetch failed: {str(e)}. No synthetic fallback allowed.")

def stream_locomo_tasks(config: Dict[str, Any]):
    """Stream dataset tasks if memory pressure is detected."""
    if check_memory_pressure():
        logger.warning("Memory pressure detected, switching to streaming mode")
        dataset = load_dataset(
            config['dataset']['name'],
            config['dataset']['config'],
            split=config['dataset']['split'],
            trust_remote_code=config['dataset']['trust_remote_code'],
            streaming=True
        )
        for task in dataset:
            yield task
    else:
        tasks = fetch_locomo_dataset(config)
        for task in tasks:
            yield task

def save_raw_data(tasks: List[Dict[str, Any]], output_path: str):
    """Save raw dataset to JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
    logger.info(f"Saved {len(tasks)} raw tasks to {output_path}")

def extract_triples_from_context(context: str, nlp) -> List[Tuple[str, str, str]]:
    """
    Extract subject-verb-object triples from context using spaCy.
    Returns list of (subject, verb, object) tuples.
    """
    if not context or not context.strip():
        return []
    
    doc = nlp(context)
    triples = []
    
    for sentence in doc.sents:
        for token in sentence:
            if token.dep_ == "nsubj":  # Nominal subject
                subject = token.text
                # Find the head verb
                verb_token = token.head
                verb = verb_token.text
                
                # Find direct object
                for child in verb_token.children:
                    if child.dep_ == "dobj":  # Direct object
                        obj = child.text
                        triples.append((subject, verb, obj))
                        break
    
    return triples

def save_triples_to_jsonl(tasks: List[Dict[str, Any]], output_path: str, nlp) -> int:
    """Extract and save triples to JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            task_id = task.get('question', f"task_{count}")
            context = task.get('context', '')
            
            if not context or not context.strip():
                logger.debug(f"Skipping empty context for task: {task_id}")
                continue
            
            triples = extract_triples_from_context(context, nlp)
            if not triples:
                logger.debug(f"No triples found for task: {task_id}")
                continue
            
            record = {
                "task_id": task_id,
                "triples": [{"source": s, "relation": v, "target": o} for s, v, o in triples]
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            count += 1
    
    logger.info(f"Saved {count} triple records to {output_path}")
    return count

def build_memory_graph(triples: List[Tuple[str, str, str]]) -> Dict[str, Any]:
    """Build a graph structure from triples."""
    nodes = set()
    edges = []
    
    for source, relation, target in triples:
        nodes.add(source)
        nodes.add(target)
        edges.append({
            "source": source,
            "target": target,
            "relation": relation
        })
    
    return {
        "nodes": list(nodes),
        "edges": edges
    }

def save_graphs(tasks_with_triples: List[Dict[str, Any]], output_path: str):
    """Save graph structures to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    graphs = {}
    for record in tasks_with_triples:
        task_id = record['task_id']
        triples = [(t['source'], t['relation'], t['target']) for t in record['triples']]
        graph = build_memory_graph(triples)
        graphs[task_id] = graph
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graphs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")

def load_graphs(input_path: str) -> Dict[str, Any]:
    """Load graphs from JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        graphs = json.load(f)
    
    logger.info(f"Loaded {len(graphs)} graphs from {input_path}")
    return graphs

def save_noisy_graphs(noisy_graphs: Dict[str, Any], output_path: str):
    """Save noisy graphs to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(noisy_graphs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(noisy_graphs)} noisy graphs to {output_path}")

def load_noisy_graphs(input_path: str) -> Dict[str, Any]:
    """Load noisy graphs from JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Noisy graph file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        graphs = json.load(f)
    
    logger.info(f"Loaded {len(graphs)} noisy graphs from {input_path}")
    return graphs

def download_spacy_model(model_name: str = "en_core_web_sm"):
    """Download spaCy model if not present."""
    try:
        spacy.load(model_name)
        logger.info(f"spaCy model '{model_name}' already available")
    except OSError:
        logger.info(f"Downloading spaCy model '{model_name}'...")
        download(model_name)
        logger.info(f"Successfully downloaded '{model_name}'")

def process_in_chunks(tasks: List[Dict[str, Any]], nlp, chunk_size: int = 100):
    """Process tasks in chunks to manage memory."""
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i + chunk_size]
        yield chunk

def generate_noisy_graph_dataset(config: Dict[str, Any]) -> str:
    """
    Generate noisy graph dataset by applying noise injection to clean graphs.
    This is the main function for task T011c.
    
    Args:
        config: Configuration dictionary containing noise parameters and paths
    
    Returns:
        Path to the generated noisy graph file
    """
    # Load configuration
    noise_ratio = config['noise']['injection_ratio']
    seed = config['noise']['seed']
    clean_graphs_path = config['paths']['clean_graphs']
    noisy_graphs_path = config['paths']['noisy_graphs']
    
    logger.info(f"Generating noisy graph dataset with ratio={noise_ratio}, seed={seed}")
    
    # Pre-run check: Verify clean graphs file exists and is non-empty
    if not os.path.exists(clean_graphs_path):
        raise FileNotFoundError(
            f"Clean graphs file not found: {clean_graphs_path}. "
            f"Please ensure T011a-1b-serialize has completed successfully."
        )
    
    file_size = os.path.getsize(clean_graphs_path)
    if file_size == 0:
        raise ValueError(
            f"Clean graphs file is empty: {clean_graphs_path}. "
            f"Please ensure T011a-1b-serialize has generated valid output."
        )
    
    logger.info(f"Clean graphs file validated: {file_size} bytes")
    
    # Load clean graphs
    clean_graphs = load_graphs(clean_graphs_path)
    
    if not clean_graphs:
        raise ValueError("Clean graphs dictionary is empty. Cannot generate noisy graphs.")
    
    # Apply noise injection
    noisy_graphs = {}
    total_edges_original = 0
    total_edges_noisy = 0
    
    for task_id, graph in clean_graphs.items():
        # Validate graph before noise injection
        is_valid, message = validate_graph(graph)
        if not is_valid:
            logger.warning(f"Invalid graph for task {task_id}: {message}. Skipping.")
            continue
        
        # Inject noise
        noisy_graph = inject_noise(graph, ratio=noise_ratio, seed=seed)
        
        # Verify edge count preservation
        original_edge_count = len(graph['edges'])
        noisy_edge_count = len(noisy_graph['edges'])
        
        if original_edge_count != noisy_edge_count:
            logger.error(
                f"Edge count mismatch for task {task_id}: "
                f"original={original_edge_count}, noisy={noisy_edge_count}"
            )
            # Continue anyway but log the error
        
        total_edges_original += original_edge_count
        total_edges_noisy += noisy_edge_count
        noisy_graphs[task_id] = noisy_graph
    
    # Save noisy graphs
    save_noisy_graphs(noisy_graphs, noisy_graphs_path)
    
    # Verification
    logger.info(f"Noisy graph generation complete:")
    logger.info(f"  - Tasks processed: {len(noisy_graphs)}")
    logger.info(f"  - Total edges (original): {total_edges_original}")
    logger.info(f"  - Total edges (noisy): {total_edges_noisy}")
    logger.info(f"  - Output file: {noisy_graphs_path}")
    
    # Verify output file exists and has content
    if not os.path.exists(noisy_graphs_path):
        raise RuntimeError(f"Failed to create noisy graph file: {noisy_graphs_path}")
    
    output_size = os.path.getsize(noisy_graphs_path)
    if output_size == 0:
        raise RuntimeError(f"Noisy graph file is empty: {noisy_graphs_path}")
    
    logger.info(f"Verification passed: Output file size = {output_size} bytes")
    
    return noisy_graphs_path

def main():
    """Main entry point for data loading pipeline."""
    parser = argparse.ArgumentParser(description="llmXive Data Loader")
    parser.add_argument("--download", action="store_true", help="Download LoCoMo dataset")
    parser.add_argument("--extract", action="store_true", help="Extract triples")
    parser.add_argument("--generate-noisy", action="store_true", help="Generate noisy graphs (T011c)")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    ensure_output_dirs()
    
    if args.download:
        logger.info("=== Downloading LoCoMo Dataset ===")
        download_spacy_model()
        tasks = fetch_locomo_dataset(config)
        save_raw_data(tasks, config['paths']['raw_data'])
    
    if args.extract:
        logger.info("=== Extracting Triples ===")
        download_spacy_model()
        nlp = spacy.load("en_core_web_sm")
        tasks = fetch_locomo_dataset(config)
        save_triples_to_jsonl(tasks, config['paths']['intermediate_triples'], nlp)
    
    if args.generate_noisy:
        logger.info("=== Generating Noisy Graphs (T011c) ===")
        output_path = generate_noisy_graph_dataset(config)
        logger.info(f"Noisy graph dataset generated: {output_path}")
        
        # Verify output
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info("SUCCESS: Noisy graph dataset created and verified.")
        else:
            logger.error("FAILED: Noisy graph dataset not created properly.")
            sys.exit(1)

if __name__ == "__main__":
    main()
