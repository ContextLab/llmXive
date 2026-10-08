"""
LLM code generation module.

This module handles loading language models, creating prompts, generating
code solutions, and saving results. It is designed to work with CPU-tractable
models as specified in the project constraints.

Key Functions:
    - load_model_and_tokenizer: Load model with fallback strategies
    - create_prompt: Format problem into model prompt
    - generate_solution: Generate code solution for a problem
    - process_dataset: Iterate over dataset and generate solutions
    - save_results: Save generated solutions to JSON

Model Strategy:
    - Primary: TinyLlama (CPU-tractable)
    - Attempts 8-bit loading first, falls back to float16
    - Does NOT fallback to larger models (Phi-2 is too large per Plan.md)

Usage:
    from generate import process_dataset, save_results
    results = process_dataset('mbpp', split='test', n_samples=30)
    save_results(results, 'data/processed/generated_solutions.json')
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

from config import (
    MODEL_NAME,
    MODEL_MAX_LENGTH,
    GENERATION_TEMPERATURE,
    GENERATION_MAX_NEW_TOKENS,
    RANDOM_SEED,
    DATA_PROCESSED_DIR
)


def load_model_and_tokenizer(
    model_name: Optional[str] = None,
    use_8bit: bool = True
) -> Tuple[Any, Any]:
    """
    Load model and tokenizer with fallback strategies.

    Args:
        model_name: Model name to load. Defaults to config.MODEL_NAME.
        use_8bit: Attempt 8-bit loading first.

    Returns:
        Tuple[Model, Tokenizer]: Loaded model and tokenizer.

    Raises:
        RuntimeError: If model loading fails completely.
    """
    if model_name is None:
        model_name = MODEL_NAME

    print(f"Loading model: {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )

    # Set pad token if not set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Try 8-bit loading first
    if use_8bit:
        try:
            import bitsandbytes
            print("Attempting 8-bit loading...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                load_in_8bit=True,
                device_map="auto",
                trust_remote_code=True
            )
            return model, tokenizer
        except ImportError:
            print("bitsandbytes not available, falling back to float16")
        except Exception as e:
            print(f"8-bit loading failed: {e}, falling back to float16")

    # Fallback to float16
    print("Loading with float16...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        trust_remote_code=True
    )

    return model, tokenizer


def create_prompt(problem: Dict[str, Any]) -> str:
    """
    Create a prompt for code generation from a problem.

    Args:
        problem: Problem dictionary with 'prompt' and 'test' fields.

    Returns:
        str: Formatted prompt string.
    """
    prompt_text = problem.get('prompt', '')
    test_text = problem.get('test', '')

    # Format prompt
    full_prompt = f"""Complete the following Python function:

{prompt_text}

Test cases:
{test_text}

Provide only the function implementation:
"""

    return full_prompt


def generate_solution(
    model: Any,
    tokenizer: Any,
    problem: Dict[str, Any],
    max_new_tokens: int = GENERATION_MAX_NEW_TOKENS
) -> str:
    """
    Generate a code solution for a problem.

    Args:
        model: Loaded model.
        tokenizer: Loaded tokenizer.
        problem: Problem dictionary.
        max_new_tokens: Maximum tokens to generate.

    Returns:
        str: Generated code solution.
    """
    prompt = create_prompt(problem)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MODEL_MAX_LENGTH)

    # Move to device
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=GENERATION_TEMPERATURE,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id
        )

    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract code (remove prompt)
    code = generated_text[len(prompt):].strip()

    return code


def process_dataset(
    dataset_name: str,
    split: str = 'test',
    n_samples: Optional[int] = None,
    seed: int = RANDOM_SEED
) -> List[Dict[str, Any]]:
    """
    Process a dataset and generate solutions for problems.

    Args:
        dataset_name: Name of the dataset.
        split: Dataset split.
        n_samples: Number of samples to process. None for all.
        seed: Random seed.

    Returns:
        List[Dict]: List of results with problem info and generated code.
    """
    import random
    random.seed(seed)

    print(f"Loading dataset: {dataset_name} (split={split})")
    ds = load_dataset(dataset_name, split=split, trust_remote_code=True)

    # Sample if needed
    if n_samples:
        indices = random.sample(range(len(ds)), min(n_samples, len(ds)))
        ds = ds.select(indices)

    # Load model
    model, tokenizer = load_model_and_tokenizer()

    results = []
    for i, problem in enumerate(ds):
        print(f"Processing problem {i+1}/{len(ds)}")

        try:
            solution = generate_solution(model, tokenizer, problem)
            results.append({
                'problem_id': problem.get('task_id', i),
                'prompt': problem.get('prompt', ''),
                'test': problem.get('test', ''),
                'solution': solution,
                'source_type': 'LLM',
                'generation_time': time.time()
            })
        except Exception as e:
            print(f"Error generating solution for problem {i}: {e}")
            results.append({
                'problem_id': problem.get('task_id', i),
                'prompt': problem.get('prompt', ''),
                'test': problem.get('test', ''),
                'solution': None,
                'source_type': 'LLM',
                'error': str(e)
            })

    return results


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save generation results to a JSON file.

    Args:
        results: List of result dictionaries.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} results to {output_path}")


def main():
    """
    Main entry point for code generation.

    Generates solutions for a sample of MBPP problems.
    """
    dataset_name = 'mbpp'
    split = 'test'
    n_samples = 5  # Small sample for testing

    output_path = os.path.join(DATA_PROCESSED_DIR, 'generated_solutions.json')

    try:
        results = process_dataset(dataset_name, split, n_samples)
        save_results(results, output_path)

        # Count successes
        successes = sum(1 for r in results if r.get('solution'))
        print(f"Generated {successes}/{len(results)} successful solutions")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()