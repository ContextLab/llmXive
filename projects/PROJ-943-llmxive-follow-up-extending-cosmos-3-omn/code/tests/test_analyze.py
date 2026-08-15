"""
Unit tests for error analysis and categorization logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.analyze_errors import categorize_error, load_misclassified, generate_report


class TestErrorCategorization:
    """Tests for error categorization logic."""

    def test_categorize_error_visual_ambiguity(self):
        """Test categorization of visual ambiguity errors."""
        sample = {
            "id": 1,
            "true_label": "constraint_violated",
            "predicted_label": "constraint_satisfied",
            "error_type": "visual_ambiguity",
            "features": {"visual_confusion_score": 0.9}
        }
        category = categorize_error(sample)
        assert category == "visual_ambiguity"

    def test_categorize_error_logical_complexity(self):
        """Test categorization of logical complexity errors."""
        sample = {
            "id": 2,
            "true_label": "constraint_violated",
            "predicted_label": "constraint_satisfied",
            "error_type": "logical_complexity",
            "features": {"rule_depth": 5}
        }
        category = categorize_error(sample)
        assert category == "logical_complexity"

    def test_categorize_error_context_mismatch(self):
        """Test categorization of context mismatch errors."""
        sample = {
            "id": 3,
            "true_label": "constraint_violated",
            "predicted_label": "constraint_satisfied",
            "error_type": "context_mismatch",
            "features": {"context_confidence": 0.1}
        }
        category = categorize_error(sample)
        assert category == "context_mismatch"

    def test_categorize_error_unknown(self):
        """Test categorization of unknown error types."""
        sample = {
            "id": 4,
            "true_label": "constraint_violated",
            "predicted_label": "constraint_satisfied",
            "error_type": "unknown",
            "features": {}
        }
        category = categorize_error(sample)
        assert category == "unknown"
