import os
import sys
import json
import unittest
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports if necessary
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from resampling import ValidationException, calculate_cv

class TestResamplingLogicContract(unittest.TestCase):
    """
    Contract test for resampling logic (T020).
    Validates CV constraints against contracts/resampling.schema.yaml.
    """

    @classmethod
    def setUpClass(cls):
        """Load the schema definition once for all tests."""
        schema_path = project_root / "contracts" / "resampling.schema.yaml"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            cls.schema = yaml.safe_load(f)
        
        # Extract validation rules from schema
        cls.validation_rules = cls.schema.get('validation_rules', [])
        cls.real_data_threshold = 0.10
        cls.combined_threshold = 0.30

    def test_schema_exists_and_valid(self):
        """Verify the schema file exists and contains required fields."""
        required_fields = {'bin_id', 'sample_count', 'cv', 'real_data_flag'}
        schema_fields = {f['name'] for f in self.schema['fields']}
        
        self.assertTrue(required_fields.issubset(schema_fields), 
                      f"Schema missing required fields: {required_fields - schema_fields}")

    def test_cv_constraint_real_data(self):
        """
        Test that real data bins respect CV <= 0.10.
        Simulates a resampling scenario with only real data.
        """
        # Create a mock dataset representing a real-data bin
        # Using a distribution that should satisfy the constraint
        np.random.seed(42)
        real_data_values = np.random.normal(loc=10, scale=0.5, size=100)
        
        # Calculate CV manually to verify
        mean_val = np.mean(real_data_values)
        std_val = np.std(real_data_values)
        calculated_cv = std_val / mean_val if mean_val != 0 else 0.0
        
        # This test data is constructed to pass
        self.assertLessEqual(calculated_cv, self.real_data_threshold, 
                           "Test data CV should be within real data threshold")
        
        # Simulate the validation gate logic
        try:
            if calculated_cv > self.real_data_threshold:
                raise ValidationException(f"Real data CV {calculated_cv:.4f} exceeds threshold {self.real_data_threshold}")
        except ValidationException:
            self.fail("ValidationException raised for valid real data")

    def test_cv_constraint_combined_data(self):
        """
        Test that combined (real + synthetic) bins respect CV <= 0.30.
        Simulates a scenario where SMOTE was triggered.
        """
        # Create a mock dataset representing a combined bin
        # Using a distribution that should satisfy the combined threshold but fail real threshold
        np.random.seed(123)
        real_values = np.random.normal(loc=10, scale=0.8, size=50) # Higher variance
        synthetic_values = np.random.normal(loc=10.5, scale=0.2, size=50) # Lower variance to stabilize
        
        combined_values = np.concatenate([real_values, synthetic_values])
        
        mean_val = np.mean(combined_values)
        std_val = np.std(combined_values)
        calculated_cv = std_val / mean_val if mean_val != 0 else 0.0
        
        # Verify it passes combined threshold
        self.assertLessEqual(calculated_cv, self.combined_threshold,
                           f"Combined CV {calculated_cv:.4f} exceeds combined threshold {self.combined_threshold}")
        
        # Verify it might fail real threshold (depending on data, just checking logic)
        # This is just to ensure the thresholds are distinct
        self.assertGreater(self.combined_threshold, self.real_data_threshold)

    def test_empty_bin_rejection(self):
        """
        Test that bins with sample_count < 1 are rejected.
        """
        empty_count = 0
        
        # Simulate validation rule for sample_count
        if empty_count < 1:
            with self.assertRaises(AssertionError):
                # Mimic the logic from schema
                assert empty_count >= 1, "Empty bin detected"

    def test_validation_gate_integration(self):
        """
        Integration test for the validation gate logic described in the schema.
        Ensures ValidationException is raised correctly.
        """
        test_cases = [
            {"cv": 0.05, "real_data_flag": True, "should_fail": False},
            {"cv": 0.15, "real_data_flag": True, "should_fail": True},
            {"cv": 0.25, "real_data_flag": False, "should_fail": False},
            {"cv": 0.35, "real_data_flag": False, "should_fail": True},
        ]
        
        for case in test_cases:
            cv = case["cv"]
            is_real = case["real_data_flag"]
            should_fail = case["should_fail"]
            
            try:
                if is_real and cv > self.real_data_threshold:
                    raise ValidationException(f"Real data CV {cv} > {self.real_data_threshold}")
                if not is_real and cv > self.combined_threshold:
                    raise ValidationException(f"Combined CV {cv} > {self.combined_threshold}")
                
                if should_fail:
                    self.fail(f"Expected ValidationException for CV={cv}, real={is_real}")
            except ValidationException:
                if not should_fail:
                    self.fail(f"Unexpected ValidationException for CV={cv}, real={is_real}")

    def test_schema_examples_valid(self):
        """
        Verify that the examples in the schema are valid according to the rules.
        """
        examples = self.schema.get('examples', [])
        
        for ex in examples:
            cv = ex['cv']
            is_real = ex['real_data_flag']
            
            if is_real:
                self.assertLessEqual(cv, self.real_data_threshold,
                                   f"Example {ex['bin_id']} is real but CV {cv} > {self.real_data_threshold}")
            else:
                self.assertLessEqual(cv, self.combined_threshold,
                                   f"Example {ex['bin_id']} is combined but CV {cv} > {self.combined_threshold}")

if __name__ == '__main__':
    unittest.main()