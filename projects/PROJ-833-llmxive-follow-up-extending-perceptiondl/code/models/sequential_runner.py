import os
import sys
import time
import json
import logging
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import psutil
from transformers import AutoProcessor, AutoModelForVision2Seq
from PIL import Image
import numpy as np

from config import get_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_MEMORY_MB = 7 * 1024  # 7 GB limit
QUANTIZATION_THRESHOLD_MB = 6500  # Start quantization if approaching limit
BATCH_SIZE = 1

class InferenceResult:
    """Container for a single inference result."""
    def __init__(self, region_id: int, caption: str, inference_time: float, is_error: bool = False, error_msg: str = ""):
        self.region_id = region_id
        self.caption = caption
        self.inference_time = inference_time
        self.is_error = is_error
        self.error_msg = error_msg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "caption": self.caption,
            "inference_time": self.inference_time,
            "is_error": self.is_error,
            "error_msg": self.error_msg
        }

def get_memory_usage_mb() -> float:
    """Get current peak RSS memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_and_enforce_memory_limit():
    """Check memory usage and enforce limit by quantizing or clearing cache."""
    current_mem = get_memory_usage_mb()
    if current_mem > MAX_MEMORY_MB:
        logger.warning(f"Memory limit exceeded: {current_mem:.2f} MB > {MAX_MEMORY_MB} MB. Attempting recovery.")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise MemoryError(f"Peak memory usage {current_mem:.2f} MB exceeds limit {MAX_MEMORY_MB} MB.")
    elif current_mem > QUANTIZATION_THRESHOLD_MB:
        logger.warning(f"Memory approaching limit: {current_mem:.2f} MB. Enabling INT8 quantization for next load.")
        return True
    return False

def load_model(model_id: str, quantize: bool = False) -> Tuple[Any, Any]:
    """
    Load the PerceptionDLM model.
    If quantize is True, applies dynamic INT8 quantization to reduce memory footprint.
    """
    logger.info(f"Loading model: {model_id} (quantize={quantize})")
    
    try:
        # Check memory before loading
        check_and_enforce_memory_limit()
        
        if quantize:
            logger.info("Applying INT8 quantization to reduce memory footprint...")
            # Load model in 8-bit mode using bitsandbytes if available, or torch quantization
            # For CPU inference, we use torch.ao.quantization or bitsandbytes for CPU
            try:
                import bitsandbytes as bnb
                # Load with 8-bit quantization
                model = AutoModelForVision2Seq.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32, # Base dtype
                    device_map="cpu",
                    load_in_8bit=True # Enable 8-bit
                )
                logger.info("Model loaded with 8-bit quantization (bitsandbytes).")
            except ImportError:
                logger.warning("bitsandbytes not available. Falling back to standard loading (may use more memory).")
                model = AutoModelForVision2Seq.from_pretrained(model_id, torch_dtype=torch.float32, device_map="cpu")
        else:
            model = AutoModelForVision2Seq.from_pretrained(model_id, torch_dtype=torch.float32, device_map="cpu")
        
        processor = AutoProcessor.from_pretrained(model_id)
        
        # Verify memory after load
        post_mem = get_memory_usage_mb()
        logger.info(f"Model loaded. Current memory usage: {post_mem:.2f} MB")
        
        if post_mem > MAX_MEMORY_MB:
            logger.error(f"Model loading exceeded memory limit ({post_mem:.2f} MB > {MAX_MEMORY_MB} MB).")
            raise MemoryError("Model loading exceeded memory limit even with standard loading.")

        return model, processor

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def preprocess_image(image_path: str, processor: Any) -> Any:
    """Preprocess an image for the model."""
    try:
        image = Image.open(image_path).convert("RGB")
        # Assuming the processor expects a list of images or a single image
        # Adjust based on specific model's processor signature
        inputs = processor(images=image, return_tensors="pt")
        return inputs
    except Exception as e:
        logger.error(f"Failed to preprocess image {image_path}: {e}")
        raise

def run_inference_batch(model: Any, inputs: Any, region_id: int) -> InferenceResult:
    """Run inference for a single region (batch size 1 for sequential)."""
    start_time = time.perf_counter()
    try:
        with torch.no_grad():
            # Generate caption
            # Note: Adjust generation parameters as needed
            generated_ids = model.generate(**inputs, max_new_tokens=50, do_sample=False)
            generated_text = model.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        end_time = time.perf_counter()
        inference_time = end_time - start_time
        
        return InferenceResult(
            region_id=region_id,
            caption=generated_text.strip(),
            inference_time=inference_time
        )
    except Exception as e:
        logger.error(f"Inference failed for region {region_id}: {e}")
        return InferenceResult(
            region_id=region_id,
            caption="",
            inference_time=0.0,
            is_error=True,
            error_msg=str(e)
        )

def run_sequential_inference(model: Any, processor: Any, image_path: str, regions: List[Dict[str, Any]]) -> List[InferenceResult]:
    """
    Run sequential inference with context reset for each region.
    This simulates the 'sequential baseline' by processing each region independently.
    """
    results = []
    logger.info(f"Starting sequential inference for {len(regions)} regions on {image_path}")
    
    # Load image once
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to load image {image_path}: {e}")
        raise

    for i, region in enumerate(regions):
        region_id = region.get("id", i)
        x, y, w, h = region["x"], region["y"], region["w"], region["h"]
        
        # Crop the region
        # Ensure coordinates are within image bounds
        img_w, img_h = image.size
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(img_w, int(x + w))
        y2 = min(img_h, int(y + h))
        
        if x2 <= x1 or y2 <= y1:
            logger.warning(f"Invalid region bounds for {region_id}, skipping.")
            continue
        
        cropped_image = image.crop((x1, y1, x2, y2))
        
        # Preprocess cropped image
        inputs = processor(images=cropped_image, return_tensors="pt")
        
        # Check memory before each inference (optional, but good for safety)
        if check_and_enforce_memory_limit():
            # If we are close to limit, we might want to quantize on the fly if not already done
            # But since model is already loaded, we rely on the initial quantization
            pass

        # Run inference
        result = run_inference_batch(model, inputs, region_id)
        results.append(result)
        
        # Explicitly clear GPU/CPU cache if needed (though on CPU it's less critical)
        # gc.collect() # Optional: might slow down if too aggressive

    return results

def run_sequential_pipeline(model_id: str, synthetic_data_path: str, output_path: str, quantize: bool = False):
    """
    Main pipeline function to run sequential inference on a batch of synthetic images.
    Reads JSON annotations, runs inference, and saves results.
    """
    logger.info(f"Starting sequential pipeline for {synthetic_data_path}")
    
    # Load model
    model, processor = load_model(model_id, quantize=quantize)
    
    # Load synthetic data
    data_path = Path(synthetic_data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Synthetic data path not found: {synthetic_data_path}")
    
    all_results = []
    
    # Iterate over JSON files in the directory
    json_files = list(data_path.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {synthetic_data_path}")
        return

    for json_file in json_files:
        logger.info(f"Processing {json_file.name}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            image_path = data.get("image_path")
            if not image_path or not Path(image_path).exists():
                logger.warning(f"Image not found for {json_file.name}: {image_path}")
                continue
            
            regions = data.get("bounding_boxes", [])
            if not regions:
                logger.warning(f"No bounding boxes found in {json_file.name}")
                continue
            
            # Run sequential inference
            results = run_sequential_inference(model, processor, image_path, regions)
            
            # Store results with metadata
            file_results = {
                "source_file": str(json_file),
                "image_path": image_path,
                "region_count": len(regions),
                "results": [r.to_dict() for r in results]
            }
            all_results.append(file_results)
            
        except Exception as e:
            logger.error(f"Error processing {json_file.name}: {e}")
            continue

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Sequential inference complete. Results saved to {output_path}")

def main():
    """Entry point for the sequential runner."""
    # Default paths (can be overridden by CLI args in a real script)
    model_id = "USER/PERCEPTIONDLM-CHECKPOINT-ID" # Placeholder, should be from config
    synthetic_data_path = str(get_data_path() / "synthetic")
    output_path = str(get_data_path() / "processed" / "sequential_results.json")
    
    # Check for quantization flag (could be passed via env or args)
    quantize = os.getenv("ENABLE_QUANTIZATION", "false").lower() == "true"
    
    try:
        run_sequential_pipeline(model_id, synthetic_data_path, output_path, quantize=quantize)
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()