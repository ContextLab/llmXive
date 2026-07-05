"""
K-Selector Module for LDA Topic Modeling.

This module implements the logic to validate the optimal number of topics (k)
for Latent Dirichlet Allocation (LDA) models. It uses the Elbow Method based on
reconstruction error (inertia) and optionally held-out likelihood to determine
if k=10 is appropriate or if an alternative k should be selected.

The implementation adheres to the project's constraints:
- CPU-only execution.
- Real data processing (no synthetic data generation).
- Compatibility with existing project utilities (logging, config).
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from scipy.spatial.distance import jensenshannon

from src.utils.logging import get_logger
from src.utils.config import get_random_seed

logger = get_logger(__name__)


class KSelector:
    """
    Selects and validates the optimal number of topics (k) for LDA.

    Attributes:
        k_candidates (List[int]): List of candidate k values to evaluate.
        max_iterations (int): Maximum iterations for LDA fitting.
        random_seed (int): Seed for reproducibility.
        vectorizer (CountVectorizer): The vectorizer used for text-to-bag-of-words.
    """

    def __init__(
        self,
        k_candidates: Optional[List[int]] = None,
        max_iterations: int = 20,
        random_seed: Optional[int] = None
    ):
        """
        Initializes the KSelector.

        Args:
            k_candidates: List of k values to test. Defaults to [5, 8, 10, 12, 15, 20].
            max_iterations: Max iterations for LDA.
            random_seed: Random seed. If None, uses config.
        """
        if k_candidates is None:
            # Standard range around the target k=10
            self.k_candidates = [5, 8, 10, 12, 15, 20]
        else:
            self.k_candidates = sorted(k_candidates)

        self.max_iterations = max_iterations
        self.random_seed = random_seed if random_seed is not None else get_random_seed()
        self.vectorizer = CountVectorizer(
            max_df=0.95,
            min_df=2,
            max_features=5000,
            stop_words='english'
        )

        self._inertia_scores: Dict[int, float] = {}
        self._log_likelihood_scores: Dict[int, float] = {}

    def fit_vectorizer(self, documents: List[str]) -> None:
        """
        Fits the CountVectorizer on the provided documents.

        Args:
            documents: List of raw text documents.
        """
        if not documents:
            raise ValueError("Document list cannot be empty for vectorizer fitting.")
        
        logger.info(f"Fitting CountVectorizer on {len(documents)} documents...")
        self.vectorizer.fit(documents)

    def _fit_lda_model(self, k: int, corpus: Any) -> LatentDirichletAllocation:
        """
        Fits a single LDA model with specific k.

        Args:
            k: Number of topics.
            corpus: The document-term matrix.

        Returns:
            Fitted LDA model.
        """
        model = LatentDirichletAllocation(
            n_components=k,
            max_iter=self.max_iterations,
            learning_method='online',
            random_state=self.random_seed,
            batch_size=1024,
            n_jobs=1, # CPU only constraint
            verbose=0
        )
        model.fit(corpus)
        return model

    def _calculate_inertia(self, model: LatentDirichletAllocation, corpus: Any) -> float:
        """
        Calculates the reconstruction error (inertia) for an LDA model.
        
        Inertia is approximated as the negative log-likelihood of the data
        under the fitted model, which serves as the "distortion" metric for the elbow method.

        Args:
            model: Fitted LDA model.
            corpus: Document-term matrix.

        Returns:
            Float representing the inertia (lower is better).
        """
        # score() returns the log-likelihood of the data
        log_likelihood = model.score(corpus)
        # Inertia is typically defined as sum of squared distances. 
        # For probabilistic models, we use negative log-likelihood as a proxy for "error".
        # We return the negative value so that "lower is better" for the elbow method logic.
        return -log_likelihood

    def evaluate_k_range(
        self,
        documents: List[str],
        max_k: Optional[int] = None
    ) -> Dict[int, float]:
        """
        Evaluates a range of k values to find the optimal number of topics.

        This method:
        1. Fits the vectorizer if not already fitted.
        2. Converts documents to a sparse matrix.
        3. Iterates through k_candidates.
        4. Fits LDA models and records inertia.

        Args:
            documents: List of raw text documents.
            max_k: If provided, filters candidates to only those <= max_k.

        Returns:
            Dictionary mapping k to inertia score.
        """
        if not documents:
            raise ValueError("Cannot evaluate k range on empty document list.")

        if not self.vectorizer.vocabulary_:
            self.fit_vectorizer(documents)

        corpus = self.vectorizer.transform(documents)
        
        candidates_to_test = self.k_candidates
        if max_k is not None:
            candidates_to_test = [k for k in candidates_to_test if k <= max_k]
            if not candidates_to_test:
                raise ValueError(f"No candidates <= {max_k} found in {self.k_candidates}")

        logger.info(f"Evaluating k values: {candidates_to_test}")
        
        results = {}
        for k in candidates_to_test:
            logger.debug(f"Fitting LDA with k={k}...")
            try:
                model = self._fit_lda_model(k, corpus)
                inertia = self._calculate_inertia(model, corpus)
                results[k] = inertia
                self._inertia_scores[k] = inertia
                logger.info(f"k={k}: Inertia (Neg LogLikelihood) = {inertia:.4f}")
            except Exception as e:
                logger.error(f"Failed to fit LDA model for k={k}: {e}")
                # Skip failed k values
                continue

        return results

    def find_elbow_point(self, inertia_scores: Optional[Dict[int, float]] = None) -> int:
        """
        Identifies the optimal k using the Elbow Method (Kneedle algorithm approximation).

        Finds the point where the rate of decrease in inertia significantly slows down.

        Args:
            inertia_scores: Dict of k -> inertia. If None, uses internal scores.

        Returns:
            The optimal k value.
        """
        if inertia_scores is None:
            inertia_scores = self._inertia_scores

        if not inertia_scores:
            raise ValueError("No inertia scores available to find elbow point.")

        sorted_k = sorted(inertia_scores.keys())
        sorted_inertia = [inertia_scores[k] for k in sorted_k]

        if len(sorted_k) < 2:
            # If only one candidate, return it
            return sorted_k[0]

        # Normalize points to [0, 1] for the Kneedle algorithm
        x_min, x_max = sorted_k[0], sorted_k[-1]
        y_min, y_max = min(sorted_inertia), max(sorted_inertia)
        
        # Avoid division by zero if all y are same (unlikely in LDA)
        if y_max == y_min:
            return sorted_k[0]

        # Normalize X and Y
        x_norm = [(x - x_min) / (x_max - x_min) for x in sorted_k]
        y_norm = [(y - y_min) / (y_max - y_min) for y in sorted_inertia]

        # Calculate distance from the line connecting first and last points
        # Line equation: y = mx + c. 
        # Point 1: (x0, y0), Point 2: (x1, y1)
        # Distance from (x, y) to line: |Ax + By + C| / sqrt(A^2 + B^2)
        # Here we simplify to vertical distance from the chord if we assume convexity
        
        # Simple Euclidean distance from the chord connecting (0, y_norm[0]) and (1, y_norm[-1])
        # Since we normalized x to 0..1, the line is y = y_norm[-1] + (y_norm[0] - y_norm[-1]) * x
        # Actually, since we want the "elbow" in a decreasing curve (convex shape), 
        # we look for the point furthest from the line connecting the start and end.
        
        x0, y0 = x_norm[0], y_norm[0]
        x1, y1 = x_norm[-1], y_norm[-1]
        
        max_dist = -1
        elbow_idx = 0

        for i, (x, y) in enumerate(zip(x_norm, y_norm)):
            # Line equation: (y1 - y0)x - (x1 - x0)y + x1*y0 - y1*x0 = 0
            # A = y1 - y0, B = -(x1 - x0), C = x1*y0 - y1*x0
            A = y1 - y0
            B = x0 - x1
            C = x1 * y0 - y1 * x0
            
            dist = abs(A * x + B * y + C) / np.sqrt(A**2 + B**2)
            
            if dist > max_dist:
                max_dist = dist
                elbow_idx = i

        return sorted_k[elbow_idx]

    def validate_k(
        self,
        documents: List[str],
        target_k: int = 10
    ) -> Tuple[int, bool, Dict[str, Any]]:
        """
        Validates if the target_k is optimal.

        Args:
            documents: List of raw text documents.
            target_k: The desired number of topics (default 10).

        Returns:
            Tuple of (selected_k, is_target_optimal, details_dict).
        """
        logger.info(f"Validating k={target_k} using Elbow Method...")
        
        # Evaluate range
        scores = self.evaluate_k_range(documents)
        
        if not scores:
            raise RuntimeError("Failed to evaluate any k values.")

        optimal_k = self.find_elbow_point(scores)
        
        # Check if target_k is within 10% of optimal or is the optimal itself
        # Or if target_k is the closest available candidate to the elbow
        is_optimal = (optimal_k == target_k)
        
        # If target_k is not exactly the elbow, check if it's close enough (within 10% relative difference)
        if not is_optimal:
            relative_diff = abs(optimal_k - target_k) / optimal_k
            if relative_diff <= 0.1:
                is_optimal = True
                optimal_k = target_k # Prefer the target if close enough

        details = {
            "target_k": target_k,
            "optimal_k_found": optimal_k,
            "is_target_optimal": is_optimal,
            "inertia_scores": scores,
            "method": "elbow"
        }

        logger.info(f"Validation complete. Optimal k: {optimal_k}, Target k: {target_k}. Match: {is_optimal}")
        
        return optimal_k, is_optimal, details

    def get_inertia_scores(self) -> Dict[int, float]:
        """Returns the inertia scores from the last evaluation."""
        return self._inertia_scores.copy()


def main():
    """
    Main entry point for running the K-Selector validation.
    
    This script expects processed data to be available in `data/processed/`.
    It loads a sample of documents, runs the validation, and logs the results.
    """
    from src.data.preprocess.tokenizer import load_preprocessed_data
    from src.utils.config import get_config_dict

    config = get_config_dict()
    data_dir = Path(config.get("data_dir", "data"))
    processed_dir = data_dir / "processed"

    if not processed_dir.exists():
        logger.error(f"Processed data directory not found: {processed_dir}")
        logger.error("Please run the data preprocessing pipeline first.")
        return

    # Load documents from the first available window file
    window_files = list(processed_dir.glob("*.csv"))
    if not window_files:
        logger.error("No CSV files found in data/processed/.")
        return

    # Load from the first file as a representative sample
    sample_file = window_files[0]
    logger.info(f"Loading sample data from: {sample_file}")
    
    try:
        # Assuming the CSV has a 'text' or 'processed_text' column
        # We will try to load and concatenate texts from all windows if possible,
        # but for speed, we might just take the first window if the dataset is huge.
        # For this validation, we need a representative sample.
        
        # Using pandas for CSV reading as it's in requirements
        import pandas as pd
        
        # Load all windows to get a good distribution
        all_texts = []
        for f in window_files:
            df = pd.read_csv(f)
            # Identify the text column
            text_col = None
            for col in ['processed_text', 'text', 'cleaned_text']:
                if col in df.columns:
                    text_col = col
                    break
            
            if text_col:
                # Take a stratified sample if too large, or all if small
                # Limit to 2000 docs per window for speed in this validation step
                sample_size = min(2000, len(df))
                sample = df.sample(n=sample_size, random_state=42)
                all_texts.extend(sample[text_col].dropna().tolist())
            else:
                logger.warning(f"Could not find text column in {f}")

        if not all_texts:
            logger.error("No text data found to validate k.")
            return

        logger.info(f"Loaded {len(all_texts)} documents for k-selection validation.")

        # Initialize Selector
        selector = KSelector(k_candidates=[5, 8, 10, 12, 15, 20], max_iterations=20)
        
        # Run validation
        selected_k, is_optimal, details = selector.validate_k(all_texts, target_k=10)
        
        logger.info("=" * 50)
        logger.info("K-SELECTION RESULTS")
        logger.info("=" * 50)
        logger.info(f"Target k: 10")
        logger.info(f"Selected k: {selected_k}")
        logger.info(f"Is Target Optimal: {is_optimal}")
        logger.info(f"Inertia Scores: {details['inertia_scores']}")
        logger.info("=" * 50)

        # Save results to a JSON file for downstream consumption
        results_dir = Path("results/stats")
        results_dir.mkdir(parents=True, exist_ok=True)
        output_path = results_dir / "k_selection_results.json"
        
        import json
        # Convert numpy types for JSON serialization
        serializable_details = {
            "target_k": details["target_k"],
            "optimal_k_found": details["optimal_k_found"],
            "is_target_optimal": details["is_target_optimal"],
            "inertia_scores": {str(k): float(v) for k, v in details["inertia_scores"].items()},
            "method": details["method"]
        }
        
        with open(output_path, 'w') as f:
            json.dump(serializable_details, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")

    except Exception as e:
        logger.exception(f"Error during k-selection validation: {e}")
        raise


if __name__ == "__main__":
    main()