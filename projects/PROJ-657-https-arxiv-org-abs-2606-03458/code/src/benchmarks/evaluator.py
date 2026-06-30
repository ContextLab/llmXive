"""
Evaluator module for calculating exact-match accuracy on reasoning benchmarks.

This module implements the evaluation logic for User Story 2, calculating
exact-match accuracy between model generations and ground truth answers
for datasets like MATH500, AIME, HumanEval, and IFEval.
"""

import json
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from src.benchmarks.loader import load_dataset_by_name


def normalize_answer(answer: str) -> str:
    """
    Normalize an answer string for exact matching.
    
    Removes leading/trailing whitespace, converts to lowercase,
    and strips common LaTeX delimiters or markdown formatting.
    
    Args:
        answer: The raw answer string from model or ground truth.
        
    Returns:
        Normalized answer string.
    """
    if not answer:
        return ""
        
    # Strip whitespace
    answer = answer.strip().lower()
    
    # Remove common LaTeX delimiters
    delimiters = [r'\[', r'\]', r'\(', r'\)', '$$', '$', r'\{', r'\}']
    for delim in delimiters:
        answer = answer.replace(delim, '')
        
    # Remove markdown code blocks
    if answer.startswith('```'):
        answer = answer[3:]
    if answer.endswith('```'):
        answer = answer[:-3]
        
    return answer.strip()


def extract_answer_from_generation(generation: str, dataset_type: str) -> Optional[str]:
    """
    Extract the final answer from a model generation.
    
    For reasoning datasets, models often include chain-of-thought before
    the final answer. This function attempts to extract the final answer.
    
    Args:
        generation: The full model generation string.
        dataset_type: The type of dataset (e.g., 'math', 'humaneval', 'ifeval').
        
    Returns:
        Extracted answer string or None if extraction fails.
    """
    if not generation:
        return None
        
    # For HumanEval, we typically expect code completion
    if dataset_type == 'humaneval':
        # Return the code block if present
        if '```python' in generation:
            start = generation.find('```python') + len('```python')
            end = generation.find('```', start)
            if end != -1:
                return generation[start:end].strip()
        return generation.strip()
        
    # For math datasets, look for common answer patterns
    if dataset_type in ['math', 'aime']:
        # Look for boxed answer
        if r'\boxed{' in generation:
            start = generation.find(r'\boxed{') + len(r'\boxed{')
            depth = 1
            end = start
            while end < len(generation) and depth > 0:
                if generation[end] == '{':
                    depth += 1
                elif generation[end] == '}':
                    depth -= 1
                end += 1
            return generation[start:end-1].strip()
        
        # Look for "The answer is" pattern
        if 'the answer is' in generation.lower():
            parts = generation.lower().split('the answer is')
            if len(parts) > 1:
                return parts[-1].strip()
                
    # For IFEval, return the full generation as instructions vary
    if dataset_type == 'ifeval':
        return generation.strip()
        
    # Default: return the last non-empty line
    lines = [l.strip() for l in generation.strip().split('\n') if l.strip()]
    return lines[-1] if lines else None


def calculate_exact_match_accuracy(
    generations: List[str],
    ground_truths: List[str],
    dataset_type: str
) -> float:
    """
    Calculate exact-match accuracy between generations and ground truths.
    
    Args:
        generations: List of model generation strings.
        ground_truths: List of ground truth answer strings.
        dataset_type: Type of dataset for answer extraction logic.
        
    Returns:
        Accuracy as a float between 0.0 and 1.0.
        
    Raises:
        ValueError: If generations and ground_truths have different lengths.
    """
    if len(generations) != len(ground_truths):
        raise ValueError(
            f"Length mismatch: {len(generations)} generations vs "
            f"{len(ground_truths)} ground truths"
        )
        
    if len(generations) == 0:
        return 0.0
        
    matches = 0
    for gen, gt in zip(generations, ground_truths):
        extracted = extract_answer_from_generation(gen, dataset_type)
        if extracted is None:
            extracted = gen.strip()
            
        norm_gen = normalize_answer(extracted)
        norm_gt = normalize_answer(gt)
        
        if norm_gen == norm_gt and norm_gen != "":
            matches += 1
            
    return matches / len(generations)


def evaluate_benchmark(
    dataset_name: str,
    quantizer_type: str,
    outputs_path: str,
    results_path: str,
    num_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run evaluation on a benchmark dataset and log results.
    
    This function loads a dataset, runs evaluation on the provided
    generations (from outputs_path), calculates accuracy metrics,
    and logs the results to the specified results file.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'math_dataset', 'humaneval').
        quantizer_type: Type of quantizer used ('kvarn' or 'uniform').
        outputs_path: Path to JSONL file with generations and ground truths.
        results_path: Path to save the results summary JSONL.
        num_samples: Optional limit on number of samples to evaluate.
        
    Returns:
        Dictionary containing evaluation metrics.
        
    Raises:
        FileNotFoundError: If outputs_path does not exist.
    """
    # Determine dataset type from name
    dataset_type = 'math'  # default
    if 'math' in dataset_name.lower():
        dataset_type = 'math'
    elif 'aime' in dataset_name.lower():
        dataset_type = 'aime'
    elif 'human' in dataset_name.lower() or 'eval' in dataset_name.lower():
        dataset_type = 'humaneval'
    elif 'ifeval' in dataset_name.lower():
        dataset_type = 'ifeval'
        
    # Load generations from outputs file
    if not os.path.exists(outputs_path):
        raise FileNotFoundError(f"Outputs file not found: {outputs_path}")
        
    generations = []
    ground_truths = []
    sample_ids = []
    
    with open(outputs_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if num_samples is not None and i >= num_samples:
                break
            data = json.loads(line)
            generations.append(data.get('generation', ''))
            ground_truths.append(data.get('ground_truth', ''))
            sample_ids.append(data.get('id', str(i)))
            
    if len(generations) == 0:
        return {
            'dataset': dataset_name,
            'quantizer': quantizer_type,
            'num_samples': 0,
            'accuracy': 0.0,
            'error': 'No samples found in outputs file'
        }
        
    # Calculate accuracy
    accuracy = calculate_exact_match_accuracy(
        generations, ground_truths, dataset_type
    )
    
    # Calculate per-sample accuracy for detailed logging
    per_sample_results = []
    matches = 0
    for i, (gen, gt) in enumerate(zip(generations, ground_truths)):
        extracted = extract_answer_from_generation(gen, dataset_type)
        if extracted is None:
            extracted = gen.strip()
            
        norm_gen = normalize_answer(extracted)
        norm_gt = normalize_answer(gt)
        is_match = (norm_gen == norm_gt and norm_gen != "")
        if is_match:
            matches += 1
            
        per_sample_results.append({
            'sample_id': sample_ids[i],
            'is_correct': is_match,
            'generation': gen[:200] + '...' if len(gen) > 200 else gen,
            'ground_truth': gt,
            'normalized_generation': norm_gen,
            'normalized_ground_truth': norm_gt
        })
        
    # Prepare result summary
    result = {
        'dataset': dataset_name,
        'dataset_type': dataset_type,
        'quantizer': quantizer_type,
        'num_samples': len(generations),
        'accuracy': accuracy,
        'num_correct': matches,
        'timestamp': None,  # Will be set by caller if needed
        'per_sample_results': per_sample_results
    }
    
    # Log results to file
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'a', encoding='utf-8') as f:
        # Remove per_sample_results for the summary line (too large)
        summary_result = {k: v for k, v in result.items() 
                         if k != 'per_sample_results'}
        f.write(json.dumps(summary_result) + '\n')
        
    # Also save detailed per-sample results
    detailed_path = results_path.replace('.jsonl', '_detailed.jsonl')
    with open(detailed_path, 'w', encoding='utf-8') as f:
        for sample_result in per_sample_results:
            f.write(json.dumps(sample_result) + '\n')
            
    return result


def evaluate_multiple_benchmarks(
    datasets: List[str],
    quantizer_type: str,
    outputs_dir: str,
    results_dir: str,
    num_samples_per_dataset: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Evaluate multiple benchmark datasets and aggregate results.
    
    Args:
        datasets: List of dataset names to evaluate.
        quantizer_type: Type of quantizer used.
        outputs_dir: Directory containing output generation files.
        results_dir: Directory to save results.
        num_samples_per_dataset: Optional limit per dataset.
        
    Returns:
        List of result dictionaries for each dataset.
    """
    all_results = []
    
    for dataset_name in datasets:
        # Construct expected output file path
        outputs_path = os.path.join(
            outputs_dir, 
            f"{dataset_name}_{quantizer_type}_outputs.jsonl"
        )
        
        # Construct result file path
        results_path = os.path.join(
            results_dir,
            f"{dataset_name}_{quantizer_type}_results.jsonl"
        )
        
        try:
            result = evaluate_benchmark(
                dataset_name=dataset_name,
                quantizer_type=quantizer_type,
                outputs_path=outputs_path,
                results_path=results_path,
                num_samples=num_samples_per_dataset
            )
            all_results.append(result)
        except FileNotFoundError as e:
            all_results.append({
                'dataset': dataset_name,
                'quantizer': quantizer_type,
                'error': str(e),
                'accuracy': None
            })
            
    return all_results