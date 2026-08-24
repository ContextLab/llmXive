import ast
import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from datasets import load_dataset

from src.config import load_config, get_config_value
from src.utils import set_global_seed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_model(model_name: str = None) -> Tuple[Any, Any]:
    """
    Load the specified model and tokenizer.
    Falls back to config if model_name is not provided.
    """
    config = load_config()
    if not model_name:
        model_name = get_config_value(config, 'MODEL_NAME', 'codellama/CodeLlama-1.3b-Instruct-hf')
    
    logger.info(f"Loading model: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        # Ensure tokenizer has a pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Check for GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True
        )
        if device == "cpu":
            model = model.to(device)
        
        return model, tokenizer
    except OSError as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def normalize_ast(code: str) -> Optional[str]:
    """
    Normalize code by parsing to AST and un-parsing to handle whitespace/aliasing differences.
    Returns None if parsing fails.
    """
    try:
        tree = ast.parse(code)
        # Remove docstrings for better comparison if needed, but standard unparse is usually enough
        return ast.unparse(tree)
    except SyntaxError:
        return None

def generate_samples(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10, temperature: float = 0.7, top_p: float = 0.95) -> List[str]:
    """
    Generate n_samples completions for the given prompt.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples = []
    
    # Set seed for reproducibility if needed, but we want randomness here
    with torch.no_grad():
        for _ in range(n_samples):
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
            generated = outputs[0][inputs['input_ids'].shape[1]:]
            text = tokenizer.decode(generated, skip_special_tokens=True)
            samples.append(text)
    
    return samples

def cluster_samples(samples: List[str]) -> Dict[str, int]:
    """
    Cluster samples by their normalized AST hash.
    Returns a dict mapping hash -> count.
    """
    clusters = {}
    for sample in samples:
        normalized = normalize_ast(sample)
        if normalized is None:
            # Treat syntax errors as unique or a special cluster? 
            # Let's hash the raw string for syntax errors to distinguish them
            h = hashlib.sha256(sample.encode()).hexdigest()
        else:
            h = hashlib.sha256(normalized.encode()).hexdigest()
        
        clusters[h] = clusters.get(h, 0) + 1
    return clusters

def compute_shannon_entropy(cluster_counts: Dict[str, int]) -> float:
    """
    Compute Shannon entropy from cluster counts.
    H = - sum(p * log2(p))
    """
    total = sum(cluster_counts.values())
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in cluster_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * (p.bit_length() * (3.321928094887362) / p) # Approx log2
            # More precise:
            import math
            entropy -= p * math.log2(p)
    return entropy

def log_exclusions(exclusions: List[Dict[str, Any]], output_path: str):
    """
    Log exclusion reasons to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(exclusions, f, indent=2)

def process_entropy_for_dataset(
    input_path: str,
    output_path: str,
    exclusion_log_path: str,
    model_name: str = None,
    n_samples: int = 10,
    temperature: float = 0.7,
    top_p: float = 0.95,
    seed: int = 42
):
    """
    Main function to process a dataset (JSON/JSONL) and compute entropy for each problem.
    Expects input to be a list of dicts with 'task_id' and 'prompt' (or 'instruction').
    """
    set_global_seed(seed)
    
    # Load model
    model, tokenizer = load_model(model_name)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'train' in data:
        # Handle split structure if present, assume 'test' or 'train' key
        # For filtered_splits.json, it's likely a dict with 'train' and 'test' keys
        # We will process the 'test' set as per standard evaluation, or all if not specified
        # The task says "Load ... filtered_splits.json". Usually we evaluate on test.
        if 'test' in data:
            problems = data['test']
        elif 'train' in data:
            problems = data['train']
        else:
            problems = list(data.values())[0] if isinstance(data, dict) else data
    else:
        problems = data

    results = []
    exclusions = []

    logger.info(f"Processing {len(problems)} problems...")
    
    for i, problem in enumerate(problems):
        task_id = problem.get('task_id', f"task_{i}")
        prompt = problem.get('prompt') or problem.get('instruction') or problem.get('text', '')
        
        if not prompt:
            exclusions.append({'task_id': task_id, 'reason': 'No prompt found'})
            results.append({'task_id': task_id, 'entropy': None, 'exclusion_reason': 'No prompt'})
            continue

        try:
            samples = generate_samples(prompt, model, tokenizer, n_samples, temperature, top_p)
            clusters = cluster_samples(samples)
            entropy = compute_shannon_entropy(clusters)
            
            results.append({
                'task_id': task_id,
                'entropy': entropy,
                'exclusion_reason': None
            })
            
            if i % 10 == 0:
                logger.info(f"Processed {i}/{len(problems)}")
                
        except Exception as e:
            logger.error(f"Error processing {task_id}: {e}")
            exclusions.append({'task_id': task_id, 'reason': str(e)})
            results.append({'task_id': task_id, 'entropy': None, 'exclusion_reason': str(e)})

    # Save results
    logger.info(f"Saving results to {output_path}")
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    
    # Save exclusions
    if exclusions:
        log_exclusions(exclusions, exclusion_log_path)
        logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_path}")
    else:
        # Create empty file if no exclusions to satisfy file check
        with open(exclusion_log_path, 'w') as f:
            json.dump([], f)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract entropy from dataset")
    parser.add_argument('--input', type=str, required=True, help='Path to input JSON/JSONL file')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV file')
    parser.add_argument('--model', type=str, default=None, help='Model name (optional)')
    parser.add_argument('--n-samples', type=int, default=10, help='Number of samples per prompt')
    parser.add_argument('--temperature', type=float, default=0.7, help='Sampling temperature')
    parser.add_argument('--top-p', type=float, default=0.95, help='Top-p sampling')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    exclusion_log = str(Path(args.output).parent / "exclusion_log.json")
    
    process_entropy_for_dataset(
        input_path=args.input,
        output_path=args.output,
        exclusion_log_path=exclusion_log,
        model_name=args.model,
        n_samples=args.n_samples,
        temperature=args.temperature,
        top_p=args.top_p,
        seed=args.seed
    )
    logger.info("Entropy extraction completed.")

if __name__ == "__main__":
    main()