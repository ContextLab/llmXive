"""
Diagnostic analysis module for User Story 1.

Performs collinearity checks on multi-layer activation variances and logs outliers.
This supports the validation of the correlation hypothesis by ensuring that
the variance signals from different layers are not perfectly redundant and
identifying samples that deviate significantly from the expected distribution.
"""
import os
import json
import logging
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.covariance import EmpiricalCovariance, MinCovDet

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_activation_variances(config: Config) -> Dict[str, Any]:
    """
    Load activation variances from the processed data file.
    
    Args:
        config: The project configuration object.
        
    Returns:
        A dictionary containing sample IDs and their variance vectors across layers.
    """
    variance_path = config.get_variance_path()
    
    if not os.path.exists(variance_path):
        raise FileNotFoundError(f"Activation variance file not found: {variance_path}")
    
    logger.info(f"Loading activation variances from {variance_path}")
    
    data = []
    with open(variance_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['sample_id']
            # Parse variance columns (assumed to be named variance_layer_0, variance_layer_1, etc.)
            variance_vector = []
            layer_idx = 0
            while True:
                col_name = f'variance_layer_{layer_idx}'
                if col_name not in row:
                    break
                try:
                    val = float(row[col_name])
                    variance_vector.append(val)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid variance value for {sample_id}, layer {layer_idx}: {row[col_name]}")
                    variance_vector.append(0.0)
                layer_idx += 1
            
            if variance_vector:
                data.append({
                    'sample_id': sample_id,
                    'variance_vector': np.array(variance_vector)
                })
    
    logger.info(f"Loaded {len(data)} samples with {len(data[0]['variance_vector']) if data else 0} layers")
    return {'samples': data, 'n_layers': len(data[0]['variance_vector']) if data else 0}

def compute_collinearity_matrix(variance_data: Dict[str, Any]) -> np.ndarray:
    """
    Compute the Pearson correlation matrix between layers to check for collinearity.
    
    Args:
        variance_data: Dictionary containing 'samples' list with 'variance_vector' arrays.
        
    Returns:
        A correlation matrix of shape (n_layers, n_layers).
    """
    if not variance_data['samples']:
        raise ValueError("No samples provided for collinearity analysis")
    
    # Stack variance vectors into a matrix: (n_samples, n_layers)
    variance_matrix = np.vstack([s['variance_vector'] for s in variance_data['samples']])
    
    # Compute correlation matrix between layers (columns)
    correlation_matrix = np.corrcoef(variance_matrix, rowvar=False)
    
    return correlation_matrix

def detect_collinearity_issues(correlation_matrix: np.ndarray, threshold: float = 0.99) -> List[Tuple[int, int, float]]:
    """
    Identify pairs of layers with near-perfect collinearity.
    
    Args:
        correlation_matrix: The correlation matrix between layers.
        threshold: Correlation coefficient threshold above which layers are considered collinear.
        
    Returns:
        List of tuples (layer_i, layer_j, correlation) for highly collinear pairs.
    """
    n_layers = correlation_matrix.shape[0]
    collinear_pairs = []
    
    for i in range(n_layers):
        for j in range(i + 1, n_layers):
            corr_val = correlation_matrix[i, j]
            if abs(corr_val) > threshold:
                collinear_pairs.append((i, j, corr_val))
                logger.warning(f"High collinearity detected: Layer {i} and Layer {j} (r={corr_val:.4f})")
    
    return collinear_pairs

def detect_outliers_iqr(variance_data: Dict[str, Any], multiplier: float = 1.5) -> Dict[str, List[int]]:
    """
    Detect outliers using the Interquartile Range (IQR) method per layer.
    
    Args:
        variance_data: Dictionary containing 'samples' list with 'variance_vector' arrays.
        multiplier: Factor for IQR to determine outlier bounds.
        
    Returns:
        Dictionary mapping layer index to list of outlier sample IDs.
    """
    if not variance_data['samples']:
        return {}
    
    variance_matrix = np.vstack([s['variance_vector'] for s in variance_data['samples']])
    sample_ids = [s['sample_id'] for s in variance_data['samples']]
    n_layers = variance_matrix.shape[1]
    
    outliers_by_layer = {i: [] for i in range(n_layers)}
    
    for layer_idx in range(n_layers):
        layer_data = variance_matrix[:, layer_idx]
        q1 = np.percentile(layer_data, 25)
        q3 = np.percentile(layer_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        for i, val in enumerate(layer_data):
            if val < lower_bound or val > upper_bound:
                outliers_by_layer[layer_idx].append(sample_ids[i])
        
        if outliers_by_layer[layer_idx]:
            logger.info(f"Layer {layer_idx}: Found {len(outliers_by_layer[layer_idx])} outliers (IQR method)")
    
    return outliers_by_layer

def detect_outliers_mcd(variance_data: Dict[str, Any], contamination: float = 0.05) -> List[str]:
    """
    Detect multivariate outliers using the Minimum Covariance Determinant (MCD) estimator.
    
    Args:
        variance_data: Dictionary containing 'samples' list with 'variance_vector' arrays.
        contamination: Expected proportion of outliers in the data.
        
    Returns:
        List of sample IDs identified as outliers.
    """
    if not variance_data['samples']:
        return []
    
    variance_matrix = np.vstack([s['variance_vector'] for s in variance_data['samples']])
    sample_ids = [s['sample_id'] for s in variance_data['samples']]
    
    try:
        mcd = MinCovDet(contamination=contamination, random_state=42)
        mcd.fit(variance_matrix)
        
        # Get outlier mask (True for outliers)
        outlier_mask = mcd.outlier_status_
        outlier_ids = [sample_ids[i] for i, is_outlier in enumerate(outlier_mask) if is_outlier]
        
        logger.info(f"Multivariate outlier detection (MCD): Found {len(outlier_ids)} outliers")
        return outlier_ids
        
    except Exception as e:
        logger.error(f"Failed to run MCD outlier detection: {e}")
        return []

def run_diagnostic_analysis(config: Config, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full diagnostic analysis pipeline.
    
    Args:
        config: The project configuration object.
        output_path: Optional path to save the results JSON.
        
    Returns:
        A dictionary containing all diagnostic results.
    """
    logger.info("Starting diagnostic analysis for multi-layer variances")
    
    # Load data
    variance_data = load_activation_variances(config)
    
    # Collinearity analysis
    correlation_matrix = compute_collinearity_matrix(variance_data)
    collinear_pairs = detect_collinearity_issues(correlation_matrix)
    
    # Outlier detection
    outliers_iqr = detect_outliers_iqr(variance_data)
    outliers_mcd = detect_outliers_mcd(variance_data)
    
    # Compile results
    results = {
        'n_samples': len(variance_data['samples']),
        'n_layers': variance_data['n_layers'],
        'collinearity': {
            'correlation_matrix': correlation_matrix.tolist(),
            'highly_collinear_pairs': [
                {'layer_i': p[0], 'layer_j': p[1], 'correlation': p[2]}
                for p in collinear_pairs
            ],
            'max_correlation': float(np.max(np.abs(correlation_matrix)))
        },
        'outliers': {
            'iqr_method': {
                layer_idx: outliers
                for layer_idx, outliers in outliers_iqr.items()
                if outliers
            },
            'mcd_method': outliers_mcd,
            'total_unique_outliers': len(set(outliers_mcd + [sid for layer in outliers_iqr.values() for sid in layer]))
        }
    }
    
    # Save to file if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Diagnostic results saved to {output_path}")
    
    return results

def main():
    """Main entry point for the diagnostic analysis script."""
    config = Config()
    
    # Default output path based on config
    output_dir = config.get_data_dir() / 'processed'
    output_path = str(output_dir / 'diagnostic_results.json')
    
    try:
        results = run_diagnostic_analysis(config, output_path)
        logger.info("Diagnostic analysis completed successfully")
        
        # Log summary
        collinear_count = len(results['collinearity']['highly_collinear_pairs'])
        outlier_count = results['outliers']['total_unique_outliers']
        logger.info(f"Summary: {collinear_count} collinear layer pairs, {outlier_count} unique outliers detected")
        
    except Exception as e:
        logger.error(f"Diagnostic analysis failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()