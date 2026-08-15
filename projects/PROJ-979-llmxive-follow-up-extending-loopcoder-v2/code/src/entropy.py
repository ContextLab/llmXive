"""
Entropy Extraction Pipeline for LoopCoder-v2 Extension.

This module implements the semantic entropy extraction pipeline.
It loads the model, generates samples, clusters them by AST structure,
executes code in a sandbox to verify functional equivalence, and computes
Shannon entropy.
"""

import ast
import hashlib
import json
import logging
import os
import random
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Import utils from sibling module
from utils import set_global_seed, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model and tokenizer instances (lazy loaded)
_model = None
_tokenizer = None

def load_model(config: Dict[str, Any]) -> Tuple[Any, Any]:
    """
    Load the CodeLlama model and tokenizer based on configuration.
    """
    global _model, _tokenizer
    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer

    model_path = config.get('CODELLAMA_CPU_PATH') or config.get('CODELLAMA_GPU_PATH')
    if not model_path or model_path == "NOT_SET":
        raise ValueError("Model path not configured. Set CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH.")

    logger.info(f"Loading model from {model_path}...")
    try:
        _tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        # Force padding side to right for generation
        _tokenizer.padding_side = 'right'
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token

        device = 'cuda' if torch.cuda.is_available() and config.get('USE_GPU', False) else 'cpu'
        logger.info(f"Using device: {device}")

        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == 'cuda' else torch.float32,
            device_map='auto' if device == 'cuda' else None,
            trust_remote_code=True
        )
        if device == 'cpu':
            _model = _model.to(device)

        logger.info("Model loaded successfully.")
        return _model, _tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_samples(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10, max_length: int = 512) -> List[str]:
    """
    Generate n_samples completions for a given prompt.
    """
    inputs = tokenizer(prompt, return_tensors='pt').to(model.device)
    generated_ids = []

    # Generate with different seeds for diversity if needed, or use temperature
    # For entropy estimation, we need diverse samples, so we use temperature sampling
    for i in range(n_samples):
        # Set seed for reproducibility if global seed is set, but we want variation
        # We'll use the model's internal sampling with temperature
        output = model.generate(
            **inputs,
            max_new_tokens=max_length,
            do_sample=True,
            temperature=0.8,
            top_p=0.95,
            pad_token_id=tokenizer.pad_token_id,
            num_return_sequences=1
        )
        # Decode only the new tokens
        generated_text = tokenizer.decode(output[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        generated_ids.append(generated_text)

    return generated_ids

def normalize_ast(code_str: str) -> Optional[str]:
    """
    Normalize code to AST hash for clustering.
    Returns None if code is not valid Python.
    """
    try:
        tree = ast.parse(code_str)
        # Normalize: remove constant values and comments, keep structure
        # We'll use a simple approach: dump the AST with specific attributes
        # A more robust way is to traverse and build a normalized representation
        normalized = []
        for node in ast.walk(tree):
            node_type = node.__class__.__name__
            # We only care about structure, not literals
            normalized.append(node_type)
        # Create a hash of the structure
        structure_str = " ".join(normalized)
        return hashlib.sha256(structure_str.encode()).hexdigest()
    except SyntaxError:
        return None

def execute_code_in_sandbox(code_str: str, test_code: str, timeout: int = 10) -> bool:
    """
    Execute code in a Docker sandbox and return True if it passes the tests.
    This is a simplified version; in production, use the Dockerfile.unseen sandbox.
    """
    try:
        # Create a temporary directory for the execution
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = os.path.join(tmpdir, "solution.py")
            test_file = os.path.join(tmpdir, "test.py")

            with open(code_file, "w") as f:
                f.write(code_str)

            with open(test_file, "w") as f:
                f.write(test_code)

            # Run the test using subprocess (simplified, assumes local Python)
            # In production, this should be wrapped in Docker
            result = subprocess.run(
                ["python", test_file],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        logger.warning(f"Execution error: {e}")
        return False

def cluster_samples(samples: List[str], test_code: str = None) -> Dict[str, List[int]]:
    """
    Cluster samples by AST structure and optionally by execution results on unseen tests.
    Returns a dict mapping cluster_id (hash) to list of sample indices.
    """
    clusters = {}
    ast_hashes = []

    for i, sample in enumerate(samples):
        ast_hash = normalize_ast(sample)
        if ast_hash is None:
            # Invalid syntax, treat as unique cluster or exclude
            ast_hash = f"invalid_{i}"
        
        # If test_code is provided, also group by execution pattern
        if test_code:
            passed = execute_code_in_sandbox(sample, test_code)
            ast_hash = f"{ast_hash}_pass" if passed else f"{ast_hash}_fail"

        if ast_hash not in clusters:
            clusters[ast_hash] = []
        clusters[ast_hash].append(i)
        ast_hashes.append(ast_hash)

    return clusters

def compute_shannon_entropy(cluster_counts: List[int]) -> float:
    """
    Compute Shannon entropy from cluster counts.
    H = - sum(p_i * log2(p_i))
    """
    total = sum(cluster_counts)
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in cluster_counts:
        if count > 0:
            p = count / total
            entropy -= p * (p.bit_length() - 1)  # Approx log2
            # Use math.log2 for precision
            import math
            entropy -= p * math.log2(p)
    
    return entropy

def load_filtered_splits(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the filtered splits JSON file.
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    return data

def log_exclusions(exclusions: List[Dict[str, Any]], log_path: str):
    """
    Log exclusion events to a JSON file.
    """
    with open(log_path, 'a') as f:
        for exc in exclusions:
            f.write(json.dumps(exc) + '\n')

def process_entropy_for_dataset(task_id: str, entropy: float) -> Dict[str, Any]:
    """
    Process entropy result for CSV output.
    """
    return {
        'task_id': task_id,
        'entropy': entropy,
        'exclusion_reason': None
    }

def extract_entropy(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10, test_code: str = None) -> float:
    """
    Extract semantic entropy for a single prompt.
    """
    samples = generate_samples(prompt, model, tokenizer, n_samples)
    clusters = cluster_samples(samples, test_code)
    
    cluster_counts = [len(indices) for indices in clusters.values()]
    entropy = compute_shannon_entropy(cluster_counts)
    
    # Handle undefined entropy (zero entropy) by assigning a small value
    if entropy == 0.0:
        entropy = 1e-9
    
    return entropy

def main(input_path: str, output_path: str, sample_size: Optional[int] = None):
    """
    Main function to run the entropy extraction pipeline.
    """
    # Load configuration
    config = load_config()
    
    # Set global seed for reproducibility
    set_global_seed(42)
    
    # Load model
    model, tokenizer = load_model(config)
    
    # Load input data
    logger.info(f"Loading input data from {input_path}...")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    input_data = load_filtered_splits(input_path)
    
    # If sample_size is specified, limit the data
    if sample_size is not None:
        input_data = input_data[:sample_size]
        logger.info(f"Using sample size: {sample_size}")
    
    # Prepare output
    results = []
    exclusions = []
    
    # Process each input
    for idx, item in enumerate(input_data):
        task_id = item.get('task_id', f'task_{idx}')
        prompt = item.get('prompt', '')
        test_code = item.get('test', None)  # Use test code if available for functional equivalence
        
        logger.info(f"Processing {task_id} ({idx+1}/{len(input_data)})...")
        
        try:
            entropy = extract_entropy(prompt, model, tokenizer, n_samples=10, test_code=test_code)
            result = process_entropy_for_dataset(task_id, entropy)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {task_id}: {e}")
            exclusions.append({
                'task_id': task_id,
                'reason': str(e)
            })
    
    # Log exclusions
    if exclusions:
        exclusion_log_path = str(Path(output_path).parent / 'exclusion_log.json')
        log_exclusions(exclusions, exclusion_log_path)
        logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_path}")
    
    # Write results to CSV
    logger.info(f"Writing results to {output_path}...")
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Entropy extraction complete. {len(results)} results written.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Entropy Extraction Pipeline')
    parser.add_argument('--input', type=str, required=True, help='Path to filtered splits JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV')
    parser.add_argument('--sample-size', type=int, default=None, help='Sample size for validation')
    
    args = parser.parse_args()
    main(args.input, args.output, args.sample_size)
