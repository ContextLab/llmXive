import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import textstat
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

# Import from project utils to ensure consistency
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_ITERATIONS = 10
MIN_FLESCH_DIFF = 5.0
MIN_JACCARD = 0.85
MAX_SENTENCE_LENGTH_DEFAULT = 15
MIN_SENTENCE_LENGTH_DEFAULT = 5
REPETITION_PENALTY_DEFAULT = 1.1
TEMPERATURE_DEFAULT = 0.7

def load_moderate_tiers(input_path: str) -> pd.DataFrame:
    """Load moderate tiers from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Moderate tiers file not found: {input_path}")
    
    df = pd.read_csv(path)
    required_cols = ['instructional_unit_id', 'text']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Moderate tiers must contain columns: {required_cols}")
    
    logger.info(f"Loaded {len(df)} moderate tiers from {input_path}")
    return df

def simplify_text(text: str, model, tokenizer, max_length: int, repetition_penalty: float, temperature: float) -> str:
    """
    Simplify text using BART-large-cnn with specific parameters.
    
    Args:
        text: Input text to simplify
        model: BART model
        tokenizer: BART tokenizer
        max_length: Maximum length for summary (controls brevity)
        repetition_penalty: Penalty for repetition
        temperature: Sampling temperature
    
    Returns:
        Simplified text
    """
    # Prepend instruction to guide the model
    instruction = "Simplify the following text for easier reading while keeping the meaning: "
    input_text = instruction + text
    
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            min_length=10,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            do_sample=True,
            early_stopping=True
        )
    
    simplified = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return simplified

def iterative_simplify(text: str, moderate_fk: float, model, tokenizer, max_iterations: int = MAX_ITERATIONS) -> Tuple[str, Dict[str, Any]]:
    """
    Iteratively simplify text until constraints are met.
    
    Constraints:
        1. Flesch-Kincaid difference (moderate - simple) >= MIN_FLESCH_DIFF
        2. Jaccard similarity (simple vs moderate) >= MIN_JACCARD
    
    Args:
        text: Original moderate tier text
        moderate_fk: Flesch-Kincaid score of the moderate tier
        model: BART model
        tokenizer: BART tokenizer
        max_iterations: Maximum refinement iterations
    
    Returns:
        Tuple of (simplified_text, metadata_dict)
    
    Raises:
        ValueError: If constraints cannot be met after max_iterations
    """
    import torch
    
    best_text = text
    best_fk_diff = -float('inf')
    best_jaccard = 0.0
    best_params = {}
    
    # Start with default parameters
    current_max_length = MAX_SENTENCE_LENGTH_DEFAULT
    current_repetition = REPETITION_PENALTY_DEFAULT
    current_temperature = TEMPERATURE_DEFAULT
    
    for iteration in range(max_iterations):
        # Generate simplified text
        try:
            simplified = simplify_text(
                text, model, tokenizer,
                max_length=current_max_length,
                repetition_penalty=current_repetition,
                temperature=current_temperature
            )
        except Exception as e:
            logger.warning(f"Generation failed at iteration {iteration}: {e}")
            # Adjust parameters and retry
            current_max_length = max(MIN_SENTENCE_LENGTH_DEFAULT, current_max_length - 2)
            continue
        
        # Calculate metrics
        simple_fk = calculate_flesch_kincaid(simplified)
        fk_diff = moderate_fk - simple_fk
        jaccard = calculate_jaccard_similarity(text, simplified)
        
        logger.info(f"Iteration {iteration}: FK_diff={fk_diff:.2f}, Jaccard={jaccard:.3f}, MaxLen={current_max_length}")
        
        # Check if constraints are met
        if fk_diff >= MIN_FLESCH_DIFF and jaccard >= MIN_JACCARD:
            logger.info(f"Constraints met at iteration {iteration}")
            return simplified, {
                'iterations': iteration + 1,
                'final_fk_diff': fk_diff,
                'final_jaccard': jaccard,
                'final_max_length': current_max_length,
                'final_repetition_penalty': current_repetition,
                'final_temperature': current_temperature,
                'status': 'success'
            }
        
        # Track best attempt so far
        if fk_diff > best_fk_diff:
            best_fk_diff = fk_diff
            best_text = simplified
            best_jaccard = jaccard
            best_params = {
                'iterations': iteration + 1,
                'final_fk_diff': fk_diff,
                'final_jaccard': jaccard,
                'final_max_length': current_max_length,
                'final_repetition_penalty': current_repetition,
                'final_temperature': current_temperature,
                'status': 'best_attempt'
            }
        
        # Adjust parameters for next iteration
        # If FK diff is too low, reduce max_length (make it shorter/simpler)
        if fk_diff < MIN_FLESCH_DIFF:
            current_max_length = max(MIN_SENTENCE_LENGTH_DEFAULT, current_max_length - 2)
            # Also increase repetition penalty slightly to force more variety
            current_repetition = min(2.0, current_repetition + 0.1)
        # If Jaccard is too low, we might be changing meaning too much
        # Increase max_length to preserve more content
        elif jaccard < MIN_JACCARD:
            current_max_length = min(50, current_max_length + 2)
            current_temperature = max(0.3, current_temperature - 0.1)
        
        # Safety break if parameters go out of bounds
        if current_max_length < MIN_SENTENCE_LENGTH_DEFAULT:
            logger.warning("Reached minimum sentence length limit")
            break
    
    # If we exit the loop without meeting constraints, raise error
    logger.error(f"Failed to meet constraints after {max_iterations} iterations. Best FK_diff: {best_fk_diff:.2f}, Best Jaccard: {best_jaccard:.3f}")
    raise ValueError(
        f"Iterative simplification failed to meet constraints after {max_iterations} iterations. "
        f"Required FK diff >= {MIN_FLESCH_DIFF}, achieved {best_fk_diff:.2f}. "
        f"Required Jaccard >= {MIN_JACCARD}, achieved {best_jaccard:.3f}. "
        f"Best parameters: {best_params}"
    )

def generate_simple_tiers(moderate_df: pd.DataFrame, model, tokenizer) -> pd.DataFrame:
    """
    Generate simple tiers for all moderate tiers.
    
    Args:
        moderate_df: DataFrame with moderate tiers
        model: BART model
        tokenizer: BART tokenizer
    
    Returns:
        DataFrame with simple tiers and metadata
    """
    results = []
    
    for idx, row in moderate_df.iterrows():
        unit_id = row['instructional_unit_id']
        text = row['text']
        
        logger.info(f"Processing unit {unit_id}")
        
        # Calculate moderate FK score
        moderate_fk = calculate_flesch_kincaid(text)
        
        try:
            simple_text, metadata = iterative_simplify(text, moderate_fk, model, tokenizer)
            metadata['instructional_unit_id'] = unit_id
            metadata['moderate_fk'] = moderate_fk
            metadata['simple_fk'] = calculate_flesch_kincaid(simple_text)
            metadata['moderate_text'] = text
            metadata['simple_text'] = simple_text
            results.append(metadata)
        except ValueError as e:
            logger.error(f"Failed to simplify unit {unit_id}: {e}")
            # Store failure info
            results.append({
                'instructional_unit_id': unit_id,
                'status': 'failed',
                'error': str(e),
                'moderate_fk': moderate_fk
            })
    
    return pd.DataFrame(results)

def save_simple_tiers(df: pd.DataFrame, output_path: str):
    """Save simple tiers to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} simple tiers to {output_path}")

def main():
    """Main entry point for simple tier generation."""
    import torch
    
    # Paths
    moderate_path = "data/explanation_tiers/moderate_tiers.csv"
    output_path = "data/explanation_tiers/simple_tiers.csv"
    
    # Load moderate tiers
    logger.info("Loading moderate tiers...")
    moderate_df = load_moderate_tiers(moderate_path)
    
    # Load model and tokenizer
    logger.info("Loading BART model...")
    model_name = "facebook/bart-large-cnn"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        model.eval()
        if torch.cuda.is_available():
            model = model.to('cuda')
            logger.info("Model moved to GPU")
        else:
            logger.info("Using CPU for inference")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Generate simple tiers
    logger.info("Generating simple tiers with iterative refinement...")
    start_time = time.time()
    simple_df = generate_simple_tiers(moderate_df, model, tokenizer)
    elapsed = time.time() - start_time
    logger.info(f"Generation completed in {elapsed:.2f} seconds")
    
    # Save results
    save_simple_tiers(simple_df, output_path)
    
    # Summary
    success_count = len(simple_df[simple_df['status'] == 'success'])
    fail_count = len(simple_df[simple_df['status'] == 'failed'])
    logger.info(f"Summary: {success_count} successful, {fail_count} failed out of {len(simple_df)} total")
    
    if fail_count > 0:
        logger.warning(f"{fail_count} units failed to meet constraints. Check logs for details.")

if __name__ == "__main__":
    main()
