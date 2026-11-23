import os
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import scipy.sparse as sp

# Import the functions we are testing
# We need to adjust imports to match the project structure if run from root
# Assuming this test is run from the project root or code/
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.sweep_hygiene import generate_sweep_configs, run_single_sweep_instance
from utils.config import get_project_paths, ensure_directories
from utils.checksum import compute_file_checksum

def test_generate_sweep_configs():
    """Test that sweep configs are generated correctly."""
    n_vals = [100, 200]
    theta_vals = [1.0, 2.0]
    sparse_vals = [0.5]
    repeats = 2

    configs = generate_sweep_configs(n_vals, theta_vals, sparse_vals, repeats)

    # Total expected: 2 (N) * 2 (theta) * 1 (sparse) * 2 (repeats) = 8
    assert len(configs) == 8

    # Check structure of first config
    first = configs[0]
    assert "N" in first
    assert "theta" in first
    assert "sparsity" in first
    assert "repeat_id" in first
    assert "seed" in first
    assert first["N"] in n_vals
    assert first["theta"] in theta_vals
    assert first["sparsity"] in sparse_vals
    assert first["repeat_id"] < repeats

def test_run_single_sweep_instance():
    """Test that a single sweep instance generates raw files and checksums."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)

        config = {
            "N": 100,
            "theta": 2.5,
            "sparsity": 0.5,
            "repeat_id": 0,
            "seed": 42
        }

        result = run_single_sweep_instance(config, output_dir)

        # Verify result dictionary
        assert result["N"] == 100
        assert result["theta"] == 2.5
        assert "wigner_checksum" in result
        assert "perturbation_checksum" in result
        assert "output_dir" in result

        # Verify files exist
        run_dir = Path(result["output_dir"])
        assert run_dir.exists()

        wigner_path = run_dir / "wigner_matrix.npy"
        perturbation_path = run_dir / "perturbation_matrix.npz"
        manifest_path = run_dir / "checksums.json"

        assert wigner_path.exists(), "Wigner matrix file missing"
        assert perturbation_path.exists(), "Perturbation matrix file missing"
        assert manifest_path.exists(), "Checksum manifest missing"

        # Verify content types
        loaded_wigner = np.load(wigner_path)
        assert loaded_wigner.shape == (100, 100)
        assert isinstance(loaded_wigner, np.ndarray)

        loaded_pert = sp.load_npz(perturbation_path)
        assert loaded_pert.shape == (100, 100)
        assert sp.issparse(loaded_pert)

        # Verify checksums match
        with open(manifest_path, "r") as f:
            checksums = json.load(f)

        computed_wigner_hash = compute_file_checksum(wigner_path)
        computed_pert_hash = compute_file_checksum(perturbation_path)

        assert checksums["wigner_matrix.npy"] == computed_wigner_hash
        assert checksums["perturbation_matrix.npz"] == computed_pert_hash
