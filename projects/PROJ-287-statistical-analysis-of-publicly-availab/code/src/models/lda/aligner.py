"""
Topic Alignment Module for Temporal LDA Analysis.

This module implements the alignment of topic indices across different time windows
to resolve the label switching problem inherent in LDA models. It uses cosine
similarity of topic-word distributions to find the optimal permutation of topic
indices for each subsequent window relative to a reference window.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment

from src.utils.logging import get_logger
from src.utils.manifest import load_reproducibility_manifest, save_reproducibility_manifest

logger = get_logger(__name__)


class TopicAligner:
    """
    Aligns topic indices across multiple time windows using cosine similarity
    and the Hungarian algorithm for optimal assignment.
    """

    def __init__(self, reference_window: str = "2000-2004"):
        """
        Initialize the TopicAligner.

        Args:
            reference_window: The time window to use as the reference for alignment.
                              Defaults to the first window (2000-2004).
        """
        self.reference_window = reference_window
        self.alignment_map: Dict[str, Dict[int, int]] = {}
        self.similarity_matrices: Dict[Tuple[str, str], np.ndarray] = {}

    def load_topic_vectors(self, stats_dir: Path, windows: List[str]) -> Dict[str, np.ndarray]:
        """
        Load topic-word distributions for all windows from the stats directory.

        Args:
            stats_dir: Path to the results/stats directory containing topic_vectors.json.
            windows: List of window identifiers (e.g., ['2000-2004', '2005-2009', ...]).

        Returns:
            Dictionary mapping window identifiers to topic-word distribution matrices.
        """
        topic_vectors_path = stats_dir / "topic_vectors.json"
        
        if not topic_vectors_path.exists():
            raise FileNotFoundError(
                f"Topic vectors file not found at {topic_vectors_path}. "
                "Ensure T020 (LDA fitting) and T024 (proportions) have been completed."
            )

        with open(topic_vectors_path, 'r') as f:
            data = json.load(f)

        topic_matrices = {}
        for window in windows:
            if window not in data:
                raise ValueError(f"Window {window} not found in topic_vectors.json")
            
            # Extract the topic-word distribution matrix
            # Expected format: {"window_id": {"topics": [[word_prob, ...], ...]}}
            window_data = data[window]
            topics = window_data.get("topics", [])
            
            if not topics:
                raise ValueError(f"No topics found for window {window}")
            
            topic_matrix = np.array(topics, dtype=np.float64)
            topic_matrices[window] = topic_matrix
            logger.info(f"Loaded topic matrix for {window}: shape {topic_matrix.shape}")

        return topic_matrices

    def compute_similarity_matrix(
        self, 
        ref_matrix: np.ndarray, 
        target_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Compute the cosine similarity matrix between reference and target topic distributions.

        Args:
            ref_matrix: Reference topic-word distribution (n_topics_ref x n_words).
            target_matrix: Target topic-word distribution (n_topics_target x n_words).

        Returns:
            Similarity matrix (n_topics_ref x n_topics_target).
        """
        # Ensure matrices are normalized (topic-word distributions should sum to 1)
        ref_norm = ref_matrix / (np.linalg.norm(ref_matrix, axis=1, keepdims=True) + 1e-10)
        target_norm = target_matrix / (np.linalg.norm(target_matrix, axis=1, keepdims=True) + 1e-10)
        
        similarity = cosine_similarity(ref_norm, target_norm)
        return similarity

    def find_optimal_permutation(self, similarity_matrix: np.ndarray) -> np.ndarray:
        """
        Find the optimal permutation of target topics to match reference topics
        using the Hungarian algorithm (linear sum assignment).

        The Hungarian algorithm minimizes cost, so we negate the similarity matrix.

        Args:
            similarity_matrix: Cosine similarity matrix (n_ref x n_target).

        Returns:
            Array of target indices mapped to reference indices.
            result[i] = j means reference topic i is aligned to target topic j.
        """
        # Negate similarity to convert maximization to minimization
        cost_matrix = -similarity_matrix
        
        # Apply Hungarian algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # col_ind[i] gives the target topic index that best matches reference topic i
        return col_ind

    def align_window(
        self, 
        ref_window: str, 
        target_window: str, 
        ref_matrix: np.ndarray, 
        target_matrix: np.ndarray
    ) -> Tuple[Dict[int, int], np.ndarray]:
        """
        Align a target window's topics to a reference window.

        Args:
            ref_window: Identifier of the reference window.
            target_window: Identifier of the target window.
            ref_matrix: Topic-word distribution for reference window.
            target_matrix: Topic-word distribution for target window.

        Returns:
            Tuple of (alignment_map, similarity_matrix).
            alignment_map: Dictionary mapping target topic indices to reference indices.
        """
        logger.info(f"Aligning {target_window} to {ref_window}")
        
        similarity_matrix = self.compute_similarity_matrix(ref_matrix, target_matrix)
        permutation = self.find_optimal_permutation(similarity_matrix)
        
        # Create alignment map: target_idx -> ref_idx
        # permutation[i] = j means reference topic i matches target topic j
        # We want: for each target topic j, which reference topic i does it correspond to?
        alignment_map = {}
        for ref_idx, target_idx in enumerate(permutation):
            alignment_map[target_idx] = ref_idx
        
        self.similarity_matrices[(ref_window, target_window)] = similarity_matrix
        logger.info(
            f"Alignment complete. "
            f"Max similarity: {np.max(similarity_matrix):.4f}, "
            f"Mean similarity: {np.mean(similarity_matrix):.4f}"
        )
        
        return alignment_map, similarity_matrix

    def align_all_windows(
        self, 
        topic_matrices: Dict[str, np.ndarray], 
        windows: List[str]
    ) -> Dict[str, Dict[int, int]]:
        """
        Align all windows to the reference window.

        Args:
            topic_matrices: Dictionary of window_id -> topic matrix.
            windows: Ordered list of windows (first is reference).

        Returns:
            Dictionary mapping each window (except reference) to its alignment map.
        """
        if self.reference_window not in topic_matrices:
            raise ValueError(f"Reference window {self.reference_window} not in topic matrices")

        ref_matrix = topic_matrices[self.reference_window]
        self.alignment_map[self.reference_window] = {i: i for i in range(ref_matrix.shape[0])}
        
        for window in windows:
            if window == self.reference_window:
                continue
            
            target_matrix = topic_matrices[window]
            alignment_map, _ = self.align_window(
                self.reference_window, window, ref_matrix, target_matrix
            )
            self.alignment_map[window] = alignment_map

        return self.alignment_map

    def apply_alignment(
        self, 
        window: str, 
        topic_vector: np.ndarray
    ) -> np.ndarray:
        """
        Apply the alignment permutation to a topic proportion vector.

        Args:
            window: The window identifier.
            topic_vector: Original topic proportion vector (n_topics,).

        Returns:
            Aligned topic proportion vector.
        """
        if window not in self.alignment_map:
            raise ValueError(f"No alignment map found for window {window}")
        
        if window == self.reference_window:
            return topic_vector.copy()

        alignment_map = self.alignment_map[window]
        aligned_vector = np.zeros_like(topic_vector)
        
        for target_idx, ref_idx in alignment_map.items():
            if ref_idx < len(aligned_vector):
                aligned_vector[ref_idx] = topic_vector[target_idx]
            else:
                logger.warning(
                    f"Reference index {ref_idx} out of bounds for aligned vector of size {len(aligned_vector)}"
                )

        return aligned_vector

    def save_alignment_results(self, output_path: Path) -> None:
        """
        Save alignment results to a JSON file.

        Args:
            output_path: Path to save the alignment results.
        """
        results = {
            "reference_window": self.reference_window,
            "alignment_maps": {
                window: {str(k): v for k, v in map_dict.items()}
                for window, map_dict in self.alignment_map.items()
            },
            "similarity_matrices": {
                f"{k[0]}_{k[1]}": similarity.tolist()
                for k, similarity in self.similarity_matrices.items()
            }
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Alignment results saved to {output_path}")

    def update_manifest(self, manifest_path: Path) -> None:
        """
        Update the reproducibility manifest with alignment information.

        Args:
            manifest_path: Path to the manifest file.
        """
        manifest = load_reproducibility_manifest(manifest_path)
        
        manifest["topic_alignment"] = {
            "reference_window": self.reference_window,
            "alignment_performed": True,
            "windows_aligned": list(self.alignment_map.keys())
        }
        
        save_reproducibility_manifest(manifest, manifest_path)
        logger.info("Manifest updated with topic alignment information")


def align_topics_across_windows(
    stats_dir: Union[str, Path],
    output_dir: Union[str, Path],
    windows: Optional[List[str]] = None,
    reference_window: str = "2000-2004"
) -> TopicAligner:
    """
    Main function to align topics across all windows.

    Args:
        stats_dir: Path to the results/stats directory.
        output_dir: Path to save alignment results.
        windows: List of window identifiers. If None, inferred from topic_vectors.json.
        reference_window: The reference window for alignment.

    Returns:
        The configured TopicAligner instance.
    """
    stats_dir = Path(stats_dir)
    output_dir = Path(output_dir)

    logger.info(f"Starting topic alignment for windows: {windows}")
    
    aligner = TopicAligner(reference_window=reference_window)
    topic_matrices = aligner.load_topic_vectors(stats_dir, windows)
    
    if windows is None:
        windows = list(topic_matrices.keys())
    
    # Ensure reference window is first in the list
    if reference_window in windows:
        windows.remove(reference_window)
        windows.insert(0, reference_window)
    
    aligner.align_all_windows(topic_matrices, windows)
    
    # Save results
    alignment_output = output_dir / "topic_alignment.json"
    aligner.save_alignment_results(alignment_output)
    
    # Update manifest
    manifest_path = stats_dir.parent / "manifest.json"
    if manifest_path.exists():
        aligner.update_manifest(manifest_path)
    
    logger.info("Topic alignment completed successfully")
    return aligner


def main():
    """
    Entry point for topic alignment from command line.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Align LDA topics across time windows")
    parser.add_argument(
        "--stats-dir", 
        type=str, 
        default="results/stats",
        help="Directory containing topic_vectors.json"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="results/stats",
        help="Directory to save alignment results"
    )
    parser.add_argument(
        "--reference-window", 
        type=str, 
        default="2000-2004",
        help="Reference window for alignment"
    )
    parser.add_argument(
        "--windows", 
        type=str, 
        nargs="+",
        default=["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"],
        help="List of window identifiers"
    )
    
    args = parser.parse_args()
    
    align_topics_across_windows(
        stats_dir=args.stats_dir,
        output_dir=args.output_dir,
        windows=args.windows,
        reference_window=args.reference_window
    )


if __name__ == "__main__":
    main()
