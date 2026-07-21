"""
External validation module for WALS data correlation.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from config import load_config, get_path, get_hyperparameter

class ExternalValidationError(Exception):
    pass

class WALSDataNotFoundError(Exception):
    pass

def load_config() -> Dict[str, Any]:
    """Load configuration."""
    from config import load_config as cfg
    return cfg()

def get_wals_feature_ids() -> List[int]:
    """Get specific WALS feature IDs for phonological/morphological features."""
    # Example feature IDs (phonology, morphology)
    return [1, 2, 3, 4, 5] # Placeholder for actual IDs

def get_correlation_method() -> str:
    """Get the correlation method (Spearman's rank)."""
    return "spearman"

def fetch_wals_data(config: Dict) -> Dict[str, Any]:
    """Fetch WALS data from the verified artifact."""
    raw_dir = get_path(config, "data_raw") / "wals"
    if not raw_dir.exists():
        raise WALSDataNotFoundError(f"WALS data not found at {raw_dir}")
    
    # Load WALS data (assuming JSON format)
    files = list(raw_dir.glob("*.json"))
    if not files:
        raise WALSDataNotFoundError("No WALS JSON files found")
    
    data = {}
    for f in files:
        with open(f, "r") as fp:
            data.update(json.load(fp))
    
    return data

def align_subspace_orientations(similarity_data: List[Dict], wals_data: Dict[str, Any]) -> List[Tuple[str, float]]:
    """Align subspace orientation data with WALS features."""
    # Map models to languages
    model_lang_map = {
        "Llama-3": "en",
        "Mistral": "en",
        "BLOOM": "fr" # Example mapping
    }
    
    aligned = []
    for pair in similarity_data:
        lang_a = model_lang_map.get(pair["model_a"])
        lang_b = model_lang_map.get(pair["model_b"])
        
        if lang_a and lang_b:
            # Combine language features
            features = []
            if lang_a in wals_data:
                features.extend(wals_data[lang_a])
            if lang_b in wals_data:
                features.extend(wals_data[lang_b])
            
            if features:
                aligned.append((pair["model_a"] + "-" + pair["model_b"], np.mean(features)))
    
    return aligned

def compute_spearman_correlation(similarities: List[float], features: List[float]) -> float:
    """Compute Spearman's rank correlation."""
    if len(similarities) != len(features) or len(similarities) == 0:
        return 0.0
    
    # Use scipy if available, otherwise manual calculation
    try:
        from scipy.stats import spearmanr
        corr, _ = spearmanr(similarities, features)
        return float(corr)
    except ImportError:
        # Fallback to numpy implementation
        rank_x = np.argsort(np.argsort(similarities))
        rank_y = np.argsort(np.argsort(features))
        
        d = rank_x - rank_y
        n = len(similarities)
        rho = 1 - (6 * np.sum(d**2)) / (n * (n**2 - 1))
        return float(rho)

def run_external_validation(config: Dict, similarity_data: List[Dict], wals_data: Dict) -> Dict[str, Any]:
    """Run external validation."""
    aligned = align_subspace_orientations(similarity_data, wals_data)
    
    sims = [pair["cosine_similarity"] for pair in similarity_data]
    feats = [x[1] for x in aligned]
    
    if not sims or not feats:
        return {
            "data_unavailable": True,
            "correlation": None,
            "message": "Insufficient data for correlation"
        }
    
    corr = compute_spearman_correlation(sims, feats)
    
    return {
        "data_unavailable": False,
        "correlation_method": get_correlation_method(),
        "correlation": corr,
        "significant": abs(corr) > 0.5 # Example threshold
    }

def main():
    """Run external validation (example)."""
    config = load_config()
    print("External validation module ready.")

if __name__ == "__main__":
    main()
