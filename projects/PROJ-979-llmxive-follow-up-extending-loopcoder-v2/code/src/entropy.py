"""
Entropy extraction module for llmXive project.

Implements semantic entropy calculation based on clustering of generated code samples.
Uses exact match, AST normalization, and execution-based comparison for clustering.
"""
import ast
import hashlib
import json
import logging
import os
import random
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import ensure_directories, fetch_dataset, stratified_sample
from scripts.execute import setup_execution_env, execute_code, validate_code_syntax

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXCLUSION_LOG_PATH = DATA_PROCESSED_DIR / "exclusion_log.json"
ENTROPY_RESULTS_PATH = DATA_PROCESSED_DIR / "entropy_results.csv"

# Configuration
NUM_SAMPLES = 10
MODEL_NAME = os.getenv("MODEL_NAME", "codellama/CodeLlama-1.3b-Instruct-hf")
MAX_GENERATION_LENGTH = 512
TEMPERATURE = 0.8
TOP_P = 0.95

# Ensure output directories exist
ensure_directories()

def normalize_ast(code_str: str) -> Optional[str]:
    """
    Normalize code by parsing AST and removing non-semantic elements.
    Returns a canonical string representation or None if parsing fails.
    """
    try:
        tree = ast.parse(code_str)
        # Remove docstrings and comments by filtering AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    node.value.value = ""
        
        # Convert back to string with consistent formatting
        # Using unparse if available (Python 3.9+), otherwise simple dump
        if hasattr(ast, 'unparse'):
            return ast.unparse(tree)
        else:
            # Fallback: simple AST dump for hashing (less robust but functional)
            return ast.dump(tree, annotate_fields=False)
    except SyntaxError:
        return None
    except Exception as e:
        logger.debug(f"AST normalization failed: {e}")
        return None

def execute_and_compare(code1: str, code2: str, test_input: str, expected_output: str, timeout: int = 5) -> bool:
    """
    Execute both code snippets and compare their outputs against expected result.
    Returns True if both produce the same correct output, False otherwise.
    """
    try:
        # Validate syntax first
        if not validate_code_syntax(code1) or not validate_code_syntax(code2):
            return False

        # Setup execution environment
        env = setup_execution_env()

        # Execute first code
        result1 = execute_code(code1, test_input, timeout=timeout)
        
        # Execute second code
        result2 = execute_code(code2, test_input, timeout=timeout)

        # Compare results
        # Normalize output strings for comparison
        out1 = str(result1).strip().lower()
        out2 = str(result2).strip().lower()
        expected = str(expected_output).strip().lower()

        # Both must match expected output to be considered equivalent
        return out1 == out2 == expected

    except Exception as e:
        logger.debug(f"Execution comparison failed: {e}")
        return False

def cluster_samples(samples: List[Dict[str, Any]], test_input: str, expected_output: str) -> Dict[int, List[int]]:
    """
    Cluster code samples using a hierarchical approach:
    1. Exact string match
    2. AST normalization match
    3. Execution-based equivalence (if both pass tests)
    
    Returns a dictionary mapping cluster_id -> list of sample indices
    """
    clusters: Dict[int, List[int]] = {}
    sample_to_cluster: Dict[int, int] = {}
    next_cluster_id = 0

    for i, sample in enumerate(samples):
        code = sample.get('code', '')
        if not code:
            continue

        # Step 1: Exact match check
        found_cluster = None
        for cluster_id, indices in clusters.items():
            if any(samples[idx]['code'] == code for idx in indices):
                found_cluster = cluster_id
                break

        if found_cluster is not None:
            clusters[found_cluster].append(i)
            sample_to_cluster[i] = found_cluster
            continue

        # Step 2: AST normalization check
        norm_code = normalize_ast(code)
        if norm_code:
            for cluster_id, indices in clusters.items():
                for idx in indices:
                    other_norm = normalize_ast(samples[idx]['code'])
                    if other_norm and other_norm == norm_code:
                        clusters[cluster_id].append(i)
                        sample_to_cluster[i] = cluster_id
                        found_cluster = cluster_id
                        break
                if found_cluster is not None:
                    break

        if found_cluster is not None:
            continue

        # Step 3: Execution-based equivalence
        # Only consider samples that pass the test
        try:
            result = execute_code(code, test_input, timeout=5)
            matches_test = str(result).strip().lower() == str(expected_output).strip().lower()
        except:
            matches_test = False

        if matches_test:
            # Check against other passing samples
            for cluster_id, indices in clusters.items():
                for idx in indices:
                    try:
                        other_result = execute_code(samples[idx]['code'], test_input, timeout=5)
                        other_matches = str(other_result).strip().lower() == str(expected_output).strip().lower()
                        if other_matches:
                            # They are both correct, consider them equivalent for entropy purposes
                            clusters[cluster_id].append(i)
                            sample_to_cluster[i] = cluster_id
                            found_cluster = cluster_id
                            break
                    except:
                        continue
                if found_cluster is not None:
                    break

        if found_cluster is None:
            # Create new cluster
            clusters[next_cluster_id] = [i]
            sample_to_cluster[i] = next_cluster_id
            next_cluster_id += 1

    return clusters

def compute_shannon_entropy(clusters: Dict[int, List[int]], total_samples: int) -> float:
    """
    Compute Shannon entropy over cluster probabilities.
    Handles zero entropy case by returning a small positive value.
    """
    if total_samples == 0:
        return 1e-9

    entropy = 0.0
    for cluster_id, indices in clusters.items():
        p = len(indices) / total_samples
        if p > 0:
            entropy -= p * (p if p == 0 else __import__('math').log2(p))
    
    # Handle zero entropy case
    if entropy == 0.0:
        return 1e-9
    
    return entropy

def load_model() -> Any:
    """
    Load the language model for generation.
    Returns the model and tokenizer.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        logger.info(f"Loading model: {MODEL_NAME}")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True
        )
        
        if device == "cpu":
            model = model.to(device)
        
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_samples(model: Any, tokenizer: Any, prompt: str, num_samples: int = NUM_SAMPLES) -> List[str]:
    """
    Generate multiple code samples from the model for a given prompt.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples = []
    
    for _ in range(num_samples):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=MAX_GENERATION_LENGTH,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract code block if present
        if "```python" in generated:
            start = generated.find("```python") + len("```python")
            end = generated.find("```", start)
            code = generated[start:end].strip()
        elif "```" in generated:
            start = generated.find("```") + len("```")
            end = generated.find("```", start)
            code = generated[start:end].strip()
        else:
            code = generated.strip()
        
        samples.append(code)
    
    return samples

def process_entropy_for_dataset(
    dataset: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Process a dataset to compute semantic entropy for each problem.
    """
    if output_path is None:
        output_path = ENTROPY_RESULTS_PATH
    
    results = []
    exclusion_count = 0
    total_count = len(dataset)

    logger.info(f"Processing {total_count} problems for entropy calculation")

    for idx, problem in enumerate(dataset):
        task_id = problem.get('task_id', f'unknown_{idx}')
        prompt = problem.get('prompt', '')
        test_input = problem.get('test_input', '')
        expected_output = problem.get('expected_output', '')

        if not prompt:
            logger.warning(f"Skipping {task_id}: no prompt")
            exclusion_count += 1
            continue

        try:
            logger.info(f"Processing {idx+1}/{total_count}: {task_id}")
            
            # Generate samples
            samples = generate_samples(model, tokenizer, prompt, NUM_SAMPLES)
            
            if not samples or all(not s.strip() for s in samples):
                logger.warning(f"No valid samples generated for {task_id}")
                exclusion_count += 1
                continue

            # Convert to dict format
            sample_dicts = [{'code': s} for s in samples]
            
            # Cluster samples
            clusters = cluster_samples(sample_dicts, test_input, expected_output)
            
            # Compute entropy
            entropy = compute_shannon_entropy(clusters, len(samples))
            
            results.append({
                'task_id': task_id,
                'entropy': entropy,
                'num_clusters': len(clusters),
                'samples_generated': len(samples),
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"Error processing {task_id}: {e}")
            exclusion_count += 1
            results.append({
                'task_id': task_id,
                'entropy': None,
                'num_clusters': 0,
                'samples_generated': 0,
                'status': 'error',
                'error': str(e)
            })

    # Log exclusions
    exclusion_rate = exclusion_count / total_count if total_count > 0 else 0
    exclusion_log = {
        'total_problems': total_count,
        'excluded_count': exclusion_count,
        'exclusion_rate': exclusion_rate,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(EXCLUSION_LOG_PATH, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    logger.info(f"Exclusion log saved to {EXCLUSION_LOG_PATH}")
    logger.info(f"Exclusion rate: {exclusion_rate:.2%}")

    # Save results to CSV
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Entropy results saved to {output_path}")
    
    return results

def main():
    """
    Main entry point for entropy extraction pipeline.
    """
    logger.info("Starting entropy extraction pipeline")
    
    # Load data
    try:
        # Fetch HumanEval dataset
        dataset = fetch_dataset('openai/human-eval', split='test')
        logger.info(f"Loaded {len(dataset)} problems from HumanEval")
        
        # Apply stratified sampling if needed
        sample_size = 50  # For CPU validation
        if len(dataset) > sample_size:
            dataset = stratified_sample(dataset, sample_size, strata_column='difficulty' if 'difficulty' in dataset[0] else 'task_id')
            logger.info(f"Applied stratified sampling: {len(dataset)} problems")
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return 1

    # Load model
    try:
        model, tokenizer = load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return 1

    # Process dataset
    results = process_entropy_for_dataset(dataset, model, tokenizer)

    logger.info(f"Entropy extraction completed. Processed {len(results)} problems.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
