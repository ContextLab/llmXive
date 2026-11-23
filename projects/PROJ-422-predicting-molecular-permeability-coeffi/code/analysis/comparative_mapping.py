"""
Comparative Mapping Logic for FR-009.

This module implements the logic to map and compare feature importance
between the Random Forest (SHAP) and GNN (GNNExplainer) models.
It identifies substructures important to the GNN that are not captured
by standard descriptors used by the Random Forest.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_feature_importance_rf(file_path: str) -> Dict[str, Any]:
    """
    Load the Random Forest feature importance (SHAP) data.
    
    Args:
        file_path: Path to the JSON file containing RF feature importance.
        
    Returns:
        Dictionary containing feature names and their importance scores.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"RF feature importance file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded RF feature importance from {file_path}")
    return data

def load_feature_importance_gnn(file_path: str) -> Dict[str, Any]:
    """
    Load the GNN feature importance (GNNExplainer) data.
    
    Args:
        file_path: Path to the JSON file containing GNN feature importance.
        
    Returns:
        Dictionary containing substructure names and their importance scores.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"GNN feature importance file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded GNN feature importance from {file_path}")
    return data

def load_metrics(file_path: str) -> Dict[str, Any]:
    """
    Load the model metrics (RMSE, MAE, R2, etc.).
    
    Args:
        file_path: Path to the metrics JSON file.
        
    Returns:
        Dictionary containing model metrics.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded metrics from {file_path}")
    return data

def map_feature_ranks(
    rf_importance: Dict[str, Any],
    gnn_importance: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Map and compare feature ranks between RF and GNN.
    
    This function identifies:
    1. Features with high GNN scores but low/no RF scores (unique topological features)
    2. Features with high scores in both models (shared predictive patterns)
    
    Args:
        rf_importance: Dictionary of RF feature importance (SHAP values).
        gnn_importance: Dictionary of GNN feature importance (GNNExplainer scores).
        
    Returns:
        Dictionary containing the mapping analysis results.
    """
    rf_features = rf_importance.get('features', [])
    gnn_features = gnn_importance.get('features', [])
    
    # Create rank dictionaries
    rf_rank_map = {f['name']: f['rank'] for f in rf_features if 'rank' in f}
    gnn_rank_map = {f['name']: f['rank'] for f in gnn_features if 'rank' in f}
    
    # If ranks are not pre-computed, compute them based on importance scores
    if not rf_rank_map and rf_features:
        sorted_rf = sorted(rf_features, key=lambda x: x.get('importance', 0), reverse=True)
        rf_rank_map = {f['name']: i+1 for i, f in enumerate(sorted_rf)}
    
    if not gnn_rank_map and gnn_features:
        sorted_gnn = sorted(gnn_features, key=lambda x: x.get('importance', 0), reverse=True)
        gnn_rank_map = {f['name']: i+1 for i, f in enumerate(sorted_gnn)}
    
    # Identify unique GNN features (high GNN rank, low/missing RF rank)
    gnn_top_features = sorted(gnn_rank_map.items(), key=lambda x: x[1])[:10]
    unique_gnn_features = []
    shared_features = []
    
    for name, gnn_rank in gnn_top_features:
        rf_rank = rf_rank_map.get(name, float('inf'))
        
        if rf_rank > 10 or rf_rank == float('inf'):
            # High GNN importance, low/missing RF importance
            unique_gnn_features.append({
                'name': name,
                'gnn_rank': gnn_rank,
                'rf_rank': rf_rank if rf_rank != float('inf') else 'N/A',
                'gnn_importance': next(
                    (f['importance'] for f in gnn_features if f['name'] == name), 0
                ),
                'rf_importance': next(
                    (f['importance'] for f in rf_features if f['name'] == name), 0
                )
            })
        else:
            shared_features.append({
                'name': name,
                'gnn_rank': gnn_rank,
                'rf_rank': rf_rank,
                'gnn_importance': next(
                    (f['importance'] for f in gnn_features if f['name'] == name), 0
                ),
                'rf_importance': next(
                    (f['importance'] for f in rf_features if f['name'] == name), 0
                )
            })
    
    # Sort by GNN rank
    unique_gnn_features.sort(key=lambda x: x['gnn_rank'])
    shared_features.sort(key=lambda x: x['gnn_rank'])
    
    return {
        'unique_gnn_features': unique_gnn_features,
        'shared_features': shared_features,
        'summary': {
            'total_gnn_features_analyzed': len(gnn_rank_map),
            'unique_gnn_count': len(unique_gnn_features),
            'shared_count': len(shared_features),
            'analysis_method': 'Rank comparison (Top 10 GNN features)'
        }
    }

def generate_mapping_data(
    rf_file: str,
    gnn_file: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Generate the mapping data structure for the comparative report.
    
    Args:
        rf_file: Path to RF feature importance JSON.
        gnn_file: Path to GNN feature importance JSON.
        output_file: Path to save the mapping data JSON.
        
    Returns:
        Dictionary containing the mapping analysis results.
    """
    logger.info("Starting comparative mapping analysis...")
    
    try:
        rf_importance = load_feature_importance_rf(rf_file)
        gnn_importance = load_feature_importance_gnn(gnn_file)
        
        mapping_results = map_feature_ranks(rf_importance, gnn_importance)
        
        # Save to output file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(mapping_results, f, indent=2)
        
        logger.info(f"Mapping data saved to {output_file}")
        return mapping_results
        
    except Exception as e:
        logger.error(f"Error during mapping analysis: {e}")
        raise

def main():
    """Main entry point for the comparative mapping script."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    rf_file = base_dir / "results" / "feature_importance_rf.json"
    gnn_file = base_dir / "results" / "feature_importance_gnn.json"
    output_file = base_dir / "results" / "mapping_data.json"
    
    if not rf_file.exists():
        logger.error(f"RF feature importance file not found: {rf_file}")
        sys.exit(1)
    
    if not gnn_file.exists():
        logger.error(f"GNN feature importance file not found: {gnn_file}")
        sys.exit(1)
    
    try:
        results = generate_mapping_data(
            str(rf_file),
            str(gnn_file),
            str(output_file)
        )
        
        logger.info("Mapping analysis completed successfully.")
        logger.info(f"Unique GNN features identified: {results['summary']['unique_gnn_count']}")
        logger.info(f"Shared features identified: {results['summary']['shared_count']}")
        
    except Exception as e:
        logger.error(f"Failed to complete mapping analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()