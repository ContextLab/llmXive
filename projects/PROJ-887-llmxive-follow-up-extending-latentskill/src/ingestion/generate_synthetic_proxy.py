"""
T012c: Generate Synthetic Proxy for LoRA Weights.

This script acts as a conditional fallback ONLY. It checks
data/processed/data_fetch_status.json. If the status is "failed",
it generates synthetic LoRA-like weight matrices matching the
TinyLlama architecture (hidden_size=2048, rank=16, num_layers=16)
using seed=42. If the status is "success" or the file is missing,
it skips generation and exits cleanly.

Output: data/raw/synthetic_proxy_weights.npz
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants matching TinyLlama-1B
# Reference: 2411.15484 (TinyLlama architecture details)
HIDDEN_SIZE = 2048
RANK = 16
NUM_LAYERS = 16
SEED = 42
OUTPUT_PATH = "data/raw/synthetic_proxy_weights.npz"
STATUS_FILE = "data/processed/data_fetch_status.json"

def check_fetch_status():
    """Check the data fetch status file."""
    status_path = Path(STATUS_FILE)
    if not status_path.exists():
        logger.warning(f"Status file {STATUS_FILE} not found. Assuming success (no proxy needed).")
        return "success"
    
    try:
        with open(status_path, 'r') as f:
            data = json.load(f)
        return data.get('status', 'success')
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read status file: {e}")
        return "success" # Default to success to avoid blocking if file is corrupt

def generate_synthetic_weights():
    """
    Generate synthetic LoRA A and B matrices.
    
    Structure:
    - For each layer (NUM_LAYERS):
      - down_proj: A (rank, hidden_size), B (hidden_size, rank)
      - up_proj: A (rank, hidden_size), B (hidden_size, rank)
      - gate_proj: A (rank, hidden_size), B (hidden_size, rank)
      - o_proj: A (rank, hidden_size), B (hidden_size, rank)
      
    We simulate the flattened weight vectors for these matrices.
    """
    logger.info(f"Generating synthetic proxy weights (seed={SEED})...")
    np.random.seed(SEED)
    
    weights = {}
    
    # We will store flattened vectors for each matrix to match the expected
    # ingestion format of flattened LoRA weights.
    # Dimensions: hidden_size=2048, rank=16.
    # A matrix shape: (rank, hidden_size) -> 2048 * 16 = 32768 elements
    # B matrix shape: (hidden_size, rank) -> 2048 * 16 = 32768 elements
    
    dim_a = RANK * HIDDEN_SIZE
    dim_b = HIDDEN_SIZE * RANK
    
    for layer_idx in range(NUM_LAYERS):
        layer_key = f"layer_{layer_idx}"
        weights[layer_key] = {}
        
        # Simulate 4 projection types per layer (common in Llama)
        for proj_type in ["down", "up", "gate", "o"]:
            # Generate random weights with small variance (typical for LoRA init)
            # Using Xavier-like initialization logic for synthetic data
            a_matrix = np.random.randn(RANK, HIDDEN_SIZE).astype(np.float32) * 0.02
            b_matrix = np.random.randn(HIDDEN_SIZE, RANK).astype(np.float32) * 0.02
            
            # Flatten
            a_flat = a_matrix.flatten()
            b_flat = b_matrix.flatten()
            
            weights[layer_key][f"{proj_type}_a"] = a_flat
            weights[layer_key][f"{proj_type}_b"] = b_flat
    
    # Save to .npz
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten the dictionary structure for npz save
    # npz expects a flat dict of arrays: {'key': array}
    flat_weights = {}
    for layer_key, layer_data in weights.items():
        for mat_name, mat_data in layer_data.items():
            full_key = f"{layer_key}_{mat_name}"
            flat_weights[full_key] = mat_data
    
    np.savez(str(output_path), **flat_weights)
    logger.info(f"Successfully generated synthetic proxy at {output_path}")
    return True

def main():
    status = check_fetch_status()
    
    if status == "failed":
        logger.warning("Data fetch failed. Generating synthetic proxy weights.")
        generate_synthetic_weights()
        logger.info("SYNTHETIC DATA USED - Proceeding with proxy.")
        return 0
    else:
        logger.info(f"Data fetch status is '{status}'. Skipping synthetic proxy generation.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
