import csv
import json
import logging
import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import networkx as nx
from nilearn import datasets, image, masking
from nilearn.connectome import ConnectivityMeasure
from nilearn.input_data import NiftiLabelsMasker

# Importing from project utils to ensure consistent logging format
try:
    from utils.logging import setup_logging, log_provenance, log_exclusion
except ImportError:
    # Fallback for standalone execution if utils not in path yet
    def setup_logging(*args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    def log_provenance(*args, **kwargs): pass
    def log_exclusion(*args, **kwargs): pass

# Importing Config from project root
try:
    from config import Config
except ImportError:
    class Config:
        DATA_DIR = Path("data")
        METRICS_DIR = Path("data/metrics")
        LOG_DIR = Path("logs")
        PREPROCESSED_DIR = Path("data/processed")

logger = logging.getLogger(__name__)

def load_preprocessed_data(subject_id: str) -> Optional[Path]:
    """
    Locate the preprocessed NIfTI file for a given subject.
    Expects file at: data/processed/<subject_id>_preprocessed.nii.gz
    """
    preprocessed_dir = Config.PREPROCESSED_DIR
    filepath = preprocessed_dir / f"{subject_id}_preprocessed.nii.gz"
    if filepath.exists():
        return filepath
    logger.warning(f"Preprocessed file not found for subject {subject_id} at {filepath}")
    return None

def extract_roi_timeseries(nifti_path: Path, atlas: str = "aal") -> Tuple[np.ndarray, List[str]]:
    """
    Extract ROI timeseries using the specified atlas (default AAL).
    Returns: (timeseries matrix: [n_timepoints, n_rois], roi_names: List[str])
    """
    # Load atlas
    if atlas == "aal":
        atlas_data = datasets.fetch_atlas_aal()
        atlas_img = atlas_data.maps
        labels = atlas_data.labels
    elif atlas == "schaefer":
        # Using Schaefer 100 parcels as a moderate default
        atlas_data = datasets.fetch_atlas_schaefer_2018(n_rois=100)
        atlas_img = atlas_data.maps
        labels = atlas_data.labels
    else:
        raise ValueError(f"Unsupported atlas: {atlas}. Use 'aal' or 'schaefer'.")

    masker = NiftiLabelsMasker(
        labels_img=atlas_img,
        standardize=True,
        detrend=True,
        low_pass=0.1,
        high_pass=0.01,
        t_r=2.0, # Default TR, should ideally come from metadata
        memory="nilearn_cache",
        memory_level=1
    )

    try:
        timeseries = masker.fit_transform(nifti_path)
    except Exception as e:
        logger.error(f"Failed to extract timeseries from {nifti_path}: {e}")
        raise

    return timeseries, list(labels)

def calculate_connectivity_matrix(timeseries: np.ndarray, method: str = "pearson") -> np.ndarray:
    """
    Calculate the connectivity matrix from timeseries.
    Handles NaN/Inf in input timeseries by replacing with 0 before calculation.
    """
    # Sanitize input
    if np.any(np.isnan(timeseries)) or np.any(np.isinf(timeseries)):
        logger.warning("Input timeseries contains NaN or Inf. Replacing with 0.")
        timeseries = np.nan_to_num(timeseries, nan=0.0, posinf=0.0, neginf=0.0)

    conn_measure = ConnectivityMeasure(kind=method)
    try:
        matrices = conn_measure.fit_transform([timeseries])
        return matrices[0]
    except Exception as e:
        logger.error(f"Error calculating connectivity matrix: {e}")
        raise

def calculate_network_metrics(connectivity_matrix: np.ndarray) -> Dict[str, float]:
    """
    Calculate Modularity, Global Efficiency, and Local Efficiency.
    Implements robust NaN/Infinity handling:
    1. Checks input matrix for invalid values.
    2. Checks calculated metrics for invalid values.
    3. Returns None for invalid metrics and logs the event.
    """
    metrics = {}

    # 1. Input Validation
    if np.any(np.isnan(connectivity_matrix)) or np.any(np.isinf(connectivity_matrix)):
        logger.error("Connectivity matrix contains NaN or Inf. Skipping metric calculation.")
        return {
            "modularity": None,
            "global_efficiency": None,
            "local_efficiency": None
        }

    # Create NetworkX graph
    # Thresholding: Keep edges > 0 (positive correlation) for efficiency calc
    # Convert to directed graph for efficiency calculations (undirected is also fine, but nx expects specific types)
    G = nx.from_numpy_array(connectivity_matrix, create_using=nx.Graph)
    # Remove self-loops
    G.remove_edges_from(nx.selfloop_edges(G))

    # 2. Modularity Calculation
    try:
        # Community detection using Louvain
        # If graph is disconnected or empty, handle gracefully
        if G.number_of_nodes() == 0:
            raise ValueError("Graph has no nodes")
        
        # Use a fixed random seed for reproducibility if needed, but here we just run
        try:
            partition = nx.community.louvain_communities(G, seed=42)
            q = nx.community.modularity(G, partition)
            
            if math.isnan(q) or math.isinf(q):
                logger.warning(f"Calculated Modularity Q is invalid: {q}. Setting to None.")
                metrics["modularity"] = None
            else:
                metrics["modularity"] = float(q)
        except Exception as comm_err:
            logger.warning(f"Community detection failed ({comm_err}). Setting modularity to None.")
            metrics["modularity"] = None
    except Exception as e:
        logger.error(f"Error calculating modularity: {e}")
        metrics["modularity"] = None

    # 3. Global Efficiency
    try:
        if G.number_of_nodes() < 2:
            raise ValueError("Graph too small for efficiency")
        
        ge = nx.global_efficiency(G)
        if math.isnan(ge) or math.isinf(ge):
            logger.warning(f"Calculated Global Efficiency is invalid: {ge}. Setting to None.")
            metrics["global_efficiency"] = None
        else:
            metrics["global_efficiency"] = float(ge)
    except Exception as e:
        logger.error(f"Error calculating global efficiency: {e}")
        metrics["global_efficiency"] = None

    # 4. Local Efficiency
    try:
        if G.number_of_nodes() < 2:
            raise ValueError("Graph too small for local efficiency")
        
        le = nx.local_efficiency(G)
        if math.isnan(le) or math.isinf(le):
            logger.warning(f"Calculated Local Efficiency is invalid: {le}. Setting to None.")
            metrics["local_efficiency"] = None
        else:
            metrics["local_efficiency"] = float(le)
    except Exception as e:
        logger.error(f"Error calculating local efficiency: {e}")
        metrics["local_efficiency"] = None

    return metrics

def save_metrics_to_csv(subject_id: str, metrics: Dict[str, float], output_path: Path):
    """
    Append metrics to a CSV file.
    Handles None values by writing 'NaN' string or empty cell.
    """
    file_exists = output_path.exists()
    
    with open(output_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["subject_id", "modularity", "global_efficiency", "local_efficiency"])
        
        # Convert None to string 'NaN' for CSV consistency
        row = [
            subject_id,
            metrics.get("modularity") if metrics.get("modularity") is not None else "NaN",
            metrics.get("global_efficiency") if metrics.get("global_efficiency") is not None else "NaN",
            metrics.get("local_efficiency") if metrics.get("local_efficiency") is not None else "NaN"
        ]
        writer.writerow(row)

def run_analysis(subject_id: str, atlas: str = "aal") -> Dict[str, float]:
    """
    Run the full analysis pipeline for a single subject.
    Returns the dictionary of metrics (with None for invalid ones).
    """
    logger.info(f"Starting analysis for subject: {subject_id}")
    
    nifti_path = load_preprocessed_data(subject_id)
    if not nifti_path:
        logger.error(f"Skipping {subject_id}: No preprocessed data found.")
        return {"modularity": None, "global_efficiency": None, "local_efficiency": None}

    try:
        timeseries, roi_names = extract_roi_timeseries(nifti_path, atlas=atlas)
        logger.info(f"Extracted timeseries for {subject_id}: shape {timeseries.shape}")
        
        conn_matrix = calculate_connectivity_matrix(timeseries)
        logger.info(f"Calculated connectivity matrix for {subject_id}")
        
        metrics = calculate_network_metrics(conn_matrix)
        
        # Log specific invalid metrics found
        invalid_keys = [k for k, v in metrics.items() if v is None]
        if invalid_keys:
            logger.warning(f"Subject {subject_id} has invalid metrics: {invalid_keys}")
            log_exclusion(subject_id, "Invalid Network Metrics", f"Metrics {invalid_keys} contained NaN/Inf")
        
        return metrics

    except Exception as e:
        logger.error(f"Analysis failed for {subject_id}: {e}")
        log_exclusion(subject_id, "Analysis Failure", str(e))
        return {"modularity": None, "global_efficiency": None, "local_efficiency": None}

def main():
    """
    Main entry point for running analysis on all subjects in the processed directory.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Ensure output directories exist
    Config.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = Config.METRICS_DIR / "network_metrics.csv"
    
    # Get list of subjects (simple heuristic: look for _preprocessed.nii.gz)
    subjects = []
    if Config.PREPROCESSED_DIR.exists():
        for f in Config.PREPROCESSED_DIR.glob("*_preprocessed.nii.gz"):
            sid = f.stem.replace("_preprocessed", "")
            subjects.append(sid)
    
    if not subjects:
        logger.warning("No preprocessed subjects found in data/processed. Exiting.")
        sys.exit(0)
    
    logger.info(f"Found {len(subjects)} subjects to process.")
    
    for sid in subjects:
        metrics = run_analysis(sid)
        save_metrics_to_csv(sid, metrics, output_file)
        logger.info(f"Saved metrics for {sid}")
    
    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()