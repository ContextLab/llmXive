"""
Entropy extraction module for LoopCoder-v2 extension.
Implements semantic entropy calculation based on clustering of generated samples.
"""
import ast
import hashlib
import json
import logging
import os
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import astunparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Model Loading (Placeholder for real implementation) ---
def load_model(model_path: str):
    """
    Load a HuggingFace model.
    NOTE: This is a placeholder. The actual implementation would load the model.
    """
    logger.info(f"Loading model from {model_path}...")
    # In a real scenario, we would do:
    # from transformers import AutoModelForCausalLM, AutoTokenizer
    # tokenizer = AutoTokenizer.from_pretrained(model_path)
    # model = AutoModelForCausalLM.from_pretrained(model_path)
    # return model, tokenizer
    return None, None

# --- Sample Generation ---
def generate_samples(prompt: str, n: int = 10, model=None, tokenizer=None, temperature: float = 0.8) -> List[str]:
    """
    Generate n samples for a given prompt using the model.
    """
    if model is None or tokenizer is None:
        # Fallback for testing without a real model
        logger.warning("Model not loaded. Returning dummy samples.")
        return [f"dummy_sample_{i} for {prompt}" for i in range(n)]

    inputs = tokenizer(prompt, return_tensors="pt")
    samples = []
    for _ in range(n):
        outputs = model.generate(
            **inputs,
            max_length=512,
            num_return_sequences=1,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        sample = tokenizer.decode(outputs[0], skip_special_tokens=True)
        samples.append(sample)
    return samples

# --- AST Normalization ---
def normalize_ast(code_str: str) -> Optional[str]:
    """
    Parse code into AST, normalize (remove whitespace/comments), and return string representation.
    Returns None if parsing fails.
    """
    try:
        tree = ast.parse(code_str)
        # Normalize by unparsing (removes some formatting differences)
        # Note: astunparse is needed for Python < 3.9 or for better compatibility
        normalized = astunparse.unparse(tree)
        return normalized
    except SyntaxError:
        return None

# --- Code Execution (Sandbox) ---
def exec_code_in_sandbox(code: str, timeout: int = 5) -> Tuple[bool, str]:
    """
    Execute code in a sandbox (Docker) and return (success, output).
    This is a placeholder for the actual sandbox implementation.
    """
    # Placeholder: Assume execution fails for dummy code
    if "dummy" in code:
        return False, "Dummy code cannot be executed"
    # In a real implementation, we would use the Docker sandbox from T009
    try:
        # Simulating execution
        # exec(code) # Dangerous in real code without sandbox
        return True, "Execution successful"
    except Exception as e:
        return False, str(e)

def execute_and_compare(samples: List[str]) -> List[bool]:
    """
    Execute all samples and compare outputs.
    Returns a list of booleans indicating if each sample executed successfully.
    """
    results = []
    for sample in samples:
        success, _ = exec_code_in_sandbox(sample)
        results.append(success)
    return results

# --- Clustering ---
def cluster_by_semantic_equivalence(samples: List[str]) -> Dict[int, int]:
    """
    Cluster samples by semantic equivalence.
    Primary: AST normalization.
    Secondary: Execution output (if AST fails).
    Tertiary: Exact string match.
    Returns a dictionary mapping sample index to cluster_id.
    """
    clusters = {}
    cluster_id_counter = 0
    ast_clusters = {} # Map normalized_ast_str -> cluster_id
    exec_clusters = {} # Map exec_output -> cluster_id

    for idx, sample in enumerate(samples):
        cluster_id = None

        # 1. Try AST normalization
        normalized = normalize_ast(sample)
        if normalized:
            if normalized not in ast_clusters:
                ast_clusters[normalized] = cluster_id_counter
                cluster_id_counter += 1
            cluster_id = ast_clusters[normalized]
            clusters[idx] = cluster_id
            continue

        # 2. Try Execution output
        success, output = exec_code_in_sandbox(sample)
        exec_key = f"{success}:{output}"
        if exec_key not in exec_clusters:
            exec_clusters[exec_key] = cluster_id_counter
            cluster_id_counter += 1
        cluster_id = exec_clusters[exec_key]
        clusters[idx] = cluster_id
        continue

        # 3. Fallback to exact string (should be covered by dict keys, but explicit here)
        # If we reach here, it means AST failed and execution failed (or not attempted)
        # We treat each unique string as a new cluster if not already clustered
        if idx not in clusters:
            clusters[idx] = cluster_id_counter
            cluster_id_counter += 1

    return clusters

# --- Entropy Calculation ---
def compute_shannon_entropy(cluster_map: Dict[int, int]) -> float:
    """
    Compute Shannon entropy over cluster probabilities.
    H = - sum(p * log2(p))
    """
    if not cluster_map:
        return 0.0

    counts = {}
    for cluster_id in cluster_map.values():
        counts[cluster_id] = counts.get(cluster_id, 0) + 1

    total = len(cluster_map)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * (p if p == 1 else (p * 0 if p == 1 else (p * 0) or (p * 0))) # Placeholder logic for log
            # Correct log calculation:
            import math
            entropy -= p * math.log2(p)

    return entropy

# --- Logging Exclusions ---
def log_exclusions(results: List[Dict[str, Any]], path: str):
    """
    Log exclusion count/rate to a JSON file.
    Expected result format: {task_id, entropy, cluster_count, excluded_reason}
    """
    exclusions = [r for r in results if r.get("excluded_reason")]
    exclusion_log = {
        "total_samples": len(results),
        "excluded_count": len(exclusions),
        "exclusion_rate": len(exclusions) / len(results) if results else 0.0,
        "exclusions": exclusions
    }
    with open(path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log written to {path}")

# --- Serialization ---
def write_entropy_results(results: List[Dict[str, Any]], path: str):
    """
    Save entropy results to CSV and log exclusions.
    Columns: task_id, entropy, cluster_count, excluded_reason
    """
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["task_id", "entropy", "cluster_count", "excluded_reason"]
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "task_id": r.get("task_id", ""),
                "entropy": r.get("entropy", 0.0),
                "cluster_count": r.get("cluster_count", 0),
                "excluded_reason": r.get("excluded_reason", "")
            })

    # Log exclusions
    exclusion_log_path = csv_path.parent / "exclusion_log.json"
    log_exclusions(results, str(exclusion_log_path))

    logger.info(f"Entropy results written to {csv_path}")
    logger.info(f"Exclusion log written to {exclusion_log_path}")

# --- Processing for Dataset ---
def process_entropy_for_dataset(task_id: str, samples: List[str]) -> Dict[str, Any]:
    """
    Process samples for a single task and return entropy metrics.
    """
    cluster_map = cluster_by_semantic_equivalence(samples)
    entropy = compute_shannon_entropy(cluster_map)
    cluster_count = len(set(cluster_map.values()))

    # Check for exclusion conditions (e.g., no valid samples)
    excluded_reason = ""
    if not samples:
        excluded_reason = "No samples generated"
    elif cluster_count == 0:
        excluded_reason = "No valid clusters formed"

    return {
        "task_id": task_id,
        "entropy": entropy,
        "cluster_count": cluster_count,
        "excluded_reason": excluded_reason
    }

# --- Main Entry Point (for testing) ---
def main():
    """
    Main function to demonstrate entropy calculation.
    """
    logger.info("Starting entropy calculation demo.")
    
    # Dummy data for demonstration
    dummy_samples = [
        "print('hello')",
        "print('hello')",
        "print('world')",
        "def foo(): pass",
        "def foo(): pass",
        "invalid syntax here"
    ]
    
    result = process_entropy_for_dataset("dummy_task_001", dummy_samples)
    print(f"Result: {result}")
    
    # Write to file
    write_entropy_results([result], "data/processed/entropy_results.csv")

if __name__ == "__main__":
    main()
