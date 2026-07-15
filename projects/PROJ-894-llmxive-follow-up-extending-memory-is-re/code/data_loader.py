"""
Data Loader for LoCoMo Benchmark and Synthetic Noisy Graph Generation.

This script fetches the LoCoMo benchmark dataset from HuggingFace and generates
a synthetic noisy graph dataset by injecting distractor edges into the memory graphs
constructed from the benchmark data.

Requirements:
- datasets (from HuggingFace)
- graph_utils (local module)
- config (local module)
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from datasets import load_dataset
from tqdm import tqdm

# Local imports matching the provided API surface
from graph_utils import build_memory_graph, inject_noise, validate_graph, get_graph_statistics
from config import get_huggingface_cache_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HF_DATASET_NAME = "locomo/locomo-benchmark"
HF_SPLIT = "test"
HF_COLUMNS = ["question", "context", "answer"]
NOISE_PROPORTION = 0.1  # 10% of edges replaced with distractors
RANDOM_SEED = 42
OUTPUT_DIR = Path("data") / "processed"
RAW_DATA_FILE = OUTPUT_DIR / "locomo_raw.json"
NOISY_GRAPHS_FILE = OUTPUT_DIR / "noisy_graphs.json"

def ensure_output_dirs():
    """Create output directories if they don't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {OUTPUT_DIR}")

def fetch_locomo_dataset() -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.

    Returns:
        List of dictionaries containing question, context, and answer.
    """
    logger.info(f"Fetching dataset: {HF_DATASET_NAME} (split: {HF_SPLIT})")
    
    try:
        dataset = load_dataset(
            HF_DATASET_NAME,
            split=HF_SPLIT,
            cache_dir=get_huggingface_cache_dir()
        )
    except Exception as e:
        logger.error(f"Failed to load dataset from HuggingFace: {e}")
        raise RuntimeError(f"Could not fetch LoCoMo benchmark: {e}")

    # Validate columns
    missing_cols = [col for col in HF_COLUMNS if col not in dataset.column_names]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    logger.info(f"Successfully loaded {len(dataset)} examples from LoCoMo benchmark.")
    
    # Convert to list of dicts
    data = []
    for item in dataset:
        data.append({
            "question": item["question"],
            "context": item["context"],
            "answer": item["answer"]
        })
    
    return data

def save_raw_data(data: List[Dict[str, Any]], filepath: Path):
    """Save raw dataset to JSON file."""
    logger.info(f"Saving raw data to {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} records to {filepath}")

def generate_noisy_graphs(
    data: List[Dict[str, Any]], 
    noise_proportion: float = NOISE_PROPORTION, 
    seed: int = RANDOM_SEED
) -> List[Dict[str, Any]]:
    """
    Generate synthetic noisy graphs from the LoCoMo data.
    
    For each task:
    1. Build a memory graph from the context.
    2. Inject noise (distractor edges) based on the specified proportion.
    3. Validate the resulting graph.
    
    Args:
        data: List of task dictionaries (question, context, answer).
        noise_proportion: Fraction of edges to replace with random distractors.
        seed: Random seed for reproducibility.
    
    Returns:
        List of dictionaries containing task metadata and the noisy graph.
    """
    logger.info(f"Generating noisy graphs with noise proportion: {noise_proportion}")
    np.random.seed(seed)
    
    noisy_results = []
    
    for idx, task in enumerate(tqdm(data, desc="Processing tasks")):
        task_id = f"task_{idx:04d}"
        context = task["context"]
        
        # Build memory graph
        try:
            graph = build_memory_graph(context)
            stats_before = get_graph_statistics(graph)
            
            # Inject noise
            noisy_graph = inject_noise(graph, noise_proportion=noise_proportion, seed=seed + idx)
            
            # Validate graph
            is_valid = validate_graph(noisy_graph)
            stats_after = get_graph_statistics(noisy_graph)
            
            # Serialize graph for storage (NetworkX to JSON)
            # Convert nodes and edges to serializable format
            nodes = list(noisy_graph.nodes(data=True))
            edges = list(noisy_graph.edges(data=True))
            
            noisy_results.append({
                "task_id": task_id,
                "question": task["question"],
                "answer": task["answer"],
                "is_valid": is_valid,
                "stats_before": stats_before,
                "stats_after": stats_after,
                "graph_nodes": nodes,
                "graph_edges": edges
            })
            
        except Exception as e:
            logger.warning(f"Failed to process task {task_id}: {e}. Skipping.")
            # Continue processing other tasks
            continue
    
    logger.info(f"Generated {len(noisy_results)} noisy graph entries.")
    return noisy_results

def save_noisy_graphs(noisy_graphs: List[Dict[str, Any]], filepath: Path):
    """Save noisy graphs to JSON file."""
    logger.info(f"Saving noisy graphs to {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(noisy_graphs, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(noisy_graphs)} noisy graph entries to {filepath}")

def main():
    """Main entry point for the data loading and graph generation pipeline."""
    logger.info("Starting LoCoMo data loading and noisy graph generation pipeline.")
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    # Fetch raw data
    raw_data = fetch_locomo_dataset()
    
    # Save raw data
    save_raw_data(raw_data, RAW_DATA_FILE)
    
    # Generate noisy graphs
    noisy_graphs = generate_noisy_graphs(raw_data)
    
    # Save noisy graphs
    save_noisy_graphs(noisy_graphs, NOISY_GRAPHS_FILE)
    
    logger.info("Pipeline completed successfully.")
    logger.info(f"Raw data saved to: {RAW_DATA_FILE}")
    logger.info(f"Noisy graphs saved to: {NOISY_GRAPHS_FILE}")

if __name__ == "__main__":
    main()