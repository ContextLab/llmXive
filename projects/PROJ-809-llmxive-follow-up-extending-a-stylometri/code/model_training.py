"""
Model training module for character-level n-gram models with Kneser-Ney smoothing.
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
from optimization_wrapper import run_with_constraints, optimize_training_parameters, check_memory_usage

logger = get_logger(__name__)

# Constants
ARTIFACTS_DIR = Path("artifacts")
MODELS_DIR = ARTIFACTS_DIR / "models"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
DATA_PROCESSED_DIR = Path("data") / "processed"

# Ensure directories exist
ensure_dir(MODELS_DIR)
ensure_dir(METRICS_DIR)


class KneserNeyCountVectorizer:
    """
    Custom character-level n-gram vectorizer with Kneser-Ney smoothing.
    Optimized for memory efficiency and CPU execution.
    """

    def __init__(self, ngram_order: int = 5, min_count: int = 1):
        self.ngram_order = ngram_order
        self.min_count = min_count
        self.vocabulary_ = {}
        self.idf_ = {}
        self.total_ngrams = 0
        self.ngram_counts = Counter()
        self.continuation_counts = Counter()  # For Kneser-Ney

    def fit(self, texts: List[str]):
        """Fit the vectorizer on a list of texts."""
        logger.debug(f"Fitting KneserNeyCountVectorizer for n={self.ngram_order}")
        
        self.ngram_counts.clear()
        self.continuation_counts.clear()
        
        for text in texts:
            ngrams = self._get_ngrams(text)
            self.ngram_counts.update(ngrams)
            
            # Track unique contexts for continuation counts
            seen_contexts = set()
            for i in range(len(ngrams)):
                context = ngrams[i][:-1] if len(ngrams[i]) > 1 else ""
                if context not in seen_contexts:
                    seen_contexts.add(context)
                    self.continuation_counts[context] += 1

        # Filter by min_count
        filtered_ngrams = {
            ngram: count for ngram, count in self.ngram_counts.items()
            if count >= self.min_count
        }
        
        # Build vocabulary
        self.vocabulary_ = {ngram: idx for idx, ngram in enumerate(filtered_ngrams)}
        self.total_ngrams = sum(filtered_ngrams.values())
        
        logger.info(f"Vocabulary size: {len(self.vocabulary_)}, Total n-grams: {self.total_ngrams}")
        return self

    def transform(self, texts: List[str]) -> Dict[str, List[int]]:
        """Transform texts into n-gram counts."""
        results = {}
        for idx, text in enumerate(texts):
            ngrams = self._get_ngrams(text)
            counts = Counter(ngrams)
            results[idx] = [counts.get(ngram, 0) for ngram in sorted(self.vocabulary_, key=self.vocabulary_.get)]
        return results

    def _get_ngrams(self, text: str) -> List[str]:
        """Extract n-grams from text."""
        if len(text) < self.ngram_order:
            return []
        
        ngrams = []
        for i in range(len(text) - self.ngram_order + 1):
            ngrams.append(text[i:i + self.ngram_order])
        return ngrams

    def get_smoothed_probability(self, ngram: str) -> float:
        """Calculate Kneser-Ney smoothed probability for an n-gram."""
        if self.total_ngrams == 0:
            return 1e-10
        
        # Get raw count
        count = self.ngram_counts.get(ngram, 0)
        
        # Kneser-Ney discount (simplified)
        discount = 0.75
        discounted_count = max(0, count - discount)
        
        # Continuation probability
        context = ngram[:-1] if len(ngram) > 1 else ""
        continuation_prob = self.continuation_counts.get(context, 0) / max(1, sum(self.continuation_counts.values()))
        
        # Smoothed probability
        prob = (discounted_count / self.total_ngrams) + (discount * continuation_prob)
        return max(prob, 1e-10)  # Avoid log(0)


def load_author_data(author_id: str) -> List[str]:
    """Load preprocessed text data for a specific author."""
    author_dir = DATA_PROCESSED_DIR / author_id
    if not author_dir.exists():
        raise FileNotFoundError(f"Author directory not found: {author_dir}")
    
    texts = []
    for file_path in sorted(author_dir.glob("*.txt")):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            if text:
                texts.append(text)
    
    if not texts:
        raise ValueError(f"No text data found for author {author_id}")
    
    return texts


def train_test_split_authors(texts: List[str], test_ratio: float = 0.2) -> Tuple[List[str], List[str]]:
    """Split texts into train and test sets."""
    set_seed(get_seed())
    import random
    random.shuffle(texts)
    split_idx = int(len(texts) * (1 - test_ratio))
    return texts[:split_idx], texts[split_idx:]


def check_sparsity(model: KneserNeyCountVectorizer, threshold: float = 0.9) -> bool:
    """Check if the model's vocabulary is too sparse."""
    if not model.vocabulary_:
        return True
    
    # Calculate sparsity as ratio of unseen n-grams
    total_possible = len(model.vocabulary_) ** 2 if model.vocabulary_ else 1
    observed = len(model.ngram_counts)
    sparsity = 1 - (observed / total_possible) if total_possible > 0 else 1.0
    
    logger.info(f"Sparsity check: {sparsity:.4f} (threshold: {threshold})")
    return sparsity > threshold


def train_author_models(
    author_id: str, 
    ngram_orders: List[int] = [4, 5, 6],
    max_time: int = 30
) -> Dict[str, Any]:
    """
    Train n-gram models for a single author with constraint enforcement.
    
    Args:
        author_id: Author identifier
        ngram_orders: List of n-gram orders to train
        max_time: Maximum time allowed for training this author
        
    Returns:
        Dictionary containing model info and metrics
    """
    logger.info(f"Training models for author {author_id}")
    
    try:
        # Load data
        texts = run_with_constraints(load_author_data, author_id, author_id)
        
        # Split data
        train_texts, test_texts = run_with_constraints(
            train_test_split_authors, 
            author_id, 
            texts, 
            timeout=max_time
        )
        
        results = {
            "author_id": author_id,
            "train_count": len(train_texts),
            "test_count": len(test_texts),
            "models": {},
            "fallbacks": []
        }
        
        for n in ngram_orders:
            start_time = time.time()
            
            # Check memory before training
            check_memory_usage()
            
            # Train model
            vectorizer = KneserNeyCountVectorizer(ngram_order=n, min_count=1)
            vectorizer.fit(train_texts)
            
            # Check sparsity for n=6
            if n == 6 and check_sparsity(vectorizer):
                logger.warning(f"High sparsity for n=6 in author {author_id}, triggering fallback")
                results["fallbacks"].append({"order": 6, "reason": "sparsity"})
                # Skip saving n=6, will be handled by fallback logic
                continue
            
            # Save model
            model_path = MODELS_DIR / f"author_{author_id}_n{n}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(vectorizer, f)
            
            elapsed = time.time() - start_time
            results["models"][f"n{n}"] = {
                "vocabulary_size": len(vectorizer.vocabulary_),
                "training_time": elapsed,
                "path": str(model_path)
            }
            
            logger.info(f"Trained n={n} model for {author_id} in {elapsed:.2f}s")
            
            # Check time constraint
            if elapsed > max_time:
                logger.warning(f"Training for n={n} exceeded time limit for {author_id}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error training models for author {author_id}: {str(e)}")
        raise


def save_model(model: KneserNeyCountVectorizer, author_id: str, ngram_order: int, is_fallback: bool = False):
    """Save a trained model to disk."""
    suffix = "_fallback" if is_fallback else ""
    model_path = MODELS_DIR / f"author_{author_id}_n{ngram_order}{suffix}.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Saved model to {model_path}")
    return model_path


def main():
    """Main entry point for model training."""
    logger.info("Starting model training pipeline")
    
    # Load configuration
    config = load_config()
    set_seed(config.get("seed", 42))
    
    # Get list of authors
    authors = [d.name for d in DATA_PROCESSED_DIR.iterdir() if d.is_dir()]
    logger.info(f"Found {len(authors)} authors to process")
    
    if not authors:
        logger.error("No authors found in data/processed/")
        sys.exit(1)
    
    # Train models for each author
    all_results = []
    for author_id in authors:
        try:
            result = run_with_constraints(
                train_author_models,
                author_id,
                author_id,
                ngram_orders=[4, 5, 6],
                timeout=30
            )
            all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to train models for {author_id}: {str(e)}")
            continue
    
    # Save summary
    summary_path = METRICS_DIR / "training_summary.json"
    save_json(all_results, summary_path)
    logger.info(f"Training summary saved to {summary_path}")
    
    logger.info("Model training pipeline completed")


if __name__ == "__main__":
    main()
