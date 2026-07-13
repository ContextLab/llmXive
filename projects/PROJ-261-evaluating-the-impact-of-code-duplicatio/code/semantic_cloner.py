"""
Semantic cloner utilities.

Provides compute_semantic_distance_batch which computes a simple
semantic distance between code snippets using TF‑IDF vectors and cosine
similarity. The distance for each snippet is defined as 1 minus the
maximum cosine similarity to any *other* snippet in the batch. For a
single‑element batch the distance is defined as 0.0.
"""

from __future__ import annotations

from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_semantic_distance_batch(snippets: List[str]) -> List[float]:
    """
    Compute semantic distances for a batch of code snippets.

    Parameters
    ----------
    snippets: List[str]
        List of source‑code strings.

    Returns
    -------
    List[float]
        Distance for each input snippet. Distance is 0 for identical
        snippets and >0 for dissimilar ones.
    """
    if not isinstance(snippets, list):
        raise TypeError("snippets must be a list of strings")
    if len(snippets) == 0:
        return []

    # TF‑IDF representation (character n‑grams capture code structure)
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    tfidf_matrix = vectorizer.fit_transform(snippets)

    # Cosine similarity matrix
    similarity = cosine_similarity(tfidf_matrix)

    distances: List[float] = []
    for i in range(len(snippets)):
        # Exclude self‑similarity
        other_sims = np.delete(similarity[i], i)
        if other_sims.size == 0:
            # Single element batch
            distances.append(0.0)
        else:
            max_sim = other_sims.max()
            distances.append(1.0 - max_sim)
    return distances