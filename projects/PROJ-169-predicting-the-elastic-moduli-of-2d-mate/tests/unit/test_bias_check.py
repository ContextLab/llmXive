"""
Unit tests for the bias check module (T012).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ingest.bias_check import (
    ExclusionReason,
    BiasReport,
    load_exclusion_log,
    analyze_exclusion_bias,
    write_bias_report,
    main
)
from utils.config import Config

class TestExclusionReason:
    def test_creation(self):
        exc = ExclusionReason(
            material_id="mp-123",
            reason_code="MISSING_TENSOR",
            details="Tensor has NaN values",
            family="Graphite"
        )
        assert exc.material_id == "mp-123"
        assert exc.reason_code == "MISSING_TENSOR"
        assert exc.family == "Graphite"

class TestLoadExclusionLog:
    def test_load_valid_log(self, tmp_path):
        log_file = tmp_path / "filter_exclusions.log"
        data = [
            {"material_id": "mp-1", "reason": "MISSING_TENSOR", "details": "N/A", "family": "FamilyA"},
            {"material_id": "mp-2", "reason": "NOT_2D", "details": "3D structure", "family": "FamilyB"}
        ]
        with open(log_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        
        exclusions = load_exclusion_log(tmp_path)
        
        assert len(exclusions) == 2
        assert exclusions[0].material_id == "mp-1"
        assert exclusions[0].reason_code == "MISSING_TENSOR"
        assert exclusions[1].material_id == "mp-2"
        assert exclusions[1].reason_code == "NOT_2D"

    def test_missing_log_file(self, tmp_path):
        # Log file does not exist
        exclusions = load_exclusion_log(tmp_path)
        assert len(exclusions) == 0

    def test_invalid_json_line(self, tmp_path):
        log_file = tmp_path / "filter_exclusions.log"
        with open(log_file, 'w') as f:
            f.write("not valid json\n")
            f.write('{"material_id": "mp-1", "reason": "MISSING_TENSOR", "details": "N/A", "family": "Fam"}\n')
        
        exclusions = load_exclusion_log(tmp_path)
        # Should skip the invalid line and parse the valid one
        assert len(exclusions) == 1
        assert exclusions[0].material_id == "mp-1"

class TestAnalyzeExclusionBias:
    def test_analyze_basic(self):
        exclusions = [
            ExclusionReason("mp-1", "MISSING_TENSOR", "", "FamilyA"),
            ExclusionReason("mp-2", "MISSING_TENSOR", "", "FamilyA"),
            ExclusionReason("mp-3", "NOT_2D", "", "FamilyB"),
        ]
        
        report = analyze_exclusion_bias(exclusions, small_family_threshold=2)
        
        assert report.total_excluded == 3
        assert report.reason_counts["MISSING_TENSOR"] == 2
        assert report.reason_counts["NOT_2D"] == 1
        assert report.family_distribution["FamilyA"] == 2
        assert report.family_distribution["FamilyB"] == 1
        # FamilyB has 1 exclusion, which is < 2 (threshold), so it should be flagged
        assert "FamilyB" in report.flagged_families
        # FamilyA has 2, which is not < 2, so not flagged
        assert "FamilyA" not in report.flagged_families

    def test_empty_exclusions(self):
        report = analyze_exclusion_bias([], small_family_threshold=5)
        assert report.total_excluded == 0
        assert report.reason_counts == {}
        assert report.flagged_families == []

class TestWriteBiasReport:
    def test_write_report(self, tmp_path):
        report = BiasReport(
            total_excluded=10,
            reason_counts={"MISSING": 5},
            family_distribution={"Fam1": 5},
            small_family_threshold=2,
            flagged_families=[],
            report_path=""
        )
        
        path = write_bias_report(report, tmp_path)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            data = json.load(f)
        assert data["total_excluded"] == 10
        assert data["report_path"] == path

class TestMain:
    def test_main_with_exclusions(self, tmp_path, caplog):
        # Setup mock config
        config = Config()
        config.data_dir = str(tmp_path)
        
        # Create logs dir and fake exclusion log
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "filter_exclusions.log"
        with open(log_file, 'w') as f:
            f.write('{"material_id": "mp-1", "reason": "MISSING_TENSOR", "details": "N/A", "family": "Fam1"}\n')
        
        # Run main
        report_path = main(config)
        
        assert report_path is not None
        assert os.path.exists(report_path)
        
        # Verify report content
        with open(report_path, 'r') as f:
            data = json.load(f)
        assert data["total_excluded"] == 1
        assert data["reason_counts"]["MISSING_TENSOR"] == 1

    def test_main_without_exclusions(self, tmp_path, caplog):
        config = Config()
        config.data_dir = str(tmp_path)
        
        # No logs dir or log file
        report_path = main(config)
        
        assert report_path is not None
        with open(report_path, 'r') as f:
            data = json.load(f)
        assert data["total_excluded"] == 0