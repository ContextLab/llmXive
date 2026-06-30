import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import psutil
import os

from src.lib.config import get_logger, configure_logging, set_seed
from src.lib.memory_monitor import check_memory_limit, format_bytes
from src.lib.text_utils import parse_llm_route_output, generate_route_sequence
from src.models.validation import validate_route_sequence

# Configure logging
configure_logging(level=logging.INFO)
logger = get_logger("optimize_inference")

# Constants
MAX_TIME_SECONDS = 6 * 3600  # 6 hours
MEMORY_LIMIT_GB = 7
BATCH_SIZE = 1  # Keep batch size 1 for CPU stability, optimize via other means

def load_model_optimized(model_name: str, max_memory_gb: float = 7.0) -> tuple:
    """
    Loads a model optimized for CPU inference with memory constraints.
    Returns (model, tokenizer).
    """
    logger.info(f"Loading model: {model_name} with max memory {max_memory_gb}GB")
    
    # Check memory before loading
    if not check_memory_limit(max_memory_gb * 1024 * 1024 * 1024):
        raise RuntimeError(f"Insufficient memory available. Limit: {max_memory_gb}GB")

    # Use 8-bit quantization for CPU to reduce memory footprint and improve speed
    # without significant accuracy loss for this specific task
    try:
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
            llm_int8_skip_modules=["lm_head"],
        )
    except Exception:
        # Fallback if bitsandbytes not configured correctly or model incompatible
        logger.warning("8-bit quantization failed or not supported, falling back to standard loading")
        bnb_config = None

    try:
        if bnb_config:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="cpu",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info(f"Model loaded successfully. Memory usage: {format_bytes(psutil.Process().memory_info().rss)}")
    return model, tokenizer

def run_batched_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompts: List[str],
    max_new_tokens: int = 128,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> List[str]:
    """
    Runs inference on a list of prompts.
    Optimizations:
    1. Tokenize all prompts at once to avoid overhead.
    2. Use padding to create a batch (even if batch_size=1 effectively, padding helps CPU vectorization).
    3. Disable caching if memory is tight (though we use low_cpu_mem_usage).
    """
    logger.info(f"Running inference on {len(prompts)} prompts")
    
    # Tokenize
    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    generated_sequences = []
    
    # Process in chunks if the list is huge to avoid OOM on the input tensor itself,
    # though for N=100 this is usually fine.
    chunk_size = 10
    for i in range(0, len(prompts), chunk_size):
        chunk_ids = input_ids[i:i+chunk_size]
        chunk_mask = attention_mask[i:i+chunk_size]
        
        with torch.no_grad():
            outputs = model.generate(
                chunk_ids,
                attention_mask=chunk_mask,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                # Optimization: disable cache for CPU if memory is critical, 
                # but usually model.generate handles this well.
                use_cache=True 
            )
        
        for output_ids in outputs:
            # Decode only the new tokens
            new_tokens = output_ids[len(chunk_ids[0]):]
            text = tokenizer.decode(new_tokens, skip_special_tokens=True)
            generated_sequences.append(text)
            
        # Force garbage collection between chunks to free VRAM/RAM
        if i + chunk_size < len(prompts):
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()

    return generated_sequences

def run_optimized_benchmark(
    graph_path: Path,
    od_pairs_path: Path,
    output_path: Path,
    model_name: str,
    max_new_tokens: int = 128
) -> Dict[str, Any]:
    """
    Runs the full benchmark with optimizations to ensure N=100 completes < 6h.
    """
    logger.info("Starting optimized benchmark run")
    
    # Load Data
    with open(od_pairs_path, 'r') as f:
        od_pairs = json.load(f)
    
    # Limit to N=100 if more exist
    if len(od_pairs) > 100:
        logger.info(f"Limiting benchmark to first 100 pairs (found {len(od_pairs)})")
        od_pairs = od_pairs[:100]
    
    prompts = []
    od_metadata = []
    
    for item in od_pairs:
        origin = item.get("origin")
        destination = item.get("destination")
        prompt = generate_route_sequence(origin, destination)
        prompts.append(prompt)
        od_metadata.append({"origin": origin, "destination": destination})
    
    # Load Model
    model, tokenizer = load_model_optimized(model_name, MEMORY_LIMIT_GB)
    
    start_time = time.time()
    
    # Inference
    logger.info("Running inference...")
    outputs = run_batched_inference(model, tokenizer, prompts, max_new_tokens=max_new_tokens)
    
    inference_time = time.time() - start_time
    logger.info(f"Inference completed in {inference_time:.2f} seconds")
    
    # Parse and Validate
    results = []
    validation_start = time.time()
    
    # Load graph for validation
    from src.lib.splitter import load_graph_from_file
    graph = load_graph_from_file(graph_path)
    
    for i, (output, meta) in enumerate(zip(outputs, od_metadata)):
        parsed_route = parse_llm_route_output(output)
        if not parsed_route:
            results.append({
                "origin": meta["origin"],
                "destination": meta["destination"],
                "valid": False,
                "score": 0.0,
                "raw_output": output,
                "error": "Failed to parse route"
            })
            continue
        
        validation_result = validate_route_sequence(parsed_route, graph)
        results.append({
            "origin": meta["origin"],
            "destination": meta["destination"],
            "valid": validation_result.valid,
            "score": validation_result.exact_match_score,
            "raw_output": output,
            "parsed_route": parsed_route
        })
    
    validation_time = time.time() - validation_start
    total_time = time.time() - start_time
    
    # Save Results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            "results": results,
            "metrics": {
                "total_time_seconds": total_time,
                "inference_time_seconds": inference_time,
                "validation_time_seconds": validation_time,
                "samples_processed": len(results),
                "valid_count": sum(1 for r in results if r["valid"]),
                "avg_score": sum(r["score"] for r in results) / len(results) if results else 0.0
            }
        }, f, indent=2)
    
    logger.info(f"Benchmark complete. Results saved to {output_path}")
    logger.info(f"Total time: {total_time:.2f}s ({total_time/3600:.2f}h)")
    logger.info(f"Validation: {sum(1 for r in results if r['valid'])}/{len(results)} valid")
    
    return {
        "success": total_time < MAX_TIME_SECONDS,
        "total_time": total_time,
        "valid_count": sum(1 for r in results if r["valid"]),
        "total_samples": len(results)
    }

def main():
    parser = argparse.ArgumentParser(description="Optimized Inference Benchmark Runner")
    parser.add_argument("--graph", type=str, required=True, help="Path to GTFS graph JSON")
    parser.add_argument("--od-pairs", type=str, required=True, help="Path to O-D pairs JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output results JSON")
    parser.add_argument("--model", type=str, default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", help="Model name")
    
    args = parser.parse_args()
    
    try:
        result = run_optimized_benchmark(
            graph_path=Path(args.graph),
            od_pairs_path=Path(args.od_pairs),
            output_path=Path(args.output),
            model_name=args.model
        )
        
        if result["success"]:
            print(f"SUCCESS: Completed in {result['total_time']:.2f}s. Valid: {result['valid_count']}/{result['total_samples']}")
            sys.exit(0)
        else:
            print(f"FAILED: Exceeded time limit. Time: {result['total_time']:.2f}s")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
