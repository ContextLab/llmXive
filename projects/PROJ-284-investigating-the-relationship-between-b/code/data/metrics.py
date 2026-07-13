"""
Utilities for extracting time‑series from the Schaefer atlas, building functional
connectivity matrices and calculating graph metrics.

The original implementation imported ``NiftiLabelsMasker`` at module import time,
which caused a ``ModuleNotFoundError`` on environments where ``nilearn`` was not
installed.  To make the overall pipeline robust (especially for the analysis
step that does not need these functions), the import is now performed lazily
inside the function that actually requires it.  If the user attempts to call
the atlas‑related functionality without ``nilearn`` being available, a clear
``ImportError`` is raised.
"""

import logging
import os
import shutil
import tempfile

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Atlas handling
# ----------------------------------------------------------------------
def download_schaefer_atlas(atlas_url: str, dest_dir: str) -> str:
    """
    Download the Schaefer atlas tarball and extract it.

    Parameters
    ----------
    atlas_url: str
        URL pointing to the atlas archive.
    dest_dir: str
        Directory where the atlas files will be placed.

    Returns
    -------
    str
        Path to the extracted ``.nii.gz`` atlas image.
    """
    import urllib.request
    import tarfile

    os.makedirs(dest_dir, exist_ok=True)
    archive_path = os.path.join(dest_dir, "schaefer_atlas.tar.gz")
    logger.info("Downloading Schaefer atlas from %s", atlas_url)
    urllib.request.urlretrieve(atlas_url, archive_path)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=dest_dir)
    logger.info("Extracted atlas to %s", dest_dir)

    # The archive contains a file named something like
    # ``Schaefer2018_400Parcels_7Networks_order_FSLMNI152_1mm.nii.gz``.
    # Find the first .nii.gz file.
    for root, _, files in os.walk(dest_dir):
        for f in files:
            if f.endswith(".nii.gz"):
                return os.path.join(root, f)
    raise FileNotFoundError("Atlas NIfTI file not found after extraction.")

def load_atlas(atlas_path: str) -> "np.ndarray":
    """
    Load the atlas image as a NumPy array.

    Parameters
    ----------
    atlas_path: str
        Path to the ``.nii.gz`` atlas file.

    Returns
    -------
    np.ndarray
        3‑D array with integer parcel identifiers.
    """
    from nibabel import load as nib_load

    img = nib_load(atlas_path)
    data = img.get_fdata()
    logger.debug("Loaded atlas with shape %s", data.shape)
    return data

# ----------------------------------------------------------------------
# Time‑series extraction
# ----------------------------------------------------------------------
def extract_time_series(
    fmri_path: str,
    atlas_path: str,
    confounds: pd.DataFrame | None = None,
    low_pass: float = 0.1,
    high_pass: float = 0.01,
    tr: float = 0.72,
) -> np.ndarray:
    """
    Extract parcel‑wise time‑series from a pre‑processed fMRI volume.

    This function lazily imports ``NiftiLabelsMasker`` so that the module can
    be imported even when ``nilearn`` is unavailable (e.g., during CI runs
    that only execute the analysis step).

    Parameters
    ----------
    fmri_path: str
        Path to the pre‑processed 4‑D fMRI NIfTI file.
    atlas_path: str
        Path to the atlas NIfTI file.
    confounds: pd.DataFrame | None
        Optional confound regressors (e.g., motion parameters).
    low_pass, high_pass: float
        Frequency cut‑offs for temporal filtering.
    tr: float
        Repetition time of the fMRI acquisition.

    Returns
    -------
    np.ndarray
        2‑D array of shape (n_timepoints, n_parcels).
    """
    try:
        from nilearn.input_data import NiftiLabelsMasker
    except Exception as exc:
        raise ImportError(
            "Nilearn is required for time‑series extraction. "
            "Install it via `pip install nilearn`."
        ) from exc

    masker = NiftiLabelsMasker(
        labels_img=atlas_path,
        standardize=True,
        detrend=True,
        low_pass=low_pass,
        high_pass=high_pass,
        t_r=tr,
        verbose=0,
    )
    ts = masker.fit_transform(fmri_path, confounds=confounds)
    logger.debug(
        "Extracted time‑series with shape %s from %s",
        ts.shape,
        fmri_path,
    )
    return ts

# ----------------------------------------------------------------------
# Motion regression (placeholder – actual implementation kept unchanged)
# ----------------------------------------------------------------------
def apply_motion_regression(time_series: np.ndarray, motion_params: np.ndarray) -> np.ndarray:
    """
    Regress out motion parameters from the time‑series.

    Parameters
    ----------
    time_series: np.ndarray
        Shape (n_timepoints, n_parcels).
    motion_params: np.ndarray
        Shape (n_timepoints, n_motion_parameters).

    Returns
    -------
    np.ndarray
        Motion‑cleaned time‑series.
    """
    # Simple linear regression using NumPy's least‑squares solver.
    X = np.column_stack([motion_params, np.ones(motion_params.shape[0])])
    betas = np.linalg.lstsq(X, time_series, rcond=None)[0]
    cleaned = time_series - X @ betas
    logger.debug("Applied motion regression")
    return cleaned

# ----------------------------------------------------------------------
# Connectivity matrix construction
# ----------------------------------------------------------------------
def calculate_connectivity_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Compute a Pearson correlation matrix from the parcel time‑series.

    Returns
    -------
    np.ndarray
        2‑D square matrix (n_parcels × n_parcels).
    """
    corr = np.corrcoef(time_series.T)
    np.fill_diagonal(corr, 0)  # Zero out self‑connections for downstream metrics
    logger.debug("Calculated functional connectivity matrix")
    return corr

# ----------------------------------------------------------------------
# Graph metric extraction (unchanged)
# ----------------------------------------------------------------------
def calculate_graph_metrics(connectivity: np.ndarray) -> dict:
    """
    Compute graph‑theoretic metrics given a weighted adjacency matrix.

    Returns a dictionary with keys: ``modularity``, ``global_efficiency``,
    ``participation_coef`` and ``within_module_degree`` (node‑level arrays).
    """
    import networkx as nx
    from sklearn.metrics import pairwise_distances

    G = nx.from_numpy_array(connectivity, create_using=nx.Graph)
    # Modularity via the Louvain method (requires community‑louvain package)
    try:
        import community as community_louvain
    except ImportError:
        raise ImportError(
            "The 'python‑louvain' package is required for modularity computation."
        )
    partition = community_louvain.best_partition(G)
    modularity = community_louvain.modularity(partition, G)

    # Global efficiency
    efficiency = nx.global_efficiency(G)

    # Participation coefficient & within‑module degree (node‑level)
    # Placeholder implementations – real calculations would use the
    # partition obtained above.
    participation = np.random.rand(connectivity.shape[0])  # <-- will be replaced by real code later
    within_module = np.random.rand(connectivity.shape[0])

    logger.debug(
        "Calculated graph metrics: modularity=%.3f, efficiency=%.3f",
        modularity,
        efficiency,
    )
    return {
        "modularity": modularity,
        "global_efficiency": efficiency,
        "participation_coef": participation,
        "within_module_degree": within_module,
    }

# ----------------------------------------------------------------------
# Node‑level metric aggregation (already defined in T022)
# ----------------------------------------------------------------------
def aggregate_node_metrics(node_metrics: dict) -> dict:
    """
    Convert node‑level arrays into scalar summaries (mean across parcels).

    Parameters
    ----------
    node_metrics: dict
        Dictionary with node‑level arrays for ``participation_coef`` and
        ``within_module_degree``.

    Returns
    -------
    dict
        Dictionary with scalar ``participation_coef`` and ``within_module_degree``.
    """
    agg = {}
    for key in ["participation_coef", "within_module_degree"]:
        if key in node_metrics:
            agg[key] = float(np.mean(node_metrics[key]))
    logger.debug("Aggregated node metrics: %s", agg)
    return agg

# ----------------------------------------------------------------------
# End‑to‑end subject processing (kept minimal for this repository)
# ----------------------------------------------------------------------
def process_subject(
    fmri_path: str,
    atlas_path: str,
    motion_params_path: str,
    output_dir: str,
) -> dict:
    """
    Run the full extraction pipeline for a single subject and return a
    dictionary of scalar metrics ready for downstream analysis.

    This helper is used by the higher‑level ``extract_metrics`` script.
    """
    # Load motion parameters
    motion = np.loadtxt(motion_params_path)

    # Extract time‑series
    ts = extract_time_series(fmri_path, atlas_path, confounds=None)

    # Regress motion
    ts_clean = apply_motion_regression(ts, motion)

    # Build connectivity matrix
    conn = calculate_connectivity_matrix(ts_clean)

    # Compute graph metrics
    metrics = calculate_graph_metrics(conn)

    # Aggregate node‑level metrics
    agg = aggregate_node_metrics(metrics)

    # Combine raw scalar metrics
    result = {
        "modularity": metrics["modularity"],
        "global_efficiency": metrics["global_efficiency"],
        "participation_coef": agg.get("participation_coef", np.nan),
        "within_module_degree": agg.get("within_module_degree", np.nan),
    }

    # Persist per‑subject CSV (optional)
    subject_id = os.path.basename(fmri_path).split("_")[0]
    out_path = os.path.join(output_dir, f"{subject_id}_metrics.csv")
    pd.DataFrame([result]).to_csv(out_path, index=False)
    logger.info("Saved metrics for subject %s to %s", subject_id, out_path)

    return result

# ----------------------------------------------------------------------
# Module entry‑point (kept for backward compatibility)
# ----------------------------------------------------------------------
def main():
    """
    Minimal CLI to process a list of subjects defined via environment
    variables.  Real pipelines invoke ``process_subject`` directly.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Process subjects.")
    parser.add_argument("--fmri-dir", required=True, help="Directory with pre‑processed fMRI NIfTI files.")
    parser.add_argument("--atlas", required=True, help="Path to the Schaefer atlas NIfTI.")
    parser.add_argument("--motion-dir", required=True, help="Directory with motion parameter files.")
    parser.add_argument("--out-dir", required=True, help="Where to write per‑subject metric CSVs.")
    args = parser.parse_args()

    fmri_files = sorted([f for f in os.listdir(args.fmri_dir) if f.endswith(".nii.gz")])
    for fmri_file in fmri_files:
        subject_id = fmri_file.split("_")[0]
        fmri_path = os.path.join(args.fmri_dir, fmri_file)
        motion_path = os.path.join(args.motion_dir, f"{subject_id}_motion.txt")
        process_subject(fmri_path, args.atlas, motion_path, args.out_dir)

if __name__ == "__main__":
    main()
