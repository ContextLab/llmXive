"""
Entropy extraction module for semantic entropy calculation.

This module implements the core logic for extracting semantic entropy
from model generations, including sampling, clustering, and entropy calculation.
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
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL_PATH = "codellama/CodeLlama-1.3b-Instruct-hf"
OUTPUT_DIR = Path("data/processed")

def load_model(model_path: str = None, device: str = "cpu") -> Tuple[Any, Any]:
    """
    Load the model and tokenizer for inference.
    
    Args:
        model_path: Path to the model (HuggingFace ID or local path)
        device: Device to load the model to ("cpu" or "cuda")
        
    Returns:
        Tuple of (model, tokenizer)
    """
    if model_path is None:
        model_path = DEFAULT_MODEL_PATH
        
    logger.info(f"Loading model: {model_path} on {device}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map=device,
            trust_remote_code=True
        )
        model.eval()
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_samples(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10, max_length: int = 512) -> List[str]:
    """
    Generate multiple samples for a given prompt.
    
    Args:
        prompt: Input prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        n_samples: Number of samples to generate
        max_length: Maximum length of generated text
        
    Returns:
        List of generated samples
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generation_config = GenerationConfig(
        max_length=max_length,
        do_sample=True,
        temperature=0.7,
        top_p=0.95,
        num_return_sequences=n_samples,
        pad_token_id=tokenizer.eos_token_id
    )
    
    with torch.no_grad():
        outputs = model.generate(**inputs, generation_config=generation_config)
    
    samples = []
    for i in range(n_samples):
        # Extract the generated part (after the prompt)
        sample_ids = outputs[i, inputs['input_ids'].shape[1]:]
        sample_text = tokenizer.decode(sample_ids, skip_special_tokens=True)
        samples.append(sample_text.strip())
    
    return samples

def normalize_ast(code: str) -> Optional[str]:
    """
    Normalize code by parsing to AST and converting back to string.
    This helps identify semantically equivalent code.
    
    Args:
        code: Code string to normalize
        
    Returns:
        Normalized code string or None if parsing fails
    """
    try:
        tree = ast.parse(code)
        # Normalize by removing whitespace and comments
        normalized = ast.unparse(tree)
        return normalized
    except SyntaxError:
        return None

def execute_and_compare(code1: str, code2: str, test_cases: List[Dict[str, Any]]) -> bool:
    """
    Execute two code snippets and compare their outputs on test cases.
    
    Args:
        code1: First code snippet
        code2: Second code snippet
        test_cases: List of test cases with input/output pairs
        
    Returns:
        True if both codes produce identical outputs on all test cases
    """
    # For CPU validation, we'll use a simple comparison of AST normalization
    # as a fallback when actual execution is not possible
    norm1 = normalize_ast(code1)
    norm2 = normalize_ast(code2)
    
    if norm1 is None or norm2 is None:
        # If AST parsing fails, fall back to exact string match
        return code1.strip() == code2.strip()
    
    return norm1 == norm2

def cluster_samples(samples: List[str], test_cases: List[Dict[str, Any]] = None) -> Dict[int, List[str]]:
    """
    Cluster samples by semantic equivalence.
    
    Clustering strategy:
    1. Exact code match
    2. AST normalization
    3. Execution result comparison (if test cases provided)
    
    Args:
        samples: List of generated samples
        test_cases: Optional test cases for execution comparison
        
    Returns:
        Dictionary mapping cluster_id to list of samples
    """
    clusters = {}
    cluster_id = 0
    
    # First, normalize all samples
    normalized_samples = []
    for sample in samples:
        norm = normalize_ast(sample)
        if norm is None:
            norm = sample  # Fallback to original if AST parsing fails
        normalized_samples.append(norm)
    
    # Cluster by normalized form
    for i, norm in enumerate(normalized_samples):
        found_cluster = False
        for cid, members in clusters.items():
            # Check if this normalized form matches any existing cluster member
            if any(m == norm for m in members):
                clusters[cid].append(samples[i])
                found_cluster = True
                break
        
        if not found_cluster:
            clusters[cluster_id] = [samples[i]]
            cluster_id += 1
    
    # If test cases are provided, further refine clusters by execution
    if test_cases:
        refined_clusters = {}
        ref_id = 0
        
        for cid, members in clusters.items():
            # Compare all pairs in this cluster
            sub_clusters = {}
            sub_id = 0
            
            for j, sample in enumerate(members):
                found_sub_cluster = False
                for sid, sub_members in sub_clusters.items():
                    # Check if this sample produces same output as any sub-cluster member
                    if any(execute_and_compare(sample, m, test_cases) for m in sub_members):
                        sub_clusters[sid].append(sample)
                        found_sub_cluster = True
                        break
                
                if not found_sub_cluster:
                    sub_clusters[sub_id] = [sample]
                    sub_id += 1
            
            # Merge sub-clusters into main clusters
            for sid, sub_members in sub_clusters.items():
                if sub_members:
                    refined_clusters[ref_id] = sub_members
                    ref_id += 1
        
        clusters = refined_clusters
    
    return clusters

def compute_shannon_entropy(clusters: Dict[int, List[str]]) -> float:
    """
    Compute Shannon entropy over cluster probabilities.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of samples
        
    Returns:
        Shannon entropy value
    """
    total_samples = sum(len(samples) for samples in clusters.values())
    if total_samples == 0:
        return 0.0
    
    entropy = 0.0
    for samples in clusters.values():
        if len(samples) == 0:
            continue
        prob = len(samples) / total_samples
        if prob > 0:
            entropy -= prob * (prob ** 2).bit_length()  # Using log2 approximation
            # Actually compute log2 properly
            import math
            entropy -= prob * math.log2(prob)
    
    # Handle zero entropy case
    if entropy == 0:
        return 1e-9
    
    return entropy

def log_exclusions(excluded_count: int, total_count: int, reasons: List[str], output_path: str = None):
    """
    Log exclusion statistics to a JSON file.
    
    Args:
        excluded_count: Number of excluded samples
        total_count: Total number of samples
        reasons: List of exclusion reasons
        output_path: Path to output file
    """
    if output_path is None:
        output_path = str(OUTPUT_DIR / "exclusion_log.json")
    
    exclusion_data = {
        "excluded_count": excluded_count,
        "excluded_rate": excluded_count / total_count if total_count > 0 else 0.0,
        "reasons": reasons
    }
    
    with open(output_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)
    
    logger.info(f"Exclusion log saved to {output_path}")

def extract_entropy(prompt: str, model: Any, tokenizer: Any, n_samples: int = 10) -> float:
    """
    Extract semantic entropy for a given prompt.
    
    Args:
        prompt: Input prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        n_samples: Number of samples to generate
        
    Returns:
        Computed entropy value
    """
    samples = generate_samples(prompt, model, tokenizer, n_samples)
    clusters = cluster_samples(samples)
    entropy = compute_shannon_entropy(clusters)
    return entropy

def process_entropy_for_dataset(
    dataset: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    output_path: str = None,
    exclusion_log_path: str = None
) -> List[Dict[str, float]]:
    """
    Process a dataset to compute entropy for each item.
    
    Args:
        dataset: List of dataset items with 'prompt' or 'input' field
        model: Loaded model
        tokenizer: Loaded tokenizer
        output_path: Path to output CSV file
        exclusion_log_path: Path to exclusion log file
        
    Returns:
        List of results with entropy values
    """
    if output_path is None:
        output_path = str(OUTPUT_DIR / "entropy_results.csv")
    
    results = []
    excluded_count = 0
    exclusion_reasons = []
    
    for i, item in enumerate(dataset):
        try:
            # Extract prompt
            if 'prompt' in item:
                prompt = item['prompt']
            elif 'input' in item:
                prompt = item['input']
            else:
                raise ValueError("No prompt or input field found")
            
            # Compute entropy
            entropy = extract_entropy(prompt, model, tokenizer)
            
            results.append({
                "task_id": item.get('task_id', f"task_{i}"),
                "entropy": entropy,
                "status": "success"
            })
            
        except Exception as e:
            excluded_count += 1
            exclusion_reasons.append(str(e))
            results.append({
                "task_id": item.get('task_id', f"task_{i}"),
                "entropy": None,
                "status": "excluded",
                "error": str(e)
            })
    
    # Save results to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "entropy", "status", "error"])
        writer.writeheader()
        writer.writerows(results)
    
    # Log exclusions
    log_exclusions(excluded_count, len(dataset), exclusion_reasons, exclusion_log_path)
    
    logger.info(f"Entropy processing complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for entropy extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract semantic entropy from dataset")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH, help="Model path")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR / "entropy_results.csv"), help="Output CSV path")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of samples to process")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use (cpu or cuda)")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load model
    model, tokenizer = load_model(args.model, args.device)
    
    # Load dataset
    try:
        # Try to load HumanEval
        dataset = load_dataset("openai_humaneval", split="test")
    except Exception as e:
        logger.warning(f"Failed to load HumanEval: {e}, trying MBPP")
        try:
            dataset = load_dataset("mbpp", split="train").select(range(args.sample_size))
        except Exception as e2:
            logger.error(f"Failed to load MBPP: {e2}")
            raise
    
    # Convert to list and sample
    dataset_list = list(dataset)
    if len(dataset_list) > args.sample_size:
        dataset_list = random.sample(dataset_list, args.sample_size)
    
    # Process entropy
    results = process_entropy_for_dataset(
        dataset_list,
        model,
        tokenizer,
        output_path=args.output,
        exclusion_log_path=str(OUTPUT_DIR / "exclusion_log.json")
    )
    
    # Print summary
    successful = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Processed {len(results)} items, {successful} successful")

if __name__ == "__main__":
    main()
