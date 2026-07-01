import pytest
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.parsers import extract_sample_size, extract_effect_size
from code.utils.oa_checker import is_open_access

class TestAbstractFallback:
    """Tests for T023: Abstract retrieval fallback mechanism."""

    def test_extract_sample_size_from_abstract(self):
        """Test that sample size can be extracted from abstract text."""
        abstract = "We analyzed a dataset with N=150 participants in our study."
        result = extract_sample_size(abstract)
        assert result == 150

    def test_extract_effect_size_from_abstract(self):
        """Test that effect size can be extracted from abstract text."""
        abstract = "Results showed a significant effect, Cohen's d=0.45, p<0.05."
        effect_size, metric_type, dof = extract_effect_size(abstract)
        assert effect_size == 0.45
        assert metric_type == "Cohen's d"
        assert dof is None

    def test_extract_f_statistic_from_abstract(self):
        """Test that F-statistic can be extracted from abstract text."""
        abstract = "An ANOVA revealed a significant effect, F(2, 97)=4.56, p=0.01."
        effect_size, metric_type, dof = extract_effect_size(abstract)
        assert metric_type == "F"
        assert dof == (2, 97)

    def test_parse_empty_abstract(self):
        """Test handling of empty abstract."""
        abstract = ""
        sample = extract_sample_size(abstract)
        effect = extract_effect_size(abstract)
        assert sample is None
        assert effect is None

    def test_parse_abstract_without_metrics(self):
        """Test abstract that has text but no extractable metrics."""
        abstract = "This study explores various factors affecting the outcome."
        sample = extract_sample_size(abstract)
        effect = extract_effect_size(abstract)
        assert sample is None
        assert effect is None

class TestOACheckerIntegration:
    """Integration tests for OA checker (mocked for T023)."""

    def test_oa_checker_exists(self):
        """Verify OA checker function exists and is callable."""
        assert callable(is_open_access)

    def test_oa_checker_signature(self):
        """Verify OA checker has expected signature."""
        import inspect
        sig = inspect.signature(is_open_access)
        params = list(sig.parameters.keys())
        assert "url" in params