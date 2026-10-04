import os
import yaml
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_generator import generate_output_schema

class TestAnalysisOutputSchema:
    """Contract tests for analysis output schema validation."""

    @pytest.fixture
    def schema(self):
        """Load the generated output schema."""
        return generate_output_schema()

    def test_schema_has_required_sections(self, schema):
        """Test that the schema contains all required sections."""
        required_sections = ["t_test_results", "effect_sizes", "power_analysis"]
        
        for section in required_sections:
            assert section in schema["properties"], f"Missing required section: {section}"

    def test_t_test_results_structure(self, schema):
        """Test that t_test_results has the correct structure."""
        t_test_props = schema["properties"]["t_test_results"]["properties"]
        assert "statistic" in t_test_props
        assert "pvalue" in t_test_props
        assert "df" in t_test_props

    def test_effect_sizes_structure(self, schema):
        """Test that effect_sizes has the correct structure."""
        effect_props = schema["properties"]["effect_sizes"]["properties"]
        assert "cohen_d" in effect_props
        assert "ci_lower" in effect_props
        assert "ci_upper" in effect_props

    def test_power_analysis_structure(self, schema):
        """Test that power_analysis has the correct structure."""
        power_props = schema["properties"]["power_analysis"]["properties"]
        assert "power" in power_props
        assert "mdes" in power_props
