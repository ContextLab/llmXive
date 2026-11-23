import unittest
import numpy as np
import json
from code.spectrum_computation import compute_bb_spectrum, save_spectrum_results

class TestSpectrumComputation(unittest.TestCase):

    def test_compute_bb_spectrum(self):
        # Create a dummy map for testing
        nside = 32
        map_data = np.random.rand(hp.nside2npix(nside))
        dummy_map_file = "test_map.fits"
        hp.write_map(dummy_map_file, map_data, nest=True)

        # Compute the BB spectrum
        cl_bb = compute_bb_spectrum(dummy_map_file)

        # Assert that the result is a numpy array and has the expected shape
        self.assertIsInstance(cl_bb, np.ndarray)
        self.assertEqual(len(cl_bb), 301) # lmax = 300 + 1

        # Clean up the dummy map file
        import os
        os.remove(dummy_map_file)

    def test_save_spectrum_results(self):
        # Create a dummy spectrum for testing
        l = np.arange(10)
        cl_bb = np.random.rand(10)
        output_path = "test_spectrum.json"

        # Save the spectrum results
        save_spectrum_results(cl_bb, output_path)

        # Load the saved spectrum and verify its contents
        with open(output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['l'], list(range(10)))
        self.assertListEqual(data['cl_bb'], cl_bb.tolist())

        # Clean up the output file
        import os
        os.remove(output_path)


if __name__ == '__main__':
    unittest.main()