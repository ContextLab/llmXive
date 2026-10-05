"""
Run LLM inference on CodeXGLUE prompts using GPT-2-medium on CPU.
Wraps execution with CodeCarbon EmissionsTracker to measure energy and CO2.
Implements robust error handling to skip failed prompts and continue processing.
"""
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
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MODEL_ID = "openai-community/gpt2-medium"
DEVICE = "cpu"
MAX_NEW_TOKENS = 128
DATASET_PATH = Path("data/raw/codexglue_sample.json")
OUTPUT_PATH = Path("data/processed/llm_inference_results.json")

def load_dataset(path: Path) -> List[Dict[str, Any]]:
    """Load the sampled CodeXGLUE dataset from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} prompts from {path}")
    return data

def load_model(model_id: str, device: str) -> tuple:
    """Load the specified model and tokenizer on the given device."""
    logger.info(f"Loading model {model_id} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    # Explicitly enforce float32 precision as per requirements
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    model.to(device)
    model.eval()
    logger.info("Model loaded successfully.")
    return model, tokenizer

def count_loc(code_string: str) -> int:
    """
    Count non-empty, non-comment lines in a code string.
    
    Args:
        code_string: The generated code as a string.
        
    Returns:
        Integer count of lines of code.
    """
    if not code_string or not code_string.strip():
        return 0
    
    lines = code_string.strip().split('\n')
    # Filter out empty lines and lines that are only whitespace
    non_empty_lines = [line for line in lines if line.strip()]
    return len(non_empty_lines)

def generate_code(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = MAX_NEW_TOKENS,
    device: str = DEVICE
) -> str:
    """Generate code completion for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    # Decode and strip the prompt from the output
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    generated_code = full_output[len(prompt):]
    return generated_code

def count_loc(code_string: str) -> int:
    """Count non-empty lines in the generated code."""
    if not code_string:
        return 0
    lines = code_string.split('\n')
    # Count lines that contain at least one non-whitespace character
    return sum(1 for line in lines if line.strip())

def run_inference_with_tracking(
    prompts: List[Dict[str, Any]],
    model,
    tokenizer,
    device: str = DEVICE
) -> List[Dict[str, Any]]:
    """
    Run inference loop with CodeCarbon tracking.
    Returns a list of result dictionaries.
    """
    results = []
    # Initialize tracker for CPU
    # Note: We wrap the whole process to capture the energy of the batch
    # However, to satisfy the requirement of "skip energy tracking for invalid code",
    # we must be careful. The prompt says: "MUST skip energy tracking for any code that fails the syntax validation".
    # Since CodeCarbon tracks global energy, we cannot easily "skip" energy for a specific item inside the loop
    # without stopping/starting the tracker.
    # Strategy: We run the tracker for the whole batch. We validate code *before* adding to results.
    # If a prompt fails validation, we still consume energy for that run, but we simply do not add
    # the invalid result to the final output list (or mark it as invalid).
    # The requirement "skip energy tracking" likely means "do not count the emission of this specific item towards the final report".
    # Given the physics of the tracker, we track the whole process but filter results.
    
    tracker = EmissionsTracker(
        project_name="llmXive-inference",
        output_dir="data/outputs",
        logging_level=20  # WARNING to reduce noise
    )
    
    try:
        tracker.start()
        
        for item in prompts:
            prompt_id = item.get("prompt_id")
            prompt_text = item.get("prompt", "")
            
            if not prompt_text:
                logger.warning(f"Skipping prompt {prompt_id}: empty prompt text")
                continue

            logger.info(f"Processing prompt {prompt_id}")
            
            # Generate code
            generated_code = generate_code(model, tokenizer, prompt_text, device=device)
            
            # Validate syntax BEFORE recording
            is_valid = True
            try:
                compile(generated_code, '<string>', 'exec')
            except SyntaxError:
                is_valid = False
                logger.warning(f"Syntax validation failed for prompt {prompt_id}. Skipping emission record.")
            
            # Only add to results if valid
            if is_valid:
                loc = count_loc(generated_code)
                result = {
                    "prompt_id": prompt_id,
                    "model_used": MODEL_ID,
                    "generated_code": generated_code,
                    "is_valid_code": True,
                    "loc_count": loc
                    # Energy and CO2 will be filled after tracker stops
                }
                results.append(result)
            else:
                # Do not add invalid code to results
                continue
        
        # Stop tracker to get final metrics
        tracker.stop()
        
        # Retrieve the final emissions (this is the total for the batch)
        # We need to distribute this or just record the total per run.
        # The task asks for a record per prompt. 
        # Standard practice in these pipelines when tracking a batch: 
        # Either track individually (slow) or attribute total to the batch.
        # Given the constraint "skip energy tracking for invalid code", 
        # and the fact that we tracked the whole batch, we will attribute 
        # the total batch energy to the valid prompts proportionally or just record the batch total 
        # in a metadata field? 
        # Re-reading T010: "MUST skip energy tracking for any code that fails...".
        # This implies the energy measurement should ideally be per-prompt to be fair.
        # Let's refactor to track per-prompt to strictly satisfy "skip energy tracking".
        
    except Exception as e:
        logger.error(f"Error during inference tracking: {e}")
        if 'tracker' in locals():
            try:
                tracker.stop()
            except:
                pass
        raise e

    # RE-IMPLEMENTATION OF LOOP FOR PER-PROMPT TRACKING TO SATISFY CONSTRAINT
    final_results = []
    # We need to re-run or structure differently. 
    # Since we already generated code in the loop above, we can't easily re-run without overhead.
    # However, to be strictly correct per "skip energy tracking", we must wrap each valid generation.
    # Let's implement the loop correctly from scratch below.
    pass

def run_inference_with_tracking_corrected(
    prompts: List[Dict[str, Any]],
    model,
    tokenizer,
    device: str = DEVICE
) -> List[Dict[str, Any]]:
    """
    Corrected loop: Tracks energy per prompt to allow skipping invalid ones.
    """
    results = []
    
    for item in prompts:
        prompt_id = item.get("prompt_id")
        prompt_text = item.get("prompt", "")
        
        if not prompt_text:
            logger.warning(f"Skipping prompt {prompt_id}: empty prompt text")
            continue

        logger.info(f"Processing prompt {prompt_id}")
        
        # Start tracker for this specific prompt
        tracker = EmissionsTracker(
            project_name="llmXive-inference",
            output_dir="data/outputs",
            logging_level=30  # ERROR only
        )
        
        try:
            tracker.start()
            
            # Generate code
            generated_code = generate_code(model, tokenizer, prompt_text, device=device)
            
            # Validate syntax
            is_valid = True
            try:
                compile(generated_code, '<string>', 'exec')
            except SyntaxError:
                is_valid = False
                logger.warning(f"Syntax validation failed for prompt {prompt_id}. Skipping emission record.")
            
            if is_valid:
                tracker.stop()
                
                # Get emissions
                emissions = tracker.final_emissions
                energy_kwh = emissions.get('energy', 0.0)
                co2_kg = emissions.get('carbon', 0.0)
                
                loc = count_loc(generated_code)
                
                result = {
                    "prompt_id": prompt_id,
                    "model_used": MODEL_ID,
                    "energy_kWh": float(energy_kwh),
                    "co2_kg": float(co2_kg),
                    "generated_code": generated_code,
                    "is_valid_code": True,
                    "loc_count": loc
                }
                results.append(result)
            else:
                # Stop tracker but do not record result
                try:
                    tracker.stop()
                except:
                    pass
                continue
                
        except Exception as e:
            logger.error(f"Error processing prompt {prompt_id}: {e}")
            try:
                tracker.stop()
            except:
                pass
            continue

    return results

def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point."""
    logger.info("Starting LLM Inference Pipeline...")
    
    if not DATASET_PATH.exists():
        logger.error(f"Dataset not found at {DATASET_PATH}. Run download_data.py first.")
        sys.exit(1)

    prompts = load_dataset(DATASET_PATH)
    model, tokenizer = load_model(MODEL_ID, DEVICE)
    
    results = run_inference_with_tracking_corrected(prompts, model, tokenizer, DEVICE)
    
    if not results:
        logger.warning("No valid results generated.")
    else:
        save_results(results, OUTPUT_PATH)
        
    logger.info("Pipeline completed.")

if __name__ == "__main__":
    main()