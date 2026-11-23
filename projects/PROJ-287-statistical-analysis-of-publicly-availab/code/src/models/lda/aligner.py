import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

from src.utils.logging import get_logger
from src.models.lda.saver import load_topic_vectors_from_proportions
from src.models.metrics.proportions import save_topic_vectors

logger = get_logger(__name__)


class TopicAligner:
    """
    Aligns topic indices across different time windows using cosine similarity
    of topic-word distributions to resolve label switching.
    """

    def __init__(self, reference_window: str = "2000-2004", similarity_threshold: float = 0.8):
        """
        Initialize the aligner.

        Args:
            reference_window: The window to use as the reference for alignment.
            similarity_threshold: Minimum cosine similarity to consider topics matched.
        """
        self.reference_window = reference_window
        self.similarity_threshold = similarity_threshold
        self.logger = get_logger(__name__)

    def _compute_cosine_similarity_matrix(self, topic_matrix_a: np.ndarray, topic_matrix_b: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity matrix between two topic-word matrices.

        Args:
            topic_matrix_a: Matrix of shape (n_topics_a, n_terms) for window A.
            topic_matrix_b: Matrix of shape (n_topics_b, n_terms) for window B.

        Returns:
            Similarity matrix of shape (n_topics_a, n_topics_b).
        """
        # Normalize rows to unit length
        norm_a = np.linalg.norm(topic_matrix_a, axis=1, keepdims=True)
        norm_b = np.linalg.norm(topic_matrix_b, axis=1, keepdims=True)

        # Avoid division by zero
        norm_a = np.where(norm_a == 0, 1, norm_a)
        norm_b = np.where(norm_b == 0, 1, norm_b)

        unit_a = topic_matrix_a / norm_a
        unit_b = topic_matrix_b / norm_b

        # Cosine similarity is dot product of unit vectors
        similarity = np.dot(unit_a, unit_b.T)
        return similarity

    def _greedy_align(self, sim_matrix: np.ndarray, n_topics: int) -> Dict[int, int]:
        """
        Greedily align topics from source to reference based on similarity matrix.

        Args:
            sim_matrix: Similarity matrix of shape (n_topics_ref, n_topics_source).
            n_topics: Number of topics (assumed equal for both).

        Returns:
            Mapping from source topic index to reference topic index.
        """
        alignment = {}
        used_ref = set()
        used_source = set()

        # Flatten and sort by similarity descending
        indices = np.unravel_index(np.argsort(-sim_matrix), sim_matrix.shape)

        for i, j in zip(indices[0], indices[1]):
            if i not in used_ref and j not in used_source:
                if sim_matrix[i, j] >= self.similarity_threshold:
                    alignment[j] = i
                    used_ref.add(i)
                    used_source.add(j)

        # Handle unmatched topics (assign to nearest valid or keep as is)
        for j in range(n_topics):
            if j not in alignment:
                # Find best match among unused reference topics
                if used_ref:
                    best_match = None
                    best_score = -1
                    for i in range(n_topics):
                        if i not in used_ref and sim_matrix[i, j] > best_score:
                            best_score = sim_matrix[i, j]
                            best_match = i
                    if best_match is not None:
                        alignment[j] = best_match
                        used_ref.add(best_match)
                else:
                    # No reference available, map to self
                    alignment[j] = j

        return alignment

    def align_window_to_reference(
        self,
        reference_topics: np.ndarray,
        target_topics: np.ndarray,
        target_window: str
    ) -> Tuple[np.ndarray, Dict[int, int]]:
        """
        Align a target window's topics to the reference window.

        Args:
            reference_topics: Topic-word matrix for reference window (n_topics, n_terms).
            target_topics: Topic-word matrix for target window (n_topics, n_terms).
            target_window: Identifier for the target window.

        Returns:
            Tuple of (aligned_topics, alignment_mapping).
        """
        if reference_topics.shape[0] != target_topics.shape[0]:
            raise ValueError(
                f"Topic count mismatch: reference has {reference_topics.shape[0]}, "
                f"target {target_window} has {target_topics.shape[0]}"
            )

        n_topics = reference_topics.shape[0]

        # Compute similarity
        sim_matrix = self._compute_cosine_similarity_matrix(reference_topics, target_topics)

        # Greedy alignment
        alignment = self._greedy_align(sim_matrix, n_topics)

        # Reorder target topics
        aligned_topics = np.zeros_like(target_topics)
        for source_idx, ref_idx in alignment.items():
            aligned_topics[ref_idx] = target_topics[source_idx]

        self.logger.info(
            f"Aligned window '{target_window}' to reference '{self.reference_window}'. "
            f"Alignment map: {alignment}"
        )

        return aligned_topics, alignment

    def align_all_windows(
        self,
        topic_vectors_by_window: Dict[str, np.ndarray],
        windows_order: List[str]
    ) -> Dict[str, np.ndarray]:
        """
        Align all windows to the reference window.

        Args:
            topic_vectors_by_window: Dict mapping window name to topic-word matrix.
            windows_order: Ordered list of all windows.

        Returns:
            Dict of aligned topic-word matrices.
        """
        if self.reference_window not in topic_vectors_by_window:
            raise ValueError(
                f"Reference window '{self.reference_window}' not found in topic vectors. "
                f"Available: {list(topic_vectors_by_window.keys())}"
            )

        reference_topics = topic_vectors_by_window[self.reference_window]
        aligned_vectors = {self.reference_window: reference_topics}

        for window in windows_order:
            if window == self.reference_window:
                continue

            if window not in topic_vectors_by_window:
                self.logger.warning(f"Window '{window}' not found, skipping alignment.")
                continue

            target_topics = topic_vectors_by_window[window]
            aligned_topics, _ = self.align_window_to_reference(
                reference_topics, target_topics, window
            )
            aligned_vectors[window] = aligned_topics

        return aligned_vectors


def align_topics_across_windows(
    input_dir: str,
    output_dir: str,
    reference_window: str = "2000-2004",
    similarity_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Main function to align topics across all windows.

    Args:
        input_dir: Directory containing topic vectors (JSON) from T024/T025.
        output_dir: Directory to save aligned topic vectors.
        reference_window: Window to use as reference for alignment.
        similarity_threshold: Minimum cosine similarity for matching.

    Returns:
        Dictionary with alignment results and metadata.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading topic vectors from {input_path}")

    # Load all topic vectors
    topic_vectors_by_window = {}
    windows_order = []

    # Expected windows based on task description
    expected_windows = [
        "2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"
    ]

    for window in expected_windows:
        file_path = input_path / f"topic_vector_{window.replace('-', '_')}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Convert to numpy array
                topic_matrix = np.array(data['topic_word_distributions'])
                topic_vectors_by_window[window] = topic_matrix
                windows_order.append(window)
                logger.info(f"Loaded {window}: {topic_matrix.shape}")
        else:
            logger.warning(f"Topic vector file not found: {file_path}")

    if not topic_vectors_by_window:
        raise FileNotFoundError("No topic vector files found in input directory.")

    if reference_window not in topic_vectors_by_window:
        raise ValueError(
            f"Reference window '{reference_window}' not found in loaded vectors. "
            f"Available: {list(topic_vectors_by_window.keys())}"
        )

    # Perform alignment
    aligner = TopicAligner(reference_window=reference_window, similarity_threshold=similarity_threshold)
    aligned_vectors = aligner.align_all_windows(topic_vectors_by_window, windows_order)

    # Save aligned vectors
    results = {
        "reference_window": reference_window,
        "similarity_threshold": similarity_threshold,
        "aligned_vectors": {},
        "alignment_metadata": {}
    }

    for window, matrix in aligned_vectors.items():
        # Save to file
        output_file = output_path / f"aligned_topic_vector_{window.replace('-', '_')}.json"
        save_data = {
            "window": window,
            "topic_word_distributions": matrix.tolist(),
            "n_topics": matrix.shape[0],
            "n_terms": matrix.shape[1]
        }

        with open(output_file, 'w') as f:
            json.dump(save_data, f, indent=2)

        results["aligned_vectors"][window] = {
            "file": str(output_file),
            "shape": list(matrix.shape)
        }
        results["alignment_metadata"][window] = {
            "n_topics": matrix.shape[0],
            "n_terms": matrix.shape[1]
        }

    # Save alignment summary
    summary_file = output_path / "alignment_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Alignment complete. Summary saved to {summary_file}")
    return results


def main():
    """
    Entry point for running topic alignment.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Align topics across time windows")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="results/stats",
        help="Directory containing unaligned topic vectors"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/stats",
        help="Directory to save aligned topic vectors"
    )
    parser.add_argument(
        "--reference-window",
        type=str,
        default="2000-2004",
        help="Reference window for alignment"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.8,
        help="Minimum cosine similarity for topic matching"
    )

    args = parser.parse_args()

    results = align_topics_across_windows(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        reference_window=args.reference_window,
        similarity_threshold=args.similarity_threshold
    )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()