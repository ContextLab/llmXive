import os
import sys
import json
import random
import argparse
import numpy as np
import torch
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Project imports
from config import get_config, validate_config
from utils.logging import get_logger, EvaluationError
from models.base_llama import BaseLlamaWrapper
from models.recursive_llama import RecursiveLlamaWrapper
from evaluation.results import EvaluationResult
from evaluation.metrics import calculate_self_consistency, calculate_brier_score, calculate_ece, calculate_roc_auc

# Configure paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
RESULTS_DIR = ARTIFACTS_DIR / "results"

logger = get_logger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_model_and_tokenizer(
    model_path: str,
    is_recursive: bool = False,
    device: str = "cpu"
) -> Tuple[Any, Any]:
    """Load a trained model and its tokenizer."""
    from transformers import AutoTokenizer
    
    logger.info(f"Loading model from {model_path} (recursive={is_recursive})")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if is_recursive:
        model = RecursiveLlamaWrapper.from_pretrained(model_path)
    else:
        model = BaseLlamaWrapper.from_pretrained(model_path)
    
    model.to(device)
    model.eval()
    logger.info("Model loaded successfully")
    return model, tokenizer

def prepare_gsm8k_prompt(example: Dict[str, Any]) -> str:
    """Format a GSM8K example into a prompt."""
    question = example['question']
    # Standard GSM8K prompt format
    prompt = f"Question: {question}\nAnswer:"
    return prompt

def prepare_mmlu_prompt(example: Dict[str, Any], subject: str) -> str:
    """Format an MMLU example into a prompt."""
    question = example['question']
    choices = example['choices']
    # Format choices as A, B, C, D
    choices_str = "\n".join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])
    prompt = f"Question: {question}\n{choices_str}\nAnswer:"
    return prompt

def generate_reasoning_path(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 256,
    num_paths: int = 5
) -> List[str]:
    """Generate multiple reasoning paths for a given prompt."""
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    reasoning_paths = []

    for _ in range(num_paths):
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tokenizer.pad_token_id
            )
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract the generated part after the prompt
            generated_part = generated_text[len(prompt):].strip()
            reasoning_paths.append(generated_part)

    return reasoning_paths

def run_gsm8k_benchmark(
    model: Any,
    tokenizer: Any,
    data_path: str,
    num_samples: int = 100,
    num_paths: int = 5
) -> Dict[str, Any]:
    """Run the GSM8K benchmark and return metrics."""
    from datasets import load_dataset
    
    logger.info(f"Loading GSM8K dataset from {data_path}")
    dataset = load_dataset("gsm8k", "main", split="test")
    
    # Sample if necessary
    if len(dataset) > num_samples:
        dataset = dataset.shuffle(seed=42).select(range(num_samples))

    results = []
    correct_count = 0
    confidence_scores = []

    for i, example in enumerate(dataset):
        prompt = prepare_gsm8k_prompt(example)
        reasoning_paths = generate_reasoning_path(model, tokenizer, prompt, num_paths=num_paths)
        
        # Extract answers from reasoning paths
        answers = []
        for path in reasoning_paths:
            # Simple heuristic: look for the last number in the text
            import re
            numbers = re.findall(r'\d+', path)
            if numbers:
                answers.append(numbers[-1])
            else:
                answers.append(None)

        # Majority vote
        from collections import Counter
        valid_answers = [a for a in answers if a is not None]
        if valid_answers:
            majority_answer = Counter(valid_answers).most_common(1)[0][0]
        else:
            majority_answer = None

        # Ground truth
        ground_truth = example['answer'].split('####')[-1].strip()
        
        is_correct = (majority_answer == ground_truth)
        if is_correct:
            correct_count += 1

        # Estimate confidence (simplified: proportion of paths agreeing with majority)
        if valid_answers:
            confidence = valid_answers.count(majority_answer) / len(valid_answers)
        else:
            confidence = 0.0
        
        confidence_scores.append(confidence)
        results.append({
            "question": example['question'],
            "ground_truth": ground_truth,
            "prediction": majority_answer,
            "reasoning_paths": reasoning_paths,
            "correct": is_correct,
            "confidence": confidence
        })

        if (i + 1) % 20 == 0:
            logger.info(f"Processed {i + 1}/{len(dataset)} GSM8K samples")

    accuracy = correct_count / len(dataset) if len(dataset) > 0 else 0.0
    
    # Calculate calibration metrics
    brier_score = calculate_brier_score(results, "correct", "confidence")
    ece = calculate_ece(results, "correct", "confidence", num_bins=10)
    
    return {
        "dataset": "gsm8k",
        "num_samples": len(dataset),
        "accuracy": accuracy,
        "brier_score": brier_score,
        "ece": ece,
        "raw_results": results
    }

def run_mmlu_benchmark(
    model: Any,
    tokenizer: Any,
    data_path: str,
    num_samples: int = 100,
    num_paths: int = 5
) -> Dict[str, Any]:
    """Run the MMLU benchmark and return metrics."""
    from datasets import load_dataset
    
    logger.info(f"Loading MMLU dataset from {data_path}")
    # Load a subset of MMLU (e.g., 'high_school_mathematics')
    dataset = load_dataset("cais/mmlu", "high_school_mathematics", split="test")
    
    if len(dataset) > num_samples:
        dataset = dataset.shuffle(seed=42).select(range(num_samples))

    results = []
    correct_count = 0
    confidence_scores = []

    for i, example in enumerate(dataset):
        prompt = prepare_mmlu_prompt(example, "high_school_mathematics")
        reasoning_paths = generate_reasoning_path(model, tokenizer, prompt, num_paths=num_paths)
        
        # Extract answers (expecting A, B, C, or D)
        answers = []
        for path in reasoning_paths:
            # Look for the last letter in the path that is A, B, C, or D
            import re
            matches = re.findall(r'[ABCD]', path)
            if matches:
                answers.append(matches[-1])
            else:
                answers.append(None)

        # Majority vote
        from collections import Counter
        valid_answers = [a for a in answers if a is not None]
        if valid_answers:
            majority_answer = Counter(valid_answers).most_common(1)[0][0]
        else:
            majority_answer = None

        # Ground truth (MMLU labels are 0, 1, 2, 3 -> A, B, C, D)
        label_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        ground_truth = label_map.get(example['answer'], None)
        
        is_correct = (majority_answer == ground_truth)
        if is_correct:
            correct_count += 1

        # Estimate confidence
        if valid_answers:
            confidence = valid_answers.count(majority_answer) / len(valid_answers)
        else:
            confidence = 0.0
        
        confidence_scores.append(confidence)
        results.append({
            "question": example['question'],
            "ground_truth": ground_truth,
            "prediction": majority_answer,
            "reasoning_paths": reasoning_paths,
            "correct": is_correct,
            "confidence": confidence
        })

        if (i + 1) % 20 == 0:
            logger.info(f"Processed {i + 1}/{len(dataset)} MMLU samples")

    accuracy = correct_count / len(dataset) if len(dataset) > 0 else 0.0
    
    # Calculate calibration metrics
    brier_score = calculate_brier_score(results, "correct", "confidence")
    ece = calculate_ece(results, "correct", "confidence", num_bins=10)
    
    return {
        "dataset": "mmlu_high_school_mathematics",
        "num_samples": len(dataset),
        "accuracy": accuracy,
        "brier_score": brier_score,
        "ece": ece,
        "raw_results": results
    }

def create_shuffled_attention_control_dataset(
    model: Any,
    tokenizer: Any,
    data_path: str,
    output_path: str,
    num_samples: int = 50
) -> None:
    """Create a control dataset with shuffled attention to isolate temporal recursion effects."""
    from datasets import load_dataset
    
    logger.info(f"Creating shuffled attention control dataset for {num_samples} samples")
    dataset = load_dataset("gsm8k", "main", split="test")
    
    if len(dataset) > num_samples:
        dataset = dataset.shuffle(seed=42).select(range(num_samples))

    control_results = []
    
    for i, example in enumerate(dataset):
        prompt = prepare_gsm8k_prompt(example)
        
        # Generate with standard attention
        standard_paths = generate_reasoning_path(model, tokenizer, prompt, num_paths=3)
        
        # Simulate shuffled attention by shuffling the tokens in the prompt before generation
        # This is a simplified proxy for the actual mechanism
        import random
        tokens = tokenizer.encode(prompt, return_tensors="pt").squeeze().tolist()
        # Shuffle tokens (excluding special tokens at start/end if any)
        if len(tokens) > 10:
            middle = tokens[5:-5]
            random.shuffle(middle)
            shuffled_tokens = tokens[:5] + middle + tokens[-5:]
            shuffled_prompt = tokenizer.decode(shuffled_tokens)
        else:
            shuffled_prompt = prompt # Fallback if too short
        
        shuffled_paths = generate_reasoning_path(model, tokenizer, shuffled_prompt, num_paths=3)
        
        control_results.append({
            "question": example['question'],
            "standard_reasoning": standard_paths,
            "shuffled_reasoning": shuffled_paths
        })

    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(control_results, f, indent=2)
    
    logger.info(f"Shuffled attention control dataset saved to {output_path}")

def validate_evaluation_result_schema(result: Dict[str, Any]) -> bool:
    """
    Validate that the benchmark result dictionary matches the EvaluationResult schema.
    This implements T021: Contract validation.
    """
    # Expected schema based on EvaluationResult dataclass
    required_fields = [
        "model_id",
        "timestamp",
        "dataset_results",
        "control_results",
        "metadata"
    ]
    
    if not isinstance(result, dict):
        logger.error("Validation failed: Result is not a dictionary")
        return False

    for field in required_fields:
        if field not in result:
            logger.error(f"Validation failed: Missing required field '{field}'")
            return False

    # Validate dataset_results structure
    if not isinstance(result["dataset_results"], dict):
        logger.error("Validation failed: 'dataset_results' is not a dictionary")
        return False
    
    for dataset_name, metrics in result["dataset_results"].items():
        if not isinstance(metrics, dict):
            logger.error(f"Validation failed: Metrics for '{dataset_name}' is not a dictionary")
            return False
        
        # Check for expected metric keys
        expected_metric_keys = ["accuracy", "brier_score", "ece"]
        for key in expected_metric_keys:
            if key not in metrics:
                logger.warning(f"Warning: Expected metric '{key}' missing for dataset '{dataset_name}'")
                # We allow missing metrics but log it; strict schema might require them

    # Validate control_results
    if result["control_results"] is not None and not isinstance(result["control_results"], list):
        logger.error("Validation failed: 'control_results' is not a list")
        return False

    # Validate metadata
    if not isinstance(result["metadata"], dict):
        logger.error("Validation failed: 'metadata' is not a dictionary")
        return False

    logger.info("Validation passed: Result matches EvaluationResult schema")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run benchmarks and evaluate meta-cognitive metrics.")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the trained model")
    parser.add_argument("--is_recursive", action="store_true", help="Flag indicating if the model is recursive")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--gsm8k_samples", type=int, default=100, help="Number of GSM8K samples to evaluate")
    parser.add_argument("--mmlu_samples", type=int, default=100, help="Number of MMLU samples to evaluate")
    parser.add_argument("--num_paths", type=int, default=5, help="Number of reasoning paths per question")
    parser.add_argument("--output_dir", type=str, default=str(RESULTS_DIR), help="Directory to save results")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load model
    device = "cpu" # Enforcing CPU-only per constraints
    model, tokenizer = load_model_and_tokenizer(args.model_path, args.is_recursive, device)
    
    # Run benchmarks
    logger.info("Starting GSM8K benchmark...")
    gsm8k_results = run_gsm8k_benchmark(model, tokenizer, str(RAW_DATA_DIR / "gsm8k.json"), args.gsm8k_samples, args.num_paths)
    
    logger.info("Starting MMLU benchmark...")
    mmlu_results = run_mmlu_benchmark(model, tokenizer, str(RAW_DATA_DIR / "mmlu.json"), args.mmlu_samples, args.num_paths)
    
    # Create shuffled attention control dataset
    control_output_path = os.path.join(args.output_dir, "shuffled_attention_control.json")
    create_shuffled_attention_control_dataset(model, tokenizer, str(RAW_DATA_DIR / "gsm8k.json"), control_output_path, num_samples=50)
    
    # Aggregate results into EvaluationResult schema
    evaluation_result = {
        "model_id": os.path.basename(args.model_path),
        "timestamp": datetime.now().isoformat(),
        "dataset_results": {
            "gsm8k": {
                "accuracy": gsm8k_results["accuracy"],
                "brier_score": gsm8k_results["brier_score"],
                "ece": gsm8k_results["ece"]
            },
            "mmlu_high_school_mathematics": {
                "accuracy": mmlu_results["accuracy"],
                "brier_score": mmlu_results["brier_score"],
                "ece": mmlu_results["ece"]
            }
        },
        "control_results": control_output_path,
        "metadata": {
            "seed": args.seed,
            "num_paths": args.num_paths,
            "gsm8k_samples": args.gsm8k_samples,
            "mmlu_samples": args.mmlu_samples,
            "is_recursive": args.is_recursive,
            "device": device
        }
    }
    
    # T021: Contract Validation
    if not validate_evaluation_result_schema(evaluation_result):
        raise EvaluationError("Output JSON failed schema validation against EvaluationResult contract.")
    
    # Save results
    output_file = os.path.join(args.output_dir, "evaluation_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_result, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_file}")
    logger.info(f"GSM8K Accuracy: {gsm8k_results['accuracy']:.4f}")
    logger.info(f"MMLU Accuracy: {mmlu_results['accuracy']:.4f}")

if __name__ == "__main__":
    main()