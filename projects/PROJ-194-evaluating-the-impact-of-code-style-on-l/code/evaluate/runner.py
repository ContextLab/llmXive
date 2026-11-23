"""
runner.py - Orchestrates LLM task execution and metric collection.

This module implements T026:
1) Load the balanced dataset (from T022a).
2) Execute tasks (completion, bug detection, summarization).
3) Tag samples with is_semantic_opacity (using logic from T016b).
4) Log mutation types (from T022).
5) Save intermediate results to results/metrics_raw.csv with columns including token_count.
"""
import os
import csv
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Project imports based on provided API surface
from evaluate.dataset_balancer import load_json_data, determine_ground_truth, build_balanced_dataset, save_balanced_dataset, run_dataset_balancing, main as balancer_main
from evaluate.loader import load_codegen_2b_cpu, run_loader_test, main as loader_main
from evaluate.metrics import TaskResult, MetricsCalculator, run_metrics_evaluation, main as metrics_main
from evaluate.retry_logic import InferenceTimeoutError, InferenceRateLimitError, InferenceTransientError, retry_with_backoff, run_with_retry, run_retry_logic_test, main as retry_main
from evaluate.task_prompts import construct_prompt, get_task_prompt, TASK_COMPLETION, TASK_BUG_DETECTION, TASK_SUMMARIZATION
from transform.seed_manager import log_transform_seed, compute_mapping_hash, get_seed_entry, verify_reproducibility
from transform.generator import generate_all_variants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for paths
BALANCED_DATASET_PATH = "data/derived/balanced_dataset.csv"
OUTPUT_RESULTS_PATH = "results/metrics_raw.csv"
CONFIG_TOKEN_THRESHOLD_PATH = "code/evaluate/config/token_threshold.yaml"

def load_balanced_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Load the balanced dataset from CSV.
    Expected columns: id, code, is_buggy, mutation_type, is_generic_naming, is_stripped_comments, is_minified, is_semantic_opacity, token_count
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Balanced dataset not found at {dataset_path}. "
                              "Please ensure T022a has been executed to create data/derived/balanced_dataset.csv")
    
    data = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string booleans to actual booleans if needed
            for key in ['is_buggy', 'is_generic_naming', 'is_stripped_comments', 'is_minified', 'is_semantic_opacity']:
                if key in row:
                    row[key] = row[key].lower() == 'true' if isinstance(row[key], str) else bool(row[key])
            
            # Convert token_count to int
            if 'token_count' in row:
                try:
                    row['token_count'] = int(row['token_count'])
                except (ValueError, TypeError):
                    row['token_count'] = 0
            
            data.append(row)
    
    logger.info(f"Loaded {len(data)} samples from balanced dataset")
    return data

def get_semantic_opacity_flag(sample: Dict[str, Any]) -> bool:
    """
    Determine if a sample has semantic opacity (generic naming AND stripped comments).
    This replicates the logic from T016b.
    """
    is_generic = sample.get('is_generic_naming', False)
    is_stripped = sample.get('is_stripped_comments', False)
    return is_generic and is_stripped

def execute_task_for_sample(
    model,
    tokenizer,
    sample: Dict[str, Any],
    task_type: str,
    retry_attempts: int = 3
) -> Optional[TaskResult]:
    """
    Execute a single LLM task for a sample with retry logic.
    
    Args:
        model: The loaded CodeGen model
        tokenizer: The model tokenizer
        sample: The dataset sample
        task_type: One of 'completion', 'bug_detection', 'summarization'
        retry_attempts: Number of retry attempts for transient errors
    
    Returns:
        TaskResult object or None if execution fails permanently
    """
    code = sample.get('code', '')
    sample_id = sample.get('id', 'unknown')
    
    # Construct prompt based on task type
    try:
        prompt = get_task_prompt(task_type, code)
    except Exception as e:
        logger.error(f"Failed to construct prompt for {sample_id} task {task_type}: {e}")
        return None
    
    # Execute inference with retry logic
    try:
        logger.info(f"Executing {task_type} for sample {sample_id}")
        
        # Use retry logic for inference
        @retry_with_backoff(
            max_attempts=retry_attempts,
            backoff_factor=2.0,
            exceptions=(InferenceTimeoutError, InferenceRateLimitError, InferenceTransientError)
        )
        def run_inference():
            # Call the model
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            
            # Generate response
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract just the generated part (after the prompt)
            generated_text = response[len(prompt):] if response.startswith(prompt) else response
            return generated_text
        
        model_response = run_inference()
        
        # Calculate metrics
        # For bug detection and summarization, we need ground truth
        # For completion, we compare with original code if available
        metrics_calc = MetricsCalculator()
        
        if task_type == 'completion':
            # For completion, ground truth is the original code (if available)
            ground_truth = sample.get('ground_truth', code)
            result = metrics_calc.calculate_completion_metrics(
                prediction=model_response,
                ground_truth=ground_truth,
                sample_id=sample_id
            )
        elif task_type == 'bug_detection':
            # For bug detection, ground truth is is_buggy flag
            ground_truth_label = sample.get('is_buggy', False)
            # Convert model response to binary prediction
            prediction_label = 'bug' in model_response.lower() or 'error' in model_response.lower()
            result = metrics_calc.calculate_classification_metrics(
                prediction=prediction_label,
                ground_truth=ground_truth_label,
                sample_id=sample_id,
                task_type='bug_detection'
            )
        elif task_type == 'summarization':
            # For summarization, we might not have ground truth in the balanced dataset
            # We'll calculate BLEU/ROUGE against a placeholder or skip if no GT
            ground_truth = sample.get('summary', None)
            if ground_truth:
                result = metrics_calc.calculate_summarization_metrics(
                    prediction=model_response,
                    ground_truth=ground_truth,
                    sample_id=sample_id
                )
            else:
                # No ground truth available, return partial result
                result = TaskResult(
                    sample_id=sample_id,
                    task_type=task_type,
                    prediction=model_response,
                    ground_truth=None,
                    exact_match=0.0,
                    code_bleu=0.0,
                    precision=0.0,
                    recall=0.0,
                    f1=0.0,
                    rouge_l=0.0,
                    bleu=0.0,
                    token_count=sample.get('token_count', 0),
                    is_semantic_opacity=get_semantic_opacity_flag(sample),
                    mutation_type=sample.get('mutation_type', 'none'),
                    is_buggy=sample.get('is_buggy', False),
                    timestamp=datetime.now().isoformat()
                )
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"Inference failed for sample {sample_id}, task {task_type}: {e}")
        return None

def run_evaluation_pipeline(
    dataset_path: str = BALANCED_DATASET_PATH,
    output_path: str = OUTPUT_RESULTS_PATH,
    tasks: List[str] = None,
    max_samples: Optional[int] = None
) -> List[TaskResult]:
    """
    Run the full evaluation pipeline.
    
    Args:
        dataset_path: Path to balanced dataset CSV
        output_path: Path to save results CSV
        tasks: List of tasks to run (default: all three)
        max_samples: Maximum number of samples to process (None for all)
    
    Returns:
        List of TaskResult objects
    """
    if tasks is None:
        tasks = [TASK_COMPLETION, TASK_BUG_DETECTION, TASK_SUMMARIZATION]
    
    # Load dataset
    logger.info(f"Loading balanced dataset from {dataset_path}")
    samples = load_balanced_dataset(dataset_path)
    
    if max_samples:
        samples = samples[:max_samples]
        logger.info(f"Limiting to {max_samples} samples")
    
    # Load model
    logger.info("Loading CodeGen-2B model")
    model, tokenizer = load_codegen_2b_cpu()
    if model is None or tokenizer is None:
        raise RuntimeError("Failed to load model. Check loader implementation.")
    
    # Process each sample
    all_results = []
    start_time = time.time()
    
    for i, sample in enumerate(samples):
        logger.info(f"Processing sample {i+1}/{len(samples)}: {sample.get('id', 'unknown')}")
        
        for task_type in tasks:
            result = execute_task_for_sample(
                model=model,
                tokenizer=tokenizer,
                sample=sample,
                task_type=task_type,
                retry_attempts=3
            )
            
            if result:
                all_results.append(result)
                logger.info(f"  Completed {task_type} for {sample.get('id')}")
        
        # Small delay to avoid overwhelming the system
        time.sleep(0.1)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed {len(all_results)} task executions in {elapsed:.2f} seconds")
    
    # Save results to CSV
    logger.info(f"Saving results to {output_path}")
    save_results_to_csv(all_results, output_path)
    
    return all_results

def save_results_to_csv(results: List[TaskResult], output_path: str) -> None:
    """
    Save TaskResult objects to CSV with all required columns.
    
    Columns include:
    - sample_id, task_type, prediction, ground_truth
    - exact_match, code_bleu, precision, recall, f1, rouge_l, bleu
    - token_count, is_semantic_opacity, mutation_type, is_buggy
    - timestamp
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        'sample_id', 'task_type', 'prediction', 'ground_truth',
        'exact_match', 'code_bleu', 'precision', 'recall', 'f1', 'rouge_l', 'bleu',
        'token_count', 'is_semantic_opacity', 'mutation_type', 'is_buggy', 'timestamp'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                'sample_id': result.sample_id,
                'task_type': result.task_type,
                'prediction': result.prediction if result.prediction else '',
                'ground_truth': result.ground_truth if result.ground_truth else '',
                'exact_match': result.exact_match,
                'code_bleu': result.code_bleu,
                'precision': result.precision,
                'recall': result.recall,
                'f1': result.f1,
                'rouge_l': result.rouge_l,
                'bleu': result.bleu,
                'token_count': result.token_count,
                'is_semantic_opacity': str(result.is_semantic_opacity),
                'mutation_type': result.mutation_type if result.mutation_type else 'none',
                'is_buggy': str(result.is_buggy),
                'timestamp': result.timestamp
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def run_runner_test(max_samples: int = 2) -> bool:
    """
    Run a test of the runner with a small number of samples.
    Returns True if test passes, False otherwise.
    """
    try:
        logger.info("Running runner test...")
        
        # Run with max_samples to verify functionality
        results = run_evaluation_pipeline(
            dataset_path=BALANCED_DATASET_PATH,
            output_path=OUTPUT_RESULTS_PATH,
            max_samples=max_samples
        )
        
        if len(results) == 0:
            logger.error("No results generated in test")
            return False
        
        # Verify required fields are present
        first_result = results[0]
        required_fields = ['sample_id', 'task_type', 'token_count', 'is_semantic_opacity', 'mutation_type']
        
        for field in required_fields:
            if not hasattr(first_result, field):
                logger.error(f"Missing required field: {field}")
                return False
        
        logger.info(f"Runner test passed. Generated {len(results)} results.")
        return True
        
    except Exception as e:
        logger.error(f"Runner test failed: {e}")
        return False

def main():
    """Main entry point for the runner script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LLM evaluation pipeline")
    parser.add_argument('--dataset', type=str, default=BALANCED_DATASET_PATH,
                      help='Path to balanced dataset CSV')
    parser.add_argument('--output', type=str, default=OUTPUT_RESULTS_PATH,
                      help='Path to output results CSV')
    parser.add_argument('--tasks', type=str, nargs='+', 
                      choices=[TASK_COMPLETION, TASK_BUG_DETECTION, TASK_SUMMARIZATION],
                      default=None, help='Tasks to run (default: all)')
    parser.add_argument('--max-samples', type=int, default=None,
                      help='Maximum number of samples to process')
    parser.add_argument('--test', action='store_true',
                      help='Run test mode with limited samples')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_runner_test(max_samples=2)
        if success:
            print("Test passed")
            return 0
        else:
            print("Test failed")
            return 1
    
    try:
        results = run_evaluation_pipeline(
            dataset_path=args.dataset,
            output_path=args.output,
            tasks=args.tasks,
            max_samples=args.max_samples
        )
        
        print(f"Successfully processed {len(results)} tasks")
        print(f"Results saved to: {args.output}")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())