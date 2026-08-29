import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import write_sample_info, enforce_sample_limit

class TestSampleInfoDeclaration:
    """
    Unit tests for T044: Explicit Sample Size Declaration.
    
    Verifies that sample_info.json is written with correct structure
    and that sampling logic is deterministic.
    """

    def setup_method(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir) / "sample_info.json"

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_write_sample_info_creates_file(self):
        """Test that write_sample_info creates the JSON file."""
        subjects = [
            {"id": "sub-01", "age": 25, "gender": "M", "fluid_intelligence_score": 10.5},
            {"id": "sub-02", "age": 30, "gender": "F", "fluid_intelligence_score": 11.2}
        ]
        
        write_sample_info(
            subjects_used=subjects,
            total_available=100,
            sampling_method="first 2 subjects",
            output_path=self.output_path
        )
        
        assert self.output_path.exists(), "sample_info.json was not created"

    def test_write_sample_info_content(self):
        """Test that the JSON content matches the required schema."""
        subjects = [
            {"id": "sub-01", "age": 25, "gender": "M", "fluid_intelligence_score": 10.5}
        ]
        
        write_sample_info(
            subjects_used=subjects,
            total_available=50,
            sampling_method="random seed 42",
            output_path=self.output_path
        )
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        # Verify required keys
        assert "subjects_used_count" in data
        assert "total_available_count" in data
        assert "sampling_method" in data
        assert "subject_ids" in data
        assert "timestamp" in data
        
        # Verify values
        assert data["subjects_used_count"] == 1
        assert data["total_available_count"] == 50
        assert data["sampling_method"] == "random seed 42"
        assert data["subject_ids"] == ["sub-01"]
        assert isinstance(data["timestamp"], str)

    def test_enforce_sample_limit_first_n(self):
        """Test that enforce_sample_limit correctly selects the first N subjects."""
        all_subs = [{"id": f"sub-{i:03d}"} for i in range(100)]
        
        selected = enforce_sample_limit(all_subs, limit=10, method="first_n")
        
        assert len(selected) == 10
        assert selected[0]["id"] == "sub-000"
        assert selected[9]["id"] == "sub-009"

    def test_enforce_sample_limit_within_limit(self):
        """Test that if available < limit, all are returned."""
        all_subs = [{"id": f"sub-{i:03d}"} for i in range(5)]
        
        selected = enforce_sample_limit(all_subs, limit=10, method="first_n")
        
        assert len(selected) == 5
        assert selected == all_subs