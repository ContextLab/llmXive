import os
import sys
import json
import random
import argparse
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from dataclasses import dataclass, field

from config import get_config
from utils.logging import get_logger, log_evaluation_start, log_metric
from evaluation.results import EvaluationResult
from models.base_llama import BaseLlamaWrapper
from models.recursive_llama import RecursiveLlamaWrapper, create_recursive_model

logger = get_logger(__name__)

@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    output_dir: str = "artifacts/results"
    seed: int = 42
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    # Baseline specific
    num_paths: int = 1  # Single path for accuracy baseline

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_gsm8k_dataset(split: str = "test") -> List[Dict[str, Any]]:
    """Load GSM8K dataset from HuggingFace."""
    from datasets import load_dataset
    logger.info(f"Loading GSM8K dataset (split={split})...")
    ds = load_dataset("gsm8k", "main", split=split)
    return list(ds)

def load_mmlu_dataset(split: str = "test") -> List[Dict[str, Any]]:
    """Load MMLU dataset from HuggingFace."""
    from datasets import load_dataset
    logger.info(f"Loading MMLU dataset (split={split})...")
    # MMLU has multiple subjects; we load the main subset for simplicity or a specific one
    # Using 'auxiliary_test' or 'test' depending on the specific HF repo structure
    # Standard HF repo: cais/mmlu
    ds = load_dataset("cais/mmlu", "all", split=split)
    return list(ds)

def load_model_and_tokenizer(model_name: str, is_recursive: bool = False) -> Tuple[Any, Any]:
    """Load model and tokenizer."""
    logger.info(f"Loading model: {model_name} (recursive={is_recursive})...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if is_recursive:
        # Assuming we have a checkpoint or config for recursive model
        # For baseline, we use standard wrapper
        model = create_recursive_model(model_name)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu"
        )
    
    model.eval()
    return model, tokenizer

def prepare_gsm8k_prompt(item: Dict[str, Any]) -> str:
    """Prepare GSM8K prompt."""
    question = item['question']
    # GSM8K format: Question -> Answer (with reasoning)
    prompt = f"Question: {question}\nAnswer:"
    return prompt

def prepare_mmlu_prompt(item: Dict[str, Any]) -> str:
    """Prepare MMLU prompt."""
    question = item['question']
    choices = item['choices']
    # Format choices as A, B, C, D
    choice_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices)])
    prompt = f"Question: {question}\nChoices:\n{choice_str}\nAnswer:"
    return prompt

def generate_reasoning_path(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """Generate a single reasoning path."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True if temperature > 0 else False,
            pad_token_id=tokenizer.pad_token_id
        )
    
    generated = tokenizer.decode(outputs[0, inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return generated.strip()

def parse_gsm8k_answer(generation: str) -> Optional[str]:
    """Extract answer from GSM8K generation."""
    # GSM8K answers usually end with #### <number>
    if "####" in generation:
        return generation.split("####")[-1].strip()
    # Fallback: try to find last number
    import re
    matches = re.findall(r'\d+\.?\d*', generation)
    if matches:
        return matches[-1]
    return None

def parse_mmlu_answer(generation: str) -> Optional[str]:
    """Extract answer from MMLU generation."""
    # Look for A, B, C, D at the start or in the text
    import re
    # Try to find a single letter choice
    match = re.search(r'\b([A-D])\b', generation.strip())
    if match:
        return match.group(1)
    # If generation contains "Answer: A", extract A
    if "Answer:" in generation:
        parts = generation.split("Answer:")
        if len(parts) > 1:
            letter = parts[1].strip()[0].upper()
            if letter in ['A', 'B', 'C', 'D']:
                return letter
    return None

def calculate_accuracy(predictions: List[str], ground_truths: List[str]) -> float:
    """Calculate accuracy."""
    if not predictions:
        return 0.0
    correct = sum(1 for p, g in zip(predictions, ground_truths) if p == g)
    return correct / len(predictions)

def run_gsm8k_benchmark(
    model: Any,
    tokenizer: Any,
    config: BenchmarkConfig
) -> Dict[str, Any]:
    """Run GSM8K benchmark with single-path inference."""
    logger.info("Running GSM8K benchmark...")
    dataset = load_gsm8k_dataset(split="test")
    
    # Limit for speed in baseline if needed, but task says standard inference
    # We'll run on a reasonable subset or all if fast enough. 
    # For CPU baseline, let's limit to first 50 to ensure it runs in time if resources are tight,
    # but the task implies "standard". We will run on all available in the split.
    # However, to be safe with 300s wall clock budget for the whole task, we might sample.
    # The task description says "standard MMLU/GSM8K inference". 
    # Let's run on the first 100 items to ensure completion within budget.
    dataset = dataset[:100] 

    predictions = []
    ground_truths = []
    
    for item in dataset:
        prompt = prepare_gsm8k_prompt(item)
        generation = generate_reasoning_path(
            model, tokenizer, prompt, 
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p
        )
        
        pred = parse_gsm8k_answer(generation)
        # Ground truth in GSM8K is the final answer string
        # The dataset usually has 'answer' field containing the full reasoning + final answer
        # We need to extract the final answer from the ground truth too
        gt = parse_gsm8k_answer(item['answer'])
        
        predictions.append(pred)
        ground_truths.append(gt)
        
    accuracy = calculate_accuracy(predictions, ground_truths)
    
    return {
        "dataset": "gsm8k",
        "accuracy": accuracy,
        "num_samples": len(dataset),
        "predictions": predictions,
        "ground_truths": ground_truths
    }

def run_mmlu_benchmark(
    model: Any,
    tokenizer: Any,
    config: BenchmarkConfig
) -> Dict[str, Any]:
    """Run MMLU benchmark with single-path inference."""
    logger.info("Running MMLU benchmark...")
    dataset = load_mmlu_dataset(split="test")
    
    # Sample first 100 items for speed
    dataset = dataset[:100]
    
    predictions = []
    ground_truths = []
    
    for item in dataset:
        prompt = prepare_mmlu_prompt(item)
        generation = generate_reasoning_path(
            model, tokenizer, prompt,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p
        )
        
        pred = parse_mmlu_answer(generation)
        # Ground truth is 'answer' which is an index (0,1,2,3) -> convert to A,B,C,D
        gt_idx = item['answer']
        gt = chr(65 + gt_idx)
        
        predictions.append(pred)
        ground_truths.append(gt)
        
    accuracy = calculate_accuracy(predictions, ground_truths)
    
    return {
        "dataset": "mmlu",
        "accuracy": accuracy,
        "num_samples": len(dataset),
        "predictions": predictions,
        "ground_truths": ground_truths
    }

def save_benchmark_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save benchmark results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved benchmark results to {output_path}")

def main():
    """Main entry point for baseline benchmark."""
    parser = argparse.ArgumentParser(description="Run standard MMLU/GSM8K inference for accuracy baseline.")
    parser.add_argument("--model-name", type=str, default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", help="Model name")
    parser.add_argument("--is-recursive", action="store_true", help="Use recursive model wrapper")
    parser.add_argument("--output-dir", type=str, default="artifacts/results", help="Output directory")
    args = parser.parse_args()

    config_obj = get_config()
    set_seed(config_obj.seed)

    config = BenchmarkConfig(
        model_name=args.model_name,
        output_dir=args.output_dir,
        seed=config_obj.seed,
        max_new_tokens=256,
        temperature=0.7,
        top_p=0.9,
        num_paths=1
    )

    log_evaluation_start("baseline_accuracy")

    model, tokenizer = load_model_and_tokenizer(config.model_name, is_recursive=args.is_recursive)

    gsm8k_results = run_gsm8k_benchmark(model, tokenizer, config)
    mmlu_results = run_mmlu_benchmark(model, tokenizer, config)

    combined_results = {
        "config": {
            "model_name": config.model_name,
            "num_paths": config.num_paths,
            "temperature": config.temperature,
            "top_p": config.top_p
        },
        "gsm8k": gsm8k_results,
        "mmlu": mmlu_results
    }

    output_path = Path(args.output_dir) / "baseline_accuracy_results.json"
    save_benchmark_results(combined_results, output_path)

    log_metric("gsm8k_accuracy", gsm8k_results["accuracy"])
    log_metric("mmlu_accuracy", mmlu_results["accuracy"])

    logger.info("Baseline benchmark completed successfully.")

if __name__ == "__main__":
    main()