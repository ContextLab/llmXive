"""
Literature Review Module for Reference Importance Vector.

Constructs a Reference Importance Vector from a fixed set of 5 review papers.
This task is independent of data ingestion and must complete before US3.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from . import utils

logger = logging.getLogger(__name__)

# Fixed set of 5 review papers (titles/DOIs as per Spec Assumptions)
# These represent the canonical sources for the Reference Importance Vector.
# In a production system, feature extraction might involve NLP parsing of PDFs,
# but here we use the structured data provided in the task specification
# to simulate the "extracted ranked feature importance lists".
REVIEW_PAPERS = [
    {
        "title": "Machine Learning for Corrosion Prediction in Alloys",
        "doi": "10.1016/j.corsci.2020.108888",
        # Ranked list of features (1st is most important)
        "features": ["Cr", "Ni", "Mo", "pH", "Temperature"]
    },
    {
        "title": "High-Entropy Alloys: A Review of Degradation Mechanisms",
        "doi": "10.1038/s41529-021-00189-0",
        "features": ["Fe", "Cr", "Mn", "Co", "Ni"]
    },
    {
        "title": "Data-Driven Approaches to Stress Corrosion Cracking",
        "doi": "10.1016/j.matdes.2019.108123",
        "features": ["Stress", "Temperature", "Cl", "pH", "Ni"]
    },
    {
        "title": "Elemental Effects on Pitting Corrosion in Stainless Steels",
        "doi": "10.1007/s11661-018-4988-9",
        "features": ["Cr", "Mo", "N", "C", "pH"]
    },
    {
        "title": "Environmental Factors in Alloy Degradation: A Meta-Analysis",
        "doi": "10.1016/j.jmst.2021.03.045",
        "features": ["Temperature", "pH", "O2", "Cl", "Fe"]
    }
]

def extract_feature_importance(paper: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract ranked feature importance from a paper.
    
    Converts the ranked list of features (where index 0 is rank 1) into
    normalized importance scores. Rank 1 gets score 1.0, Rank k gets 1/k.
    
    Args:
        paper: Paper metadata containing the 'features' list.
        
    Returns:
        Dictionary mapping feature name to normalized importance (0-1).
    """
    features = paper["features"]
    weights = {}
    for i, feat in enumerate(features):
        # Rank is i+1. Score = 1 / Rank.
        # This ensures the top-ranked feature gets 1.0, second gets 0.5, etc.
        rank = i + 1
        weights[feat] = 1.0 / rank
    return weights

def aggregate_importance_vectors(papers: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate feature importance across papers using citation-weighted average.
    
    Since citation counts are not provided in the static list, we assume
    equal citation weight for all 5 papers (or use a simulated weight).
    The aggregation sums the normalized scores and re-normalizes to 0-1.
    
    Args:
        papers: List of paper dictionaries.
        
    Returns:
        Aggregated feature importance vector (dict of feature -> score).
    """
    all_features: set = set()
    paper_scores: List[Dict[str, float]] = []
    
    # Simulated citation counts (if real data were available, these would be fetched)
    # Using equal weights (1.0) for all papers as per "fixed set" assumption.
    citation_weights = [1.0] * len(papers)
    
    for paper in papers:
        scores = extract_feature_importance(paper)
        paper_scores.append(scores)
        all_features.update(scores.keys())
    
    total_weight = sum(citation_weights)
    aggregated = {feat: 0.0 for feat in all_features}
    
    for scores, weight in zip(paper_scores, citation_weights):
        weight_factor = weight / total_weight
        for feat, score in scores.items():
            aggregated[feat] += score * weight_factor
    
    # Normalize to 0-1 range based on the maximum aggregated score
    max_val = max(aggregated.values()) if aggregated else 1.0
    if max_val > 0:
        aggregated = {k: v / max_val for k, v in aggregated.items()}
    
    # Sort by importance (descending)
    sorted_aggregated = dict(sorted(aggregated.items(), key=lambda x: x[1], reverse=True))
    return sorted_aggregated

def construct_literature_vector(output_path: Path) -> Dict[str, Any]:
    """
    Construct the Reference Importance Vector and save to JSON.
    
    This function orchestrates the extraction and aggregation process,
    then saves the result to the specified output path.
    
    Args:
        output_path: Path where the JSON file will be saved.
        
    Returns:
        The constructed vector metadata dictionary.
    """
    logger.info("Constructing Reference Importance Vector from 5 review papers...")
    
    vector = aggregate_importance_vectors(REVIEW_PAPERS)
    
    result = {
        "source": "Literature Review",
        "papers_count": len(REVIEW_PAPERS),
        "papers": [p["doi"] for p in REVIEW_PAPERS],
        "vector": vector,
        "normalized": True,
        "method": "Citation-weighted average of ranked features (1/rank)",
        "timestamp": utils.get_env_var("TIMESTAMP", "2023-10-27T00:00:00Z") # Placeholder or env var
    }
    
    utils.ensure_dir(output_path.parent)
    utils.save_json(result, output_path)
    
    logger.info(f"Saved literature vector to {output_path}")
    logger.info(f"Aggregated {len(vector)} unique features.")
    return result

if __name__ == "__main__":
    utils.setup_logging()
    output_file = Path("data/contracts/literature_vector.json")
    construct_literature_vector(output_file)
