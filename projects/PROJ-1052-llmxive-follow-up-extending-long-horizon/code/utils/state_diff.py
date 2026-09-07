"""
State Diff Module for Recovery Segment Identification.

Implements FR-007: Recovery segment identification using cosine similarity
of sentence embeddings as a proxy for attention-weighted overlap.

This module avoids circularity by not using the model's internal attention
weights, instead relying on semantic similarity of context segments.
"""

import logging
import math
from typing import List, Dict, Any, Tuple, Optional

# Lazy import to avoid heavy dependency unless used
_sentence_transformers = None

logger = logging.getLogger(__name__)

def _get_sentence_transformer():
    """Lazily import sentence-transformers to avoid heavy startup cost."""
    global _sentence_transformers
    if _sentence_transformers is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use a lightweight but effective model for semantic similarity
            # all-MiniLM-L6-v2 is fast and effective for this purpose
            _sentence_transformers = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        except ImportError:
            raise ImportError(
                "The 'sentence-transformers' package is required for state_diff. "
                "Install it via: pip install sentence-transformers"
            )
    return _sentence_transformers

def _embed_text(text: str) -> List[float]:
    """
    Generate a sentence embedding for the given text.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.
    """
    if not text or not text.strip():
        # Return zero vector for empty text to avoid model errors
        # Dimension matches all-MiniLM-L6-v2 (384)
        return [0.0] * 384

    model = _get_sentence_transformer()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity value between -1 and 1.
    """
    if not vec_a or not vec_b:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)

def identify_recovery_segments(
    trajectory: List[Dict[str, Any]],
    error_start_index: int,
    threshold: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Identify recovery-critical segments in a trajectory using cosine similarity.

    This function segments the trajectory into context windows before the error
    and calculates which segments contribute most to the semantic state change
    observed after the error, using cosine similarity of sentence embeddings.

    Args:
        trajectory: List of steps in the trajectory, each containing 'observation',
                   'action', 'reward', etc.
        error_start_index: The index in the trajectory where the error state begins.
        threshold: Minimum contribution threshold (0.0 to 1.0) to be considered
                  recovery-critical. Segments contributing less than this are
                  discarded.

    Returns:
        List of dictionaries containing segment_id, start_index, end_index,
        contribution_score, and text_snippet for recovery-critical segments.
    """
    if error_start_index <= 0:
        logger.warning("Error start index is 0 or less; no prior context to analyze.")
        return []

    # Extract context segments before the error
    # We treat each step's observation as a potential segment
    context_steps = trajectory[:error_start_index]

    if not context_steps:
        logger.warning("No context steps found before error.")
        return []

    # Get the error state observation (the state after error injection)
    error_observation = trajectory[error_start_index].get('observation', '')

    # Embed all context observations and the error observation
    logger.debug(f"Embedding {len(context_steps)} context steps and error observation...")

    context_embeddings = []
    context_texts = []

    for i, step in enumerate(context_steps):
        obs = step.get('observation', '')
        if not obs:
            continue
        emb = _embed_text(obs)
        context_embeddings.append(emb)
        context_texts.append(obs)

    if not context_embeddings:
        logger.warning("No valid observations to embed in context.")
        return []

    error_embedding = _embed_text(error_observation)

    # Calculate semantic drift for each segment
    # We measure how much each context segment's embedding correlates with
    # the error state, normalized by total drift
    segment_scores = []

    total_drift = 0.0
    for i, ctx_emb in enumerate(context_embeddings):
        # Calculate similarity between this context segment and the error state
        # Lower similarity implies this segment is more distinct/different from
        # the error state, potentially indicating it was "lost" or "changed"
        # However, for recovery, we want segments that are semantically related
        # to the error state (high similarity) as they contain relevant context
        similarity = cosine_similarity(ctx_emb, error_embedding)
        segment_scores.append({
            'index': i,
            'similarity': similarity,
            'text': context_texts[i]
        })
        total_drift += (1.0 - similarity)  # Drift = 1 - similarity

    if total_drift == 0:
        # All segments are identical to error state (or all zero)
        # No useful differentiation possible
        logger.warning("Total drift is zero; cannot differentiate segments.")
        return []

    # Normalize scores to get contribution percentages
    # Higher contribution = segment is more similar to error state (critical context)
    critical_segments = []
    for score in segment_scores:
        contribution = (1.0 - score['similarity']) / total_drift
        # Invert: if we want segments that are DISTINCT from the error (which caused the error),
        # we might use similarity directly. But for "recovery", we want context that helps
        # resolve the error, which should be semantically related.
        # Let's use a different metric: how much this segment's presence changes the state.
        # Actually, let's measure: if we remove this segment, how much does the similarity
        # to the error state change? (Leave-one-out approach)

        # For efficiency, we'll use a simpler heuristic:
        # Segments with high similarity to the error state are likely "recovery-critical"
        # because they contain the semantic content needed to recover.
        # Normalize by the sum of all similarities
        pass

    # Recalculate using a more direct approach:
    # Sum of all similarities
    total_similarity = sum(s['similarity'] for s in segment_scores)
    if total_similarity == 0:
        logger.warning("Total similarity is zero; no segments contribute to error state.")
        return []

    for score in segment_scores:
        contribution = score['similarity'] / total_similarity
        if contribution >= threshold:
            critical_segments.append({
                'segment_id': f"seg_{score['index']}",
                'start_index': score['index'],
                'end_index': score['index'] + 1,
                'contribution_score': contribution,
                'text_snippet': score['text'][:200] + "..." if len(score['text']) > 200 else score['text'],
                'similarity_to_error': score['similarity']
            })

    # Sort by contribution score descending
    critical_segments.sort(key=lambda x: x['contribution_score'], reverse=True)

    logger.info(f"Identified {len(critical_segments)} recovery-critical segments "
               f"above threshold {threshold:.2f}")

    return critical_segments

def calculate_state_diff_embedding(
    state_before: Dict[str, Any],
    state_after: Dict[str, Any]
) -> float:
    """
    Calculate the semantic difference between two states using embeddings.

    Args:
        state_before: Dictionary representing the state before an action/error.
        state_after: Dictionary representing the state after an action/error.

    Returns:
        A float representing the semantic distance (1 - cosine_similarity) between
        the two states. 0 means identical, 1 means completely different.
    """
    # Extract relevant text fields for comparison
    # Typically 'observation' is the key state indicator
    obs_before = state_before.get('observation', '')
    obs_after = state_after.get('observation', '')

    emb_before = _embed_text(obs_before)
    emb_after = _embed_text(obs_after)

    similarity = cosine_similarity(emb_before, emb_after)
    return 1.0 - similarity  # Distance metric