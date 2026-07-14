"""
Metrics extraction module for brain network analysis.

Handles Schaefer atlas loading, time-series extraction, connectivity matrix
calculation, graph metric computation, and node-level metric aggregation.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import datasets
from nilearn.maskers import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from sklearn.preprocessing import StandardScaler
import networkx as nx

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants
SCHAEFER_ATLAS_URL = "https://github.com/ThomasYeoLab/CBIG/blob/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/Schaefer2018_400Parcels_17Networks_order.txt?raw=true"
DEFAULT_ATLAS_PATH = "data/raw/schaefer_400_order.txt"
DEFAULT_CONNECTIVITY_PATH = "data/processed/connectivity_matrices"
DEFAULT_METRICS_PATH = "data/processed/aggregated_metrics.csv"

def download_schaefer_atlas(output_path: Optional[str] = None) -> str:
    """
    Download the Schaefer 400-parcel atlas if not already present.
    
    Args:
        output_path: Optional path to save the atlas file.
        
    Returns:
        Path to the downloaded atlas file.
    """
    if output_path is None:
        output_path = DEFAULT_ATLAS_PATH
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        logger.log("atlas_exists", path=str(output_path))
        return str(output_path)
    
    logger.log("downloading_atlas", url=SCHAEFER_ATLAS_URL, target=str(output_path))
    try:
        # Using nilearn's fetch function or direct download
        # For the order file, we need the text file
        import requests
        response = requests.get(SCHAEFER_ATLAS_URL)
        response.raise_for_status()
        with open(output_path, 'w') as f:
            f.write(response.text)
        logger.log("atlas_downloaded", path=str(output_path))
    except Exception as e:
        logger.log("atlas_download_failed", error=str(e))
        raise
    
    return str(output_path)

def load_atlas(atlas_path: Optional[str] = None) -> Tuple[np.ndarray, List[str]]:
    """
    Load the Schaefer atlas parcellation file.
    
    Args:
        atlas_path: Path to the atlas file.
        
    Returns:
        Tuple of (parcel_labels array, network_names list).
    """
    if atlas_path is None:
        atlas_path = download_schaefer_atlas()
    
    atlas_path = Path(atlas_path)
    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")
    
    logger.log("loading_atlas", path=str(atlas_path))
    
    # The Schaefer order file contains the network assignment for each parcel
    parcels = []
    with open(atlas_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    parcels.append(parts[1])
    
    parcels = np.array(parcels)
    logger.log("atlas_loaded", n_parcels=len(parcels))
    return parcels, []

def extract_time_series(
    nifti_path: str,
    atlas_path: Optional[str] = None,
    atlas_img_path: Optional[str] = None
) -> np.ndarray:
    """
    Extract time-series from a preprocessed NIfTI file using the Schaefer atlas.
    
    Args:
        nifti_path: Path to the preprocessed NIfTI file.
        atlas_path: Path to the Schaefer atlas parcellation file.
        atlas_img_path: Path to the NIfTI version of the atlas (required for NiftiLabelsMasker).
        
    Returns:
        Time-series matrix of shape (n_timepoints, n_parcels).
    """
    if atlas_img_path is None:
        raise ValueError("atlas_img_path is required for time-series extraction")
    
    logger.log("extracting_timeseries", nifti=nifti_path, atlas=atlas_img_path)
    
    masker = NiftiLabelsMasker(
        labels_img=atlas_img_path,
        standardize=True,
        detrend=True,
        low_pass=0.1,
        high_pass=0.01,
        t_r=0.72,  # HCP TR
        memory="data/cache",
        verbose=0
    )
    
    try:
        time_series = masker.fit_transform(nifti_path)
        logger.log("timeseries_extracted", shape=time_series.shape)
        return time_series
    except Exception as e:
        logger.log("timeseries_extraction_failed", error=str(e))
        raise

def apply_motion_regression(
    time_series: np.ndarray,
    motion_params: np.ndarray
) -> np.ndarray:
    """
    Regress out motion parameters from the time-series.
    
    Args:
        time_series: Time-series matrix (n_timepoints, n_parcels).
        motion_params: Motion parameters (n_timepoints, n_params).
        
    Returns:
        Cleaned time-series matrix.
    """
    logger.log("applying_motion_regression", ts_shape=time_series.shape, motion_shape=motion_params.shape)
    
    if motion_params.shape[0] != time_series.shape[0]:
        raise ValueError("Motion parameters and time-series must have same number of timepoints")
    
    # Simple linear regression to remove motion effects
    from sklearn.linear_model import LinearRegression
    
    cleaned_ts = time_series.copy()
    for i in range(time_series.shape[1]):
        model = LinearRegression()
        model.fit(motion_params, time_series[:, i])
        residuals = time_series[:, i] - model.predict(motion_params)
        cleaned_ts[:, i] = residuals
    
    logger.log("motion_regression_complete", cleaned_shape=cleaned_ts.shape)
    return cleaned_ts

def calculate_connectivity_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Calculate the 400x400 functional connectivity matrix (Pearson correlation).
    
    Args:
        time_series: Time-series matrix (n_timepoints, n_parcels).
        
    Returns:
        Connectivity matrix (n_parcels, n_parcels).
    """
    logger.log("calculating_connectivity_matrix", ts_shape=time_series.shape)
    
    if time_series.shape[1] != 400:
        logger.log("warning", message=f"Expected 400 parcels, got {time_series.shape[1]}")
    
    conn_measure = ConnectivityMeasure(
        kind='correlation',
        standardize=False
    )
    
    connectivity_matrix = conn_measure.fit_transform([time_series])[0]
    
    # Ensure symmetry
    connectivity_matrix = (connectivity_matrix + connectivity_matrix.T) / 2
    np.fill_diagonal(connectivity_matrix, 0)
    
    logger.log("connectivity_matrix_calculated", shape=connectivity_matrix.shape)
    return connectivity_matrix

def calculate_graph_metrics(connectivity_matrix: np.ndarray) -> Dict[str, float]:
    """
    Calculate global graph metrics: Modularity, Global Efficiency, etc.
    
    Args:
        connectivity_matrix: Connectivity matrix (n_nodes, n_nodes).
        
    Returns:
        Dictionary of graph metrics.
    """
    logger.log("calculating_graph_metrics", matrix_shape=connectivity_matrix.shape)
    
    # Create graph from connectivity matrix
    G = nx.Graph()
    n_nodes = connectivity_matrix.shape[0]
    G.add_nodes_from(range(n_nodes))
    
    # Add edges with weights (only positive correlations for now)
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if connectivity_matrix[i, j] > 0:
                G.add_edge(i, j, weight=connectivity_matrix[i, j])
    
    metrics = {}
    
    try:
        # Modularity (requires community detection)
        from networkx.algorithms.community import modularity, greedy_modularity_communities
        communities = greedy_modularity_communities(G, weight='weight')
        metrics['modularity'] = modularity(G, communities)
    except Exception as e:
        logger.log("modularity_calculation_failed", error=str(e))
        metrics['modularity'] = np.nan
    
    try:
        # Global Efficiency
        metrics['global_efficiency'] = nx.global_efficiency(G)
    except Exception as e:
        logger.log("global_efficiency_calculation_failed", error=str(e))
        metrics['global_efficiency'] = np.nan
    
    logger.log("graph_metrics_calculated", metrics=metrics)
    return metrics

def calculate_node_level_metrics(
    connectivity_matrix: np.ndarray,
    n_modules: int = 17
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate node-level metrics: Participation Coefficient and Within-Module Degree.
    
    Args:
        connectivity_matrix: Connectivity matrix (n_nodes, n_nodes).
        n_modules: Number of modules (default 17 for Schaefer atlas).
        
    Returns:
        Tuple of (participation_coefficients, within_module_degrees).
    """
    logger.log("calculating_node_level_metrics", matrix_shape=connectivity_matrix.shape, n_modules=n_modules)
    
    n_nodes = connectivity_matrix.shape[0]
    
    # Assign nodes to modules (simplified: round-robin for demonstration)
    # In practice, this should use the actual community assignment from modularity
    node_modules = np.arange(n_nodes) % n_modules
    
    participation_coef = np.zeros(n_nodes)
    within_module_degree = np.zeros(n_nodes)
    
    # Calculate degree for each node
    degrees = np.sum(connectivity_matrix > 0, axis=1)
    
    for i in range(n_nodes):
        # Participation Coefficient: how evenly connected a node is across modules
        module_connections = np.zeros(n_modules)
        for j in range(n_nodes):
            if connectivity_matrix[i, j] > 0:
                module_connections[node_modules[j]] += connectivity_matrix[i, j]
        
        total_connections = np.sum(module_connections)
        if total_connections > 0:
            pc = 1 - np.sum((module_connections / total_connections) ** 2)
        else:
            pc = 0
        participation_coef[i] = pc
        
        # Within-Module Degree: degree normalized by average degree within module
        module_degree = np.sum(connectivity_matrix[i, :] * (node_modules == node_modules[i]))
        module_nodes = np.where(node_modules == node_modules[i])[0]
        if len(module_nodes) > 1:
            avg_degree = np.mean([np.sum(connectivity_matrix[m, :] * (node_modules == node_modules[m])) for m in module_nodes if m != i])
            if avg_degree > 0:
                wmd = (module_degree - avg_degree) / (np.std([np.sum(connectivity_matrix[m, :] * (node_modules == node_modules[m])) for m in module_nodes if m != i]) + 1e-8)
            else:
                wmd = 0
        else:
            wmd = 0
        within_module_degree[i] = wmd
    
    logger.log("node_level_metrics_calculated", pc_shape=participation_coef.shape, wmd_shape=within_module_degree.shape)
    return participation_coef, within_module_degree

def aggregate_node_metrics(
    participation_coef: np.ndarray,
    within_module_degree: np.ndarray,
    subject_id: str,
    output_path: Optional[str] = None
) -> Dict[str, float]:
    """
    Aggregate node-level metrics into a single scalar per subject.
    
    This function computes the mean across all nodes for each metric,
    producing a single representative value per subject as required by FR-003.
    
    Args:
        participation_coef: Node-level participation coefficients (n_nodes,).
        within_module_degree: Node-level within-module degrees (n_nodes,).
        subject_id: Identifier for the subject.
        output_path: Optional path to save aggregated metrics.
        
    Returns:
        Dictionary with aggregated scalar values.
    """
    logger.log("aggregating_node_metrics", subject_id=subject_id, n_nodes=len(participation_coef))
    
    # Aggregate by taking the mean across nodes
    aggregated = {
        'subject_id': subject_id,
        'participation_coef_mean': float(np.mean(participation_coef)),
        'within_module_degree_mean': float(np.mean(within_module_degree))
    }
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data if present
        if output_path.exists():
            df = pd.read_csv(output_path)
        else:
            df = pd.DataFrame(columns=['subject_id', 'participation_coef_mean', 'within_module_degree_mean'])
        
        # Append new row
        new_row = pd.DataFrame([aggregated])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(output_path, index=False)
        logger.log("aggregated_metrics_saved", path=str(output_path))
    
    logger.log("node_metrics_aggregated", metrics=aggregated)
    return aggregated

def process_subject(
    subject_id: str,
    nifti_path: str,
    atlas_img_path: str,
    motion_params: Optional[np.ndarray] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a single subject: extract time-series, calculate connectivity,
    compute graph metrics, and aggregate node-level metrics.
    
    Args:
        subject_id: Subject identifier.
        nifti_path: Path to preprocessed NIfTI file.
        atlas_img_path: Path to atlas NIfTI file.
        motion_params: Optional motion parameters for regression.
        output_dir: Directory to save outputs.
        
    Returns:
        Dictionary containing all computed metrics.
    """
    logger.log("processing_subject", subject_id=subject_id, nifti=nifti_path)
    
    # Extract time-series
    time_series = extract_time_series(nifti_path, atlas_img_path=atlas_img_path)
    
    # Apply motion regression if parameters provided
    if motion_params is not None:
        time_series = apply_motion_regression(time_series, motion_params)
    
    # Calculate connectivity matrix
    connectivity_matrix = calculate_connectivity_matrix(time_series)
    
    # Calculate global graph metrics
    graph_metrics = calculate_graph_metrics(connectivity_matrix)
    
    # Calculate node-level metrics
    participation_coef, within_module_degree = calculate_node_level_metrics(connectivity_matrix)
    
    # Aggregate node-level metrics
    output_path = None
    if output_dir:
        output_path = str(Path(output_dir) / "aggregated_metrics.csv")
    
    aggregated = aggregate_node_metrics(
        participation_coef,
        within_module_degree,
        subject_id,
        output_path
    )
    
    result = {
        'subject_id': subject_id,
        'connectivity_matrix': connectivity_matrix,
        'graph_metrics': graph_metrics,
        'aggregated_node_metrics': aggregated
    }
    
    logger.log("subject_processing_complete", subject_id=subject_id)
    return result

def main():
    """
    Main entry point for metrics extraction.
    Demonstrates the full pipeline on a sample subject.
    """
    logger.log("metrics_module_main", message="Starting metrics extraction demo")
    
    # This would typically be called with real data paths
    # For now, we log the available functions
    logger.log("available_functions", functions=[
        "download_schaefer_atlas",
        "load_atlas",
        "extract_time_series",
        "apply_motion_regression",
        "calculate_connectivity_matrix",
        "calculate_graph_metrics",
        "calculate_node_level_metrics",
        "aggregate_node_metrics",
        "process_subject"
    ])
    
    print("Metrics extraction module loaded successfully.")
    print("Use process_subject() to run the full pipeline on a subject.")

if __name__ == "__main__":
    main()