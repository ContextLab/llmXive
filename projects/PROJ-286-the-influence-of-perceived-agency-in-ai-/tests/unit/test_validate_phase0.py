import json
import os
import sys
from pathlib import Path
import pytest

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.research.validate_phase0 import (
    load_json_file,
    read_text_file,
    validate_power_calculation_json,
    validate_citations_json,
    validate_research_md
)

class TestValidatePhase0:
    def test_validate_power_calculation_json_valid(self, tmp_path):
        """Test validation of a correctly structured power calculation JSON."""
        data = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "power": 0.80,
            "results": {
                "sample_size": 128
            }
        }
        assert validate_power_calculation_json(data) is True

    def test_validate_power_calculation_json_missing_key(self, tmp_path):
        """Test validation fails when a required key is missing."""
        data = {
            "effect_size": 0.25,
            "alpha": 0.05,
            # missing 'power' and 'results'
        }
        assert validate_power_calculation_json(data) is False

    def test_validate_power_calculation_json_wrong_type(self, tmp_path):
        """Test validation fails when a value has wrong type."""
        data = {
            "effect_size": "small", # should be number
            "alpha": 0.05,
            "power": 0.80,
            "results": {
                "sample_size": 128
            }
        }
        assert validate_power_calculation_json(data) is False

    def test_validate_citations_json_valid(self, tmp_path):
        """Test validation of a correctly structured citations list."""
        data = [
            {
                "title": "Trust in Automation",
                "doi": "10.1234/test",
                "overlap_score": 0.85,
                "status": "valid"
            }
        ]
        assert validate_citations_json(data) is True

    def test_validate_citations_json_missing_key(self, tmp_path):
        """Test validation fails when a required key is missing in citation."""
        data = [
            {
                "title": "Trust in Automation",
                # missing 'doi', 'overlap_score', 'status'
            }
        ]
        assert validate_citations_json(data) is False

    def test_validate_research_md_valid(self, tmp_path):
        """Test validation of a correctly structured research.md."""
        content = """
        # Research Plan

        | Effect Size | Alpha | Target Power | Required N | Calculated N |
        | --- | --- | --- | --- | --- |
        | 0.25 | 0.05 | 0.80 | 128 | 128 |

        See [power_report.md](../research/power_report.md) for details.
        """
        power_data = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "power": 0.80,
            "results": {"sample_size": 128}
        }
        assert validate_research_md(content, power_data) is True

    def test_validate_research_md_missing_reference(self, tmp_path):
        """Test validation fails when power_report.md reference is missing."""
        content = """
        # Research Plan

        | Effect Size | Alpha | Target Power | Required N | Calculated N |
        | --- | --- | --- | --- | --- |
        | 0.25 | 0.05 | 0.80 | 128 | 128 |
        """
        power_data = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "power": 0.80,
            "results": {"sample_size": 128}
        }
        assert validate_research_md(content, power_data) is False