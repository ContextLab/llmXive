"""
Download LoRA weights from HuggingFace datasets for ALFWorld and Search-QA.

If real weights are unavailable, generate documented proxy weights using
numpy.random.normal with seed=42, mean=0, std=1, preserving statistical properties.

Outputs:
  - data/raw/proxy_alfworld_weights.npz (if real weights unavailable)
  - data/raw/proxy_searchqa_weights.npz (if real weights unavailable)
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import json

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_project_paths, load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected dataset paths
DATASET_CONFIGS = {
    'alfworld': {
        'dataset_id': 'latent-skills/alfworld-weights',
        'path': 'weights/alfworld/*.npz',
        'output_file': 'data/raw/proxy_alfworld_weights.npz',
        'expected_shape': (512, 128),  # Example shape, will be inferred
    },
    'searchqa': {
        'dataset_id': 'latent-skills/searchqa-weights',
        'path': 'weights/searchqa/*.npz',
        'output_file': 'data/raw/proxy_searchqa_weights.npz',
        'expected_shape': (512, 128),  # Example shape, will be inferred
    }
}

def load_real_weights(dataset_id: str, path_pattern: str) -> Optional[Tuple[Dict[str, np.ndarray], bool]]:
    """
    Attempt to load real weights from HuggingFace dataset.
    
    Returns:
        Tuple of (weights_dict, is_proxy) or None if dataset not found.
    """
    try:
        # Try to import datasets library
        from datasets import load_dataset
        from pathlib import Path as PPath
        import glob
        
        logger.info(f"Attempting to load real weights from dataset: {dataset_id}")
        
        # Load dataset
        dataset = load_dataset(dataset_id, split='train', streaming=True)
        
        # Collect all weight files
        weights = {}
        count = 0
        
        for item in dataset:
            # Check if this item contains weight data
            if 'weights' in item or 'weight' in item:
                # Handle different weight formats
                for key, value in item.items():
                    if 'weight' in key.lower() and isinstance(value, (list, np.ndarray)):
                        arr = np.array(value) if not isinstance(value, np.ndarray) else value
                        weights[key] = arr
                        count += 1
            
            # Also check for file-like entries
            for key, value in item.items():
                if isinstance(value, dict) and 'path' in value:
                    # This might be a file reference
                    pass
            
            if count > 0:
                break  # Found some weights
        
        if count == 0:
            logger.warning(f"No weight data found in dataset {dataset_id}")
            return None
        
        logger.info(f"Successfully loaded {count} weight matrices from {dataset_id}")
        return weights, False
        
    except Exception as e:
        logger.warning(f"Failed to load real weights from {dataset_id}: {e}")
        return None

def generate_proxy_weights(dataset_name: str, expected_shape: Tuple[int, int]) -> Dict[str, np.ndarray]:
    """
    Generate proxy weights using numpy.random.normal with seed=42, mean=0, std=1.
    
    Args:
        dataset_name: Name of the dataset (alfworld or searchqa)
        expected_shape: Expected shape of the weight matrices
    
    Returns:
        Dictionary of weight matrices
    """
    logger.info(f"Generating proxy weights for {dataset_name} with seed=42, mean=0, std=1")
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate A and B matrices with specified statistical properties
    # Using mean=0, std=1 as specified
    shape_a = (expected_shape[0], expected_shape[1] // 2)  # A matrix (down projection)
    shape_b = (expected_shape[1] // 2, expected_shape[1])  # B matrix (up projection)
    
    # Generate with mean=0, std=1
    A = np.random.normal(loc=0.0, scale=1.0, size=shape_a)
    B = np.random.normal(loc=0.0, scale=1.0, size=shape_b)
    
    # Ensure structural identity (preserve dimensions and statistical properties)
    proxy_weights = {
        'A': A.astype(np.float32),
        'B': B.astype(np.float32),
        'is_proxy': True,
        'generation_seed': 42,
        'mean': 0.0,
        'std': 1.0,
        'dataset_name': dataset_name,
        'shape': expected_shape
    }
    
    logger.info(f"Generated proxy weights with shape A: {A.shape}, B: {B.shape}")
    logger.info(f"Proxy statistics - Mean: {np.mean(A):.6f}, Std: {np.std(A):.6f}")
    
    return proxy_weights

def save_weights(weights: Dict[str, np.ndarray], output_path: str, is_proxy: bool = False) -> str:
    """
    Save weights to .npz file with metadata.
    
    Args:
        weights: Dictionary of weight matrices
        output_path: Path to save the .npz file
        is_proxy: Whether these are proxy weights
    
    Returns:
        Path to saved file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for saving
    save_data = {}
    for key, value in weights.items():
        if isinstance(value, (np.ndarray, np.floating, np.integer)):
            save_data[key] = value
        elif isinstance(value, bool):
            save_data[key] = np.array(value)
        elif isinstance(value, (int, float, str)):
            save_data[key] = np.array(value)
    
    # Save as .npz
    np.savez_compressed(output_file, **save_data)
    
    logger.info(f"Saved weights to {output_file} (is_proxy={is_proxy})")
    
    # Also save metadata as JSON
    metadata_file = output_file.with_suffix('.json')
    metadata = {
        'is_proxy': is_proxy,
        'dataset_name': weights.get('dataset_name', 'unknown'),
        'generation_seed': weights.get('generation_seed', None),
        'mean': weights.get('mean', None),
        'std': weights.get('std', None),
        'shape': weights.get('shape', None),
        'saved_at': str(Path(__file__).resolve())
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return str(output_file)

def process_dataset(dataset_name: str, config: Dict[str, Any]) -> str:
    """
    Process a single dataset: try real weights, fall back to proxy.
    
    Args:
        dataset_name: Name of the dataset
        config: Dataset configuration
    
    Returns:
        Path to saved weights file
    """
    logger.info(f"Processing dataset: {dataset_name}")
    
    # Try to load real weights
    real_weights = load_real_weights(config['dataset_id'], config['path'])
    
    if real_weights is not None:
        weights, is_proxy = real_weights
        logger.info(f"Using real weights from {config['dataset_id']}")
    else:
        # Generate proxy weights
        logger.warning(f"Real weights not available for {dataset_name}, generating proxy")
        weights = generate_proxy_weights(dataset_name, config.get('expected_shape', (512, 128)))
        is_proxy = True
    
    # Save weights
    output_path = save_weights(weights, config['output_file'], is_proxy)
    
    return output_path

def main():
    """Main entry point for weight download/generation."""
    logger.info("Starting weight download/generation process")
    
    # Load configuration
    config = load_config()
    paths = get_project_paths()
    
    # Ensure output directories exist
    raw_data_dir = paths['raw_data']
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Process each dataset
    for dataset_name, dataset_config in DATASET_CONFIGS.items():
        try:
            output_path = process_dataset(dataset_name, dataset_config)
            results[dataset_name] = {
                'status': 'success',
                'output_file': output_path,
                'is_proxy': 'proxy' in output_path
            }
            logger.info(f"Successfully processed {dataset_name}: {output_path}")
        except Exception as e:
            logger.error(f"Failed to process {dataset_name}: {e}")
            results[dataset_name] = {
                'status': 'failed',
                'error': str(e)
            }
    
    # Log summary
    logger.info("=" * 50)
    logger.info("Weight download/generation summary:")
    for name, result in results.items():
        logger.info(f"  {name}: {result['status']} - {result.get('output_file', result.get('error', 'N/A'))}")
    
    # Save results summary
    summary_file = raw_data_dir / 'weight_download_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Summary saved to {summary_file}")
    
    # Verify outputs exist
    for name, result in results.items():
        if result['status'] == 'success':
            output_path = Path(result['output_file'])
            if not output_path.exists():
                raise RuntimeError(f"Output file does not exist: {output_path}")
            logger.info(f"Verified output exists: {output_path}")
    
    logger.info("Weight download/generation process completed successfully")
    return results

if __name__ == '__main__':
    main()
