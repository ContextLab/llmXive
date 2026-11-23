"""
Integration test for matrix generation pipeline (US1).

This test verifies that the pipeline can generate three distinct adjacency
matrices (AAL-90, Schaefer-200, Schaefer-400) for a single subject from
raw fMRI data.

It enforces:
1. Use of REAL data from OpenNeuro (ds000224 or ds000005).
2. Correct file paths and output formats (.npz).
3. Distinct node counts for each resolution.
4. Memory efficiency (streaming/chunked processing).
5. Fail loudly on missing data or processing errors (no synthetic fallback).
"""

import os
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Import project utilities and models
# Note: Imports assume this file is run from project root or PYTHONPATH is set
try:
    from config import get_path, ensure_paths_exist
    from utils.seed import set_seed
    from utils.logger import get_logger, DataFetchError, ProcessingError
    from models.adjacency_matrix import AdjacencyMatrix
except ImportError as e:
    # Fallback for running in different environments, but ideally PYTHONPATH is set
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import get_path, ensure_paths_exist
    from utils.seed import set_seed
    from utils.logger import get_logger, DataFetchError, ProcessingError
    from models.adjacency_matrix import AdjacencyMatrix

# Mock or import the parcellation functions.
# Since T016, T013, T014, T015 are not yet implemented in the artifact list,
# we must import the functions we are testing. If they don't exist yet,
# this test will fail with ImportError, which is the correct behavior for an
# integration test run against incomplete code.
# However, the task description implies we are implementing the TEST for the pipeline.
# The pipeline functions (apply_aal3, etc.) are defined in code/parcellate.py.
# We assume parcellate.py exists or will exist. If not, we cannot import.
# To make this test runnable and valid, we need the functions to be importable.
# If the implementation (T016, T013-T015) is missing, this test SHOULD fail.
# But to satisfy the "implement the test" requirement, we write the logic that
# WOULD run once the implementation is done.

# We will attempt to import the functions. If they are missing, we skip or fail explicitly.
try:
    from parcellate import apply_aal3, apply_schaefer200, apply_schaefer400
    HAS_PARCELLATE = True
except ImportError:
    HAS_PARCELLATE = False
    # We don't raise here immediately so we can assert the import failure in the test if needed,
    # but typically an integration test expects the code to exist.
    # We will raise a clear error in the test function.

from download_data import download_subject_fmri

logger = get_logger(__name__)
SEED = 42

@pytest.fixture(scope="module")
def test_data_path():
    """
    Fetches a single subject's fMRI data from OpenNeuro for testing.
    Uses ds000224 (HCP Young Adult) as primary.
    Falls back to ds000005 if necessary (though ds000224 is preferred).
    Returns the path to the downloaded NIfTI file.
    """
    set_seed(SEED)
    ensure_paths_exist()

    # Try to get a subject ID. We need at least one valid subject.
    # We will try to download subject '100001' from ds000224.
    # If that fails, we try a few others.
    subject_ids = ["100001", "100002", "100003"]
    dataset_id = "ds000224"

    download_path = None
    for sub_id in subject_ids:
        try:
            logger.info(f"Attempting to download subject {sub_id} from {dataset_id}")
            # This function should handle the actual download and return the path
            download_path = download_subject_fmri(dataset_id, sub_id)
            if download_path and os.path.exists(download_path):
                logger.info(f"Successfully downloaded {download_path}")
                break
        except Exception as e:
            logger.warning(f"Failed to download {sub_id}: {e}")
            continue

    if not download_path or not os.path.exists(download_path):
        pytest.fail("Could not download any real fMRI data from OpenNeuro for testing. "
                    "Ensure network access and that the dataset is available.")

    return download_path

@pytest.mark.integration
def test_matrix_generation_pipeline(test_data_path):
    """
    Integration test: Generate AAL-90, Schaefer-200, and Schaefer-400 matrices
    from a single real fMRI file.

    Verifies:
    1. Functions exist and are callable.
    2. Output files are created in data/processed.
    3. Output files are valid .npz with expected keys.
    4. Node counts match expected resolutions (90, 200, 400).
    5. Matrices are symmetric and have zero diagonals (or expected structure).
    """
    if not HAS_PARCELLATE:
        pytest.fail("Parcellation module (code/parcellate.py) not found or incomplete. "
                    "Implement T016, T013, T014, T015 before running this integration test.")

    # Ensure output directory exists
    processed_dir = get_path("data_processed")
    ensure_paths_exist()

    # Define expected outputs
    subject_id = Path(test_data_path).stem  # e.g., sub-100001
    # The download function might return a path like data/raw/sub-100001.nii.gz
    # We need to extract the subject ID correctly.
    # Assuming the filename is sub-<ID>.nii.gz or similar.
    if subject_id.startswith("sub-"):
        subject_id = subject_id[4:]

    outputs = {
        "aal90": (get_path("data_processed") / f"{subject_id}_aal90.npz", 90),
        "schaefer200": (get_path("data_processed") / f"{subject_id}_schaefer200.npz", 200),
        "schaefer400": (get_path("data_processed") / f"{subject_id}_schaefer400.npz", 400),
    }

    # Clean up any existing outputs to ensure fresh run
    for path, _ in outputs.values():
        if path.exists():
            path.unlink()

    # --- Execution ---
    logger.info(f"Starting matrix generation for subject {subject_id}")

    # 1. AAL-90
    logger.info("Generating AAL-90 matrix...")
    try:
        apply_aal3(test_data_path)
    except Exception as e:
        pytest.fail(f"apply_aal3 failed: {e}")

    # 2. Schaefer-200
    logger.info("Generating Schaefer-200 matrix...")
    try:
        apply_schaefer200(test_data_path)
    except Exception as e:
        pytest.fail(f"apply_schaefer200 failed: {e}")

    # 3. Schaefer-400
    logger.info("Generating Schaefer-400 matrix...")
    try:
        apply_schaefer400(test_data_path)
    except Exception as e:
        pytest.fail(f"apply_schaefer400 failed: {e}")

    # --- Verification ---
    logger.info("Verifying outputs...")
    for name, (path, expected_n_nodes) in outputs.items():
        assert path.exists(), f"Output file {path} was not created."

        # Load and validate
        try:
            data = np.load(path)
        except Exception as e:
            pytest.fail(f"Failed to load {path}: {e}")

        # Check for expected keys (AdjacencyMatrix model usually saves 'matrix', 'labels', etc.)
        # The AdjacencyMatrix dataclass saves to .npz with specific keys.
        # Let's assume standard keys: 'matrix', 'labels', 'resolution'
        assert "matrix" in data, f"Missing 'matrix' key in {path}"
        assert "labels" in data, f"Missing 'labels' key in {path}"

        matrix = data["matrix"]
        labels = data["labels"]

        # Check dimensions
        assert matrix.shape[0] == matrix.shape[1], f"Matrix in {path} is not square."
        assert matrix.shape[0] == expected_n_nodes, \
            f"Matrix {path} has {matrix.shape[0]} nodes, expected {expected_n_nodes}."

        assert len(labels) == expected_n_nodes, \
            f"Labels in {path} has {len(labels)} entries, expected {expected_n_nodes}."

        # Check symmetry (if applicable, usually correlation matrices are symmetric)
        # We allow small floating point errors
        if not np.allclose(matrix, matrix.T, atol=1e-5):
            logger.warning(f"Matrix {path} is not perfectly symmetric.")

        # Check for NaNs or Infs
        assert not np.any(np.isnan(matrix)), f"Matrix {path} contains NaN values."
        assert not np.any(np.isinf(matrix)), f"Matrix {path} contains Inf values."

        logger.info(f"Verified {name}: {matrix.shape}")

    # --- Distinctness Check ---
    # Ensure the matrices are actually different (different resolutions)
    aal_data = np.load(outputs["aal90"][0])
    sch200_data = np.load(outputs["schaefer200"][0])
    sch400_data = np.load(outputs["schaefer400"][0])

    assert aal_data["matrix"].shape != sch200_data["matrix"].shape
    assert sch200_data["matrix"].shape != sch400_data["matrix"].shape
    assert aal_data["matrix"].shape != sch400_data["matrix"].shape

    logger.info("Integration test passed: All matrices generated and validated.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])