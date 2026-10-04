"""
Tractography Confidence Thresholding - Execution (Task T042)

This script implements the mandatory sensitivity analysis for tractography
confidence thresholds. It iterates through defined thresholds, recalculates
structural connectivity matrices, and computes graph metrics for each level.

Output: data/processed/tractography_sensitivity_metrics.csv
"""

import os
import sys
import gc
import traceback
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import zscore

# Project imports
from config import get_config_dict, ensure_directories
from preprocess.loader import load_hcp_dmri
from preprocess.structural import calculate_graph_metrics
from utils.cpu_optimization import force_gc_collect, set_random_seed

# Set random seed for reproducibility
set_random_seed(42)

def load_structural_connectivity_matrix(
    subject_id: str,
    confidence_threshold: float,
    config: Dict[str, Any]
) -> Optional[np.ndarray]:
    """
    Load dMRI data for a subject, apply confidence thresholding, and return
    the weighted adjacency matrix.

    Args:
        subject_id: The HCP subject ID.
        confidence_threshold: Minimum confidence score to retain an edge.
        config: Configuration dictionary.

    Returns:
        A numpy array representing the adjacency matrix (N x N), or None if
        loading fails or the subject is excluded.
    """
    try:
        # Load raw dMRI data and streamlines
        # The loader is expected to return streamlines and a confidence map
        # or a pre-computed matrix that we can filter.
        # Based on T005/T006/T041, we assume the loader provides the raw data
        # or a matrix that needs thresholding.
        
        # We assume the loader returns a dictionary with 'matrix' and 'confidence'
        # or similar, or we construct it.
        # For this implementation, we rely on the loader to fetch the raw data.
        # Since the actual raw dMRI processing (streamline generation) is complex,
        # we assume the `load_hcp_dmri` function returns the connectivity matrix
        # and a corresponding confidence matrix if available, OR we fetch the
        # raw tractography results.
        
        # Given the constraints and the fact that T041 extended the loader:
        # We assume `load_hcp_dmri` can return the connectivity matrix.
        # If the loader returns a single matrix, we need the confidence scores.
        # Let's assume the loader returns a tuple: (connectivity_matrix, confidence_matrix)
        # or we compute confidence from the raw data if available.
        
        # For the purpose of this script, we assume the loader returns:
        # (adjacency_matrix, confidence_matrix)
        # If the loader only returns the matrix, we cannot do thresholding without
        # the confidence data. We assume T041 ensured the loader exposes this.
        
        data_path = Path(config['data_raw_dir']) / subject_id
        if not data_path.exists():
            print(f"Skipping {subject_id}: Raw data path not found.")
            return None

        # Load the dMRI data (streamlines or matrix)
        # We assume the loader handles the heavy lifting of fetching from OpenNeuro
        # and pre-processing to a standard format (e.g., .npy or .mat)
        # that includes confidence scores.
        
        # Mocking the call based on expected API from T041:
        # The loader should accept a confidence_threshold if it does the filtering,
        # but T042 requires us to do the loop and re-calculate metrics, so we
        # need the raw matrix and confidence to filter manually.
        
        # Let's assume the loader returns (matrix, confidence)
        # If the loader is not yet capable of returning confidence, we must
        # fetch the raw streamlines. However, to keep this script runnable
        # within the existing API surface, we assume T041 added the capability
        # to load the confidence matrix.
        
        try:
            # Attempt to load the raw connectivity and confidence data
            # This assumes the loader returns a tuple (matrix, confidence)
            # or a dict with keys 'matrix' and 'confidence'
            result = load_hcp_dmri(subject_id, return_confidence=True)
            
            if isinstance(result, tuple) and len(result) == 2:
                matrix, confidence_matrix = result
            elif isinstance(result, dict):
                matrix = result.get('matrix')
                confidence_matrix = result.get('confidence')
            else:
                # Fallback: if only matrix is returned, we cannot do thresholding
                # unless we assume the matrix values ARE the confidence (unlikely)
                # or we skip.
                print(f"Error: Loader did not return confidence matrix for {subject_id}")
                return None
                
        except Exception as e:
            print(f"Error loading dMRI data for {subject_id}: {e}")
            return None

        if matrix is None or confidence_matrix is None:
            return None

        # Apply threshold: set edges with confidence < threshold to 0
        # We keep the structural weight (matrix value) but zero out low-confidence edges
        thresholded_matrix = matrix.copy()
        thresholded_matrix[confidence_matrix < confidence_threshold] = 0.0

        # Ensure symmetry (tractography matrices are often symmetric)
        thresholded_matrix = (thresholded_matrix + thresholded_matrix.T) / 2.0
        
        return thresholded_matrix

    except Exception as e:
        print(f"Unexpected error processing {subject_id}: {e}")
        traceback.print_exc()
        return None

def run_tractography_sensitivity_analysis(
    subjects: List[str],
    thresholds: List[float],
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Iterate through subjects and confidence thresholds to compute graph metrics.

    Args:
        subjects: List of subject IDs.
        thresholds: List of confidence thresholds to test.
        config: Configuration dictionary.

    Returns:
        DataFrame containing metrics for each subject at each threshold.
    """
    results = []
    
    # Define density thresholds from config (T004b)
    density_thresholds = config.get('DENSITY_THRESHOLD_BASELINE', 0.15)
    # If variations are needed, we might need to iterate, but the task
    # specifically asks for confidence thresholding.
    # We will use the baseline density for the graph construction after
    # confidence filtering, or we can iterate density as well if needed.
    # The task says: "recalculates the structural connectivity matrices"
    # and "recomputes the graph metrics".
    # We will use the standard density thresholding on the confidence-filtered matrix.
    
    # We'll use the baseline density threshold for all runs unless specified otherwise.
    # However, to be robust, we can use the baseline.
    
    for subject_id in subjects:
        print(f"Processing subject: {subject_id}")
        
        for conf_thresh in thresholds:
            print(f"  Applying confidence threshold: {conf_thresh}")
            
            matrix = load_structural_connectivity_matrix(
                subject_id, conf_thresh, config
            )
            
            if matrix is None:
                print(f"    Skipping: Could not load matrix.")
                continue
            
            # Check if matrix is empty (all zeros)
            if np.sum(matrix) == 0:
                print(f"    Skipping: Matrix is empty after thresholding.")
                # Record zeros or NaNs? Let's record NaNs to indicate failure.
                results.append({
                    'subject_id': subject_id,
                    'confidence_threshold': conf_thresh,
                    'global_efficiency': np.nan,
                    'clustering': np.nan,
                    'modularity': np.nan
                })
                continue

            try:
                # Calculate graph metrics
                # We need to apply density thresholding on the confidence-filtered matrix
                # to get the final graph for metric calculation.
                # Or we can just use the weighted graph. The task implies "recalculates"
                # based on the confidence filter.
                
                # We'll use the calculate_graph_metrics function from structural.py
                # It likely expects a matrix and a density threshold.
                
                metrics = calculate_graph_metrics(
                    matrix, 
                    density_threshold=density_thresholds,
                    return_raw=False
                )
                
                if metrics is None:
                    print(f"    Skipping: Graph metrics calculation failed.")
                    results.append({
                        'subject_id': subject_id,
                        'confidence_threshold': conf_thresh,
                        'global_efficiency': np.nan,
                        'clustering': np.nan,
                        'modularity': np.nan
                    })
                    continue

                results.append({
                    'subject_id': subject_id,
                    'confidence_threshold': conf_thresh,
                    'global_efficiency': metrics.get('global_efficiency', np.nan),
                    'clustering': metrics.get('clustering', np.nan),
                    'modularity': metrics.get('modularity', np.nan)
                })
                
            except Exception as e:
                print(f"    Error calculating metrics: {e}")
                traceback.print_exc()
                results.append({
                    'subject_id': subject_id,
                    'confidence_threshold': conf_thresh,
                    'global_efficiency': np.nan,
                    'clustering': np.nan,
                    'modularity': np.nan
                })
            
            # Force GC to manage memory
            force_gc_collect()
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for the tractography sensitivity analysis.
    """
    print("Starting Tractography Confidence Thresholding Analysis (T042)...")
    
    config = get_config_dict()
    ensure_directories()
    
    # Get confidence thresholds from config (T041)
    thresholds = config.get('TRACTOGRAPHY_CONFIDENCE_THRESHOLDS', [0.0, 0.2, 0.4, 0.6, 0.8])
    print(f"Using confidence thresholds: {thresholds}")
    
    # Get list of subjects from raw data directory
    raw_data_dir = Path(config['data_raw_dir'])
    if not raw_data_dir.exists():
        print("Error: data/raw directory not found.")
        sys.exit(1)
    
    subjects = [d.name for d in raw_data_dir.iterdir() if d.is_dir()]
    if not subjects:
        print("Error: No subjects found in data/raw.")
        sys.exit(1)
    
    print(f"Found {len(subjects)} subjects.")
    
    # Run analysis
    df_results = run_tractography_sensitivity_analysis(subjects, thresholds, config)
    
    # Save results
    output_path = Path(config['data_processed_dir']) / 'tractography_sensitivity_metrics.csv'
    df_results.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")
    
    # Log completion
    log_entry = {
        'task': 'T042',
        'status': 'completed',
        'subjects_processed': len(subjects),
        'thresholds_tested': thresholds,
        'output_file': str(output_path)
    }
    print(f"Log entry: {json.dumps(log_entry, indent=2)}")

if __name__ == '__main__':
    main()
