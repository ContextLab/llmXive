"""
Task T042: Generate results/attribution.json with feature importance rankings.

This script aggregates the results from the Integrated Gradients attribution
analysis (T035) and the statistical aggregation (T037), then ranks features
by their absolute importance and variance to produce a structured JSON report.

It depends on:
- code/analysis/attribution.py (for loading attribution results)
- code/analysis/aggregate_attribution.py (for aggregation logic)
- data/processed/descriptors.csv (for feature names and VIF context)

Output:
- results/attribution.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.attribution import run_attribution_analysis, load_trained_model, load_graphs
from analysis.aggregate_attribution import aggregate_attribution_results, load_existing_stats
from data.descriptor_extractor import load_curated_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_feature_names_from_descriptors() -> List[str]:
    """
    Load feature names from the descriptors CSV to ensure we have a consistent
    list of topological features for the attribution report.
    """
    descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
    if not descriptors_path.exists():
        logger.warning(f"Descriptors file not found at {descriptors_path}. "
                       "Feature names will be inferred from attribution results.")
        return []

    # We need to read the CSV to get column names (skipping the first row which is header)
    # Since we can't import pandas directly without checking dependencies, we'll use csv module
    import csv
    with open(descriptors_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers:
            # Filter out common non-feature columns like 'id', 'polymer_smiles', etc.
            # Based on T017, descriptors include: degree, density, clustering_coefficient
            # and potentially others derived from the graph.
            feature_cols = [col for col in headers if col.lower() not in 
                            ['id', 'polymer_smiles', 'filler_smiles', 'adhesion_energy', 
                             'polymer_graph_id', 'filler_graph_id']]
            return feature_cols
    return []

def generate_attribution_json(
    attribution_results: Dict[str, Any],
    feature_names: List[str],
    output_path: Path
) -> None:
    """
    Generate the attribution.json file with feature importance rankings.

    The JSON structure includes:
    - summary: Overall statistics (mean absolute importance, std dev, etc.)
    - rankings: List of features sorted by importance (descending)
    - top_features: Top N features with detailed stats
    - attribution_method: Description of the method used
    - metadata: Timestamp, model info, etc.
    """
    # Calculate summary statistics
    importance_scores = attribution_results.get('mean_absolute_importance', {})
    std_scores = attribution_results.get('std_importance', {})
    
    # Create a list of features with their stats
    feature_stats = []
    for feature, mean_imp in importance_scores.items():
        std_imp = std_scores.get(feature, 0.0)
        feature_stats.append({
            'feature': feature,
            'mean_absolute_importance': float(mean_imp),
            'std_importance': float(std_imp),
            'rank': 0  # Will be filled after sorting
        })
    
    # Sort by mean absolute importance (descending)
    feature_stats.sort(key=lambda x: x['mean_absolute_importance'], reverse=True)
    
    # Assign ranks
    for i, stat in enumerate(feature_stats):
        stat['rank'] = i + 1
    
    # Determine top features (std > 0.1 as per T037 requirement)
    top_features = [f for f in feature_stats if f['std_importance'] > 0.1]
    
    # Build the JSON structure
    attribution_report = {
        'summary': {
            'total_features': len(feature_stats),
            'features_with_high_variance': len(top_features),
            'attribution_method': 'Integrated Gradients',
            'model_type': 'GAT (Graph Attention Network)',
            'dataset_size': attribution_results.get('dataset_size', 0)
        },
        'rankings': feature_stats,
        'top_features': top_features,
        'metadata': {
            'generated_at': str(Path(__file__).parent.parent.parent),
            'task_id': 'T042',
            'user_story': 'US3'
        }
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file
    with open(output_path, 'w') as f:
        json.dump(attribution_report, f, indent=2)
    
    logger.info(f"Attribution report saved to {output_path}")
    logger.info(f"Total features: {len(feature_stats)}")
    logger.info(f"Features with std > 0.1: {len(top_features)}")

def main():
    """
    Main entry point for T042.
    """
    logger.info("Starting T042: Generate attribution.json")
    
    # Paths
    output_path = project_root / "results" / "attribution.json"
    
    # Check if we have the necessary inputs
    # 1. Check if attribution results exist (from T035)
    # We assume T035 has already run and saved results to a temporary location
    # or that we can re-run the attribution analysis.
    
    # For this implementation, we'll attempt to re-run the attribution analysis
    # if the necessary model and graphs are available.
    
    model_path = project_root / "results" / "model.pt"
    graphs_path = project_root / "data" / "processed" / "graphs.pt"
    
    if not model_path.exists():
        logger.error(f"Trained model not found at {model_path}. "
                     "Please ensure T028 has been completed successfully.")
        sys.exit(1)
    
    if not graphs_path.exists():
        logger.error(f"Processed graphs not found at {graphs_path}. "
                     "Please ensure T024 has been completed successfully.")
        sys.exit(1)
    
    # Load the trained model
    logger.info(f"Loading model from {model_path}")
    model = load_trained_model(model_path)
    
    # Load graphs and targets
    logger.info(f"Loading graphs from {graphs_path}")
    graphs, targets = load_graphs(graphs_path)
    
    if len(graphs) == 0:
        logger.error("No graphs loaded. Cannot perform attribution analysis.")
        sys.exit(1)
    
    # Run attribution analysis
    logger.info("Running Integrated Gradients attribution analysis...")
    attribution_results = run_attribution_analysis(
        model=model,
        graphs=graphs,
        targets=targets,
        n_steps=50,  # Number of steps for Integrated Gradients
        baseline='zeros'
    )
    
    # Load feature names from descriptors
    logger.info("Loading feature names from descriptors...")
    feature_names = load_feature_names_from_descriptors()
    
    # If we couldn't load feature names, use the ones from attribution results
    if not feature_names:
        feature_names = list(attribution_results.get('mean_absolute_importance', {}).keys())
        logger.warning(f"Using inferred feature names: {feature_names}")
    
    # Generate the JSON report
    logger.info("Generating attribution.json...")
    generate_attribution_json(attribution_results, feature_names, output_path)
    
    logger.info("T042 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())