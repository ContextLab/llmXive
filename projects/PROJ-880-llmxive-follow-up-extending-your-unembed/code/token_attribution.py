"""
Token attribution module for projecting frequency distributions onto subspace.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from config import load_config, get_path, get_hyperparameter, ensure_dirs

def load_frequency_distribution(config: Dict, language: str) -> Dict[str, float]:
    """Load frequency distribution for a given language."""
    path_map = {
        "en": "data/processed/frequency_distributions_en.json",
        "fr": "data/processed/frequency_distributions_fr.json",
        "zh": "data/processed/frequency_distributions_zh.json"
    }
    file_path = get_path(config, "data_processed") / path_map.get(language, f"data/processed/frequency_distributions_{language}.json")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Frequency distribution not found for {language}")
    
    with open(file_path, "r") as f:
        return json.load(f)

def compute_frequency_weighted_mean_embedding(freq_dist: Dict[str, float], W_U: np.ndarray, tokenizer_vocab: Dict[str, int]) -> np.ndarray:
    """Compute the mean embedding vector weighted by frequency."""
    total_weight = 0.0
    weighted_sum = np.zeros(W_U.shape[1])
    
    for token, freq in freq_dist.items():
        if token in tokenizer_vocab:
            idx = tokenizer_vocab[token]
            if idx < W_U.shape[0]:
                weighted_sum += freq * W_U[idx].cpu().numpy()
                total_weight += freq
    
    if total_weight == 0:
        return np.zeros(W_U.shape[1])
    
    return weighted_sum / total_weight

def project_onto_edge_spectrum(mean_embedding: np.ndarray, V_edge: np.ndarray) -> np.ndarray:
    """Project a vector onto the edge spectrum subspace."""
    # V_edge is shape (k, vocab_size) or (k, hidden_dim) depending on context
    # Assuming V_edge is the basis of the subspace (k, hidden_dim)
    # Project: P = V^T * (V * V^T)^-1 * V * x  (orthogonal projection)
    # Simplified for orthonormal basis: P = V^T * (V * x)
    return V_edge @ mean_embedding

def rank_tokens_by_projection(projection_scores: np.ndarray, tokenizer_vocab: Dict[str, int], top_n: int = 100) -> List[Tuple[str, float]]:
    """Rank tokens by their projection scores."""
    # Reverse mapping
    vocab_to_token = {v: k for k, v in tokenizer_vocab.items()}
    
    # Get top indices
    top_indices = np.argsort(projection_scores)[::-1][:top_n]
    
    results = []
    for idx in top_indices:
        # Find token with this index in vocab
        # This is a simplified lookup; real implementation needs robust mapping
        for token, token_idx in tokenizer_vocab.items():
            if token_idx == idx:
                results.append((token, float(projection_scores[idx])))
                break
    
    return results

def generate_token_attribution_report(config: Dict, language: str, W_U: np.ndarray, V_edge: np.ndarray, tokenizer_vocab: Dict[str, int]) -> Dict[str, Any]:
    """Generate the full token attribution report."""
    freq_dist = load_frequency_distribution(config, language)
    mean_emb = compute_frequency_weighted_mean_embedding(freq_dist, W_U, tokenizer_vocab)
    projection = project_onto_edge_spectrum(mean_emb, V_edge)
    ranked_tokens = rank_tokens_by_projection(projection, tokenizer_vocab)
    
    return {
        "language": language,
        "top_tokens": [{"token": t, "score": s} for t, s in ranked_tokens]
    }

def main():
    """Run token attribution (example)."""
    config = load_config()
    print("Token attribution module ready.")

if __name__ == "__main__":
    main()
