import json
import pathlib

import pytest

from analysis.connectivity import (
    fisher_z_transform,
    compute_pearson_correlation_chunked,
    process_subject_connectivity,
)
from analysis.atlas import load_atlas, TARGET_NETWORKS
from analysis.network_metrics import compute_network_metrics

# Helper to create a tiny synthetic NIfTI for testing
def _create_dummy_nifti(tmp_path, subject_id):
    import nibabel as nib
    import numpy as np
    shape = (5, 5, 5, 10)  # small volume, 10 time points
    data = np.random.randn(*shape).astype(np.float32)
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    out_path = tmp_path / "mock_nifti" / f"{subject_id}.nii.gz"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(out_path))
    return out_path

def test_fisher_z_transform_scalar():
    r = 0.5
    z = fisher_z_transform(r)
    assert isinstance(z, float) or isinstance(z, np.ndarray)

def test_compute_pearson_correlation_chunked():
    ts = np.random.randn(20, 8)
    corr = compute_pearson_correlation_chunked(ts, chunk_size=4, memory_limit_gb=1.0)
    assert corr.shape == (8, 8)
    # Symmetry and unit diagonal
    np.testing.assert_allclose(corr, corr.T, atol=1e-7)
    np.testing.assert_allclose(np.diag(corr), 1.0, atol=1e-7)

def test_end_to_end_connectivity_and_network_metrics(tmp_path):
    # Create a minimal atlas CSV with three ROIs belonging to each target network
    atlas_csv = tmp_path / "schaefer_200.csv"
    rows = [
        {"roi_id": 0, "x": 1, "y": 1, "z": 1, "network": "auditory"},
        {"roi_id": 1, "x": 2, "y": 2, "z": 2, "network": "motor"},
        {"roi_id": 2, "x": 3, "y": 3, "z": 3, "network": "executive"},
    ]
    import pandas as pd

    pd.DataFrame(rows).to_csv(atlas_csv, index=False)

    atlas_df = load_atlas(atlas_csv)

    subject_id = "SUBJ001"
    nifti_path = _create_dummy_nifti(tmp_path, subject_id)

    conn = process_subject_connectivity(
        subject_id=subject_id,
        nifti_path=nifti_path,
        atlas_df=atlas_df,
        chunk_size=2,
    )

    # Verify matrix properties
    z = conn.matrix
    assert z.shape == (3, 3)
    np.testing.assert_allclose(z, z.T, atol=1e-7)
    np.testing.assert_allclose(np.diag(z), 0.0, atol=1e-7)  # Fisher‑z of 1.0 correlation is 0

    # Network metrics – each network has a single ROI, so intra‑network mean is NaN
    metrics = compute_network_metrics(z, atlas_df, target_networks=TARGET_NETWORKS)
    for net in TARGET_NETWORKS:
        assert net in metrics
        # Single‑ROI networks return NaN per implementation
        assert metrics[net] != metrics[net]  # NaN check