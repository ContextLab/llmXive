import os
import sys
import time
import threading
import logging
import json
import torch
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from config import get_model_path, get_timeout_inference, get_seed_global, ensure_directories
from utils.logging import get_inference_logger, init_logging
from utils.memory_monitor import get_current_memory_mb, check_memory_limit, set_soft_memory_limit
from model.sandbox import execute_test_case, ExecutionStatus

# Initialize logger
logger = get_inference_logger()

def load_model(model_id: str = "bigcode/starcoder2-3b") -> Tuple[Any, Any]:
    """
    Loads the StarCoder2-3B model with 4-bit quantization for CPU compatibility.
    
    Args:
        model_id: HuggingFace model identifier.
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {model_id}")
    
    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        llm_int8_enable_fp32_cpu_offload=True,
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"]
    )

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            cache_dir=str(Path.home() / ".cache/huggingface")
        )
        
        # Set padding token if not exists
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            cache_dir=str(Path.home() / ".cache/huggingface")
        )
        
        model.eval()
        logger.info("Model loaded successfully with 4-bit quantization")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_code(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
    top_p: float = 0.95
) -> Dict[str, Any]:
    """
    Generates code from a prompt and calculates confidence score.
    
    Args:
        model: The loaded model.
        tokenizer: The loaded tokenizer.
        prompt: The input prompt text.
        max_new_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.
        top_p: Top-p sampling threshold.
        
    Returns:
        Dictionary containing 'code', 'confidence_score', and 'raw_tokens'.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_len = inputs["input_ids"].shape[1]
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True if temperature > 0 else False,
            pad_token_id=tokenizer.pad_token_id,
            return_dict_in_generate=True,
            output_scores=True
        )
    
    generated_ids = outputs.sequences[0]
    generated_tokens = generated_ids[input_len:]
    
    # Decode the generated code
    generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    
    # Calculate confidence score (average token probability)
    # Get logits for the generated sequence
    if hasattr(outputs, 'scores'):
        scores = outputs.scores
        # scores is a tuple of tensors, one for each generated token
        # Each tensor has shape (batch_size, vocab_size)
        
        log_probs = []
        for i, score in enumerate(scores):
            # Get the log probability of the generated token at this step
            token_id = generated_tokens[i].item()
            log_prob = torch.log_softmax(score[0], dim=-1)[token_id]
            log_probs.append(log_prob.item())
        
        avg_log_prob = sum(log_probs) / len(log_probs) if log_probs else 0.0
        # Convert log-prob to a probability-like score (0-1 range, higher is better)
        confidence_score = float(torch.exp(torch.tensor(avg_log_prob)).item())
    else:
        # Fallback if scores not available
        confidence_score = 0.0
    
    return {
        "code": generated_text,
        "confidence_score": confidence_score,
        "raw_tokens": len(generated_tokens),
        "avg_log_prob": avg_log_prob if 'avg_log_prob' in locals() else 0.0
    }

def run_generation_loop(
    model: Any,
    tokenizer: Any,
    tasks: List[Dict[str, Any]],
    output_path: str,
    timeout_per_task: int = 60
) -> List[Dict[str, Any]]:
    """
    Runs generation for a list of tasks and logs results.
    
    Args:
        model: The loaded model.
        tokenizer: The loaded tokenizer.
        tasks: List of task dictionaries with 'task_id' and 'prompt'.
        output_path: Path to save results JSON.
        timeout_per_task: Timeout in seconds per task.
        
    Returns:
        List of result dictionaries.
    """
    results = []
    
    for task in tasks:
        task_id = task.get("task_id", "unknown")
        prompt = task.get("prompt", "")
        
        logger.info(f"Processing task: {task_id}")
        
        try:
            # Check memory before generation
            mem_mb = get_current_memory_mb()
            if mem_mb > 5500:  # Safety margin below 6GB
                logger.warning(f"Memory usage high ({mem_mb}MB). Skipping task {task_id}.")
                results.append({
                    "task_id": task_id,
                    "code": None,
                    "confidence_score": None,
                    "status": "OOM",
                    "error": "Memory limit exceeded"
                })
                continue
            
            start_time = time.time()
            generation_result = generate_code(model, tokenizer, prompt)
            elapsed = time.time() - start_time
            
            if elapsed > timeout_per_task:
                logger.warning(f"Task {task_id} timed out ({elapsed:.2f}s)")
                results.append({
                    "task_id": task_id,
                    "code": None,
                    "confidence_score": None,
                    "status": "TIMEOUT",
                    "error": f"Generation took {elapsed:.2f}s"
                })
            else:
                results.append({
                    "task_id": task_id,
                    "code": generation_result["code"],
                    "confidence_score": generation_result["confidence_score"],
                    "status": "SUCCESS",
                    "generation_time": elapsed,
                    "raw_tokens": generation_result["raw_tokens"]
                })
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            results.append({
                "task_id": task_id,
                "code": None,
                "confidence_score": None,
                "status": "ERROR",
                "error": str(e)
            })
        
        # Garbage collection to manage memory
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
    return results

def save_results_to_json(results: List[Dict[str, Any]], output_path: str):
    """
    Saves generation results to a JSON file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to save the JSON file.
    """
    ensure_directories()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for running inference on perturbed tasks.
    """
    # Load configuration
    model_path = get_model_path()
    timeout = get_timeout_inference()
    seed = get_seed_global()
    
    # Set random seeds for reproducibility
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    
    # Load perturbation tasks
    perturbation_file = Path("data/processed/perturbation_candidates.json")
    if not perturbation_file.exists():
        logger.error("Perturbation candidates file not found. Run T018 first.")
        sys.exit(1)
        
    with open(perturbation_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    logger.info(f"Loaded {len(tasks)} perturbation tasks")
    
    # Load model
    try:
        model, tokenizer = load_model(model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Run generation
    results = run_generation_loop(model, tokenizer, tasks, timeout)
    
    # Save results
    output_path = "data/processed/inference_logs.json"
    save_results_to_json(results, output_path)
    
    # Log summary
    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    logger.info(f"Generation complete: {success_count}/{len(results)} tasks successful")
    
    # Verify output format for T021
    if results:
        assert 'code' in results[0], "Missing 'code' field in result"
        assert 'confidence_score' in results[0], "Missing 'confidence_score' field in result"
        logger.info("Verification passed: Output format matches T021 requirements")

if __name__ == "__main__":
    init_logging()
    main()
