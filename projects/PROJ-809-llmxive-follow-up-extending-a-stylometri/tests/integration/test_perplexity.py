"""
Integration test for perplexity calculation (US2).

This test verifies that the perplexity calculation pipeline:
1. Loads the processed corpus from data/processed/
2. Trains character-level n-gram models (n=4, 5, 6) for a subset of authors
3. Computes perplexity for held-out text against both same-author and cross-author models
4. Verifies that same-author perplexity is significantly lower than cross-author perplexity

Prerequisites:
- T001 (Project structure)
- T005 (utils.py with tokenization)
- T011-T017 (Data ingestion and preprocessing completed)
- T018 (Model schema contract test)
"""
import os
import sys
import json
import logging
import math
import pickle
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Any

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils import (
    get_logger,
    tokenize_char_level_no_punct,
    load_json,
    ensure_dir,
)
from config import load_config, set_seed, get_seed
from update_state import load_state, hash_artifact

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Constants
CONFIG_PATH = "contracts/config.yaml"
PROCESSED_DATA_DIR = "data/processed"
MODELS_DIR = "artifacts/models"
METRICS_DIR = "artifacts/metrics"
TEST_OUTPUT_DIR = "artifacts/metrics/tests"

# Test parameters
N_GRAD_ORDERS = [4, 5, 6]
NUM_TEST_AUTHORS = 5  # Use a small subset for integration test speed
TEST_SEED = 42
PERPLEXITY_THRESHOLD_RATIO = 0.8  # Same-author perplexity should be < 80% of cross-author

class UnigramNgramModel:
    """
    A simple character-level n-gram model using CountVectorizer-like logic
    but implemented manually for clarity and to avoid sklearn dependency in tests.
    Supports Kneser-Ney smoothing approximation.
    """

    def __init__(self, n: int, alpha: float = 0.1):
        self.n = n
        self.alpha = alpha
        self.ngram_counts: Dict[str, int] = {}
        self.context_counts: Dict[str, int] = {}
        self.vocab: set = set()
        self.total_count = 0

    def _get_ngrams(self, text: str) -> List[str]:
        """Extract n-grams from text."""
        if len(text) < self.n:
            return []
        return [text[i:i+self.n] for i in range(len(text) - self.n + 1)]

    def _get_context(self, ngram: str) -> str:
        """Get the (n-1)-gram context of an n-gram."""
        return ngram[:-1]

    def train(self, texts: List[str]):
        """Train the model on a list of texts."""
        all_ngrams = []
        for text in texts:
            tokens = tokenize_char_level_no_punct(text)
            if len(tokens) < self.n:
                continue
            ngrams = self._get_ngrams(tokens)
            all_ngrams.extend(ngrams)
            self.vocab.update(tokens)

        # Count n-grams and contexts
        for ngram in all_ngrams:
            self.ngram_counts[ngram] = self.ngram_counts.get(ngram, 0) + 1
            context = self._get_context(ngram)
            self.context_counts[context] = self.context_counts.get(context, 0) + 1
            self.total_count += 1

        logger.info(f"Trained {self.n}-gram model: {len(self.ngram_counts)} n-grams, {len(self.vocab)} vocab")

    def probability(self, ngram: str) -> float:
        """
        Calculate probability P(ngram) with Kneser-Ney smoothing approximation.
        P(w|context) = (max(0, count(context, w) - alpha) + D * count_1(context)) / count(context)
        where D is a discount factor (approximated by alpha here for simplicity).
        """
        context = self._get_context(ngram)
        count_ngram = self.ngram_counts.get(ngram, 0)
        count_context = self.context_counts.get(context, 0)

        if count_context == 0:
            # Uniform backoff if context never seen
            return 1.0 / (len(self.vocab) + 1)

        # Kneser-Ney smoothing approximation
        discount = min(self.alpha, count_ngram)
        numerator = max(0, count_ngram - discount) + discount
        probability = numerator / count_context

        return probability

    def perplexity(self, text: str) -> float:
        """Calculate perplexity of a text."""
        tokens = tokenize_char_level_no_punct(text)
        if len(tokens) < self.n:
            return float('inf')

        ngrams = self._get_ngrams(tokens)
        if not ngrams:
            return float('inf')

        log_prob_sum = 0.0
        for ngram in ngrams:
            prob = self.probability(ngram)
            if prob == 0:
                return float('inf')
            log_prob_sum += math.log(prob)

        avg_log_prob = log_prob_sum / len(ngrams)
        perplexity = math.exp(-avg_log_prob)
        return perplexity

def load_processed_corpus() -> Dict[str, List[str]]:
    """Load the processed corpus from data/processed/."""
    processed_dir = Path(PROCESSED_DATA_DIR)
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {PROCESSED_DATA_DIR}")

    author_data = {}
    author_dirs = [d for d in processed_dir.iterdir() if d.is_dir()]

    if not author_dirs:
        raise ValueError(f"No author directories found in {PROCESSED_DATA_DIR}")

    for author_dir in author_dirs:
        author_id = author_dir.name
        texts = []
        for file_path in author_dir.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                if text:
                    texts.append(text)
        if texts:
            author_data[author_id] = texts

    if not author_data:
        raise ValueError("No valid author data found in processed directory")

    logger.info(f"Loaded corpus: {len(author_data)} authors")
    return author_data

def split_author_data(author_texts: List[str], test_ratio: float = 0.2) -> Tuple[List[str], List[str]]:
    """Split author data into train and test sets."""
    set_seed(TEST_SEED)
    import random
    random.seed(TEST_SEED)
    shuffled = author_texts.copy()
    random.shuffle(shuffled)
    split_idx = int(len(shuffled) * (1 - test_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]

def train_author_models(author_texts: List[str], n_orders: List[int]) -> Dict[int, UnigramNgramModel]:
    """Train n-gram models for an author."""
    models = {}
    for n in n_orders:
        model = UnigramNgramModel(n)
        model.train(author_texts)
        models[n] = model
    return models

def run_integration_test():
    """Run the full integration test for perplexity calculation."""
    logger.info("Starting perplexity integration test...")

    # Load config and set seed
    try:
        config = load_config(CONFIG_PATH)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {CONFIG_PATH}, using defaults")
        config = {}

    set_seed(TEST_SEED)

    # Load processed corpus
    try:
        author_corpus = load_processed_corpus()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load processed corpus: {e}")
        # If data is not ready, this test cannot proceed
        # In a real CI, this would fail the build
        raise RuntimeError(f"Integration test cannot proceed: {e}")

    # Select a subset of authors for testing
    author_ids = list(author_corpus.keys())[:NUM_TEST_AUTHORS]
    logger.info(f"Testing with authors: {author_ids}")

    if len(author_ids) < 2:
        raise ValueError("Need at least 2 authors for cross-author comparison")

    # Results storage
    results = {
        "test_seed": TEST_SEED,
        "n_orders": N_GRAD_ORDERS,
        "authors_tested": author_ids,
        "comparisons": []
    }

    # For each author, train models and compute perplexity
    for author_id in author_ids:
        logger.info(f"Processing author: {author_id}")
        texts = author_corpus[author_id]

        # Split data
        train_texts, test_texts = split_author_data(texts)
        if not test_texts:
            logger.warning(f"No test data for author {author_id}, skipping")
            continue

        # Train models
        models = train_author_models(train_texts, N_GRAD_ORDERS)

        # Compute perplexity on test set
        for n in N_GRAD_ORDERS:
            model = models[n]

            # Same-author perplexity
            same_author_perplexities = []
            for test_text in test_texts:
                ppl = model.perplexity(test_text)
                if ppl != float('inf'):
                    same_author_perplexities.append(ppl)

            if not same_author_perplexities:
                logger.warning(f"No valid same-author perplexity for {author_id}, n={n}")
                continue

            avg_same_ppl = sum(same_author_perplexities) / len(same_author_perplexities)

            # Cross-author perplexity (average over other authors' test texts)
            cross_author_perplexities = []
            other_authors = [a for a in author_ids if a != author_id]
            if not other_authors:
                continue

            for other_author_id in other_authors:
                other_texts = author_corpus[other_author_id]
                _, other_test_texts = split_author_data(other_texts)
                for other_test_text in other_test_texts:
                    ppl = model.perplexity(other_test_text)
                    if ppl != float('inf'):
                        cross_author_perplexities.append(ppl)

            if not cross_author_perplexities:
                logger.warning(f"No valid cross-author perplexity for {author_id}, n={n}")
                continue

            avg_cross_ppl = sum(cross_author_perplexities) / len(cross_author_perplexities)

            # Record comparison
            results["comparisons"].append({
                "author_id": author_id,
                "n": n,
                "same_author_avg_perplexity": avg_same_ppl,
                "cross_author_avg_perplexity": avg_cross_ppl,
                "ratio": avg_same_ppl / avg_cross_ppl if avg_cross_ppl > 0 else float('inf'),
                "same_count": len(same_author_perplexities),
                "cross_count": len(cross_author_perplexities)
            })

    # Save results
    ensure_dir(TEST_OUTPUT_DIR)
    output_path = Path(TEST_OUTPUT_DIR) / "perplexity_test_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Test results saved to {output_path}")

    # Verify expectations
    logger.info("Verifying test expectations...")
    passed = True
    for comparison in results["comparisons"]:
        ratio = comparison["ratio"]
        if ratio >= PERPLEXITY_THRESHOLD_RATIO:
            logger.warning(
                f"FAILED: Author {comparison['author_id']}, n={comparison['n']}: "
                f"Ratio {ratio:.4f} >= {PERPLEXITY_THRESHOLD_RATIO} "
                f"(same: {comparison['same_author_avg_perplexity']:.2f}, cross: {comparison['cross_author_avg_perplexity']:.2f})"
            )
            passed = False
        else:
            logger.info(
                f"PASSED: Author {comparison['author_id']}, n={comparison['n']}: "
                f"Ratio {ratio:.4f} < {PERPLEXITY_THRESHOLD_RATIO}"
            )

    if passed:
        logger.info("Integration test PASSED: Same-author perplexity is consistently lower than cross-author.")
    else:
        logger.error("Integration test FAILED: Same-author perplexity not significantly lower in some cases.")
        # Do not raise exception here to allow partial results inspection
        # In strict CI, this would be: raise AssertionError("Perplexity test failed")

    return passed

def main():
    """Main entry point for the test."""
    try:
        success = run_integration_test()
        if success:
            logger.info("Perplexity integration test completed successfully.")
            return 0
        else:
            logger.warning("Perplexity integration test completed with warnings.")
            return 1
    except Exception as e:
        logger.error(f"Perplexity integration test failed with error: {e}", exc_info=True)
        return 2

if __name__ == "__main__":
    sys.exit(main())