import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import numpy as np

# Ensure code/scripts is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.analyze_errors import load_misclassified_samples, categorize_error, analyze_errors, generate_report, generate_visualizations, main


class TestErrorCategorization:
    """
    Unit tests for error categorization logic as required by T022b.
    Specifically tests:
    - test_categorize_visual_ambiguity
    - test_categorize_logical_complexity
    """

    def test_categorize_visual_ambiguity(self):
        """
        Test Visual Ambiguity categorization.
        Heuristic: model confidence < 0.6 OR observation data is missing/low quality.
        """
        # Case 1: Low confidence triggers Visual Ambiguity
        sample_low_conf = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.45,
            "norm_value": 0.8,
            "keyword_match": True,
            "observation_data": "some_image_data"
        }
        category = categorize_error(sample_low_conf)
        assert category == "Visual Ambiguity", f"Expected 'Visual Ambiguity' for low confidence, got {category}"

        # Case 2: Missing observation data triggers Visual Ambiguity
        sample_missing_obs = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.85,
            "norm_value": 0.8,
            "keyword_match": True,
            "observation_data": None
        }
        category = categorize_error(sample_missing_obs)
        assert category == "Visual Ambiguity", f"Expected 'Visual Ambiguity' for missing observation, got {category}"

        # Case 3: High confidence and valid data should NOT be Visual Ambiguity (even if misclassified)
        sample_high_conf_valid_obs = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.92,
            "norm_value": 0.8,
            "keyword_match": True,
            "observation_data": "valid_image"
        }
        category = categorize_error(sample_high_conf_valid_obs)
        assert category != "Visual Ambiguity", f"Expected NOT 'Visual Ambiguity' for high confidence/valid obs, got {category}"

    def test_categorize_logical_complexity(self):
        """
        Test Logical Complexity categorization.
        Heuristic: (norm > 0.5 AND keyword_match == False) OR (norm <= 0.5 AND keyword_match == True).
        Essentially, the composite rule inputs disagree or are ambiguous in a way that suggests complexity.
        Based on T018: "if `norm > 0.5` AND `keyword_match == False` (or vice versa)".
        """
        # Case 1: Norm high, keyword missing -> Logical Complexity
        sample_norm_high_no_keyword = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.75,
            "norm_value": 0.85,
            "keyword_match": False,
            "observation_data": "valid_image"
        }
        category = categorize_error(sample_norm_high_no_keyword)
        assert category == "Logical Complexity", f"Expected 'Logical Complexity' for high norm/no keyword, got {category}"

        # Case 2: Norm low, keyword present -> Logical Complexity (vice versa)
        sample_norm_low_keyword = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.75,
            "norm_value": 0.3,
            "keyword_match": True,
            "observation_data": "valid_image"
        }
        category = categorize_error(sample_norm_low_keyword)
        assert category == "Logical Complexity", f"Expected 'Logical Complexity' for low norm/keyword, got {category}"

        # Case 3: Norm high, keyword present -> Should NOT be Logical Complexity (composite rule is satisfied by both)
        sample_norm_high_keyword = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.75,
            "norm_value": 0.85,
            "keyword_match": True,
            "observation_data": "valid_image"
        }
        category = categorize_error(sample_norm_high_keyword)
        assert category != "Logical Complexity", f"Expected NOT 'Logical Complexity' for high norm/keyword, got {category}"

        # Case 4: Norm low, keyword missing -> Should NOT be Logical Complexity (composite rule is satisfied by neither, but not conflicting)
        # Note: The heuristic "or vice versa" in T018 implies conflict. If both are false, it's likely Context Mismatch or just a standard error,
        # but definitely not the specific "conflict" defined as Logical Complexity here.
        sample_norm_low_no_keyword = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.75,
            "norm_value": 0.3,
            "keyword_match": False,
            "observation_data": "valid_image"
        }
        category = categorize_error(sample_norm_low_no_keyword)
        # Assuming this falls into Context Mismatch or general error, but not the specific "conflict" of Logical Complexity
        assert category != "Logical Complexity", f"Expected NOT 'Logical Complexity' for low norm/no keyword, got {category}"

    def test_categorize_context_mismatch(self):
        """
        Test Context Mismatch categorization.
        Heuristic: text_description contains "Safety Constraint" AND actions vector is zero or contradicts text.
        Simplified for this test: keyword_match is True (implies text has constraint) BUT norm is 0 (zero vector).
        """
        sample_context_mismatch = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.75,
            "norm_value": 0.0,
            "keyword_match": True,
            "observation_data": "valid_image",
            "text_description": "Safety Constraint: Stop immediately"
        }
        category = categorize_error(sample_context_mismatch)
        assert category == "Context Mismatch", f"Expected 'Context Mismatch' for zero vector with safety text, got {category}"

    def test_categorize_no_error(self):
        """
        Test that correctly classified samples are not categorized.
        """
        sample_correct = {
            "predicted_label": "constraint_satisfied",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.9,
            "norm_value": 0.3,
            "keyword_match": False,
            "observation_data": "valid_image"
        }
        category = categorize_error(sample_correct)
        assert category is None, f"Expected None for correct classification, got {category}"

    def test_categorize_priority(self):
        """
        Test that Visual Ambiguity takes priority over Logical Complexity if both conditions might be met.
        (e.g., low confidence AND norm/keyword conflict).
        """
        sample_priority = {
            "predicted_label": "constraint_violated",
            "true_label": "constraint_satisfied",
            "model_confidence": 0.4, # Low confidence -> Visual Ambiguity
            "norm_value": 0.85,      # High norm
            "keyword_match": False,  # No keyword -> Logical Complexity condition
            "observation_data": "valid_image"
        }
        # The categorize_error function should check Visual Ambiguity first
        category = categorize_error(sample_priority)
        assert category == "Visual Ambiguity", f"Expected 'Visual Ambiguity' to take priority, got {category}"