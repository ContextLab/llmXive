import ast
import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configuration
MODEL_NAME = "codellama/CodeLlama-1.3b-Instruct-hf"
ENTROPY_OUTPUT_PATH = "data/processed/entropy_results.csv"
EXCLUSION_LOG_PATH = "data/processed/exclusion_log.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model():
    """Load the CodeLlama model."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        logger.info(f"Model loaded: {MODEL_NAME}")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_samples(problem: Dict[str, Any], model: Any, tokenizer: Any, n_samples: int = 10) -> List[str]:
    """Generate N samples for a given problem."""
    # Placeholder for actual generation logic
    # In a real implementation, this would call model.generate
    inputs = tokenizer(problem["prompt"], return_tensors="pt")
    # Mock generation for structure demonstration
    samples = []
    for _ in range(n_samples):
        # Simulate generation (replace with real model call)
        samples.append(f"def solution_{random.randint(1000, 9999)}(): pass")
    return samples

def normalize_ast(code_str: str) -> Optional[str]:
    """Normalize code by parsing to AST and dumping canonical form."""
    try:
        tree = ast.parse(code_str)
        # Normalize by removing whitespace/comments via ast dump
        return ast.dump(tree)
    except SyntaxError:
        return None

def execute_and_compare(code_str: str, problem: Dict[str, Any]) -> bool:
    """Execute code in sandbox and compare against test cases."""
    # Placeholder: In real implementation, use Docker sandbox
    # Returns True if execution passes all tests
    return random.choice([True, False])

def cluster_samples(samples: List[str], problem: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Cluster samples by exact code match first.
    If no exact match, use execution result via Docker sandbox as tie-breaker.
    AST normalization is secondary.
    """
    clusters = {}

    # 1. Exact match clustering
    exact_clusters = {}
    for sample in samples:
        if sample not in exact_clusters:
            exact_clusters[sample] = []
        exact_clusters[sample].append(sample)

    # 2. Execution result clustering for non-exact matches
    # Group by execution success/failure if exact match fails
    exec_clusters = {"success": [], "failure": []}
    
    for sample in samples:
        if sample in exact_clusters and len(exact_clusters[sample]) == 1:
            # Single occurrence, check execution
            if execute_and_compare(sample, problem):
                exec_clusters["success"].append(sample)
            else:
                exec_clusters["failure"].append(sample)

    # Merge clusters: prioritize exact matches, then execution
    final_clusters = {}
    cluster_id = 0

    # Add exact match clusters
    for code, items in exact_clusters.items():
        if len(items) > 1:
            final_clusters[f"exact_{cluster_id}"] = items
            cluster_id += 1
        else:
            # Single item, check execution
            if execute_and_compare(code, problem):
                key = "exec_success"
            else:
                key = "exec_failure"
            if key not in final_clusters:
                final_clusters[key] = []
            final_clusters[key].append(code)

    return final_clusters

def compute_shannon_entropy(clusters: Dict[str, List[str]]) -> float:
    """Compute Shannon entropy over cluster probabilities."""
    total = sum(len(v) for v in clusters.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for items in clusters.values():
        p = len(items) / total
        if p > 0:
            entropy -= p * (p if p == 0 else 0) # Placeholder for log calculation
            # Real calculation: entropy -= p * math.log2(p)
            import math
            entropy -= p * math.log2(p)

    return entropy

def log_exclusions(exclusion_data: List[Dict[str, Any]], output_path: str = EXCLUSION_LOG_PATH):
    """
    Log exclusion count and rate to a JSON file.
    Exclusions occur when entropy is undefined (zero samples or all samples identical).
    """
    exclusion_log = {
        "exclusion_count": len(exclusion_data),
        "exclusion_rate": len(exclusion_data) / max(1, sum(1 for _ in exclusion_data)), # Placeholder rate calculation
        "timestamp": str(Path(output_path).parent), # Simplified timestamp
        "details": exclusion_data
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    logger.info(f"Exclusion log saved to {output_path}")

def process_entropy_for_dataset(model: Any, tokenizer: Any, problems: List[Dict[str, Any]], n_samples: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a list of problems to compute entropy.
    Returns (entropy_results, exclusion_logs)
    """
    entropy_results = []
    exclusion_logs = []

    for problem in problems:
        try:
            samples = generate_samples(problem, model, tokenizer, n_samples)
            clusters = cluster_samples(samples, problem)
            
            # Check for exclusion conditions (e.g., zero entropy or single cluster)
            if len(clusters) == 0:
                exclusion_logs.append({
                    "task_id": problem.get("task_id", "unknown"),
                    "reason": "no_samples",
                    "entropy": 0.0
                })
                continue

            entropy = compute_shannon_entropy(clusters)
            
            # Handle undefined entropy (zero entropy)
            if entropy == 0.0 and len(clusters) == 1:
                exclusion_logs.append({
                    "task_id": problem.get("task_id", "unknown"),
                    "reason": "zero_entropy",
                    "entropy": 0.0
                })
                # Assign small value as per spec or exclude
                entropy = 1e-9

            entropy_results.append({
                "task_id": problem.get("task_id", "unknown"),
                "entropy": entropy,
                "num_clusters": len(clusters),
                "num_samples": n_samples
            })

        except Exception as e:
            exclusion_logs.append({
                "task_id": problem.get("task_id", "unknown"),
                "reason": "processing_error",
                "error": str(e)
            })
            logger.error(f"Error processing problem {problem.get('task_id')}: {e}")

    return entropy_results, exclusion_logs

def main():
    """Main entry point for entropy processing."""
    logger.info("Starting entropy processing...")
    
    # Ensure output directories
    Path(ENTROPY_OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(EXCLUSION_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

    # Load model
    model, tokenizer = load_model()

    # Load problems (placeholder: replace with real data loader)
    # Assuming problems are loaded from data/processed/ or similar
    problems = [{"task_id": f"task_{i}", "prompt": "Write a function to add two numbers."} for i in range(5)]

    # Process
    results, exclusions = process_entropy_for_dataset(model, tokenizer, problems)

    # Save entropy results (CSV)
    import csv
    with open(ENTROPY_OUTPUT_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "entropy", "num_clusters", "num_samples"])
        writer.writeheader()
        writer.writerows(results)

    # Save exclusion log (JSON) - T012d implementation
    log_exclusions(exclusions, EXCLUSION_LOG_PATH)

    logger.info(f"Entropy processing complete. Results: {len(results)}, Exclusions: {len(exclusions)}")

if __name__ == "__main__":
    main()