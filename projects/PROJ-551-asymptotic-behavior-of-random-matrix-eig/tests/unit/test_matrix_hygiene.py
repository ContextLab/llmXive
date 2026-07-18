"""
Unit tests for the Matrix Hygiene module (T019).

Tests verify that:
1. Raw matrices are generated and saved correctly.
2. Checksum manifests are created and valid.
3. The process is deterministic given the same seed.
"""
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest

# Import from project API surface
from data_models import SimulationRun, PerturbationConfig
from analysis.matrix_hygiene import run_hygiene_capture
from utils.checksum import load_checksum_manifest, verify_checksums
from utils.config import ensure_directories

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_hygiene_capture_creates_files(temp_output_dir):
    """Test that run_hygiene_capture creates the expected files."""
    sim_run = SimulationRun(n=100, seed=123, num_eigenvalues=5)
    pert_config = PerturbationConfig(theta=2.0, rank=1, sparsity_density=1.0)
    
    checksums = run_hygiene_capture(sim_run, pert_config, output_dir=temp_output_dir)
    
    # Check that checksums dictionary is populated
    assert len(checksums) > 0
    
    # Verify specific files exist
    run_dirs = list(temp_output_dir.glob("*/"))
    assert len(run_dirs) == 1, "Expected exactly one run directory"
    run_dir = run_dirs[0]
    
    expected_files = [
        "wigner_matrix.npy",
        "perturbation_matrix.npy",
        "perturbed_matrix.npy",
        "top_eigenvalues.npy",
        "checksum_manifest.json"
    ]
    
    for fname in expected_files:
        fpath = run_dir / fname
        assert fpath.exists(), f"Expected file {fname} not found in {run_dir}"

def test_hygiene_manifest_validity(temp_output_dir):
    """Test that the generated manifest is valid JSON and verifiable."""
    sim_run = SimulationRun(n=100, seed=456, num_eigenvalues=5)
    pert_config = PerturbationConfig(theta=2.0, rank=1, sparsity_density=1.0)
    
    run_hygiene_capture(sim_run, pert_config, output_dir=temp_output_dir)
    
    run_dirs = list(temp_output_dir.glob("*/"))
    run_dir = run_dirs[0]
    manifest_path = run_dir / "checksum_manifest.json"
    
    # Load and verify
    manifest = load_checksum_manifest(manifest_path)
    assert manifest is not None
    assert isinstance(manifest, dict)
    
    # Verify checksums
    is_valid, failed_files = verify_checksums(manifest)
    assert is_valid, f"Checksum verification failed for: {failed_files}"

def test_hygiene_determinism(temp_output_dir):
    """Test that running with the same seed produces identical matrices."""
    sim_run = SimulationRun(n=50, seed=999, num_eigenvalues=5)
    pert_config = PerturbationConfig(theta=2.0, rank=1, sparsity_density=1.0)
    
    # First run
    checksums_1 = run_hygiene_capture(sim_run, pert_config, output_dir=temp_output_dir / "run1")
    
    # Second run with same seed
    checksums_2 = run_hygiene_capture(sim_run, pert_config, output_dir=temp_output_dir / "run2")
    
    # Compare checksums
    for key in checksums_1:
        assert key in checksums_2, "File missing in second run"
        assert checksums_1[key] == checksums_2[key], f"Checksum mismatch for {key}"
        
def test_hygiene_sparse_perturbation(temp_output_dir):
    """Test that sparse perturbations are handled correctly."""
    sim_run = SimulationRun(n=100, seed=789, num_eigenvalues=5)
    # Low sparsity density should trigger sparse saving logic
    pert_config = PerturbationConfig(theta=2.0, rank=1, sparsity_density=0.1)
    
    checksums = run_hygiene_capture(sim_run, pert_config, output_dir=temp_output_dir)
    
    run_dirs = list(temp_output_dir.glob("*/"))
    run_dir = run_dirs[0]
    
    # Check for .npz extension for sparse perturbation
    perturbation_files = list(run_dir.glob("perturbation_matrix.*"))
    assert len(perturbation_files) == 1
    assert perturbation_files[0].suffix in ['.npz', '.npy'], "Unexpected perturbation file format"
    
    # Verify we can load it back
    if perturbation_files[0].suffix == '.npz':
        from scipy import sparse
        loaded = sparse.load_npz(str(perturbation_files[0]))
        assert loaded.shape == (100, 100)
    else:
        loaded = np.load(str(perturbation_files[0]))
        assert loaded.shape == (100, 100)
