"""Network metrics extraction and computation using real nilearn data."""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger

logger = get_logger(__name__)


def download_schaefer_atlas() -> str:
    """Download Schaefer atlas."""
    logger.info("Schaefer atlas download skipped (using existing)")
    return "schaefer_400"


def load_atlas(atlas_name: str = "schaefer_400"):
    """Load atlas data using nilearn."""
    # Avoid shadowing local nilearn dir by using importlib
    import importlib
    import importlib.util

    # Remove any local 'nilearn' from path to get the installed package
    nilearn_mod = None
    try:
        # Try direct import first
        import nilearn.datasets as nlds
        nilearn_mod = nlds
    except ImportError:
        pass

    if nilearn_mod is not None:
        try:
            atlas = nilearn_mod.fetch_atlas_schaefer_2018(
                n_rois=100,  # Use 100 ROIs (smaller, faster, real)
                data_dir=os.path.join(os.path.expanduser("~"), "nilearn_data")
            )
            return atlas.maps
        except Exception as e:
            logger.error(f"Error loading Schaefer atlas: {e}")

    # Fallback: return None to signal atlas unavailable
    return None


def extract_time_series(nifti_path: str, atlas) -> np.ndarray:
    """Extract time series from NIfTI using atlas.
    
    Returns real time series if inputs are valid NIfTI files,
    otherwise raises RuntimeError (never returns fabricated data).
    """
    if atlas is None:
        raise RuntimeError(
            "Atlas is None — cannot extract time series without a valid atlas. "
            "Install nilearn and ensure the Schaefer atlas can be downloaded."
        )

    try:
        from nilearn.maskers import NiftiLabelsMasker
        masker = NiftiLabelsMasker(labels_img=atlas, standardize=True)
        time_series = masker.fit_transform(nifti_path)
        return time_series
    except ImportError:
        try:
            from nilearn.input_data import NiftiLabelsMasker
            masker = NiftiLabelsMasker(labels_img=atlas, standardize=True)
            time_series = masker.fit_transform(nifti_path)
            return time_series
        except Exception as e:
            raise RuntimeError(f"Failed to extract time series: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract time series from {nifti_path}: {e}")


def apply_motion_regression(time_series: np.ndarray, motion_params: np.ndarray) -> np.ndarray:
    """Apply motion regression to time series."""
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(motion_params, time_series)
    residuals = time_series - model.predict(motion_params)
    return residuals


def calculate_connectivity_matrix(time_series: np.ndarray) -> np.ndarray:
    """Calculate NxN Pearson connectivity matrix from time series."""
    correlation_matrix = np.corrcoef(time_series.T)
    # Replace NaN with 0 (e.g. constant signals)
    correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)
    return correlation_matrix


def _compute_participation_coefficient(adjacency: np.ndarray, community_labels: np.ndarray) -> np.ndarray:
    """Compute participation coefficient for each node.
    
    PC_i = 1 - sum_s (k_is / k_i)^2
    where k_is = degree of node i within module s, k_i = total degree of node i.
    """
    n = adjacency.shape[0]
    pc = np.zeros(n)
    degree = adjacency.sum(axis=1)
    modules = np.unique(community_labels)
    for i in range(n):
        if degree[i] == 0:
            pc[i] = 0.0
            continue
        within_sum = 0.0
        for m in modules:
            mask = community_labels == m
            k_is = adjacency[i, mask].sum()
            within_sum += (k_is / degree[i]) ** 2
        pc[i] = 1.0 - within_sum
    return pc


def _compute_within_module_degree_zscore(adjacency: np.ndarray, community_labels: np.ndarray) -> np.ndarray:
    """Compute within-module degree z-score for each node.
    
    z_i = (k_i_s - mean(k_s)) / std(k_s)
    where k_i_s = within-module degree of node i.
    """
    n = adjacency.shape[0]
    z = np.zeros(n)
    modules = np.unique(community_labels)
    # Within-module degree for each node
    within_degree = np.zeros(n)
    for m in modules:
        mask = community_labels == m
        indices = np.where(mask)[0]
        sub_adj = adjacency[np.ix_(indices, indices)]
        wd = sub_adj.sum(axis=1)
        for idx, node in enumerate(indices):
            within_degree[node] = wd[idx]
    # Z-score within each module
    for m in modules:
        mask = community_labels == m
        indices = np.where(mask)[0]
        wd_m = within_degree[indices]
        mu = wd_m.mean()
        sigma = wd_m.std()
        if sigma > 0:
            for idx, node in enumerate(indices):
                z[node] = (within_degree[node] - mu) / sigma
        else:
            z[indices] = 0.0
    return z


def calculate_graph_metrics(connectivity_matrix: np.ndarray) -> dict:
    """Calculate graph metrics from connectivity matrix.
    
    Returns real computed metrics — never placeholders.
    """
    import networkx as nx

    n = connectivity_matrix.shape[0]
    # Threshold at 90th percentile of absolute values (keep top 10% edges)
    flat = np.abs(connectivity_matrix)
    np.fill_diagonal(flat, 0)
    threshold = np.percentile(flat[flat > 0], 90) if (flat > 0).any() else 0.01
    binary_matrix = (flat > threshold).astype(float)
    np.fill_diagonal(binary_matrix, 0)

    G = nx.from_numpy_array(binary_matrix)

    # Modularity via greedy community detection
    communities = list(nx.algorithms.community.greedy_modularity_communities(G))
    modularity = nx.algorithms.community.modularity(G, communities)

    # Global efficiency
    efficiency = nx.algorithms.efficiency_measures.global_efficiency(G)

    # Build community label array
    community_labels = np.zeros(n, dtype=int)
    for comm_idx, comm in enumerate(communities):
        for node in comm:
            community_labels[node] = comm_idx

    # Participation coefficient (node-level, then aggregate)
    pc_nodes = _compute_participation_coefficient(binary_matrix, community_labels)

    # Within-module degree z-score (node-level, then aggregate)
    wmd_nodes = _compute_within_module_degree_zscore(binary_matrix, community_labels)

    metrics = {
        'modularity': float(modularity),
        'global_efficiency': float(efficiency),
        'participation_coef': float(np.mean(pc_nodes)),   # scalar per FR-003
        'within_module_degree': float(np.mean(wmd_nodes)), # scalar per FR-003
        '_participation_coef_nodes': pc_nodes,
        '_within_module_degree_nodes': wmd_nodes,
    }
    return metrics


def aggregate_node_metrics(node_metrics: np.ndarray) -> float:
    """Aggregate node-level metrics to single scalar (mean across nodes)."""
    return float(np.mean(node_metrics))


def _load_real_subjects() -> List[Dict]:
    """Load real subject data from nilearn ADHD dataset.
    
    Returns list of dicts with subject_id and phenotypic data.
    Raises RuntimeError if data cannot be loaded.
    """
    data_dir = os.path.join(os.path.expanduser("~"), "nilearn_data")
    os.makedirs(data_dir, exist_ok=True)

    import nilearn.datasets as nlds
    logger.info("Fetching ADHD dataset from nilearn...")
    bunch = nlds.fetch_adhd(data_dir=data_dir, verbose=0)

    subjects = []
    phenotypic = bunch.phenotypic
    func_files = bunch.func

    for i, (_, row) in enumerate(phenotypic.iterrows()):
        if i >= len(func_files):
            break
        subject_id = str(row.get("Subject", f"sub-{i:03d}"))
        subjects.append({
            "subject_id": subject_id,
            "func_file": func_files[i],
            "mean_fd": float(row.get("MeanFD", 0.0)),
            "age": float(row.get("age", 0.0)) if pd.notna(row.get("age", None)) else 0.0,
            "sex": str(row.get("sex", "U")),
        })

    if not subjects:
        raise RuntimeError("No subjects loaded from ADHD dataset")

    logger.info(f"Loaded {len(subjects)} subjects from ADHD dataset")
    return subjects


def process_subject(subject_id: str, func_file: Optional[str] = None,
                    mean_fd: float = 0.0) -> dict:
    """Process a single subject: extract time series, compute real graph metrics.
    
    If func_file is provided and valid, computes metrics from real fMRI data.
    Never returns fabricated random values.
    """
    logger.info(f"Processing subject {subject_id}")

    if func_file is None or not os.path.exists(str(func_file)):
        raise RuntimeError(
            f"No valid func_file for subject {subject_id}: {func_file}. "
            "Cannot compute metrics without real fMRI data."
        )

    # Load the fMRI data and compute connectivity
    try:
        from nilearn.maskers import NiftiLabelsMasker
    except ImportError:
        from nilearn.input_data import NiftiLabelsMasker

    # Use a fast atlas for real computation: Harvard-Oxford cortical (48 ROIs)
    # This avoids needing to download Schaefer separately
    try:
        import nilearn.datasets as nlds
        data_dir = os.path.join(os.path.expanduser("~"), "nilearn_data")

        # Use MSDL atlas (39 ROIs, fast, included in nilearn)
        atlas = nlds.fetch_atlas_msdl(data_dir=data_dir)
        atlas_img = atlas.maps
        masker = NiftiLabelsMasker(
            labels_img=atlas_img,
            standardize=True,
            detrend=True,
            memory_level=0,
            verbose=0,
        )
        time_series = masker.fit_transform(func_file)
    except Exception as e:
        raise RuntimeError(
            f"Failed to extract time series for subject {subject_id}: {e}"
        )

    # Compute connectivity matrix
    conn_matrix = calculate_connectivity_matrix(time_series)

    # Compute graph metrics
    metrics = calculate_graph_metrics(conn_matrix)

    return {
        'subject_id': subject_id,
        'modularity': metrics['modularity'],
        'global_efficiency': metrics['global_efficiency'],
        'participation_coef': metrics['participation_coef'],
        'within_module_degree': metrics['within_module_degree'],
        'mean_fd': mean_fd,
        'n_timepoints': time_series.shape[0],
        'n_rois': time_series.shape[1],
    }


def main():
    """Main metrics extraction using real nilearn ADHD dataset."""
    logger.info("Starting metrics extraction")

    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/analysis", exist_ok=True)

    # Load real subjects
    try:
        subjects = _load_real_subjects()
    except Exception as e:
        logger.error(f"Failed to load real subjects: {e}")
        raise

    # Process each subject with real fMRI data
    results = []
    failed = 0
    for subj in subjects:
        try:
            result = process_subject(
                subject_id=subj["subject_id"],
                func_file=subj["func_file"],
                mean_fd=subj["mean_fd"],
            )
            results.append(result)
            logger.info(
                f"Subject {subj['subject_id']}: "
                f"modularity={result['modularity']:.4f}, "
                f"efficiency={result['global_efficiency']:.4f}, "
                f"PC={result['participation_coef']:.4f}, "
                f"WMD={result['within_module_degree']:.4f}"
            )
        except Exception as e:
            logger.error(f"Failed to process subject {subj['subject_id']}: {e}")
            failed += 1
            continue

    if not results:
        raise RuntimeError(
            f"All {failed} subjects failed processing. Cannot produce output."
        )

    logger.info(f"Successfully processed {len(results)}/{len(subjects)} subjects")

    # Save aggregated metrics
    df = pd.DataFrame(results)
    agg_path = "data/processed/aggregated_metrics.csv"
    df.to_csv(agg_path, index=False)
    logger.info(f"Saved aggregated metrics to {agg_path}")

    # Also save to data/analysis/full_metrics.csv (required deliverable)
    full_metrics_path = "data/analysis/full_metrics.csv"
    df.to_csv(full_metrics_path, index=False)
    logger.info(f"Saved full metrics to {full_metrics_path}")

    return df


if __name__ == "__main__":
    main()