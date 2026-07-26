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
from evaluation.latency_monitor import measure_inference_latency, save_latency_results, collect_latency_stats

# --- Data Loading ---

def load_repopeftbench_data() -> List[Dict[str, Any]]:
    """
    Loads the RepoPeftBench Python subset.
    Expects data to be available at data/raw/repopeftbench/python.jsonl or similar.
    For this implementation, we assume the data is pre-loaded in data/raw/
    as per T054 (Data Acquisition).
    """
    config = load_config()
    data_path = Path(config.repo_peft_bench_path) / "python.jsonl"
    
    if not data_path.exists():
        # Fallback to a standard location if config path is not set correctly
        data_path = Path("data/raw/repopeftbench/python.jsonl")
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"RepoPeftBench data not found at {data_path}. "
            "Please run T054 (download_repopeftbench.py) first."
        )

    tasks = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    return tasks

# --- Adapter Loading ---

def load_ast_adapter(adapter_path: str, base_model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads the base model and the AST-generated adapter.
    """
    config = load_config()
    base_model_path = config.base_model_path or base_model_name
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float32, # Force float32 for CPU compatibility as per constraints
        low_cpu_mem_usage=True
    )
    
    adapter_path_obj = Path(adapter_path)
    if not adapter_path_obj.exists():
        # Try relative to data/adapters if not absolute
        alt_path = Path("data/adapters") / adapter_path
        if alt_path.exists():
            adapter_path_obj = alt_path
        else:
            raise FileNotFoundError(f"Adapter not found at {adapter_path}")
    
    model = PeftModel.from_pretrained(base_model, str(adapter_path_obj))
    model.eval()
    return model, tokenizer

# --- Inference & Scoring ---

def run_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    task: Dict[str, Any],
    max_new_tokens: int = 128
) -> str:
    """
    Runs inference for a single task.
    task expected to have 'prompt' and potentially 'input' fields.
    """
    prompt = task.get('prompt', '')
    input_text = task.get('input', '')
    full_input = f"{prompt}\n{input_text}" if input_text else prompt

    inputs = tokenizer(full_input, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Strip the input part to get just the completion
    if generated_text.startswith(full_input):
        return generated_text[len(full_input):].strip()
    return generated_text.strip()

def compute_exact_match(generation: str, expected: str) -> float:
    """
    Computes exact match score. Returns 1.0 if match, 0.0 otherwise.
    Normalizes whitespace for comparison.
    """
    gen_norm = " ".join(generation.split())
    exp_norm = " ".join(expected.split())
    return 1.0 if gen_norm == exp_norm else 0.0

# --- Main Evaluation Logic ---

def run_evaluation(
    adapter_path: str,
    base_model_name: str,
    output_csv: str,
    latency_csv: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs the full evaluation pipeline.
    Optionally measures inference latency per task if latency_csv is provided.
    """
    tasks = load_repopeftbench_data()
    model, tokenizer = load_ast_adapter(adapter_path, base_model_name)
    
    results = []
    latencies = []
    
    print(f"Evaluating {len(tasks)} tasks...")
    
    for i, task in enumerate(tasks):
        task_id = task.get('task_id', f'task_{i}')
        expected = task.get('expected_output', '')
        
        # Measure latency
        start_time = time.perf_counter()
        try:
            generation = run_inference(model, tokenizer, task)
            latency_ms = (time.perf_counter() - start_time) * 1000
        except Exception as e:
            # If inference fails, record 0 or handle appropriately
            # For strict FR-004 compliance, we might want to crash, but usually
            # we log the error and continue. Here we record 0 latency for failed tasks.
            latency_ms = 0.0
            generation = ""
            print(f"Error in task {task_id}: {e}")
        
        score = compute_exact_match(generation, expected)
        
        results.append({
            'task_id': task_id,
            'score': score,
            'generation': generation,
            'expected': expected
        })
        
        if latency_csv:
            latencies.append({
                'task_id': task_id,
                'latency_ms': latency_ms
            })
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(tasks)} tasks. Current Score: {sum(r['score'] for r in results)/(i+1):.4f}")

    # Save results
    save_results(results, output_csv)
    
    if latency_csv:
        save_latency_results(latencies, latency_csv)
        stats = collect_latency_stats(latencies)
        print(f"Latency Stats: {stats}")

    return {
        'total_tasks': len(tasks),
        'average_score': sum(r['score'] for r in results) / len(results) if results else 0.0,
        'results_path': output_csv,
        'latency_path': latency_csv
    }

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Saves evaluation results to a CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'score', 'generation', 'expected'])
        writer.writeheader()
        writer.writerows(results)

def main():
    """
    CLI entry point for evaluation.
    Usage: python code/main.py evaluate --adapter <path> --latency-csv <path>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate AST-based adapter")
    parser.add_argument('--adapter', type=str, required=True, help="Path to the adapter .safetensors")
    parser.add_argument('--model', type=str, default=None, help="Base model name/path")
    parser.add_argument('--output', type=str, default="data/results/ast_scores.csv", help="Output CSV for scores")
    parser.add_argument('--latency-csv', type=str, default=None, help="Output CSV for latency (FR-004)")
    
    args = parser.parse_args()
    
    config = load_config()
    base_model = args.model or config.base_model_path
    
    if not base_model:
        print("Error: Base model not specified in config or --model argument.")
        return 1

    result = run_evaluation(
        adapter_path=args.adapter,
        base_model_name=base_model,
        output_csv=args.output,
        latency_csv=args.latency_csv
    )
    
    print(f"Evaluation Complete. Avg Score: {result['average_score']:.4f}")
    if result['latency_path']:
        print(f"Latency results saved to: {result['latency_path']}")
        
    return 0

if __name__ == "__main__":
    exit(main())
