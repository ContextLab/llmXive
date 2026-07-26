"""
Feature integration module that combines per-sample statistics with global eigenvalue.
"""
import argparse
import json
import logging
import os
import sys
import numpy as np
from typing import Dict, List, Any, Optional

from features import (
    setup_logging,
    calculate_per_sample_stats,
    calculate_frobenius_norm_outer_product,
    calculate_fidelity_loss
)

REQUIRED_DIMENSIONS = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']

def setup_directories(base_path: str) -> None:
    """Ensure required directories exist."""
    os.makedirs(os.path.join(base_path, 'data', 'raw'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'data', 'processed'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'results'), exist_ok=True)

def compute_global_eigenvalue(
    data_path: str,
    score_columns: List[str] = REQUIRED_DIMENSIONS
) -> float:
    """
    Compute the global dominant eigenvalue from teacher scores.
    
    Args:
        data_path: Path to the aligned data JSON file.
        score_columns: List of column names for teacher scores.
    
    Returns:
        The dominant eigenvalue (scalar).
    """
    logger = setup_logging()
    logger.info(f"Loading data from {data_path} for global eigenvalue computation")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    if not data:
        raise ValueError("Data file is empty")
    
    # Extract teacher scores
    teacher_scores_list = []
    for row in data:
        scores = [row.get(col, 0.0) for col in score_columns]
        teacher_scores_list.append(scores)
    
    all_teacher_scores = np.array(teacher_scores_list)
    
    if all_teacher_scores.shape[0] < 2:
        raise ValueError("Need at least 2 samples to compute covariance matrix.")
    
    # Compute covariance matrix
    cov_matrix = np.cov(all_teacher_scores, rowvar=False)
    cov_matrix = (cov_matrix + cov_matrix.T) / 2.0  # Ensure symmetry
    
    # Compute eigenvalues
    eigenvalues = np.linalg.eigvalsh(cov_matrix)
    dominant_eigenvalue = float(np.max(eigenvalues))
    
    if not np.isfinite(dominant_eigenvalue):
        raise ValueError(f"Dominant eigenvalue is not finite: {dominant_eigenvalue}")
    
    logger.info(f"Global dominant eigenvalue: {dominant_eigenvalue:.6f}")
    return dominant_eigenvalue

def compute_per_sample_frobenius_norm(teacher_scores: List[float]) -> float:
    """
    Compute the Frobenius norm of the outer product for a single sample.
    
    Args:
        teacher_scores: List of 4 teacher scores.
    
    Returns:
        Frobenius norm value.
    """
    return calculate_frobenius_norm_outer_product(np.array(teacher_scores))

def integrate_features(
    data_path: str,
    global_stats_path: str,
    output_path: str,
    score_columns: List[str] = REQUIRED_DIMENSIONS
) -> List[Dict[str, Any]]:
    """
    Integrate per-sample features with the global eigenvalue.
    
    Args:
        data_path: Path to the aligned data JSON file.
        global_stats_path: Path to save global statistics (eigenvalue).
        output_path: Path to save the integrated features JSON.
        score_columns: List of column names for teacher scores.
    
    Returns:
        List of integrated feature records.
    """
    logger = setup_logging()
    logger.info(f"Loading data from {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    if not data:
        raise ValueError("Data file is empty")
    
    # Compute global eigenvalue
    logger.info("Computing global dominant eigenvalue...")
    global_eigenvalue = compute_global_eigenvalue(data_path, score_columns)
    
    # Save global stats
    global_stats = {
        'global_eigenvalue': global_eigenvalue,
        'num_samples': len(data),
        'num_dimensions': len(score_columns)
    }
    
    os.makedirs(os.path.dirname(global_stats_path), exist_ok=True)
    with open(global_stats_path, 'w') as f:
        json.dump(global_stats, f, indent=2)
    
    logger.info(f"Global stats saved to {global_stats_path}")
    
    # Process each sample
    integrated_features = []
    for idx, row in enumerate(data):
        # Extract teacher scores
        teacher_scores = [row.get(col, 0.0) for col in score_columns]
        
        # Compute per-sample statistics
        sample_stats = calculate_per_sample_stats(np.array(teacher_scores))
        
        # Compute entanglement score (Frobenius norm)
        entanglement_score = compute_per_sample_frobenius_norm(teacher_scores)
        
        # Compute fidelity loss if human annotation exists
        fidelity_loss = 0.0
        if 'human_annotations' in row and row['human_annotations']:
            # Use primary dimension if available, otherwise default to first
            primary_dim = row.get('primary_dimension', score_columns[0])
            human_score = row['human_annotations'].get(primary_dim, None)
            student_scalar = row.get('student_scalar', 0.0)
            
            if human_score is not None:
                fidelity_loss = calculate_fidelity_loss(student_scalar, human_score)
        
        # Create integrated record
        record = {
            'sample_id': row.get('sample_id', f'sample_{idx}'),
            'variance': sample_stats['variance'],
            'entropy': sample_stats['entropy'],
            'skewness': sample_stats['skewness'],
            'kurtosis': sample_stats['kurtosis'],
            'range': sample_stats['range'],
            'entanglement_score': entanglement_score,
            'global_eigenvalue': global_eigenvalue,
            'fidelity_loss': fidelity_loss,
            'primary_dimension': row.get('primary_dimension', score_columns[0])
        }
        
        integrated_features.append(record)
    
    # Validate output
    for record in integrated_features:
        for key in ['sample_id', 'variance', 'entropy', 'global_eigenvalue', 
                   'entanglement_score', 'fidelity_loss']:
            if record.get(key) is None:
                raise ValueError(f"Null value found for key '{key}' in sample {record.get('sample_id')}")
    
    # Save integrated features
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(integrated_features, f, indent=2)
    
    logger.info(f"Integrated features saved to {output_path}")
    logger.info(f"Processed {len(integrated_features)} samples")
    
    return integrated_features

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Integrate per-sample features with global eigenvalue'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        required=True,
        help='Path to the aligned data JSON file'
    )
    parser.add_argument(
        '--global-stats-path',
        type=str,
        required=True,
        help='Path to save global statistics JSON'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        required=True,
        help='Path to save integrated features JSON'
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for feature integration."""
    args = parse_args()
    logger = setup_logging()
    
    try:
        integrate_features(
            data_path=args.data_path,
            global_stats_path=args.global_stats_path,
            output_path=args.output_path
        )
        logger.info("Feature integration completed successfully")
    except Exception as e:
        logger.error(f"Error during feature integration: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
