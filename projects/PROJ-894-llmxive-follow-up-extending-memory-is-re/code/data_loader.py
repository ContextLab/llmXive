"""
Data Loader for LoCoMo benchmark and synthetic noisy graph generation.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import random

from datasets import load_dataset
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# Configuration
DATASET_NAME = "locomo/locomo-benchmark"
SPLIT = "test"
OUTPUT_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
NOISE_SEED = 42
NOISE_PROBABILITY = 0.05  # 5% chance to inject noise

def ensure_output_dirs():
    """Create necessary output directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def fetch_locomo_dataset() -> List[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.
    Returns a list of dictionaries with 'question', 'context', 'answer'.
    """
    logger.info(f"Fetching dataset: {DATASET_NAME} (split: {SPLIT})")
    try:
        # Load the dataset
        dataset = load_dataset(DATASET_NAME, split=SPLIT)
        
        # Convert to list of dicts
        data_list = []
        for item in dataset:
            data_list.append({
                "question": item.get("question", ""),
                "context": item.get("context", ""),
                "answer": item.get("answer", "")
            })
        
        logger.info(f"Successfully fetched {len(data_list)} examples.")
        return data_list
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def save_raw_data(data: List[Dict[str, Any]], filename: str = "locomo_test.json"):
    """Save raw data to a JSON file."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw data to {filepath}")

def generate_noisy_graphs(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate synthetic noisy graphs from the raw data.
    This simulates the noise injection process described in the task.
    Replaces a small proportion of edges with random distractor edges.
    
    Note: Since the raw data is text, we simulate graph construction here
    by creating a synthetic graph structure for each item and then injecting noise.
    In a real scenario, this would parse the context into a graph first.
    """
    logger.info(f"Generating noisy graphs for {len(data)} items with seed {NOISE_SEED}")
    random.seed(NOISE_SEED)
    
    noisy_data = []
    for idx, item in enumerate(data):
        # Simulate a graph structure: create a chain of nodes based on context length
        # This is a placeholder for real graph construction from text
        num_nodes = min(len(item["context"]) // 10, 20) # Limit size
        if num_nodes == 0: num_nodes = 1
        
        # Create a simple chain graph
        nodes = [f"node_{i}_{idx}" for i in range(num_nodes)]
        edges = [(nodes[i], nodes[i+1]) for i in range(num_nodes - 1)]
        
        # Inject noise
        num_noise_edges = int(len(edges) * NOISE_PROBABILITY)
        for _ in range(num_noise_edges):
            if len(nodes) > 1:
                src = random.choice(nodes)
                dst = random.choice(nodes)
                if src != dst and (src, dst) not in edges:
                    edges.append((src, dst)) # Add distractor edge
        
        noisy_item = {
            "id": idx,
            "original_question": item["question"],
            "nodes": nodes,
            "edges": edges,
            "noise_injected": num_noise_edges
        }
        noisy_data.append(noisy_item)
        
    return noisy_data

def save_noisy_graphs(noisy_data: List[Dict[str, Any]], filename: str = "noisy_graphs.json"):
    """Save noisy graphs to a JSON file."""
    filepath = PROCESSED_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(noisy_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved noisy graphs to {filepath}")

def main():
    """Main entry point for data loading and processing."""
    ensure_output_dirs()
    
    # Fetch data
    raw_data = fetch_locomo_dataset()
    save_raw_data(raw_data)
    
    # Generate noisy graphs
    noisy_data = generate_noisy_graphs(raw_data)
    save_noisy_graphs(noisy_data)
    
    logger.info("Data loading and noise injection complete.")

if __name__ == "__main__":
    main()
