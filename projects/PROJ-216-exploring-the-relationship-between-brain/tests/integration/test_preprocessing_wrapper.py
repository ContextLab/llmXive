"""
Integration test for T017d: Execute Preprocessing on Real Data.

This test verifies that the preprocessing wrapper script:
1. Runs without crashing.
2. Produces the required `data/processed/preprocessing_stats.json` file.
3. The JSON file contains the required `total_subjects` key.

Note: This test is designed to run in the CI environment where real data
might be mocked via the --mock-input flag or where the download log exists.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from run_preprocessing import run_preprocessing_wrapper

class TestPreprocessingWrapper:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for input, output, and atlas."""
        temp_base = tempfile.mkdtemp()
        input_dir = Path(temp_base) / "raw"
        output_dir = Path(temp_base) / "interim"
        atlas_dir = Path(temp_base) / "atlas"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        atlas_dir.mkdir(parents=True)
        
        yield {
            "input": input_dir,
            "output": output_dir,
            "atlas": atlas_dir
        }
        
        shutil.rmtree(temp_base)

    def test_wrapper_creates_stats_file(self, temp_dirs):
        """
        Test that the wrapper creates the stats file even if no subjects are found.
        In a real run, it would process subjects, but here we verify the file creation logic.
        """
        # Create a mock download log to simulate T015b having run
        download_log_path = temp_dirs["input"].parent / "download_log.json"
        mock_subjects = [
            {"id": "subj_001", "fluid_intelligence_score": 0.85, "age": 25, "gender": "M"},
            {"id": "subj_002", "fluid_intelligence_score": 0.72, "age": 30, "gender": "F"}
        ]
        
        with open(download_log_path, 'w') as f:
            json.dump({"subjects": mock_subjects}, f)

        # Run the wrapper with sample_size=1
        stats = run_preprocessing_wrapper(
            input_dir=temp_dirs["input"],
            output_dir=temp_dirs["output"],
            atlas_dir=temp_dirs["atlas"],
            sample_size=1
        )

        # Verify the stats dictionary structure
        assert "total_subjects" in stats
        assert "processed_successfully" in stats
        assert "failed" in stats
        assert "subjects" in stats

        # Verify the file was written
        stats_file = temp_dirs["output"] / "preprocessing_stats.json"
        assert stats_file.exists(), "preprocessing_stats.json was not created"

        # Verify file content matches stats
        with open(stats_file, 'r') as f:
            file_stats = json.load(f)
        
        assert file_stats["total_subjects"] == stats["total_subjects"]
        # Note: processed_successfully might be 0 if preprocessing fails due to missing FSL,
        # but the file must exist and have the correct schema.

    def test_wrapper_with_mock_input(self, temp_dirs):
        """Test the wrapper using the --mock-input path logic."""
        mock_subjects_file = temp_dirs["input"] / "mock_subjects.json"
        mock_subjects = [
            {"id": "mock_subj_001", "fluid_intelligence_score": 0.90}
        ]
        with open(mock_subjects_file, 'w') as f:
            json.dump({"subjects": mock_subjects}, f)

        stats = run_preprocessing_wrapper(
            input_dir=temp_dirs["input"],
            output_dir=temp_dirs["output"],
            atlas_dir=temp_dirs["atlas"],
            sample_size=1,
            mock_input=mock_subjects_file
        )

        assert stats["total_subjects"] == 1
        assert (temp_dirs["output"] / "preprocessing_stats.json").exists()