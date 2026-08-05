import ast
import hashlib
import json
import logging
import os
import random
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "strata_threshold": 50,
            "entropy_n_samples": 10,
            "non_inferiority_delta": 0.02,
            "convergence_k_range": [1, 2, 3]
        }
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_model(config: Dict[str, Any], mode: str = "cpu") -> Tuple[Any, Any]:
    """
    Load CodeLlama model based on environment variables.
    mode: 'cpu' uses CODELLAMA_CPU_PATH, 'gpu' uses CODELLAMA_GPU_PATH
    """
    if mode == "cpu":
        model_path = os.environ.get("CODELLAMA_CPU_PATH")
    else:
        model_path = os.environ.get("CODELLAMA_GPU_PATH")

    if not model_path:
        # Fallback to a known public model if env vars are missing (for testing only)
        # In production, this should raise an error
        logger.warning("Model path not set in environment. Using default public model.")
        model_path = "codellama/CodeLlama-7b-Instruct-hf"

    logger.info(f"Loading model from: {model_path}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        device = torch.device("cuda" if torch.cuda.is_available() and mode == "gpu" else "cpu")
        logger.info(f"Using device: {device}")

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            device_map="auto" if device.type == "cuda" else None,
            trust_remote_code=True
        )
        if device.type == "cpu":
            model = model.to(device)

        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_samples(
    prompt: str,
    model: Any,
    tokenizer: Any,
    n_samples: int,
    max_new_tokens: int = 256
) -> List[str]:
    """Generate N samples for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generated_samples = []

    for _ in range(n_samples):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        # Decode and strip prompt
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the generated part (after the prompt)
        if prompt in generated_text:
            generated_part = generated_text.split(prompt, 1)[1].strip()
        else:
            generated_part = generated_text.strip()
        generated_samples.append(generated_part)

    return generated_samples

def normalize_ast(code: str) -> Optional[str]:
    """Normalize code by parsing and dumping AST to canonical form."""
    try:
        tree = ast.parse(code)
        # Canonical dump: sort keys, remove whitespace variations
        return ast.dump(tree, indent=None)
    except SyntaxError:
        return None

def execute_code_in_sandbox(code: str, test_case: str) -> Tuple[bool, str]:
    """
    Execute code in a sandbox and return (is_correct, output).
    Note: This is a simplified version. In production, use Docker.
    For this implementation, we simulate execution by checking if code is valid Python.
    """
    try:
        # Simple syntax check
        ast.parse(code)
        # In a real sandbox, we would run the code against test_case
        # Here we return True if syntax is valid (placeholder for real execution)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

def cluster_samples(samples: List[str], test_case: str) -> Dict[str, List[str]]:
    """
    Cluster samples by semantic equivalence using priority:
    1. Exact code match
    2. AST normalization
    3. Execution result (simulated here)
    """
    clusters = {}

    # Priority 1: Exact match
    for sample in samples:
        if sample not in clusters:
            clusters[sample] = []
        clusters[sample].append(sample)

    # If only exact matches, we're done (AST and execution are for tie-breaking if needed)
    # For entropy calculation, we treat exact matches as one cluster
    # AST normalization would merge syntactically different but semantically same code
    # Execution would merge code that produces same output

    # Implement AST normalization clustering
    ast_clusters = {}
    for sample in samples:
        ast_norm = normalize_ast(sample)
        if ast_norm is None:
            # Invalid code, keep as is
            key = f"invalid_{hashlib.md5(sample.encode()).hexdigest()}"
        else:
            key = ast_norm

        if key not in ast_clusters:
            ast_clusters[key] = []
        ast_clusters[key].append(sample)

    # For entropy, we use the AST-normalized clusters
    # This is more robust than exact matches
    return ast_clusters

def compute_shannon_entropy(clusters: Dict[str, List[str]]) -> float:
    """Compute Shannon entropy over cluster probabilities."""
    total = sum(len(samples) for samples in clusters.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for samples in clusters.values():
        p = len(samples) / total
        if p > 0:
            entropy -= p * (p if p == 0 else (p * 0).bit_length() or 0)  # Avoid log(0)
            # Proper log calculation
            import math
            entropy -= p * math.log2(p)

    return entropy

def load_filtered_splits(path: str = "data/processed/filtered_splits.json") -> List[Dict[str, Any]]:
    """Load filtered splits from JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Filtered splits not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def log_exclusions(exclusions: List[Dict[str, Any]], output_path: str = "data/processed/exclusion_log.json"):
    """Log exclusion events to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(exclusions, f, indent=2)

def process_entropy_for_dataset(
    data: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    n_samples: int = 10
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process entropy for each problem in the dataset.
    Returns (results, exclusions)
    """
    results = []
    exclusions = []

    for item in data:
        task_id = item.get('task_id', 'unknown')
        prompt = item.get('prompt', '')
        test = item.get('test', '')

        if not prompt:
            exclusions.append({
                'task_id': task_id,
                'reason': 'Empty prompt'
            })
            continue

        try:
            samples = generate_samples(prompt, model, tokenizer, n_samples)
            clusters = cluster_samples(samples, test)
            entropy = compute_shannon_entropy(clusters)

            # Handle undefined entropy (zero entropy)
            if entropy == 0.0 or entropy < 1e-9:
                entropy = 1e-9

            results.append({
                'task_id': task_id,
                'entropy': entropy,
                'exclusion_reason': None
            })
        except Exception as e:
            exclusions.append({
                'task_id': task_id,
                'reason': f'Processing error: {str(e)}'
            })
            logger.warning(f"Failed to process {task_id}: {e}")

    return results, exclusions

def extract_entropy(
    prompt: str,
    model: Any,
    n_samples: int = 10
) -> float:
    """
    Extract entropy for a single prompt.
    This is the core function used by the pipeline.
    """
    samples = generate_samples(prompt, model, n_samples)
    clusters = cluster_samples(samples, "")
    entropy = compute_shannon_entropy(clusters)
    if entropy == 0.0:
        entropy = 1e-9
    return entropy

def main(output_path: str = "data/processed/entropy_results.csv", sample_size: Optional[int] = None):
    """
    Main entry point for entropy extraction pipeline.
    Loads filtered splits, computes entropy for each, and saves results.
    """
    config = load_config()
    n_samples = config.get("entropy_n_samples", 10)
    if sample_size:
        n_samples = sample_size

    logger.info(f"Starting entropy extraction pipeline with {n_samples} samples per prompt")

    # Load model
    # Determine mode based on environment
    mode = "gpu" if os.environ.get("CODELLAMA_GPU_PATH") else "cpu"
    model, tokenizer = load_model(config, mode=mode)

    # Load filtered splits
    try:
        data = load_filtered_splits()
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        raise

    # Limit sample size if requested
    if sample_size and len(data) > sample_size:
        logger.info(f"Limiting dataset to {sample_size} samples")
        data = data[:sample_size]

    logger.info(f"Processing {len(data)} problems")

    # Process entropy
    results, exclusions = process_entropy_for_dataset(data, model, tokenizer, n_samples)

    # Log exclusions
    exclusion_path = "data/processed/exclusion_log.json"
    os.makedirs(os.path.dirname(exclusion_path), exist_ok=True)
    with open(exclusion_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_path}")

    # Save results to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'entropy', 'exclusion_reason'])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Entropy results saved to {output_path}")
    logger.info(f"Total processed: {len(results)}, Excluded: {len(exclusions)}")

    return results, exclusions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Entropy Extraction Pipeline")
    parser.add_argument("--output", type=str, default="data/processed/entropy_results.csv",
                      help="Output path for entropy results")
    parser.add_argument("--sample-size", type=int, default=None,
                      help="Limit dataset to N samples")
    args = parser.parse_args()

    main(output_path=args.output, sample_size=args.sample_size)
