import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig,
)
from peft import PeftModel

from src.utils.config import get_config
from src.utils.logging import get_logger
from src.utils.model_loader import load_model, get_model_card
from src.train.lora_config import create_lora_config_from_env

# Configure logger
logger = get_logger(__name__)

# Constants for benchmarking
GSM8K_TEST_SPLIT = "test"
MMLU_STEM_SUBJECTS = [
    "abstract_algebra",
    "anatomy",
    "astronomy",
    "biology",
    "chemistry",
    "college_biology",
    "college_chemistry",
    "college_computer_science",
    "college_mathematics",
    "college_physics",
    "computer_security",
    "conceptual_physics",
    "econometrics",
    "electrical_engineering",
    "elementary_mathematics",
    "high_school_biology",
    "high_school_chemistry",
    "high_school_computer_science",
    "high_school_mathematics",
    "high_school_physics",
    "high_school_statistics",
    "machine_learning",
    "mathematics",
    "medical_genetics",
    "miscellaneous",
    "nutrition",
    "professional_accounting",
    "professional_medicine",
    "virology",
]

def load_gsm8k_test() -> Dataset:
    """Load GSM8K test split."""
    try:
        dataset = load_dataset("gsm8k", "main", split=GSM8K_TEST_SPLIT)
        logger.info(f"Loaded GSM8K test split with {len(dataset)} samples.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load GSM8K test split: {e}")
        raise

def load_mmlu_stem() -> Dataset:
    """Load MMLU STEM subset."""
    all_stem_data = []
    for subject in MMLU_STEM_SUBJECTS:
        try:
            ds = load_dataset("cais/mmlu", subject, split="test")
            all_stem_data.append(ds)
            logger.info(f"Loaded MMLU {subject} with {len(ds)} samples.")
        except Exception as e:
            logger.warning(f"Failed to load MMLU {subject}: {e}")
    
    if not all_stem_data:
        raise RuntimeError("No MMLU STEM datasets could be loaded.")
    
    combined = Dataset.from_list(all_stem_data[0].to_list())
    for ds in all_stem_data[1:]:
        combined = combined.add(ds)
    
    logger.info(f"Combined MMLU STEM dataset has {len(combined)} samples.")
    return combined

def format_gsm8k_question(sample: Dict[str, Any]) -> str:
    """Format GSM8K question for model input."""
    return f"Question: {sample['question']}\nAnswer:"

def format_mmlu_question(sample: Dict[str, Any]) -> str:
    """Format MMLU question for model input."""
    choices = sample["choices"]
    choice_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices)])
    return (
        f"Question: {sample['question']}\n"
        f"Choices:\n{choice_str}\n"
        f"Answer:"
    )

def extract_gsm8k_answer(response: str) -> Optional[str]:
    """Extract the final answer from GSM8K model response."""
    # GSM8K answers typically end with #### <number>
    if "####" in response:
        return response.split("####")[-1].strip()
    return response.strip()

def extract_mmlu_answer(response: str) -> Optional[str]:
    """Extract the final answer choice from MMLU model response."""
    response_upper = response.upper()
    for label in ["A", "B", "C", "D"]:
        if label in response_upper:
            return label
    return None

def evaluate_model_on_gsm8k(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    dataset: Dataset,
    max_samples: Optional[int] = None,
    max_new_tokens: int = 256,
) -> Dict[str, Any]:
    """Evaluate model on GSM8K test set."""
    logger.info("Starting GSM8K evaluation...")
    
    correct = 0
    total = 0
    results = []

    for i, sample in enumerate(dataset):
        if max_samples and i >= max_samples:
            break

        prompt = format_gsm8k_question(sample)
        ground_truth = sample["answer"]
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.0,  # Deterministic for benchmarking
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove prompt from response
        response = response.replace(prompt, "").strip()
        
        predicted = extract_gsm8k_answer(response)
        
        # Compare answers (simplified: check if predicted number is in ground truth)
        is_correct = False
        if predicted and ground_truth:
            # Extract number from ground truth (format: ... #### <number>)
            if "####" in ground_truth:
                gt_num = ground_truth.split("####")[-1].strip()
                is_correct = predicted == gt_num
            
            results.append({
                "question": sample["question"][:100],
                "predicted": predicted,
                "ground_truth": gt_num if "####" in ground_truth else ground_truth,
                "correct": is_correct,
            })
            
            if is_correct:
                correct += 1
        
        total += 1
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{total} GSM8K samples")

    accuracy = correct / total if total > 0 else 0.0
    
    return {
        "dataset": "gsm8k",
        "total_samples": total,
        "correct": correct,
        "accuracy": accuracy,
        "results": results,
    }

def evaluate_model_on_mmlu(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    dataset: Dataset,
    max_samples: Optional[int] = None,
    max_new_tokens: int = 64,
) -> Dict[str, Any]:
    """Evaluate model on MMLU STEM subset."""
    logger.info("Starting MMLU STEM evaluation...")
    
    correct = 0
    total = 0
    results = []

    for i, sample in enumerate(dataset):
        if max_samples and i >= max_samples:
            break

        prompt = format_mmlu_question(sample)
        ground_truth = chr(65 + sample["answer"])  # Convert 0->A, 1->B, etc.
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.0,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.replace(prompt, "").strip()
        
        predicted = extract_mmlu_answer(response)
        
        is_correct = predicted == ground_truth if predicted else False
        
        results.append({
            "question": sample["question"][:100],
            "subject": sample.get("subject", "unknown"),
            "predicted": predicted,
            "ground_truth": ground_truth,
            "correct": is_correct,
        })
        
        if is_correct:
            correct += 1
        
        total += 1
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{total} MMLU samples")

    accuracy = correct / total if total > 0 else 0.0
    
    return {
        "dataset": "mmlu_stem",
        "total_samples": total,
        "correct": correct,
        "accuracy": accuracy,
        "results": results,
    }

def run_benchmark(
    model_path: str,
    output_dir: str,
    use_lora: bool = True,
    lora_path: Optional[str] = None,
    max_samples_gsm8k: Optional[int] = None,
    max_samples_mmlu: Optional[int] = None,
) -> Dict[str, Any]:
    """Run full benchmark suite on GSM8K and MMLU STEM."""
    config = get_config()
    logger.info(f"Starting benchmark with model: {model_path}")
    logger.info(f"Output directory: {output_dir}")

    # Load model and tokenizer
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
    )
    
    # Load LoRA weights if specified
    if use_lora and lora_path:
        logger.info(f"Loading LoRA weights from: {lora_path}")
        model = PeftModel.from_pretrained(model, lora_path)

    model.eval()

    # Load datasets
    gsm8k_dataset = load_gsm8k_test()
    mmlu_dataset = load_mmlu_stem()

    # Run evaluations
    gsm8k_results = evaluate_model_on_gsm8k(
        model,
        tokenizer,
        gsm8k_dataset,
        max_samples=max_samples_gsm8k,
    )
    
    mmlu_results = evaluate_model_on_mmlu(
        model,
        tokenizer,
        mmlu_dataset,
        max_samples=max_samples_mmlu,
    )

    # Compile final results
    final_results = {
        "model_path": model_path,
        "lora_path": lora_path,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gsm8k": gsm8k_results,
        "mmlu_stem": mmlu_results,
        "summary": {
            "gsm8k_accuracy": gsm8k_results["accuracy"],
            "mmlu_stem_accuracy": mmlu_results["accuracy"],
        },
    }

    # Save results to disk
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "benchmark_results.json")
    
    with open(output_path, "w") as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Benchmark results saved to: {output_path}")
    logger.info(f"GSM8K Accuracy: {gsm8k_results['accuracy']:.4f}")
    logger.info(f"MMLU STEM Accuracy: {mmlu_results['accuracy']:.4f}")

    return final_results

def main():
    """Main entry point for benchmark script."""
    config = get_config()
    
    model_path = config.get("model_path", "microsoft/phi-1_5")
    lora_path = config.get("lora_path", None)
    output_dir = config.get("output_dir", "data/results/benchmarks")
    
    max_samples_gsm8k = config.get("max_samples_gsm8k", None)
    max_samples_mmlu = config.get("max_samples_mmlu", None)
    
    try:
        results = run_benchmark(
            model_path=model_path,
            output_dir=output_dir,
            use_lora=(lora_path is not None),
            lora_path=lora_path,
            max_samples_gsm8k=max_samples_gsm8k,
            max_samples_mmlu=max_samples_mmlu,
        )
        
        # Log summary to stdout for quick verification
        print(f"\n=== BENCHMARK SUMMARY ===")
        print(f"GSM8K Accuracy: {results['summary']['gsm8k_accuracy']:.4f}")
        print(f"MMLU STEM Accuracy: {results['summary']['mmlu_stem_accuracy']:.4f}")
        print(f"Results saved to: {output_dir}/benchmark_results.json")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise

if __name__ == "__main__":
    main()