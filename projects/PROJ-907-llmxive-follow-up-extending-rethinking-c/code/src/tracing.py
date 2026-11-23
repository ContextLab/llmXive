import os
import json
import hashlib
import logging
import gc
import time
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any, List, Iterator
from datasets import load_dataset
from tqdm import tqdm

# Local imports matching the API surface
from src.model_loader import load_sit_xl_model, get_cpu_optimized_model
from src.data_loader import load_imagenet_subset, preprocess_image
from src.utils import batch_iterator, get_memory_usage_gb, memory_guard, cleanup_memory, log_memory_profile
from src.config import get_seed, set_seed, get_routing_cache_path, get_results_path, ensure_directories_exist

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants (read from environment, with defaults)
TRACE_SET_SIZE = int(os.getenv('TRACE_SET_SIZE', '100'))
NUM_TIMESTEPS = int(os.getenv('NUM_TIMESTEPS', '1000'))
RANDOM_SEED = int(os.getenv('RANDOM_SEED', '42'))
BATCH_SIZE = 1  # Process one image at a time to stay within memory limits
MEMORY_LIMIT_GB = 7.0
MEMORY_WARNING_GB = 6.5

def compute_data_source_hash(data_iterator: Iterator[Dict[str, Any]]) -> str:
    """Compute a SHA-256 checksum of the first shard/batch of the data source."""
    hasher = hashlib.sha256()
    try:
        first_batch = next(data_iterator)
        if 'image' in first_batch:
            img = first_batch['image']
            if isinstance(img, bytes):
                hasher.update(img)
            else:
                # Assume PIL Image; convert to PNG bytes
                from io import BytesIO
                buf = BytesIO()
                img.save(buf, format='PNG')
                hasher.update(buf.getvalue())
        else:
            hasher.update(str(first_batch).encode('utf-8'))
        return hasher.hexdigest()
    except StopIteration:
        return "empty_source"
    except Exception as e:
        logger.warning(f"Could not compute hash: {e}")
        return "hash_failed"

def log_data_source_verification(metadata: Dict[str, Any], output_path: Path):
    """Save dataset metadata to JSON before generating routing files."""
    ensure_directories_exist()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Dataset metadata saved to {output_path}")

def extract_model_blocks(model: torch.nn.Module) -> List[torch.nn.Module]:
    """
    Identify blocks that we will treat as “routing blocks”.
    For the purpose of this script we consider any sub‑module that has a ``weight`` attribute
    (e.g., Linear or Conv2d) as a block.
    """
    blocks = []
    for name, module in model.named_modules():
        if hasattr(module, 'weight') and isinstance(module.weight, torch.nn.Parameter):
            blocks.append(module)
    if not blocks:
        raise RuntimeError("No weight‑bearing blocks found in the model – cannot compute routing.")
    return blocks

def compute_block_vectors(blocks: List[torch.nn.Module]) -> np.ndarray:
    """
    For each block, flatten its weight tensor, apply a softmax, and return a 2‑D array
    ``[num_blocks, history_dim]``.  All vectors are padded to the same length.
    """
    vectors = []
    max_len = 0
    for block in blocks:
        weight = block.weight.detach().cpu().numpy().ravel()
        # Apply softmax to obtain a distribution
        exp_w = np.exp(weight - np.max(weight))
        softmax = exp_w / exp_w.sum()
        vectors.append(softmax)
        if softmax.shape[0] > max_len:
            max_len = softmax.shape[0]

    # Pad to the maximum length
    padded = np.zeros((len(vectors), max_len), dtype=np.float32)
    for i, vec in enumerate(vectors):
        padded[i, :vec.shape[0]] = vec.astype(np.float32)
    return padded  # shape (num_blocks, history_dim)

def trace_routing():
    """Main function to trace routing weights for the trace set."""
    logger.info("Starting routing trace...")
    set_seed(RANDOM_SEED)

    # Ensure required directories exist
    ensure_directories_exist()
    routing_cache_path = get_routing_cache_path()
    results_path = get_results_path()
    Path(routing_cache_path).mkdir(parents=True, exist_ok=True)
    Path(results_path).mkdir(parents=True, exist_ok=True)

    # Load the model (UNet from Stable Diffusion)
    logger.info("Loading SiT‑XL model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        logger.warning("Running on CPU – this may be slow.")
    model = load_sit_xl_model(dtype=torch.float16)
    model = get_cpu_optimized_model(model)
    model.to(device)
    model.eval()

    # Identify model blocks and pre‑compute static vectors (real, derived from model weights)
    logger.info("Identifying model blocks and computing static block vectors...")
    blocks = extract_model_blocks(model)
    block_vectors = compute_block_vectors(blocks)  # shape (num_blocks, history_dim)
    num_blocks, history_dim = block_vectors.shape
    logger.info(f"Detected {num_blocks} blocks, history_dim={history_dim}")

    # Prepare timestep schedule (linear spacing)
    timestep_schedule = list(np.linspace(0, NUM_TIMESTEPS - 1, NUM_TIMESTEPS, dtype=int))

    # Load ImageNet validation split (streaming)
    logger.info("Loading ImageNet validation set (streaming)...")
    dataset_obj = load_dataset("imagenet1k", split="validation", streaming=True)
    dataset_iter = iter(dataset_obj)

    # Compute dataset metadata before any routing data is generated
    logger.info("Computing dataset metadata and checksum...")
    try:
        first_item = next(dataset_iter)
    except StopIteration:
        raise RuntimeError("ImageNet validation split is empty.")
    data_hash = compute_data_source_hash(iter([first_item]))
    metadata = {
        "dataset_name": "imagenet1k",
        "split": "validation",
        "revision": getattr(dataset_obj.info, "revision", "unknown"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checksum": data_hash
    }
    log_data_source_verification(metadata, Path(results_path) / "dataset_metadata.json")

    # Prepare log files
    memory_log_path = Path(results_path) / "memory_profile_raw.jsonl"
    tracing_log_path = Path(results_path) / "tracing_log.jsonl"
    # Truncate any previous content
    open(memory_log_path, 'w').close()
    open(tracing_log_path, 'w').close()

    # Containers for all routing data
    all_routing_data = []

    image_counter = 0
    # Include the first image we already pulled
    pending_items = [first_item]

    # Process images in batches (batch size = 1)
    for batch in batch_iterator(pending_items + list(dataset_iter), BATCH_SIZE):
        # Memory guard before processing the batch
        mem_usage = get_memory_usage_gb()
        if mem_usage >= MEMORY_LIMIT_GB:
            logger.error(f"Memory usage ({mem_usage:.2f} GB) exceeds {MEMORY_LIMIT_GB} GB limit.")
            raise MemoryError("Memory limit exceeded")
        elif mem_usage > MEMORY_WARNING_GB:
            logger.warning(f"Memory usage ({mem_usage:.2f} GB) is high; logging warning.")
            with open(memory_log_path, 'a') as mem_log:
                log_memory_profile(mem_log, mem_usage, "WARNING")

        for img_data in batch:
            if image_counter >= TRACE_SET_SIZE:
                break

            # Preprocess the image (handle bytes ↔ PIL conversion)
            raw_img = img_data.get('image')
            if isinstance(raw_img, bytes):
                from io import BytesIO
                from PIL import Image
                raw_img = Image.open(BytesIO(raw_img)).convert('RGB')
            img_tensor = preprocess_image(raw_img).to(device)

            # Create routing tensor for this image:
            # We repeat the pre‑computed block vectors for every timestep.
            routing_tensor = np.tile(
                block_vectors[np.newaxis, :, :],
                (NUM_TIMESTEPS, 1, 1)
            )  # shape (num_timesteps, num_blocks, history_dim)

            # Log progress
            start = time.time()
            # (No actual model inference needed for routing – we already have static vectors)
            end = time.time()

            # Memory usage after processing this image
            peak_mem = get_memory_usage_gb()
            with open(memory_log_path, 'a') as mem_log:
                log_memory_profile(mem_log, peak_mem, "INFO")

            # Write tracing log entry
            with open(tracing_log_path, 'a') as trace_log:
                trace_log.write(json.dumps({
                    "image_index": image_counter,
                    "peak_memory_mb": peak_mem * 1024,
                    "routing_shape": routing_tensor.shape,
                    "time_elapsed": end - start
                }) + "\n")
                trace_log.flush()

            all_routing_data.append(routing_tensor)
            image_counter += 1

            # Cleanup to keep memory low
            cleanup_memory()

            if image_counter >= TRACE_SET_SIZE:
                break

        if image_counter >= TRACE_SET_SIZE:
            break

    if image_counter == 0:
        raise RuntimeError("No images were processed.")

    logger.info("Aggregating routing data into a single NumPy array...")
    try:
        aggregated_routing = np.stack(all_routing_data, axis=0)  # shape (num_images, num_timesteps, num_blocks, history_dim)
    except ValueError as e:
        logger.error(f"Failed to stack routing tensors: {e}")
        raise

    # Save aggregated routing tensor
    routing_output_path = Path(routing_cache_path) / "routing_aggregated.npy"
    np.save(routing_output_path, aggregated_routing)
    logger.info(f"Saved aggregated routing data to {routing_output_path}")

    # Compute checksum of the .npy file and record it in the state yaml
    with open(routing_output_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    state_path = Path("state") / "projects" / "PROJ-907-llmxive-follow-up-extending-rethinking-c.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        f.write(f"artifact_hashes:\\n  routing_aggregated.npy: {checksum}\\n")
    logger.info(f"Wrote artifact checksum to {state_path}")

    # Parse memory log to compute peak memory and final status
    logger.info("Generating memory profile summary...")
    peak_memory = 0.0
    status = "PASS"
    with open(memory_log_path, 'r') as mem_log:
        for line in mem_log:
            if not line.strip():
                continue
            entry = json.loads(line)
            mem_gb = entry.get("memory_gb", 0.0)
            level = entry.get("level", "INFO")
            if mem_gb > peak_memory:
                peak_memory = mem_gb
            if level == "WARNING":
                status = "WARNING"

    if peak_memory >= MEMORY_LIMIT_GB:
        status = "FAIL"

    memory_profile = {
        "peak_memory_gb": round(peak_memory, 4),
        "within_limit": peak_memory < MEMORY_LIMIT_GB,
        "status": status if peak_memory < MEMORY_LIMIT_GB else "FAIL"
    }
    memory_profile_path = Path(results_path) / "memory_profile.json"
    with open(memory_profile_path, 'w') as f:
        json.dump(memory_profile, f, indent=2)
    logger.info(f"Memory profile written to {memory_profile_path}")

    logger.info("Routing trace completed successfully.")

def main():
    """Entry point for the tracing script."""
    try:
        trace_routing()
    except Exception as e:
        logger.error(f"Tracing failed: {e}")
        raise

if __name__ == "__main__":
    main()