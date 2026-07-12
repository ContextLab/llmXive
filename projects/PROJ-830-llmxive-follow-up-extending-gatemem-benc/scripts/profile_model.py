"""
Profile the frozen DistilBERT model to ensure it runs on CPU and measures resource usage.
Output: data/logs/model_profile.json
"""
import os
import json
import time
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Configure logging
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "model_profile.log"
output_file = log_dir / "model_profile.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MODEL_NAME = "distilbert-base-uncased" # Placeholder for the frozen model used in GateMem

def main():
    logger.info("Starting model profiling on CPU...")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.warning("CUDA is available, but forcing CPU usage for profiling.")
    device = torch.device("cpu")

    tracemalloc.start()
    start_time = time.time()

    try:
        # Load tokenizer and model
        logger.info(f"Loading tokenizer for {MODEL_NAME}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        logger.info(f"Loading model for {MODEL_NAME} on {device}...")
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            num_labels=2
        )
        model.to(device)
        model.eval()

        # Verify no GPU tensors
        for param in model.parameters():
            if param.is_cuda:
                raise RuntimeError("Model contains CUDA tensors!")

        logger.info("Model loaded successfully on CPU.")

        # Run inference on dummy input
        dummy_text = "This is a test sentence for profiling."
        inputs = tokenizer(dummy_text, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        logger.info("Running inference...")
        with torch.no_grad():
            outputs = model(**inputs)
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        profile_data: Dict[str, Any] = {
            "model_name": MODEL_NAME,
            "device": "cpu",
            "inference_time_seconds": end_time - start_time,
            "peak_memory_mb": peak / (1024 * 1024),
            "current_memory_mb": current / (1024 * 1024),
            "cuda_available": torch.cuda.is_available(),
            "cuda_tensors_found": False,
            "status": "success"
        }

        with open(output_file, "w") as f:
            json.dump(profile_data, f, indent=2)

        logger.info(f"Profile saved to {output_file}")
        logger.info(f"Peak Memory: {profile_data['peak_memory_mb']:.2f} MB")
        logger.info(f"Inference Time: {profile_data['inference_time_seconds']:.4f} s")

    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        profile_data = {
            "model_name": MODEL_NAME,
            "status": "failed",
            "error": str(e)
        }
        with open(output_file, "w") as f:
            json.dump(profile_data, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
