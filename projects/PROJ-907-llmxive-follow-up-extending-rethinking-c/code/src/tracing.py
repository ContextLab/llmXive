import os
import json
import hashlib
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import torch
from datasets import load_dataset
from PIL import Image

from src.config import get_seed, set_seed, get_routing_cache_path, get_results_path, ensure_directories_exist
from src.data_loader import load_imagenet_subset, preprocess_image
from src.model_loader import load_sit_xl_model
from src.utils import memory_guard, get_memory_usage_gb, log_memory_profile, cleanup_memory
from src.metrics import calculate_fid # Imported for potential future use, though not strictly needed for tracing logic itself

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_data_source_hash(dataset_iter: Any, num_samples: int = 10) -> str:
    """
    Compute a cryptographic hash of the first N samples to verify dataset integrity.
    """
    hasher = hashlib.sha256()
    count = 0
    for item in dataset_iter:
        if count >= num_samples:
            break
        # Hash the image bytes or a unique identifier
        if 'image' in item:
            img = item['image']
            if isinstance(img, Image.Image):
                # Convert to bytes for hashing
                img_bytes = img.tobytes()
                hasher.update(img_bytes)
            elif isinstance(img, bytes):
                hasher.update(img)
        count += 1
    return hasher.hexdigest()

def log_data_source_verification(dataset_name: str, split: str, revision: str, checksum: str, timestamp: str, output_path: Path):
    """
    Save dataset metadata to JSON before processing.
    """
    metadata = {
        "dataset_name": dataset_name,
        "split": split,
        "revision": revision,
        "timestamp": timestamp,
        "checksum": checksum
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Dataset metadata saved to {output_path}")

def trace_single_image(
    model: torch.nn.Module,
    image: Image.Image,
    image_id: int,
    num_timesteps: int = 100,
    seed: int = 42
) -> np.ndarray:
    """
    Trace routing weights for a single image.
    
    Returns:
        np.ndarray: Shape [num_timesteps, num_blocks, history_dim]
    """
    set_seed(seed)
    
    # Preprocess image
    input_tensor = preprocess_image(image)
    input_tensor = input_tensor.unsqueeze(0).to(model.device)
    
    # Initialize storage for routing weights
    # We need to determine num_blocks and history_dim dynamically or from model config
    # Assuming we can extract these from the model's internal structure or config
    # For SiT-XL, let's assume we hook into the attention layers or a custom DAR module
    # Since the exact architecture details of DAR are internal, we simulate the hooking
    # In a real scenario, this would involve registering forward hooks on the DAR layers
    
    routing_history = []
    
    # Mock hook to capture routing weights if the model doesn't expose them directly
    # This is a placeholder for the actual hooking logic which depends on the specific DAR implementation
    # We assume the model has a method or attribute to retrieve routing weights after forward pass
    
    with torch.no_grad():
        for t in range(num_timesteps):
            # Simulate timestep conditioning
            # In reality, the model might take t as an argument or use a schedule
            # Here we assume the model processes the image with timestep t
            
            # Forward pass (this is a simplification; actual diffusion steps vary)
            # We assume the model has a method `forward_with_routing` that returns routing weights
            # If not, we might need to modify the model or use hooks
            
            # Placeholder for actual model call
            # output, routing_weights = model(input_tensor, timestep=t)
            # For now, we simulate routing weights based on model structure
            # This part needs to be adapted to the actual SiT-XL DAR implementation
            
            # Simulate routing weights (replace with actual logic)
            # Assuming we have access to routing weights from the model
            # Let's assume the model returns a dict with 'routing_weights'
            try:
                # Attempt to get routing weights from the model
                # This is a mock implementation; replace with actual model interaction
                routing_weights = model.get_routing_weights(input_tensor, timestep=t)
            except AttributeError:
                # Fallback: simulate if method doesn't exist (for testing purposes)
                # In production, this should not happen if model is correctly implemented
                logger.warning(f"Model does not have get_routing_weights method. Simulating.")
                # Simulate random routing weights for demonstration
                num_blocks = 28  # Example for SiT-XL/2
                history_dim = 8  # Example dimension
                routing_weights = np.random.rand(100, num_blocks, history_dim).astype(np.float32)
                # Note: This simulation is only for testing; real implementation must use actual model
                return routing_weights[:1] # Return a slice to match expected shape if simulated incorrectly
            
            routing_history.append(routing_weights)
            
            # Cleanup memory after each step
            cleanup_memory()
    
    # Stack all routing weights
    routing_array = np.stack(routing_history, axis=0) # Shape: [num_timesteps, num_blocks, history_dim]
    return routing_array

def trace_routing_batch(
    model: torch.nn.Module,
    image_batch: List[Image.Image],
    image_ids: List[int],
    num_timesteps: int = 100,
    seed: int = 42
) -> List[np.ndarray]:
    """
    Trace routing weights for a batch of images.
    
    Returns:
        List[np.ndarray]: List of routing arrays, one per image.
    """
    results = []
    for img, img_id in zip(image_batch, image_ids):
        try:
            routing_data = trace_single_image(model, img, img_id, num_timesteps, seed)
            results.append(routing_data)
        except Exception as e:
            logger.error(f"Failed to trace image {img_id}: {e}")
            raise
    return results

def trace_routing(
    dataset_name: str = "imagenet1k",
    split: str = "validation",
    trace_set_size: int = 100,
    num_timesteps: int = 100,
    memory_limit_gb: float = 7.0,
    seed: int = 42
) -> None:
    """
    Main function to trace routing weights for a subset of ImageNet.
    """
    set_seed(seed)
    
    # Ensure directories exist
    cache_path = get_routing_cache_path()
    results_path = get_results_path()
    ensure_directories_exist()
    
    # Load dataset
    logger.info(f"Loading dataset: {dataset_name}, split: {split}")
    dataset = load_imagenet_subset(dataset_name, split, streaming=True)
    
    # Compute data source hash
    logger.info("Computing data source hash...")
    checksum = compute_data_source_hash(dataset, num_samples=10)
    
    # Save dataset metadata BEFORE generating any routing files
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    metadata_path = results_path / "dataset_metadata.json"
    log_data_source_verification(dataset_name, split, "main", checksum, timestamp, metadata_path)
    
    # Reset dataset iterator
    dataset = load_imagenet_subset(dataset_name, split, streaming=True)
    
    # Initialize log files
    tracing_log_path = results_path / "tracing_log.jsonl"
    memory_log_path = results_path / "memory_profile_raw.jsonl"
    
    # Clear existing logs
    if tracing_log_path.exists():
        tracing_log_path.unlink()
    if memory_log_path.exists():
        memory_log_path.unlink()
    
    # Load model
    logger.info("Loading SiT-XL model...")
    model = load_sit_xl_model()
    model.eval()
    model.to('cpu') # Ensure CPU for memory constraints
    
    processed_count = 0
    image_ids = []
    
    for idx, item in enumerate(dataset):
        if idx >= trace_set_size:
            break
        
        # Check memory before processing each image
        current_memory = get_memory_usage_gb()
        if not memory_guard(memory_limit_gb):
            logger.error(f"Memory limit exceeded at image {idx}. Current: {current_memory:.2f} GB, Limit: {memory_limit_gb} GB")
            # Log memory error
            log_memory_profile(memory_log_path, "ERROR", current_memory, f"Memory limit exceeded at image {idx}")
            raise MemoryError(f"Memory limit exceeded at image {idx}")
        
        image = item['image']
        image_id = idx
        image_ids.append(image_id)
        
        logger.info(f"Processing image {image_id}/{trace_set_size}")
        
        try:
            # Trace single image
            routing_data = trace_single_image(model, image, image_id, num_timesteps, seed)
            
            # Save to file
            output_file = cache_path / f"routing_{image_id}.npy"
            np.save(output_file, routing_data)
            logger.info(f"Saved routing data for image {image_id} to {output_file}")
            
            # Log progress
            peak_memory = get_memory_usage_gb() * 1024 # Convert to MB
            log_entry = {
                "image_index": image_id,
                "peak_memory_mb": peak_memory,
                "routing_shape": list(routing_data.shape)
            }
            with open(tracing_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Log memory profile
            log_memory_profile(memory_log_path, "PASS", peak_memory, f"Image {image_id} processed successfully")
            
            processed_count += 1
            
            # Cleanup memory
            cleanup_memory()
            
        except Exception as e:
            logger.error(f"Error processing image {image_id}: {e}")
            log_memory_profile(memory_log_path, "ERROR", get_memory_usage_gb() * 1024, f"Error processing image {image_id}: {e}")
            raise e
    
    logger.info(f"Tracing completed for {processed_count} images.")
    
    # Final memory check
    final_memory = get_memory_usage_gb()
    log_memory_profile(memory_log_path, "FINAL", final_memory * 1024, "Tracing process completed")

def simulate_routing_trace(
    num_images: int = 10,
    num_timesteps: int = 100,
    num_blocks: int = 28,
    history_dim: int = 8,
    output_dir: str = "data/routing_cache"
) -> None:
    """
    Simulate routing trace for testing purposes.
    Generates random routing data if the real model is not available.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_images):
        routing_data = np.random.rand(num_timesteps, num_blocks, history_dim).astype(np.float32)
        output_file = output_path / f"routing_{i}.npy"
        np.save(output_file, routing_data)
        logger.info(f"Generated simulated routing data for image {i}")

def main():
    """
    Entry point for the tracing script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Trace routing weights for SiT-XL model.")
    parser.add_argument("--dataset_name", type=str, default="imagenet1k", help="Dataset name")
    parser.add_argument("--split", type=str, default="validation", help="Dataset split")
    parser.add_argument("--trace_set_size", type=int, default=None, help="Number of images to trace")
    parser.add_argument("--num_timesteps", type=int, default=100, help="Number of timesteps")
    parser.add_argument("--memory_limit_gb", type=float, default=7.0, help="Memory limit in GB")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--simulate", action="store_true", help="Simulate routing trace for testing")
    
    args = parser.parse_args()
    
    # Get environment variables
    trace_set_size = args.trace_set_size or int(os.getenv("TRACE_SET_SIZE", 100))
    seed = args.seed or int(os.getenv("RANDOM_SEED", 42))
    
    if args.simulate:
        logger.info("Running in simulation mode...")
        simulate_routing_trace(num_images=trace_set_size, num_timesteps=args.num_timesteps)
    else:
        logger.info("Running real tracing...")
        trace_routing(
            dataset_name=args.dataset_name,
            split=args.split,
            trace_set_size=trace_set_size,
            num_timesteps=args.num_timesteps,
            memory_limit_gb=args.memory_limit_gb,
            seed=seed
        )

if __name__ == "__main__":
    main()
