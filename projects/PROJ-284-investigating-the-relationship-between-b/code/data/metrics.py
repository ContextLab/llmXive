from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_schaefer_2018
from nilearn.input_data import NiftiLabelsMasker
import networkx as nx

from code.logging_config import get_logger

logger = get_logger(__name__)


def download_schaefer_atlas(
    n_rois: int = 400,
    yeo_networks: int = 7,
    resolution_mm: int = 2,
    base_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Download the Schaefer atlas and return the path to the label file.

    Args:
        n_rois: Number of ROIs (parcels) in the atlas.
        yeo_networks: Number of Yeo networks (7 or 17).
        resolution_mm: Resolution in mm (2 or 3).
        base_dir: Directory to download the atlas to.

    Returns:
        Path to the Schaefer atlas label file.
    """
    logger.log("download_schaefer_atlas", n_rois=n_rois, yeo_networks=yeo_networks)

    atlas_data = fetch_atlas_schaefer_2018(
        n_rois=n_rois,
        yeo_networks=yeo_networks,
        resolution_mm=resolution_mm,
        data_dir=str(base_dir) if base_dir else None,
    )

    return Path(atlas_data.maps)


def load_atlas(atlas_path: Union[str, Path]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load the Schaefer atlas and return the label image and metadata.

    Args:
        atlas_path: Path to the atlas NIfTI file.

    Returns:
        Tuple of (nibabel image, metadata dict).
    """
    logger.log("load_atlas", atlas_path=str(atlas_path))
    atlas_img = nib.load(str(atlas_path))
    return atlas_img, {"shape": atlas_img.shape, "affine": atlas_img.affine}


def extract_time_series(
    func_img: Union[str, Path, nib.Nifti1Image],
    atlas_img: Union[str, Path, nib.Nifti1Image],
    mask_img: Optional[Union[str, Path, nib.Nifti1Image]] = None,
    standardize: bool = True,
    detrend: bool = True,
) -> np.ndarray:
    """
    Extract time series from fMRI data using the Schaefer atlas.

    Args:
        func_img: Path to functional image or NIfTI image object.
        atlas_img: Path to atlas image or NIfTI image object.
        mask_img: Optional brain mask.
        standardize: Whether to standardize the time series.
        detrend: Whether to detrend the time series.

    Returns:
        Array of shape (n_rois, n_timepoints).
    """
    logger.log(
        "extract_time_series",
        func_img=str(func_img) if isinstance(func_img, (str, Path)) else "NiftiImage",
        atlas_img=str(atlas_img) if isinstance(atlas_img, (str, Path)) else "NiftiImage",
        standardize=standardize,
        detrend=detrend,
    )

    if isinstance(func_img, (str, Path)):
        func_img = nib.load(str(func_img))
    if isinstance(atlas_img, (str, Path)):
        atlas_img = nib.load(str(atlas_img))
    if mask_img and isinstance(mask_img, (str, Path)):
        mask_img = nib.load(str(mask_img))

    masker = NiftiLabelsMasker(
        labels_img=atlas_img,
        mask_img=mask_img,
        standardize=standardize,
        detrend=detrend,
        resampling_target="labels",
    )
    time_series = masker.fit_transform(func_img)

    # NiftiLabelsMasker returns (n_timepoints, n_rois), we want (n_rois, n_timepoints)
    return time_series.T


def apply_motion_regression(
    time_series: np.ndarray,
    motion_params: Optional[np.ndarray] = None,
    global_signal: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Regress out motion parameters and/or global signal from time series.

    Args:
        time_series: Time series of shape (n_rois, n_timepoints).
        motion_params: Motion parameters of shape (n_timepoints, n_params).
        global_signal: Global signal of shape (n_timepoints,).

    Returns:
        Regressed time series of shape (n_rois, n_timepoints).
    """
    logger.log(
        "apply_motion_regression",
        time_series_shape=time_series.shape,
        has_motion_params=motion_params is not None,
        has_global_signal=global_signal is not None,
    )

    if motion_params is None and global_signal is None:
        return time_series

    # Transpose to (n_timepoints, n_rois) for regression
    ts_T = time_series.T
    n_timepoints = ts_T.shape[0]

    # Build regressors
    regressors = []
    if motion_params is not None:
        regressors.append(motion_params)
    if global_signal is not None:
        regressors.append(global_signal.reshape(-1, 1))

    if regressors:
        X = np.hstack(regressors)
        # Add intercept
        X = np.column_stack([np.ones(n_timepoints), X])

        # Compute residuals: Y - X @ beta
        # beta = (X^T X)^-1 X^T Y
        try:
            beta = np.linalg.lstsq(X, ts_T, rcond=None)[0]
            residuals = ts_T - X @ beta
            return residuals.T
        except np.linalg.LinAlgError:
            logger.log("apply_motion_regression_error", error="Singular matrix")
            return time_series

    return time_series


def calculate_connectivity_matrix(
    time_series: np.ndarray,
    method: str = "pearson",
) -> np.ndarray:
    """
    Calculate functional connectivity matrix from time series.

    Args:
        time_series: Time series of shape (n_rois, n_timepoints).
        method: Correlation method ('pearson', 'spearman', etc.).

    Returns:
        Connectivity matrix of shape (n_rois, n_rois).
    """
    logger.log("calculate_connectivity_matrix", method=method, shape=time_series.shape)

    if method == "pearson":
        corr_matrix = np.corrcoef(time_series)
    else:
        from scipy import stats
        if method == "spearman":
            corr_matrix, _ = stats.spearmanr(time_series, axis=1)
        else:
            raise ValueError(f"Unsupported correlation method: {method}")

    # Handle NaNs (e.g., constant time series)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

    return corr_matrix


def calculate_graph_metrics(
    connectivity_matrix: np.ndarray,
    threshold: Optional[float] = None,
    community_detection: bool = True,
    n_modularity: int = 10,
) -> Dict[str, Any]:
    """
    Calculate graph theory metrics from a connectivity matrix.

    Args:
        connectivity_matrix: Square connectivity matrix.
        threshold: Optional threshold to binarize the network.
        community_detection: Whether to detect communities for modularity.
        n_modularity: Number of random restarts for modularity optimization.

    Returns:
        Dictionary containing:
            - 'modularity': Modularity value (scalar)
            - 'participation_coeff': Participation coefficient per node (array)
            - 'within_module_degree': Within-module degree Z-score per node (array)
            - 'global_efficiency': Global efficiency (scalar)
            - 'community_labels': Community assignment per node (array, if detected)
    """
    logger.log(
        "calculate_graph_metrics",
        matrix_shape=connectivity_matrix.shape,
        threshold=threshold,
        community_detection=community_detection,
    )

    n_nodes = connectivity_matrix.shape[0]

    # Create NetworkX graph
    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))

    # Add edges with weights
    upper_tri_indices = np.triu_indices(n_nodes, k=1)
    for i, j in zip(upper_tri_indices[0], upper_tri_indices[1]):
        weight = connectivity_matrix[i, j]
        if threshold is not None:
            if abs(weight) >= threshold:
                G.add_edge(i, j, weight=weight)
        else:
            # Add all edges (weighted graph)
            G.add_edge(i, j, weight=weight)

    # Calculate metrics
    metrics = {}

    # Modularity and communities
    if community_detection:
        try:
            # Louvain community detection
            communities = nx.community.louvain_communities(G, seed=42)
            community_labels = np.zeros(n_nodes, dtype=int)
            for idx, comm in enumerate(communities):
                for node in comm:
                    community_labels[node] = idx

            # Modularity
            modularity = nx.community.modularity(G, communities)
            metrics['modularity'] = float(modularity)
            metrics['community_labels'] = community_labels
        except Exception as e:
            logger.log("community_detection_failed", error=str(e))
            metrics['modularity'] = 0.0
            metrics['community_labels'] = np.zeros(n_nodes, dtype=int)
    else:
        metrics['modularity'] = 0.0
        metrics['community_labels'] = np.zeros(n_nodes, dtype=int)

    # Participation coefficient and within-module degree
    # These require community labels
    try:
        pc, wmd = nx.community.participation_coefficient(
            G,
            community_labels,
            weight='weight',
        )
        metrics['participation_coeff'] = pc
        metrics['within_module_degree'] = wmd
    except Exception as e:
        logger.log("node_metrics_failed", error=str(e))
        metrics['participation_coeff'] = np.zeros(n_nodes)
        metrics['within_module_degree'] = np.zeros(n_nodes)

    # Global efficiency
    try:
        # For weighted graphs, use weighted shortest paths
        global_eff = nx.global_efficiency(G)
        metrics['global_efficiency'] = float(global_eff)
    except Exception as e:
        logger.log("global_efficiency_failed", error=str(e))
        metrics['global_efficiency'] = 0.0

    return metrics


def aggregate_node_metrics(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
) -> None:
    """
    Aggregate node-level metrics into subject-level scalars.

    Reads metrics_raw.csv (containing Modularity, Global Efficiency,
    Participation Coefficient, and Within-Module Degree) and produces
    aggregated_metrics.csv where node-level metrics are averaged across nodes.

    Args:
        input_path: Path to metrics_raw.csv.
        output_path: Path to write aggregated_metrics.csv.
    """
    logger.log("aggregate_node_metrics", input=str(input_path), output=str(output_path))

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read the raw metrics
    df = pd.read_csv(input_path)

    # Identify columns
    # Expected columns: subject_id, modularity, global_efficiency,
    #                   participation_coeff (node-level), within_module_degree (node-level)
    # The raw file might have multiple rows per subject if node-level metrics are stored per node.
    # We need to aggregate participation_coeff and within_module_degree by subject_id.

    # Check if we have node-level data (multiple rows per subject)
    subject_counts = df['subject_id'].value_counts()
    has_node_level = subject_counts.max() > 1

    if has_node_level:
        # Aggregate node-level metrics
        # Participation coefficient and Within-module degree are node-level
        # Modularity and Global Efficiency are already subject-level (should be repeated or single)

        # Group by subject and aggregate
        agg_dict = {}

        # For node-level metrics, take the mean
        node_level_cols = []
        if 'participation_coeff' in df.columns:
            node_level_cols.append('participation_coeff')
            agg_dict['participation_coeff'] = 'mean'
        if 'within_module_degree' in df.columns:
            node_level_cols.append('within_module_degree')
            agg_dict['within_module_degree'] = 'mean'

        # For scalar metrics, take the first value (they should be constant per subject)
        scalar_cols = []
        if 'modularity' in df.columns:
            scalar_cols.append('modularity')
            agg_dict['modularity'] = 'first'
        if 'global_efficiency' in df.columns:
            scalar_cols.append('global_efficiency')
            agg_dict['global_efficiency'] = 'first'

        # Perform aggregation
        if agg_dict:
            aggregated = df.groupby('subject_id').agg(agg_dict).reset_index()
        else:
            # Fallback: just keep unique subjects
            aggregated = df.drop_duplicates(subset=['subject_id'])
    else:
        # Already aggregated, just ensure we have the right columns
        aggregated = df.copy()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    aggregated.to_csv(output_path, index=False)

    logger.log(
        "aggregate_node_metrics_complete",
        input_rows=len(df),
        output_rows=len(aggregated),
        output_path=str(output_path),
    )


def process_subject(
    subject_id: str,
    func_path: Union[str, Path],
    atlas_path: Union[str, Path],
    motion_params_path: Optional[Union[str, Path]] = None,
    threshold: Optional[float] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Process a single subject: extract time series, compute connectivity,
    and calculate graph metrics.

    Args:
        subject_id: Subject identifier.
        func_path: Path to functional fMRI image.
        atlas_path: Path to atlas image.
        motion_params_path: Optional path to motion parameters.
        threshold: Optional threshold for network binarization.
        output_dir: Optional directory to save intermediate results.

    Returns:
        Dictionary containing:
            - 'subject_id': Subject identifier
            - 'time_series_shape': Shape of extracted time series
            - 'connectivity_matrix_shape': Shape of connectivity matrix
            - 'metrics': Graph metrics dictionary
    """
    logger.log(
        "process_subject",
        subject_id=subject_id,
        func_path=str(func_path),
        atlas_path=str(atlas_path),
        threshold=threshold,
    )

    # Extract time series
    time_series = extract_time_series(func_path, atlas_path)

    # Load motion parameters if available
    motion_params = None
    if motion_params_path and Path(motion_params_path).exists():
        motion_params = np.loadtxt(str(motion_params_path))

    # Apply motion regression
    if motion_params is not None:
        time_series = apply_motion_regression(time_series, motion_params)

    # Calculate connectivity matrix
    connectivity_matrix = calculate_connectivity_matrix(time_series)

    # Calculate graph metrics
    metrics = calculate_graph_metrics(connectivity_matrix, threshold=threshold)

    result = {
        'subject_id': subject_id,
        'time_series_shape': time_series.shape,
        'connectivity_matrix_shape': connectivity_matrix.shape,
        'metrics': metrics,
    }

    # Save intermediate results if output_dir is provided
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save connectivity matrix
        np.savetxt(
            output_dir / f"{subject_id}_connectivity.csv",
            connectivity_matrix,
            delimiter=",",
        )

        # Save metrics
        metrics_path = output_dir / f"{subject_id}_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

    return result


def main() -> None:
    """
    Main entry point for metrics computation.
    This function is intended to be called from a script that processes
    all subjects and writes the metrics to a CSV file.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute graph metrics from fMRI data")
    parser.add_argument("--input", type=str, required=True, help="Path to input metrics_raw.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to output aggregated_metrics.csv")
    args = parser.parse_args()

    aggregate_node_metrics(args.input, args.output)
    print(f"Aggregated metrics written to {args.output}")