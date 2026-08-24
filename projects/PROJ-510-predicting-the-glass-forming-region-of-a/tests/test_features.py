import unittest
from unittest.mock import patch
import pandas as pd
from code.features import get_element_properties, validate_composition, calculate_mixing_enthalpy, calculate_atomic_size_mismatch, compute_features
import numpy as np

class TestFeatures(unittest.TestCase):

    def test_get_element_properties(self):
        props = get_element_properties("Fe")
        self.assertIsInstance(props, dict)
        self.assertAlmostEqual(props["atomic_size"], 140.0, places=2)

    def test_validate_composition(self):
        self.assertTrue(validate_composition("Fe,Cr,Ni"))
        self.assertFalse(validate_composition("Fe,X,Ni"))

    def test_calculate_mixing_enthalpy(self):
        composition = ["Fe", "Cr", "Ni"]
        weights = [0.5, 0.3, 0.2]
        enthalpy = calculate_mixing_enthalpy(composition, weights)
        self.assertIsInstance(enthalpy, float)

    def test_compute_features(self):
        data = {"composition": "Fe:0.5,Cr:0.3,Ni:0.2"}
        df = pd.DataFrame([data])
        result = compute_features(df.iloc[0])
        self.assertIsInstance(result, pd.Series)

if __name__ == '__main__':
    unittest.main()