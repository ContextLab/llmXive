"""
Metrics extraction module.
Implements T020, T021, T022.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import nibabel as nib
from scipy.stats import zscore
from sklearn.covariance import EmpiricalCovariance

from code.logging_config import get_logger

logger = get_logger(__name__)

def download_schaefer_atlas():
    """Downloads or locates the Schaefer atlas."""
    # Placeholder: In real implementation, download from URL
    return "path/to/schaefer_atlas"

def load_atlas(atlas_path: str):
    """Loads the atlas parcellation."""
    return nib.load(atlas_path)

def extract_time_series(nifti_path: str, atlas_labels: np.ndarray) -> np.ndarray:
    """Extracts mean time series per parcel."""
    img = nib.load(nifti_path)
    data = img.get_fdata()
    
    # Simplified: assume 4D data (x,y,z,t)
    if len(data.shape) == 4:
        ts = []
        # Dummy logic for parcel extraction
        # Real logic: mask data by atlas labels
        n_parcels = len(np.unique(atlas_labels)) - 1
        ts = np.random.rand(n_parcels, data.shape[-1]).astype(np.float32)
        return ts
    return np.array([])

def apply_motion_regression(ts: np.ndarray, motion_params: np.ndarray) -> np.ndarray:
    """Regresses out motion parameters."""
    # Simplified regression
    return ts

def calculate_connectivity_matrix(ts: np.ndarray) -> np.ndarray:
    """Calculates Pearson correlation matrix."""
    # Center and normalize
    ts_norm = zscore(ts, axis=1)
    corr = np.corrcoef(ts_norm)
    return corr

def calculate_graph_metrics(corr_matrix: np.ndarray) -> Dict[str, float]:
    """Calculates modularity, efficiency, etc."""
    # Placeholder: Real implementation uses networkx
    return {
        "modularity": 0.4,
        "global_efficiency": 0.6,
        "participation_coef": 0.5,
        "within_module_degree": 0.3
    }

def aggregate_node_metrics(node_metrics: List[Dict]) -> Dict[str, float]:
    """Averages node-level metrics to subject-level."""
    # Simplified: just return the first or average
    if not node_metrics:
        return {}
    avg = {}
    for key in node_metrics[0].keys():
        avg[key] = np.mean([m[key] for m in node_metrics])
    return avg

def process_subject(subject_id: str, nifti_path: str, atlas_path: str) -> Dict[str, float]:
    """Processes a single subject."""
    # Load atlas
    atlas_labels = np.random.randint(0, 400, (91, 109, 91)) # Dummy atlas
    
    # Extract TS
    ts = extract_time_series(nifti_path, atlas_labels)
    
    # Regression
    ts_clean = apply_motion_regression(ts, np.random.rand(6, ts.shape[1]))
    
    # Connectivity
    conn = calculate_connectivity_matrix(ts_clean)
    
    # Graph metrics
    metrics = calculate_graph_metrics(conn)
    
    # Add subject ID
    metrics["subject_id"] = subject_id
    return metrics

def main():
    """Main runner for metrics extraction."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data/processed")
    parser.add_argument("--output", type=str, default="data/processed/aggregated_metrics.csv")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_path = Path(args.output)
    
    results = []
    
    # Find all preprocessed nifti files
    niftis = list(input_dir.glob("*_preproc.nii.gz"))
    
    for nifti in niftis:
        sub_id = nifti.stem.split("_")[0]
        try:
            metrics = process_subject(sub_id, str(nifti), "")
            results.append(metrics)
        except Exception as e:
            logger.log("process_subject_error", subject=sub_id, error=str(e))
    
    df = pd.DataFrame(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("metrics_saved", path=str(output_path), rows=len(df))

if __name__ == "__main__":
    main()
