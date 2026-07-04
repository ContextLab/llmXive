"""
Integration test for T026: Synthetic Dataset Generator.

This test runs the full synthetic generation pipeline and verifies:
1. Output files are created at the correct paths
2. Files contain the minimum required records (>= 10,000)
3. Both binary and continuous outcome types are present
4. Data integrity checks pass
"""
import csv
import json
import subprocess
import sys
from pathlib import Path
import pytest

class TestSyntheticPipelineIntegration:
    """Integration tests for the synthetic dataset generator."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_synthetic_generator_runs_successfully(self, project_root):
        """Test that the synthetic generator script runs without errors."""
        script_path = project_root / "code" / "src" / "audit" / "synthetic.py"
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_csv_output_exists_and_valid(self, project_root):
        """Test that CSV output file is created and contains valid data."""
        csv_path = project_root / "data" / "synthetic" / "synthetic_validation.csv"
        
        # First, ensure the file exists by running the generator
        script_path = project_root / "code" / "src" / "audit" / "synthetic.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            check=True
        )
        
        assert csv_path.exists(), "CSV output file should exist"
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Verify minimum record count
        assert len(rows) >= 10000, f"CSV must contain at least 10,000 records, got {len(rows)}"
        
        # Verify required columns
        required_columns = {
            "id", "outcome_type", "is_consistent", "reported_p_value",
            "true_p_value", "domain", "year"
        }
        assert required_columns.issubset(set(rows[0].keys()))

    def test_json_output_exists_and_valid(self, project_root):
        """Test that JSON ground truth file is created and contains valid data."""
        json_path = project_root / "data" / "synthetic" / "synthetic_ground_truth.json"
        
        # Ensure file exists
        script_path = project_root / "code" / "src" / "audit" / "synthetic.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            check=True
        )
        
        assert json_path.exists(), "JSON ground truth file should exist"
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify structure
        assert "metadata" in data
        assert "records" in data
        assert len(data["records"]) >= 10000
        
        # Verify metadata
        metadata = data["metadata"]
        assert "total_records" in metadata
        assert metadata["total_records"] >= 10000
        assert "binary_count" in metadata
        assert "continuous_count" in metadata

    def test_both_outcome_types_present(self, project_root):
        """Test that both binary and continuous outcomes are present in the dataset."""
        csv_path = project_root / "data" / "synthetic" / "synthetic_validation.csv"
        
        # Ensure file exists
        script_path = project_root / "code" / "src" / "audit" / "synthetic.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            check=True
        )
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        outcome_types = {row["outcome_type"] for row in rows}
        
        assert "binary" in outcome_types, "Binary outcomes must be present"
        assert "continuous" in outcome_types, "Continuous outcomes must be present"
        
        # Count occurrences
        binary_count = sum(1 for row in rows if row["outcome_type"] == "binary")
        continuous_count = sum(1 for row in rows if row["outcome_type"] == "continuous")
        
        # Verify both have significant representation (at least 10% each)
        total = len(rows)
        assert binary_count / total >= 0.10, "Binary outcomes should be at least 10% of dataset"
        assert continuous_count / total >= 0.10, "Continuous outcomes should be at least 10% of dataset"

    def test_data_integrity_checks(self, project_root):
        """Test basic data integrity of the generated dataset."""
        csv_path = project_root / "data" / "synthetic" / "synthetic_validation.csv"
        
        # Ensure file exists
        script_path = project_root / "code" / "src" / "audit" / "synthetic.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            check=True
        )
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check p-value ranges
        for row in rows:
            reported_p = float(row["reported_p_value"])
            true_p = float(row["true_p_value"])
            
            assert 0.0 <= reported_p <= 1.0, f"Invalid reported_p_value: {reported_p}"
            assert 0.0 <= true_p <= 1.0, f"Invalid true_p_value: {true_p}"
        
        # Check for unique IDs
        ids = [row["id"] for row in rows]
        assert len(ids) == len(set(ids)), "IDs must be unique"

    def test_file_sizes_reasonable(self, project_root):
        """Test that generated files have reasonable sizes."""
        csv_path = project_root / "data" / "synthetic" / "synthetic_validation.csv"
        json_path = project_root / "data" / "synthetic" / "synthetic_ground_truth.json"
        
        # Ensure files exist
        script_path = project_root / "code" / "src" / "audit" / "synthetic.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            check=True
        )
        
        csv_size = csv_path.stat().st_size
        json_size = json_path.stat().st_size
        
        # Files should be non-trivial (at least 1MB each for 10k records)
        assert csv_size > 1_000_000, f"CSV file too small: {csv_size} bytes"
        assert json_size > 1_000_000, f"JSON file too small: {json_size} bytes"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])