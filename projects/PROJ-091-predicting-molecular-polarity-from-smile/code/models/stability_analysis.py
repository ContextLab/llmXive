import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from utils.logging_config import get_logger

logger = get_logger(__name__)

def get_top_feature_indices(shap_values, n: int = 10) -> List[int]:
    """Get top feature indices by absolute SHAP value."""
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    return np.argsort(mean_abs)[-n:].tolist()

def calculate_jaccard_similarity(list1: List[int], list2: List[int]) -> float:
    """Calculate Jaccard similarity."""
    s1 = set(list1)
    s2 = set(list2)
    return len(s1.intersection(s2)) / len(s1.union(s2)) if len(s1.union(s2)) > 0 else 0.0

def analyze_cluster_stability(bootstrap_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Analyze cluster stability."""
    if len(bootstrap_results) < 2:
        return {}
    jaccards = []
    for i in range(len(bootstrap_results) - 1):
        j = calculate_jaccard_similarity(
            bootstrap_results[i]["top_features"],
            bootstrap_results[i+1]["top_features"]
        )
        jaccards.append(j)
    return {"mean_jaccard": np.mean(jaccards), "std_jaccard": np.std(jaccards)}

def analyze_individual_feature_stability(bootstrap_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Analyze individual feature stability."""
    # Placeholder
    return {}

def run_stability_analysis(bootstrap_path: Path, output_path: Path) -> None:
    """Run stability analysis."""
    with open(bootstrap_path, "r") as f:
        results = json.load(f)
    cluster_stats = analyze_cluster_stability(results)
    feature_stats = analyze_individual_feature_stability(results)
    report = {"cluster": cluster_stats, "feature": feature_stats}
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

def main() -> None:
    """Main entry point."""
    bootstrap_path = Path("data/processed/analysis/bootstrap_results.json")
    output_path = Path("data/processed/analysis/stability_analysis.json")
    run_stability_analysis(bootstrap_path, output_path)

if __name__ == "__main__":
    main()
