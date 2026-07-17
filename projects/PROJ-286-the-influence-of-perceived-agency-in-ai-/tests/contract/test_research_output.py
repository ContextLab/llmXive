import pytest
import json
import os

class TestResearchOutputContracts:
    """Contract tests for research output artifacts."""

    def test_power_calculation_schema(self):
        """Test that power_calculation.json has the required schema."""
        path = "research/power_calculation.json"
        assert os.path.exists(path), f"Missing required file: {path}"
        
        with open(path, "r") as f:
            data = json.load(f)
        
        required_fields = [
            "effect_size",
            "alpha",
            "power",
            "num_groups",
            "n_per_group",
            "total_n"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Type checks
        assert isinstance(data["effect_size"], (int, float))
        assert isinstance(data["alpha"], (int, float))
        assert isinstance(data["power"], (int, float))
        assert isinstance(data["num_groups"], int)
        assert isinstance(data["n_per_group"], int)
        assert isinstance(data["total_n"], int)
        
        # Value constraints
        assert data["effect_size"] > 0
        assert 0 < data["alpha"] < 1
        assert 0 < data["power"] < 1
        assert data["num_groups"] >= 2
        assert data["total_n"] == data["n_per_group"] * data["num_groups"]

    def test_research_md_content(self):
        """Test that research.md contains required sections and table."""
        path = "code/research/research.md"
        assert os.path.exists(path), f"Missing required file: {path}"
        
        with open(path, "r") as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "Literature Review",
            "Lee & See",
            "Langer",
            "Power Analysis",
            "Effect Size",
            "Alpha",
            "Target Power",
            "Required N",
            "Calculated N"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"
        
        # Check for table with required columns
        assert "Effect Size (f)" in content
        assert "Alpha" in content
        assert "Target Power" in content
        assert "Required N" in content or "n_per_group" in content
        assert "Calculated N" in content or "total_n" in content

    def test_validation_report_exists(self):
        """Test that validation_report.json exists (from T000)."""
        path = "research/validation_report.json"
        assert os.path.exists(path), f"Missing required file: {path}"
        
        with open(path, "r") as f:
            data = json.load(f)
        
        # Check for expected structure
        assert "Lee & See (2004)" in str(data) or "Lee" in str(data)
        assert "Langer (1975)" in str(data) or "Langer" in str(data)
        assert "title_overlap" in str(data).lower() or "overlap" in str(data).lower()