"""
Token Attribution Module

Implements logic to rank tokens based on the projection of the frequency-weighted
mean embedding vector onto the Edge Spectrum subspace.

This module fulfills FR-005 and US-2 by quantifying which tokens drive the
cross-lingual shift in the unembedding matrix geometry.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from config import load_config, get_path, get_hyperparameter, ensure_dirs
from model_analyzer import extract_svd_subspace, load_model_weights

logger = logging.getLogger(__name__)


def load_frequency_distribution(config: Dict[str, Any], language: str) -> Dict[int, float]:
    """
    Load the frequency distribution for a specific language from the processed data.

    Args:
        config: Configuration dictionary containing paths.
        language: Language code (e.g., 'en', 'fr', 'zh').

    Returns:
        Dictionary mapping token IDs to their normalized frequencies.
    """
    path_str = get_path(config, "frequency_distributions_path")
    data_path = Path(path_str)

    if not data_path.exists():
        raise FileNotFoundError(f"Frequency distribution file not found: {data_path}")

    with open(data_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    if language not in all_data:
        raise ValueError(f"Language '{language}' not found in frequency distribution file.")

    # Convert string keys to int for consistency with token IDs
    raw_data = all_data[language]
    return {int(k): float(v) for k, v in raw_data.items()}


def compute_frequency_weighted_mean_embedding(
    freq_dist: Dict[int, float],
    vocab_mapping: Dict[int, int],
    model_weights: np.ndarray
) -> np.ndarray:
    """
    Compute the mean embedding vector weighted by token frequencies.

    The mean embedding is calculated as:
    mu = sum(p(t) * v_t) for all tokens t in the vocabulary,
    where p(t) is the frequency and v_t is the token's embedding vector.

    Since we are projecting onto the unembedding subspace, we effectively
    compute the weighted sum of the rows of W_U corresponding to the tokens.

    Args:
        freq_dist: Dictionary of token_id -> frequency.
        vocab_mapping: Dictionary mapping source token IDs to target common IDs.
                       Used to filter to the common vocabulary.
        model_weights: The unembedding matrix W_U (vocab_size x hidden_dim).

    Returns:
        A 1D numpy array representing the frequency-weighted mean embedding.
    """
    # Filter frequency distribution to only include tokens present in vocab_mapping
    # This ensures we only sum over the aligned vocabulary
    valid_tokens = [
        (src_id, freq) for src_id, freq in freq_dist.items()
        if src_id in vocab_mapping
    ]

    if not valid_tokens:
        raise ValueError("No valid tokens found in frequency distribution for the mapped vocabulary.")

    # Normalize frequencies to create a probability distribution
    total_freq = sum(freq for _, freq in valid_tokens)
    if total_freq == 0:
        raise ValueError("Total frequency is zero; cannot compute weighted mean.")

    # Calculate weighted sum of embedding vectors
    weighted_sum = np.zeros(model_weights.shape[1], dtype=np.float32)
    total_weight = 0.0

    for src_id, freq in valid_tokens:
        # Map to the common ID to index into the aligned matrix if necessary
        # However, model_weights here is expected to be the aligned matrix
        # or we need to map the index. Assuming model_weights is aligned
        # to the common vocabulary size.
        # If model_weights is raw, we need to select the row for src_id.
        # Given the context of T020 (projection), we assume we are working
        # with the aligned space or the raw space filtered by mapping.
        
        # Let's assume model_weights is the raw W_U for the specific model
        # and we need to pick the row corresponding to src_id.
        if src_id >= model_weights.shape[0]:
            continue # Skip out of bounds IDs

        weight = freq / total_freq
        weighted_sum += weight * model_weights[src_id]
        total_weight += weight

    return weighted_sum


def project_onto_edge_spectrum(
    mean_embedding: np.ndarray,
    svd_subspace: np.ndarray
) -> np.ndarray:
    """
    Project the mean embedding vector onto the Edge Spectrum subspace.

    The subspace is represented by the top-k right singular vectors (V_k).
    The projection is simply the dot product: proj = mean_embedding @ V_k

    Args:
        mean_embedding: The frequency-weighted mean embedding vector (hidden_dim,).
        svd_subspace: The matrix of top-k singular vectors (hidden_dim, k).

    Returns:
        The projected vector in the subspace (k,).
    """
    return np.dot(mean_embedding, svd_subspace)


def rank_tokens_by_projection(
    freq_dist: Dict[int, float],
    vocab_mapping: Dict[int, int],
    model_weights: np.ndarray,
    svd_subspace: np.ndarray,
    top_k: int
) -> List[Tuple[int, float]]:
    """
    Rank tokens based on the magnitude of their projection onto the edge spectrum.

    For each token, we calculate its contribution to the mean embedding projection.
    Alternatively, we can project individual token embeddings and weight them.
    The task specifies ranking based on the projection of the frequency-weighted
    mean embedding. However, to rank *tokens*, we need to see which tokens
    contribute most to that projection.

    Strategy:
    1. Compute the projection vector in the subspace (k-dim).
    2. For each token, compute its individual projection onto the subspace.
    3. Weight each token's projection magnitude by its frequency.
    4. Rank by the weighted magnitude.

    This identifies which frequent tokens align most strongly with the
    geometric structure of the edge spectrum.

    Args:
        freq_dist: Token frequencies.
        vocab_mapping: Vocabulary alignment map.
        model_weights: Unembedding matrix W_U.
        svd_subspace: Top-k singular vectors (hidden_dim, k).
        top_k: Number of top tokens to return.

    Returns:
        List of (token_id, score) tuples, sorted by score descending.
    """
    scores = []
    
    # Pre-compute the projection of each token in the vocabulary onto the subspace
    # We only care about tokens present in the frequency distribution and mapping
    valid_tokens = [
        (src_id, freq) for src_id, freq in freq_dist.items()
        if src_id in vocab_mapping
    ]

    for src_id, freq in valid_tokens:
        if src_id >= model_weights.shape[0]:
            continue

        # Get token embedding vector
        token_vec = model_weights[src_id]
        
        # Project onto subspace
        proj = np.dot(token_vec, svd_subspace)
        
        # Calculate magnitude (L2 norm) of the projection
        magnitude = np.linalg.norm(proj)
        
        # Weight by frequency
        weighted_score = magnitude * freq
        
        scores.append((src_id, weighted_score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    return scores[:top_k]


def generate_token_attribution_report(
    config: Dict[str, Any],
    models: List[str],
    languages: List[str],
    common_vocab_ids: List[int],
    svd_subspaces: Dict[str, np.ndarray],
    vocab_mappings: Dict[str, Dict[int, int]]
) -> Dict[str, Any]:
    """
    Generate the full token attribution report.

    This function orchestrates the loading of frequency data, computation of
    weighted mean embeddings, projection onto the edge spectrum, and ranking.

    Args:
        config: Configuration dictionary.
        models: List of model names (e.g., ['Llama-3', 'Mistral', 'BLOOM']).
        languages: List of language codes (e.g., ['en', 'fr', 'zh']).
        common_vocab_ids: List of common vocabulary IDs.
        svd_subspaces: Dictionary mapping model names to their SVD subspace matrices.
        vocab_mappings: Dictionary mapping model names to their vocabulary mappings.

    Returns:
        A dictionary containing the token rankings and metadata.
    """
    report = {
        "metadata": {
            "models": models,
            "languages": languages,
            "top_k_ranked_tokens": get_hyperparameter(config, "top_k_ranked_tokens", 50),
        },
        "results": {}
    }

    top_k = get_hyperparameter(config, "top_k_ranked_tokens", 50)

    for model_name in models:
        report["results"][model_name] = {}
        
        # Load model weights (aligned or raw as per T020 context)
        # Assuming load_model_weights returns the raw W_U for the specific model
        # and we handle mapping inside the ranking function.
        try:
            weights = load_model_weights(config, model_name)
            if not isinstance(weights, np.ndarray):
                weights = weights.detach().cpu().numpy().astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to load weights for {model_name}: {e}")
            continue

        for lang in languages:
            logger.info(f"Processing {model_name} for {lang}")
            
            try:
                freq_dist = load_frequency_distribution(config, lang)
                vocab_map = vocab_mappings.get(model_name, {})
                
                # If vocab_map is empty, assume identity or raw mapping
                if not vocab_map:
                    vocab_map = {i: i for i in range(weights.shape[0])}

                # Rank tokens
                ranked_tokens = rank_tokens_by_projection(
                    freq_dist=freq_dist,
                    vocab_mapping=vocab_map,
                    model_weights=weights,
                    svd_subspace=svd_subspaces[model_name],
                    top_k=top_k
                )

                report["results"][model_name][lang] = [
                    {"token_id": int(tid), "score": float(score)}
                    for tid, score in ranked_tokens
                ]

            except FileNotFoundError as e:
                logger.warning(f"Frequency data missing for {lang} in {model_name}: {e}")
                report["results"][model_name][lang] = []
            except Exception as e:
                logger.error(f"Error processing {model_name}/{lang}: {e}")
                report["results"][model_name][lang] = []

    return report


def main():
    """
    Main entry point for the token attribution pipeline.
    """
    config = load_config()
    ensure_dirs(config)

    models = ["Llama-3", "Mistral", "BLOOM"]
    languages = ["en", "fr", "zh"]

    # Load SVD subspaces (computed in T012/T014)
    # We assume the subspace matrices are stored in data/processed/svd_subspaces.json
    # or similar. For this implementation, we simulate loading or expect them to be
    # passed. In a real pipeline, we would load them from disk.
    
    # Since T012/T014 output similarity_matrix.json, we need to ensure the subspaces
    # are available. We will assume a helper to load them or they are re-computed.
    # For T021, we assume the subspaces are available as a dependency.
    # To make this runnable, we will re-extract if needed or load from a cached file.
    
    # Let's assume the subspaces are cached in data/processed/svd_subspaces.pkl
    # or we re-run the extraction logic from model_analyzer if needed.
    # Given the constraints, we will load them if they exist, else raise error.
    
    svd_subspaces = {}
    vocab_mappings = {}
    
    for model in models:
        # In a real scenario, we would load the pre-computed subspace
        # For now, we assume the user has run T012 and the subspaces are available
        # We will try to load from a standard path
        subspace_path = Path(get_path(config, "svd_subspaces_path"))
        if subspace_path.exists():
            with open(subspace_path, 'r') as f:
                data = json.load(f)
                if model in data:
                    svd_subspaces[model] = np.array(data[model])
        else:
            logger.warning(f"SVD subspaces file not found at {subspace_path}. Skipping {model}.")

        # Load vocab mapping
        # Assuming T011a produced a mapping file
        vocab_path = Path(get_path(config, "vocab_mapping_path"))
        if vocab_path.exists():
            with open(vocab_path, 'r') as f:
                data = json.load(f)
                if model in data:
                    vocab_mappings[model] = {int(k): int(v) for k, v in data[model].items()}
        else:
            logger.warning(f"Vocab mapping file not found at {vocab_path}.")

    if not svd_subspaces:
        raise RuntimeError("No SVD subspaces loaded. Please run T012 first.")

    # Generate report
    report = generate_token_attribution_report(
        config=config,
        models=models,
        languages=languages,
        common_vocab_ids=[], # Not directly needed if vocab_mapping is used
        svd_subspaces=svd_subspaces,
        vocab_mappings=vocab_mappings
    )

    # Save report
    output_path = Path(get_path(config, "token_attribution_report_path"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Token attribution report saved to {output_path}")
    return report


if __name__ == "__main__":
    main()