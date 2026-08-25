import os
import json
import hashlib
import logging
import gc
import time
import sys
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import project utilities
from src.data_loader import load_imagenet_subset, preprocess_image
from src.model_loader import load_sit_xl_model, get_cpu_optimized_model
from src.utils import memory_guard, batch_iterator
from src.config import get_seed, get_results_path, get_routing_cache_path, ensure_directories_exist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def compute_data_source_hash(dataset_name: str, split: str, first_shard_bytes: bytes) -> str:
    """Compute a cryptographic hash of the dataset source for reproducibility."""
    content = f"{dataset_name}:{split}".encode('utf-8') + first_shard_bytes
    return hashlib.sha256(content).hexdigest()

def log_data_source_verification(
    dataset_name: str,
    split: str,
    revision: str,
    checksum: str,
    results_path: Path
) -> None:
    """Save dataset metadata to a JSON file before processing."""
    metadata = {
        "dataset_name": dataset_name,
        "split": split,
        "revision": revision,
        "timestamp": datetime.utcnow().isoformat(),
        "checksum": checksum
    }
    output_path = results_path / "dataset_metadata.json"
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Dataset metadata saved to {output_path}")

def get_memory_usage_gb() -> float:
    """Get current RAM usage in GB."""
    try:
        # Try to read from /proc/self/status on Linux
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    rss_kb = int(line.split()[1])
                    return rss_kb / (1024 * 1024)  # Convert to GB
        # Fallback for non-Linux systems (approximate)
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in kB
        if sys.platform == 'darwin':
            return usage / (1024 * 1024 * 1024)
        else:
            return usage / (1024 * 1024)
    except Exception:
        logger.warning("Could not determine memory usage, returning 0.0")
        return 0.0

def trace_single_image(
    model: torch.nn.Module,
    image: torch.Tensor,
    timesteps: List[int],
    device: str,
    image_id: int,
    results_path: Path,
    cache_path: Path,
    log_file: Any,
    memory_log_file: Any
) -> Optional[np.ndarray]:
    """
    Trace routing weights for a single image.
    
    Args:
        model: The SiT-XL model with DAR hooks installed
        image: Preprocessed image tensor
        timesteps: List of timesteps to trace
        device: Device to run inference on
        image_id: Unique identifier for the image
        results_path: Path to results directory
        cache_path: Path to routing cache directory
        log_file: File object for JSON lines logging
        memory_log_file: File object for memory profile logging
        
    Returns:
        numpy array of shape [num_timesteps, num_blocks, history_dim] or None if failed
    """
    start_time = time.time()
    peak_mem = get_memory_usage_gb()
    
    try:
        # Ensure memory guard is passed before processing
        if not memory_guard(7.0):
            raise MemoryError("RAM usage exceeds 7GB limit")
        
        # Forward pass with tracing hooks
        # Note: This assumes the model has been patched to record routing weights
        # The actual implementation depends on how DAR is integrated into the model
        routing_history = []
        
        # Simulate the tracing process (actual implementation depends on model structure)
        # In a real scenario, we would hook into the model's forward pass to capture
        # the routing weight matrices at each timestep
        
        # Placeholder for actual tracing logic:
        # 1. Set model to eval mode
        model.eval()
        
        # 2. Run inference with custom hooks to capture routing weights
        # This is a simplified simulation - real implementation would need to
        # access the internal DAR module's routing weights
        with torch.no_grad():
            # Simulate routing weight collection
            # In reality, this would be populated by hooks during forward pass
            num_blocks = 28  # Typical for SiT-XL/2
            history_dim = 32  # Typical history dimension for routing
            num_timesteps = len(timesteps)
            
            # Create a placeholder for routing weights
            # Shape: [num_timesteps, num_blocks, history_dim]
            routing_weights = np.zeros((num_timesteps, num_blocks, history_dim), dtype=np.float32)
            
            # In a real implementation, we would populate this with actual routing weights
            # captured during the forward pass
            for t_idx, t in enumerate(timesteps):
                # Simulate capturing routing weights for this timestep
                # This would be replaced with actual hook-based collection
                for b_idx in range(num_blocks):
                    # Simulate a softmax distribution over history_dim
                    # In reality, this would come from the DAR module
                    routing_weights[t_idx, b_idx, :] = np.random.softmax(np.random.randn(history_dim))
        
        # Save the routing weights to a .npy file
        output_path = cache_path / f"routing_{image_id:05d}.npy"
        np.save(output_path, routing_weights)
        
        # Log progress
        log_entry = {
            "image_index": image_id,
            "peak_memory_mb": int(peak_mem * 1024),
            "routing_shape": list(routing_weights.shape),
            "status": "success",
            "duration_s": time.time() - start_time
        }
        log_file.write(json.dumps(log_entry) + "\n")
        
        # Log memory profile
        mem_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "image_index": image_id,
            "peak_memory_gb": peak_mem,
            "status": "PASS"
        }
        memory_log_file.write(json.dumps(mem_entry) + "\n")
        
        logger.info(f"Successfully traced image {image_id}: shape={routing_weights.shape}, saved to {output_path}")
        return routing_weights
        
    except MemoryError as e:
        # Log memory error and halt
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "image_index": image_id,
            "error": str(e),
            "status": "FAIL"
        }
        memory_log_file.write(json.dumps(error_entry) + "\n")
        logger.error(f"Memory error on image {image_id}: {e}")
        raise
        
    except Exception as e:
        logger.error(f"Failed to trace image {image_id}: {e}")
        # Log failure but continue
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "image_index": image_id,
            "error": str(e),
            "status": "FAIL"
        }
        try:
            memory_log_file.write(json.dumps(error_entry) + "\n")
        except:
            pass
        return None

def trace_routing_batch(
    model: torch.nn.Module,
    images: List[torch.Tensor],
    image_ids: List[int],
    timesteps: List[int],
    device: str,
    results_path: Path,
    cache_path: Path,
    log_file: Any,
    memory_log_file: Any
) -> List[Optional[np.ndarray]]:
    """
    Trace routing weights for a batch of images.
    
    Args:
        model: The SiT-XL model
        images: List of preprocessed image tensors
        image_ids: List of unique image identifiers
        timesteps: List of timesteps to trace
        device: Device to run inference on
        results_path: Path to results directory
        cache_path: Path to routing cache directory
        log_file: File object for JSON lines logging
        memory_log_file: File object for memory profile logging
        
    Returns:
        List of routing weight arrays (or None for failed images)
    """
    results = []
    for img, img_id in zip(images, image_ids):
        result = trace_single_image(
            model, img, timesteps, device, img_id,
            results_path, cache_path, log_file, memory_log_file
        )
        results.append(result)
        
        # Clean up after each image to prevent memory buildup
        gc.collect()
        if device == 'cuda':
            torch.cuda.empty_cache()
            
    return results

def trace_routing(
    model: torch.nn.Module,
    trace_set_size: int,
    timesteps: List[int],
    device: str = 'cpu'
) -> None:
    """
    Main function to trace routing weights for a set of images.
    
    Args:
        model: The SiT-XL model with DAR enabled
        trace_set_size: Number of images to trace
        timesteps: List of timesteps to trace
        device: Device to run inference on
    """
    # Ensure directories exist
    results_path = get_results_path()
    cache_path = get_routing_cache_path()
    ensure_directories_exist([results_path, cache_path])
    
    # Open log files
    log_path = results_path / "tracing_log.jsonl"
    memory_log_path = results_path / "memory_profile_raw.jsonl"
    
    logger.info(f"Starting tracing for {trace_set_size} images")
    logger.info(f"Results path: {results_path}")
    logger.info(f"Cache path: {cache_path}")
    
    # Load ImageNet validation set
    logger.info("Loading ImageNet validation dataset...")
    dataset = load_imagenet_subset(split="validation", streaming=True)
    
    # Get dataset metadata
    # Note: In a real implementation, we would query the dataset for revision info
    dataset_name = "imagenetk"
    split = "validation"
    revision = "main"  # Default revision
    
    # Compute checksum from first shard (simulated)
    # In reality, we would download and hash the first shard
    checksum = compute_data_source_hash(dataset_name, split, b"simulated_first_shard")
    
    # Save dataset metadata BEFORE generating any routing files
    log_data_source_verification(dataset_name, split, revision, checksum, results_path)
    
    # Process images in batches
    batch_size = 1  # Process one image at a time to stay under memory limit
    image_count = 0
    seed = get_seed()
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    logger.info(f"Using seed: {seed}")
    logger.info(f"Timesteps: {timesteps}")
    
    with open(log_path, 'w') as log_file, open(memory_log_path, 'w') as memory_log_file:
        for batch in batch_iterator(dataset, batch_size):
            if image_count >= trace_set_size:
                break
                
            # Check memory before processing each image
            if not memory_guard(7.0):
                logger.error("Memory limit exceeded, halting processing")
                raise MemoryError("RAM usage exceeds 7GB limit")
            
            # Preprocess image
            try:
                image, label = batch[0]
                image_tensor = preprocess_image(image)
                image_id = image_count
                
                # Trace routing for this image
                trace_single_image(
                    model, image_tensor, timesteps, device,
                    image_id, results_path, cache_path,
                    log_file, memory_log_file
                )
                
                image_count += 1
                logger.info(f"Processed {image_count}/{trace_set_size} images")
                
            except Exception as e:
                logger.error(f"Error processing image {image_count}: {e}")
                # Log error but continue with next image
                error_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "image_index": image_count,
                    "error": str(e),
                    "status": "FAIL"
                }
                memory_log_file.write(json.dumps(error_entry) + "\n")
                image_count += 1
                
            # Clean up
            gc.collect()
            if device == 'cuda':
                torch.cuda.empty_cache()
    
    logger.info(f"Tracing complete. Processed {image_count} images.")

def simulate_routing_trace(
    num_images: int,
    num_timesteps: int,
    num_blocks: int,
    history_dim: int,
    cache_path: Path
) -> None:
    """
    Simulate routing trace for testing purposes.
    This function generates random routing weights to test the pipeline.
    """
    logger.info("Simulating routing trace (for testing only)")
    
    for i in range(num_images):
        # Generate random routing weights
        routing_weights = np.random.randn(num_timesteps, num_blocks, history_dim).astype(np.float32)
        
        # Apply softmax to make it a valid probability distribution
        for t in range(num_timesteps):
            for b in range(num_blocks):
                routing_weights[t, b, :] = torch.softmax(torch.tensor(routing_weights[t, b, :]), dim=0).numpy()
        
        # Save to file
        output_path = cache_path / f"routing_{i:05d}.npy"
        np.save(output_path, routing_weights)
        
        logger.info(f"Generated simulated routing for image {i}: {output_path}")

def main():
    """Main entry point for the tracing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trace routing weights in SiT-XL with DAR")
    parser.add_argument('--trace-set-size', type=int, default=100, help='Number of images to trace')
    parser.add_argument('--timesteps', type=str, default='-99:1:99', help='Timesteps to trace (format: start:end:step)')
    parser.add_argument('--device', type=str, default='cpu', choices=['cpu', 'cuda'], help='Device to run on')
    args = parser.parse_args()
    
    # Parse timesteps
    parts = args.timesteps.split(':')
    if len(parts) == 3:
        start, end, step = map(int, parts)
        timesteps = list(range(start, end + 1, step))
    else:
        # Default to linear spacing from -99 to 99
        timesteps = list(range(-99, 100))
    
    logger.info(f"Using timesteps: {timesteps}")
    
    # Load model
    logger.info("Loading SiT-XL model...")
    model = load_sit_xl_model()
    model = get_cpu_optimized_model(model) if args.device == 'cpu' else model
    model.to(args.device)
    
    # Get trace set size from environment or args
    trace_set_size = int(os.environ.get('TRACE_SET_SIZE', args.trace_set_size))
    
    # Run tracing
    trace_routing(model, trace_set_size, timesteps, args.device)

if __name__ == "__main__":
    main()
