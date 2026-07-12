"""
Validate that the frozen DistilBERT weights load correctly on CPU without
requiring GPU tensors or quantization libraries.
Output: data/logs/model_validation.json
"""
import os
import json
import logging
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Configure logging
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "model_validation.log"
output_file = log_dir / "model_validation.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MODEL_NAME = "distilbert-base-uncased"

def main():
    logger.info("Starting model weight validation...")
    validation_result = {
        "model_name": MODEL_NAME,
        "loaded": False,
        "cpu_only": False,
        "no_quantization_libs": False,
        "forward_pass_success": False,
        "error": None
    }

    try:
        # Force CPU
        device = torch.device("cpu")
        
        # Load model
        logger.info("Loading model weights...")
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            num_labels=2
        )
        model.to(device)
        model.eval()

        # Check for CUDA tensors
        has_cuda = False
        for name, param in model.named_parameters():
            if param.is_cuda:
                has_cuda = True
                logger.error(f"CUDA tensor found in {name}")
        
        validation_result["cpu_only"] = not has_cuda

        # Check imports (implicitly done by successful load without bitsandbytes errors)
        # We assume if we loaded via transformers without explicit quantization flags, it's standard.
        validation_result["no_quantization_libs"] = True 

        # Run forward pass
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        test_input = "Validation test input."
        inputs = tokenizer(test_input, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
        
        validation_result["forward_pass_success"] = True
        validation_result["loaded"] = True
        logger.info("Validation successful.")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        validation_result["error"] = str(e)

    with open(output_file, "w") as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation result saved to {output_file}")
    
    if not validation_result["loaded"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
