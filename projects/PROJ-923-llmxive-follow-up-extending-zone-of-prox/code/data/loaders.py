"""
Data Loaders for MMLU and synthetic negative candidates.
"""
import os
import json
import random
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datasets import load_dataset, Dataset

from utils.logging import get_logger
from utils.seeds import get_seed

logger = get_logger(__name__)

def load_mmlu_schema() -> Dict[str, Any]:
    """Loads the MMLU dataset schema."""
    # In a real scenario, this might load a schema file.
    # For now, we assume the dataset structure is known.
    return {
        "question": str,
        "answer": str,
        "subject": str,
        "choices": list
    }

def load_real_mmlu_subset(subject: str = "abstract_algebra", split: str = "validation") -> Dataset:
    """
    Loads a subset of the real MMLU dataset.
    FAILS LOUDLY if the dataset cannot be loaded.
    """
    try:
        dataset = load_dataset("cais/mmlu", subject, split=split)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load MMLU dataset: {e}")
        raise RuntimeError(f"Real MMLU data source unavailable: {e}")

def generate_synthetic_negative_candidates(real_data: Dataset, num_candidates: int = 4) -> List[str]:
    """
    Generates synthetic negative candidates based on the schema.
    Uses the real data's answer choices to create plausible negatives.
    """
    # Extract all choices from the dataset
    all_choices = []
    for item in real_data:
        if 'choices' in item:
            all_choices.extend(item['choices'])
    
    # Remove duplicates
    unique_choices = list(set(all_choices))
    
    # Select random negatives
    if len(unique_choices) < num_candidates:
        return unique_choices
    
    return random.sample(unique_choices, num_candidates)

def save_negative_candidates(candidates: List[str], filepath: str):
    """Saves candidates to a file."""
    with open(filepath, 'w') as f:
        json.dump(candidates, f)

def load_mmlu_held_out_set() -> List[Dict[str, Any]]:
    """
    Loads the held-out set for evaluation.
    Combines real MMLU data with synthetic negative candidates.
    """
    logger.info("Loading MMLU held-out set...")
    
    # Load real data
    try:
        dataset = load_real_mmlu_subset()
    except Exception as e:
        logger.error("Cannot proceed without real MMLU data.")
        raise e
    
    held_out = []
    for i, item in enumerate(dataset):
        question = item['question']
        answer = item['answer']
        choices = item['choices']
        
        # Generate synthetic negatives (if not already in choices)
        # For simulation, we use the other choices as negatives
        negatives = [c for c in choices if c != answer]
        
        if not negatives:
            # Fallback if only one choice
            negatives = ["synthetic_negative_1", "synthetic_negative_2"]
        
        held_out.append({
            "id": f"mmlu_{i}",
            "question": question,
            "ground_truth": answer,
            "candidates": negatives,
            "subject": item.get('subject', 'unknown')
        })
    
    logger.info(f"Loaded {len(held_out)} items for held-out set.")
    return held_out
