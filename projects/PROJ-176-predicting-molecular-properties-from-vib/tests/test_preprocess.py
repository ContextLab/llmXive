"""
Minimal test suite for the preprocessing step (T005).
The test checks that the NPZ file is created, that its shape matches the
specification and that the spectra are properly normalized.
"""

import pathlib
import numpy as np
import pytest

from data.preprocess import main as preprocess_main
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def run_preprocess(tmp_path_factory):
    """Run the preprocessing script once for the whole test module."""
    # Ensure a clean environment
    out_path = paths.data("processed", "aligned_dataset.npz")
    if out_path.is_file():
        out_path.unlink()
    # Execute the main function (which writes the NPZ)
    preprocess_main()
    return out_path

def test_npz_exists(run_preprocess):
    """The expected .npz file must exist after preprocessing."""
    assert run_preprocess.is_file()

def test_npz_contents(run_preprocess):
    """Validate the content shapes and unit‑area normalization."""
    data = np.load(run_preprocess)
    spectra = data["spectra"]
    dipole = data["dipole"]
    polar = data["polarizability"]
    gap = data["gap"]
    inchikeys = data["InChIKeys"]

    # Basic shape checks
    assert spectra.ndim == 3  # (N, 1, 3601)
    assert spectra.shape[1:] == (1, 3601)
    assert dipole.shape[0] == spectra.shape[0]
    assert polar.shape[0] == spectra.shape[0]
    assert gap.shape[0] == spectra.shape[0]
    assert inchikeys.shape[0] == spectra.shape[0]

    # Unit‑area normalization (tolerance 1e-6 as per spec)
    area = spectra.sum(axis=2)  # sum over the wavenumber dimension
    assert np.allclose(area, 1.0, atol=1e-6)

def test_file_size_limit(run_preprocess):
    """The NPZ file must be smaller than 1 GB."""
    size_bytes = run_preprocess.stat().st_size
    assert size_bytes < 1_000_000_000  # 1 GB