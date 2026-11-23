"""
Unit tests for the Data Leakage Audit module (code/models/audit.py).
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add the project root to the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.audit import (
    extract_material_ids,
    check_leakage,
    run_audit_pipeline,
    write_leakage_report,
    ensure_dirs
)


class TestExtractMaterialIds:
    def test_extract_ids_success(self):
        """Test extraction of material IDs from a valid DataFrame."""
        df = pd.DataFrame({
            "material_id": ["M1", "M2", "M3", "M1"],
            "capacity": [1.0, 2.0, 3.0, 1.0]
        })
        ids = extract_material_ids(df)
        assert ids == {"M1", "M2", "M3"}

    def test_extract_ids_with_nan(self):
        """Test that NaN values are ignored."""
        df = pd.DataFrame({
            "material_id": ["M1", None, "M2", "M1"],
            "capacity": [1.0, 2.0, 3.0, 1.0]
        })
        ids = extract_material_ids(df)
        assert ids == {"M1", "M2"}

    def test_extract_ids_missing_column(self):
        """Test that ValueError is raised if column is missing."""
        df = pd.DataFrame({
            "id": ["M1", "M2"],
            "capacity": [1.0, 2.0]
        })
        with pytest.raises(ValueError, match="Column 'material_id' not found"):
            extract_material_ids(df, material_id_col="material_id")


class TestCheckLeakage:
    def test_no_leakage(self):
        """Test that empty list is returned when no overlap exists."""
        train_ids = {"M1", "M2", "M3"}
        test_ids = {"M4", "M5", "M6"}
        result = check_leakage(train_ids, test_ids)
        assert result == []

    def test_leakage_detected(self):
        """Test that leaking IDs are returned when overlap exists."""
        train_ids = {"M1", "M2", "M3"}
        test_ids = {"M3", "M4", "M5"}
        result = check_leakage(train_ids, test_ids)
        assert set(result) == {"M3"}
        assert len(result) == 1

    def test_full_overlap(self):
        """Test handling of full overlap."""
        train_ids = {"M1", "M2"}
        test_ids = {"M1", "M2"}
        result = check_leakage(train_ids, test_ids)
        assert set(result) == {"M1", "M2"}


class TestWriteLeakageReport:
    def test_report_content(self):
        """Test that the report is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override the global path for testing
            import models.audit as audit_module
            original_path = audit_module.LEAKAGE_REPORT_PATH
            audit_module.LEAKAGE_REPORT_PATH = Path(tmpdir) / "test_report.json"

            try:
                write_leakage_report(
                    leaking_ids=["M1", "M2"],
                    train_count=10,
                    test_count=10,
                    is_leaked=True
                )

                report_path = audit_module.LEAKAGE_REPORT_PATH
                assert report_path.exists()

                with open(report_path, 'r') as f:
                    report = json.load(f)

                assert report["status"] == "LEAKAGE_DETECTED"
                assert report["is_leaked"] is True
                assert report["leakage_count"] == 2
                assert set(report["leaking_material_ids"]) == {"M1", "M2"}
            finally:
                audit_module.LEAKAGE_REPORT_PATH = original_path


class TestRunAuditPipeline:
    def test_no_leakage_scenario(self):
        """Test the full pipeline with no leakage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create train and test files with no overlap
            train_file = Path(tmpdir) / "train.csv"
            test_file = Path(tmpdir) / "test.csv"

            train_df = pd.DataFrame({
                "material_id": ["M1", "M2", "M3"],
                "capacity": [1.0, 2.0, 3.0]
            })
            test_df = pd.DataFrame({
                "material_id": ["M4", "M5", "M6"],
                "capacity": [4.0, 5.0, 6.0]
            })

            train_df.to_csv(train_file, index=False)
            test_df.to_csv(test_file, index=False)

            result = run_audit_pipeline(str(train_file), str(test_file))
            assert result is True

    def test_leakage_scenario(self):
        """Test the full pipeline with leakage detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create train and test files with overlap
            train_file = Path(tmpdir) / "train.csv"
            test_file = Path(tmpdir) / "test.csv"

            train_df = pd.DataFrame({
                "material_id": ["M1", "M2", "M3"],
                "capacity": [1.0, 2.0, 3.0]
            })
            test_df = pd.DataFrame({
                "material_id": ["M3", "M4", "M5"],
                "capacity": [3.0, 4.0, 5.0]
            })

            train_df.to_csv(train_file, index=False)
            test_df.to_csv(test_file, index=False)

            result = run_audit_pipeline(str(train_file), str(test_file))
            assert result is False

    def test_missing_train_file(self):
        """Test handling of missing training file."""
        result = run_audit_pipeline("nonexistent_train.csv", "nonexistent_test.csv")
        assert result is False

    def test_missing_test_file(self):
        """Test handling of missing test file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            train_file = Path(tmpdir) / "train.csv"
            pd.DataFrame({"material_id": ["M1"]}).to_csv(train_file, index=False)
            
            result = run_audit_pipeline(str(train_file), "nonexistent_test.csv")
            assert result is False