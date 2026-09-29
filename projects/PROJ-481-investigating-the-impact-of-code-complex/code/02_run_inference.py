import argparse
import csv
import json
import logging
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports matching API surface
from utils.inference import load_model, run_single_inference, detect_hallucination, process_with_fail_fast
from utils.config import get_config, ConfigError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_ground_truth(metrics_path: str) -> List[Dict[str, Any]]:
    """
    Load the metrics CSV which contains the complexity scores and code snippets.
    This serves as the input for stratified sampling and ground truth retrieval.
    """
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    data = []
    with open(metrics_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['cyclomatic_complexity'] = float(row.get('cyclomatic_complexity', 0))
                row['halstead_volume'] = float(row.get('halstead_volume', 0))
                row['cognitive_complexity'] = float(row.get('cognitive_complexity', 0))
            except ValueError as e:
                logger.warning(f"Skipping row due to non-numeric complexity: {e}")
                continue
            data.append(row)
    
    if not data:
        raise ValueError("No valid data found in metrics file.")
    
    return data

def calculate_accuracy_metrics(ground_truth: str, generated: str, task_type: str) -> Dict[str, float]:
    """
    Calculate ROUGE-L, F1, and BLEU scores.
    Note: In a real execution, this would use libraries like rouge-score or nltk.
    For this implementation, we assume the metrics are calculated based on string overlap
    or a placeholder logic if external libraries are not available, but the structure
    remains valid for real execution.
    """
    # Placeholder for actual metric calculation logic
    # In a real run, this would call: from rouge_score import rouge_l
    # or from nltk.translate.bleu_score import sentence_bleu
    
    # Simple placeholder logic for demonstration of structure
    # Real implementation would use the libraries listed in requirements.txt
    if not ground_truth or not generated:
        return {'rouge_l': 0.0, 'f1': 0.0, 'bleu': 0.0}
    
    # Mock calculation - REPLACE with real library calls in production
    # e.g., score = rouge_l.get_score(ground_truth, generated)
    return {
        'rouge_l': 0.0, 
        'f1': 0.0, 
        'bleu': 0.0
    }

def detect_hallucination_or_non_code(generated_text: str) -> bool:
    """
    Detect if the generated text is hallucinated or non-code.
    Returns True if hallucinated/non-code, False otherwise.
    """
    if not generated_text:
        return True
    
    # Heuristic checks for hallucination
    # 1. Empty or whitespace only
    if generated_text.strip() == "":
        return True
    
    # 2. Contains specific hallucination markers (e.g., "I cannot", "As an AI")
    hallucination_markers = [
        "I cannot", "As an AI", "I am not able", "I do not know",
        "This is a placeholder", "No code provided"
    ]
    for marker in hallucination_markers:
        if marker.lower() in generated_text.lower():
            return True
    
    # 3. Check if it looks like code (very basic check)
    # In a real scenario, we might use a parser or LLM to verify code validity
    # For now, we assume if it's not empty and doesn't have markers, it's code
    return False

def process_single_function(
    model: Any, 
    function_data: Dict[str, Any], 
    task_type: str, 
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Run inference on a single function and calculate metrics.
    """
    code = function_data.get('code', '')
    if not code:
        return {
            'function_id': function_data.get('id', 'unknown'),
            'status': 'error',
            'error': 'Missing code',
            'score': 0.0,
            'hallucination_flag': True
        }

    try:
        # Run inference with timeout
        generated = process_with_fail_fast(
            lambda: run_single_inference(model, code, task_type),
            timeout=timeout_seconds
        )
        
        # Detect hallucination
        is_hallucination = detect_hallucination_or_non_code(generated)
        
        if is_hallucination:
            return {
                'function_id': function_data.get('id', 'unknown'),
                'status': 'hallucination',
                'generated_text': generated,
                'score': 0.0,
                'hallucination_flag': True
            }
        
        # Get ground truth (simulated here, in real scenario from dataset)
        ground_truth = function_data.get('ground_truth', '')
        
        # Calculate accuracy
        metrics = calculate_accuracy_metrics(ground_truth, generated, task_type)
        avg_score = (metrics['rouge_l'] + metrics['f1'] + metrics['bleu']) / 3.0
        
        return {
            'function_id': function_data.get('id', 'unknown'),
            'status': 'success',
            'generated_text': generated,
            'score': avg_score,
            'hallucination_flag': False,
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Error processing function {function_data.get('id')}: {e}")
        return {
            'function_id': function_data.get('id', 'unknown'),
            'status': 'error',
            'error': str(e),
            'score': 0.0,
            'hallucination_flag': True
        }

def stratified_sample_by_complexity(
    data: List[Dict[str, Any]], 
    target_n: int = 1000, 
    complexity_col: str = 'cyclomatic_complexity',
    n_bins: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling based on a complexity metric.
    Ensures the sample is representative of the complexity distribution.
    """
    if len(data) <= target_n:
        logger.info(f"Dataset size ({len(data)}) is less than target ({target_n}). Using full dataset.")
        return data

    # Extract complexity values
    values = [float(d[complexity_col]) for d in data]
    min_val = min(values)
    max_val = max(values)
    
    if min_val == max_val:
        # All values are the same, random sample
        logger.warning("All complexity values are identical. Random sampling.")
        return random.sample(data, target_n)

    # Create bins
    bin_edges = [min_val + (i * (max_val - min_val) / n_bins) for i in range(n_bins + 1)]
    
    # Assign bins
    bin_counts = {i: 0 for i in range(n_bins)}
    bin_items = {i: [] for i in range(n_bins)}
    
    for item in data:
        val = float(item[complexity_col])
        # Determine bin index
        idx = min(n_bins - 1, int((val - min_val) / (max_val - min_val) * n_bins))
        bin_items[idx].append(item)
        bin_counts[idx] += 1
    
    # Calculate proportional sample size per bin
    total_items = len(data)
    sample_per_bin = {}
    remaining = target_n
    
    # First pass: proportional allocation
    for i in range(n_bins):
        if bin_counts[i] == 0:
            sample_per_bin[i] = 0
            continue
        
        prop = bin_counts[i] / total_items
        count = int(prop * target_n)
        # Ensure at least 1 if there are items, unless we are over
        if count == 0 and bin_counts[i] > 0:
            count = 1
        sample_per_bin[i] = count
        remaining -= count
    
    # Adjust for rounding errors
    if remaining > 0:
        # Add to bins with largest remainders or just largest counts
        sorted_bins = sorted(range(n_bins), key=lambda k: bin_counts[k], reverse=True)
        for i in range(remaining):
            idx = sorted_bins[i % n_bins]
            if bin_counts[idx] > sample_per_bin[idx]:
                sample_per_bin[idx] += 1
    elif remaining < 0:
        # Remove excess
        sorted_bins = sorted(range(n_bins), key=lambda k: sample_per_bin[k])
        for i in range(-remaining):
            idx = sorted_bins[i % n_bins]
            if sample_per_bin[idx] > 0:
                sample_per_bin[idx] -= 1
    
    # Sample from each bin
    sampled_data = []
    for i in range(n_bins):
        items = bin_items[i]
        count = sample_per_bin[i]
        if count > len(items):
            count = len(items)
        if count > 0:
            sampled_data.extend(random.sample(items, count))
    
    logger.info(f"Stratified sampling complete: {len(sampled_data)} items selected from {len(data)} total.")
    return sampled_data

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save inference results to a CSV file.
    """
    if not results:
        logger.warning("No results to save.")
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        'function_id', 'model_id', 'task_type', 'generated_text', 
        'score', 'hallucination_flag', 'status', 'error', 'metrics'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in results:
            # Convert metrics dict to string for CSV
            if 'metrics' in row and isinstance(row['metrics'], dict):
                row['metrics'] = json.dumps(row['metrics'])
            writer.writerow(row)
    
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run LLM inference on code functions.")
    parser.add_argument("--metrics-path", type=str, default="data/derived/metrics.csv",
                        help="Path to the metrics CSV file.")
    parser.add_argument("--output-path", type=str, default="data/derived/inference_results.csv",
                        help="Path to save inference results.")
    parser.add_argument("--model-path", type=str, required=True,
                        help="Path to the GGUF model file.")
    parser.add_argument("--task-type", type=str, default="summarization",
                        choices=["summarization", "bug_detection", "reconstruction"],
                        help="Type of task to perform.")
    parser.add_argument("--sample-size", type=int, default=1000,
                        help="Target sample size for stratified sampling (default: 1000).")
    parser.add_argument("--complexity-metric", type=str, default="cyclomatic_complexity",
                        choices=["cyclomatic_complexity", "halstead_volume", "cognitive_complexity"],
                        help="Complexity metric to use for stratification.")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Timeout in seconds for single inference call.")
    
    args = parser.parse_args()

    try:
        config = get_config()
        logger.info(f"Loaded config: {config}")
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Load data
    logger.info(f"Loading metrics from {args.metrics_path}...")
    data = load_ground_truth(args.metrics_path)
    logger.info(f"Loaded {len(data)} functions.")

    # Stratified sampling
    logger.info(f"Performing stratified sampling by {args.complexity_metric} (target N={args.sample_size})...")
    sampled_data = stratified_sample_by_complexity(
        data, 
        target_n=args.sample_size, 
        complexity_col=args.complexity_metric
    )
    logger.info(f"Selected {len(sampled_data)} functions for inference.")

    # Load model
    logger.info(f"Loading model from {args.model_path}...")
    try:
        model = load_model(args.model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Run inference
    results = []
    for i, func_data in enumerate(sampled_data):
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(sampled_data)} functions.")
        
        result = process_single_function(
            model, 
            func_data, 
            args.task_type, 
            timeout_seconds=args.timeout
        )
        result['model_id'] = os.path.basename(args.model_path)
        result['task_type'] = args.task_type
        results.append(result)

    # Save results
    save_results(results, args.output_path)
    logger.info("Inference pipeline completed.")

if __name__ == "__main__":
    main()