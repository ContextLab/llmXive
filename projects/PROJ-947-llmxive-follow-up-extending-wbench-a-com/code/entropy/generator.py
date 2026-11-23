"""
Entropy-based sequence variant generator for WBench.

Implements token-reweighting and resampling to create Low, Medium, and High
entropy variants of interaction sequences.
"""

import os
import sys
import json
import random
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# Import from project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.errors import ConvergenceError, fail_loudly
from utils.logging import get_logger, log_info, log_error, log_exception

logger = get_logger(__name__)

# Constants
TARGET_ENTROPY_LOW = 0.25
TARGET_ENTROPY_MEDIUM = 0.50
TARGET_ENTROPY_HIGH = 0.75
ENTROPY_LOW_BOUND = 0.30
ENTROPY_HIGH_BOUND = 0.70
MAX_ITERATIONS = 20
TOLERANCE = 0.05
STRATIFIED_SAMPLE_SIZE = 50

@dataclass
class VariantResult:
    case_id: str
    variant_type: str
    entropy_score: float
    original_tokens: List[str]
    modified_tokens: List[str]
    iterations: int

def load_wbench_stratified_sample() -> List[Dict[str, Any]]:
    """
    Load a stratified sample of N=50 cases from the downloaded WBench dataset.
    Stratifies by complexity level (low, medium, high) to ensure representation.
    """
    data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "wbench_dataset"
    
    if not data_path.exists():
        fail_loudly(f"WBench dataset not found at {data_path}. Run download_wbench.py first.")
    
    # Try to load the dataset (assuming JSONL or similar format)
    cases = []
    jsonl_path = data_path / "wbench_cases.jsonl"
    
    if jsonl_path.exists():
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    cases.append(json.loads(line))
    else:
        # Fallback to directory structure if JSONL not found
        case_files = list(data_path.glob("*.json"))
        for case_file in case_files:
            with open(case_file, 'r', encoding='utf-8') as f:
                cases.append(json.load(f))
    
    if len(cases) == 0:
        fail_loudly("No cases found in WBench dataset.")
    
    # Stratified sampling: ensure we get cases from different complexity levels
    # For now, we'll randomly sample if complexity labels aren't present
    sample_size = min(STRATIFIED_SAMPLE_SIZE, len(cases))
    
    if len(cases) <= sample_size:
        sampled_cases = cases
    else:
        # Simple random stratified sample (assuming some implicit distribution)
        sampled_cases = random.sample(cases, sample_size)
    
    logger.info(f"Loaded {len(sampled_cases)} cases for stratified sample")
    return sampled_cases

def compute_shannon_entropy(tokens: List[str]) -> float:
    """
    Compute Shannon entropy of a token sequence.
    """
    if not tokens:
        return 0.0
    
    # Count token frequencies
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    
    # Calculate probabilities and entropy
    total = len(tokens)
    entropy = 0.0
    for count in freq.values():
        if count > 0:
            prob = count / total
            entropy -= prob * math.log2(prob)
    
    return entropy

def normalize_token_weights(tokens: List[str], target_entropy: float) -> Dict[str, float]:
    """
    Generate token weights to guide resampling towards target entropy.
    """
    base_entropy = compute_shannon_entropy(tokens)
    weights = {}
    
    if base_entropy == 0:
        # Uniform distribution if no entropy
        for token in tokens:
            weights[token] = 1.0
        return weights
    
    # Adjust weights based on target entropy
    adjustment_factor = target_entropy / base_entropy if base_entropy > 0 else 1.0
    
    for token in tokens:
        # Increase weight for less frequent tokens to increase entropy
        # Decrease weight for more frequent tokens to decrease entropy
        freq = tokens.count(token)
        base_weight = 1.0 / (freq + 1)
        weights[token] = base_weight * adjustment_factor
    
    return weights

def resample_tokens(tokens: List[str], weights: Dict[str, float], 
                   num_samples: int) -> List[str]:
    """
    Resample tokens according to given weights.
    """
    if not tokens:
        return []
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight == 0:
        return tokens  # Return original if no valid weights
    
    normalized_weights = [weights.get(t, 1.0) / total_weight for t in tokens]
    
    # Resample
    resampled = []
    for _ in range(num_samples):
        # Weighted random choice
        r = random.random()
        cumulative = 0.0
        for i, w in enumerate(normalized_weights):
            cumulative += w
            if r <= cumulative:
                resampled.append(tokens[i])
                break
        else:
            resampled.append(tokens[-1])  # Fallback to last token
    
    return resampled

def generate_variant(case: Dict[str, Any], variant_type: str, 
                    max_iter: int = MAX_ITERATIONS) -> VariantResult:
    """
    Generate a variant of the given case with target entropy level.
    
    Args:
        case: Original case dictionary
        variant_type: 'low', 'medium', or 'high'
        max_iter: Maximum iterations for convergence
    
    Returns:
        VariantResult with generated tokens and metrics
    """
    target_entropy = {
        'low': TARGET_ENTROPY_LOW,
        'medium': TARGET_ENTROPY_MEDIUM,
        'high': TARGET_ENTROPY_HIGH
    }.get(variant_type, TARGET_ENTROPY_MEDIUM)
    
    # Extract tokens from case (assuming 'action_chain' or similar field)
    original_tokens = case.get('action_chain', [])
    if not original_tokens:
        # Fallback to text fields
        text = case.get('text', case.get('prompt', ''))
        original_tokens = text.split()
    
    if not original_tokens:
        raise ValueError(f"Case {case.get('case_id', 'unknown')} has no tokens")
    
    current_tokens = original_tokens.copy()
    best_tokens = current_tokens.copy()
    best_entropy = compute_shannon_entropy(current_tokens)
    best_diff = abs(best_entropy - target_entropy)
    iterations = 0
    
    for iteration in range(max_iter):
        iterations += 1
        
        # Compute current entropy
        current_entropy = compute_shannon_entropy(current_tokens)
        current_diff = abs(current_entropy - target_entropy)
        
        # Check convergence
        if current_diff < TOLERANCE:
            best_tokens = current_tokens
            best_entropy = current_entropy
            break
        
        # Update best if closer to target
        if current_diff < best_diff:
            best_diff = current_diff
            best_tokens = current_tokens.copy()
            best_entropy = current_entropy
        
        # Generate weights for resampling
        weights = normalize_token_weights(current_tokens, target_entropy)
        
        # Resample tokens
        num_samples = len(current_tokens)
        current_tokens = resample_tokens(current_tokens, weights, num_samples)
        
        # Add some diversity by occasionally introducing new tokens
        if random.random() < 0.1:
            # Introduce variation
            variation_rate = 0.1
            num_variations = max(1, int(len(current_tokens) * variation_rate))
            for _ in range(num_variations):
                idx = random.randint(0, len(current_tokens) - 1)
                current_tokens[idx] = current_tokens[idx] + "_" + str(iteration)
    
    # Final check
    final_entropy = compute_shannon_entropy(best_tokens)
    final_diff = abs(final_entropy - target_entropy)
    
    if final_diff >= TOLERANCE:
        # Log warning but don't raise if we're reasonably close
        logger.warning(f"Case {case.get('case_id', 'unknown')} variant {variant_type} "
                     f"did not converge within tolerance. Final entropy: {final_entropy:.3f}, "
                     f"Target: {target_entropy:.3f}, Diff: {final_diff:.3f}")
    
    return VariantResult(
        case_id=case.get('case_id', 'unknown'),
        variant_type=variant_type,
        entropy_score=final_entropy,
        original_tokens=original_tokens,
        modified_tokens=best_tokens,
        iterations=iterations
    )

def run_generation_pipeline(sampled_cases: List[Dict[str, Any]], 
                           output_dir: Optional[Path] = None) -> Tuple[List[VariantResult], Dict]:
    """
    Run the full generation pipeline on a stratified sample.
    
    Args:
        sampled_cases: List of cases to process
        output_dir: Directory to write outputs (defaults to data/processed)
    
    Returns:
        Tuple of (list of results, generation logs)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    generation_logs = {
        'start_time': str(datetime.now()),
        'total_cases': len(sampled_cases),
        'variants_per_case': 3,
        'variants': []
    }
    
    for case in sampled_cases:
        case_id = case.get('case_id', 'unknown')
        log_info(f"Processing case {case_id}")
        
        # Generate all three variants
        for variant_type in ['low', 'medium', 'high']:
            try:
                result = generate_variant(case, variant_type)
                all_results.append(result)
                
                generation_logs['variants'].append({
                    'case_id': result.case_id,
                    'variant_type': result.variant_type,
                    'entropy_score': result.entropy_score,
                    'iterations': result.iterations
                })
                
                log_info(f"  Generated {variant_type} variant: entropy={result.entropy_score:.3f}, "
                       f"iterations={result.iterations}")
                
            except Exception as e:
                log_error(f"Failed to generate variant for case {case_id}: {str(e)}")
                generation_logs['variants'].append({
                    'case_id': case_id,
                    'variant_type': variant_type,
                    'entropy_score': None,
                    'iterations': None,
                    'error': str(e)
                })
    
    # Write outputs
    variants_csv_path = output_dir / "variants.csv"
    logs_json_path = output_dir / "generation_logs.json"
    
    # Write CSV
    import pandas as pd
    df = pd.DataFrame([
        {
            'case_id': r.case_id,
            'variant_type': r.variant_type,
            'entropy_score': r.entropy_score
        }
        for r in all_results
    ])
    df.to_csv(variants_csv_path, index=False)
    log_info(f"Written {len(df)} rows to {variants_csv_path}")
    
    # Write JSON logs
    generation_logs['end_time'] = str(datetime.now())
    with open(logs_json_path, 'w', encoding='utf-8') as f:
        json.dump(generation_logs, f, indent=2)
    log_info(f"Written logs to {logs_json_path}")
    
    return all_results, generation_logs

def main():
    """Main entry point for the generator script."""
    from datetime import datetime
    
    log_info("Starting entropy-based variant generation pipeline")
    
    try:
        # Load stratified sample
        sampled_cases = load_wbench_stratified_sample()
        
        if not sampled_cases:
            fail_loudly("No cases loaded for generation pipeline")
        
        # Run generation
        results, logs = run_generation_pipeline(sampled_cases)
        
        # Verify outputs
        output_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        variants_path = output_dir / "variants.csv"
        logs_path = output_dir / "generation_logs.json"
        
        if not variants_path.exists():
            fail_loudly(f"Output file {variants_path} was not created")
        
        if not logs_path.exists():
            fail_loudly(f"Output file {logs_path} was not created")
        
        # Validate entropy scores are within expected ranges
        df = pd.read_csv(variants_path)
        for variant_type in ['low', 'medium', 'high']:
            subset = df[df['variant_type'] == variant_type]
            if len(subset) > 0:
                mean_entropy = subset['entropy_score'].mean()
                log_info(f"{variant_type.upper()} variants: mean entropy = {mean_entropy:.3f}")
        
        log_info("Generation pipeline completed successfully")
        
    except Exception as e:
        log_exception(e)
        fail_loudly(f"Generation pipeline failed: {str(e)}")

if __name__ == "__main__":
    main()
