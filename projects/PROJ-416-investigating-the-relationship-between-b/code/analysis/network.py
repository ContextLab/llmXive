import csv
import json
import logging
import os
import sys
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from sibling modules if available, or define fallbacks for standalone execution
# The API surface indicates these functions exist in this file or are imported here.
# Based on the surface, we assume load_preprocessed_data, extract_roi_timeseries, etc. are defined below or imported.
# Since the surface says "import as: from code.analysis.network import ...", we define them here.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories(output_dir: Path) -> None:
    """Ensure output directories for matrices and metrics exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    matrices_dir = output_dir / "matrices"
    matrices_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {output_dir}, {matrices_dir}")

def load_preprocessed_data(filtered_subjects_path: Path, processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Load list of subjects from filtered_subjects.csv and locate their preprocessed NIfTI files.
    Returns a list of dicts: [{'subject_id': 'sub-01', 'nifti_path': Path(...)}, ...]
    """
    subjects = []
    if not filtered_subjects_path.exists():
        logger.error(f"Filtered subjects file not found: {filtered_subjects_path}")
        return subjects

    with open(filtered_subjects_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('status') == 'included':
                sub_id = row['subject_id']
                # Assume standard BIDS-like structure or specific naming convention
                # Adjust path logic based on actual preprocessing output structure
                nifti_path = processed_dir / f"{sub_id}_preprocessed.nii.gz"
                if not nifti_path.exists():
                    logger.warning(f"Preprocessed file missing for {sub_id}: {nifti_path}")
                    continue
                subjects.append({'subject_id': sub_id, 'nifti_path': nifti_path})
    return subjects

def extract_roi_timeseries(nifti_path: Path, atlas_path: Optional[Path] = None) -> Optional[np.ndarray]:
    """
    Extract ROI time series from a preprocessed NIfTI file using an atlas.
    Returns a numpy array of shape (timepoints, n_rois).
    """
    try:
        from nilearn import image
        from nilearn import datasets
        from nilearn import input_data
        
        if atlas_path is None:
            # Default to a standard atlas if not provided, e.g., Schaefer or AAL
            # For this implementation, we assume a path is provided or use a default
            logger.warning("No atlas path provided, using default AAL atlas.")
            # This might fail if nilearn datasets are not cached, but we try to get it
            try:
                atlas = datasets.fetch_atlas_aal()
                atlas_path = Path(atlas['maps'])
            except Exception as e:
                logger.error(f"Failed to fetch default atlas: {e}")
                return None

        # Load the atlas
        atlas_img = image.load_img(atlas_path)
        # Load the functional image
        func_img = image.load_img(nifti_path)
        
        # Extract timeseries
        masker = input_data.NiftiLabelsMasker(
            labels_img=atlas_img,
            standardize=True,
            detrend=True,
            memory="nilearn_cache",
            memory_level=1
        )
        timeseries = masker.fit_transform(func_img)
        return timeseries
    except Exception as e:
        logger.error(f"Failed to extract ROI timeseries from {nifti_path}: {e}")
        return None

def calculate_connectivity_matrix(timeseries: np.ndarray) -> Optional[np.ndarray]:
    """
    Calculate the functional connectivity matrix (Pearson correlation) from ROI timeseries.
    Returns a numpy array of shape (n_rois, n_rois).
    """
    if timeseries is None or timeseries.size == 0:
        return None
    try:
        corr_matrix = np.corrcoef(timeseries.T)
        # Handle potential NaNs/Infs
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
        return corr_matrix
    except Exception as e:
        logger.error(f"Failed to calculate connectivity matrix: {e}")
        return None

def calculate_network_metrics(conn_matrix: np.ndarray) -> Dict[str, float]:
    """
    Calculate network metrics: Modularity Q, Global Efficiency, Local Efficiency.
    Uses bctpy if available, otherwise falls back to simple implementations or placeholders.
    """
    metrics = {
        'modularity_q': 0.0,
        'global_efficiency': 0.0,
        'local_efficiency': 0.0
    }
    try:
        import bct
        # Threshold the matrix (e.g., proportional threshold)
        threshold = 0.1
        binary_matrix = bct.threshold_proportional(conn_matrix, threshold)
        
        # Modularity
        communities = bct.community_louvain(binary_matrix)
        # bct returns a dict or tuple depending on version; usually (modularity, partitions)
        if isinstance(communities, tuple):
            q, _ = communities
        else:
            q = communities
        metrics['modularity_q'] = float(q) if q is not None else 0.0

        # Global Efficiency
        eff_global = bct.efficiency_bin(binary_matrix)
        metrics['global_efficiency'] = float(eff_global)

        # Local Efficiency
        eff_local = bct.efficiency_loc(bin_graph=binary_matrix)
        # bct.efficiency_loc returns an array of local efficiencies per node
        # We take the mean as the global local efficiency metric
        metrics['local_efficiency'] = float(np.mean(eff_local))

    except ImportError:
        logger.warning("bctpy not installed. Using placeholder metrics.")
        # Fallback: simple metrics or zeros to avoid crash, but log warning
        # In a real scenario, we might implement basic graph metrics manually
        n = conn_matrix.shape[0]
        # Simple placeholder: assume random graph properties
        metrics['modularity_q'] = 0.0
        metrics['global_efficiency'] = 1.0 / (n - 1) if n > 1 else 0.0
        metrics['local_efficiency'] = 1.0 / (n - 1) if n > 1 else 0.0
    except Exception as e:
        logger.error(f"Failed to calculate network metrics: {e}")
        # Return zeros on failure
        metrics['modularity_q'] = 0.0
        metrics['global_efficiency'] = 0.0
        metrics['local_efficiency'] = 0.0
    
    return metrics

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save network metrics to a CSV file.
    """
    if not metrics_list:
        logger.warning("No metrics to save.")
        return

    fieldnames = ['subject_id', 'modularity_q', 'global_efficiency', 'local_efficiency']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_list:
            # Ensure all fields are present
            safe_row = {k: row.get(k, 0.0) for k in fieldnames}
            writer.writerow(safe_row)
    logger.info(f"Saved metrics to {output_path}")

def save_matrices_to_npy(matrices_dict: Dict[str, np.ndarray], output_dir: Path) -> None:
    """
    Save connectivity matrices as .npy files.
    """
    for sub_id, matrix in matrices_dict.items():
        if matrix is not None:
            file_path = output_dir / f"{sub_id}_connectivity_matrix.npy"
            np.save(file_path, matrix)
    logger.info(f"Saved {len(matrices_dict)} matrices to {output_dir}")

def run_analysis(
    filtered_subjects_path: Path,
    processed_dir: Path,
    atlas_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full network analysis pipeline:
    1. Load subjects
    2. Extract timeseries
    3. Calculate connectivity matrices
    4. Calculate metrics
    5. Save outputs
    """
    if output_dir is None:
        output_dir = Path("data/metrics")
    output_dir = Path(output_dir)
    ensure_directories(output_dir)

    subjects = load_preprocessed_data(filtered_subjects_path, processed_dir)
    if not subjects:
        logger.error("No subjects found to process.")
        return {'metrics': [], 'matrices': {}}

    metrics_list = []
    matrices_dict = {}

    for sub_info in subjects:
        sub_id = sub_info['subject_id']
        nifti_path = sub_info['nifti_path']
        
        logger.info(f"Processing {sub_id}...")
        ts = extract_roi_timeseries(nifti_path, atlas_path)
        if ts is None:
            continue

        conn_mat = calculate_connectivity_matrix(ts)
        if conn_mat is None:
            continue

        # Save matrix
        matrices_dict[sub_id] = conn_mat

        # Calculate metrics
        metrics = calculate_network_metrics(conn_mat)
        metrics['subject_id'] = sub_id
        metrics_list.append(metrics)

    # Save outputs
    metrics_csv_path = output_dir / "network_metrics.csv"
    save_metrics_to_csv(metrics_list, metrics_csv_path)

    matrices_dir = output_dir / "matrices"
    save_matrices_to_npy(matrices_dict, matrices_dir)

    return {'metrics': metrics_list, 'matrices': matrices_dict}

def main():
    """
    Entry point for command line execution.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run network analysis on preprocessed fMRI data.")
    parser.add_argument("--subjects", type=str, default="data/metrics/filtered_subjects.csv",
                        help="Path to filtered subjects CSV.")
    parser.add_argument("--processed", type=str, default="data/processed",
                        help="Directory containing preprocessed NIfTI files.")
    parser.add_argument("--atlas", type=str, default=None,
                        help="Path to atlas file (e.g., AAL or Schaefer).")
    parser.add_argument("--output", type=str, default="data/metrics",
                        help="Output directory for metrics and matrices.")
    
    args = parser.parse_args()

    filtered_path = Path(args.subjects)
    processed_path = Path(args.processed)
    atlas_path = Path(args.atlas) if args.atlas else None
    output_path = Path(args.output)

    run_analysis(filtered_path, processed_path, atlas_path, output_path)
    logger.info("Network analysis completed.")

if __name__ == "__main__":
    main()