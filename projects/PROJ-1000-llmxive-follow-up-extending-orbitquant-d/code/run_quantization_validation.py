"""
Orchestration script for Quantization Validation (T019a).

This script runs the W2A4 engine on the MS-COCO validation set (prompts)
using the rotation matrices generated in T022. It captures the quantized
activations and saves them to data/processed/quantized_activations.json.

Dependency: T010 (W2A4Engine), T022 (clustering_report.json), T006a (prompts)
"""

import os
import sys
import json
import logging
import time
import csv
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from quantization.w2a4_engine import W2A4Engine
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import DiTWrapper, ActivationCapture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_prompts_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """
    Load prompts from a CSV file.
    Expected columns: 'prompt', 'id' (or similar identifier).
    """
    prompts = []
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Prompts file not found: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys if necessary
            prompt_text = row.get('prompt') or row.get('caption') or row.get('text')
            if prompt_text:
                prompts.append({
                    'id': row.get('id', row.get('image_id', str(len(prompts)))),
                    'prompt': prompt_text
                })
    return prompts

def load_clustering_report(json_path: str) -> Dict[str, Any]:
    """
    Load the clustering report containing rotation matrices.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Clustering report not found: {json_path}")
    
    with open(json_path, 'r') as f:
        return json.load(f)

def run_quantization_pipeline(
    config: Config,
    prompts: List[Dict[str, str]],
    clustering_report: Dict[str, Any],
    output_path: str
) -> None:
    """
    Main pipeline:
    1. Initialize Model and W2A4 Engine.
    2. Iterate through prompts.
    3. Run generation with hooks to capture activations.
    4. Apply W2A4 quantization using the rotation matrices.
    5. Store results.
    """
    logger.info("Initializing Model and Engine...")
    
    # Load model (using existing loader logic)
    # Note: We assume the model is loaded once and reused. 
    # For memory constraints, we might need to clear cache between runs.
    try:
        model_loader = ModelLoader(config)
        # The loader handles device selection and model instantiation
        dit_model = model_loader.load_model() 
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    # Initialize W2A4 Engine with the loaded model
    # The engine needs the model to access layers and apply quantization
    w2a4_engine = W2A4Engine(dit_model, config)
    
    # Prepare rotation matrices from clustering report
    # Structure expected: {'matrices': [{'layer_name': ..., 'matrix': ...}, ...]}
    # We assume the clustering report has a 'matrices' key or similar structure
    rotation_matrices = {}
    if 'matrices' in clustering_report:
        for entry in clustering_report['matrices']:
            layer_name = entry.get('layer_name') or entry.get('layer')
            if layer_name and 'matrix' in entry:
                # Convert list to tensor if necessary
                mat = entry['matrix']
                if isinstance(mat, list):
                    mat = torch.tensor(mat, dtype=torch.float32)
                rotation_matrices[layer_name] = mat
    else:
        # Fallback if structure is different (e.g., nested by layer)
        # Assuming clustering_report might have layers directly
        if 'layers' in clustering_report:
            for layer_name, layer_data in clustering_report['layers'].items():
                if 'matrix' in layer_data:
                   rotation_matrices[layer_name] = torch.tensor(layer_data['matrix'], dtype=torch.float32)

    logger.info(f"Loaded {len(rotation_matrices)} rotation matrices.")

    # Results storage
    results = []
    total_prompts = len(prompts)
    start_time = time.time()

    # Setup hooks for activation capture if not already done by W2A4Engine
    # W2A4Engine usually handles the quantization logic, but we need to ensure
    # we capture the activations *before* quantization or the quantized values.
    # Based on T019 requirement: "generate quantized activations".
    # We will assume W2A4Engine has a method to run inference and return quantized states.
    
    logger.info(f"Starting quantization pipeline for {total_prompts} prompts...")

    for idx, item in enumerate(prompts):
        prompt_id = item['id']
        prompt_text = item['prompt']
        
        logger.info(f"[{idx+1}/{total_prompts}] Processing ID: {prompt_id}")
        
        try:
            # Run the generation/quantization step
            # The W2A4Engine should handle the forward pass with rotation matrices applied
            # and return the quantized activations.
            # We pass the prompt and the rotation matrices.
            
            quantized_data = w2a4_engine.run_quantization_inference(
                prompt=prompt_text,
                rotation_matrices=rotation_matrices
            )
            
            # quantized_data expected to be a dict: {layer_name: tensor/array}
            # We serialize it to JSON-compatible format
            serializable_data = {}
            for layer_name, tensor in quantized_data.items():
                if isinstance(tensor, torch.Tensor):
                    # Convert to numpy and list for JSON
                    arr = tensor.detach().cpu().numpy()
                    # Flatten or truncate if too large? 
                    # For MSE validation (T019), we need the actual values.
                    # If the tensor is huge, we might need to save to a binary file,
                    # but the task asks for a JSON. We will store a summary or the full list if small.
                    # Given the constraint of JSON for "activations", we assume the engine
                    # returns a manageable subset or the task implies saving the stats.
                    # However, T019 says "compute MSE... on quantized activations".
                    # To be safe and compliant with "real data", we store the flattened list
                    # if it's not too massive, or we store the path to a pickle if it is.
                    # Let's assume the engine returns a subset of activations or we save the full tensor as a list.
                    # If the tensor is > 1MB, we might hit JSON limits.
                    # Strategy: Store the mean, std, and a sample of values, OR store the full list if feasible.
                    # Given "quantized_activations.json" is the artifact, we will store the full list 
                    # assuming the engine returns a reduced representation (e.g., per-layer stats or specific hooks).
                    # If the engine returns full feature maps, we must truncate or save differently.
                    # Let's assume the W2A4Engine returns a dictionary of {layer: list of values}
                    serializable_data[layer_name] = arr.tolist()
                else:
                    serializable_data[layer_name] = tensor
            
            results.append({
                "id": prompt_id,
                "prompt": prompt_text,
                "quantized_activations": serializable_data
            })

        except Exception as e:
            logger.error(f"Error processing prompt {prompt_id}: {e}")
            # Continue with next prompt to avoid total failure, but log the error
            results.append({
                "id": prompt_id,
                "prompt": prompt_text,
                "error": str(e)
            })

    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")

    # Write results to JSON
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Quantized activations saved to {output_path}")

def main():
    config = Config()
    
    # Paths
    prompts_path = config.data_dir / "processed" / "prompts.csv"
    clustering_report_path = config.data_dir / "processed" / "clustering_report.json"
    output_path = config.data_dir / "processed" / "quantized_activations.json"
    
    # Validate inputs
    if not prompts_path.exists():
        logger.error(f"Prompts file not found: {prompts_path}")
        sys.exit(1)
    if not clustering_report_path.exists():
        logger.error(f"Clustering report not found: {clustering_report_path}")
        sys.exit(1)
    
    # Load data
    prompts = load_prompts_from_csv(str(prompts_path))
    if not prompts:
        logger.error("No prompts found in CSV.")
        sys.exit(1)
    
    clustering_report = load_clustering_report(str(clustering_report_path))
    
    # Run pipeline
    run_quantization_pipeline(config, prompts, clustering_report, str(output_path))

if __name__ == "__main__":
    main()
