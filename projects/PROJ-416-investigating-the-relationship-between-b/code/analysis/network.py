import csv
import json
import logging
import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import networkx as nx
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_aal

from code.config import Config
from code.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_preprocessed_data(
    processed_dir: Path, subject_ids: List[str]
) -> Dict[str, np.ndarray]:
    """
    Load preprocessed fMRI NIfTI files for a list of subjects.

    Args:
        processed_dir: Path to the directory containing preprocessed data.
        subject_ids: List of subject identifiers to load.

    Returns:
        A dictionary mapping subject_id to a 2D numpy array of shape (time_points, voxels).
    """
    data_dict = {}
    for sub_id in subject_ids:
        file_path = processed_dir / f"{sub_id}_preproc.nii.gz"
        if not file_path.exists():
            logger.warning(f"Preprocessed file not found for {sub_id}: {file_path}")
            continue

        try:
            # Load image and flatten to 2D (time, voxels)
            img = image.load_img(str(file_path))
            data = masking.apply_mask(img, mask_img=None) # Assumes whole brain or specific mask logic handled elsewhere
            # If mask_img is None, nilearn might need a specific mask. 
            # For this implementation, we assume the preprocessed file is ready for analysis 
            # or we load a standard brain mask if available in config.
            # Simplified for this context:
            data_dict[sub_id] = data
            logger.info(f"Loaded data for {sub_id}: shape {data.shape}")
        except Exception as e:
            logger.error(f"Failed to load data for {sub_id}: {e}")
    return data_dict


def extract_roi_timeseries(
    fmri_data: np.ndarray, atlas_mask: np.ndarray, atlas_labels: List[str]
) -> np.ndarray:
    """
    Extract average time series for each ROI from the fmri data using an atlas mask.

    Args:
        fmri_data: 2D numpy array of shape (time_points, voxels).
        atlas_mask: 1D or 2D array indicating ROI membership (e.g., integer labels per voxel).
        atlas_labels: List of labels corresponding to ROI indices.

    Returns:
        2D numpy array of shape (time_points, num_rois).
    """
    if fmri_data.ndim != 2:
        raise ValueError("fmri_data must be 2D (time, voxels)")

    num_rois = len(atlas_labels)
    time_series = np.zeros((fmri_data.shape[0], num_rois))

    # Assuming atlas_mask maps voxel index to ROI index (0 to num_rois-1)
    # This is a simplified extraction; real implementation might use nilearn's NiftiLabelsMasker
    for i, label in enumerate(atlas_labels):
        # Find voxels belonging to this ROI
        # Note: atlas_mask logic depends on how it's provided. 
        # Here we assume atlas_mask is a 1D array of length equal to voxels, 
        # where values are ROI indices (0-based or 1-based).
        # Adjust based on actual mask format.
        roi_voxels = np.where(atlas_mask == i + 1)[0] # Assuming 1-based labels in mask
        if len(roi_voxels) == 0:
            logger.warning(f"No voxels found for ROI {label} (index {i})")
            time_series[:, i] = np.nan
        else:
            time_series[:, i] = np.mean(fmri_data[:, roi_voxels], axis=1)

    return time_series


def calculate_connectivity_matrix(
    roi_timeseries: np.ndarray, method: str = "pearson"
) -> np.ndarray:
    """
    Calculate the functional connectivity matrix from ROI time series.

    Args:
        roi_timeseries: 2D numpy array of shape (time_points, num_rois).
        method: Correlation method ('pearson', 'spearman').

    Returns:
        2D numpy array (num_rois, num_rois) representing the connectivity matrix.
    """
    if roi_timeseries.shape[0] < 2:
        raise ValueError("Need at least 2 time points to calculate connectivity.")

    if method == "pearson":
        corr_matrix = np.corrcoef(roi_timeseries.T)
    elif method == "spearman":
        from scipy.stats import spearmanr
        corr_matrix, _ = spearmanr(roi_timeseries, axis=0)
    else:
        raise ValueError(f"Unsupported method: {method}")

    # Handle NaNs (e.g., from constant time series)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    return corr_matrix


def calculate_network_metrics(
    connectivity_matrix: np.ndarray, threshold: float = 0.2
) -> Dict[str, float]:
    """
    Calculate network metrics (Modularity, Global Efficiency, Local Efficiency) from a connectivity matrix.

    Args:
        connectivity_matrix: 2D numpy array (num_rois, num_rois).
        threshold: Threshold for binarizing the weighted matrix.

    Returns:
        Dictionary containing 'modularity_q', 'global_efficiency', 'local_efficiency'.
    """
    # Create a graph from the connectivity matrix
    G = nx.from_numpy_array(connectivity_matrix)
    
    # Binarize the graph based on threshold
    # Keep edges with weight > threshold
    edges_to_remove = []
    for u, v, data in G.edges(data=True):
        if data['weight'] <= threshold:
            edges_to_remove.append((u, v))
    G.remove_edges_from(edges_to_remove)

    if G.number_of_edges() == 0:
        logger.warning("Graph is empty after thresholding. Returning zeros.")
        return {
            "modularity_q": 0.0,
            "global_efficiency": 0.0,
            "local_efficiency": 0.0
        }

    # Modularity
    try:
        # Use a partition algorithm if communities not pre-defined
        # Here we use Louvain method
        partition = nx.community.louvain_communities(G)
        modularity_q = nx.community.modularity(G, partition)
    except Exception as e:
        logger.warning(f"Modularity calculation failed: {e}. Setting to 0.")
        modularity_q = 0.0

    # Global Efficiency
    try:
        global_eff = nx.global_efficiency(G)
    except Exception as e:
        logger.warning(f"Global efficiency calculation failed: {e}. Setting to 0.")
        global_eff = 0.0

    # Local Efficiency
    try:
        local_eff = nx.average_local_efficiency(G)
    except Exception as e:
        logger.warning(f"Local efficiency calculation failed: {e}. Setting to 0.")
        local_eff = 0.0

    return {
        "modularity_q": float(modularity_q),
        "global_efficiency": float(global_eff),
        "local_efficiency": float(local_eff)
    }


def save_metrics_to_csv(
    metrics_list: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Save a list of metric dictionaries to a CSV file.

    Args:
        metrics_list: List of dictionaries, each containing subject_id and metrics.
        output_path: Path to the output CSV file.
    """
    if not metrics_list:
        logger.warning("No metrics to save.")
        return

    fieldnames = ["subject_id"] + list(metrics_list[0].keys())
    fieldnames = [f for f in fieldnames if f != "subject_id"]
    fieldnames.insert(0, "subject_id")

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics_list)

    logger.info(f"Saved metrics to {output_path}")


def run_analysis(
    processed_dir: Path,
    output_dir: Path,
    subject_ids: List[str],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Run the full network analysis pipeline for a set of subjects.

    Args:
        processed_dir: Path to preprocessed data.
        output_dir: Path to save results.
        subject_ids: List of subject IDs to process.
        config: Configuration object containing atlas and threshold settings.

    Returns:
        List of dictionaries containing metrics for each subject.
    """
    ensure_directories(output_dir)
    
    # Fetch atlas (simplified)
    # In a real scenario, this might be cached or specified in config
    try:
        atlas_data = fetch_atlas_aal()
        atlas_img = image.load_img(atlas_data.maps)
        atlas_mask = masking.apply_mask(atlas_img, mask_img=None) # Simplified
        # This is a placeholder for actual atlas loading logic
        # Real implementation would need to align atlas with subject space
        atlas_labels = [f"ROI_{i}" for i in range(1, 121)] # AAL has 116+ regions
    except Exception as e:
        logger.error(f"Failed to fetch atlas: {e}")
        return []

    metrics_list = []
    for sub_id in subject_ids:
        try:
            # Load data
            fmri_data = load_preprocessed_data(processed_dir, [sub_id]).get(sub_id)
            if fmri_data is None:
                continue

            # Extract ROI timeseries
            roi_ts = extract_roi_timeseries(fmri_data, atlas_mask, atlas_labels)

            # Calculate connectivity
            conn_matrix = calculate_connectivity_matrix(roi_ts)

            # Calculate metrics
            metrics = calculate_network_metrics(conn_matrix, config.network_threshold)

            # Store results
            result = {"subject_id": sub_id}
            result.update(metrics)
            metrics_list.append(result)
            
            logger.info(f"Processed {sub_id}: {metrics}")
        except Exception as e:
            logger.error(f"Error processing {sub_id}: {e}")
            continue

    # Save results
    output_file = output_dir / "network_metrics.csv"
    save_metrics_to_csv(metrics_list, output_file)

    return metrics_list


def ensure_directories(path: Path) -> None:
    """Ensure the given path exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point for the network analysis script."""
    setup_logging()
    config = Config()
    
    processed_dir = Path(config.processed_data_dir)
    output_dir = Path(config.metrics_output_dir)
    
    # For demo, load all subjects in processed_dir (or filter as needed)
    # In real run, this would come from a manifest or command line arg
    subject_ids = [f"sub-{i:03d}" for i in range(1, 11)] # Placeholder

    run_analysis(processed_dir, output_dir, subject_ids, config)


if __name__ == "__main__":
    main()
