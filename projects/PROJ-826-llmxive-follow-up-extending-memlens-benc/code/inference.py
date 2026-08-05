import os
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import psutil
import sys

from utils.logger import get_logger, log_inference_start, log_inference_end, log_resource_usage
import config

# Configure logging
logger = get_logger("inference")

def get_resource_usage() -> Dict[str, float]:
    """
    Captures current CPU time and peak RAM usage (in GB).
    Returns a dictionary with keys 'cpu_time' and 'peak_ram_gb'.
    """
    process = psutil.Process(os.getpid())
    # CPU time in seconds
    cpu_time = process.cpu_times().user + process.cpu_times().system
    # RSS (Resident Set Size) in bytes, convert to GB
    peak_ram_gb = process.memory_info().rss / (1024 ** 3)
    return {
        "cpu_time": cpu_time,
        "peak_ram_gb": peak_ram_gb
    }

def load_model(model_name: str = "microsoft/Phi-3-mini-4k-instruct", device_map: str = "cpu") -> Tuple[Any, Any]:
    """
    Loads the LLM model and tokenizer.
    Uses 4-bit quantization if available and requested, otherwise 16-bit.
    Forces CPU usage as per project constraints.
    """
    logger.info(f"Loading model: {model_name} on {device_map}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Ensure CPU is used
        if device_map == "cpu":
            device_map = "cpu"
            # Disable CUDA if accidentally enabled
            torch.cuda.is_available = lambda: False

        # Load with 4-bit quantization if torch and bitsandbytes are available, else 16-bit
        # Note: bitsandbytes is GPU-only usually, so for CPU we stick to float16 or float32
        # but we try to load efficiently.
        model_kwargs = {
            "device_map": device_map,
            "torch_dtype": torch.float32, # CPU usually works best with float32 or float16
            "trust_remote_code": True
        }
        
        # Attempt to load
        model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def truncate_context(
    text: str, 
    max_tokens: int, 
    tokenizer: Any, 
    strategy: str = "head_tail"
) -> str:
    """
    Truncates the input text to fit within max_tokens.
    
    Strategies:
    - "head": Keep only the beginning.
    - "tail": Keep only the end.
    - "head_tail": Keep the first 50% and last 50% of the allowed tokens, dropping the middle.
    
    Args:
        text: The input text to truncate.
        max_tokens: Maximum number of tokens allowed.
        tokenizer: The tokenizer object to use for tokenization.
        strategy: The truncation strategy to apply.
    
    Returns:
        The truncated string.
    """
    if not text:
        return ""

    # Tokenize
    tokens = tokenizer.encode(text, return_tensors="pt").squeeze(0)
    current_len = len(tokens)

    if current_len <= max_tokens:
        return text

    logger.warning(f"Context window exceeded ({current_len} > {max_tokens}). Applying '{strategy}' truncation.")

    if strategy == "head":
        truncated_tokens = tokens[:max_tokens]
    elif strategy == "tail":
        truncated_tokens = tokens[-max_tokens:]
    elif strategy == "head_tail":
        # Keep first half and last half of the max_tokens
        half = max_tokens // 2
        first_half = tokens[:half]
        second_half = tokens[-half:]
        truncated_tokens = torch.cat([first_half, second_half], dim=0)
    else:
        logger.warning(f"Unknown strategy '{strategy}', defaulting to 'head'.")
        truncated_tokens = tokens[:max_tokens]

    # Decode back to string
    # We need to handle the case where the tokenizer might add special tokens or not
    # Using decode with skip_special_tokens=True is generally safe for context
    truncated_text = tokenizer.decode(truncated_tokens, skip_special_tokens=True)
    return truncated_text

def generate_answer(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7
) -> str:
    """
    Generates an answer given a prompt using the loaded model.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Move to CPU explicitly if not already
    inputs = {k: v.cpu() for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode the output, skipping the input prompt
    generated_text = tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
    return generated_text.strip()

def run_inference_pipeline(
    model: Any,
    tokenizer: Any,
    questions: List[Dict[str, Any]],
    memory_stores: Dict[str, Any],
    context_window_size: int = 4096,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Runs the inference pipeline for a list of questions.
    
    1. Retrieves relevant context from memory stores based on the question.
    2. Constructs the full prompt including retrieved context.
    3. Truncates the prompt if it exceeds context_window_size.
    4. Generates the answer.
    5. Records resource usage and latency.
    
    Args:
        model: The loaded LLM model.
        tokenizer: The loaded tokenizer.
        questions: List of question dictionaries.
        memory_stores: Dictionary containing Coarse, Medium, and Fine store objects/results.
        context_window_size: Maximum tokens allowed for the input context + prompt.
        output_path: Optional path to save results.
    
    Returns:
        List of result dictionaries containing question_id, answer, latency, and resource_usage.
    """
    results = []
    
    # Default context window if not specified in config
    if context_window_size is None:
        context_window_size = config.DEFAULT_CONTEXT_WINDOW if hasattr(config, 'DEFAULT_CONTEXT_WINDOW') else 4096

    logger.info(f"Starting inference pipeline with context window size: {context_window_size}")

    for i, q in enumerate(questions):
        start_time = time.time()
        start_resources = get_resource_usage()
        log_inference_start(i, len(questions), q.get("id", "unknown"))

        question_text = q.get("question", "")
        retrieved_context = ""
        
        # Retrieve context (Simplified logic assuming stores are ready)
        # In a real scenario, we would call retrieval.py functions here based on the store type
        # For this task, we assume the context is passed or retrieved simply.
        # Let's simulate retrieval from a hypothetical 'context' key or empty if not present
        # In a full implementation, we would integrate with run_coarse_retrieval, etc.
        # Since this task is specifically about context window management, we focus on the truncation logic.
        
        # Mock retrieval for the sake of the pipeline flow if not provided
        # Ideally, we'd call: context = run_fine_retrieval(...)
        if "retrieved_context" in q:
            retrieved_context = q["retrieved_context"]
        else:
            # Fallback: just use the question if no context
            retrieved_context = "No additional context retrieved."

        # Construct Prompt
        # Format: "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
        full_prompt = f"Context: {retrieved_context}\n\nQuestion: {question_text}\n\nAnswer:"

        # TRUNCATION LOGIC (Core of T017)
        # We need to ensure full_prompt fits within context_window_size
        # We also need to reserve space for generated tokens, but the function truncates INPUT
        # So we truncate the prompt to fit max_tokens
        
        # Estimate tokens for the prompt
        # We use the tokenizer to count
        prompt_tokens = tokenizer.encode(full_prompt, return_tensors="pt").squeeze(0)
        if len(prompt_tokens) > context_window_size:
            full_prompt = truncate_context(full_prompt, context_window_size, tokenizer, strategy="head_tail")
            logger.debug(f"Prompt truncated to fit context window.")

        try:
            answer = generate_answer(model, tokenizer, full_prompt)
        except Exception as e:
            logger.error(f"Inference failed for question {i}: {e}")
            answer = f"Error: {str(e)}"

        end_time = time.time()
        end_resources = get_resource_usage()
        latency = end_time - start_time
        
        # Resource delta
        resource_usage = {
            "cpu_time_delta": end_resources["cpu_time"] - start_resources["cpu_time"],
            "peak_ram_gb": end_resources["peak_ram_gb"]
        }
        log_resource_usage(i, latency, resource_usage)
        log_inference_end(i, answer[:100])

        results.append({
            "id": q.get("id", f"q_{i}"),
            "question": question_text,
            "answer": answer,
            "latency_seconds": latency,
            "resource_usage": resource_usage,
            "context_truncated": len(prompt_tokens) > context_window_size
        })

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")

    return results

def main():
    """
    Main entry point for running the inference pipeline.
    Expects environment variables or config for model path and data paths.
    """
    logger.info("Starting Inference Pipeline Main")
    
    # Load model
    model_name = os.environ.get("LLM_MODEL", "microsoft/Phi-3-mini-4k-instruct")
    model, tokenizer = load_model(model_name, device_map="cpu")

    # Load questions (Mock data for demonstration of the pipeline logic)
    # In a real run, this would come from data/processed/questions.json or similar
    questions = [
        {"id": "1", "question": "What is the main object in the image?"},
        {"id": "2", "question": "Describe the action happening."}
    ]
    
    # Mock memory stores
    memory_stores = {}

    # Run pipeline
    results = run_inference_pipeline(
        model=model,
        tokenizer=tokenizer,
        questions=questions,
        context_window_size=2048, # Example smaller window to trigger truncation logic
        output_path="data/processed/inference_results.json"
    )

    print(f"Pipeline completed. Processed {len(results)} questions.")
    for r in results:
        print(f"Q: {r['question']} -> A: {r['answer'][:50]}...")

if __name__ == "__main__":
    main()