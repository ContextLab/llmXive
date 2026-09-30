"""
Unit tests for the synthetic test data generator.

These tests verify that:
1. The script requires --test-mode flag
2. The script generates valid CSV output
3. The manifest file is created with correct structure
4. The file hash is correctly calculated
"""
import os
import sys
import csv
import subprocess
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
CODE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(CODE_DIR))

from generate_synthetic_test_data import generate_synthetic_dataset, hash_file_content, write_test_artifacts_manifest

class TestSyntheticDataGeneration:
    
    def test_requires_test_mode_flag(self):
        """Verify the script fails without --test-mode flag."""
        result = subprocess.run(
            [sys.executable, str(CODE_DIR / "generate_synthetic_test_data.py")],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "--test-mode" in result.stderr or "REQUIRED" in result.stderr
    
    def test_generates_synthetic_dataset_structure(self):
        """Verify the generated dataset has the correct structure."""
        data = generate_synthetic_dataset(n_subjects=2, n_trials=2, n_samples=10)
        
        assert len(data) == 2 * 2 * 10  # 40 rows
        assert isinstance(data, list)
        assert isinstance(data[0], dict)
        
        # Check required keys
        required_keys = {"subject_id", "trial_id", "timestamp", "pupil_diameter", "x", "y"}
        assert set(data[0].keys()) == required_keys
    
    def test_synthetic_data_values(self):
        """Verify synthetic data has reasonable values."""
        data = generate_synthetic_dataset(n_subjects=1, n_trials=1, n_samples=100)
        
        timestamps = [row["timestamp"] for row in data]
        assert all(0 <= t <= 1000 for t in timestamps)  # 0 to 1000ms
        
        pupil_diameters = [row["pupil_diameter"] for row in data if not (isinstance(row["pupil_diameter"], float) and str(row["pupil_diameter"]) == "nan")]
        assert all(3.0 <= p <= 5.0 for p in pupil_diameters)  # Reasonable pupil size
    
    def test_hash_file_content(self):
        """Verify hash calculation works correctly."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            hash1 = hash_file_content(tmp_path)
            hash2 = hash_file_content(tmp_path)
            
            assert len(hash1) == 64  # SHA-256 hex length
            assert hash1 == hash2  # Deterministic
            
            # Verify different content produces different hash
            with tempfile.NamedTemporaryFile(delete=False) as tmp2:
                tmp2.write(b"different content")
                tmp_path2 = Path(tmp2.name)
            
            try:
                hash3 = hash_file_content(tmp_path2)
                assert hash1 != hash3
            finally:
                os.unlink(tmp_path2)
        finally:
            os.unlink(tmp_path)
    
    def test_write_test_artifacts_manifest(self):
        """Verify manifest file is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            synthetic_file = tmp_path / "test.csv"
            manifest_file = tmp_path / "manifest.yaml"
            
            # Create dummy synthetic file
            synthetic_file.write_text("col1,col2\n1,2\n")
            
            config = {"test": "config"}
            write_test_artifacts_manifest(manifest_file, synthetic_file, config)
            
            assert manifest_file.exists()
            content = manifest_file.read_text()
            
            assert "artifact_type" in content
            assert "file_hash" in content
            assert "generated_at" in content
            assert "purpose" in content
            assert "unit_testing_only" in content
    
    def test_full_script_execution(self):
        """Test the full script execution with --test-mode flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data" / "raw"
            state_dir = tmp_path / "state"
            data_dir.mkdir(parents=True)
            state_dir.mkdir(parents=True)
            
            # Create a temporary code directory structure
            test_code_dir = tmp_path / "code"
            test_code_dir.mkdir()
            
            # Copy the script to temp location
            script_path = test_code_dir / "generate_synthetic_test_data.py"
            script_path.write_text((CODE_DIR / "generate_synthetic_test_data.py").read_text())
            
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path), "--test-mode", 
                 "--n-subjects", "1", "--n-trials", "1", "--n-samples", "10"],
                capture_output=True,
                text=True,
                cwd=str(test_code_dir)
            )
            
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            
            # Verify outputs
            csv_file = data_dir / "synthetic_test_data.csv"
            manifest_file = state_dir / "test_artifacts.yaml"
            
            assert csv_file.exists()
            assert manifest_file.exists()
            
            # Verify CSV structure
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 10
                assert "subject_id" in reader.fieldnames
                assert "pupil_diameter" in reader.fieldnames
    
    def test_no_synthetic_data_in_main_pipeline(self):
        """Verify that the main pipeline does not call this script."""
        # Read main.py and check it doesn't import or call this script
        main_py = CODE_DIR / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            assert "generate_synthetic_test_data" not in content, \
                "Main pipeline should not call synthetic data generator"
            assert "synthetic" not in content.lower() or "test" in content.lower(), \
                "Main pipeline should not reference synthetic data"