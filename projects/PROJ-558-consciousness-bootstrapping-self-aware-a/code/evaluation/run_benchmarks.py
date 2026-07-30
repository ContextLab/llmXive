import os
import sys
import json
import random
import argparse
import numpy as np

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

from utils.logging import get_logger, EvaluationError
from evaluation.results import EvaluationResult
from config import get_config

logger = get_logger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_model_and_tokenizer(model_path: str, device: str = "cpu") -> tuple:
    """Load model and tokenizer from path."""
    logger.info(f"Loading model from {model_path} on {device}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
            device_map={"": device} if device != "cpu" else None,
            low_cpu_mem_usage=True
        )
        if device == "cpu":
            model = model.to("cpu")
        model.eval()
        return model, tokenizer
    except Exception as e:
        raise EvaluationError(f"Failed to load model: {e}")

def prepare_gsm8k_prompt(question: str) -> str:
    """Prepare GSM8K question with prompt template."""
    return f"Question: {question}\nAnswer: "

def prepare_mmlu_prompt(question: str, choices: list, subject: str) -> str:
    """Prepare MMLU question with prompt template."""
    choices_text = "\n".join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])
    return f"Subject: {subject}\nQuestion: {question}\nChoices:\n{choices_text}\nAnswer:"

def generate_reasoning_path(
    model, 
    tokenizer, 
    prompt: str, 
    max_new_tokens: int = 256, 
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True
) -> str:
    """Generate a single reasoning path."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if do_sample else 1.0,
            top_p=top_p if do_sample else 1.0,
            do_sample=do_sample,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract the generated part
    generated_text = full_response[len(prompt):].strip()
    return generated_text

def run_gsm8k_benchmark(
    model, 
    tokenizer, 
    dataset, 
    max_samples: int = None,
    seed: int = 42
) -> list:
    """Run GSM8K benchmark with single-path inference."""
    set_seed(seed)
    results = []
    
    logger.info(f"Starting GSM8K benchmark on {len(dataset)} samples")
    
    for i, item in enumerate(dataset):
        if max_samples and i >= max_samples:
            break
        
        question = item['question']
        answer = item['answer']
        
        prompt = prepare_gsm8k_prompt(question)
        generation = generate_reasoning_path(
            model, tokenizer, prompt, 
            max_new_tokens=512, 
            temperature=0.0,  # Greedy for baseline accuracy
            do_sample=False
        )
        
        # Simple extraction: look for the last number in the generation
        import re
        numbers = re.findall(r'\d+\.?\d*', generation)
        predicted = numbers[-1] if numbers else "0"
        
        # Extract correct answer (format: "The answer is 123")
        correct_match = re.search(r'The answer is (\d+\.?\d*)', answer)
        correct = correct_match.group(1) if correct_match else "0"
        
        is_correct = predicted == correct
        
        result = {
            "id": i,
            "question": question,
            "prediction": generation,
            "predicted_value": predicted,
            "correct_value": correct,
            "is_correct": is_correct
        }
        results.append(result)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(dataset)} GSM8K samples")
    
    return results

def run_mmlu_benchmark(
    model, 
    tokenizer, 
    dataset, 
    subject: str,
    max_samples: int = None,
    seed: int = 42
) -> list:
    """Run MMLU benchmark with single-path inference."""
    set_seed(seed)
    results = []
    
    logger.info(f"Starting MMLU benchmark on {subject} ({len(dataset)} samples)")
    
    for i, item in enumerate(dataset):
        if max_samples and i >= max_samples:
            break
        
        question = item['question']
        choices = item['choices']
        correct_label = item['answer']  # 0, 1, 2, or 3
        
        prompt = prepare_mmlu_prompt(question, choices, subject)
        generation = generate_reasoning_path(
            model, tokenizer, prompt,
            max_new_tokens=256,
            temperature=0.0,
            do_sample=False
        )
        
        # Extract predicted letter (A, B, C, D)
        import re
        letter_match = re.search(r'[A-D]', generation)
        predicted_letter = letter_match.group(0) if letter_match else None
        
        if predicted_letter:
            predicted_idx = ord(predicted_letter) - ord('A')
        else:
            predicted_idx = -1
        
        is_correct = (predicted_idx == correct_label)
        
        result = {
            "id": i,
            "subject": subject,
            "question": question,
            "choices": choices,
            "prediction": generation,
            "predicted_label": predicted_letter,
            "correct_label": chr(65 + correct_label),
            "is_correct": is_correct
        }
        results.append(result)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(dataset)} MMLU samples")
    
    return results

def validate_evaluation_result_schema(results: list, dataset_name: str) -> bool:
    """Validate that results match expected schema."""
    if not results:
        raise EvaluationError(f"No results generated for {dataset_name}")
    
    required_fields = ["id", "question", "prediction", "is_correct"]
    sample = results[0]
    
    for field in required_fields:
        if field not in sample:
            raise EvaluationError(f"Missing field '{field}' in {dataset_name} results")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Run standard MMLU/GSM8K inference for accuracy baseline")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--output_dir", type=str, default="artifacts/results", help="Output directory")
    parser.add_argument("--max_samples", type=int, default=None, help="Maximum number of samples to process")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on")
    args = parser.parse_args()

    config = get_config()
    set_seed(args.seed)

    os.makedirs(args.output_dir, exist_ok=True)

    try:
        model, tokenizer = load_model_and_tokenizer(args.model_path, args.device)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Load datasets
    logger.info("Loading GSM8K dataset...")
    try:
        gsm8k_dataset = load_dataset("gsm8k", "main", split="test")
    except Exception as e:
        raise EvaluationError(f"Failed to load GSM8K dataset: {e}")

    logger.info("Loading MMLU dataset...")
    try:
        mmlu_dataset = load_dataset("cais/mmlu", split="test")
    except Exception as e:
        raise EvaluationError(f"Failed to load MMLU dataset: {e}")

    # Run GSM8K benchmark
    logger.info("Running GSM8K benchmark...")
    gsm8k_results = run_gsm8k_benchmark(
        model, tokenizer, gsm8k_dataset, 
        max_samples=args.max_samples, 
        seed=args.seed
    )
    
    gsm8k_correct = sum(1 for r in gsm8k_results if r["is_correct"])
    gsm8k_accuracy = gsm8k_correct / len(gsm8k_results) if gsm8k_results else 0.0
    logger.info(f"GSM8K Accuracy: {gsm8k_accuracy:.4f} ({gsm8k_correct}/{len(gsm8k_results)})")

    # Run MMLU benchmark (subset of subjects for speed, or all)
    # For baseline, we run on a representative subset or all if feasible
    subjects = ["abstract_algebra", "anatomy", "astronomy", "business_ethics", "clinical_knowledge"]
    mmlu_all_results = []
    
    for subject in subjects:
        logger.info(f"Processing MMLU subject: {subject}")
        subject_data = mmlu_dataset.filter(lambda x: x["subject"] == subject)
        if len(subject_data) == 0:
            logger.warning(f"No data found for subject {subject}")
            continue
        
        subject_results = run_mmlu_benchmark(
            model, tokenizer, subject_data, 
            subject=subject,
            max_samples=args.max_samples, 
            seed=args.seed
        )
        mmlu_all_results.extend(subject_results)

    mmlu_correct = sum(1 for r in mmlu_all_results if r["is_correct"])
    mmlu_accuracy = mmlu_correct / len(mmlu_all_results) if mmlu_all_results else 0.0
    logger.info(f"MMLU Accuracy (subset): {mmlu_accuracy:.4f} ({mmlu_correct}/{len(mmlu_all_results)})")

    # Aggregate results
    final_results = {
        "gsm8k": {
            "accuracy": gsm8k_accuracy,
            "total_samples": len(gsm8k_results),
            "correct": gsm8k_correct,
            "details": gsm8k_results
        },
        "mmlu": {
            "accuracy": mmlu_accuracy,
            "total_samples": len(mmlu_all_results),
            "correct": mmlu_correct,
            "details": mmlu_all_results,
            "subjects": subjects
        },
        "overall_accuracy": (gsm8k_correct + mmlu_correct) / (len(gsm8k_results) + len(mmlu_all_results)) if (len(gsm8k_results) + len(mmlu_all_results)) > 0 else 0.0
    }

    output_path = os.path.join(args.output_dir, "baseline_accuracy_results.json")
    with open(output_path, "w") as f:
        json.dump(final_results, f, indent=2)

    logger.info(f"Baseline results saved to {output_path}")
    
    # Create EvaluationResult artifact for contract validation
    eval_result = EvaluationResult(
        model_path=args.model_path,
        metrics={
            "gsm8k_accuracy": gsm8k_accuracy,
            "mmlu_accuracy": mmlu_accuracy,
            "overall_accuracy": final_results["overall_accuracy"]
        },
        raw_data_path=output_path
    )
    
    eval_result_path = os.path.join(args.output_dir, "baseline_evaluation_result.json")
    eval_result.save(eval_result_path)
    logger.info(f"Evaluation result contract saved to {eval_result_path}")

if __name__ == "__main__":
    main()