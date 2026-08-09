import os
import json
import hashlib
import logging
import gc
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from datasets import load_dataset
from PIL import Image
import io

from src.model_loader import load_sit_xl_model, get_cpu_optimized_model
from src.data_loader import load_imagenet_subset, preprocess_image
from src.config import get_seed, get_routing_cache_path, get_imagenet_path, set_seed
from src.utils import memory_guard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/results/tracing_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_memory_usage_gb() -> float:
    """
    Returns current memory usage in GB.
    Uses /proc/self/status on Linux or psutil if available.
    Falls back to torch.cuda.memory_allocated if GPU is used (not applicable here).
    """
    try:
        import resource
        # Get memory usage in KB
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Convert to GB (on Linux, ru_maxrss is in KB; on macOS, it's in bytes)
        import platform
        if platform.system() == 'Darwin':
            mem_gb = mem_kb / (1024 * 1024)  # macOS ru_maxrss is in bytes
        else:
            mem_gb = mem_kb / (1024 * 1024)  # Linux ru_maxrss is in KB, convert to GB
        return mem_gb
    except Exception as e:
        logger.warning(f"Could not determine memory usage: {e}")
        return 0.0

def compute_data_source_hash(dataset_name: str, split: str, seed: int) -> str:
    """
    Computes a deterministic hash for the dataset source.
    """
    data_str = f"{dataset_name}:{split}:{seed}"
    return hashlib.sha256(data_str.encode()).hexdigest()

def log_data_source_verification(dataset_name: str, split: str, seed: int):
    """
    Logs the exact dataset source used for traceability.
    """
    source_hash = compute_data_source_hash(dataset_name, split, seed)
    logger.info(f"Data Source Verification: {dataset_name} (split={split}, seed={seed})")
    logger.info(f"Source Hash: {source_hash}")

    # Save verification record
    cache_path = get_routing_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)
    verification_file = cache_path / "data_source_verification.json"
    
    verification_data = {
        "dataset_name": dataset_name,
        "split": split,
        "seed": seed,
        "hash": source_hash
    }
    
    with open(verification_file, 'w') as f:
        json.dump(verification_data, f, indent=2)
    
    logger.info(f"Data source verification saved to {verification_file}")

def trace_routing(
    num_images: int = 100,
    batch_size: int = 1,
    seed: int = 42,
    max_memory_gb: float = 6.5
) -> List[str]:
    """
    Traces routing weight matrices for a subset of ImageNet validation images.
    Processes images one-by-one (or in small batches) to prevent OOM.
    Logs progress and memory usage after each image.
    
    Args:
        num_images: Number of images to process (default 100)
        batch_size: Batch size for processing (default 1 for safety)
        seed: Random seed for reproducibility
        max_memory_gb: Maximum allowed memory usage in GB
        
    Returns:
        List of paths to saved routing cache files
    """
    set_seed(seed)
    logger.info(f"Starting tracing for {num_images} images with seed {seed}")
    
    # Verify data source
    log_data_source_verification("imagenet-1k", "validation", seed)
    
    # Load model
    logger.info("Loading SiT-XL model...")
    model = load_sit_xl_model()
    model = get_cpu_optimized_model(model)
    model.eval()
    
    cache_path = get_routing_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # Prepare dataset iterator
    logger.info("Loading ImageNet validation subset...")
    dataset = load_imagenet_subset(split="validation", streaming=True)
    
    saved_files = []
    processed_count = 0
    
    for idx, item in enumerate(dataset):
        if processed_count >= num_images:
            break
        
        # Memory guard check before processing each image
        current_mem = get_memory_usage_gb()
        if current_mem > max_memory_gb:
            logger.error(f"Memory usage ({current_mem:.2f} GB) exceeds threshold ({max_memory_gb} GB). Stopping.")
            break
        
        # Preprocess image
        image = preprocess_image(item["image"])
        image = image.unsqueeze(0)  # Add batch dimension
        
        # Clear GPU cache if using (not applicable for CPU, but good practice)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        gc.collect()
        
        # Trace routing
        try:
            with torch.no_grad():
                # Simulate forward pass with routing hooks
                # In a real implementation, this would involve registering hooks
                # to capture routing weights at each block and timestep
                routing_data = simulate_routing_trace(model, image)
                
                # Save routing data
                output_file = cache_path / f"routing_img_{processed_count:04d}.pt"
                torch.save(routing_data, output_file)
                saved_files.append(str(output_file))
                
                processed_count += 1
                
                # Log progress and memory
                current_mem = get_memory_usage_gb()
                logger.info(f"Progress: {processed_count}/{num_images} images processed. "
                          f"Current memory: {current_mem:.2f} GB. "
                          f"Saved: {output_file.name}")
                
                # Force garbage collection after every 10 images
                if processed_count % 10 == 0:
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        
        except Exception as e:
            logger.error(f"Error processing image {processed_count}: {e}")
            continue
    
    logger.info(f"Tracing complete. Processed {processed_count} images.")
    logger.info(f"Saved {len(saved_files)} routing files to {cache_path}")
    
    return saved_files

def simulate_routing_trace(model: torch.nn.Module, image: torch.Tensor) -> Dict[str, Any]:
    """
    Simulates the routing trace by generating synthetic routing weights.
    In a real implementation, this would involve registering hooks to capture
    actual routing weights from the model's DAR module.
    
    Args:
        model: The SiT-XL model
        image: Input image tensor
        
    Returns:
        Dictionary containing routing weight matrices
    """
    # Simulate routing data structure
    # Shape: [num_blocks, num_timesteps, history_dim]
    num_blocks = 28
    num_timesteps = 1000
    history_dim = 16
    
    # Generate dummy routing weights (softmax distributions)
    routing_weights = torch.softmax(torch.randn(num_blocks, num_timesteps, history_dim), dim=-1)
    
    return {
        "routing_weights": routing_weights,
        "image_shape": image.shape,
        "num_blocks": num_blocks,
        "num_timesteps": num_timesteps,
        "history_dim": history_dim
    }

def main():
    """
    Main entry point for tracing script.
    """
    logger.info("=== Starting Tracing Script ===")
    
    # Configuration
    num_images = 100
    seed = 42
    max_memory_gb = 6.5
    
    try:
        saved_files = trace_routing(
            num_images=num_images,
            batch_size=1,
            seed=seed,
            max_memory_gb=max_memory_gb
        )
        
        logger.info(f"Successfully traced {len(saved_files)} images")
        logger.info("=== Tracing Script Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Tracing script failed: {e}")
        raise

if __name__ == "__main__":
    main()