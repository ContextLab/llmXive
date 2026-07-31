"""
Benchmark execution script for Self-Aware AI Through Recursive Introspection.
Implements standard MMLU/GSM8K inference (single path) for accuracy baseline.
"""
import os
import sys
import json
import random
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import LlamaForCausalLM, LlamaTokenizer
from datasets import load_dataset

# Project imports
from config import get_config, validate_config
from utils.logging import get_logger, log_evaluation_start, log_metric, EvaluationError
from evaluation.results import EvaluationResult
from evaluation.metrics import calculate_self_consistency, aggregate_metrics

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ARTIFACTS_RESULTS_DIR = PROJECT_ROOT / "artifacts" / "results"

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_model_and_tokenizer(model_path: str) -> Tuple[LlamaForCausalLM, LlamaTokenizer]:
    """Load model and tokenizer from checkpoint."""
    logger.info(f"Loading model from {model_path}")
    try:
        tokenizer = LlamaTokenizer.from_pretrained(model_path)
        model = LlamaForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32, # CPU constraint
            device_map="cpu"
        )
        model.eval()
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise EvaluationError(f"Model loading failed: {e}")

def prepare_gsm8k_prompt(example: Dict[str, Any]) -> str:
    """Prepare GSM8K prompt from dataset example."""
    question = example['question']
    # Standard GSM8K prompt format
    prompt = f"Question: {question}\nAnswer:"
    return prompt

def prepare_mmlu_prompt(example: Dict[str, Any], subject: str) -> str:
    """Prepare MMLU prompt from dataset example."""
    question = example['question']
    choices = example['choices']
    # Format choices
    choices_str = "\n".join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])
    prompt = f"Question: {question}\nOptions:\n{choices_str}\nAnswer:"
    return prompt

def generate_reasoning_path(
    model: LlamaForCausalLM,
    tokenizer: LlamaTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.0, # Single path baseline: greedy decoding
    top_p: float = 1.0
) -> str:
    """Generate a single reasoning path (answer) for the given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']

    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=(temperature > 0),
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode output, removing the prompt
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if full_output.startswith(prompt):
        generated_text = full_output[len(prompt):]
    else:
        generated_text = full_output

    return generated_text.strip()

def parse_gsm8k_answer(generated_text: str) -> Optional[str]:
    """Parse the final answer from GSM8K generation."""
    # Look for "####" or "The answer is" pattern
    if "####" in generated_text:
        parts = generated_text.split("####")
        if len(parts) > 1:
            return parts[-1].strip()
    # Fallback: try to extract last number
    import re
    numbers = re.findall(r'\d+\.?\d*', generated_text)
    if numbers:
        return numbers[-1]
    return None

def parse_mmlu_answer(generated_text: str) -> Optional[str]:
    """Parse the final answer (A, B, C, D) from MMLU generation."""
    # Look for the first letter A-D
    import re
    match = re.search(r'\b([A-D])\b', generated_text)
    if match:
        return match.group(1)
    return None

def run_gsm8k_benchmark(
    model: LlamaForCausalLM,
    tokenizer: LlamaTokenizer,
    dataset: List[Dict[str, Any]],
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Run GSM8K benchmark with single-path inference."""
    logger.info("Starting GSM8K benchmark (single path)...")
    results = []

    for i, example in enumerate(dataset):
        if max_samples and i >= max_samples:
            break

        prompt = prepare_gsm8k_prompt(example)
        generated = generate_reasoning_path(model, tokenizer, prompt)
        predicted = parse_gsm8k_answer(generated)
        correct_answer = example['answer'] # Usually contains the final number after ####

        # Extract correct answer for comparison
        correct_val = parse_gsm8k_answer(correct_answer)

        results.append({
            "question_id": i,
            "question": example['question'],
            "prompt": prompt,
            "generated_text": generated,
            "predicted_answer": predicted,
            "correct_answer": correct_val,
            "is_correct": (predicted == correct_val) if predicted and correct_val else False
        })

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(dataset)} GSM8K samples")

    return results

def run_mmlu_benchmark(
    model: LlamaForCausalLM,
    tokenizer: LlamaTokenizer,
    dataset: List[Dict[str, Any]],
    subject: str,
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Run MMLU benchmark with single-path inference."""
    logger.info(f"Starting MMLU benchmark for subject '{subject}' (single path)...")
    results = []

    for i, example in enumerate(dataset):
        if max_samples and i >= max_samples:
            break

        prompt = prepare_mmlu_prompt(example, subject)
        generated = generate_reasoning_path(model, tokenizer, prompt)
        predicted = parse_mmlu_answer(generated)
        correct_answer = example['answer'] # 0, 1, 2, 3 -> A, B, C, D

        correct_letter = chr(65 + correct_answer)

        results.append({
            "question_id": i,
            "question": example['question'],
            "prompt": prompt,
            "generated_text": generated,
            "predicted_answer": predicted,
            "correct_answer": correct_letter,
            "is_correct": (predicted == correct_letter) if predicted else False
        })

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(dataset)} MMLU {subject} samples")

    return results

def validate_evaluation_result_schema(result: Dict[str, Any]) -> bool:
    """Validate that the result dictionary matches the expected schema."""
    required_keys = ['accuracy', 'total_samples', 'correct_samples', 'results']
    return all(key in result for key in required_keys)

def main():
    parser = argparse.ArgumentParser(description="Run standard MMLU/GSM8K inference for accuracy baseline.")
    parser.add_argument("--model-path", type=str, required=True, help="Path to the model checkpoint.")
    parser.add_argument("--dataset", type=str, choices=["gsm8k", "mmlu"], required=True, help="Dataset to evaluate.")
    parser.add_argument("--mmlu-subject", type=str, default="all", help="MMLU subject (or 'all' for average).")
    parser.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to process.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path.")
    args = parser.parse_args()

    # Validate config
    try:
        config = get_config()
        validate_config(config)
    except Exception as e:
        logger.critical(f"Configuration validation failed: {e}")
        sys.exit(1)

    set_seed(args.seed)
    ARTIFACTS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load model
    model, tokenizer = load_model_and_tokenizer(args.model_path)

    # Load dataset
    dataset_path = RAW_DATA_DIR / f"{args.dataset}.json"
    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        logger.error("Please ensure T004b-GSM8K or T004b-MMLU has been completed to generate the data.")
        sys.exit(1)

    logger.info(f"Loading dataset from {dataset_path}")
    with open(dataset_path, 'r') as f:
        data = json.load(f)

    if args.dataset == "gsm8k":
        benchmark_results = run_gsm8k_benchmark(model, tokenizer, data, args.max_samples)
        subject_name = "GSM8K"
    elif args.dataset == "mmlu":
        if args.mmlu_subject == "all":
            # For 'all', we might need to aggregate multiple subjects if the JSON contains them
            # Assuming the JSON structure has a 'subject' field if it's a mix, or we process the whole list as one subject
            # If the file is a specific subject, we just run it.
            # To be safe, we check if 'subject' exists in the first item.
            if data and 'subject' in data[0]:
                subjects = list(set(item['subject'] for item in data))
                logger.warning(f"Dataset contains multiple subjects: {subjects}. Processing all sequentially.")
                all_results = []
                for subj in subjects:
                    subj_data = [item for item in data if item['subject'] == subj]
                    all_results.extend(run_mmlu_benchmark(model, tokenizer, subj_data, subj, args.max_samples))
                benchmark_results = all_results
            else:
                # Assume single subject or no subject field, treat as generic
                benchmark_results = run_mmlu_benchmark(model, tokenizer, data, "mixed", args.max_samples)
        else:
            # Filter by subject if specific
            if data and 'subject' in data[0]:
                filtered_data = [item for item in data if item['subject'] == args.mmlu_subject]
                benchmark_results = run_mmlu_benchmark(model, tokenizer, filtered_data, args.mmlu_subject, args.max_samples)
            else:
                benchmark_results = run_mmlu_benchmark(model, tokenizer, data, args.mmlu_subject, args.max_samples)
    else:
        logger.error(f"Unsupported dataset: {args.dataset}")
        sys.exit(1)

    # Calculate metrics
    total_samples = len(benchmark_results)
    correct_samples = sum(1 for r in benchmark_results if r['is_correct'])
    accuracy = correct_samples / total_samples if total_samples > 0 else 0.0

    evaluation_result = {
        "model_path": args.model_path,
        "dataset": args.dataset,
        "subject": args.mmlu_subject if args.dataset == "mmlu" else "N/A",
        "timestamp": datetime.now().isoformat(),
        "seed": args.seed,
        "total_samples": total_samples,
        "correct_samples": correct_samples,
        "accuracy": accuracy,
        "results": benchmark_results
    }

    # Validate schema
    if not validate_evaluation_result_schema(evaluation_result):
        logger.error("Evaluation result schema validation failed.")
        sys.exit(1)

    # Save output
    output_path = args.output if args.output else ARTIFACTS_RESULTS_DIR / f"baseline_{args.dataset}_{args.seed}.json"
    with open(output_path, 'w') as f:
        json.dump(evaluation_result, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    logger.info(f"Accuracy: {accuracy:.4f} ({correct_samples}/{total_samples})")
    log_metric("accuracy", accuracy)

if __name__ == "__main__":
    main()