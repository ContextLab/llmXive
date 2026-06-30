import os
import json
import logging
import time
from typing import Optional, List, Dict, Any, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

from config import get_api_key, get_fallback_models, resolve_model
from utils import safe_call_with_retry

# Configure logging
logger = logging.getLogger(__name__)

def generate_code(
    prompt: str,
    model_name: str,
    max_tokens: int = 512,
    temperature: float = 0.2,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Generate code using the specified model.
    
    Args:
        prompt: Input prompt for code generation
        model_name: Name of the model to use
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        logger: Optional logger instance
    
    Returns:
        Tuple of (success, generated_code_or_error, model_used)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        # Check if we need to use local model (fallback) or API
        # For this implementation, we assume local model usage for fallback models
        # as per SC-005 (7GB RAM limit) requiring 4-bit quantization

        # Load tokenizer and model with 4-bit quantization for memory efficiency
        logger.info(f"Loading model: {model_name}")
        
        # Quantization config for 4-bit inference
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Handle padding token for models that don't have it set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto", # Automatically map to available devices (CPU/GPU)
            trust_remote_code=True,
            torch_dtype=torch.float16
        )

        logger.info("Model loaded successfully")

        # Prepare input
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        
        # Generate
        start_time = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generation_time = time.time() - start_time
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract code (assuming the model outputs code directly or in a block)
        # Simple extraction: remove prompt if present
        if prompt in generated_text:
            generated_code = generated_text.split(prompt, 1)[1].strip()
        else:
            generated_code = generated_text.strip()

        logger.info(f"Generation completed in {generation_time:.2f}s")
        return (True, generated_code, model_name)

    except Exception as e:
        error_msg = f"Generation failed: {str(e)}"
        logger.error(error_msg)
        return (False, error_msg, None)

def run_generation_batch(
    tasks: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    batch_size: int = 10,
    logger: Optional[logging.Logger] = None
) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Run code generation for a batch of tasks.
    
    Args:
        tasks: List of task dictionaries with 'task_id' and 'prompt'
        model_name: Model to use (optional, will use default if None)
        batch_size: Number of tasks to process
        logger: Optional logger instance
    
    Returns:
        Tuple of (last_generated_path, overall_success, error_message)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if not model_name:
        model_name = resolve_model(None)
        if not model_name:
            return (None, False, "No model available")

    logger.info(f"Starting batch generation for {len(tasks)} tasks using {model_name}")
    
    generated_files = []
    
    for task in tasks:
        task_id = task.get('task_id', 'unknown')
        prompt = task.get('prompt', '')
        
        if not prompt:
            logger.warning(f"Skipping task {task_id}: No prompt provided")
            continue

        # Generate code
        success, result, used_model = generate_code(
            prompt,
            model_name,
            logger=logger
        )

        if success:
            # Save to file
            output_path = f"data/generated/{task_id}.py"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Task ID: {task_id}\n")
                f.write(f"# Model: {used_model}\n")
                f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(result)
            
            generated_files.append(output_path)
            logger.info(f"Saved generated code for {task_id} to {output_path}")
        else:
            logger.error(f"Failed to generate code for {task_id}: {result}")
            # Return immediately on first failure for this implementation
            # In a more robust version, we might continue
            return (None, False, result)

    if generated_files:
        return (generated_files[-1], True, None)
    else:
        return (None, False, "No tasks were successfully generated")
