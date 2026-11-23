import os
import sys
import argparse
from pathlib import Path
from utils.common import get_logger, ModelError, ensure_dir, read_yaml
from transformers import AutoModelForCausalLM, AutoConfig, AutoTokenizer

logger = get_logger(__name__)

def load_model(model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
    """
    Load the base TinyLlama model and tokenizer without mid-training.
    Uses CPU by default to align with project constraints.
    """
    logger.info(f"Loading base model: {model_name}")
    try:
        config = AutoConfig.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            config=config,
            torch_dtype="auto",
            device_map="cpu"  # Force CPU usage as per US2 constraints
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        logger.info(f"Model loaded successfully. Params: {model.num_parameters()}")
        return model, tokenizer, config
    except Exception as e:
        raise ModelError(f"Failed to load model {model_name}: {e}")

def save_model(model, tokenizer, config, output_dir: str):
    """
    Save the model, tokenizer, and config to the specified directory.
    Produces pytorch_model.bin and config.json as required.
    """
    output_path = Path(output_dir)
    ensure_dir(output_path)
    logger.info(f"Saving model artifacts to {output_path}")
    
    try:
        model.save_pretrained(output_path)
        tokenizer.save_pretrained(output_path)
        config.save_pretrained(output_path)
        logger.info("Model saved successfully.")
    except Exception as e:
        raise ModelError(f"Failed to save model to {output_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Baseline Model")
    parser.add_argument(
        "--model-name", 
        type=str, 
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        help="HuggingFace model identifier for the base model"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/artifacts/baseline_model",
        help="Directory to save the baseline model artifacts"
    )
    args = parser.parse_args()

    try:
        # Load the base model (no mid-training)
        model, tokenizer, config = load_model(args.model_name)
        
        # Save to the required location
        save_model(model, tokenizer, config, args.output_dir)
        
        logger.info(f"Baseline generation complete. Artifacts in {args.output_dir}")
        
        # Verify expected files exist
        expected_files = ["pytorch_model.bin", "config.json", "tokenizer.json"]
        output_path = Path(args.output_dir)
        missing = [f for f in expected_files if not (output_path / f).exists()]
        
        if missing:
            raise ModelError(f"Missing expected files after save: {missing}")
        
        logger.info("Verification passed: All expected files present.")

    except ModelError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during baseline generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
