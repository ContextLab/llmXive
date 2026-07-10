"""
T031: Implement overlap statistics calculation against known terpene synthase gene families.

This module calculates the overlap between the top-ranked features from the 
trained model and known terpene synthase (TPS) gene families.

FR-008: Validate that top features correspond to known biological pathways.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import get_config


# Known TPS gene families for Arabidopsis thaliana (based on literature)
# Source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3300343/
KNOWN_TPS_FAMILIES = {
    'TPSa', 'TPSb', 'TPSc', 'TPSd', 'TPSe', 'TPSf', 'TPSg', 'TPSh', 
    'TPSi', 'TPSj', 'TPSk', 'TPSl', 'TPSm', 'TPSn', 'TPSo', 'TPSp',
    'TPSq', 'TPSr', 'TPSs', 'TPSt', 'TPSu', 'TPSv', 'TPSw', 'TPSx',
    'TPSy', 'TPSz'
}

# Mapping of pathway features to TPS families (derived from T016 aggregation)
# In a real scenario, this would come from a curated database or mapping file
# For this implementation, we assume the pathway features are named like 'pathway_TPSa', 'pathway_TPSb', etc.
def _extract_tps_family(feature_name: str) -> str:
    """Extract TPS family name from a pathway feature string."""
    feature_lower = feature_name.lower()
    for family in KNOWN_TPS_FAMILIES:
        if family.lower() in feature_lower:
            return family
    return None


def load_model_and_feature_importance(
    metrics_path: Path, 
    importance_path: Path
) -> Tuple[Dict[str, float], List[str]]:
    """
    Load model metrics and feature importance data.
    
    Args:
        metrics_path: Path to model_metrics.json
        importance_path: Path to feature_importance_pvalues.json
        
    Returns:
        Tuple of (importance_dict, feature_names_list)
    """
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    with open(importance_path, 'r') as f:
        importance_data = json.load(f)
    
    # Extract feature importance and names
    importance_dict = importance_data.get('importance', {})
    feature_names = list(importance_dict.keys())
    
    return importance_dict, feature_names


def calculate_overlap_statistics(
    importance_dict: Dict[str, float],
    top_n: int = 20
) -> Dict[str, Any]:
    """
    Calculate overlap statistics between top features and known TPS families.
    
    Args:
        importance_dict: Dictionary of feature names to importance scores
        top_n: Number of top features to consider
        
    Returns:
        Dictionary containing overlap statistics
    """
    # Sort features by importance
    sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    top_features = sorted_features[:top_n]
    top_feature_names = [f[0] for f in top_features]
    
    # Identify which top features are TPS-related
    tps_features = []
    non_tps_features = []
    
    for feature in top_feature_names:
        family = _extract_tps_family(feature)
        if family:
            tps_features.append({
                'feature': feature,
                'family': family,
                'importance': importance_dict[feature]
            })
        else:
            non_tps_features.append({
                'feature': feature,
                'importance': importance_dict[feature]
            })
    
    # Calculate statistics
    total_top = len(top_features)
    tps_count = len(tps_features)
    non_tps_count = len(non_tps_features)
    
    overlap_percentage = (tps_count / total_top * 100) if total_top > 0 else 0.0
    
    # Check for enrichment
    # Expected: if features were random, what % would be TPS?
    # We'll use a simple heuristic: if >50% of top features are TPS, it's enriched
    is_enriched = overlap_percentage > 50.0
    
    # Calculate which TPS families are represented
    represented_families = set(f['family'] for f in tps_features)
    
    return {
        'top_n': top_n,
        'total_top_features': total_top,
        'tps_features_count': tps_count,
        'non_tps_features_count': non_tps_count,
        'overlap_percentage': round(overlap_percentage, 2),
        'is_enriched': is_enriched,
        'tps_features': tps_features,
        'non_tps_features': non_tps_features,
        'represented_families': sorted(list(represented_families)),
        'all_tps_families': sorted(list(KNOWN_TPS_FAMILIES)),
        'families_not_represented': sorted(list(KNOWN_TPS_FAMILIES - represented_families))
    }


def generate_overlap_report(
    stats: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate a detailed overlap report and save to JSON.
    
    Args:
        stats: Overlap statistics dictionary
        output_path: Path to save the report
    """
    report = {
        'task_id': 'T031',
        'description': 'Overlap statistics calculation against known terpene synthase gene families',
        'fr_reference': 'FR-008',
        'timestamp': pd.Timestamp.now().isoformat(),
        'statistics': stats,
        'interpretation': {
            'summary': f"Out of top {stats['top_n']} features, {stats['tps_features_count']} ({stats['overlap_percentage']}%) are associated with known TPS families.",
            'enrichment': f"Feature overlap {'is' if stats['is_enriched'] else 'is not'} enriched for known TPS families.",
            'represented_families': f"TPS families represented in top features: {', '.join(stats['represented_families']) if stats['represented_families'] else 'None'}",
            'missing_families': f"TPS families not represented in top features: {', '.join(stats['families_not_represented']) if stats['families_not_represented'] else 'None'}"
        }
    }
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)


def main():
    """Main entry point for T031."""
    config = get_config()
    
    # Define paths
    project_root = Path(config.get('project_root', '.'))
    metrics_path = project_root / 'data' / 'results' / 'model_metrics.json'
    importance_path = project_root / 'data' / 'results' / 'feature_importance_pvalues.json'
    output_path = project_root / 'data' / 'results' / 'overlap_statistics.json'
    
    # Check if required files exist
    if not metrics_path.exists():
        print(f"Error: Model metrics file not found at {metrics_path}")
        print("Please ensure T024 and T030 have been completed.")
        sys.exit(1)
    
    if not importance_path.exists():
        print(f"Error: Feature importance file not found at {importance_path}")
        print("Please ensure T030 has been completed.")
        sys.exit(1)
    
    print("Loading model and feature importance data...")
    importance_dict, feature_names = load_model_and_feature_importance(metrics_path, importance_path)
    
    print(f"Found {len(feature_names)} features in the model.")
    
    # Calculate overlap statistics
    print("Calculating overlap statistics...")
    stats = calculate_overlap_statistics(importance_dict, top_n=20)
    
    # Generate report
    print(f"Generating overlap report at {output_path}...")
    generate_overlap_report(stats, output_path)
    
    print("Overlap analysis completed successfully!")
    print(f"  - TPS features in top 20: {stats['tps_features_count']}")
    print(f"  - Overlap percentage: {stats['overlap_percentage']}%")
    print(f"  - Enriched: {stats['is_enriched']}")
    
    return stats


if __name__ == '__main__':
    main()
