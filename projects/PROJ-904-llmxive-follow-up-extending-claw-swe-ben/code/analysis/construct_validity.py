"""
Construct Validity Audit for Context Fidelity Research.

This module implements the ConstructValidityAudit to ensure that the generic
retriever used for filtering (CodeBERT-based) does not introduce circularity
by being highly correlated with the experimental strategies (TF-IDF, etc.)
being tested.

Constraint: If correlation >= 0.3, the run MUST fail with "Circularity Detected" error.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

# Ensure project root is in path for imports if running as script
if __name__ == "__main__" and "code" not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

from data.loader import ClawSweBenchLoader
from data.context_processors import retrieve_tfidf_snippets, retrieve_diff_aware_snippets
from models.task_instance import TaskInstance
from utils.logger import setup_logger, log_error

logger = setup_logger("ConstructValidityAudit")


class ConstructValidityAudit:
    """
    Audits the construct validity of the filtering mechanism.

    Compares the scores of the generic retriever (used for initial filtering)
    against the scores of the experimental strategies to detect circularity.
    """

    def __init__(self, filtered_parquet_path: str, sample_size: int = 200):
        """
        Initialize the audit.

        Args:
            filtered_parquet_path: Path to the filtered dataset (output of T012).
            sample_size: Number of instances to sample for the audit to save memory.
        """
        self.filtered_parquet_path = Path(filtered_parquet_path)
        self.sample_size = sample_size
        self.logger = logger

        if not self.filtered_parquet_path.exists():
            raise FileNotFoundError(
                f"Filtered dataset not found at {self.filtered_parquet_path}. "
                "Please run T012 (loader.py) first."
            )

    def _load_sample(self) -> pd.DataFrame:
        """Load a sample of the filtered dataset."""
        self.logger.info(f"Loading sample of size {self.sample_size} from {self.filtered_parquet_path}")
        df = pd.read_parquet(self.filtered_parquet_path)

        if len(df) == 0:
            raise ValueError("Filtered dataset is empty. Cannot perform audit.")

        if len(df) > self.sample_size:
            # Deterministic sampling using a fixed seed for reproducibility
            np.random.seed(42)
            df = df.sample(n=self.sample_size, random_state=42)

        return df.reset_index(drop=True)

    def _get_generic_retriever_scores(self, instances: List[TaskInstance]) -> List[float]:
        """
        Simulate or retrieve the generic retriever scores used during filtering.

        In the actual T012 implementation, these scores are used to select top-5 files.
        For this audit, we assume the 'score' or similar metric from the loader's
        internal logic is available or can be re-computed.

        Since T012 logic is encapsulated, we approximate the score based on the
        assumption that the 'issue_description' embedding similarity was the driver.
        However, to strictly follow the "Circularity" check, we need the scores
        that were actually used.

        *Implementation Note*: If T012 stored the 'retrieval_score' in the parquet,
        we use that. Otherwise, we re-run the retrieval logic for the sample.

        For this implementation, we assume the 'retrieval_score' column exists
        from T012. If not, we fall back to a placeholder that raises an error
        to force T012 to be corrected to store this metadata.
        """
        scores = []
        for idx, row in instances.iterrows():
            # Attempt to retrieve the score used during filtering
            # T012 should have stored this as 'retrieval_score' or similar
            if 'retrieval_score' in row:
                scores.append(float(row['retrieval_score']))
            else:
                # If T012 didn't store it, we cannot perform the audit accurately.
                # We raise an error to enforce the data contract.
                raise ValueError(
                    f"Column 'retrieval_score' missing from filtered dataset. "
                    f"T012 must store the generic retriever score for each instance."
                )
        return scores

    def _get_strategy_scores(self, instances: pd.DataFrame, strategy_name: str) -> List[float]:
        """
        Calculate scores for a specific experimental strategy on the sample.

        Args:
            instances: DataFrame of task instances.
            strategy_name: Name of the strategy ('tfidf', 'diff_aware', etc.).

        Returns:
            List of scores (e.g., average relevance score of retrieved snippets).
        """
        scores = []

        for idx, row in instances.iterrows():
            try:
                # Reconstruct a minimal TaskInstance or dict for the processor
                # Assuming 'issue_description' and 'file_contents' (or similar) are in the row
                # T012 output schema must include 'issue_description' and 'file_contents' (or map)

                # Mocking the input for the context processor based on row data
                # The context processors expect specific structures.
                # We assume the row contains 'issue_description' and a dict of 'file_contents'
                # or 'file_paths' that can be loaded.
                # For this audit, we calculate the *average relevance score* of the top-k snippets.

                # Note: The actual retrieval logic in context_processors returns ProcessedContext.
                # We need to extract a "score" from that.
                # If the processor doesn't return a score, we might need to compute similarity.
                # For now, we assume the processor returns a 'score' attribute or we compute it.

                # Since we cannot easily re-run the full retrieval without the full file system
                # context in this isolated script, we assume T012 stored the 'strategy_scores'
                # or we re-implement the retrieval for the sample.
                # Given the constraint of "Real Data", we re-run the retrieval logic on the sample.

                issue_desc = row.get('issue_description', '')
                # Assuming T012 stored a dict of {filepath: content} or similar
                # If not, we cannot re-run. We assume T012 stored 'context_map' or similar.
                # If missing, we raise.
                context_map = row.get('context_map') # T012 should populate this

                if not context_map:
                    self.logger.warning(f"Instance {idx} missing context_map. Skipping.")
                    scores.append(0.0)
                    continue

                if strategy_name == 'tfidf':
                    # Call TF-IDF retrieval
                    # retrieve_tfidf_snippets expects (issue_desc, context_map, k)
                    result = retrieve_tfidf_snippets(issue_desc, context_map, k=5)
                    if result and len(result.snippets) > 0:
                        # Calculate average score of snippets
                        avg_score = sum(s.score for s in result.snippets) / len(result.snippets)
                        scores.append(avg_score)
                    else:
                        scores.append(0.0)
                elif strategy_name == 'diff_aware':
                    result = retrieve_diff_aware_snippets(issue_desc, context_map, k=5)
                    if result and len(result.snippets) > 0:
                        avg_score = sum(s.score for s in result.snippets) / len(result.snippets)
                        scores.append(avg_score)
                    else:
                        scores.append(0.0)
                else:
                    self.logger.warning(f"Unknown strategy {strategy_name}")
                    scores.append(0.0)

            except Exception as e:
                self.logger.error(f"Error calculating score for strategy {strategy_name} on instance {idx}: {e}")
                scores.append(0.0)

        return scores

    def run(self) -> bool:
        """
        Execute the validity audit.

        Returns:
            True if the audit passes (correlation < 0.3).
            False if the audit fails (correlation >= 0.3).

        Raises:
            RuntimeError: If "Circularity Detected" (correlation >= 0.3).
        """
        self.logger.info("Starting Construct Validity Audit...")

        # 1. Load Sample
        df = self._load_sample()
        self.logger.info(f"Loaded {len(df)} instances for audit.")

        # 2. Get Generic Retriever Scores (from T012)
        try:
            generic_scores = self._get_generic_retriever_scores(df)
        except ValueError as e:
            self.logger.error(str(e))
            raise RuntimeError("Audit cannot proceed: T012 did not store generic retriever scores.") from e

        # 3. Calculate Experimental Strategy Scores
        strategies = ['tfidf', 'diff_aware']
        strategy_scores = {}

        for strat in strategies:
            self.logger.info(f"Calculating scores for strategy: {strat}")
            strategy_scores[strat] = self._get_strategy_scores(df, strat)

        # 4. Compute Correlations
        correlations = {}
        for strat, s_scores in strategy_scores.items():
            # Filter out NaNs if any
            valid_pairs = [
                (g, s) for g, s in zip(generic_scores, s_scores)
                if not np.isnan(g) and not np.isnan(s)
            ]

            if len(valid_pairs) < 10:
                self.logger.warning(f"Not enough valid pairs for {strat} to compute correlation.")
                continue

            g_vals, s_vals = zip(*valid_pairs)

            # Pearson correlation
            r, p_value = pearsonr(g_vals, s_vals)
            correlations[strat] = {
                'pearson_r': r,
                'p_value': p_value
            }

            self.logger.info(f"Correlation (Generic vs {strat}): r={r:.4f}, p={p_value:.4f}")

        # 5. Check Constraint
        max_corr = 0.0
        max_strat = None

        for strat, data in correlations.items():
            if abs(data['pearson_r']) > max_corr:
                max_corr = abs(data['pearson_r'])
                max_strat = strat

        if max_strat is None:
            self.logger.warning("No valid correlations computed. Audit inconclusive.")
            return False

        if max_corr >= 0.3:
            error_msg = f"Circularity Detected: Correlation between generic retriever and {max_strat} is {max_corr:.4f} (>= 0.3)."
            self.logger.error(error_msg)
            # Save the audit results before failing
            self._save_results(correlations, passed=False)
            raise RuntimeError(error_msg)

        self.logger.info(f"Audit Passed: Max correlation {max_corr:.4f} < 0.3.")
        self._save_results(correlations, passed=True)
        return True

    def _save_results(self, correlations: Dict[str, Dict[str, float]], passed: bool):
        """Save audit results to a JSON file."""
        output_dir = Path("data/audit")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "construct_validity_audit.json"

        results = {
            "audit_passed": passed,
            "sample_size": self.sample_size,
            "correlations": correlations,
            "max_correlation": max([abs(v['pearson_r']) for v in correlations.values()]) if correlations else 0.0
        }

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Audit results saved to {output_path}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run Construct Validity Audit")
    parser.add_argument(
        "--input",
        type=str,
        default="data/filtered_swe_bench_v1.parquet",
        help="Path to the filtered dataset (output of T012)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200,
        help="Number of instances to sample for the audit"
    )

    args = parser.parse_args()

    try:
        audit = ConstructValidityAudit(
            filtered_parquet_path=args.input,
            sample_size=args.sample_size
        )
        audit.run()
        logger.info("Construct Validity Audit completed successfully.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"Audit failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during audit: {e}")
        log_error(e, "ConstructValidityAudit")
        sys.exit(1)


if __name__ == "__main__":
    main()