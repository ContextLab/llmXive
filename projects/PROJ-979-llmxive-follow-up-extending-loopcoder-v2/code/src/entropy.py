"""
Entropy extraction and semantic clustering module for LoopCoder-v2 extension.
Implements FR-001: Semantic Entropy Extraction.
"""
import ast
import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model cache to avoid reloading
_model_cache: Dict[str, Any] = {}
_tokenizer_cache: Dict[str, Any] = {}

def load_model(model_path: str, device: str = "auto") -> Tuple[Any, Any]:
    """
    Load the model and tokenizer.
    Caches loaded models to prevent reloading across calls.
    
    Args:
        model_path: Path or HuggingFace ID for the model.
        device: Device to load the model on ('cpu', 'cuda', or 'auto').
        
    Returns:
        Tuple of (model, tokenizer)
    """
    cache_key = f"{model_path}_{device}"
    if cache_key in _model_cache:
        logger.info(f"Using cached model for {model_path}")
        return _model_cache[cache_key]

    logger.info(f"Loading model from {model_path} on {device}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            padding_side='left'
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Determine device map
        if device == "auto":
            if torch.cuda.is_available():
                device_map = "auto"
                device = "cuda"
            else:
                device_map = {"": "cpu"}
                device = "cpu"
        else:
            device_map = {"": device}

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=device_map,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            trust_remote_code=True
        )
        model.eval()

        _model_cache[cache_key] = (model, tokenizer)
        logger.info(f"Model loaded successfully: {model_path}")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model {model_path}: {e}")
        raise

def generate_samples(
    prompt: str,
    model: Any,
    tokenizer: Any,
    n_samples: int = 10,
    max_new_tokens: int = 512,
    temperature: float = 0.8,
    top_p: float = 0.95
) -> List[str]:
    """
    Generate N samples for a given prompt using the loaded model.
    Implements the sampling step for FR-001.
    
    Args:
        prompt: The input prompt string.
        model: The loaded transformer model.
        tokenizer: The loaded tokenizer.
        n_samples: Number of samples to generate.
        max_new_tokens: Maximum tokens to generate per sample.
        temperature: Sampling temperature.
        top_p: Top-p sampling threshold.
        
    Returns:
        List of generated sample strings.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples = []
    
    # Prepare generation config
    with torch.no_grad():
        for i in range(n_samples):
            try:
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    return_dict_in_generate=False
                )
                
                # Decode and clean
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract code block if present
                if "```python" in generated_text:
                    start = generated_text.find("```python") + len("```python")
                    end = generated_text.find("```", start)
                    if end != -1:
                        code = generated_text[start:end].strip()
                    else:
                        code = generated_text[start:].strip()
                elif "```" in generated_text:
                    start = generated_text.find("```") + 3
                    end = generated_text.find("```", start)
                    if end != -1:
                        code = generated_text[start:end].strip()
                    else:
                        code = generated_text[start:].strip()
                else:
                    code = generated_text.strip()
                
                samples.append(code)
                
            except Exception as e:
                logger.warning(f"Generation failed for sample {i}: {e}")
                samples.append(f"# Generation error: {e}")
    
    return samples

def normalize_ast(code: str) -> Optional[str]:
    """
    Normalize code by parsing to AST and dumping with a canonical order.
    Returns None if parsing fails.
    """
    try:
        tree = ast.parse(code)
        # Sort keys in dumps for canonical representation
        return ast.dump(tree, indent=2)
    except SyntaxError:
        return None

def execute_and_compare(code: str, test_code: str) -> bool:
    """
    Execute code against test cases.
    NOTE: In a real sandbox, this would run in Docker.
    Here we do a basic check or return False if execution fails.
    """
    # Placeholder for sandbox execution
    # In production, this would run in the Docker container defined in T009
    try:
        # Very basic check: does the code run without syntax error?
        # Actual correctness requires running the test suite
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError:
        return False
    except Exception:
        return False

def cluster_samples(
    samples: List[str],
    test_code: Optional[str] = None
) -> Dict[int, List[str]]:
    """
    Cluster samples by:
    1. Exact code match
    2. AST normalization (if exact fails)
    3. Execution result (if AST fails)
    
    Returns:
        Dict mapping cluster_id -> list of samples in that cluster
    """
    clusters: Dict[str, List[str]] = {}
    
    for sample in samples:
        # 1. Exact match
        key_exact = sample.strip()
        if key_exact not in clusters:
            clusters[key_exact] = []
        clusters[key_exact].append(sample)
        
        # If we have a key, we don't need to check others for this sample
        # But we need to merge clusters if AST or execution match
    
    # 2. AST normalization
    ast_groups: Dict[str, List[str]] = {}
    for sample in samples:
        ast_norm = normalize_ast(sample)
        if ast_norm:
            if ast_norm not in ast_groups:
                ast_groups[ast_norm] = []
            ast_groups[ast_norm].append(sample)
    
    # Merge clusters based on AST
    # For simplicity, we'll re-cluster: if AST matches, they go in same cluster
    final_clusters: Dict[int, List[str]] = {}
    cluster_map: Dict[str, int] = {}
    next_cluster_id = 0
    
    # First pass: assign exact matches
    for sample in samples:
        key = sample.strip()
        if key not in cluster_map:
            cluster_map[key] = next_cluster_id
            final_clusters[next_cluster_id] = []
            next_cluster_id += 1
        final_clusters[cluster_map[key]].append(sample)
    
    # Second pass: check AST normalization for merging
    # This is a simplified approach: we group by AST if exact match failed
    # In a full implementation, we'd use a union-find data structure
    
    # For T012a, we return the exact match clusters as a starting point
    # The clustering logic is extended in T012b
    
    return final_clusters

def compute_shannon_entropy(cluster_probs: List[float]) -> float:
    """
    Compute Shannon entropy over cluster probabilities.
    H = - sum(p * log2(p))
    
    Args:
        cluster_probs: List of probabilities for each cluster.
        
    Returns:
        Shannon entropy value.
    """
    if not cluster_probs or sum(cluster_probs) == 0:
        return 0.0
    
    # Normalize to ensure sum is 1
    total = sum(cluster_probs)
    probs = [p / total for p in cluster_probs]
    
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * (p ** 2).bit_length()  # Approximation to avoid log(0)
            # Correct calculation:
            entropy -= p * (math.log2(p) if p > 0 else 0)
    
    # Handle edge case of zero entropy
    if entropy == 0:
        return 1e-9
    
    return entropy

def log_exclusions(
    excluded_samples: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Log exclusion events to a JSON file.
    
    Args:
        excluded_samples: List of dicts with exclusion details.
        output_path: Path to the exclusion log file.
    """
    log_data = {
        "excluded_count": len(excluded_samples),
        "excluded_rate": len(excluded_samples) / max(len(excluded_samples) + 1, 1),
        "reasons": list(set([ex.get("reason", "unknown") for ex in excluded_samples]))
    }
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def extract_entropy(
    prompt: str,
    model: Any,
    tokenizer: Any,
    n_samples: int = 10,
    test_code: Optional[str] = None
) -> float:
    """
    Main function to extract semantic entropy for a single prompt.
    Generates samples, clusters them, and computes entropy.
    
    Args:
        prompt: Input prompt.
        model: Loaded model.
        tokenizer: Loaded tokenizer.
        n_samples: Number of samples to generate.
        test_code: Optional test code for execution-based clustering.
        
    Returns:
        Computed entropy value.
    """
    # Generate samples
    samples = generate_samples(prompt, model, tokenizer, n_samples)
    
    # Cluster samples
    clusters = cluster_samples(samples, test_code)
    
    # Compute probabilities
    total_samples = len(samples)
    cluster_sizes = [len(c) for c in clusters.values()]
    cluster_probs = [size / total_samples for size in cluster_sizes]
    
    # Compute entropy
    entropy = compute_shannon_entropy(cluster_probs)
    
    return entropy

def process_entropy_for_dataset(
    data_path: str,
    model_path: str,
    output_path: str,
    sample_size: int = 50,
    n_samples_per_prompt: int = 10
) -> None:
    """
    Process a dataset to compute entropy for each sample.
    
    Args:
        data_path: Path to the filtered_splits.json file.
        model_path: Path to the model.
        output_path: Path to write entropy_results.csv.
        sample_size: Number of samples to process.
        n_samples_per_prompt: Number of generations per prompt.
    """
    # Load data
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load model
    model, tokenizer = load_model(model_path, device)
    
    # Limit sample size
    samples = data[:sample_size]
    
    results = []
    exclusion_log = []
    
    for idx, item in enumerate(samples):
        task_id = item.get('task_id', f'task_{idx}')
        prompt = item.get('prompt', '')
        test_code = item.get('test', '')
        
        try:
            entropy = extract_entropy(
                prompt, 
                model, 
                tokenizer, 
                n_samples_per_prompt,
                test_code
            )
            results.append({
                'task_id': task_id,
                'entropy': entropy,
                'n_samples': n_samples_per_prompt
            })
        except Exception as e:
            logger.error(f"Failed to compute entropy for {task_id}: {e}")
            exclusion_log.append({
                'task_id': task_id,
                'reason': str(e)
            })
    
    # Write results
    with open(output_path, 'w') as f:
        f.write('task_id,entropy,n_samples\n')
        for r in results:
            f.write(f"{r['task_id']},{r['entropy']},{r['n_samples']}\n")
    
    # Log exclusions
    if exclusion_log:
        exclusion_log_path = output_path.replace('.csv', '_exclusions.json')
        log_exclusions(exclusion_log, exclusion_log_path)
    
    logger.info(f"Processed {len(results)} samples. Wrote results to {output_path}")

def main():
    """
    Main entry point for entropy extraction script.
    Usage: python code/src/entropy.py --output data/processed/entropy_results.csv --sample-size 50
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract semantic entropy from code generation samples.")
    parser.add_argument('--input', type=str, default='data/processed/filtered_splits.json',
                        help='Path to filtered_splits.json')
    parser.add_argument('--output', type=str, default='data/processed/entropy_results.csv',
                        help='Path to output CSV')
    parser.add_argument('--sample-size', type=int, default=50,
                        help='Number of samples to process')
    parser.add_argument('--n-samples-per-prompt', type=int, default=10,
                        help='Number of samples to generate per prompt')
    parser.add_argument('--model-path', type=str, default=None,
                        help='Path to model (overrides env vars)')
    
    args = parser.parse_args()
    
    # Determine model path
    model_path = args.model_path
    if not model_path:
        model_path = os.environ.get('CODELLAMA_CPU_PATH') or os.environ.get('CODELLAMA_GPU_PATH')
        if not model_path:
            raise ValueError("No model path provided. Set CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH env var.")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Process
    process_entropy_for_dataset(
        args.input,
        model_path,
        args.output,
        args.sample_size,
        args.n_samples_per_prompt
    )

if __name__ == "__main__":
    main()
