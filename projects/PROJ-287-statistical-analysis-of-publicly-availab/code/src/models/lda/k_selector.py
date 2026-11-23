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
    Selects the optimal number of topics (k) using the elbow method on
    reconstruction error (or held-out likelihood approximation) and
    validates the default k=10.

    This class supports the task:
    T022: Implement src/models/lda/k_selector.py to validate k=10 using
    elbow method/held-out likelihood; select optimal k if needed.
    """

    def __init__(
        self,
        min_k: int = 5,
        max_k: int = 15,
        max_iter: int = 20,
        random_state: Optional[int] = None,
        n_jobs: int = 1,
    ):
        """
        Initialize the KSelector.

        Args:
            min_k: Minimum number of topics to test.
            max_k: Maximum number of topics to test.
            max_iter: Maximum iterations for LDA fitting.
            random_state: Random seed for reproducibility.
            n_jobs: Number of CPU cores to use (-1 for all).
        """
        self.min_k = min_k
        self.max_k = max_k
        self.max_iter = max_iter
        self.random_state = random_state
        self.n_jobs = n_jobs
        self._scores: Dict[int, float] = {}
        self._optimal_k: Optional[int] = None

    def fit_scores(
        self,
        documents: List[str],
        vectorizer: Optional[CountVectorizer] = None,
    ) -> Dict[int, float]:
        """
        Fit LDA models for k in [min_k, max_k] and compute reconstruction error.

        The reconstruction error (||V - WH||_F^2) serves as a proxy for
        held-out likelihood in this CPU-constrained context. Lower is better.

        Args:
            documents: List of preprocessed document strings.
            vectorizer: Optional pre-fitted CountVectorizer. If None, a new one
                        is fitted with standard parameters.

        Returns:
            Dict mapping k -> reconstruction error.
        """
        if not documents:
            raise ValueError("Documents list is empty; cannot fit LDA models.")

        if vectorizer is None:
            vectorizer = CountVectorizer(
                max_df=0.95,
                min_df=2,
                max_features=5000,
                stop_words="english",
            )

        logger.info(f"Vectorizing {len(documents)} documents...")
        try:
            X = vectorizer.fit_transform(documents)
        except ValueError as e:
            logger.error(f"Failed to vectorize documents: {e}")
            raise

        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(
                "Vectorized matrix is empty. Check document content and tokenization."
            )

        self._scores = {}

        logger.info(
            f"Running LDA grid search for k in [{self.min_k}, {self.max_k}]..."
        )

        for k in range(self.min_k, self.max_k + 1):
            logger.info(f"Fitting LDA with k={k}...")
            lda = LatentDirichletAllocation(
                n_components=k,
                max_iter=self.max_iter,
                learning_method="batch",
                random_state=self.random_state,
                n_jobs=self.n_jobs,
                verbose=0,
            )

            try:
                lda.fit(X)
                # Reconstruction error is available as score_ in newer sklearn
                # or we compute ||X - X_reconstructed||_F^2 manually if needed.
                # In sklearn, .score(X) returns the lower bound of the ELBO.
                # We use the negative ELBO as a proxy: higher ELBO (less negative) is better.
                # However, for elbow method on "error", we often look at reconstruction.
                # sklearn LDA doesn't expose reconstruction error directly, but we can
                # approximate it via the likelihood score or compute X_reconstructed.
                # Let's use the negative ELBO (score) as the metric: higher is better.
                # To make it an "error" metric for elbow, we take -score.
                score = lda.score(X)
                # We store the negative score as "error" so lower is better (elbow works on error)
                error_metric = -score
                self._scores[k] = error_metric
                logger.info(f"k={k}: ELBO={score:.4f}, Error Proxy={error_metric:.4f}")
            except Exception as e:
                logger.error(f"Failed to fit LDA for k={k}: {e}")
                self._scores[k] = float("inf")

        return self._scores

    def find_elbow_k(self) -> int:
        """
        Find the optimal k using the knee/elbow method on the computed scores.

        Uses the second derivative (acceleration) of the error curve to find
        the point of maximum curvature.

        Returns:
            The optimal k value.
        """
        if not self._scores:
            raise RuntimeError(
                "No scores computed. Call fit_scores() before find_elbow_k()."
            )

        ks = sorted(self._scores.keys())
        errors = [self._scores[k] for k in ks]

        if len(ks) < 3:
            logger.warning(
                "Not enough points for elbow detection. Returning middle k."
            )
            return ks[len(ks) // 2]

        # Normalize errors to [0, 1] for stability
        min_err = min(errors)
        max_err = max(errors)
        if max_err - min_err == 0:
            normalized = errors
        else:
            normalized = [(e - min_err) / (max_err - min_err) for e in errors]

        # Compute first derivative (slope)
        slopes = np.diff(normalized)
        # Compute second derivative (curvature)
        curvatures = np.diff(slopes)

        # The elbow is where curvature is maximum (most positive change in slope,
        # or least negative if we are looking at decreasing error)
        # Since error decreases then flattens, we look for the point where
        # the rate of decrease slows down most.
        # In a decreasing curve, the "elbow" is where the second derivative is
        # most positive (bending up).
        # However, standard elbow detection often looks for the point of
        # maximum distance from the line connecting start and end, or max curvature.
        # Let's use the point of maximum curvature (max second derivative).
        # Note: np.diff reduces length by 1 each time.
        # curvatures corresponds to indices 1 to len-2 of original ks.

        max_curvature_idx = np.argmax(curvatures)
        # The index in 'ks' corresponds to max_curvature_idx + 1 (because of first diff)
        optimal_idx = max_curvature_idx + 1

        if optimal_idx >= len(ks):
            optimal_idx = len(ks) - 1

        self._optimal_k = ks[optimal_idx]
        logger.info(f"Elbow method selected k={self._optimal_k}")
        return self._optimal_k

    def validate_k_default(
        self,
        documents: List[str],
        default_k: int = 10,
        vectorizer: Optional[CountVectorizer] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate if the default k=10 is optimal or if another k is better.

        Args:
            documents: List of documents.
            default_k: The default number of topics to validate (usually 10).
            vectorizer: Optional vectorizer.

        Returns:
            Tuple of (is_optimal, details_dict).
            details_dict contains:
                - 'scores': dict of k -> error
                - 'optimal_k': int
                - 'is_optimal': bool
                - 'recommendation': str
        """
        self.fit_scores(documents, vectorizer)

        optimal_k = self.find_elbow_k()
        is_optimal = optimal_k == default_k

        details = {
            "scores": self._scores,
            "optimal_k": optimal_k,
            "is_optimal": is_optimal,
            "default_k": default_k,
            "recommendation": (
                f"Use k={optimal_k}"
                if not is_optimal
                else f"Default k={default_k} is optimal"
            ),
        }

        logger.info(f"Validation result: {details['recommendation']}")
        return is_optimal, details

    def save_results(
        self,
        output_path: str,
        window_name: Optional[str] = None,
        validation_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save the k-selection results to a JSON file.

        Args:
            output_path: Path to save the JSON file.
            window_name: Optional name of the time window.
            validation_details: Optional details from validate_k_default.
        """
        results = {
            "window": window_name,
            "min_k": self.min_k,
            "max_k": self.max_k,
            "scores": self._scores,
            "optimal_k": self._optimal_k,
        }

        if validation_details:
            results["validation"] = validation_details

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved k-selection results to {output_path}")


def main() -> None:
    """
    Main entry point for running the KSelector as a script.
    This script is intended to be run after data preprocessing (T016)
    and before LDA fitting (T020) to determine the optimal k.
    It loads a sample of processed data, runs the selection, and saves results.
    """
    logger.info("Starting K-Selector validation...")

    # Configuration
    # In a real pipeline, this would be passed via config or command line args.
    # Here we assume the processed data exists at the expected path.
    processed_data_dir = Path("data/processed")
    if not processed_data_dir.exists():
        logger.error(
            "Processed data directory not found. "
            "Please run T016 (saver.py) first."
        )
        return

    # Load a sample of documents from the first available window file
    # This is a heuristic for the script; the actual pipeline passes data directly.
    window_files = list(processed_data_dir.glob("window_*.csv"))
    if not window_files:
        logger.error("No window files found in data/processed.")
        return

    # Load one window for demonstration/validation
    sample_file = window_files[0]
    logger.info(f"Loading sample data from {sample_file}...")

    try:
        import pandas as pd

        df = pd.read_csv(sample_file)
        if "tokens" not in df.columns and "text" not in df.columns:
            logger.error(
                f"CSV {sample_file} must contain 'tokens' or 'text' column."
            )
            return

        text_col = "tokens" if "tokens" in df.columns else "text"
        # Ensure tokens are joined if they are lists
        if isinstance(df[text_col].iloc[0], list):
            documents = [" ".join(t) for t in df[text_col]]
        else:
            documents = df[text_col].tolist()

        logger.info(f"Loaded {len(documents)} documents.")
    except Exception as e:
        logger.error(f"Failed to load data from {sample_file}: {e}")
        return

    # Initialize and run selector
    selector = KSelector(min_k=5, max_k=15, max_iter=20, random_state=42)

    is_optimal, details = selector.validate_k_default(documents)

    # Save results
    output_path = "results/stats/k_selection_results.json"
    selector.save_results(output_path, validation_details=details)

    if not is_optimal:
        logger.warning(
            f"Default k=10 is NOT optimal. Recommended k={details['optimal_k']}. "
            "Downstream tasks (T020) should use the recommended k."
        )
    else:
        logger.info("Default k=10 is validated as optimal.")


if __name__ == "__main__":
    main()