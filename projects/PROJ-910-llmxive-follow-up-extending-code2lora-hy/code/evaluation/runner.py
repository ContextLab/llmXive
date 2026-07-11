"""
Evaluation runner for RepoPeftBench tasks.

Loads the AST-based adapter, runs inference on benchmark tasks,
computes exact-match scores, and measures inference latency.
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

from utils.config import load_config, Config
from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path
from evaluation.latency_monitor import (
    measure_inference_latency,
    save_latency_results,
    collect_latency_stats
)


def load_repopeftbench_data(dataset_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load RepoPeftBench dataset.
    
    Args:
        dataset_path: Optional path to the dataset. If None, uses the 
                    path from config.
                    
    Returns:
        List of task dictionaries with 'task_id', 'prompt', 'expected_output'
    """
    config = load_config()
    if dataset_path is None:
        dataset_path = config.data_paths.repopeftbench_python
    
    data_path = Path(dataset_path)
    if not data_path.exists():
        raise FileNotFoundError(f"RepoPeftBench data not found at {data_path}")
    
    # Load JSONL or JSON format
    tasks = []
    if data_path.suffix == '.jsonl':
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                tasks.append(json.loads(line))
    elif data_path.suffix == '.json':
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list format and dict with 'tasks' key
            if isinstance(data, list):
                tasks = data
            elif isinstance(data, dict) and 'tasks' in data:
                tasks = data['tasks']
            else:
                tasks = [data]
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    return tasks


def load_ast_adapter(
    adapter_path: Optional[str] = None,
    base_model_name: Optional[str] = None
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the AST-based adapter on top of the base model.
    
    Args:
        adapter_path: Path to the adapter weights (.safetensors)
        base_model_name: Name of the base model (from config if None)
        
    Returns:
        Tuple of (model, tokenizer)
    """
    config = load_config()
    
    if base_model_name is None:
        base_model_name = config.model_paths.base_model
    if adapter_path is None:
        # Default to the generated adapter
        adapter_path = str(Path(config.data_paths.adapters) / "ast_adapter.safetensors")
    
    # Load base model
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float32,
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )
    
    # Load adapter
    model = PeftModel.from_pretrained(model, adapter_path)
    
    return model, tokenizer


def run_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 128
) -> str:
    """
    Run inference on a single prompt.
    
    Args:
        model: The loaded model with adapter
        tokenizer: The tokenizer
        prompt: Input prompt
        max_new_tokens: Maximum tokens to generate
        
    Returns:
        Generated text
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode and extract generated text
    generated = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return generated.strip()


def compute_exact_match(generated: str, expected: str) -> bool:
    """
    Compute exact match between generated and expected output.
    
    Args:
        generated: Model's generated output
        expected: Expected ground truth output
        
    Returns:
        True if exact match, False otherwise
    """
    # Normalize whitespace for comparison
    gen_normalized = ' '.join(generated.split())
    exp_normalized = ' '.join(expected.split())
    return gen_normalized == exp_normalized


def run_evaluation(
    adapter_path: Optional[str] = None,
    dataset_path: Optional[str] = None,
    output_scores_path: Optional[str] = None,
    output_latency_path: Optional[str] = None,
    max_new_tokens: int = 128,
    measure_latency: bool = True
) -> Dict[str, Any]:
    """
    Run full evaluation on RepoPeftBench tasks.
    
    Args:
        adapter_path: Path to the AST adapter
        dataset_path: Path to RepoPeftBench data
        output_scores_path: Path to save scores CSV
        output_latency_path: Path to save latency CSV
        max_new_tokens: Max tokens for generation
        measure_latency: Whether to measure inference latency
        
    Returns:
        Dict with evaluation results and statistics
    """
    config = load_config()
    
    # Load data
    tasks = load_repopeftbench_data(dataset_path)
    
    # Load model and tokenizer
    model, tokenizer = load_ast_adapter(adapter_path)
    
    # Prepare results
    scores = []
    latency_results = []
    
    for task in tasks:
        task_id = task.get('task_id', f"task_{len(scores)}")
        prompt = task.get('prompt', '')
        expected = task.get('expected_output', '')
        
        # Measure latency if requested
        if measure_latency:
            def inference_func():
                return run_inference(model, tokenizer, prompt, max_new_tokens)
            
            try:
                latency_ms = measure_inference_latency(task_id, inference_func)
                latency_results.append({
                    'task_id': task_id,
                    'latency_ms': latency_ms
                })
            except Exception as e:
                # Record high latency or skip for failed tasks
                latency_results.append({
                    'task_id': task_id,
                    'latency_ms': -1.0  # Indicator for error
                })
                # Continue to compute score (will likely fail)
        
        # Run inference
        try:
            generated = run_inference(model, tokenizer, prompt, max_new_tokens)
            is_match = compute_exact_match(generated, expected)
            scores.append({
                'task_id': task_id,
                'exact_match': int(is_match),
                'generated': generated,
                'expected': expected
            })
        except Exception as e:
            scores.append({
                'task_id': task_id,
                'exact_match': 0,
                'generated': '',
                'expected': expected,
                'error': str(e)
            })
    
    # Save results
    if output_scores_path is None:
        output_scores_path = "data/results/ast_scores.csv"
    
    save_results(scores, output_scores_path)
    
    latency_stats = {}
    if measure_latency and latency_results:
        if output_latency_path is None:
            output_latency_path = "data/results/latency.csv"
        save_latency_results(latency_results, output_latency_path)
        latency_stats = collect_latency_stats(latency_results)
    
    # Compute overall accuracy
    total_tasks = len(scores)
    correct = sum(s['exact_match'] for s in scores)
    accuracy = correct / total_tasks if total_tasks > 0 else 0.0
    
    return {
        'accuracy': accuracy,
        'total_tasks': total_tasks,
        'correct': correct,
        'scores_path': output_scores_path,
        'latency_stats': latency_stats,
        'latency_path': output_latency_path if measure_latency else None
    }


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save evaluation results to CSV.
    
    Args:
        results: List of result dicts
        output_path: Path to output file
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Use first result to determine fieldnames
        if results:
            fieldnames = list(results[0].keys())
        else:
            fieldnames = ['task_id', 'exact_match']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


def main():
    """
    CLI entry point for evaluation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate AST-based adapter on RepoPeftBench')
    parser.add_argument('--adapter', type=str, default=None, help='Path to adapter weights')
    parser.add_argument('--dataset', type=str, default=None, help='Path to RepoPeftBench data')
    parser.add_argument('--scores-output', type=str, default=None, help='Path for scores CSV')
    parser.add_argument('--latency-output', type=str, default=None, help='Path for latency CSV')
    parser.add_argument('--max-tokens', type=int, default=128, help='Max new tokens')
    parser.add_argument('--no-latency', action='store_true', help='Disable latency measurement')
    
    args = parser.parse_args()
    
    results = run_evaluation(
        adapter_path=args.adapter,
        dataset_path=args.dataset,
        output_scores_path=args.scores_output,
        output_latency_path=args.latency_output,
        max_new_tokens=args.max_tokens,
        measure_latency=not args.no_latency
    )
    
    print(f"Evaluation completed.")
    print(f"Accuracy: {results['accuracy']:.4f} ({results['correct']}/{results['total_tasks']})")
    
    if results['latency_stats']:
        print(f"Latency stats: {results['latency_stats']}")
        print(f"Latency saved to: {results['latency_path']}")
    
    print(f"Scores saved to: {results['scores_path']}")


if __name__ == '__main__':
    main()