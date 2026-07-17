"""
Correlation analysis pipeline.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

from code.config import DATA_PROCESSED_DIR, DATA_RESULTS_DIR
from scipy.stats import pearsonr, spearmanr

def load_features(file_path: Path) -> List[Dict[str, Any]]:
    """Load features from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)

def compute_correlation(features: List[Dict[str, Any]], proxy_target: str) -> Dict[str, float]:
    """
    Compute correlation between features and a proxy target.
    """
    # Extract feature values and proxy target values
    # This is a placeholder; actual implementation depends on the proxy target
    feature_values = []
    proxy_values = []

    for item in features:
        # Placeholder logic: assume proxy target is stored in the item
        # In reality, we need to load the proxy target from the original dataset
        pass

    if not feature_values or not proxy_values:
        return {"pearson": np.nan, "spearman": np.nan, "p_value": np.nan}

    pearson_corr, p_value = pearsonr(feature_values, proxy_values)
    spearman_corr, _ = spearmanr(feature_values, proxy_values)

    return {
        "pearson": float(pearson_corr),
        "spearman": float(spearman_corr),
        "p_value": float(p_value),
    }

def main():
    """Main entry point for correlation analysis."""
    # Load features
    book_corpus_features = load_features(DATA_PROCESSED_DIR / "book_corpus_features.json")
    beir_features = load_features(DATA_PROCESSED_DIR / "beir_features.json")

    # Compute correlations (placeholder)
    book_corpus_corr = compute_correlation(book_corpus_features, "text_length")
    beir_corr = compute_correlation(beir_features, "relevance_score")

    # Save results
    results = {
        "book_corpus": book_corpus_corr,
        "beir": beir_corr,
    }

    output_file = DATA_RESULTS_DIR / "correlation_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved correlation results to {output_file}")

if __name__ == "__main__":
    main()
