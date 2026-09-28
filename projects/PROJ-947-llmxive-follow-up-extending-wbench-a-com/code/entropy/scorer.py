import math
import os
import json
import pandas as pd
from collections import Counter
from typing import Any, Dict, List, Union, Optional
from pathlib import Path

# Import logging utilities from project structure
from utils.logging import get_logger, log_info, log_error, log_exception

# Import error handling utilities
from utils.errors import fail_loudly, DataValidationError

logger = get_logger(__name__)

# Constants
COMPLEXITY_SCORE_FILE = "data/processed/complexity_scores.csv"
VARIANTS_FILE = "data/processed/variants.csv"
VALIDITY_FILE = "data/processed/validity_flags.csv"

def compute_shannon_entropy(text: str) -> float:
    """
    Compute Shannon entropy of a text string.
    
    Args:
        text: Input text string
        
    Returns:
        Shannon entropy value (normalized to [0, 1] range based on character set)
    """
    if not text:
        return 0.0
    
    # Count character frequencies
    counter = Counter(text)
    total_chars = len(text)
    
    # Calculate entropy
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            probability = count / total_chars
            entropy -= probability * math.log2(probability)
    
    # Normalize by log2 of possible character set size (approx 256 for ASCII)
    # This ensures entropy is in a reasonable range
    max_entropy = math.log2(256)  # Assuming extended ASCII
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return min(1.0, max(0.0, normalized_entropy))

def compute_dependency_depth(action_chain: str) -> int:
    """
    Compute dependency graph depth from the original semantic intent.
    
    CRITICAL: This function MUST derive depth from the original semantic intent
    of the base case, NOT the generated text, to avoid circular correlation.
    
    Args:
        action_chain: String representation of the action chain from original intent
        
    Returns:
        Integer depth >= 1 representing the dependency graph depth
    """
    if not action_chain or not isinstance(action_chain, str):
        fail_loudly("Invalid action chain provided to compute_dependency_depth")
    
    # Parse the action chain to determine dependency depth
    # Actions are typically separated by delimiters like ' -> ', ' | ', or newlines
    # We'll use a heuristic based on action sequence complexity
    
    # Clean and split the action chain
    separators = [' -> ', ' | ', ' then ', ' and ', ';', '\n']
    actions = [action_chain]
    
    for sep in separators:
        if sep in action_chain:
            actions = [a.strip() for a in action_chain.split(sep) if a.strip()]
            break
    
    # If no separators found, treat as single action
    if len(actions) == 1 and not separators[0] in action_chain:
        # Check for other common patterns
        if ',' in action_chain:
            actions = [a.strip() for a in action_chain.split(',') if a.strip()]
    
    # Calculate depth based on action sequence
    # Depth 1: Single atomic action
    # Depth 2: Simple sequence (A then B)
    # Depth 3+: Complex nested dependencies
    
    num_actions = len(actions)
    
    # Heuristic: depth increases with action count and complexity
    # Base depth is 1 for any valid action chain
    depth = 1
    
    if num_actions > 1:
        # Simple sequence adds depth
        depth = min(10, num_actions)  # Cap at 10 for practical purposes
        
        # Check for nested/conditional patterns
        if any('if' in action.lower() or 'when' in action.lower() for action in actions):
            depth += 1
        if any('and' in action.lower() or 'or' in action.lower() for action in actions):
            depth += 1
        
        # Ensure minimum depth of 1
        depth = max(1, depth)
    
    return int(depth)

def compute_complexity_score(entropy: float, depth: int) -> float:
    """
    Compute the combined Sequence Complexity Score.
    
    The complexity score is a weighted combination of entropy and dependency depth.
    Formula: complexity_score = 0.6 * entropy + 0.4 * (depth / max_depth)
    
    Args:
        entropy: Shannon entropy value (0-1)
        depth: Dependency graph depth (integer >= 1)
        
    Returns:
        Combined complexity score (0-1 range)
    """
    if not (0.0 <= entropy <= 1.0):
        log_error(f"Entropy value {entropy} out of expected range [0, 1]")
        entropy = max(0.0, min(1.0, entropy))
    
    if depth < 1:
        fail_loudly(f"Dependency depth must be >= 1, got {depth}")
    
    # Normalize depth (assuming max reasonable depth is 10)
    max_depth = 10
    normalized_depth = min(depth, max_depth) / max_depth
    
    # Weighted combination: 60% entropy, 40% depth
    complexity_score = 0.6 * entropy + 0.4 * normalized_depth
    
    return round(complexity_score, 6)

def validate_complexity_scores(df: pd.DataFrame) -> bool:
    """
    Validate that complexity scores meet requirements.
    
    Args:
        df: DataFrame with complexity score columns
        
    Returns:
        True if validation passes, False otherwise
    """
    required_columns = ['case_id', 'variant_type', 'entropy', 'depth', 'complexity_score']
    
    # Check required columns exist
    for col in required_columns:
        if col not in df.columns:
            log_error(f"Missing required column: {col}")
            return False
    
    # Validate depth is integer >= 1
    if not all(isinstance(d, int) and d >= 1 for d in df['depth']):
        log_error("All depth values must be integers >= 1")
        return False
    
    # Validate entropy is in [0, 1]
    if not all(0.0 <= e <= 1.0 for e in df['entropy']):
        log_error("All entropy values must be in range [0, 1]")
        return False
    
    # Validate complexity_score is in [0, 1]
    if not all(0.0 <= c <= 1.0 for c in df['complexity_score']):
        log_error("All complexity_score values must be in range [0, 1]")
        return False
    
    return True

def main():
    """
    Main function to compute complexity scores for all variants.
    
    Reads variants from data/processed/variants.csv, computes entropy and depth,
    and writes results to data/processed/complexity_scores.csv.
    """
    logger.info("Starting complexity score computation pipeline")
    
    # Ensure output directory exists
    output_path = Path(COMPLEXITY_SCORE_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load variants data
    variants_path = Path(VARIANTS_FILE)
    if not variants_path.exists():
        fail_loudly(f"Variants file not found: {VARIANTS_FILE}. Run generator first.")
    
    try:
        variants_df = pd.read_csv(variants_path)
        logger.info(f"Loaded {len(variants_df)} variants from {VARIANTS_FILE}")
    except Exception as e:
        fail_loudly(f"Failed to load variants: {str(e)}")
    
    # Load validity flags if available
    validity_df = None
    validity_path = Path(VALIDITY_FILE)
    if validity_path.exists():
        try:
            validity_df = pd.read_csv(validity_path)
            logger.info(f"Loaded validity flags from {VALIDITY_FILE}")
        except Exception as e:
            log_error(f"Failed to load validity flags: {str(e)}")
    
    # Process each variant
    results = []
    for idx, row in variants_df.iterrows():
        case_id = row['case_id']
        variant_type = row['variant_type']
        
        # Get the action chain - try multiple column names
        action_chain = None
        if 'action_chain' in row:
            action_chain = row['action_chain']
        elif 'generated_chain' in row:
            action_chain = row['generated_chain']
        elif 'original_chain' in row:
            action_chain = row['original_chain']
        
        if not action_chain:
            log_error(f"No action chain found for case {case_id}, variant {variant_type}")
            continue
        
        # Compute entropy
        entropy = compute_shannon_entropy(str(action_chain))
        
        # Compute dependency depth from original semantic intent
        # We use the original_chain if available, otherwise the action_chain
        original_chain = row.get('original_chain', action_chain)
        depth = compute_dependency_depth(str(original_chain))
        
        # Compute complexity score
        complexity_score = compute_complexity_score(entropy, depth)
        
        results.append({
            'case_id': case_id,
            'variant_type': variant_type,
            'entropy': round(entropy, 6),
            'depth': depth,
            'complexity_score': complexity_score
        })
        
        logger.debug(f"Processed {case_id}/{variant_type}: entropy={entropy:.4f}, depth={depth}, score={complexity_score:.4f}")
    
    # Create results DataFrame
    if not results:
        fail_loudly("No results generated - check input data")
    
    results_df = pd.DataFrame(results)
    
    # Validate results
    if not validate_complexity_scores(results_df):
        fail_loudly("Complexity scores validation failed")
    
    # Write output
    results_df.to_csv(COMPLEXITY_SCORE_FILE, index=False)
    logger.info(f"Successfully wrote {len(results_df)} complexity scores to {COMPLEXITY_SCORE_FILE}")
    
    # Print summary statistics
    logger.info(f"Summary - Mean entropy: {results_df['entropy'].mean():.4f}")
    logger.info(f"Summary - Mean depth: {results_df['depth'].mean():.2f}")
    logger.info(f"Summary - Mean complexity score: {results_df['complexity_score'].mean():.4f}")
    
    return results_df

if __name__ == "__main__":
    main()
