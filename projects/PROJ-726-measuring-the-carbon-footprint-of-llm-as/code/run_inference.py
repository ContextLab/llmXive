import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from codecarbon import EmissionsTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_FILE = PROCESSED_DIR / "llm_inference_results.json"

MODEL_NAME = "gpt2-medium"
MAX_LENGTH = 128
BATCH_SIZE = 1  # CPU inference is slow, keep batch small

def load_dataset() -> List[Dict[str, Any]]:
    """
    Load the CodeXGLUE prompts from the downloaded dataset.
    Expects the dataset to be in data/raw/codexglue_python.json
    """
    input_file = RAW_DIR / "codexglue_python.json"
    if not input_file.exists():
        raise FileNotFoundError(
            f"Dataset file not found at {input_file}. "
            "Please run download_data.py first."
        )
    
    logger.info(f"Loading dataset from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we have a list of dicts with 'prompt_id' and 'prompt'
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'data' in data:
        return data['data']
    else:
        # Try to normalize if it's a dict of prompts
        return [
            {"prompt_id": k, "prompt": v} 
            for k, v in data.items()
        ]

def load_model() -> tuple:
    """
    Load GPT-2-medium on CPU.
    Returns (model, tokenizer)
    """
    logger.info(f"Loading model: {MODEL_NAME} on CPU")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()
    
    # Force CPU
    model = model.to("cpu")
    logger.info("Model loaded successfully")
    return model, tokenizer

def generate_code(
    model, 
    tokenizer, 
    prompt: str, 
    max_length: int = MAX_LENGTH
) -> str:
    """
    Generate code for a given prompt.
    Returns the generated code string.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to("cpu") for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False,  # Deterministic for reproducibility
            temperature=0.7,
            top_p=0.95
        )
    
    generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return generated_text

def count_loc(code_string: str) -> int:
    """
    Count non-empty lines in the generated code.
    """
    if not code_string or not code_string.strip():
        return 0
    lines = code_string.strip().split('\n')
    # Filter out purely whitespace lines
    return len([l for l in lines if l.strip()])

def run_inference_with_tracking(
    prompts: List[Dict[str, Any]], 
    model, 
    tokenizer,
    output_file: Path
) -> None:
    """
    Run inference on all prompts with CodeCarbon tracking.
    Excludes prompts that failed to generate or resulted in empty strings.
    """
    results = []
    skipped_count = 0
    failed_count = 0

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Start CodeCarbon tracker
    # We track the whole batch process
    tracker = EmissionsTracker(
        project_name="llm-carbon-footprint",
        output_dir=str(PROCESSED_DIR),
        measure_power_peaks=True
    )
    
    try:
        tracker.start()
        logger.info("Inference started with CodeCarbon tracking")

        for i, item in enumerate(prompts):
            prompt_id = item.get("prompt_id", f"unknown_{i}")
            prompt_text = item.get("prompt", "")

            if not prompt_text:
                logger.warning(f"Skipping prompt {prompt_id}: Empty prompt text")
                skipped_count += 1
                continue

            try:
                start_time = time.time()
                generated_code = generate_code(model, tokenizer, prompt_text)
                end_time = time.time()

                # Calculate LOC immediately
                loc_count = count_loc(generated_code)

                # Validation: Exclude prompts that failed to generate code or resulted in empty strings
                if not generated_code or not generated_code.strip():
                    logger.warning(
                        f"Excluding prompt {prompt_id}: Generated empty string"
                    )
                    failed_count += 1
                    continue

                if loc_count == 0:
                    logger.warning(
                        f"Excluding prompt {prompt_id}: Generated code has 0 LOC"
                    )
                    failed_count += 1
                    continue

                result = {
                    "prompt_id": prompt_id,
                    "model_used": MODEL_NAME,
                    "prompt_text": prompt_text,
                    "generated_code": generated_code,
                    "loc_count": loc_count,
                    "generation_time_seconds": end_time - start_time
                }
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(prompts)} prompts. "
                                f"Valid results: {len(results)}, Skipped: {skipped_count}, "
                                f"Failed/Excluded: {failed_count}")

            except Exception as e:
                logger.error(
                    f"Error processing prompt {prompt_id}: {str(e)}", 
                    exc_info=True
                )
                failed_count += 1
                continue

        # Stop tracker to get final metrics
        emissions = tracker.stop()
        logger.info(f"Inference completed. Total emissions: {emissions} kg CO2e")

    except Exception as e:
        logger.error(f"Critical error during inference tracking: {str(e)}", exc_info=True)
        if tracker._started:
            tracker.stop()
        raise

    # Save results
    save_results(results, output_file)
    logger.info(f"Saved {len(results)} valid results to {output_file}")
    logger.info(f"Summary: Total={len(prompts)}, Valid={len(results)}, "
                f"Skipped={skipped_count}, Failed/Excluded={failed_count}")

def save_results(results: List[Dict[str, Any]], output_file: Path) -> None:
    """
    Save results to a JSON file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    """
    Main entry point for the inference pipeline.
    """
    logger.info("Starting LLM Inference Pipeline")
    
    # Load data
    try:
        prompts = load_dataset()
        logger.info(f"Loaded {len(prompts)} prompts")
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        sys.exit(1)

    # Load model
    try:
        model, tokenizer = load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        sys.exit(1)

    # Run inference
    try:
        run_inference_with_tracking(prompts, model, tokenizer, OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Inference pipeline failed: {str(e)}")
        sys.exit(1)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
