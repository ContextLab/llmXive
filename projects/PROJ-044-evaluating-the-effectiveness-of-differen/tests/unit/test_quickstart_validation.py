"""
Unit tests for quickstart validation functionality.
Tests edge cases and ensures validation logic works correctly.
"""

import os
import sys
import tempfile
from pathlib import Path
import json
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.validate_quickstart import (
    check_directory_structure,
    check_tree_output,
    check_requirements,
    check_precommit_config,
    verify_checksum,
    check_data_download,
    check_partition_metadata,
    check_training_logs,
    check_filtered_data,
    check_plots,
    check_summary_results,
    run_validation_checks,
    generate_report
)

class TestQuickstartValidation:
    """Tests for quickstart validation functions."""

    def test_check_directory_structure_with_valid_structure(self, tmp_path):
        """Test directory structure check with valid structure."""
        # Create a mock project structure
        required_dirs = [
            "code", "code/data", "code/training", "code/analysis",
            "tests", "tests/unit", "data", "data/raw", "results"
        ]
        
        for dir_path in required_dirs:
            (tmp_path / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Temporarily override PROJECT_ROOT
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_directory_structure()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_directory_structure_with_missing_dirs(self, tmp_path):
        """Test directory structure check with missing directories."""
        # Create partial structure
        (tmp_path / "code").mkdir(parents=True, exist_ok=True)
        # Missing other required dirs
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_directory_structure()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_tree_output_with_valid_file(self, tmp_path):
        """Test tree output check with valid file."""
        tree_file = tmp_path / "tree_output.txt"
        tree_file.write_text("code/\n  data/\n  training/\n" * 100)  # Make it large enough
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_tree_output()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_tree_output_with_empty_file(self, tmp_path):
        """Test tree output check with empty file."""
        tree_file = tmp_path / "tree_output.txt"
        tree_file.write_text("")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_tree_output()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_requirements_with_valid_file(self, tmp_path):
        """Test requirements check with valid file."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("torch\nopacus\npandas\nnumpy\nmatplotlib\nscipy\n")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_requirements()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_requirements_with_missing_packages(self, tmp_path):
        """Test requirements check with missing packages."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("torch\npandas\n")  # Missing opacus, numpy, etc.
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_requirements()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_precommit_config_with_valid_file(self, tmp_path):
        """Test pre-commit config check with valid file."""
        config_file = tmp_path / ".pre-commit-config.yaml"
        config_file.write_text("repos:\n  - repo: black\n  - repo: ruff\n  - repo: pre-commit-hooks\n")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_precommit_config()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_precommit_config_with_missing_hooks(self, tmp_path):
        """Test pre-commit config check with missing hooks."""
        config_file = tmp_path / ".pre-commit-config.yaml"
        config_file.write_text("repos:\n  - repo: black\n")  # Missing ruff, pre-commit-hooks
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_precommit_config()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_data_download_with_valid_file(self, tmp_path):
        """Test data download check with valid file."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / "femnist.parquet"
        data_file.write_bytes(b"fake parquet content" * 1000)
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_data_download()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_data_download_with_empty_file(self, tmp_path):
        """Test data download check with empty file."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / "femnist.parquet"
        data_file.write_bytes(b"")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_data_download()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_partition_metadata_with_valid_files(self, tmp_path):
        """Test partition metadata check with valid files."""
        partition_dir = tmp_path / "data" / "partitions"
        partition_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock partition files
        for i in range(3):
            (partition_dir / f"partition_femnist_{i}.json").write_text(
                json.dumps({"client_id": i, "label_distribution": {}})
            )
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_partition_metadata()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_partition_metadata_with_no_files(self, tmp_path):
        """Test partition metadata check with no files."""
        partition_dir = tmp_path / "data" / "partitions"
        partition_dir.mkdir(parents=True, exist_ok=True)
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_partition_metadata()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_training_logs_with_valid_file(self, tmp_path):
        """Test training logs check with valid file."""
        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        logs_file = results_dir / "raw_logs.csv"
        logs_file.write_text("seed,alpha,epsilon,accuracy\n1,0.1,0.5,0.85\n")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_training_logs()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_plots_with_valid_files(self, tmp_path):
        """Test plots check with valid files."""
        plots_dir = tmp_path / "results" / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock PNG files
        for i in range(3):
            (plots_dir / f"plot_{i}.png").write_bytes(b"fake png content")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_plots()
            assert result is True
        finally:
            vq.PROJECT_ROOT = original_root

    def test_check_plots_with_no_files(self, tmp_path):
        """Test plots check with no files."""
        plots_dir = tmp_path / "results" / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            result = check_plots()
            assert result is False
        finally:
            vq.PROJECT_ROOT = original_root

    def test_generate_report_creates_json(self, tmp_path):
        """Test that generate_report creates a valid JSON file."""
        results = {"Check1": "PASS", "Check2": "FAIL"}
        all_passed = False
        
        report_path = tmp_path / "test_report.json"
        
        # Temporarily override report path
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            report = generate_report(results, all_passed)
            
            assert report_path.exists()
            with open(report_path) as f:
                loaded_report = json.load(f)
            
            assert loaded_report["overall_status"] == "FAILED"
            assert "Check1" in loaded_report["checks"]
        finally:
            vq.PROJECT_ROOT = original_root

    def test_run_validation_checks_returns_dict(self, tmp_path):
        """Test that run_validation_checks returns expected structure."""
        # Create minimal valid structure
        (tmp_path / "code").mkdir(parents=True, exist_ok=True)
        (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data/raw").mkdir(parents=True, exist_ok=True)
        (tmp_path / "results").mkdir(parents=True, exist_ok=True)
        (tmp_path / "results/plots").mkdir(parents=True, exist_ok=True)
        
        # Create required files
        (tmp_path / "tree_output.txt").write_text("x" * 200)
        (tmp_path / "requirements.txt").write_text("torch\nopacus\npandas\nnumpy\nmatplotlib\nscipy\n")
        (tmp_path / ".pre-commit-config.yaml").write_text("repos:\n  - repo: black\n  - repo: ruff\n  - repo: pre-commit-hooks\n")
        (tmp_path / "data/raw/femnist.parquet").write_bytes(b"content" * 100)
        (tmp_path / "data/raw/femnist.sha256").write_text("fakechecksum")
        (tmp_path / "data/partitions").mkdir()
        (tmp_path / "results/raw_logs.csv").write_text("seed,accuracy\n1,0.9\n")
        (tmp_path / "results/filtered_data.csv").write_text("seed,accuracy\n1,0.9\n")
        (tmp_path / "results/summary.csv").write_text("seed,alpha,epsilon,accuracy\n1,0.1,0.5,0.9\n")
        (tmp_path / "results/validation_report.md").write_text("# Report")
        (tmp_path / "results/plots/test.png").write_bytes(b"fake png")
        
        import validation.validate_quickstart as vq
        original_root = vq.PROJECT_ROOT
        vq.PROJECT_ROOT = tmp_path
        
        try:
            results, all_passed = run_validation_checks()
            
            assert isinstance(results, dict)
            assert "Directory Structure" in results
            assert "overall_status" not in results  # That's in the report, not results
        finally:
            vq.PROJECT_ROOT = original_root
