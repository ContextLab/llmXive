"""
Evaluation module for computing perplexity matrix and classification metrics.
Optimized for CPU-only execution within memory and time constraints.
"""

import os
import sys
import json
import logging
import pickle
import math
import time
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
from pathlib import Path

from utils import get_logger, ensure_dir, load_json, save_json
from config import load_config, set_seed, get_seed
from optimization_wrapper import run_with_constraints, check_memory_usage

logger = get_logger(__name__)

# Constants
ARTIFACTS_DIR = Path("artifacts")
MODELS_DIR = ARTIFACTS_DIR / "models"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
DATA_PROCESSED_DIR = Path("data") / "processed"

# Ensure directories exist
ensure_dir(METRICS_DIR)


def load_model(author_id: str, ngram_order: int, is_fallback: bool = False) -> Any:
    """Load a trained model from disk."""
    suffix = "_fallback" if is_fallback else ""
    model_path = MODELS_DIR / f"author_{author_id}_n{ngram_order}{suffix}.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def compute_perplexity(model: Any, text: str) -> float:
    """
    Compute perplexity of a text given a model.
    
    Args:
        model: Trained KneserNeyCountVectorizer
        text: Text to evaluate
        
    Returns:
        Perplexity value
    """
    ngram_order = model.ngram_order
    ngrams = model._get_ngrams(text)
    
    if not ngrams:
        return float('inf')
    
    log_prob_sum = 0.0
    for ngram in ngrams:
        prob = model.get_smoothed_probability(ngram)
        log_prob_sum += math.log(prob)
    
    avg_log_prob = log_prob_sum / len(ngrams)
    perplexity = math.exp(-avg_log_prob)
    
    return perplexity


def compute_perplexity_matrix(
    authors: List[str],
    ngram_orders: List[int] = [4, 5, 6],
    max_time_per_author: int = 30
) -> Dict[str, Dict[str, float]]:
    """
    Compute perplexity matrix for all author pairs and n-gram orders.
    
    Args:
        authors: List of author identifiers
        ngram_orders: List of n-gram orders to evaluate
        max_time_per_author: Maximum time allowed per author evaluation
        
    Returns:
        Nested dictionary: perplexity_matrix[author_test][model_author] = perplexity
    """
    logger.info("Computing perplexity matrix")
    
    perplexity_matrix = {}
    
    for test_author in authors:
        logger.info(f"Evaluating test author: {test_author}")
        
        # Load test data
        try:
            test_texts = run_with_constraints(
                lambda aid: [t for t in load_author_data(aid) if t],
                test_author,
                test_author,
                timeout=max_time_per_author
            )
        except Exception as e:
            logger.error(f"Failed to load test data for {test_author}: {str(e)}")
            continue
        
        if not test_texts:
            logger.warning(f"No test data for {test_author}")
            continue
        
        perplexity_matrix[test_author] = {}
        
        for model_author in authors:
            for n in ngram_orders:
                try:
                    # Load model
                    model = run_with_constraints(
                        load_model,
                        model_author,
                        model_author,
                        n,
                        is_fallback=False
                    )
                    
                    # Evaluate on all test texts and average
                    total_perplexity = 0.0
                    count = 0
                    
                    for text in test_texts:
                        try:
                            perplexity = compute_perplexity(model, text)
                            if not math.isinf(perplexity) and perplexity > 0:
                                total_perplexity += perplexity
                                count += 1
                        except Exception as e:
                            logger.debug(f"Error evaluating text for {test_author} vs {model_author} (n={n}): {str(e)}")
                    
                    if count > 0:
                        avg_perplexity = total_perplexity / count
                        key = f"{model_author}_n{n}"
                        perplexity_matrix[test_author][key] = avg_perplexity
                    
                except Exception as e:
                    logger.error(f"Error evaluating {test_author} vs {model_author} (n={n}): {str(e)}")
                    continue
        
        # Check memory periodically
        check_memory_usage()
    
    return perplexity_matrix


def save_perplexity_matrix(matrix: Dict[str, Dict[str, float]], output_path: str):
    """Save perplexity matrix to CSV."""
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        if matrix:
            headers = ["test_author"] + list(next(iter(matrix.values())).keys())
            f.write(",".join(headers) + "\n")
            
            # Write rows
            for test_author, row in matrix.items():
                values = [test_author] + [str(row.get(h, "")) for h in headers[1:]]
                f.write(",".join(values) + "\n")
    
    logger.info(f"Perplexity matrix saved to {output_path}")


def classify_by_min_perplexity(
    perplexity_matrix: Dict[str, Dict[str, float]],
    test_author: str
) -> Optional[str]:
    """
    Classify a test author by minimum perplexity across all models.
    
    Args:
        perplexity_matrix: Computed perplexity matrix
        test_author: Test author to classify
        
    Returns:
        Predicted author ID or None if no prediction
    """
    if test_author not in perplexity_matrix:
        return None
    
    row = perplexity_matrix[test_author]
    if not row:
        return None
    
    # Find minimum perplexity
    min_perplexity = float('inf')
    predicted_author = None
    
    for model_key, perplexity in row.items():
        if perplexity < min_perplexity:
            min_perplexity = perplexity
            # Extract author ID from model key (e.g., "author_X_n5" -> "author_X")
            predicted_author = model_key.rsplit("_", 1)[0]
        elif perplexity == min_perplexity and predicted_author:
            # Tie-breaking: alphabetical order
            candidate_author = model_key.rsplit("_", 1)[0]
            if candidate_author < predicted_author:
                predicted_author = candidate_author
    
    return predicted_author


def calculate_accuracy(
    perplexity_matrix: Dict[str, Dict[str, float]],
    authors: List[str]
) -> float:
    """Calculate classification accuracy."""
    correct = 0
    total = 0
    
    for author in authors:
        predicted = classify_by_min_perplexity(perplexity_matrix, author)
        if predicted == author:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0.0


def main():
    """Main entry point for evaluation."""
    logger.info("Starting evaluation pipeline")
    
    # Load configuration
    config = load_config()
    set_seed(config.get("seed", 42))
    
    # Get list of authors
    authors = [d.name for d in DATA_PROCESSED_DIR.iterdir() if d.is_dir()]
    logger.info(f"Evaluating {len(authors)} authors")
    
    if not authors:
        logger.error("No authors found in data/processed/")
        sys.exit(1)
    
    # Compute perplexity matrix
    try:
        perplexity_matrix = run_with_constraints(
            compute_perplexity_matrix,
            "perplexity_matrix",
            authors,
            [4, 5, 6],
            timeout=30
        )
    except Exception as e:
        logger.error(f"Failed to compute perplexity matrix: {str(e)}")
        sys.exit(1)
    
    # Save perplexity matrix
    output_path = METRICS_DIR / "perplexity_matrix.csv"
    save_perplexity_matrix(perplexity_matrix, str(output_path))
    
    # Calculate accuracy
    accuracy = calculate_accuracy(perplexity_matrix, authors)
    logger.info(f"Classification accuracy: {accuracy:.4f}")
    
    # Save accuracy
    accuracy_path = METRICS_DIR / "classification_accuracy.json"
    save_json({"accuracy": accuracy, "authors_count": len(authors)}, str(accuracy_path))
    
    logger.info("Evaluation pipeline completed")


if __name__ == "__main__":
    main()
