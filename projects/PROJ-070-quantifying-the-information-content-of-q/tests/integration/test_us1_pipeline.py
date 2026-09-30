import unittest
import numpy as np
import os
from code.metrics import load_wavefunction_from_hdf5, calculate_entanglement_entropy
from code.data_loader import generate_internal_dataset
from code.utils.sparse_helpers import convert_to_csr
import h5py

class TestUS1Pipeline(unittest.TestCase):

    def setUp(self):
        self.n = 10
        self.wavefunction_file = "data/test_wavefunction.hdf5"
        self.dataset = generate_internal_dataset(self.n)
        with h5py.File(self.wavefunction_file, 'w') as hf:
            hf.create_dataset('wavefunction', data=self.dataset)

    def tearDown(self):
        if os.path.exists(self.wavefunction_file):
            os.remove(self.wavefunction_file)

    def test_pipeline(self):
        # Load wavefunction
        wavefunction = load_wavefunction_from_hdf5(self.wavefunction_file)
        
        # Convert to CSR format
        wavefunction_csr = convert_to_csr(wavefunction)

        # Calculate entanglement entropy
        entanglement_entropy = calculate_entanglement_entropy(wavefunction_csr)
        
        # Assert that the entropy is a valid number
        self.assertIsInstance(entanglement_entropy, float)
        self.assertGreaterEqual(entanglement_entropy, 0.0)

if __name__ == '__main__':
    unittest.main()