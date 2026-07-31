import os
import sys
import json
import random
import argparse
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from transformers import LlamaForCausalLM, LlamaTokenizer
import torch
from dataclasses import dataclass
from datetime import datetime

from config import get_config
from utils.logging import get_logger, EvaluationError
from models.checkpoint import ModelCheckpoint
from evaluation.results import EvaluationResult
from data_loader import load_manifest, compute_checksum

logger = get_logger(__name__)

@dataclass
class BenchmarkConfig:
    dataset_name: str
    dataset_path: str
    split: str
    prompt_template: str
    answer_key: str
    num_shots: int = 0
    max_tokens: int = 256

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_model_and_tokenizer(model_path: str) -> Tuple[LlamaForCausalLM, LlamaTokenizer]:
    """Load a pre-trained model and tokenizer from a checkpoint."""
    logger.info(f"Loading model from {model_path}")
    
    if not os.path.exists(model_path):
        raise EvaluationError(f"Model checkpoint not found: {model_path}")
    
    try:
        tokenizer = LlamaTokenizer.from_pretrained(model_path)
        model = LlamaForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        model.eval()
        logger.info(f"Model loaded successfully: {model_path}")
        return model, tokenizer
    except Exception as e:
        raise EvaluationError(f"Failed to load model: {e}")

def prepare_gsm8k_prompt(question: str) -> str:
    """Prepare a prompt for GSM8K dataset."""
    return f"Question: {question}\nAnswer:"

def prepare_mmlu_prompt(question: str, choices: List[str]) -> str:
    """Prepare a prompt for MMLU dataset."""
    prompt = f"Question: {question}\n"
    for i, choice in enumerate(choices):
        prompt += f"{chr(65+i)}. {choice}\n"
    prompt += "Answer:"
    return prompt

def generate_reasoning_path(
    model: LlamaForCausalLM,
    tokenizer: LlamaTokenizer,
    prompt: str,
    max_tokens: int = 256
) -> str:
    """Generate a single reasoning path for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt")
    
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the generated part
    generated_part = generated_text[len(prompt):]
    return generated_part.strip()

def parse_gsm8k_answer(generation: str) -> Optional[float]:
    """Parse the answer from a GSM8K generation."""
    # Look for the final answer in the format "#### <number>"
    if "####" in generation:
        try:
            answer_str = generation.split("####")[-1].strip()
            return float(answer_str.replace(",", ""))
        except (ValueError, IndexError):
            return None
    return None

def parse_mmlu_answer(generation: str) -> Optional[str]:
    """Parse the answer from an MMLU generation."""
    # Look for A, B, C, or D in the generation
    generation_upper = generation.upper()
    for option in ["A", "B", "C", "D"]:
        if option in generation_upper:
            return option
    return None

def load_gsm8k_dataset(data_path: str) -> List[Dict[str, Any]]:
    """Load GSM8K dataset from JSON file."""
    if not os.path.exists(data_path):
        raise EvaluationError(f"GSM8K dataset not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def load_mmlu_dataset(data_path: str) -> List[Dict[str, Any]]:
    """Load MMLU dataset from JSON file."""
    if not os.path.exists(data_path):
        raise EvaluationError(f"MMLU dataset not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def run_gsm8k_benchmark(
    model: LlamaForCausalLM,
    tokenizer: LlamaTokenizer,
    dataset: List[Dict[str, Any]],
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Run GSM8K benchmark with single-path inference."""
    logger.info(f"Running GSM8K benchmark on {len(dataset)} samples")
    
    results = []
    samples_to_process = dataset if max_samples is None else dataset[:max_samples]
    
    for i, item in enumerate(samples_to_process):
        question = item.get('question', '')
        expected_answer = item.get('answer', '')
        
        prompt = prepare_gsm8k_prompt(question)
        generation = generate_reasoning_path(model, tokenizer, prompt)
        predicted_answer = parse_gsm8k_answer(generation)
        
        # Parse expected answer (format: "#### <number>")
        expected_parsed = None
        if "####" in expected_answer:
            try:
                expected_parsed = float(expected_answer.split("####")[-1].strip().replace(",", ""))
            except (ValueError, IndexError):
                pass
        
        is_correct = (predicted_answer is not None and 
                     expected_parsed is not None and 
                     abs(predicted_answer - expected_parsed) < 1e-6)
        
        result = {
            'question_id': i,
            'question': question,
            'expected_answer': expected_answer,
            'predicted_answer': predicted_answer,
            'generation': generation,
            'is_correct': is_correct
        }
        results.append(result)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(samples_to_process)} GSM8K samples")
    
    return results

def run_mmlu_benchmark(
    model: LlamaForCausalLM,
    tokenizer: LlamaTokenizer,
    dataset: List[Dict[str, Any]],
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Run MMLU benchmark with single-path inference."""
    logger.info(f"Running MMLU benchmark on {len(dataset)} samples")
    
    results = []
    samples_to_process = dataset if max_samples is None else dataset[:max_samples]
    
    for i, item in enumerate(samples_to_process):
        question = item.get('question', '')
        choices = item.get('choices', [])
        expected_answer_idx = item.get('answer', 0)
        expected_answer = chr(65 + expected_answer_idx) if expected_answer_idx < 26 else None
        
        prompt = prepare_mmlu_prompt(question, choices)
        generation = generate_reasoning_path(model, tokenizer, prompt)
        predicted_answer = parse_mmlu_answer(generation)
        
        is_correct = (predicted_answer is not None and 
                     predicted_answer.upper() == expected_answer.upper() if expected_answer else False)
        
        result = {
            'question_id': i,
            'question': question,
            'choices': choices,
            'expected_answer': expected_answer,
            'predicted_answer': predicted_answer,
            'generation': generation,
            'is_correct': is_correct
        }
        results.append(result)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(samples_to_process)} MMLU samples")
    
    return results

def calculate_accuracy(results: List[Dict[str, Any]]) -> float:
    """Calculate accuracy from benchmark results."""
    if not results:
        return 0.0
    
    correct = sum(1 for r in results if r['is_correct'])
    return correct / len(results)

def save_benchmark_results(results: List[Dict[str, Any]], output_path: str, benchmark_type: str):
    """Save benchmark results to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Benchmark results saved to {output_path}")
    
    # Update manifest
    checksum = compute_checksum(output_path)
    manifest_path = os.path.join(os.path.dirname(output_dir), 'manifest.json')
    
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    
    manifest[output_path] = {
        'checksum': checksum,
        'benchmark_type': benchmark_type,
        'timestamp': datetime.now().isoformat(),
        'num_samples': len(results)
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def main():
    """Main entry point for running MMLU/GSM8K benchmarks."""
    parser = argparse.ArgumentParser(description="Run MMLU/GSM8K benchmarks for accuracy baseline")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--gsm8k_path", type=str, default="data/raw/gsm8k.json", help="Path to GSM8K dataset")
    parser.add_argument("--mmlu_path", type=str, default="data/raw/mmlu.json", help="Path to MMLU dataset")
    parser.add_argument("--gsm8k_output", type=str, default="data/processed/gsm8k_benchmark_results.json", help="Output path for GSM8K results")
    parser.add_argument("--mmlu_output", type=str, default="data/processed/mmlu_benchmark_results.json", help="Output path for MMLU results")
    parser.add_argument("--max_samples", type=int, default=None, help="Maximum number of samples to process (for testing)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    try:
        # Load model and tokenizer
        model, tokenizer = load_model_and_tokenizer(args.model_path)
        
        # Load datasets
        gsm8k_data = load_gsm8k_dataset(args.gsm8k_path)
        mmlu_data = load_mmlu_dataset(args.mmlu_path)
        
        logger.info(f"Loaded {len(gsm8k_data)} GSM8K samples and {len(mmlu_data)} MMLU samples")
        
        # Run benchmarks
        gsm8k_results = run_gsm8k_benchmark(model, tokenizer, gsm8k_data, args.max_samples)
        mmlu_results = run_mmlu_benchmark(model, tokenizer, mmlu_data, args.max_samples)
        
        # Calculate and log accuracies
        gsm8k_accuracy = calculate_accuracy(gsm8k_results)
        mmlu_accuracy = calculate_accuracy(mmlu_results)
        
        logger.info(f"GSM8K Accuracy: {gsm8k_accuracy:.4f} ({gsm8k_accuracy*100:.2f}%)")
        logger.info(f"MMLU Accuracy: {mmlu_accuracy:.4f} ({mmlu_accuracy*100:.2f}%)")
        
        # Save results
        save_benchmark_results(gsm8k_results, args.gsm8k_output, "gsm8k_single_path")
        save_benchmark_results(mmlu_results, args.mmlu_output, "mmlu_single_path")
        
        # Create evaluation result summary
        eval_result = EvaluationResult(
            model_path=args.model_path,
            timestamp=datetime.now().isoformat(),
            metrics={
                'gsm8k_accuracy': gsm8k_accuracy,
                'mmlu_accuracy': mmlu_accuracy,
                'gsm8k_samples': len(gsm8k_results),
                'mmlu_samples': len(mmlu_results)
            },
            raw_results_paths={
                'gsm8k': args.gsm8k_output,
                'mmlu': args.mmlu_output
            }
        )
        
        summary_path = args.gsm8k_output.replace('.json', '_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(eval_result.to_dict(), f, indent=2)
        
        logger.info(f"Evaluation summary saved to {summary_path}")
        logger.info("Benchmark execution completed successfully")
        
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}", exc_info=True)
        raise EvaluationError(f"Failed to run benchmarks: {e}")

if __name__ == "__main__":
    main()