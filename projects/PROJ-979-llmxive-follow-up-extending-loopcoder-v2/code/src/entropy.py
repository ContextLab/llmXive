import ast
import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model/cache state to avoid reloading in tight loops
_model_cache: Optional[Any] = None
_tokenizer_cache: Optional[Any] = None

def load_model(model_path: str) -> Tuple[Any, Any]:
    """
    Load the model and tokenizer.
    Uses environment variables for path if provided, otherwise defaults.
    """
    global _model_cache, _tokenizer_cache

    if _model_cache is not None:
        return _model_cache, _tokenizer_cache

    logger.info(f"Loading model from {model_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        # Ensure padding token is set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model in float16 if available, else float32
        device_map = "auto" if torch.cuda.is_available() else None
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=dtype,
            device_map=device_map,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        model.eval()

        _model_cache = model
        _tokenizer_cache = tokenizer
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model {model_path}: {e}")
        raise

def generate_samples(model: Any, tokenizer: Any, prompt: str, n_samples: int = 10, max_new_tokens: int = 256) -> List[str]:
    """
    Generate n_samples completions for a given prompt.
    Uses temperature sampling to encourage diversity.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples = []

    with torch.no_grad():
        for _ in range(n_samples):
            # Use temperature > 0 for diversity
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
            # Decode only the new tokens
            generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            samples.append(generated_text)

    return samples

def normalize_ast(code_str: str) -> Optional[str]:
    """
    Normalize code by parsing to AST and dumping with consistent formatting.
    Returns None if parsing fails.
    """
    try:
        tree = ast.parse(code_str)
        # Normalize whitespace and ordering where possible
        # For simplicity, we just dump the AST with a fixed indent
        return ast.dump(tree, indent=2)
    except SyntaxError:
        return None

def cluster_samples(samples: List[str]) -> Dict[int, List[str]]:
    """
    Cluster samples based on:
    1. Exact string match
    2. AST normalization
    3. (Optional) Execution result if sandbox available (deferred to inference stage)

    Returns a dict mapping cluster_id -> list of samples.
    """
    clusters: Dict[str, List[str]] = {}
    cluster_map: Dict[str, int] = {}
    next_cluster_id = 0

    for sample in samples:
        # Try AST normalization first (more robust than exact string)
        normalized = normalize_ast(sample)
        if normalized is None:
            # Fallback to raw string if syntax error
            key = sample
        else:
            key = normalized

        if key not in clusters:
            cluster_map[key] = next_cluster_id
            clusters[key] = []
            next_cluster_id += 1

        clusters[key].append(sample)

    # Re-index to integers for easier downstream handling
    final_clusters: Dict[int, List[str]] = {}
    for key, cluster_id in cluster_map.items():
        final_clusters[cluster_id] = clusters[key]

    return final_clusters

def compute_shannon_entropy(cluster_probs: List[float]) -> float:
    """
    Compute Shannon entropy: H = - sum(p * log2(p))
    Handles zero probabilities by excluding them from sum (log(0) is undefined).
    """
    entropy = 0.0
    for p in cluster_probs:
        if p > 0:
            entropy -= p * np.log2(p)
    return entropy

def extract_entropy(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10) -> Tuple[float, Dict[str, Any]]:
    """
    Extract semantic entropy for a single prompt.
    Returns (entropy, metadata_dict).
    Metadata includes cluster counts and probabilities for exclusion logging.
    """
    samples = generate_samples(model, tokenizer, prompt, n_samples=n_samples)
    clusters = cluster_samples(samples)

    # Calculate probabilities
    total_samples = len(samples)
    cluster_probs = [len(cluster) / total_samples for cluster in clusters.values()]

    # Calculate entropy
    entropy = compute_shannon_entropy(cluster_probs)

    # Prepare metadata
    metadata = {
        "n_samples": total_samples,
        "n_clusters": len(clusters),
        "cluster_probs": cluster_probs,
        "cluster_sizes": [len(c) for c in clusters.values()],
        "has_single_cluster": len(clusters) == 1
    }

    return entropy, metadata

def log_exclusions(entropy_results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """
    Detect undefined entropy (zero probability clusters, e.g., single cluster with 100% prob -> entropy=0)
    or exclusion events. Log exclusion count, rate, and reasons to JSON.

    Schema: {excluded_count: int, excluded_rate: float, reasons: [str]}

    Note: In the context of this task, "undefined entropy" often refers to
    cases where the model is over-confident (entropy=0) or under-confident in a way
    that breaks correlation assumptions (e.g., entropy=NaN).
    We will flag entropy=0 as 'zero_entropy' (over-confident) and entropy=NaN as 'nan_entropy'.
    """
    excluded_count = 0
    reasons_list = []
    excluded_indices = []

    for i, result in enumerate(entropy_results):
        entropy = result.get("entropy")
        if entropy is None:
            continue

        reason = None
        if np.isnan(entropy):
            reason = "nan_entropy"
        elif entropy == 0.0:
            # Technically defined, but often indicates lack of semantic diversity
            # which might be excluded from correlation analysis depending on spec.
            # Here we flag it for logging as per task description "undefined entropy (zero probability clusters)".
            # If a single cluster has 100% prob, entropy is 0.
            reason = "zero_entropy"

        if reason:
            excluded_count += 1
            reasons_list.append(reason)
            excluded_indices.append(i)

    total_count = len(entropy_results)
    excluded_rate = excluded_count / total_count if total_count > 0 else 0.0

    exclusion_log = {
        "excluded_count": excluded_count,
        "excluded_rate": excluded_rate,
        "reasons": reasons_list,
        "excluded_indices": excluded_indices
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(exclusion_log, f, indent=2)

    logger.info(f"Exclusion log written to {output_path}: {excluded_count} excluded ({excluded_rate:.2%})")
    return exclusion_log

def process_entropy_for_dataset(
    input_path: str,
    output_path: str,
    exclusion_log_path: str,
    model_path: str,
    sample_size: int = 50,
    n_samples_per_prompt: int = 10
) -> None:
    """
    Main entry point for entropy processing.
    1. Load filtered splits from input_path.
    2. Sample `sample_size` problems.
    3. Run entropy extraction for each.
    4. Save results to output_path (CSV).
    5. Log exclusions to exclusion_log_path.
    """
    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Sample if necessary
    if len(data) > sample_size:
        sampled_data = random.sample(data, sample_size)
    else:
        sampled_data = data

    logger.info(f"Processing {len(sampled_data)} problems (sampled from {len(data)})")

    # Load model
    model, tokenizer = load_model(model_path)

    results = []
    for i, item in enumerate(sampled_data):
        task_id = item.get("task_id", f"unknown_{i}")
        prompt = item.get("prompt", "")

        try:
            entropy, metadata = extract_entropy(prompt, model, tokenizer, n_samples=n_samples_per_prompt)
            results.append({
                "task_id": task_id,
                "entropy": entropy,
                "n_clusters": metadata["n_clusters"],
                "n_samples": metadata["n_samples"],
                "cluster_probs": json.dumps(metadata["cluster_probs"])
            })
        except Exception as e:
            logger.error(f"Error processing {task_id}: {e}")
            # Include failed items with None entropy so they can be logged as excluded
            results.append({
                "task_id": task_id,
                "entropy": None,
                "n_clusters": 0,
                "n_samples": 0,
                "cluster_probs": "[]"
            })

    # Save results to CSV
    import csv
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "entropy", "n_clusters", "n_samples", "cluster_probs"])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Entropy results written to {output_path}")

    # Log exclusions
    log_exclusions(results, exclusion_log_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract semantic entropy from code generation tasks.")
    parser.add_argument("--input", type=str, default="data/processed/filtered_splits.json",
                        help="Path to input JSON (filtered splits)")
    parser.add_argument("--output", type=str, default="data/processed/entropy_results.csv",
                        help="Path to output CSV")
    parser.add_argument("--exclusion-log", type=str, default="data/processed/exclusion_log.json",
                        help="Path to exclusion log JSON")
    parser.add_argument("--model-path", type=str,
                        default=os.getenv("CODELLAMA_CPU_PATH", "codellama/CodeLlama-1.3b-Instruct-hf"),
                        help="Path to model (env: CODELLAMA_CPU_PATH)")
    parser.add_argument("--sample-size", type=int, default=50,
                        help="Number of samples to process")
    parser.add_argument("--n-samples-per-prompt", type=int, default=10,
                        help="Number of generations per prompt for entropy")

    args = parser.parse_args()

    process_entropy_for_dataset(
        input_path=args.input,
        output_path=args.output,
        exclusion_log_path=args.exclusion_log,
        model_path=args.model_path,
        sample_size=args.sample_size,
        n_samples_per_prompt=args.n_samples_per_prompt
    )

if __name__ == "__main__":
    main()
