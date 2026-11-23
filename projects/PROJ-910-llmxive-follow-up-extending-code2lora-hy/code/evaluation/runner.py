"""
Evaluation runner for RepoPeftBench using AST-based adapters.

This module implements FR-004 by computing both exact-match scores and inference latency.
It loads the AST-based adapter, runs inference on the RepoPeftBench dataset, and outputs
results to data/results/ast_scores.csv.
"""
import os
import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import datasets
from utils.config import load_config, Config
from utils.logging import get_logger
from utils.memory_monitor import run_step_with_memory_logging

logger = get_logger(__name__)

def load_repopeftbench_data(config: Config, sample_size: Optional[int] = None) -> datasets.Dataset:
    """
    Load the RepoPeftBench Python subset from HuggingFace.
    
    Args:
        config: Configuration object containing dataset paths
        sample_size: Optional number of samples to load (for testing)
        
    Returns:
        HuggingFace Dataset object
    """
    logger.info("Loading RepoPeftBench dataset...")
    try:
        # Use streaming to handle large datasets
        dataset = datasets.load_dataset(
            config.repo_peft_bench_path, 
            "python",
            split="test",
            streaming=True
        )
        
        if sample_size:
            dataset = dataset.take(sample_size)
        
        # Convert streaming dataset to list for processing
        data_list = list(dataset)
        logger.info(f"Loaded {len(data_list)} samples from RepoPeftBench")
        return datasets.Dataset.from_list(data_list)
    except Exception as e:
        logger.error(f"Failed to load RepoPeftBench dataset: {e}")
        raise

def load_ast_adapter(config: Config) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the base model and attach the AST-based adapter.
    
    Args:
        config: Configuration object containing model paths
        
    Returns:
        Tuple of (PeftModel, AutoTokenizer)
    """
    logger.info(f"Loading base model from {config.base_model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(config.base_model_path)
    base_model = AutoModelForCausalLM.from_pretrained(
        config.base_model_path,
        torch_dtype=torch.float32,
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )
    
    adapter_path = config.ast_adapter_path
    if not os.path.exists(adapter_path):
        raise FileNotFoundError(f"AST adapter not found at {adapter_path}")
    
    logger.info(f"Loading AST adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model = model.merge_and_unload()
    
    logger.info("AST adapter loaded successfully")
    return model, tokenizer

def compute_exact_match(prediction: str, reference: str) -> bool:
    """
    Compute exact match between prediction and reference.
    
    Args:
        prediction: Model prediction string
        reference: Reference string
        
    Returns:
        True if exact match, False otherwise
    """
    return prediction.strip() == reference.strip()

def run_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    task: Dict[str, Any],
    max_length: int = 512
) -> Tuple[str, float]:
    """
    Run inference on a single task and measure latency.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        task: Task dictionary with 'input' and 'output' keys
        max_length: Maximum generation length
        
    Returns:
        Tuple of (prediction, latency_ms)
    """
    input_text = task['input']
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    
    start_time = time.perf_counter()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.0,  # Greedy decoding for exact match
            do_sample=False
        )
    end_time = time.perf_counter()
    
    latency_ms = (end_time - start_time) * 1000
    prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the generated part (after input)
    input_len = len(inputs['input_ids'][0])
    prediction = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    
    return prediction, latency_ms

def run_evaluation(
    dataset: datasets.Dataset,
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    config: Config
) -> List[Dict[str, Any]]:
    """
    Run evaluation on the entire dataset.
    
    Args:
        dataset: RepoPeftBench dataset
        model: Loaded model
        tokenizer: Loaded tokenizer
        config: Configuration object
        
    Returns:
        List of evaluation results
    """
    results = []
    total_samples = len(dataset)
    
    logger.info(f"Starting evaluation on {total_samples} samples...")
    
    for i, task in enumerate(dataset):
        task_id = task.get('task_id', f'task_{i}')
        reference = task.get('output', '')
        
        try:
            prediction, latency_ms = run_inference(model, tokenizer, task)
            exact_match = compute_exact_match(prediction, reference)
            
            results.append({
                'task_id': task_id,
                'exact_match': 1 if exact_match else 0,
                'latency_ms': round(latency_ms, 2),
                'prediction': prediction,
                'reference': reference
            })
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{total_samples} samples")
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            # Record failed tasks
            results.append({
                'task_id': task_id,
                'exact_match': 0,
                'latency_ms': 0.0,
                'prediction': '',
                'reference': reference,
                'error': str(e)
            })
    
    logger.info(f"Evaluation complete. Processed {len(results)} tasks.")
    return results

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save evaluation results to CSV.
    
    Args:
        results: List of evaluation results
        output_path: Path to output CSV file
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV with required columns
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'exact_match', 'latency_ms'])
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'task_id': result['task_id'],
                'exact_match': result['exact_match'],
                'latency_ms': result['latency_ms']
            })
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for AST adapter evaluation."""
    config = load_config()
    
    # Ensure results directory exists
    results_dir = Path(config.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "ast_scores.csv"
    
    try:
        # Load dataset
        dataset = load_repopeftbench_data(config, sample_size=config.sample_size)
        
        # Load model and adapter
        model, tokenizer = load_ast_adapter(config)
        
        # Run evaluation
        results = run_evaluation(dataset, model, tokenizer, config)
        
        # Save results
        save_results(results, str(output_path))
        
        # Compute and log summary statistics
        total_tasks = len(results)
        exact_matches = sum(1 for r in results if r['exact_match'] == 1)
        accuracy = exact_matches / total_tasks if total_tasks > 0 else 0.0
        avg_latency = sum(r['latency_ms'] for r in results) / total_tasks if total_tasks > 0 else 0.0
        
        logger.info(f"Summary: Accuracy={accuracy:.4f}, Avg Latency={avg_latency:.2f}ms")
        
        # Save summary JSON
        summary_path = results_dir / "ast_evaluation_summary.json"
        with open(summary_path, 'w') as f:
            json.dump({
                'total_tasks': total_tasks,
                'exact_matches': exact_matches,
                'accuracy': accuracy,
                'avg_latency_ms': avg_latency
            }, f, indent=2)
        
        logger.info(f"Evaluation complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()
