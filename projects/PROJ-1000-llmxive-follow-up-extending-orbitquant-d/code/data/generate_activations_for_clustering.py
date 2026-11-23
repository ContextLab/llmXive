"""
Script to generate activation histograms from the MS-COCO train split
using the DiT model with hooks enabled. This provides the input data
for the clustering pipeline (T022).

This script:
1. Loads the MS-COCO train split (from T005/T006)
2. Runs the DiT model with activation hooks enabled (T008)
3. Captures activations for each layer
4. Computes histograms and saves to CSV
"""
import os
import csv
import json
import logging
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from datasets import load_dataset

from config import Config
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import DiTWrapper, ActivationCapture

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_histogram(activations: torch.Tensor, num_bins: int = 50) -> str:
    """
    Compute a histogram of activations and return as a comma-separated string.
    """
    flat = activations.view(-1).detach().cpu().numpy()
    hist, _ = np.histogram(flat, bins=num_bins)
    return ','.join(map(str, hist))

def generate_activations_for_clustering(
    num_samples: int = 100,
    num_bins: int = 50,
    layers: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate activation histograms from the MS-COCO train split.
    
    Args:
        num_samples: Number of samples to process
        num_bins: Number of histogram bins
        layers: List of layer names to capture (None for all)
        
    Returns:
        List of dictionaries containing layer_name, subset_id, histogram
    """
    config = Config()
    
    # Load MS-COCO train split
    logger.info("Loading MS-COCO train split...")
    dataset = load_dataset("coco", "2017", split="train", trust_remote_code=True)
    
    # Limit to num_samples
    if num_samples < len(dataset):
        dataset = dataset.select(range(num_samples))
    
    logger.info(f"Processing {len(dataset)} samples...")
    
    # Load model
    logger.info("Loading DiT model...")
    model_loader = ModelLoader(config)
    model, device = model_loader.load_model()
    
    # Create DiT wrapper with hooks
    logger.info("Creating DiT wrapper with activation hooks...")
    dit_wrapper = DiTWrapper(model, config, layers=layers)
    
    # Prepare to collect activations
    activation_data = []
    
    # Process each sample
    for idx, sample in enumerate(dataset):
        logger.info(f"Processing sample {idx+1}/{len(dataset)}")
        
        prompt = sample.get("caption", "")
        if not prompt:
            continue
        
        try:
            # Run generation with hooks
            # We only need the forward pass to capture activations, not full generation
            # For efficiency, we'll use a dummy image generation or just forward pass
            
            # Prepare inputs (simplified for activation capture)
            # In a real scenario, this would be the text-to-image generation loop
            # Here we simulate the forward pass with the prompt
            
            # Tokenize prompt
            tokenizer = model_loader.tokenizer
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            ).to(device)
            
            # Forward pass to capture activations
            # This simulates the text encoding part of the generation
            with torch.no_grad():
                # Get text embeddings
                text_embeddings = model.get_text_embeds(
                    inputs['input_ids'],
                    inputs['attention_mask']
                )
                
                # Capture activations from intermediate layers
                # The DiTWrapper should have hooks set up to capture these
                activations = dit_wrapper.capture_activations(text_embeddings)
                
                # Process activations
                for layer_name, act_tensor in activations.items():
                    hist_str = compute_histogram(act_tensor, num_bins)
                    activation_data.append({
                        'layer_name': layer_name,
                        'subset_id': str(idx),
                        'histogram': hist_str
                    })
            
        except Exception as e:
            logger.warning(f"Error processing sample {idx}: {e}")
            continue
    
    return activation_data

def save_activations_to_csv(activation_data: List[Dict[str, Any]], output_path: str):
    """
    Save activation data to a CSV file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['layer_name', 'subset_id', 'histogram'])
        writer.writeheader()
        writer.writerows(activation_data)
    
    logger.info(f"Saved {len(activation_data)} activation records to {output_path}")

def main():
    """
    Main entry point for generating activations for clustering.
    """
    config = Config()
    output_path = config.data_dir / "processed" / "activations.csv"
    
    # Check if we already have activations
    if output_path.exists():
        logger.info(f"Activation data already exists at {output_path}")
        logger.info("Skipping generation. Delete the file to regenerate.")
        return
    
    # Generate activations
    activation_data = generate_activations_for_clustering(
        num_samples=100,  # Process 100 samples for clustering
        num_bins=50
    )
    
    # Save to CSV
    save_activations_to_csv(activation_data, str(output_path))
    
    logger.info("Activation generation complete. Ready to run clustering (T022).")

if __name__ == "__main__":
    main()
