"""
Script to generate AI text samples with controlled linguistic complexity
and compute objective metrics (Flesch-Kincaid, MTLD, Sentence Length).

This script:
1. Loads a subset of Wikipedia articles.
2. Generates text samples using Gemma-2B (CPU-only).
3. Computes linguistic metrics for each sample.
4. Saves results to a CSV file.
"""
import os
import sys
import random
import logging
import time
from typing import List, Dict, Any, Optional
import csv

import pandas as pd
import numpy as np
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Import utility functions from utils.py
# Ensure utils.py is in the same directory or PYTHONPATH is set
from utils import pin_random_seed, calculate_mtld, calculate_flesch_kincaid, calculate_average_sentence_length, get_all_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/outputs/generate_text.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
NUM_SAMPLES = 500
WIKIPEDIA_DATASET_NAME = 'wikipedia'
WIKIPEDIA_CONFIG = '20220301.en'
OUTPUT_FILE = 'data/raw/generated_text.csv'
MODEL_NAME = 'google/gemma-2b'
MAX_NEW_TOKENS = 250  # Limit generation length for CPU feasibility

def pin_seed(seed: int = RANDOM_SEED) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Random seeds pinned to {seed}")

def load_wikipedia_sample(n_samples: int = NUM_SAMPLES) -> List[Dict[str, Any]]:
    """
    Load a sample of Wikipedia articles.
    Uses stratified sampling by sentence length to ensure variance.

    Args:
        n_samples: Number of samples to load.

    Returns:
        List of dictionaries containing 'id' and 'text'.
    """
    logger.info(f"Loading {n_samples} samples from Wikipedia dataset...")
    try:
        # Load a smaller subset first to calculate sentence lengths for stratification
        # We load a larger chunk to ensure we have enough for stratified sampling
        dataset = load_dataset(WIKIPEDIA_DATASET_NAME, WIKIPEDIA_CONFIG, split='train', streaming=True)
        
        # Pre-process to get sentence lengths for stratification
        # We'll take a larger pool first
        pool_size = n_samples * 5
        pool = []
        count = 0
        for item in dataset:
            if count >= pool_size:
                break
            text = item.get('text', '')
            if text and len(text) > 100: # Filter very short texts
                # Estimate sentence length (simple heuristic: word count / estimated sentences)
                # For stratification, we just need a proxy for complexity
                pool.append({'id': item.get('id', str(count)), 'text': text})
                count += 1
        
        if len(pool) < n_samples:
            logger.warning(f"Pool size {len(pool)} is less than requested {n_samples}. Adjusting.")
            n_samples = len(pool)

        # Stratify by text length (proxy for sentence length/complexity)
        # Sort by length
        pool.sort(key=lambda x: len(x['text']))
        
        # Divide into strata
        strata_size = len(pool) // n_samples
        selected = []
        for i in range(n_samples):
            # Pick one from each stratum, with some random offset
            stratum_start = i * strata_size
            stratum_end = (i + 1) * strata_size
            if stratum_end > len(pool):
                stratum_end = len(pool)
            
            if stratum_start < stratum_end:
                # Random pick within stratum
                idx = random.randint(stratum_start, stratum_end - 1)
                selected.append(pool[idx])
        
        logger.info(f"Loaded {len(selected)} samples with stratified sampling.")
        return selected

    except Exception as e:
        logger.error(f"Error loading Wikipedia dataset: {e}")
        raise

def generate_with_gemma(prompt: str, tokenizer, model, max_new_tokens: int = MAX_NEW_TOKENS) -> str:
    """
    Generate text using the Gemma model.

    Args:
        prompt: The input prompt.
        tokenizer: The tokenizer for the model.
        model: The loaded Gemma model.
        max_new_tokens: Maximum number of tokens to generate.

    Returns:
        Generated text string.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Move to CPU (explicitly, though model should be on CPU)
    input_ids = inputs.input_ids
    attention_mask = inputs.attention_mask
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    generated_ids = outputs[0][inputs.input_ids.shape[1]:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return generated_text

def compute_metrics(text: str) -> Dict[str, float]:
    """
    Compute linguistic complexity metrics for a given text.
    Uses functions from utils.py.

    Args:
        text: The input text string.

    Returns:
        Dictionary with 'flesch_kincaid', 'mtld', 'avg_sentence_length'.
    """
    if not text or len(text.strip()) == 0:
        return {
            'flesch_kincaid': 0.0,
            'mtld': 0.0,
            'avg_sentence_length': 0.0
        }
    
    # Use the get_all_metrics function from utils.py which calls the individual calculators
    metrics = get_all_metrics(text)
    return {
        'flesch_kincaid': metrics['flesch_kincaid'],
        'mtld': metrics['mtld'],
        'avg_sentence_length': metrics['avg_sentence_length']
    }

def validate_fk_range(results: List[Dict], min_fk: float = 5.0, max_fk: float = 12.0, max_retries: int = 3) -> bool:
    """
    Validate that the Flesch-Kincaid range spans at least min_fk to max_fk.
    If not, re-sample prompts (simulated by re-generating from different Wikipedia seeds).

    Args:
        results: List of result dictionaries.
        min_fk: Minimum FK score required.
        max_fk: Maximum FK score required.
        max_retries: Maximum number of retry attempts.

    Returns:
        True if range is valid, False otherwise.
    """
    if not results:
        return False
    
    fk_scores = [r['flesch_kincaid'] for r in results]
    min_score = min(fk_scores)
    max_score = max(fk_scores)
    
    logger.info(f"Current FK range: [{min_score:.2f}, {max_score:.2f}]")
    
    if min_score <= min_fk and max_score >= max_fk:
        return True
    
    return False

def main():
    """Main entry point for the script."""
    logger.info("Starting text generation and metric computation pipeline.")
    
    # Pin seeds
    pin_seed(RANDOM_SEED)
    
    # Load model and tokenizer
    logger.info(f"Loading model: {MODEL_NAME}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        # Load model on CPU, default precision (no 8-bit quantization)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32, # Explicitly float32 for CPU
            device_map="cpu"
        )
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Load Wikipedia samples
    wikipedia_samples = load_wikipedia_sample(NUM_SAMPLES)
    
    # Prepare prompts
    # We use variations of prompts to encourage different styles/complexities
    prompt_templates = [
        "Explain the following concept simply: ",
        "Describe the following topic in detail: ",
        "Write a summary of the following: ",
        "Analyze the following text: "
    ]
    
    results = []
    retry_count = 0
    max_total_retries = 3
    
    while retry_count < max_total_retries:
        if retry_count > 0:
            logger.info(f"Retry attempt {retry_count}/{max_total_retries}. Resampling prompts.")
            # Re-shuffle wikipedia samples or change prompt strategy
            random.shuffle(wikipedia_samples)
        
        current_results = []
        
        for i, sample in enumerate(wikipedia_samples):
            if i % 50 == 0:
                logger.info(f"Processing sample {i}/{len(wikipedia_samples)}")
            
            # Select a prompt template (could be random or deterministic)
            prompt_template = random.choice(prompt_templates)
            # Use a snippet of the Wikipedia text as the base, or the whole text if short
            # To ensure variety, we might take a paragraph or the first N words
            text_snippet = sample['text'][:500] # Take first 500 chars as base context
            
            prompt = f"{prompt_template}{text_snippet}"
            
            try:
                generated_text = generate_with_gemma(prompt, tokenizer, model)
                full_text = generated_text # The generated text is the sample
                
                # Compute metrics
                metrics = compute_metrics(full_text)
                
                result_entry = {
                    'text_id': f"gen_{i}_{retry_count}",
                    'raw_text': full_text,
                    'source_id': sample['id'],
                    'flesch_kincaid': metrics['flesch_kincaid'],
                    'mtld': metrics['mtld'],
                    'avg_sentence_length': metrics['avg_sentence_length']
                }
                current_results.append(result_entry)
                
            except Exception as e:
                logger.error(f"Error processing sample {i}: {e}")
                continue
        
        results = current_results
        
        # Validate FK range
        if validate_fk_range(results):
            logger.info("FK variance requirement met.")
            break
        else:
            logger.warning("FK variance requirement NOT met. Retrying...")
            retry_count += 1
    
    if not validate_fk_range(results):
        logger.error("ERROR: Could not achieve FK variance 5.0-12.0 after 3 retries.")
        sys.exit(1)
    
    # Save results to CSV
    logger.info(f"Saving {len(results)} results to {OUTPUT_FILE}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    fieldnames = ['text_id', 'raw_text', 'source_id', 'flesch_kincaid', 'mtld', 'avg_sentence_length']
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Successfully saved results to {OUTPUT_FILE}")
    logger.info(f"FK Range: [{min(r['flesch_kincaid'] for r in results):.2f}, {max(r['flesch_kincaid'] for r in results):.2f}]")
    logger.info("Pipeline completed.")

if __name__ == "__main__":
    main()