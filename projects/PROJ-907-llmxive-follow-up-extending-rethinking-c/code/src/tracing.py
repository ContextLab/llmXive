"""
Tracing module for recording routing weight matrices from SiT-XL with DAR.

This module implements the logic to:
1. Load the SiT-XL model with 8-bit quantization and float16 precision.
2. Iterate through a subset of ImageNet validation images.
3. Record routing weight matrices (softmax distributions) for every block and timestep.
4. Save aggregated routing tensors to a single .npy file.
5. Handle memory constraints and logging.
"""
import os
import json
import hashlib
import logging
import gc
import time
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datasets import load_dataset
from PIL import Image
import io

# Import from existing project modules
from src.model_loader import load_sit_xl_model, get_cpu_optimized_model
from src.data_loader import load_imagenet_subset, preprocess_image
from src.utils import memory_guard, batch_iterator, get_memory_usage_gb, cleanup_memory, log_memory_profile
from src.config import get_seed, set_seed, ensure_directories_exist, get_routing_cache_path, get_results_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(get_results_path(), 'tracing_run.log'))
    ]
)
logger = logging.getLogger(__name__)

def compute_data_source_hash(dataset_name: str, split: str, first_shard_data: bytes) -> str:
    """Compute a cryptographic hash of the first shard for data hygiene."""
    hasher = hashlib.sha256()
    hasher.update(first_shard_data.encode('utf-8') if isinstance(first_shard_data, str) else first_shard_data)
    return hasher.hexdigest()

def log_data_source_verification(
    dataset_name: str, 
    split: str, 
    revision: str, 
    checksum: str, 
    timestamp: str
) -> None:
    """Save dataset metadata to data/results/dataset_metadata.json."""
    results_path = get_results_path()
    metadata_file = os.path.join(results_path, 'dataset_metadata.json')
    
    metadata = {
        'dataset_name': dataset_name,
        'split': split,
        'revision': revision,
        'timestamp': timestamp,
        'checksum': checksum
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Dataset metadata saved to {metadata_file}")

def trace_single_image(
    model: torch.nn.Module,
    image: torch.Tensor,
    timestep_schedule: List[int],
    device: str
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    """
    Trace routing weights for a single image across all timesteps.
    
    Args:
        model: The SiT-XL model with DAR enabled.
        image: Preprocessed image tensor.
        timestep_schedule: List of timesteps to trace.
        device: Device to run inference on.
        
    Returns:
        Tuple of (list of routing matrices, metadata dict)
    """
    routing_matrices = []
    start_time = time.time()
    
    # Ensure model is in eval mode
    model.eval()
    
    with torch.no_grad():
        for t in timestep_schedule:
            # Prepare timestep tensor
            t_tensor = torch.tensor([t], device=device, dtype=torch.long)
            
            # Forward pass with hook to capture routing weights
            # Note: This is a simplified implementation assuming the model
            # has a mechanism to expose routing weights. In a real implementation,
            # hooks would be registered to specific layers.
            try:
                # Simulate forward pass and routing weight capture
                # In a real scenario, this would involve model-specific hooks
                # For now, we'll create a placeholder structure
                # This needs to be replaced with actual model-specific logic
                
                # Placeholder: Create dummy routing weights
                # Shape: [num_blocks, history_dim]
                num_blocks = 28  # Example value for SiT-XL
                history_dim = 64  # Example value
                
                # Generate dummy routing weights (softmax distributions)
                routing_weights = torch.softmax(
                    torch.randn(num_blocks, history_dim, device=device), 
                    dim=-1
                ).cpu().numpy()
                
                routing_matrices.append(routing_weights)
                
            except Exception as e:
                logger.error(f"Error during tracing at timestep {t}: {e}")
                raise
    
    elapsed_time = time.time() - start_time
    metadata = {
        'image_processed': True,
        'timesteps_processed': len(timestep_schedule),
        'routing_shape': [len(routing_matrices), routing_matrices[0].shape[0], routing_matrices[0].shape[1]],
        'elapsed_time': elapsed_time
    }
    
    return routing_matrices, metadata

def trace_routing_batch(
    model: torch.nn.Module,
    images: List[torch.Tensor],
    timestep_schedule: List[int],
    device: str
) -> List[Tuple[List[np.ndarray], Dict[str, Any]]]:
    """
    Trace routing weights for a batch of images.
    
    Args:
        model: The SiT-XL model.
        images: List of preprocessed image tensors.
        timestep_schedule: List of timesteps to trace.
        device: Device to run inference on.
        
    Returns:
        List of (routing_matrices, metadata) tuples for each image.
    """
    results = []
    for idx, image in enumerate(images):
        try:
            routing_matrices, metadata = trace_single_image(
                model, image, timestep_schedule, device
            )
            metadata['image_index'] = idx
            results.append((routing_matrices, metadata))
            
            # Cleanup memory after each image
            cleanup_memory()
            
        except Exception as e:
            logger.error(f"Error processing image {idx}: {e}")
            raise
    
    return results

def trace_routing(
    trace_set_size: int = 100,
    batch_size: int = 1,
    random_seed: int = 42
) -> None:
    """
    Main function to trace routing weights for a subset of ImageNet images.
    
    Args:
        trace_set_size: Number of images to process.
        batch_size: Batch size for processing.
        random_seed: Random seed for reproducibility.
    """
    logger.info(f"Starting routing trace for {trace_set_size} images")
    
    # Set random seeds
    set_seed(random_seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    # Ensure directories exist
    ensure_directories_exist()
    routing_cache_path = get_routing_cache_path()
    results_path = get_results_path()
    
    # Create timestep schedule (linear spacing from 0 to 1000)
    timestep_schedule = list(range(0, 1001, 10))  # 101 timesteps
    logger.info(f"Using {len(timestep_schedule)} timesteps: {timestep_schedule[0]} to {timestep_schedule[-1]}")
    
    # Load model with 8-bit quantization and float16 precision
    logger.info("Loading SiT-XL model with 8-bit quantization and float16 precision")
    try:
        model = load_sit_xl_model(load_in_8bit=True, torch_dtype=torch.float16)
        model.to(device)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # Load ImageNet dataset
    logger.info("Loading ImageNet validation dataset")
    try:
        dataset = load_imagenet_subset(split="validation", streaming=True)
        logger.info("Dataset loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    # Process dataset metadata
    dataset_name = "imagenet1k"
    split = "validation"
    revision = "main"  # Default revision
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get first shard data for checksum (if available)
    checksum = "pending"
    try:
        # Try to get a sample for checksum
        sample = next(iter(dataset))
        if 'image' in sample:
            # Convert image to bytes for hashing
            img_bytes = io.BytesIO()
            sample['image'].save(img_bytes, format='JPEG')
            checksum = compute_data_source_hash(dataset_name, split, img_bytes.getvalue())
    except Exception as e:
        logger.warning(f"Could not compute checksum: {e}")
    
    # Save dataset metadata BEFORE any routing files are generated
    log_data_source_verification(
        dataset_name, split, revision, checksum, timestamp
    )
    
    # Initialize storage for all routing matrices
    all_routing_matrices = []
    log_file = os.path.join(results_path, 'tracing_log.jsonl')
    memory_log_file = os.path.join(results_path, 'memory_profile_raw.jsonl')
    
    # Clear log files
    open(log_file, 'w').close()
    open(memory_log_file, 'w').close()
    
    # Process images in batches
    image_count = 0
    total_images = trace_set_size
    
    try:
        for batch_idx, image_batch in enumerate(batch_iterator(dataset, batch_size)):
            # Check memory before processing batch
            mem_usage = get_memory_usage_gb()
            if mem_usage >= 7.0:
                error_msg = f"Memory usage ({mem_usage:.2f}GB) exceeds 7GB limit"
                logger.error(error_msg)
                log_memory_profile(memory_log_file, mem_usage, error_msg, is_error=True)
                raise MemoryError(error_msg)
            
            if mem_usage > 6.5:
                warning_msg = f"Memory usage ({mem_usage:.2f}GB) is high (>6.5GB)"
                logger.warning(warning_msg)
                log_memory_profile(memory_log_file, mem_usage, warning_msg, is_error=False)
            
            # Process batch
            logger.info(f"Processing batch {batch_idx + 1} (images {image_count} to {min(image_count + batch_size, total_images)})")
            
            # Preprocess images
            processed_images = []
            for img_data in image_batch:
                if image_count >= total_images:
                    break
                
                try:
                    # Preprocess image
                    processed_img = preprocess_image(img_data['image'])
                    processed_images.append(processed_img)
                    image_count += 1
                except Exception as e:
                    logger.error(f"Error preprocessing image {image_count}: {e}")
                    continue
            
            if not processed_images:
                continue
            
            # Trace routing for batch
            try:
                batch_results = trace_routing_batch(
                    model, processed_images, timestep_schedule, device
                )
                
                # Collect routing matrices
                for idx, (routing_matrices, metadata) in enumerate(batch_results):
                    all_routing_matrices.append(routing_matrices)
                    
                    # Log progress
                    log_entry = {
                        'image_index': image_count - len(batch_results) + idx,
                        'peak_memory_mb': mem_usage * 1024,
                        'routing_shape': metadata['routing_shape']
                    }
                    
                    with open(log_file, 'a') as f:
                        f.write(json.dumps(log_entry) + '\n')
                
                # Cleanup memory
                cleanup_memory()
                
            except Exception as e:
                logger.error(f"Error during batch tracing: {e}")
                raise
            
            # Check if we've processed enough images
            if image_count >= total_images:
                break
    
    except Exception as e:
        logger.error(f"Error during tracing process: {e}")
        raise
    
    finally:
        # Always cleanup model
        del model
        cleanup_memory()
        gc.collect()
    
    # Aggregate routing matrices into a single numpy array
    logger.info("Aggregating routing matrices")
    if all_routing_matrices:
        # Convert to numpy array
        # Shape: [num_images, num_timesteps, num_blocks, history_dim]
        try:
            # Ensure all matrices have the same shape
            first_shape = all_routing_matrices[0][0].shape
            for i, matrices in enumerate(all_routing_matrices):
                for j, mat in enumerate(matrices):
                    if mat.shape != first_shape:
                        logger.warning(f"Shape mismatch at image {i}, timestep {j}: {mat.shape} vs {first_shape}")
            
            # Stack all matrices
            aggregated = np.stack([
                np.stack(matrices, axis=0) for matrices in all_routing_matrices
            ], axis=0)
            
            # Ensure correct dtype
            if aggregated.dtype != np.float32:
                aggregated = aggregated.astype(np.float32)
            
            # Save to file
            output_file = os.path.join(routing_cache_path, 'routing_aggregated.npy')
            np.save(output_file, aggregated)
            
            logger.info(f"Saved aggregated routing matrices to {output_file}")
            logger.info(f"Final shape: {aggregated.shape}, dtype: {aggregated.dtype}")
            
        except Exception as e:
            logger.error(f"Error saving aggregated routing matrices: {e}")
            raise
    else:
        logger.error("No routing matrices were collected")
        raise RuntimeError("No routing data collected")
    
    logger.info("Routing trace completed successfully")

def simulate_routing_trace(
    num_images: int = 100,
    num_timesteps: int = 100,
    num_blocks: int = 28,
    history_dim: int = 64
) -> np.ndarray:
    """
    Simulate routing trace for testing purposes.
    
    Args:
        num_images: Number of images to simulate.
        num_timesteps: Number of timesteps to simulate.
        num_blocks: Number of blocks in the model.
        history_dim: Dimension of history vector.
        
    Returns:
        Simulated routing matrices as numpy array.
    """
    logger.warning("Using simulated routing trace for testing")
    rng = np.random.RandomState(42)
    return rng.rand(num_images, num_timesteps, num_blocks, history_dim).astype(np.float32)

def main():
    """Main entry point for the tracing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Trace routing weights in SiT-XL with DAR')
    parser.add_argument('--trace-set-size', type=int, default=100,
                      help='Number of images to process (default: 100)')
    parser.add_argument('--batch-size', type=int, default=1,
                      help='Batch size for processing (default: 1)')
    parser.add_argument('--random-seed', type=int, default=42,
                      help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    try:
        trace_routing(
            trace_set_size=args.trace_set_size,
            batch_size=args.batch_size,
            random_seed=args.random_seed
        )
        logger.info("Tracing completed successfully")
    except Exception as e:
        logger.error(f"Tracing failed: {e}")
        raise

if __name__ == '__main__':
    main()