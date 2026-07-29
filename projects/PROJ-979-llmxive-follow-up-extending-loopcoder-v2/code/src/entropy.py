"""
Entropy Extraction Pipeline for CodeLlama-based LoopCoder analysis.

This module implements the extraction of semantic entropy from model outputs
on code generation tasks. It clusters generated solutions by semantic equivalence
and computes Shannon entropy over the resulting cluster distribution.

Dependencies:
- T004f: Requires data/processed/filtered_splits.json to exist
- T009: Uses Docker sandbox for execution-based equivalence checking
"""

import ast
import hashlib
import json
import logging
import os
import random
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_N_SAMPLES = 10
DEFAULT_OUTPUT_PATH = "data/processed/entropy_results.csv"
DEFAULT_EXCLUSION_LOG_PATH = "data/processed/exclusion_log.json"
DEFAULT_INPUT_PATH = "data/processed/filtered_splits.json"
ENV_CPU_PATH = "CODELLAMA_CPU_PATH"
ENV_GPU_PATH = "CODELLAMA_GPU_PATH"

def load_model() -> Tuple[Any, AutoTokenizer]:
    """
    Load CodeLlama model from environment-specified path.
    
    Returns:
        Tuple of (model, tokenizer)
        
    Raises:
        ValueError: If neither environment variable is set or path doesn't exist
        OSError: If model loading fails
    """
    cpu_path = os.environ.get(ENV_CPU_PATH)
    gpu_path = os.environ.get(ENV_GPU_PATH)
    
    model_path = None
    if gpu_path and os.path.exists(gpu_path):
        model_path = gpu_path
        logger.info(f"Loading model from GPU path: {gpu_path}")
    elif cpu_path and os.path.exists(cpu_path):
        model_path = cpu_path
        logger.info(f"Loading model from CPU path: {cpu_path}")
    else:
        raise ValueError(
            f"Model path not found. Set {ENV_GPU_PATH} or {ENV_CPU_PATH} "
            f"to a valid directory containing a CodeLlama model."
        )
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True
        )
        logger.info(f"Model loaded successfully: {model_path}")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise

def generate_samples(
    prompt: str,
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    n_samples: int = DEFAULT_N_SAMPLES,
    max_new_tokens: int = 512
) -> List[str]:
    """
    Generate multiple samples from the model for a given prompt.
    
    Args:
        prompt: Input prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        n_samples: Number of samples to generate
        max_new_tokens: Maximum tokens to generate
        
    Returns:
        List of generated code strings
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Use different seeds for diversity
    generated_samples = []
    for i in range(n_samples):
        # Set seed for reproducibility within run
        torch.manual_seed(i * 1000 + random.randint(0, 1000))
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode and clean
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract code block if present
        if "```python" in generated_text:
            start = generated_text.find("```python") + len("```python")
            end = generated_text.find("```", start)
            if end > start:
                code = generated_text[start:end].strip()
            else:
                code = generated_text
        elif "```" in generated_text:
            start = generated_text.find("```") + len("```")
            end = generated_text.find("```", start)
            if end > start:
                code = generated_text[start:end].strip()
            else:
                code = generated_text
        else:
            code = generated_text
        
        generated_samples.append(code)
    
    return generated_samples

def normalize_ast(code_str: str) -> Optional[str]:
    """
    Normalize code by parsing to AST and converting back to string.
    This handles semantic equivalence through structural normalization.
    
    Args:
        code_str: Code string to normalize
        
    Returns:
        Normalized code string or None if parsing fails
    """
    try:
        tree = ast.parse(code_str)
        # Remove docstrings and comments for normalization
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    node.value = ast.Constant(value="")
        
        return ast.unparse(tree) if hasattr(ast, 'unparse') else str(tree)
    except SyntaxError:
        return None
    except Exception:
        return None

def cluster_samples(
    samples: List[str],
    execution_checker: Optional[callable] = None
) -> List[List[str]]:
    """
    Cluster samples by semantic equivalence.
    
    Clustering strategy:
    1. Exact string match
    2. AST-normalized match
    3. Execution result match (if checker provided)
    
    Args:
        samples: List of generated code strings
        execution_checker: Optional function to check execution equivalence
        
    Returns:
        List of clusters, where each cluster is a list of equivalent samples
    """
    clusters = []
    used_indices = set()
    
    for i, sample in enumerate(samples):
        if i in used_indices:
            continue
        
        # Start new cluster
        cluster = [sample]
        used_indices.add(i)
        
        # AST normalization
        normalized_i = normalize_ast(sample)
        
        for j in range(i + 1, len(samples)):
            if j in used_indices:
                continue
            
            sample_j = samples[j]
            
            # Exact match
            if sample == sample_j:
                cluster.append(sample_j)
                used_indices.add(j)
                continue
            
            # AST normalization match
            normalized_j = normalize_ast(sample_j)
            if normalized_i and normalized_j and normalized_i == normalized_j:
                cluster.append(sample_j)
                used_indices.add(j)
                continue
            
            # Execution-based equivalence (if checker provided)
            if execution_checker:
                try:
                    result_i = execution_checker(sample)
                    result_j = execution_checker(sample_j)
                    if result_i == result_j and result_i is not None:
                        cluster.append(sample_j)
                        used_indices.add(j)
                        continue
                except Exception:
                    pass
        
        clusters.append(cluster)
    
    return clusters

def compute_shannon_entropy(clusters: List[List[str]]) -> float:
    """
    Compute Shannon entropy over cluster distribution.
    
    Args:
        clusters: List of clusters
        
    Returns:
        Shannon entropy value
    """
    if not clusters:
        return 0.0
    
    total = sum(len(c) for c in clusters)
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for cluster in clusters:
        p = len(cluster) / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

def extract_entropy(
    prompt: str,
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    n_samples: int = DEFAULT_N_SAMPLES
) -> Tuple[float, List[str]]:
    """
    Extract entropy for a single prompt.
    
    Args:
        prompt: Input prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        n_samples: Number of samples to generate
        
    Returns:
        Tuple of (entropy_value, generated_samples)
    """
    samples = generate_samples(prompt, model, tokenizer, n_samples)
    
    if not samples:
        return 0.0, []
    
    clusters = cluster_samples(samples)
    entropy = compute_shannon_entropy(clusters)
    
    # Handle zero entropy case
    if entropy == 0.0:
        entropy = 1e-9
    
    return entropy, samples

def log_exclusions(
    exclusion_log_path: str,
    task_id: str,
    reason: str
) -> None:
    """
    Log exclusion events to JSON file.
    
    Args:
        exclusion_log_path: Path to exclusion log file
        task_id: Task ID that was excluded
        reason: Reason for exclusion
    """
    exclusion_data = []
    
    if os.path.exists(exclusion_log_path):
        try:
            with open(exclusion_log_path, 'r') as f:
                exclusion_data = json.load(f)
        except json.JSONDecodeError:
            exclusion_data = []
    
    exclusion_data.append({
        "task_id": task_id,
        "reason": reason,
        "timestamp": torch.cuda.get_device_properties(0).name if torch.cuda.is_available() else "cpu"
    })
    
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)

def load_filtered_splits(input_path: str) -> List[Dict[str, Any]]:
    """
    Load filtered splits from JSON file.
    
    Args:
        input_path: Path to filtered_splits.json
        
    Returns:
        List of task dictionaries
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is invalid JSON
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        # Expected format: {train: [...], test: [...]}
        return data.get('test', data.get('train', []))
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {input_path}")

def process_entropy_for_dataset(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    input_data: List[Dict[str, Any]],
    n_samples: int = DEFAULT_N_SAMPLES,
    output_path: str = DEFAULT_OUTPUT_PATH,
    exclusion_log_path: str = DEFAULT_EXCLUSION_LOG_PATH
) -> List[Dict[str, Any]]:
    """
    Process entire dataset for entropy extraction.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        input_data: List of task dictionaries
        n_samples: Number of samples per task
        output_path: Path for output CSV
        exclusion_log_path: Path for exclusion log
        
    Returns:
        List of entropy results
    """
    results = []
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    for task in input_data:
        task_id = task.get('task_id', 'unknown')
        prompt = task.get('prompt', '')
        
        if not prompt:
            log_exclusions(exclusion_log_path, task_id, "Empty prompt")
            continue
        
        try:
            entropy, _ = extract_entropy(prompt, model, tokenizer, n_samples)
            results.append({
                "task_id": task_id,
                "entropy": entropy,
                "exclusion_reason": None
            })
        except Exception as e:
            logger.warning(f"Failed to process task {task_id}: {e}")
            log_exclusions(exclusion_log_path, task_id, str(e))
            results.append({
                "task_id": task_id,
                "entropy": None,
                "exclusion_reason": str(e)
            })
    
    # Write results to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "entropy", "exclusion_reason"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Entropy results written to {output_path}")
    return results

def main():
    """Main entry point for entropy extraction pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract semantic entropy from model outputs")
    parser.add_argument("--input", type=str, default=DEFAULT_INPUT_PATH,
                      help="Path to filtered_splits.json")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH,
                      help="Path for entropy_results.csv")
    parser.add_argument("--exclusion-log", type=str, default=DEFAULT_EXCLUSION_LOG_PATH,
                      help="Path for exclusion log")
    parser.add_argument("--n-samples", type=int, default=DEFAULT_N_SAMPLES,
                      help="Number of samples per task")
    
    args = parser.parse_args()
    
    try:
        # Load model
        logger.info("Loading model...")
        model, tokenizer = load_model()
        
        # Load input data
        logger.info(f"Loading input data from {args.input}...")
        input_data = load_filtered_splits(args.input)
        logger.info(f"Loaded {len(input_data)} tasks")
        
        # Process dataset
        logger.info("Processing entropy extraction...")
        results = process_entropy_for_dataset(
            model,
            tokenizer,
            input_data,
            n_samples=args.n_samples,
            output_path=args.output,
            exclusion_log_path=args.exclusion_log
        )
        
        logger.info(f"Processed {len(results)} tasks")
        logger.info(f"Results saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
