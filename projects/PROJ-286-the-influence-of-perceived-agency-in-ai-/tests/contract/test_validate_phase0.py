import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.research.validate_phase0 import (
    validate_power_calculation_json,
    validate_citations_json,
    validate_citation_log,
    validate_research_md
)

class TestValidatePowerCalculationJson:
    def test_valid_power_calculation(self):
        data = {
            "results": {
                "sample_size": 128,
                "effect_size": 0.25,
                "alpha": 0.05,
                "power": 0.80
            }
        }
        assert validate_power_calculation_json(data) is True

    def test_missing_results_key(self):
        data = {"other_key": "value"}
        assert validate_power_calculation_json(data) is False

    def test_missing_sample_size(self):
        data = {
            "results": {
                "effect_size": 0.25,
                "alpha": 0.05,
                "power": 0.80
            }
        }
        assert validate_power_calculation_json(data) is False

    def test_invalid_sample_size_type(self):
        data = {
            "results": {
                "sample_size": "not_a_number",
                "effect_size": 0.25,
                "alpha": 0.05,
                "power": 0.80
            }
        }
        assert validate_power_calculation_json(data) is False

class TestValidateCitationsJson:
    def test_valid_citations(self):
        data = [
            {
                "title": "Trust in Automation",
                "doi": "10.1234/test",
                "overlap_score": 0.85,
                "status": "valid"
            }
        ]
        assert validate_citations_json(data) is True

    def test_empty_list(self):
        data = []
        assert validate_citations_json(data) is True

    def test_not_a_list(self):
        data = {"key": "value"}
        assert validate_citations_json(data) is False

    def test_missing_required_key(self):
        data = [
            {
                "title": "Test",
                "doi": "10.1234/test",
                "overlap_score": 0.85
                # missing status
            }
        ]
        assert validate_citations_json(data) is False

    def test_invalid_status(self):
        data = [
            {
                "title": "Test",
                "doi": "10.1234/test",
                "overlap_score": 0.85,
                "status": "unknown_status"
            }
        ]
        assert validate_citations_json(data) is False

class TestValidateCitationLog:
    def test_valid_log(self):
        content = """
        # Citation Verification Log
        
        | Citation | Status |
        |----------|--------|
        | Lee & See (2004) | status = valid |
        | Langer (1975) | status = valid |
        """
        assert validate_citation_log(content) is True

    def test_no_status_line(self):
        content = """
        # Citation Verification Log
        
        No status lines here.
        """
        assert validate_citation_log(content) is False

class TestValidateResearchMd:
    def test_valid_research_md(self):
        content = """
        # Research Report
        
        | Effect Size | Alpha | Target Power | Required N | Calculated N |
        |-------------|-------|--------------|------------|--------------|
        | 0.25        | 0.05  | 0.80         | 128        | 128          |
        
        See [power_report.md](power_report.md) for details.
        """
        data = {"results": {"sample_size": 128}}
        assert validate_research_md(content, data) is True

    def test_missing_header(self):
        content = """
        # Research Report
        
        | Other | Table |
        |-------|-------|
        | 1     | 2     |
        """
        data = {"results": {"sample_size": 128}}
        assert validate_research_md(content, data) is False

    def test_missing_power_report_reference(self):
        content = """
        # Research Report
        
        | Effect Size | Alpha | Target Power | Required N | Calculated N |
        |-------------|-------|--------------|------------|--------------|
        | 0.25        | 0.05  | 0.80         | 128        | 128          |
        """
        data = {"results": {"sample_size": 128}}
        assert validate_research_md(content, data) is False
