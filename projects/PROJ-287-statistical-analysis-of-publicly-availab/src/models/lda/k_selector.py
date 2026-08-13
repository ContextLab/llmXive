import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class KSelector:
    """
    Validates k=10 using the elbow method on reconstruction error (or held-out likelihood approximation).
    Selects optimal k if the target k=10 is not within the optimal range defined by the elbow.

    This class implements a heuristic to determine the optimal number of topics (k) for LDA.
    It fits multiple LDA models with varying k values and analyzes the reconstruction error (or perplexity).
    The 'elbow' in the error curve suggests the optimal k.
    """

    def __init__(
        self,
        min_k: int = 5,
        max_k: int = 20,
        target_k: int = 10,
        max_iter: int = 20,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        """
        Initialize the KSelector.

        Args:
            min_k: Minimum number of topics to test.
            max_k: Maximum number of topics to test.
            target_k: The target number of topics (default 10) to validate.
            max_iter: Maximum iterations for LDA fitting.
            random_state: Random seed for reproducibility.
            n_jobs: Number of CPU cores to use (-1 for all).
        """
        self.min_k = min_k
        self.max_k = max_k
        self.target_k = target_k
        self.max_iter = max_iter
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.logger = get_logger(__name__)

    def fit_models(
        self,
        corpus: List[str],
        vocabulary_size: int
    ) -> Tuple[List[float], List[Dict[str, Any]]]:
        """
        Fit LDA models for k in range(min_k, max_k + 1) and collect metrics.

        Args:
            corpus: List of preprocessed documents (space-separated tokens).
            vocabulary_size: Size of the vocabulary.

        Returns:
            A tuple containing:
            - List of reconstruction errors (or negative log-likelihoods).
            - List of model details (k, error, coherence_approx).
        """
        self.logger.info(f"Fitting LDA models for k in range [{self.min_k}, {self.max_k}]")
        
        # Vectorize the corpus
        vectorizer = CountVectorizer(max_features=vocabulary_size, token_pattern=r"(?u)\b\w+\b")
        try:
            X = vectorizer.fit_transform(corpus)
        except ValueError as e:
            self.logger.error(f"Failed to vectorize corpus: {e}")
            raise

        if X.shape[0] == 0:
            raise ValueError("Corpus is empty after vectorization.")

        errors = []
        model_details = []

        for k in range(self.min_k, self.max_k + 1):
            self.logger.debug(f"Fitting LDA with k={k}...")
            lda = LatentDirichletAllocation(
                n_components=k,
                max_iter=self.max_iter,
                learning_method='batch',
                random_state=self.random_state,
                n_jobs=self.n_jobs,
                verbose=0
            )
            
            try:
                lda.fit(X)
                # Reconstruction error: ||X - WH||_F^2
                # sklearn doesn't expose reconstruction error directly, 
                # but we can approximate using the score (negative log likelihood) 
                # or calculate the Frobenius norm of the difference.
                # Using score (higher is better, so we negate for error-like metric)
                score = lda.score(X)
                reconstruction_error = -score 
                
                errors.append(reconstruction_error)
                model_details.append({
                    "k": k,
                    "reconstruction_error": float(reconstruction_error),
                    "score": float(score),
                    "status": "success"
                })
                self.logger.debug(f"k={k}: Score={score:.4f}, Error={reconstruction_error:.4f}")
            except Exception as e:
                self.logger.warning(f"Failed to fit LDA with k={k}: {e}")
                errors.append(float('inf'))
                model_details.append({
                    "k": k,
                    "reconstruction_error": float('inf'),
                    "score": float('-inf'),
                    "status": "failed"
                })

        return errors, model_details

    def find_elbow(self, errors: List[float]) -> int:
        """
        Find the 'elbow' point in the error curve using the maximum curvature method.
        
        The elbow is the point where the rate of decrease in error slows down significantly.
        We calculate the distance from each point to the line connecting the first and last points.
        The point with the maximum distance is the elbow.

        Args:
            errors: List of reconstruction errors corresponding to k values.

        Returns:
            The k value at the elbow.
        """
        ks = list(range(self.min_k, self.max_k + 1))
        valid_indices = [i for i, e in enumerate(errors) if e != float('inf')]
        
        if len(valid_indices) < 3:
            self.logger.warning("Not enough valid points to compute elbow. Returning target_k.")
            return self.target_k

        # Filter to valid points
        valid_ks = [ks[i] for i in valid_indices]
        valid_errors = [errors[i] for i in valid_indices]

        # Normalize to [0, 1] for stability
        x_min, x_max = min(valid_ks), max(valid_ks)
        y_min, y_max = min(valid_errors), max(valid_errors)
        
        if x_max == x_min or y_max == y_min:
            return valid_ks[len(valid_ks) // 2]

        x_norm = [(x - x_min) / (x_max - x_min) for x in valid_ks]
        y_norm = [(y - y_min) / (y_max - y_min) for y in valid_errors]

        # Line from first to last point
        p1 = np.array([x_norm[0], y_norm[0]])
        p2 = np.array([x_norm[-1], y_norm[-1]])
        
        max_dist = -1
        elbow_idx = 0

        for i, (x, y) in enumerate(zip(x_norm, y_norm)):
            p = np.array([x, y])
            # Distance from point to line
            dist = np.abs(np.cross(p2 - p1, p1 - p)) / np.linalg.norm(p2 - p1)
            if dist > max_dist:
                max_dist = dist
                elbow_idx = i

        return valid_ks[elbow_idx]

    def validate_target_k(
        self,
        optimal_k: int,
        tolerance: float = 0.1
    ) -> bool:
        """
        Check if the target_k is within the tolerance range of the optimal_k.

        Args:
            optimal_k: The k value determined by the elbow method.
            tolerance: Tolerance percentage (e.g., 0.1 for 10%).

        Returns:
            True if target_k is optimal, False otherwise.
        """
        lower_bound = optimal_k * (1 - tolerance)
        upper_bound = optimal_k * (1 + tolerance)
        return lower_bound <= self.target_k <= upper_bound

    def run_analysis(
        self,
        corpus: List[str],
        vocabulary_size: int,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Run the full k-selection analysis.

        Args:
            corpus: List of preprocessed documents.
            vocabulary_size: Size of the vocabulary.
            output_path: Optional path to save the results JSON.

        Returns:
            Dictionary containing analysis results.
        """
        self.logger.info("Starting K-Selection Analysis")
        
        errors, model_details = self.fit_models(corpus, vocabulary_size)
        optimal_k = self.find_elbow(errors)
        is_target_valid = self.validate_target_k(optimal_k)

        results = {
            "target_k": self.target_k,
            "optimal_k": optimal_k,
            "is_target_valid": is_target_valid,
            "tolerance": 0.1,
            "models_fitted": model_details,
            "recommendation": "Use target_k=10" if is_target_valid else f"Consider using k={optimal_k}"
        }

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            self.logger.info(f"Results saved to {output_path}")

        return results


def main():
    """
    Entry point for running the KSelector as a script.
    This is intended to be called by the main pipeline or for testing.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run K-Selector for LDA topic modeling.")
    parser.add_argument("--corpus-path", type=str, required=True, help="Path to JSONL file containing processed documents.")
    parser.add_argument("--output", type=str, default="results/stats/k_selection_results.json", help="Output path for results.")
    parser.add_argument("--min-k", type=int, default=5, help="Minimum k to test.")
    parser.add_argument("--max-k", type=int, default=20, help="Maximum k to test.")
    parser.add_argument("--target-k", type=int, default=10, help="Target k to validate.")
    
    args = parser.parse_args()

    logger.info(f"Loading corpus from {args.corpus_path}")
    
    corpus = []
    vocab_set = set()
    
    with open(args.corpus_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            if 'tokens' in data and isinstance(data['tokens'], list):
                text = " ".join(data['tokens'])
                corpus.append(text)
                vocab_set.update(data['tokens'])
            elif 'text' in data:
                # Fallback if text is already a string
                corpus.append(data['text'])
                # Simple split for vocab estimation if tokens not present
                vocab_set.update(data['text'].split())

    if not corpus:
        logger.error("No documents found in corpus.")
        return

    vocabulary_size = len(vocab_set)
    logger.info(f"Corpus size: {len(corpus)}, Vocabulary size: {vocabulary_size}")

    selector = KSelector(
        min_k=args.min_k,
        max_k=args.max_k,
        target_k=args.target_k
    )

    results = selector.run_analysis(
        corpus=corpus,
        vocabulary_size=vocabulary_size,
        output_path=Path(args.output)
    )

    logger.info(f"Analysis complete. Recommendation: {results['recommendation']}")
    logger.info(f"Optimal k: {results['optimal_k']}, Target k valid: {results['is_target_valid']}")


if __name__ == "__main__":
    main()
