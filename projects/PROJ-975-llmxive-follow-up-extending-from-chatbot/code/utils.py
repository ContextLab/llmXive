"""
Utility functions shared across the llmXive follow‑up project.
"""
import numpy as np

def mean_pairwise_similarity(embeddings: np.ndarray) -> float:
    """
    Compute the mean cosine similarity between all unique pairs of
    unit‑norm vectors in ``embeddings``.

    Parameters
    ----------
    embeddings: np.ndarray
        A 2‑D array of shape (n_items, dim). Vectors are assumed to be
        already normalised; if not, they will be normalised internally.

    Returns
    -------
    float
        The average cosine similarity over all distinct pairs.
    """
    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a 2‑D array")
    # Normalise rows to unit length (guard against zero norm)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normed = embeddings / norms
    # Cosine similarity of unit vectors is just dot product
    sim_matrix = normed @ normed.T
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    return float(sim_matrix[mask].mean())
