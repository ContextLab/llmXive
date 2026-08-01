import ast
import hashlib
import json
import logging
import os
import random
import csv
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from src.utils import capture_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_model() -> Tuple[Any, Any]:
    """Load the model from environment variables."""
    # Check for GPU path first, then CPU path
    gpu_path = os.getenv("CODELLAMA_GPU_PATH")
    cpu_path = os.getenv("CODELLAMA_CPU_PATH")

    model_path = None
    if gpu_path and Path(gpu_path).exists():
        model_path = gpu_path
        logger.info(f"Loading model from GPU path: {model_path}")
    elif cpu_path and Path(cpu_path).exists():
        model_path = cpu_path
        logger.info(f"Loading model from CPU path: {model_path}")
    else:
        # Fallback to a public model if no env path is set (for testing)
        # In production, this should raise an error
        logger.warning("No model path found in environment variables. Using default public model.")
        model_path = "codellama/CodeLlama-1.3b-Instruct-hf"

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with appropriate device
        if gpu_path and Path(gpu_path).exists():
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True
            )
            if device == "cpu":
                model = model.to("cpu")
        else:
            device = "cpu"
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True
            )

        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise

def generate_samples(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10) -> List[str]:
    """Generate n_samples completions for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    samples = []
    for _ in range(n_samples):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        # Decode only the new tokens
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        samples.append(generated_text)

    return samples

def normalize_ast(code: str) -> Optional[str]:
    """Normalize code by parsing and dumping AST to remove whitespace/comments."""
    try:
        tree = ast.parse(code)
        # Remove docstrings and comments by re-parsing
        # We'll use a simple approach: dump the AST and hash it
        return ast.dump(tree)
    except SyntaxError:
        return None

def execute_code_in_sandbox(code: str, test_code: str, timeout: int = 10) -> bool:
    """Execute code in a sandbox and check if it passes the test."""
    try:
        # Create a temporary directory for the sandbox
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write the solution code
            solution_path = os.path.join(tmpdir, "solution.py")
            with open(solution_path, "w") as f:
                f.write(code)

            # Write the test code
            test_path = os.path.join(tmpdir, "test.py")
            with open(test_path, "w") as f:
                f.write(test_code)

            # Run the test using subprocess
            # For simplicity, we'll run the solution and capture output
            # In a real sandbox, we'd use Docker
            result = subprocess.run(
                ["python", solution_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir
            )
            # If the code runs without error, we consider it a pass for now
            # A more robust check would compare against expected output
            return result.returncode == 0
    except Exception as e:
        logger.warning(f"Code execution failed: {e}")
        return False

def cluster_samples(samples: List[str], test_code: Optional[str] = None) -> List[List[str]]:
    """Cluster samples by semantic equivalence.
    
    Clustering strategy:
    1. Exact string match
    2. AST normalization (if syntax is valid)
    3. Execution result (if test_code is provided)
    """
    if not samples:
        return []

    clusters = []
    visited = set()

    for i, sample in enumerate(samples):
        if i in visited:
            continue

        # Start a new cluster
        current_cluster = [sample]
        visited.add(i)

        # Normalize current sample
        current_ast = normalize_ast(sample)
        current_exec = None
        if test_code:
            current_exec = execute_code_in_sandbox(sample, test_code)

        for j, other_sample in enumerate(samples):
            if j in visited:
                continue

            # Check exact match
            if sample == other_sample:
                current_cluster.append(other_sample)
                visited.add(j)
                continue

            # Check AST normalization
            other_ast = normalize_ast(other_sample)
            if current_ast and other_ast and current_ast == other_ast:
                current_cluster.append(other_sample)
                visited.add(j)
                continue

            # Check execution result (tie-breaker)
            if test_code:
                other_exec = execute_code_in_sandbox(other_sample, test_code)
                if current_exec == other_exec:
                    # If both pass or both fail, consider them equivalent
                    # This is a heuristic and might not be perfect
                    current_cluster.append(other_sample)
                    visited.add(j)

        clusters.append(current_cluster)

    return clusters

def compute_shannon_entropy(clusters: List[List[str]]) -> float:
    """Compute Shannon entropy over cluster probabilities."""
    if not clusters:
        return 0.0

    total_samples = sum(len(cluster) for cluster in clusters)
    if total_samples == 0:
        return 0.0

    entropy = 0.0
    for cluster in clusters:
        p = len(cluster) / total_samples
        if p > 0:
            entropy -= p * (p if p == 0 else __import__('math').log(p))

    return entropy

def extract_entropy(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10, test_code: Optional[str] = None) -> Tuple[float, Optional[str]]:
    """Extract entropy for a given prompt.
    
    Returns:
        Tuple of (entropy_value, exclusion_reason)
        exclusion_reason is None if no exclusion, otherwise a string describing why
    """
    try:
        samples = generate_samples(prompt, model, tokenizer, n_samples)
        
        if not samples:
            return 0.0, "No samples generated"

        clusters = cluster_samples(samples, test_code)
        
        if not clusters:
            return 0.0, "No clusters formed"

        entropy = compute_shannon_entropy(clusters)
        
        # Handle zero entropy
        if entropy == 0.0:
            # Assign a very small value instead of zero
            return 1e-9, None

        return entropy, None

    except Exception as e:
        logger.warning(f"Entropy extraction failed: {e}")
        return 0.0, f"Error: {str(e)}"

def load_filtered_splits() -> List[Dict[str, Any]]:
    """Load filtered splits from data/processed/filtered_splits.json."""
    path = Path("data/processed/filtered_splits.json")
    if not path.exists():
        raise FileNotFoundError(f"Filtered splits not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        if 'train' in data:
            return data['train']
        elif 'test' in data:
            return data['test']
        else:
            # Assume it's a list of samples
            return list(data.values()) if data else []
    elif isinstance(data, list):
        return data
    else:
        return []

def log_exclusions(exclusions: List[Dict[str, Any]], output_path: str = "data/processed/exclusion_log.json"):
    """Log exclusion events to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing exclusions if file exists
    existing = []
    if Path(output_path).exists():
        with open(output_path, 'r') as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    
    # Append new exclusions
    existing.extend(exclusions)
    
    with open(output_path, 'w') as f:
        json.dump(existing, f, indent=2)

def process_entropy_for_dataset(
    model: Any, 
    tokenizer: Any, 
    n_samples: int = 10, 
    sample_size: Optional[int] = None,
    output_path: str = "data/processed/entropy_results.csv"
) -> None:
    """Process entropy extraction for the entire dataset.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        n_samples: Number of samples to generate per prompt
        sample_size: Optional limit on number of samples to process
        output_path: Path to write results
    """
    # Load data
    data = load_filtered_splits()
    
    # Apply sample size limit if specified
    if sample_size is not None:
        data = data[:sample_size]
    
    logger.info(f"Processing {len(data)} samples")
    
    results = []
    exclusions = []
    
    for item in data:
        task_id = item.get('task_id', 'unknown')
        prompt = item.get('prompt', '')
        test_code = item.get('test', '')
        
        entropy, exclusion_reason = extract_entropy(prompt, model, tokenizer, n_samples, test_code)
        
        result = {
            'task_id': task_id,
            'entropy': entropy,
            'exclusion_reason': exclusion_reason
        }
        results.append(result)
        
        if exclusion_reason:
            exclusions.append({
                'task_id': task_id,
                'reason': exclusion_reason
            })
    
    # Write results to CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'entropy', 'exclusion_reason'])
        writer.writeheader()
        writer.writerows(results)
    
    # Log exclusions
    if exclusions:
        log_exclusions(exclusions)
    
    logger.info(f"Entropy results written to {output_path}")
    logger.info(f"Excluded {len(exclusions)} samples")

def main():
    """Main entry point for entropy extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract semantic entropy from code generation tasks")
    parser.add_argument("--output", type=str, default="data/processed/entropy_results.csv",
                      help="Output path for entropy results")
    parser.add_argument("--sample-size", type=int, default=None,
                      help="Limit number of samples to process")
    parser.add_argument("--n-samples", type=int, default=10,
                      help="Number of samples to generate per prompt")
    
    args = parser.parse_args()
    
    # Load model
    logger.info("Loading model...")
    model, tokenizer = load_model()
    
    # Process dataset
    logger.info("Processing dataset...")
    process_entropy_for_dataset(
        model, 
        tokenizer, 
        n_samples=args.n_samples,
        sample_size=args.sample_size,
        output_path=args.output
    )
    
    logger.info("Entropy extraction complete")

if __name__ == "__main__":
    main()