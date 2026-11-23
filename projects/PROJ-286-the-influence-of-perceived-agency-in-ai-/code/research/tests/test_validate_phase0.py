"""
Unit tests for validate_phase0.py
"""
import json
import tempfile
from pathlib import Path
import pytest
from code.research.validate_phase0 import (
    validate_power_calculation_json,
    validate_research_md,
    validate_citations_json,
    validate_citation_log
)

class TestValidatePowerCalculationJson:
    def test_valid_structure(self):
        data = {
            "params": {
                "effect_size": 0.25,
                "alpha": 0.05,
                "power": 0.80
            },
            "results": {
                "required_n": 128,
                "calculated_n": 128
            }
        }
        assert validate_power_calculation_json(data) is True

    def test_missing_params(self):
        data = {
            "results": {
                "required_n": 128,
                "calculated_n": 128
            }
        }
        assert validate_power_calculation_json(data) is False

    def test_missing_results(self):
        data = {
            "params": {
                "effect_size": 0.25,
                "alpha": 0.05,
                "power": 0.80
            }
        }
        assert validate_power_calculation_json(data) is False

    def test_missing_effect_size(self):
        data = {
            "params": {
                "alpha": 0.05,
                "power": 0.80
            },
            "results": {
                "required_n": 128,
                "calculated_n": 128
            }
        }
        assert validate_power_calculation_json(data) is False

    def test_missing_required_n(self):
        data = {
            "params": {
                "effect_size": 0.25,
                "alpha": 0.05,
                "power": 0.80
            },
            "results": {
                "calculated_n": 128
            }
        }
        assert validate_power_calculation_json(data) is False

    def test_none_input(self):
        assert validate_power_calculation_json(None) is False

class TestValidateResearchMd:
    def test_valid_research_md(self, tmp_path):
        content = """
        # Research Summary

        | Effect Size | Alpha | Target Power | Required N | Calculated N |
        | --- | --- | --- | --- | --- |
        | 0.25 | 0.05 | 0.80 | 128 | 128 |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)
        assert validate_research_md(file_path) is True

    def test_missing_header(self, tmp_path):
        content = """
        | Wrong Header |
        | --- |
        | Data |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)
        assert validate_research_md(file_path) is False

    def test_missing_data_row(self, tmp_path):
        content = """
        | Effect Size | Alpha | Target Power | Required N | Calculated N |
        | --- | --- | --- | --- | --- |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)
        assert validate_research_md(file_path) is False

    def test_missing_file(self, tmp_path):
        file_path = tmp_path / "nonexistent.md"
        assert validate_research_md(file_path) is False

class TestValidateCitationsJson:
    def test_valid_json(self, tmp_path):
        data = [{"title": "Test", "status": "valid"}]
        file_path = tmp_path / "validation_report.json"
        file_path.write_text(json.dumps(data))
        assert validate_citations_json(file_path) is True

    def test_empty_list(self, tmp_path):
        data = []
        file_path = tmp_path / "validation_report.json"
        file_path.write_text(json.dumps(data))
        assert validate_citations_json(file_path) is False

    def test_missing_file(self, tmp_path):
        file_path = tmp_path / "missing.json"
        assert validate_citations_json(file_path) is False

    def test_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not json")
        assert validate_citations_json(file_path) is False

class TestValidateCitationLog:
    def test_valid_log(self, tmp_path):
        content = "Some citation log content"
        file_path = tmp_path / "citation_log.txt"
        file_path.write_text(content)
        assert validate_citation_log(file_path) is True

    def test_empty_log(self, tmp_path):
        content = ""
        file_path = tmp_path / "citation_log.txt"
        file_path.write_text(content)
        assert validate_citation_log(file_path) is False

    def test_missing_file(self, tmp_path):
        file_path = tmp_path / "missing.txt"
        assert validate_citation_log(file_path) is False
