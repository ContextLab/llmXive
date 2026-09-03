"""
Cluster-aware permutation testing for feature importance.

Implements the algorithm described in FR-007: for each feature, shuffle values
strictly within material clusters defined by adsorbent_structure_id.

Handles edge cases where clusters are too small for permutation (size < 3).
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cluster_permutation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_dirs():
    """Create necessary output directories."""
    Path('data/validation').mkdir(parents=True, exist_ok=True)
    Path('logs').mkdir(parents=True, exist_ok=True)
    Path('data/results').mkdir(parents=True, exist_ok=True)

def load_test_data(data_dir: str = 'data/processed') -> pd.DataFrame:
    """Load preprocessed test data."""
    data_path = Path(data_dir) / 'processed_data.csv'
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded test data with {len(df)} samples")
    return df

def load_model(model_path: str = 'trained_models/best_model.pkl'):
    """Load the trained model for permutation testing."""
    import joblib
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    return joblib.load(model_path)

def identify_clusters(df: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Group indices by adsorbent_structure_id (cluster key).
    
    Returns:
        Dict mapping cluster_id to list of row indices within that cluster.
    """
    clusters = {}
    for cluster_id, group in df.groupby('adsorbent_structure_id'):
        clusters[cluster_id] = group.index.tolist()
    return clusters

def calculate_p_values(
    X: np.ndarray,
    y: np.ndarray,
    model,
    clusters: Dict[str, List[int]],
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate p-values for each feature using cluster-aware permutation.
    
    For each feature:
    1. Calculate original performance metric (R2)
    2. Shuffle feature values WITHIN each cluster (preserving cluster structure)
    3. Re-evaluate model performance
    4. Calculate p-value as proportion of permuted scores >= original score
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        model: Trained model with .predict() method
        clusters: Dict mapping cluster_id to list of row indices
        n_permutations: Number of permutation iterations per feature
        random_state: Random seed for reproducibility
        
    Returns:
        Dict mapping feature_name to p-value
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Feature names from column indices
    feature_names = [f'feature_{i}' for i in range(X.shape[1])]
    p_values = {}
    
    # Calculate original performance
    original_score = r2_score(y, model.predict(X))
    logger.info(f"Original R2 score: {original_score:.4f}")
    
    # Track excluded clusters for logging
    excluded_clusters = []
    valid_clusters = []
    
    for cluster_id, indices in clusters.items():
        if len(indices) < 3:
            excluded_clusters.append((cluster_id, len(indices)))
        else:
            valid_clusters.append((cluster_id, indices))
    
    # Log cluster exclusions
    if excluded_clusters:
        exclusion_log_path = Path('data/validation/cluster_exclusion_log.json')
        exclusion_data = {
            'excluded_clusters': [
                {'cluster_id': cid, 'size': size} 
                for cid, size in excluded_clusters
            ],
            'reason': 'Cluster size < 3 (insufficient for permutation)',
            'total_excluded': len(excluded_clusters),
            'valid_clusters': len(valid_clusters)
        }
        
        with open(exclusion_log_path, 'w') as f:
            json.dump(exclusion_data, f, indent=2)
        
        logger.warning(
            f"Excluded {len(excluded_clusters)} clusters due to size < 3. "
            f"Exclusion log written to {exclusion_log_path}"
        )
    
    if not valid_clusters:
        raise ValueError(
            "No valid clusters found for permutation testing. "
            "All clusters have size < 3."
        )
    
    # Permutation testing for each feature
    for feat_idx in range(X.shape[1]):
        permuted_scores = []
        
        for _ in range(n_permutations):
            X_perm = X.copy()
            
            # Shuffle within each valid cluster
            for cluster_id, indices in valid_clusters:
                cluster_values = X_perm[indices, feat_idx].copy()
                np.random.shuffle(cluster_values)
                X_perm[indices, feat_idx] = cluster_values
            
            # Evaluate permuted model
            permuted_score = r2_score(y, model.predict(X_perm))
            permuted_scores.append(permuted_score)
        
        # Calculate p-value: proportion of permuted scores >= original
        p_value = np.mean(permuted_scores >= original_score)
        p_values[feature_names[feat_idx]] = p_value
        
        logger.info(
            f"Feature {feature_names[feat_idx]}: p-value = {p_value:.4f}, "
            f"original R2 = {original_score:.4f}"
        )
    
    return p_values

def run_permutation_analysis(
    data_dir: str = 'data/processed',
    model_path: str = 'trained_models/best_model.pkl',
    output_path: str = 'data/results/permutation_pvalues.json',
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full permutation analysis pipeline.
    
    Args:
        data_dir: Directory containing processed data
        model_path: Path to trained model
        output_path: Path to save results
        n_permutations: Number of permutations per feature
        random_state: Random seed
        
    Returns:
        Dict containing p-values and metadata
    """
    ensure_dirs()
    
    # Load data and model
    df = load_test_data(data_dir)
    model = load_model(model_path)
    
    # Prepare features and target
    # Assuming features are all columns except metadata and target
    feature_cols = [col for col in df.columns 
                   if col not in ['material_id', 'adsorbent_structure_id', 
                                 'langmuir_capacity', 'henry_constant', 
                                 'target']]
    
    if 'target' not in df.columns and 'langmuir_capacity' in df.columns:
        target_col = 'langmuir_capacity'
    elif 'henry_constant' in df.columns:
        target_col = 'henry_constant'
    else:
        raise ValueError("No target column found in data")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Identify clusters
    clusters = identify_clusters(df)
    logger.info(f"Identified {len(clusters)} clusters")
    
    # Calculate p-values
    p_values = calculate_p_values(
        X, y, model, clusters, 
        n_permutations=n_permutations, 
        random_state=random_state
    )
    
    # Prepare results
    results = {
        'n_permutations': n_permutations,
        'random_state': random_state,
        'n_features': len(p_values),
        'n_clusters': len(clusters),
        'p_values': p_values,
        'features': list(p_values.keys())
    }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Permutation analysis complete. Results saved to {output_path}")
    return results

def run_cluster_permutation(
    data_dir: str = 'data/processed',
    model_path: str = 'trained_models/best_model.pkl',
    output_path: str = 'data/results/permutation_pvalues.json',
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main entry point for cluster permutation testing.
    
    This function orchestrates the entire permutation testing pipeline,
    including handling of small clusters and logging exclusions.
    
    Args:
        data_dir: Directory containing processed data
        model_path: Path to trained model
        output_path: Path to save results
        n_permutations: Number of permutations per feature
        random_state: Random seed
        
    Returns:
        Dict containing p-values and metadata
    """
    return run_permutation_analysis(
        data_dir=data_dir,
        model_path=model_path,
        output_path=output_path,
        n_permutations=n_permutations,
        random_state=random_state
    )

def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run cluster permutation testing')
    parser.add_argument('--data-dir', default='data/processed', 
                      help='Directory containing processed data')
    parser.add_argument('--model-path', default='trained_models/best_model.pkl',
                      help='Path to trained model')
    parser.add_argument('--output', default='data/results/permutation_pvalues.json',
                      help='Output path for results')
    parser.add_argument('--n-permutations', type=int, default=1000,
                      help='Number of permutations per feature')
    parser.add_argument('--random-state', type=int, default=42,
                      help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    try:
        results = run_cluster_permutation(
            data_dir=args.data_dir,
            model_path=args.model_path,
            output_path=args.output,
            n_permutations=args.n_permutations,
            random_state=args.random_state
        )
        
        print(f"Cluster permutation testing completed successfully.")
        print(f"Processed {results['n_features']} features across {results['n_clusters']} clusters.")
        print(f"Results saved to {args.output}")
        
        # Print summary of significant features (p < 0.05)
        significant = [k for k, v in results['p_values'].items() if v < 0.05]
        print(f"Significant features (p < 0.05): {len(significant)}")
        if significant:
            print(f"  {', '.join(significant[:5])}{'...' if len(significant) > 5 else ''}")
        
    except Exception as e:
        logger.error(f"Cluster permutation testing failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()