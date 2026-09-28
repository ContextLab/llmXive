"""
Token-reweighting and resampling algorithm to create Low, Medium, and High entropy variants.

Generates stratified variants of WBench interaction sequences targeting specific entropy ranges:
- Low: < 0.3
- Medium: 0.3 - 0.7
- High: > 0.7

Uses iterative resampling with convergence checks.
"""
import os
import sys
import json
import random
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import pandas as pd
import numpy as np

# Import from project utilities
from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import ConvergenceError, fail_loudly, assert_no_synthetic_fallback
from config import get_config
from entropy.scorer import compute_shannon_entropy

logger = get_logger(__name__)

# Constants
TARGET_RANGES = {
    'low': (0.0, 0.3),
    'medium': (0.3, 0.7),
    'high': (0.7, 1.0)
}
MAX_ITERATIONS = 20
CONVERGENCE_THRESHOLD = 0.01
STRATIFIED_SAMPLE_SIZE = 50

class ConvergenceError(Exception):
    """Raised when variant generation fails to converge within max iterations."""
    pass

def _tokenize_chain(action_chain: str) -> List[str]:
    """Simple tokenization of action chain by splitting on common delimiters."""
    if not action_chain or not isinstance(action_chain, str):
        return []
    # Split by common action separators
    tokens = action_chain.replace(',', ' ').replace(';', ' ').replace('.', ' ').split()
    return [t.strip() for t in tokens if t.strip()]

def _reweight_tokens(tokens: List[str], reweight_factor: float) -> List[str]:
    """
    Reweight tokens to increase or decrease entropy.
    
    Args:
        tokens: List of action tokens
        reweight_factor: >1.0 increases entropy (more variety), <1.0 decreases (more repetition)
    
    Returns:
        Reweighted token list
    """
    if not tokens:
        return []
    
    token_counts = Counter(tokens)
    total = len(tokens)
    
    # Calculate probability distribution
    probs = {t: c / total for t, c in token_counts.items()}
    
    # Adjust probabilities based on reweight factor
    adjusted_probs = {}
    for token, prob in probs.items():
        if reweight_factor > 1.0:
            # Increase entropy: flatten distribution slightly
            adjusted_probs[token] = prob ** (1.0 / reweight_factor)
        else:
            # Decrease entropy: sharpen distribution
            adjusted_probs[token] = prob ** reweight_factor
    
    # Normalize
    total_adj = sum(adjusted_probs.values())
    adjusted_probs = {k: v / total_adj for k, v in adjusted_probs.items()}
    
    # Resample tokens based on adjusted probabilities
    new_tokens = []
    for _ in range(total):
        r = random.random()
        cumulative = 0.0
        for token, prob in adjusted_probs.items():
            cumulative += prob
            if r <= cumulative:
                new_tokens.append(token)
                break
        else:
            new_tokens.append(list(adjusted_probs.keys())[-1])
    
    return new_tokens

def _chain_to_string(tokens: List[str]) -> str:
    """Convert token list back to action chain string."""
    return ' '.join(tokens)

def _adjust_entropy(current_entropy: float, target_range: Tuple[float, float]) -> float:
    """
    Calculate reweight factor to move entropy toward target.
    
    Args:
        current_entropy: Current Shannon entropy
        target_range: (min, max) target range
    
    Returns:
        Reweight factor to apply
    """
    target_mid = (target_range[0] + target_range[1]) / 2.0
    current_mid = (target_range[0] + target_range[1]) / 2.0 if current_entropy < target_range[0] or current_entropy > target_range[1] else current_entropy
    
    if current_entropy == target_mid:
        return 1.0
    
    # Calculate direction and magnitude
    if current_entropy < target_range[0]:
        # Need to increase entropy
        factor = 1.0 + (target_range[0] - current_entropy) * 2.0
    elif current_entropy > target_range[1]:
        # Need to decrease entropy
        factor = 1.0 - (current_entropy - target_range[1]) * 2.0
    else:
        # Already in range, minor adjustment toward center
        if current_entropy < target_mid:
            factor = 1.0 + (target_mid - current_entropy) * 0.5
        else:
            factor = 1.0 - (current_entropy - target_mid) * 0.5
    
    # Clamp factor to reasonable bounds
    return max(0.5, min(2.0, factor))

def generate_variant(
    case_id: str,
    base_chain: str,
    variant_type: str,
    max_iter: int = MAX_ITERATIONS
) -> Tuple[str, float, int]:
    """
    Generate a variant of the base chain with target entropy characteristics.
    
    Args:
        case_id: Identifier for the base case
        base_chain: Original action chain string
        variant_type: 'low', 'medium', or 'high'
        max_iter: Maximum iterations for convergence (default 20)
    
    Returns:
        Tuple of (generated_chain, entropy_score, iterations_used)
    
    Raises:
        ConvergenceError: If convergence not achieved within max_iter
    """
    if variant_type not in TARGET_RANGES:
        fail_loudly(f"Invalid variant_type: {variant_type}. Must be one of {list(TARGET_RANGES.keys())}")
    
    target_range = TARGET_RANGES[variant_type]
    tokens = _tokenize_chain(base_chain)
    
    if not tokens:
        fail_loudly(f"Case {case_id}: Empty token chain for variant generation")
    
    current_tokens = tokens.copy()
    iteration = 0
    best_chain = _chain_to_string(current_tokens)
    best_entropy = compute_shannon_entropy(current_tokens)
    converged = False
    
    while iteration < max_iter:
        current_entropy = compute_shannon_entropy(current_tokens)
        
        # Check convergence
        if target_range[0] <= current_entropy <= target_range[1]:
            converged = True
            best_chain = _chain_to_string(current_tokens)
            best_entropy = current_entropy
            break
        
        # Calculate adjustment
        reweight_factor = _adjust_entropy(current_entropy, target_range)
        current_tokens = _reweight_tokens(current_tokens, reweight_factor)
        
        iteration += 1
        
        # Track best result
        if target_range[0] <= current_entropy <= target_range[1]:
            best_chain = _chain_to_string(current_tokens)
            best_entropy = current_entropy
            converged = True
            break
    
    if not converged:
        raise ConvergenceError(
            f"Case {case_id} ({variant_type}): Failed to converge after {max_iter} iterations. "
            f"Final entropy: {current_entropy:.4f}, Target: {target_range}"
        )
    
    return best_chain, best_entropy, iteration

def load_wbench_stratified_sample(
    input_path: str,
    sample_size: int = STRATIFIED_SAMPLE_SIZE,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Load WBench data and create a stratified sample.
    
    Args:
        input_path: Path to input WBench CSV
        sample_size: Number of cases to sample
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with stratified sample
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    if not os.path.exists(input_path):
        fail_loudly(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Simple stratification by case complexity if available, otherwise random
    if 'complexity' in df.columns:
        # Stratify by complexity bins
        df['complexity_bin'] = pd.cut(df['complexity'], bins=3, labels=['low', 'medium', 'high'])
        stratified = df.groupby('complexity_bin', group_keys=False).apply(
            lambda x: x.sample(n=min(sample_size // 3, len(x)), random_state=seed)
        )
    else:
        # Random sample if no complexity column
        stratified = df.sample(n=sample_size, random_state=seed)
    
    return stratified

def run_generation_pipeline(
    input_path: str,
    output_csv_path: str,
    output_logs_path: str,
    sample_size: int = STRATIFIED_SAMPLE_SIZE,
    seed: Optional[int] = None
) -> None:
    """
    Run the full variant generation pipeline.
    
    Args:
        input_path: Path to input WBench dataset
        output_csv_path: Path for output variants CSV
        output_logs_path: Path for generation logs JSON
        sample_size: Number of cases to process
        seed: Random seed for reproducibility
    """
    log_info("Starting variant generation pipeline")
    
    # Load stratified sample
    sample_df = load_wbench_stratified_sample(input_path, sample_size, seed)
    log_info(f"Loaded {len(sample_df)} cases for stratified sampling")
    
    results = []
    logs = {
        'timestamp': str(pd.Timestamp.now()),
        'sample_size': len(sample_df),
        'variants_generated': [],
        'convergence_failures': []
    }
    
    for idx, row in sample_df.iterrows():
        case_id = row.get('case_id', row.get('id', f'case_{idx}'))
        base_chain = row.get('action_chain', row.get('generated_chain', ''))
        
        if not base_chain:
            log_error(f"Skipping {case_id}: No action chain found")
            continue
        
        for variant_type in ['low', 'medium', 'high']:
            try:
                generated_chain, entropy_score, iterations = generate_variant(
                    case_id, base_chain, variant_type
                )
                
                results.append({
                    'case_id': case_id,
                    'variant_type': variant_type,
                    'entropy_score': round(entropy_score, 4),
                    'generated_chain': generated_chain,
                    'iterations': iterations
                })
                
                logs['variants_generated'].append({
                    'case_id': case_id,
                    'variant_type': variant_type,
                    'entropy_score': round(entropy_score, 4),
                    'iterations': iterations,
                    'converged': True
                })
                
                log_info(f"Generated {variant_type} variant for {case_id}: entropy={entropy_score:.4f}, iterations={iterations}")
                
            except ConvergenceError as e:
                log_error(str(e))
                logs['convergence_failures'].append({
                    'case_id': case_id,
                    'variant_type': variant_type,
                    'error': str(e)
                })
                # Continue with other variants even if one fails
    
    # Write outputs
    if results:
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_csv_path, index=False)
        log_info(f"Wrote {len(output_df)} variants to {output_csv_path}")
    else:
        fail_loudly("No variants generated - pipeline failed")
    
    # Write logs
    with open(output_logs_path, 'w') as f:
        json.dump(logs, f, indent=2)
    log_info(f"Wrote generation logs to {output_logs_path}")
    
    # Verify output variance
    if len(output_df) > 0:
        variance = output_df['entropy_score'].var()
        if variance < 0.05:
            log_error(f"WARNING: Variance of complexity scores ({variance:.4f}) is below threshold (0.05)")
        else:
            log_info(f"Variance check passed: {variance:.4f}")

def main():
    """Main entry point for the generator script."""
    config = get_config()
    input_path = config.get('wbench_data_path', 'data/raw/wbench.csv')
    output_csv = config.get('variants_output_path', 'data/processed/variants.csv')
    output_logs = config.get('generation_logs_path', 'data/processed/generation_logs.json')
    sample_size = config.get('stratified_sample_size', STRATIFIED_SAMPLE_SIZE)
    seed = config.get('random_seed', 42)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(output_logs), exist_ok=True)
    
    run_generation_pipeline(
        input_path=input_path,
        output_csv_path=output_csv,
        output_logs_path=output_logs,
        sample_size=sample_size,
        seed=seed
    )

if __name__ == '__main__':
    main()
