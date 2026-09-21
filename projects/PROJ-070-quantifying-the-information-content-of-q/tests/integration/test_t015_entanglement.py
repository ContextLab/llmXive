import os
import sys
import tempfile
import shutil
import numpy as np
import h5py
import pytest
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from metrics import calculate_entanglement_entropy, process_dataset_for_entanglement
from logging_config import setup_logging

setup_logging()

class TestT015Entanglement:

    def test_calculate_entanglement_entropy_product_state(self):
        """
        Test T015: Entropy of a product state should be 0 (or near 0).
        Product state: |00...0>
        """
        N = 6
        dim = 2**N
        psi = np.zeros(dim, dtype=complex)
        psi[0] = 1.0 # |000000>

        # Split 3 vs 3
        partition = (2**3, 2**3)
        entropy = calculate_entanglement_entropy(psi, partition)
        
        assert abs(entropy) < 1e-6, f"Product state entropy should be ~0, got {entropy}"

    def test_calculate_entanglement_entropy_max_entangled(self):
        """
        Test T015: Entropy of a maximally entangled state (Bell pair repeated).
        State: (|00> + |11>)/sqrt(2) repeated N/2 times.
        Entropy should be N/2 * log(2) if split correctly?
        Actually, for N qubits, if we split N/2 vs N/2, and state is product of Bell pairs across the cut,
        entropy is (N/2) * log(2).
        Let's do N=4, split 2 vs 2. State: (|00> + |11>)/sqrt(2) x (|00> + |11>)/sqrt(2).
        Schmidt coeffs: 0.5, 0.5, 0.5, 0.5 (4 terms).
        Entropy = -4 * (0.25 * log(0.25)) = -log(0.25) = log(4) = 2 * log(2).
        """
        N = 4
        dim = 2**N
        # Construct state: |0000> + |0101> + |1010> + |1111> (normalized)
        # Indices: 0, 5, 10, 15
        psi = np.zeros(dim, dtype=complex)
        indices = [0, 5, 10, 15]
        for idx in indices:
            psi[idx] = 1.0 / np.sqrt(4.0)
        
        # Partition 2 vs 2 (size 4 vs 4)
        partition = (2**2, 2**2)
        entropy = calculate_entanglement_entropy(psi, partition)
        
        expected_entropy = 2 * np.log(2)
        assert abs(entropy - expected_entropy) < 1e-4, f"Expected {expected_entropy}, got {entropy}"

    def test_process_dataset_for_entanglement_io(self):
        """
        Test T015: Full pipeline from HDF5 files to CSV output.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "input")
            os.makedirs(input_dir)
            
            output_file = os.path.join(tmpdir, "output.csv")
            
            # Create a fake wavefunction file (N=4, product state)
            fname = "test_N4.h5"
            filepath = os.path.join(input_dir, fname)
            
            N = 4
            dim = 2**N
            psi = np.zeros(dim, dtype=complex)
            psi[0] = 1.0
            
            with h5py.File(filepath, 'w') as f:
                f.create_dataset("wavefunction", data=psi)
            
            # Run processing
            count = process_dataset_for_entanglement(input_dir, output_file)
            
            assert count == 1, f"Expected 1 file processed, got {count}"
            assert os.path.exists(output_file), "Output CSV not created"
            
            df = pd.read_csv(output_file)
            assert len(df) == 1
            assert df.iloc[0]['system_size'] == 4
            assert abs(df.iloc[0]['entropy']) < 1e-5 # Product state
            assert abs(df.iloc[0]['entropy_per_spin']) < 1e-5
            assert df.iloc[0]['source_file'] == fname

    def test_process_dataset_for_entanglement_empty_dir(self):
        """
        Test T015: Handles empty directory gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "empty_output.csv")
            count = process_dataset_for_entanglement(tmpdir, output_file)
            
            assert count == 0
            assert os.path.exists(output_file)
            df = pd.read_csv(output_file)
            assert len(df) == 0
            assert list(df.columns) == ["system_size", "entropy", "entropy_per_spin", "source_file"]