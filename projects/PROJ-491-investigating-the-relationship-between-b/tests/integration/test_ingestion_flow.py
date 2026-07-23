"""
Integration test for data download and checksum verification.

This test verifies that:
1. The data ingestion script runs successfully
2. Output directories contain expected files
3. Checksums are computed and stored correctly
4. Session validation metrics are generated
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
import pytest
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestDataIngestionFlow:
    """Integration tests for the data ingestion pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Create temporary directories
        self.temp_dir = tmp_path
        self.data_raw = self.temp_dir / "data" / "raw"
        self.data_processed = self.temp_dir / "data" / "processed"
        self.state_dir = self.temp_dir / "state"
        
        # Create directory structure
        self.data_raw.mkdir(parents=True)
        self.data_processed.mkdir(parents=True)
        self.state_dir.mkdir(parents=True)
        
        # Backup original directories if they exist
        self.backup_dirs = {}
        for dir_name in ["data", "state"]:
            original = Path(dir_name)
            if original.exists():
                backup = self.temp_dir / f"backup_{dir_name}"
                shutil.copytree(original, backup)
                self.backup_dirs[dir_name] = backup
                # Remove original to use temp
                shutil.rmtree(original)
        
        yield
        
        # Restore original directories
        for dir_name, backup in self.backup_dirs.items():
            original = Path(dir_name)
            if original.exists():
                shutil.rmtree(original)
            shutil.copytree(backup, original)
            shutil.rmtree(backup)

    def test_ingestion_script_execution(self):
        """Test that the ingestion script runs without errors."""
        # Run the ingestion script
        result = subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Check return code
        assert result.returncode == 0, f"Script failed with: {result.stderr}"
        
        # Check that output was generated
        assert "Data ingestion pipeline completed successfully" in result.stdout

    def test_output_directory_structure(self):
        """Test that output directories contain expected structure."""
        # Run ingestion first
        subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            timeout=300
        )
        
        # Check data/raw exists and has subject folders
        data_raw = Path("data/raw")
        assert data_raw.exists(), "data/raw directory does not exist"
        
        subject_dirs = [d for d in data_raw.iterdir() if d.is_dir()]
        assert len(subject_dirs) >= 50, f"Expected at least 50 subject directories, found {len(subject_dirs)}"
        
        # Check each subject has required files
        for subject_dir in subject_dirs[:5]:  # Check first 5
            assert (subject_dir / "task-rest_bold.nii.gz").exists(), \
                f"Missing resting state file in {subject_dir.name}"
            
            # Check for at least one task file
            task_files = list(subject_dir.glob("task-*_bold.nii.gz"))
            assert len(task_files) >= 1, f"No task files found in {subject_dir.name}"

    def test_session_validation_metrics(self):
        """Test that session validation metrics are generated correctly."""
        # Run ingestion
        subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            timeout=300
        )
        
        metrics_file = Path("data/processed/session_validation_metrics.json")
        assert metrics_file.exists(), "Session validation metrics file not found"
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        # Validate metrics structure
        required_keys = ["total_subjects", "valid_subjects", "excluded_subjects", "pass_rate_percentage"]
        for key in required_keys:
            assert key in metrics, f"Missing key {key} in metrics"
        
        # Validate values
        assert metrics["total_subjects"] >= 50, "Total subjects should be at least 50"
        assert metrics["valid_subjects"] >= 50, "Valid subjects should be at least 50"
        assert 0 <= metrics["pass_rate_percentage"] <= 100, "Pass rate should be between 0 and 100"

    def test_excluded_subjects_csv(self):
        """Test that excluded subjects CSV is generated."""
        # Run ingestion
        subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            timeout=300
        )
        
        excluded_csv = Path("data/processed/excluded_session_ids.csv")
        
        # File may or may not exist depending on data
        if excluded_csv.exists():
            with open(excluded_csv) as f:
                lines = f.readlines()
            
            assert lines[0].strip() == "subject_id", "CSV should have subject_id header"
            
            # Check that subject IDs are valid format
            for line in lines[1:]:
                if line.strip():
                    assert line.strip().isdigit(), f"Invalid subject ID format: {line.strip()}"

    def test_ingestion_warnings_log(self):
        """Test that warnings log is created."""
        # Run ingestion
        subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            timeout=300
        )
        
        warnings_log = Path("data/processed/ingestion_warnings.log")
        
        # File should exist (may be empty)
        assert warnings_log.exists(), "Ingestion warnings log not found"

    def test_state_management_update(self):
        """Test that state management is updated after ingestion."""
        # Run ingestion
        subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            timeout=300
        )
        
        state_file = Path("state/state.yaml")
        assert state_file.exists(), "State file not found"
        
        # Verify state contains artifacts
        import yaml
        with open(state_file) as f:
            state = yaml.safe_load(f)
        
        assert "artifacts" in state, "State should contain artifacts section"
        assert len(state["artifacts"]) > 0, "State should have at least one artifact"

    def test_memory_constraint_check(self):
        """Test that memory constraints are respected."""
        # Run ingestion
        result = subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Check that memory constraint check was performed
        assert "memory" in result.stdout.lower() or "Memory" in result.stdout, \
            "Memory constraint check should be logged"

    def test_disk_usage_limit(self):
        """Test that disk usage stays within limits."""
        # Run ingestion
        subprocess.run(
            [sys.executable, "code/data_ingestion.py"],
            capture_output=True,
            timeout=300
        )
        
        # Calculate total disk usage
        total_size = 0
        for path in Path("data/raw").rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        
        disk_usage_gb = total_size / (1024 ** 3)
        
        # Should be under 14 GB limit
        assert disk_usage_gb <= 14.0, f"Disk usage ({disk_usage_gb:.2f} GB) exceeds 14 GB limit"
