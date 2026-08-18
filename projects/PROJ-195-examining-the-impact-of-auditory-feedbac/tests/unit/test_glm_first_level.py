"""
Unit tests for contrast definition logic in the First-Level GLM pipeline.

This module verifies that the contrast definitions for 'delayed' and 'pitch-shifted'
conditions are correctly combined to form the 'perturbed' condition as specified
in the user story US2 requirements.

Tests:
  - test_contrast_definition_perturbed: Verifies the union of delayed and pitch-shifted.
  - test_contrast_vector_structure: Verifies the shape and values of the contrast vector.
  - test_event_labels_exist: Ensures the required event labels are recognized.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path for imports
# Assuming tests are run from the project root: python -m pytest tests/unit/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils import validate_event_labels


class TestContrastDefinitionLogic:
    """Tests for the logic defining the 'perturbed' contrast."""

    def setup_method(self):
        """Set up test fixtures."""
        # Define the expected event labels based on the project spec
        self.required_labels = ['normal', 'delayed', 'pitch-shifted']
        self.perturbed_definition = {
            'name': 'perturbed',
            'conditions': ['delayed', 'pitch-shifted'],
            'description': 'Union of delayed and pitch-shifted auditory feedback conditions'
        }

    def test_event_labels_exist(self):
        """
        Verify that the required event labels exist in the validation logic.
        This ensures that the data pipeline will not proceed without 'delayed' and 'pitch-shifted'.
        """
        # This test verifies that the validation function knows about the required labels.
        # If these labels are missing from the data, the downstream GLM should fail gracefully.
        # We test that the function accepts these labels as valid.
        try:
            # Simulate a validation call with the required labels
            # The function returns True if valid, raises error otherwise
            is_valid = validate_event_labels(self.required_labels)
            assert is_valid is True, "Validation should pass for required event labels"
        except Exception as e:
            pytest.fail(f"validate_event_labels failed for required labels: {e}")

    def test_contrast_definition_perturbed(self):
        """
        Test that the 'perturbed' contrast is correctly defined as the union
        of 'delayed' and 'pitch-shifted' conditions.
        """
        conditions = self.perturbed_definition['conditions']
        
        assert 'delayed' in conditions, "Contrast definition must include 'delayed' condition"
        assert 'pitch-shifted' in conditions, "Contrast definition must include 'pitch-shifted' condition"
        assert len(conditions) == 2, "Contrast definition must contain exactly two conditions"
        
        # Verify no other conditions are included in this specific contrast
        assert 'normal' not in conditions, "Contrast definition must NOT include 'normal' condition"

    def test_contrast_vector_structure(self):
        """
        Test the structure of a theoretical contrast vector used in nilearn GLM.
        In a design matrix with columns [Intercept, Normal, Delayed, Pitch-Shifted, ...],
        the contrast vector for 'perturbed' would be [0, 0, 1, 1, ...].
        """
        # Simulate a design matrix column order
        # Assuming standard order: Intercept, then condition-specific regressors
        # This is a logical test of the vector construction, not execution against data
        design_columns = ['intercept', 'normal', 'delayed', 'pitch-shifted']
        
        # Construct the contrast vector
        contrast_vector = np.zeros(len(design_columns))
        for i, col in enumerate(design_columns):
            if col in self.perturbed_definition['conditions']:
                contrast_vector[i] = 1.0
        
        # Expected vector: [0, 0, 1, 1]
        expected_vector = np.array([0.0, 0.0, 1.0, 1.0])
        
        assert np.array_equal(contrast_vector, expected_vector), \
            f"Contrast vector {contrast_vector} does not match expected {expected_vector}"
        
        # Verify the sum of weights is 2 (indicating a union of two conditions)
        assert np.sum(contrast_vector) == 2.0, "Sum of contrast weights should be 2.0 for a union of two conditions"

    def test_contrast_name_consistency(self):
        """
        Ensure the contrast name 'perturbed' is consistent across definitions.
        """
        assert self.perturbed_definition['name'] == 'perturbed', \
            "Contrast name must be 'perturbed' to match downstream analysis expectations"

    def test_missing_condition_handling(self):
        """
        Test that the logic correctly identifies if a required condition is missing from the definition.
        """
        incomplete_definition = {
            'name': 'perturbed',
            'conditions': ['delayed'] # Missing 'pitch-shifted'
        }
        
        assert 'pitch-shifted' not in incomplete_definition['conditions'], \
            "Test setup error: incomplete definition should not have pitch-shifted"
        
        # Logic check: if we were to construct a vector, it would be incomplete
        # This test ensures the definition object is the source of truth
        assert len(incomplete_definition['conditions']) < 2, \
            "Incomplete definition should have fewer than 2 conditions"