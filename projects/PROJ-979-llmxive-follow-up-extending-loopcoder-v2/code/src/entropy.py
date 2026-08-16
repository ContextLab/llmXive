import ast
import hashlib
import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Project relative imports (ensure path is set correctly)
# We assume this file is run from the project root or code/src is in sys.path
# The task description implies we should import from code/src
# If running as script, we need to handle imports carefully
try:
    from config import load_config
except ImportError:
    # Fallback if config.py is not directly importable
    # We will implement a simple config loader here to avoid circular deps or missing files
    def load_config(path: str = "code/config.yaml") -> Dict[str, Any]:
        import yaml
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at {path}")
        with open(path, 'r') as f:
            return yaml.safe_load(f)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model(model_path: str, device: str = "cpu") -> Tuple[Any, Any]:
    """
    Load the CodeLlama model and tokenizer.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model path not found: {model_path}. "
                                "Please set CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH environment variable.")
    
    logger.info(f"Loading model from {model_path} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None
    )
    if device == "cpu":
        model = model.to(torch.float32)
    else:
        model = model.to(device)
    
    return model, tokenizer

def normalize_ast(code: str) -> str:
    """
    Normalize code by parsing to AST and hashing it.
    This handles structural equivalence ignoring whitespace/comments.
    """
    try:
        tree = ast.parse(code)
        # Remove docstrings and comments by re-parsing or just using ast.dump
        # A simple normalization is to dump the AST structure
        # To be robust against variable renaming, we could use a custom visitor,
        # but for this task, we stick to AST hash as a proxy for structural similarity.
        # We normalize whitespace in the dump string to ensure consistency.
        dump_str = ast.dump(tree)
        # Remove whitespace for hashing
        normalized = "".join(dump_str.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    except SyntaxError:
        # If code is invalid, return a unique hash for the raw string
        return hashlib.sha256(code.encode('utf-8')).hexdigest()

def generate_samples(
    prompt: str,
    model: Any,
    tokenizer: Any,
    n_samples: int = 10,
    temperature: float = 0.7,
    top_p: float = 0.95,
    max_new_tokens: int = 512
) -> List[str]:
    """
    Generate N samples for a given prompt.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples = []
    
    # Ensure reproducibility if seed is set globally
    with torch.no_grad():
        for _ in range(n_samples):
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract just the completion part (after the prompt)
            # This is a simple heuristic; real usage might need more robust parsing
            completion = generated_text[len(prompt):]
            samples.append(completion.strip())
    
    return samples

def cluster_samples(samples: List[str]) -> Dict[str, int]:
    """
    Cluster samples by their normalized AST hash.
    Returns a dictionary mapping cluster_hash -> count.
    """
    clusters = {}
    for sample in samples:
        # Normalize and hash
        cluster_key = normalize_ast(sample)
        clusters[cluster_key] = clusters.get(cluster_key, 0) + 1
    return clusters

def compute_shannon_entropy(cluster_counts: Dict[str, int], n_total: int) -> float:
    """
    Compute Shannon entropy over cluster probabilities.
    """
    if n_total == 0:
        return 0.0
    
    entropy = 0.0
    for count in cluster_counts.values():
        if count > 0:
            p = count / n_total
            entropy -= p * np.log2(p)
    
    return entropy

def log_exclusions(exclusions: List[Dict[str, Any]], output_path: str):
    """
    Log exclusion events to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(exclusions, f, indent=2)

def load_filtered_splits(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the filtered splits from JSON.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered splits not found at {input_path}")
    with open(input_path, 'r') as f:
        data = json.load(f)
    return data.get('train', []) + data.get('test', [])

def process_entropy_for_dataset(
    model: Any,
    tokenizer: Any,
    input_data: List[Dict[str, Any]],
    n_samples: int = 10,
    temperature: float = 0.7,
    top_p: float = 0.95
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process the dataset to compute entropy for each task.
    Returns (results, exclusions).
    """
    results = []
    exclusions = []
    
    for item in input_data:
        task_id = item.get('task_id')
        prompt = item.get('prompt')
        
        if not task_id or not prompt:
            exclusions.append({
                'task_id': task_id,
                'reason': 'Missing task_id or prompt'
            })
            continue
        
        try:
            samples = generate_samples(
                prompt, model, tokenizer,
                n_samples=n_samples,
                temperature=temperature,
                top_p=top_p
            )
            
            if not samples:
                exclusions.append({
                    'task_id': task_id,
                    'reason': 'No samples generated'
                })
                continue
            
            clusters = cluster_samples(samples)
            entropy = compute_shannon_entropy(clusters, len(samples))
            
            # Handle undefined entropy (zero entropy)
            if entropy == 0.0:
                entropy = 1e-9
            
            results.append({
                'task_id': task_id,
                'entropy': entropy,
                'exclusion_reason': None
            })
            
        except Exception as e:
            exclusions.append({
                'task_id': task_id,
                'reason': str(e)
            })
            logger.error(f"Error processing task {task_id}: {e}")
    
    return results, exclusions

def main():
    """
    Main entry point for the entropy extraction pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract entropy from dataset")
    parser.add_argument("--input", type=str, default="data/processed/filtered_splits.json",
                        help="Path to filtered splits JSON")
    parser.add_argument("--output", type=str, default="data/processed/entropy_results.csv",
                        help="Path to output CSV")
    parser.add_argument("--exclusion-log", type=str, default="data/processed/exclusion_log.json",
                        help="Path to exclusion log JSON")
    parser.add_argument("--sample-size", type=int, default=10,
                        help="Number of samples per task")
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    temperature = config.get('model_temperature', 0.7)
    top_p = config.get('model_top_p', 0.95)
    
    # Determine model path
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_path = os.getenv("CODELLAMA_GPU_PATH") if device == "cuda" else os.getenv("CODELLAMA_CPU_PATH")
    
    if not model_path or model_path == "NOT_SET":
        raise ValueError("Model path not set. Please set CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH environment variable.")
    
    # Ensure output directories exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    exclusion_log_dir = os.path.dirname(args.exclusion_log)
    if exclusion_log_dir and not os.path.exists(exclusion_log_dir):
        os.makedirs(exclusion_log_dir)
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    input_data = load_filtered_splits(args.input)
    logger.info(f"Loaded {len(input_data)} samples")
    
    # Load model
    model, tokenizer = load_model(model_path, device)
    
    # Process entropy
    logger.info("Computing entropy...")
    results, exclusions = process_entropy_for_dataset(
        model, tokenizer, input_data,
        n_samples=args.sample_size,
        temperature=temperature,
        top_p=top_p
    )
    
    # Save results
    logger.info(f"Saving results to {args.output}")
    with open(args.output, 'w', newline='') as f:
        import csv
        writer = csv.DictWriter(f, fieldnames=['task_id', 'entropy', 'exclusion_reason'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    # Save exclusions
    logger.info(f"Saving exclusion log to {args.exclusion_log}")
    log_exclusions(exclusions, args.exclusion_log)
    
    logger.info("Entropy extraction complete.")
    logger.info(f"Processed {len(results)} tasks, excluded {len(exclusions)} tasks")

if __name__ == "__main__":
    main()
