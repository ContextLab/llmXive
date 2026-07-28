"""
Integration test for User Story 1: Full pipeline on small N.

This test verifies the end-to-end flow:
1. Generate internal wavefunction data (N=10, 12, 14) via ED.
2. Compute entanglement entropy (sparse SVD).
3. Quantize and compute NCD (complexity).
4. Perform correlation analysis.
5. Generate visualization.
6. Validate output artifacts exist and contain valid data.

Dependencies:
- T013 (ED Generator)
- T015 (Entanglement Metric)
- T016 (NCD Metric)
- T017 (Correlation)
- T018 (Viz)
"""

import os
import sys
import tempfile
import shutil
import numpy as np
import pandas as pd
import pytest

# Project imports
from config import Config
from data_loader import generate_internal_wavefunction, save_wavefunction_hdf5
from metrics import calculate_entanglement_entropy, quantize_wavefunction, calculate_ncd
from statistics import calculate_partial_correlation
from viz import plot_scatter_with_regression
from logging_config import setup_logging, clear_event_logs, get_instability_events

# Setup logging for the test
setup_logging()
clear_event_logs()


@pytest.fixture(scope="module")
def test_output_dir():
    """Create a temporary directory for test outputs."""
    tmp_dir = tempfile.mkdtemp(prefix="us1_integration_")
    yield tmp_dir
    # Cleanup after test
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


@pytest.fixture(scope="module")
def small_n_configs():
    """Return a list of small system sizes for integration testing."""
    # N=10, 12, 14 are small enough for exact diagonalization in unit test context
    return [10, 12, 14]


def test_us1_full_pipeline(test_output_dir, small_n_configs):
    """
    Run the full US1 pipeline: Generate -> Metrics -> Statistics -> Viz.
    """
    # 1. Generate Data
    # We use the internal generator as per T013/T014 design for small N
    # ensuring we have real wavefunction coefficients (not placeholders).
    wavefunction_files = []
    systems = []

    for n in small_n_configs:
        # Generate a random ground state approximation or exact ED state
        # For integration, we rely on generate_internal_wavefunction which
        # delegates to the ED logic defined in T013.
        try:
            psi, info = generate_internal_wavefunction(n, method="ed", seed=42)
        except Exception as e:
            pytest.fail(f"Failed to generate wavefunction for N={n}: {e}")

        # Save to HDF5 as per T013 output spec
        out_path = os.path.join(test_output_dir, f"psi_N{n}.h5")
        save_wavefunction_hdf5(psi, out_path, info)
        wavefunction_files.append(out_path)
        systems.append(n)

    # 2. Compute Metrics
    entropies = []
    complexities = []
    ns = []

    for i, n in enumerate(systems):
        psi_path = wavefunction_files[i]

        # Load state (simulating the input to metrics)
        # We reconstruct the state from file to ensure file I/O works
        # In a real pipeline, this would be a streaming reader, but for N=14
        # we can load into memory.
        with h5py.File(psi_path, 'r') as f:
            psi = f['wavefunction'][:]
            # Ensure complex type
            if psi.dtype == np.float64:
                # If stored as real/imag pairs or just real, handle accordingly
                # Assuming save_wavefunction_hdf5 stores complex as separate or complex64/128
                # If it stores real and imag, we need to reconstruct.
                # For robustness, we assume the file contains a 'real' and 'imag' dataset or a complex one.
                # Let's assume the helper saves 'real' and 'imag' keys if complex.
                if 'real' in f and 'imag' in f:
                    psi = f['real'][:] + 1j * f['imag'][:]
                else:
                    psi = psi.astype(np.complex128)

        # Calculate Entanglement (T015)
        # We assume a bipartition of 1: (N-1) or similar for 1D chain
        # The function expects a state vector and system size
        try:
            ent, ent_per_spin = calculate_entanglement_entropy(psi, n, partition=1)
        except Exception as e:
            pytest.fail(f"Entanglement calculation failed for N={n}: {e}")
        entropies.append(ent)
        ns.append(n)

        # Calculate Complexity (T016)
        # 1. Quantize
        try:
            q_psi = quantize_wavefunction(psi)
        except Exception as e:
            pytest.fail(f"Quantization failed for N={n}: {e}")

        # 2. NCD
        try:
            ncd_val = calculate_ncd(q_psi)
        except Exception as e:
            pytest.fail(f"NCD calculation failed for N={n}: {e}")
        complexities.append(ncd_val)

    # 3. Correlation Analysis (T017)
    # We have small N, so partial correlation controlling for N is trivial
    # but we must call the function to ensure the API works.
    try:
        corr_result = calculate_partial_correlation(
            x=np.array(entropies),
            y=np.array(complexities),
            z=np.array(ns)
        )
    except Exception as e:
        pytest.fail(f"Correlation analysis failed: {e}")

    # Assertions on results
    assert 'r' in corr_result, "Correlation result missing 'r'"
    assert 'p' in corr_result, "Correlation result missing 'p'"
    assert 'conf_int' in corr_result, "Correlation result missing 'conf_int'"

    # 4. Visualization (T018)
    plot_path = os.path.join(test_output_dir, "us1_scatter.png")
    try:
        fig = plot_scatter_with_regression(
            x=np.array(entropies),
            y=np.array(complexities),
            z=np.array(ns), # Size encoding
            title="US1: Entanglement vs Complexity",
            xlabel="Entanglement Entropy",
            ylabel="Complexity (NCD)"
        )
        fig.savefig(plot_path)
        plt.close(fig)
    except Exception as e:
        pytest.fail(f"Visualization generation failed: {e}")

    # 5. Validate Outputs
    # Check that the plot file exists and is non-empty
    assert os.path.exists(plot_path), f"Plot file {plot_path} not created"
    assert os.path.getsize(plot_path) > 1000, "Plot file is empty or too small"

    # Check that correlation results are plausible (not NaN/Inf)
    assert np.isfinite(corr_result['r']), "Correlation coefficient is not finite"
    assert np.isfinite(corr_result['p']), "P-value is not finite"

    # Check for numerical instability events
    inst_events = get_instability_events()
    if inst_events:
        # Log them but don't necessarily fail unless critical
        # For this integration test, we just ensure the pipeline didn't crash
        print(f"Warning: Numerical instabilities detected: {inst_events}")

    # Success: The pipeline ran end-to-end on real generated data
    print(f"Integration Test US1 PASSED. N={small_n_configs}, r={corr_result['r']:.4f}")


def test_output_files_created(test_output_dir, small_n_configs):
    """
    Verify that the specific output files mentioned in tasks.md are created.
    This is a secondary check to ensure the file system side-effects are correct.
    """
    # Note: The main test creates files in a temp dir.
    # In a real CI run, this would check `data/processed/entanglement_metrics.csv`
    # and `figures/us1_scatter.png`.
    # Here we verify the temp dir structure.
    expected_plots = [os.path.join(test_output_dir, "us1_scatter.png")]
    for p in expected_plots:
        assert os.path.exists(p), f"Expected file {p} not found"


# Note: We import h5py here because it is used in the test logic.
# It is a declared dependency in T002.
import h5py
import matplotlib.pyplot as plt