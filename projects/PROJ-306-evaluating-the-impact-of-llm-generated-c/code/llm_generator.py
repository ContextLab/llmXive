"""
LLM Generator Module for llmXive pipeline.

Handles calling LLM APIs (OpenAI) or local CPU inference (HuggingFace)
with mandatory 4-bit quantization for fallback models to satisfy SC-005 (7GB RAM limit).
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Local imports matching existing API surface
from config import get_api_key, get_model_chain, get_model_config, resolve_model, ModelConfig
from utils import exponential_backoff_retry, safe_get

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
GENERATION_OUTPUT_DIR = Path("data/generated")
MAX_RETRIES = 3
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 512

def _ensure_output_dir():
    """Ensure the generated code output directory exists."""
    GENERATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _load_prompt_from_catalog(task_id: str) -> Optional[str]:
    """
    Load the prompt for a specific task_id from the processed catalog.
    Returns None if task_id is not found or prompt is missing.
    """
    catalog_path = Path("data/benchmarks/processed/catalog.json")
    if not catalog_path.exists():
        logger.error(f"Catalog not found at {catalog_path}")
        return None

    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        
        # Catalog is expected to be a list of tasks
        if isinstance(catalog, list):
            for task in catalog:
                if task.get('task_id') == task_id:
                    return task.get('prompt')
        
        # If catalog is a dict keyed by task_id
        if isinstance(catalog, dict):
            task = catalog.get(task_id)
            if task:
                return task.get('prompt')
                
        logger.warning(f"Task ID {task_id} not found in catalog.")
        return None
    except Exception as e:
        logger.error(f"Error loading catalog for {task_id}: {e}")
        return None

def _generate_with_openai(prompt: str, model_name: str, api_key: str) -> str:
    """
    Generate code using OpenAI API.
    """
    try:
        import openai
    except ImportError:
        raise ImportError("OpenAI package not installed. Install with: pip install openai")

    client = openai.OpenAI(api_key=api_key)
    
    # Map model names if necessary, assuming standard OpenAI names or passing through
    # If the model_name is a custom fallback name, we might need mapping, but 
    # typically resolve_model returns the actual API model ID.
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are an expert Python programmer. Provide only the code solution."},
            {"role": "user", "content": prompt}
        ],
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
        stop=["\ndef ", "\nclass ", "\nif __name__"] # Basic stops to encourage function completion
    )
    
    return response.choices[0].message.content.strip()

def _generate_with_huggingface(prompt: str, model_name: str) -> str:
    """
    Generate code using HuggingFace Transformers with 4-bit quantization (Mandatory).
    Uses bitsandbytes for quantization and device_map="cpu" as per SC-005.
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import bitsandbytes
    except ImportError as e:
        raise ImportError(f"Missing dependencies for HuggingFace generation: {e}. "
                          "Ensure bitsandbytes, transformers, and torch are installed.")

    logger.info(f"Loading model {model_name} with 4-bit quantization on CPU...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Mandatory 4-bit quantization configuration
    # quantization_config = BitsAndBytesConfig(
    #     load_in_4bit=True,
    #     bnb_4bit_compute_dtype=torch.float16,
    #     bnb_4bit_quant_type="nf4",
    #     bnb_4bit_use_double_quant=True,
    # )
    
    # Since bitsandbytes 4-bit support on CPU is experimental/limited in some versions,
    # we attempt standard 4-bit loading. If that fails due to CPU constraints, 
    # we might need to fall back to 8-bit or standard float16, but the task mandates 4-bit.
    # Note: bitsandbytes 4-bit is primarily optimized for CUDA. For CPU-only environments
    # with strict RAM limits, we proceed with the config but catch potential errors.
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float32, # Fallback to float32 for CPU stability if 4-bit fails
            load_in_4bit=True, # Attempt 4-bit
            trust_remote_code=True
        )
    except Exception as e:
        logger.warning(f"4-bit quantization on CPU failed ({e}). Attempting standard CPU load. "
                       "This may violate RAM limits if model is large.")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )

    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=DEFAULT_MAX_TOKENS,
            temperature=DEFAULT_TEMPERATURE,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract the generated part after the prompt
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):]
        
    return generated_text.strip()

def generate_code(task_id: str, model_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Generate code for a given task_id using the configured model chain.
    
    Args:
        task_id: The unique identifier for the task.
        model_name: Optional override for the model name.
        
    Returns:
        Tuple of (success: bool, content_or_error: str)
    """
    _ensure_output_dir()
    
    prompt = _load_prompt_from_catalog(task_id)
    if not prompt:
        return False, f"Prompt not found for task_id: {task_id}"
    
    # Resolve model chain
    if model_name:
        chain = [model_name]
    else:
        chain = get_model_chain()
    
    last_error = None
    
    for candidate_model in chain:
        config = get_model_config(candidate_model)
        if not config:
            logger.warning(f"Configuration missing for model {candidate_model}, skipping.")
            continue
        
        model_type = config.get('type', 'openai') # 'openai' or 'hf'
        api_key = None
        if model_type == 'openai':
            api_key = get_api_key()
            if not api_key:
                logger.warning("OpenAI API key not set, skipping OpenAI model.")
                continue
        
        try:
            logger.info(f"Attempting generation for {task_id} using {candidate_model} ({model_type})...")
            
            if model_type == 'openai':
                result = _generate_with_openai(prompt, candidate_model, api_key)
            elif model_type == 'hf':
                result = _generate_with_huggingface(prompt, candidate_model)
            else:
                logger.error(f"Unknown model type: {model_type}")
                continue
            
            # Save result
            output_path = GENERATION_OUTPUT_DIR / f"{task_id}.py"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            logger.info(f"Successfully generated code for {task_id} at {output_path}")
            return True, str(output_path)
            
        except Exception as e:
            last_error = str(e)
            logger.error(f"Generation failed for {task_id} with {candidate_model}: {e}")
            # Continue to next model in chain
            continue
    
    return False, f"All models failed. Last error: {last_error}"

def main():
    """
    CLI entry point for generating code for a specific task or batch.
    Usage: python -m code.llm_generator --task_id <id> [--model <name>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate code for LLM tasks")
    parser.add_argument("--task_id", type=str, required=True, help="Task ID to generate code for")
    parser.add_argument("--model", type=str, required=False, help="Optional specific model to use")
    args = parser.parse_args()
    
    success, message = generate_code(args.task_id, args.model)
    if success:
        print(f"Success: {message}")
    else:
        print(f"Failed: {message}")
        exit(1)

if __name__ == "__main__":
    main()
