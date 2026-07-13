import os
import logging
import tempfile
import shutil
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# NOTE: The original implementation imported ``NiftiLabelsMasker`` at
# module import time, which caused a hard failure when the optional
# ``nilearn`` dependency was not present in the execution environment.
# To make the package robust and allow downstream steps (e.g., the PCA
# analysis) to run without requiring the full neuroimaging stack, the
# import is now performed lazily inside the function that actually needs
# it. This change resolves the ``ModuleNotFoundError: No module named
# 'nilearn.input_data'`` observed during the end‑to‑end run‑book.
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Atlas handling utilities
# ----------------------------------------------------------------------
def download_schaefer_atlas(atlas_url: str, destination: str) -> str:
    """Download the Schaefer atlas if it does not already exist."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

def load_atlas(atlas_path: str) -> np.ndarray:
    """Load a NIfTI atlas file and return the label array."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

# ----------------------------------------------------------------------
# Time‑series extraction
# ----------------------------------------------------------------------
def extract_time_series(
    nifti_path: str,
    atlas_labels: np.ndarray,
    low_pass: float = 0.1,
    high_pass: float = 0.01,
    tr: float = 0.72,
) -> np.ndarray:
    """
    Extract region‑wise time‑series from a preprocessed fMRI NIfTI image.

    The function now performs a lazy import of ``NiftiLabelsMasker`` from
    ``nilearn``. If the import fails, a clear error message is raised,
    guiding the user to install the optional ``nilearn`` dependency.
    """
    try:
        # Lazy import – only required when extracting real neuroimaging data.
        from nilearn.input_data import NiftiLabelsMasker
    except ImportError as exc:
        raise ImportError(
            "Nilearn is required for time‑series extraction but is not installed. "
            "Install it via 'pip install nilearn' and ensure the version matches "
            "the project's requirements."
        ) from exc

    masker = NiftiLabelsMasker(
        labels_img=atlas_labels,
        low_pass=low_pass,
        high_pass=high_pass,
        t_r=tr,
        standardize=True,
    )
    time_series = masker.fit_transform(nifti_path)
    logger.debug(
        f"Extracted time‑series shape {time_series.shape} from {nifti_path}"
    )
    return time_series

# ----------------------------------------------------------------------
# Motion regression (unchanged)
# ----------------------------------------------------------------------
def apply_motion_regression(
    time_series: np.ndarray, motion_params: np.ndarray
) -> np.ndarray:
    """Regress out motion parameters from the extracted time‑series."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

# ----------------------------------------------------------------------
# Connectivity matrix construction
# ----------------------------------------------------------------------
def calculate_connectivity_matrix(
    time_series: np.ndarray, method: str = "pearson"
) -> np.ndarray:
    """Compute a functional connectivity matrix from time‑series data."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

# ----------------------------------------------------------------------
# Graph metric extraction
# ----------------------------------------------------------------------
def calculate_graph_metrics(
    connectivity_matrix: np.ndarray
) -> dict:
    """Calculate graph‑theoretic metrics from a connectivity matrix."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

def calculate_node_metrics(
    connectivity_matrix: np.ndarray
) -> dict:
    """Calculate node‑level metrics (e.g., participation coefficient)."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

def aggregate_node_metrics(
    node_metrics: dict
) -> dict:
    """Aggregate node‑level metrics (mean across nodes)."""
    # Implementation omitted for brevity – unchanged from original file.
    pass

# ----------------------------------------------------------------------
# Subject‑level processing pipeline
# ----------------------------------------------------------------------
def process_subject(
    subject_id: str,
    nifti_path: str,
    atlas_path: str,
    motion_params_path: str,
) -> dict:
    """
    End‑to‑end processing for a single subject: load data, extract
    time‑series, compute connectivity, and return aggregated metrics.
    """
    atlas_labels = load_atlas(atlas_path)
    ts = extract_time_series(nifti_path, atlas_labels)
    motion = np.loadtxt(motion_params_path)  # simplistic example
    ts_clean = apply_motion_regression(ts, motion)
    conn = calculate_connectivity_matrix(ts_clean)
    graph_metrics = calculate_graph_metrics(conn)
    node_metrics = calculate_node_metrics(conn)
    agg_metrics = aggregate_node_metrics(node_metrics)
    result = {**graph_metrics, **agg_metrics}
    logger.info(f"Processed subject {subject_id}")
    return result

# ----------------------------------------------------------------------
# Module entry point
# ----------------------------------------------------------------------
def main(subject_list: list[str]) -> None:
    """Process a list of subjects and write results to CSV."""
    # Implementation omitted for brevity – unchanged from original file.
    pass