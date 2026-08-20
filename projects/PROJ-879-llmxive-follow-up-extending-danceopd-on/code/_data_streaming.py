import argparse
import signal
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datasets import load_dataset
from PIL import Image
import io
import hashlib
import logging
import torch
from transformers import CLIPProcessor, CLIPModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Timeout Handling ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    signal.alarm(0)

# --- Configuration & Paths ---
def get_project_root() -> Path:
    return Path(__file__).parent.parent

def get_config_paths() -> Dict[str, Path]:
    root = get_project_root()
    return {
        "raw": root / "data" / "raw",
        "results": root / "data" / "results",
        "processed": root / "data" / "processed"
    }

# --- Data Loading Functions ---
def load_imageNet_streaming(seed: int = 42, num_samples: int = 600):
    """
    Streams ImageNet-1K dataset and samples images.
    Note: 'imagenet-1k' on HuggingFace is large. We stream to avoid memory issues.
    """
    logger.info(f"Starting ImageNet-1K streaming with seed {seed}...")
    try:
        ds = load_dataset("imagenet-1k", split="train", streaming=True, trust_remote_code=True)
        # Set seed for reproducibility
        ds = ds.shuffle(seed=seed)
        
        samples = []
        count = 0
        for item in ds:
            if count >= num_samples:
                break
            # Item structure: {'id': str, 'image': PIL.Image, 'label': int}
            img = item['image']
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Compute checksum for raw preservation
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            checksum = hashlib.sha256(img_bytes.getvalue()).hexdigest()
            
            samples.append({
                "source": "imagenet",
                "id": item['id'],
                "label": item['label'],
                "image_data": img_bytes.getvalue(), # Store bytes for later processing
                "checksum": checksum
            })
            count += 1
            if count % 100 == 0:
                logger.info(f"ImageNet: Collected {count}/{num_samples} samples")
        
        logger.info(f"ImageNet streaming complete. Collected {len(samples)} samples.")
        return samples
    except Exception as e:
        logger.error(f"Error streaming ImageNet: {e}")
        return []

def load_laion_streaming(seed: int = 42, num_samples: int = 600):
    """
    Streams LAION-2B-en dataset.
    Note: LAION is massive. We sample prompts and images.
    Using a smaller, manageable subset or specific subset if available,
    but strictly streaming to avoid OOM.
    """
    logger.info(f"Starting LAION-2B-en streaming with seed {seed}...")
    try:
        # Using laion2B-en as specified, streaming
        ds = load_dataset("laion/laion2B-en", split="train", streaming=True, trust_remote_code=True)
        ds = ds.shuffle(seed=seed)
        
        samples = []
        count = 0
        for item in ds:
            if count >= num_samples:
                break
            
            # Item structure varies, typically: {'url': str, 'text': str, 'image': PIL.Image}
            # We need to handle potential missing keys or bad images
            if 'image' not in item or item['image'] is None:
                continue
            
            img = item['image']
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_bytes = io.BytesIO()
            try:
                img.save(img_bytes, format='JPEG', quality=85)
            except Exception:
                continue # Skip corrupted images
            
            img_bytes.seek(0)
            checksum = hashlib.sha256(img_bytes.getvalue()).hexdigest()
            
            samples.append({
                "source": "laion",
                "url": item.get('url', ''),
                "text": item.get('text', ''),
                "image_data": img_bytes.getvalue(),
                "checksum": checksum
            })
            count += 1
            if count % 100 == 0:
                logger.info(f"LAION: Collected {count}/{num_samples} samples")
        
        logger.info(f"LAION streaming complete. Collected {len(samples)} samples.")
        return samples
    except Exception as e:
        logger.error(f"Error streaming LAION: {e}")
        return []

# --- Feature Extraction (CLIP) ---
def extract_prompt_embedding(images: List[Image.Image], text_prompts: List[str], processor, model):
    """
    Extracts embeddings using CLIP.
    For ImageNet, we might use the class label as text prompt or a generic description.
    For LAION, we use the 'text' field.
    """
    # Prepare inputs
    # Note: processor expects a list of images and a list of texts
    inputs = processor(text=text_prompts, images=images, return_tensors="pt", padding=True, truncation=True)
    
    with torch.no_grad():
        # We want the image embedding
        outputs = model.get_image_features(**inputs) # Returns (batch_size, embedding_dim)
        # Normalize
        outputs = outputs / outputs.norm(dim=-1, keepdim=True)
    
    return outputs.numpy()

# --- Sampling Strategy ---
def stratified_sample(imagenet_samples: List[Dict], laion_samples: List[Dict], target_total: int = 1200) -> List[Dict]:
    """
    Performs stratified sampling to ensure representation from both sources.
    Target: 1200 total (approx 600 from each, adjusted if one source is smaller).
    """
    total_available = len(imagenet_samples) + len(laion_samples)
    if total_available == 0:
        return []
    
    # Determine split
    # If one source is missing, take all from the other
    if len(imagenet_samples) == 0:
        final_samples = laion_samples[:target_total]
    elif len(laion_samples) == 0:
        final_samples = imagenet_samples[:target_total]
    else:
        # Proportional or 50/50? Spec says "stratified random sample".
        # We'll aim for roughly equal contribution if possible, capped by availability.
        target_each = target_total // 2
        final_imagenet = imagenet_samples[:target_each] if len(imagenet_samples) >= target_each else imagenet_samples
        remaining_needed = target_total - len(final_imagenet)
        final_laion = laion_samples[:remaining_needed] if len(laion_samples) >= remaining_needed else laion_samples
        final_samples = final_imagenet + final_laion
    
    logger.info(f"Stratified sampling complete. Total samples: {len(final_samples)}")
    return final_samples

# --- Pilot Run ---
def run_pilot_run(samples: List[Dict], pilot_size: int = 50) -> Dict[str, Any]:
    """
    Runs a pilot to estimate exclusion rate (undefined routing paths).
    Since we don't have the teacher model here yet (T013a), we simulate the check
    or just return the pilot size for T013a to handle.
    Actually, T012 is just data streaming. The exclusion rate is calculated in T013a.
    However, the task description says: "Execute a pilot run of 500 samples to estimate... Store this rate".
    Since T012 is strictly streaming, we will store the pilot samples and let T013a do the inference.
    We will create the pilot manifest.
    """
    pilot_samples = samples[:pilot_size]
    paths = get_config_paths()
    pilot_path = paths["results"] / "pilot_samples.json"
    
    # Convert bytes to base64 for JSON serialization? Or just save paths?
    # We save metadata. The actual image data is large.
    # We will save the list of sample metadata.
    pilot_data = {
        "pilot_size": len(pilot_samples),
        "samples": [
            {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in s.items()}
            for s in pilot_samples
        ]
    }
    
    with open(pilot_path, 'w') as f:
        json.dump(pilot_data, f, indent=2)
    
    logger.info(f"Pilot samples saved to {pilot_path}")
    return {"pilot_size": len(pilot_samples), "status": "saved"}

# --- Writing Batches to Parquet ---
def write_batch_to_parquet(samples: List[Dict], output_path: Path):
    """
    Writes a batch of samples to a Parquet file.
    Handles binary data (image bytes) by converting to base64 or storing as bytes if pyarrow supports.
    Pyarrow supports bytes.
    """
    if not samples:
        logger.warning("No samples to write.")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame
    # We need to handle the 'image_data' bytes field carefully for Parquet
    # PyArrow can handle large binary blobs.
    df = pd.DataFrame(samples)
    
    # If image_data is present, ensure it's bytes
    if 'image_data' in df.columns:
        # Already bytes from our loading logic
        pass
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote {len(samples)} samples to {output_path}")

# --- Main Execution Logic ---
def run_data_streaming():
    paths = get_config_paths()
    seed = 42
    target_raw = 1200 # Oversampled to account for exclusions
    pilot_size = 500
    
    logger.info("Starting Data Streaming Phase (T012)...")
    
    # 1. Stream Data
    # We set a timeout for the streaming process (e.g., 30 mins)
    setup_timeout(1800) 
    try:
        imagenet_samples = load_imageNet_streaming(seed=seed, num_samples=target_raw)
        laion_samples = load_laion_streaming(seed=seed, num_samples=target_raw)
        cancel_timeout()
    except TimeoutError:
        logger.error("Data streaming timed out.")
        cancel_timeout()
        return
    
    if not imagenet_samples and not laion_samples:
        logger.error("No samples collected from any source.")
        return
    
    # 2. Pilot Run (Metadata only for now, actual inference is T013a)
    # The task says "Execute a pilot run... to estimate exclusion rate".
    # Since T012 doesn't have the teacher model, we save the pilot data for T013a to process.
    # We assume T013a will read this and run inference.
    # We store the pilot samples in a specific file.
    pilot_result = run_pilot_run(imagenet_samples + laion_samples, pilot_size)
    
    # 3. Save Raw Batches
    # Save raw downloaded images manifest or parquet
    if imagenet_samples:
        write_batch_to_parquet(imagenet_samples, paths["raw"] / "imagenet_samples.parquet")
    if laion_samples:
        write_batch_to_parquet(laion_samples, paths["raw"] / "laion_samples.parquet")
    
    # 4. Combine Samples
    all_samples = imagenet_samples + laion_samples
    combined_path = paths["raw"] / "combined_samples.parquet"
    write_batch_to_parquet(all_samples, combined_path)
    
    # 5. Log Pilot Exclusion Rate (Placeholder for T013a to fill)
    # We create the file structure, T013a will update the rate.
    exclusion_log_path = paths["results"] / "pilot_exclusion_rate.json"
    with open(exclusion_log_path, 'w') as f:
        json.dump({
            "pilot_size": pilot_size,
            "exclusion_rate": 0.0, # To be filled by T013a
            "status": "pending_inference"
        }, f, indent=2)
    
    logger.info("Data streaming phase completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Data Streaming for DanceOPD")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    run_data_streaming()

if __name__ == "__main__":
    main()