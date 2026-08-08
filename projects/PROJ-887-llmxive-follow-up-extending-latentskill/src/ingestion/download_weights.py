"""
Download LoRA weights for ALFWorld and Search-QA benchmarks.

Fetches real weights from HuggingFace datasets 'latent-skills/alfworld-weights'
and 'latent-skills/searchqa-weights'. If real weights are unavailable, generates
a documented proxy using numpy.random.normal with matching shapes.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from huggingface_hub import HfApi, hf_hub_download, list_repo_files
from datasets import load_dataset

from src.utils.config import get_config, get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_IDS = {
    'alfworld': 'latent-skills/alfworld-weights',
    'searchqa': 'latent-skills/searchqa-weights'
}

PROXY_OUTPUT_DIR = 'data/processed/proxy_weights'
METADATA_FILE = 'download_metadata.json'

def verify_source_existence(dataset_id: str) -> bool:
    """Verify if the dataset exists on HuggingFace."""
    try:
        api = HfApi()
        # Try to list files to verify existence
        files = list_repo_files(dataset_id, repo_type="dataset")
        if files:
            logger.info(f"Dataset {dataset_id} exists and is accessible.")
            return True
    except Exception as e:
        logger.warning(f"Dataset {dataset_id} not accessible: {e}")
    return False

def generate_proxy_weights(
    dataset_id: str, 
    output_dir: Path, 
    expected_shapes: Dict[str, Tuple[int, int]]
) -> Dict[str, Any]:
    """
    Generate proxy weights using numpy.random.normal with matching shapes.
    
    Args:
        dataset_id: The HuggingFace dataset ID
        output_dir: Directory to save proxy weights
        expected_shapes: Dict mapping matrix names to (rows, cols)
        
    Returns:
        Metadata dictionary about the generated proxy
    """
    logger.info(f"Generating proxy weights for {dataset_id}")
    
    proxy_data = {}
    for matrix_name, shape in expected_shapes.items():
        # Generate random normal data with specified shape and dtype float32
        weight_matrix = np.random.normal(
            loc=0.0, 
            scale=0.02,  # Small scale typical for LoRA initialization
            size=shape
        ).astype(np.float32)
        
        # Save to file
        matrix_path = output_dir / f"{matrix_name}.npy"
        np.save(str(matrix_path), weight_matrix)
        logger.debug(f"Saved proxy matrix {matrix_name} with shape {shape}")
        
        proxy_data[matrix_name] = {
            'shape': list(shape),
            'dtype': 'float32',
            'path': str(matrix_path),
            'is_proxy': True
        }
    
    return proxy_data

def download_real_weights(
    dataset_id: str, 
    output_dir: Path
) -> Tuple[Dict[str, Any], bool]:
    """
    Download real weights from HuggingFace.
    
    Args:
        dataset_id: The HuggingFace dataset ID
        output_dir: Directory to save weights
        
    Returns:
        Tuple of (metadata dict, success boolean)
    """
    logger.info(f"Attempting to download real weights from {dataset_id}")
    
    try:
        # Load the dataset
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        metadata = {
            'dataset_id': dataset_id,
            'is_proxy': False,
            'source': 'huggingface',
            'weights': {}
        }
        
        # Process each sample in the dataset
        count = 0
        for sample in dataset:
            count += 1
            # Assuming sample contains A and B matrices
            # This structure may need adjustment based on actual dataset format
            if 'A' in sample and 'B' in sample:
                matrix_name = f"adapter_{count}"
                
                # Convert to numpy arrays
                A = np.array(sample['A']).astype(np.float32)
                B = np.array(sample['B']).astype(np.float32)
                
                # Save matrices
                A_path = output_dir / f"{matrix_name}_A.npy"
                B_path = output_dir / f"{matrix_name}_B.npy"
                np.save(str(A_path), A)
                np.save(str(B_path), B)
                
                metadata['weights'][matrix_name] = {
                    'A': {
                        'shape': list(A.shape),
                        'dtype': 'float32',
                        'path': str(A_path),
                        'is_proxy': False
                    },
                    'B': {
                        'shape': list(B.shape),
                        'dtype': 'float32',
                        'path': str(B_path),
                        'is_proxy': False
                    }
                }
        
        logger.info(f"Successfully downloaded {count} real adapters from {dataset_id}")
        return metadata, True
        
    except Exception as e:
        logger.error(f"Failed to download real weights: {e}")
        return {}, False

def run_citation_check() -> bool:
    """Run the citation check script to verify data sources."""
    logger.info("Running citation check to verify data sources...")
    try:
        # Import and run the citation check
        from src.validate.citation_check import check_all_sources
        result = check_all_sources()
        if result:
            logger.info("Citation check passed - all sources verified")
            return True
        else:
            logger.warning("Citation check failed - some sources may be invalid")
            return False
    except Exception as e:
        logger.error(f"Error running citation check: {e}")
        return False

def main():
    """Main function to download weights or generate proxies."""
    config = get_config()
    project_root = get_project_root()
    
    # Run citation check first
    citation_ok = run_citation_check()
    if not citation_ok:
        logger.warning("Citation check did not pass, proceeding with caution")
    
    # Create output directories
    output_base = project_root / PROXY_OUTPUT_DIR
    output_base.mkdir(parents=True, exist_ok=True)
    
    all_metadata = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'datasets': {}
    }
    
    for dataset_name, dataset_id in DATASET_IDS.items():
        logger.info(f"Processing dataset: {dataset_name} ({dataset_id})")
        
        # Verify source existence
        if not verify_source_existence(dataset_id):
            logger.warning(f"Dataset {dataset_id} not available, generating proxy")
            
            # Define expected shapes for proxy generation
            # These are typical LoRA shapes - adjust based on actual dataset
            expected_shapes = {
                'A': (64, 32),  # Down projection
                'B': (32, 64)   # Up projection
            }
            
            dataset_output_dir = output_base / dataset_name
            dataset_output_dir.mkdir(parents=True, exist_ok=True)
            
            proxy_data = generate_proxy_weights(
                dataset_id, 
                dataset_output_dir, 
                expected_shapes
            )
            
            all_metadata['datasets'][dataset_name] = {
                'dataset_id': dataset_id,
                'is_proxy': True,
                'source': 'generated',
                'weights': proxy_data,
                'note': 'Real weights unavailable - proxy generated with numpy.random.normal'
            }
        else:
            # Attempt to download real weights
            dataset_output_dir = output_base / dataset_name
            dataset_output_dir.mkdir(parents=True, exist_ok=True)
            
            metadata, success = download_real_weights(dataset_id, dataset_output_dir)
            
            if success:
                all_metadata['datasets'][dataset_name] = metadata
            else:
                logger.warning(f"Failed to download real weights for {dataset_id}, generating proxy")
                
                # Generate proxy as fallback
                expected_shapes = {
                    'A': (64, 32),
                    'B': (32, 64)
                }
                
                proxy_data = generate_proxy_weights(
                    dataset_id, 
                    dataset_output_dir, 
                    expected_shapes
                )
                
                all_metadata['datasets'][dataset_name] = {
                    'dataset_id': dataset_id,
                    'is_proxy': True,
                    'source': 'generated',
                    'weights': proxy_data,
                    'note': 'Real weights download failed - proxy generated'
                }
    
    # Save metadata
    metadata_path = output_base / METADATA_FILE
    with open(metadata_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    logger.info(f"Download complete. Metadata saved to {metadata_path}")
    
    # Log summary
    proxy_count = sum(1 for d in all_metadata['datasets'].values() if d.get('is_proxy', False))
    real_count = len(all_metadata['datasets']) - proxy_count
    logger.info(f"Summary: {real_count} real datasets, {proxy_count} proxy datasets")
    
    if proxy_count > 0:
        logger.warning("Some datasets were generated as proxies. Ensure this is acceptable for your use case.")

if __name__ == "__main__":
    main()
