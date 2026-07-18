from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_api_key, get_model_chain, get_model_config, resolve_model, ModelConfig
from utils import exponential_backoff_retry
from logger_config import get_logger, log_operation

# Configure module logger
logger = get_logger("llm_generator")

# Constants for generation
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.2
GENERATION_TIMEOUT = 60  # seconds

def generate_code(
    prompt: str,
    model_config: ModelConfig,
    task_id: str,
    max_retries: int = 3,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE
) -> Optional[str]:
    """
    Generate code using the specified model configuration with exponential backoff retry logic.
    
    Args:
        prompt: The code generation prompt
        model_config: Configuration for the LLM model
        task_id: Unique identifier for the task
        max_retries: Maximum number of retry attempts
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        Generated code string or None if generation fails
    """
    logger.log("generation_attempt", task_id=task_id, model=model_config.model_name)
    
    def _attempt_generation() -> str:
        """Internal function to attempt a single generation call."""
        if model_config.model_name.startswith("gpt"):
            # Use OpenAI API for proprietary models
            import openai
            
            client = openai.OpenAI(api_key=get_api_key())
            
            response = client.chat.completions.create(
                model=model_config.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=GENERATION_TIMEOUT
            )
            
            return response.choices[0].message.content
        
        elif model_config.model_name.startswith("code-llama"):
            # Use HuggingFace transformers for local CPU inference
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                tokenizer = AutoTokenizer.from_pretrained(model_config.hf_model_id)
                model = AutoModelForCausalLM.from_pretrained(
                    model_config.hf_model_id,
                    torch_dtype=torch.float32,  # Force float32 for CPU compatibility
                    low_cpu_mem_usage=True
                )
                
                inputs = tokenizer(prompt, return_tensors="pt")
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Extract just the generated part after the prompt
                if generated_text.startswith(prompt):
                    return generated_text[len(prompt):]
                return generated_text
                
            except ImportError as e:
                logger.log("import_error", error=str(e), task_id=task_id)
                raise RuntimeError(f"Missing dependencies for local inference: {e}")
        else:
            raise ValueError(f"Unsupported model type: {model_config.model_name}")

    # Apply exponential backoff retry
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            result = _attempt_generation()
            logger.log("generation_success", task_id=task_id, model=model_config.model_name, attempt=attempt)
            return result
        except Exception as e:
            last_error = e
            wait_time = exponential_backoff_retry(attempt, base_wait=1, max_wait=10)
            logger.log("generation_retry", task_id=task_id, attempt=attempt, error=str(e), wait_time=wait_time)
            time.sleep(wait_time)
    
    logger.log("generation_failed", task_id=task_id, error=str(last_error), max_retries=max_retries)
    return None

def save_generated_code(code: str, task_id: str, output_dir: str = "data/generated") -> Path:
    """
    Save generated code to a file.
    
    Args:
        code: The generated code string
        task_id: Unique identifier for the task
        output_dir: Directory to save the generated code
        
    Returns:
        Path to the saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / f"{task_id}.py"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    logger.log("code_saved", task_id=task_id, file_path=str(file_path))
    return file_path

def save_generation_result(
    task_id: str,
    status: str,
    model_used: str,
    error_message: Optional[str] = None,
    output_dir: str = "data/generated"
) -> Path:
    """
    Save the result of a generation attempt (success or failure).
    
    Args:
        task_id: Unique identifier for the task
        status: 'success' or 'failed'
        model_used: Name of the model used for generation
        error_message: Error message if generation failed
        output_dir: Directory to save the result
        
    Returns:
        Path to the result JSON file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    result = {
        "task_id": task_id,
        "status": status,
        "model_used": model_used,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    if error_message:
        result["error_message"] = error_message
    
    result_file = output_path / f"{task_id}_result.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.log("result_saved", task_id=task_id, file_path=str(result_file), status=status)
    return result_file

def process_task_generation(
    task: Dict[str, Any],
    catalog: List[Dict[str, Any]],
    output_dir: str = "data/generated"
) -> Dict[str, Any]:
    """
    Process a single task for code generation with model fallback logic.
    
    Args:
        task: Task dictionary from the catalog
        catalog: Full task catalog (for context)
        output_dir: Directory to save generated code and results
        
    Returns:
        Dictionary with generation status and metadata
    """
    task_id = task["task_id"]
    prompt = task["prompt"]
    
    result = {
        "task_id": task_id,
        "status": "failed",
        "model_used": None,
        "generation_time": None,
        "error_message": None
    }
    
    # Get the model chain from config
    model_chain = get_model_chain()
    
    start_time = time.time()
    
    for model_name in model_chain:
        try:
            model_config = get_model_config(model_name)
            logger.log("trying_model", task_id=task_id, model_name=model_name)
            
            generated_code = generate_code(
                prompt=prompt,
                model_config=model_config,
                task_id=task_id,
                max_retries=3
            )
            
            if generated_code is not None:
                # Success - save the code
                save_generated_code(generated_code, task_id, output_dir)
                
                result["status"] = "success"
                result["model_used"] = model_name
                result["generation_time"] = time.time() - start_time
                
                logger.log("generation_complete", task_id=task_id, model=model_name)
                return result
                
        except Exception as e:
            logger.log("model_failed", task_id=task_id, model_name=model_name, error=str(e))
            continue
    
    # All models failed
    result["error_message"] = "All models in the chain failed to generate code"
    logger.log("all_models_failed", task_id=task_id)
    save_generation_result(task_id, "failed", "none", result["error_message"], output_dir)
    
    return result

def main():
    """Main entry point for the LLM generator module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Code Generator")
    parser.add_argument("--task-id", type=str, help="Specific task ID to process")
    parser.add_argument("--output-dir", type=str, default="data/generated", help="Output directory")
    parser.add_argument("--catalog", type=str, default="data/benchmarks/processed/catalog.json", help="Path to task catalog")
    
    args = parser.parse_args()
    
    # Load catalog
    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        logger.log("catalog_not_found", path=str(catalog_path))
        return
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    
    # Process specific task or all tasks
    tasks_to_process = catalog if not args.task_id else [t for t in catalog if t["task_id"] == args.task_id]
    
    if not tasks_to_process:
        logger.log("no_tasks_found", task_id=args.task_id)
        return
    
    results = []
    for task in tasks_to_process:
        result = process_task_generation(task, catalog, args.output_dir)
        results.append(result)
        
    # Log summary
    success_count = sum(1 for r in results if r["status"] == "success")
    logger.log("generation_summary", total=len(results), successful=success_count, failed=len(results) - success_count)

if __name__ == "__main__":
    main()