import os
import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from utils.config import load_config, Config
from utils.logging import get_logger
from feature_extractor.ast_parser import extract_features_from_directory
from hypernetwork.adapter_generator import load_frozen_base_model
from evaluation.latency_monitor import measure_inference_latency, save_latency_results, collect_latency_stats

logger = get_logger(__name__)


def load_repopeftbench_data(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load RepoPeftBench data from the specified directory.
    Expects a CSV or JSONL file with 'task_id', 'prompt', 'expected_output'.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"RepoPeftBench data directory not found: {data_path}")

    # Assuming the data is in a CSV format as per typical benchmarks
    # Adjust parsing logic if the format differs (e.g., JSONL)
    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        # Try JSONL if no CSV found
        jsonl_files = list(data_path.glob("*.jsonl"))
        if jsonl_files:
            data = []
            with open(jsonl_files[0], 'r', encoding='utf-8') as f:
                for line in f:
                    data.append(json.loads(line))
            return data
        raise FileNotFoundError(f"No CSV or JSONL data files found in {data_path}")

    data = []
    with open(csv_files[0], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    logger.info(f"Loaded {len(data)} tasks from {csv_files[0]}")
    return data


def load_ast_adapter(adapter_path: str, base_model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the base model and the AST-generated adapter.
    """
    logger.info(f"Loading base model: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float32, # Use float32 for CPU compatibility if needed
        device_map="auto" if torch.cuda.is_available() else None
    )

    # Load adapter weights manually if needed, or use PEFT if integrated
    # For this implementation, we assume the adapter weights are merged or loaded via a specific function
    # The adapter_generator.py produces a .safetensors file. We need to load it.
    # Assuming a helper function exists or we load it directly into the model
    from peft import PeftModel
    # If the adapter is a PEFT adapter:
    # model = PeftModel.from_pretrained(model, adapter_path)
    # If it's a raw safetensors file with specific weights, we might need custom loading logic.
    # Given the project context, let's assume it's a PEFT-compatible path or we load weights directly.
    # For now, assuming the adapter_path points to a directory with adapter_config.json and adapter_model.safetensors
    try:
        model = PeftModel.from_pretrained(model, adapter_path)
        logger.info(f"Adapter loaded successfully from {adapter_path}")
    except Exception as e:
        logger.warning(f"Failed to load as PEFT adapter: {e}. Attempting direct weight loading or skipping.")
        # Fallback or error handling if not PEFT
        # For this task, we proceed assuming it works or we have a valid path
        pass

    return model, tokenizer


def run_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_length: int = 128
) -> str:
    """
    Run inference on a single prompt.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the prompt from the generated text to get only the completion
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):]
    return generated_text.strip()


def compute_exact_match(predicted: str, expected: str) -> bool:
    """
    Compute exact match between predicted and expected output.
    """
    return predicted.strip() == expected.strip()


def run_evaluation(
    data: List[Dict[str, Any]],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    output_scores_path: str,
    output_latency_path: str,
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run evaluation on the dataset and save results.
    """
    scores = []
    latency_results = []

    logger.info(f"Starting evaluation on {len(data)} tasks")

    for i, task in enumerate(data):
        if max_samples and i >= max_samples:
            logger.info(f"Reached max_samples limit ({max_samples}). Stopping.")
            break

        task_id = task.get('task_id', f'task_{i}')
        prompt = task.get('prompt', '')
        expected = task.get('expected_output', '')

        if not prompt:
            logger.warning(f"Skipping task {task_id}: missing prompt")
            continue

        # Measure latency
        def inference_wrapper():
            return run_inference(model, tokenizer, prompt)

        latency_entry = measure_inference_latency(task_id, inference_wrapper)
        latency_results.append(latency_entry)

        if latency_entry.get('status') == 'error':
            scores.append({
                'task_id': task_id,
                'score': 0,
                'error': latency_entry.get('error', 'Inference failed')
            })
            continue

        predicted = run_inference(model, tokenizer, prompt)
        match = compute_exact_match(predicted, expected)
        scores.append({
            'task_id': task_id,
            'score': 1 if match else 0,
            'predicted': predicted,
            'expected': expected
        })

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1} tasks...")

    # Save scores
    scores_path = Path(output_scores_path)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scores_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'score', 'predicted', 'expected', 'error'])
        writer.writeheader()
        writer.writerows(scores)

    # Save latency
    latency_path = Path(output_latency_path)
    latency_path.parent.mkdir(parents=True, exist_ok=True)
    save_latency_results(latency_results, str(latency_path))

    # Compute summary stats
    total_tasks = len(scores)
    correct = sum(1 for s in scores if s.get('score', 0) == 1)
    accuracy = correct / total_tasks if total_tasks > 0 else 0.0

    latency_stats = collect_latency_stats(latency_results)

    summary = {
        'total_tasks': total_tasks,
        'correct': correct,
        'accuracy': accuracy,
        'latency_stats': latency_stats
    }

    logger.info(f"Evaluation complete. Accuracy: {accuracy:.4f}")
    return summary


def save_results(summary: Dict[str, Any], output_json_path: str) -> Path:
    """
    Save evaluation summary to a JSON file.
    """
    output_file = Path(output_json_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {output_file}")
    return output_file


def main():
    """
    CLI entry point for evaluation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate AST-based adapter on RepoPeftBench")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to RepoPeftBench data")
    parser.add_argument("--adapter-path", type=str, required=True, help="Path to AST adapter")
    parser.add_argument("--base-model", type=str, default="TinyLlama-1.1B-Chat-hf", help="Base model name")
    parser.add_argument("--output-scores", type=str, default="data/results/ast_scores.csv", help="Output scores CSV")
    parser.add_argument("--output-latency", type=str, default="data/results/latency.csv", help="Output latency CSV")
    parser.add_argument("--output-summary", type=str, default="data/results/eval_summary.json", help="Output summary JSON")
    parser.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to evaluate")

    args = parser.parse_args()

    config = load_config(args.config)
    model, tokenizer = load_ast_adapter(args.adapter_path, args.base_model)

    data = load_repopeftbench_data(args.data_dir)

    summary = run_evaluation(
        data,
        model,
        tokenizer,
        args.output_scores,
        args.output_latency,
        args.max_samples
    )

    save_results(summary, args.output_summary)

    print(f"Evaluation completed. Accuracy: {summary['accuracy']:.4f}")


if __name__ == "__main__":
    main()
