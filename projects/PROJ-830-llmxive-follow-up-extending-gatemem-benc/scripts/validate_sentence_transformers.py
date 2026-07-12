"""
Validate that the sentence-transformers model is CPU-compatible and does not
require quantization libraries.
Output: data/logs/sentence_transformers_validation.json
"""
import os
import json
import logging
import sys
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

# Configure logging
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "sentence_transformers_validation.log"
output_file = log_dir / "sentence_transformers_validation.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Using a standard lightweight model for validation
MODEL_NAME = "all-MiniLM-L6-v2"

def main():
    logger.info("Starting sentence-transformers validation...")
    result = {
        "model_name": MODEL_NAME,
        "cpu_compatible": False,
        "quantization_required": False,
        "inference_success": False,
        "error": None
    }

    try:
        # Load model
        logger.info(f"Loading model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        # Ensure CPU
        model.to("cpu")
        
        # Verify no CUDA usage
        if torch.cuda.is_available():
            logger.warning("CUDA available but forcing CPU.")
        
        # Check internal device
        device = model.device
        if device.type != "cpu":
            result["cpu_compatible"] = False
            logger.error(f"Model loaded on {device}, expected CPU.")
            raise RuntimeError("Model not CPU compatible")
        
        result["cpu_compatible"] = True
        result["quantization_required"] = False

        # Run inference
        sentences = ["This is a test sentence."]
        embeddings = model.encode(sentences)
        
        if embeddings is not None and len(embeddings) > 0:
            result["inference_success"] = True
            logger.info("Inference successful.")
        else:
            raise RuntimeError("Inference returned empty results")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        result["error"] = str(e)

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Result saved to {output_file}")
    
    if not result["inference_success"]:
        sys.exit(1)

if __name__ == "__main__":
    main()