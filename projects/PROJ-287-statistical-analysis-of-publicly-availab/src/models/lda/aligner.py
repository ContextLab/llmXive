import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

from src.utils.logging import get_logger
from src.models.entities import TopicVector
from src.models.lda.saver import load_topic_vectors_from_proportions

logger = get_logger(__name__)

class TopicAligner:
    """
    Aligns topic indices across different time windows using cosine similarity
    of topic-word distributions to resolve label switching.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the aligner.

        Args:
            similarity_threshold: Minimum cosine similarity to consider two topics matched.
        """
        self.similarity_threshold = similarity_threshold
        self.logger = get_logger(__name__)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector (topic-word distribution).
            vec2: Second vector (topic-word distribution).

        Returns:
            Cosine similarity value between -1 and 1.
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def build_similarity_matrix(
        self, topic_vectors_by_window: Dict[str, List[np.ndarray]]
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Build a pairwise similarity matrix between topics of two windows.

        Args:
            topic_vectors_by_window: Dictionary mapping window names to lists of topic vectors.
                                   Each list contains k numpy arrays of shape (vocab_size,).

        Returns:
            Dictionary with 'window1', 'window2', and 'similarity_matrix' (k x k).
        """
        windows = list(topic_vectors_by_window.keys())
        if len(windows) != 2:
            raise ValueError("build_similarity_matrix expects exactly two windows for pairwise alignment.")

        w1, w2 = windows
        vecs1 = topic_vectors_by_window[w1]
        vecs2 = topic_vectors_by_window[w2]

        k1 = len(vecs1)
        k2 = len(vecs2)

        if k1 == 0 or k2 == 0:
            raise ValueError("One or both windows have no topic vectors.")

        sim_matrix = np.zeros((k1, k2))

        for i in range(k1):
            for j in range(k2):
                sim_matrix[i, j] = self.cosine_similarity(vecs1[i], vecs2[j])

        return {
            "window1": w1,
            "window2": w2,
            "similarity_matrix": sim_matrix
        }

    def align_two_windows(
        self, sim_matrix: np.ndarray
    ) -> Tuple[List[int], List[float]]:
        """
        Perform greedy assignment to align topics from window 1 to window 2.

        Args:
            sim_matrix: k1 x k2 similarity matrix.

        Returns:
            Tuple of (mapping_list, confidence_scores).
            mapping_list: List of length k1 where mapping_list[i] is the index in window 2
                          that topic i in window 1 aligns to. -1 if no match found.
            confidence_scores: List of similarity scores for the matches.
        """
        k1, k2 = sim_matrix.shape
        mapping = [-1] * k1
        used_in_w2 = set()
        scores = [0.0] * k1

        # Flatten and sort all similarities descending
        indices = np.unravel_index(np.argsort(sim_matrix, axis=None), sim_matrix.shape)
        sorted_indices = list(zip(indices[0], indices[1]))[::-1]

        for i, j in sorted_indices:
            if mapping[i] == -1 and j not in used_in_w2:
                if sim_matrix[i, j] >= self.similarity_threshold:
                    mapping[i] = int(j)
                    scores[i] = float(sim_matrix[i, j])
                    used_in_w2.add(j)
                else:
                    # If the best match is below threshold, we stop or mark as -1
                    # For greedy, we continue to see if lower ones match, but typically
                    # if max is low, others are lower.
                    pass

        # Log unmatched topics
        unmatched = [i for i, m in enumerate(mapping) if m == -1]
        if unmatched:
            self.logger.warning(f"Topics in window 1 not matched above threshold: {unmatched}")

        return mapping, scores

    def align_sequence(
        self,
        topic_vectors_by_window: Dict[str, List[np.ndarray]],
        window_order: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Align topics across a sequence of windows.
        Strategy: Align each window to the previous one in the sequence.
        The first window is the reference.

        Args:
            topic_vectors_by_window: Dict of window_name -> list of topic vectors.
            window_order: Ordered list of window names (e.g., ['2000-2004', '2005-2009', ...]).

        Returns:
            Dictionary containing:
            - 'alignments': Nested dict mapping (ref_window, target_window) -> {mapping, scores}
            - 'reordered_vectors': Dict of window_name -> list of reordered vectors
        """
        if len(window_order) < 2:
            return {"alignments": {}, "reordered_vectors": topic_vectors_by_window}

        alignments = {}
        reordered_vectors = {}
        reordered_vectors[window_order[0]] = topic_vectors_by_window[window_order[0]]

        current_vectors = topic_vectors_by_window[window_order[0]]

        for i in range(1, len(window_order)):
            prev_window = window_order[i-1]
            curr_window = window_order[i]

            curr_vectors = topic_vectors_by_window[curr_window]

            # Build similarity matrix between prev (ref) and curr (target)
            sim_data = self.build_similarity_matrix({prev_window: current_vectors, curr_window: curr_vectors})
            sim_matrix = sim_data["similarity_matrix"]

            mapping, scores = self.align_two_windows(sim_matrix)

            key = f"{prev_window}_to_{curr_window}"
            alignments[key] = {
                "reference_window": prev_window,
                "target_window": curr_window,
                "mapping": mapping,
                "scores": scores
            }

            # Reorder current vectors based on mapping
            # We want the reordered vector at index j to be the one that maps to j from the previous window's perspective?
            # Actually, standard alignment: we want to permute the CURRENT window's topics such that topic j
            # in the current window corresponds to topic j in the reference window.
            # The mapping returned is: mapping[i] = j means topic i in prev matches topic j in curr.
            # We want to reorder 'curr_vectors' so that the new index k corresponds to the topic that matches prev's k.
            # So if mapping[k] = j, then curr_vectors[j] should move to position k.

            k_curr = len(curr_vectors)
            new_curr_vectors = [None] * k_curr
            matched_count = 0

            for i, j in enumerate(mapping):
                if j != -1:
                    new_curr_vectors[i] = curr_vectors[j]
                    matched_count += 1
                else:
                    # No match found for prev topic i. We need to fill this slot with an unmatched curr topic.
                    pass

            # Fill remaining slots with unmatched topics from curr
            unmatched_indices = [x for x in range(k_curr) if x not in mapping or mapping.index(x) == -1] # This logic is flawed if multiple map to same or none
            # Better: find which curr indices are used
            used_curr_indices = set([j for j in mapping if j != -1])
            all_curr_indices = set(range(k_curr))
            free_curr_indices = list(all_curr_indices - used_curr_indices)

            free_idx = 0
            for i in range(k_curr):
                if new_curr_vectors[i] is None:
                    if free_idx < len(free_curr_indices):
                        new_curr_vectors[i] = curr_vectors[free_curr_indices[free_idx]]
                        free_idx += 1
                    else:
                        # Should not happen if k1 == k2
                        new_curr_vectors[i] = curr_vectors[0] # Fallback

            reordered_vectors[curr_window] = new_curr_vectors
            current_vectors = new_curr_vectors

        return {
            "alignments": alignments,
            "reordered_vectors": reordered_vectors
        }


def align_topics_across_windows(
    topic_vectors_path: str,
    output_path: str,
    window_order: Optional[List[str]] = None,
    similarity_threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Main function to align topics across windows.

    Args:
        topic_vectors_path: Path to the JSON file containing topic vectors per window.
        output_path: Path to save the aligned topic vectors and alignment metadata.
        window_order: Optional explicit order of windows. If None, inferred from keys.
        similarity_threshold: Threshold for matching topics.

    Returns:
        Dictionary with alignment results.
    """
    logger.info(f"Loading topic vectors from {topic_vectors_path}")
    topic_data = load_topic_vectors_from_proportions(topic_vectors_path)

    if not topic_data or "windows" not in topic_data:
        raise ValueError(f"Invalid topic vector file format at {topic_vectors_path}")

    windows_data = topic_data["windows"]
    if window_order is None:
        # Sort keys to ensure consistent order (e.g., 2000-2004, 2005-2009...)
        window_order = sorted(windows_data.keys())

    aligner = TopicAligner(similarity_threshold=similarity_threshold)

    # Convert data to list of arrays format expected by aligner
    vectors_by_window = {}
    for w_name in window_order:
        if w_name not in windows_data:
            logger.warning(f"Window {w_name} not found in data, skipping.")
            continue
        w_data = windows_data[w_name]
        if "topic_vectors" not in w_data:
            raise ValueError(f"Missing 'topic_vectors' for window {w_name}")

        # Load vectors from JSON (list of lists)
        vecs = [np.array(v) for v in w_data["topic_vectors"]]
        vectors_by_window[w_name] = vecs

    result = aligner.align_sequence(vectors_by_window, window_order)

    # Prepare output
    aligned_output = {
        "alignment_metadata": {
            "window_order": window_order,
            "similarity_threshold": similarity_threshold,
            "pairwise_alignments": result["alignments"]
        },
        "windows": {}
    }

    for w_name, vecs in result["reordered_vectors"].items():
        aligned_output["windows"][w_name] = {
            "topic_vectors": [v.tolist() for v in vecs],
            "is_aligned": True,
            "original_window": w_name
        }

    logger.info(f"Saving aligned topics to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aligned_output, f, indent=2)

    return aligned_output


def main():
    """
    Entry point for the aligner script.
    Expects topic vectors to be saved at results/stats/topic_vectors.json
    and saves aligned results to results/stats/aligned_topic_vectors.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Align LDA topics across time windows.")
    parser.add_argument(
        "--input",
        type=str,
        default="results/stats/topic_vectors.json",
        help="Path to input topic vectors JSON."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/stats/aligned_topic_vectors.json",
        help="Path to save aligned topic vectors."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Cosine similarity threshold for matching."
    )
    parser.add_argument(
        "--windows",
        type=str,
        nargs="+",
        default=["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"],
        help="Ordered list of window names."
    )

    args = parser.parse_args()

    setup_logging()
    logger = get_logger(__name__)

    try:
        align_topics_across_windows(
            topic_vectors_path=args.input,
            output_path=args.output,
            window_order=args.windows,
            similarity_threshold=args.threshold
        )
        logger.info("Topic alignment completed successfully.")
    except Exception as e:
        logger.error(f"Topic alignment failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
