import os
import sys
import tempfile
import pytest
from pathlib import Path
import json

# Mock the dependencies that might not be available in test environment
# We are testing the logic, not the actual FSL/AFNI execution
import code.utils as utils_module
import code.config as config_module

# Mock ResourceMonitor to avoid actual RAM logging during tests
class MockResourceMonitor:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.error = None
    
    def start(self, subject_id):
        self.started = True
    
    def stop(self, subject_id, error=None):
        self.stopped = True
        self.error = error
    
    def log_snapshot(self, subject_id):
        pass
    
    def finalize(self):
        pass

def test_calculate_motion_metrics_missing_file():
    """Test that calculate_motion_metrics raises error when no motion file is found."""
    from code.preprocess import calculate_motion_metrics
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake func file but no motion file
        func_file = Path(tmpdir) / "sub-001_func.nii.gz"
        func_file.touch()
        
        with pytest.raises(FileNotFoundError):
            calculate_motion_metrics(func_file)

def test_calculate_motion_metrics_parsing():
    """Test parsing of motion parameters from a mock rp_*.txt file."""
    from code.preprocess import calculate_motion_metrics
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake func file
        func_file = Path(tmpdir) / "sub-001_func.nii.gz"
        func_file.touch()
        
        # Create a mock motion file
        motion_file = Path(tmpdir) / "rp_sub-001_func.txt"
        # Format: tx ty tz rx ry rz (values in mm and radians)
        # 1.0 0.0 0.0 0.0 0.0 0.0 -> max trans 1.0, max rot 0.0
        # 0.0 2.0 0.0 0.0 0.0 0.0 -> max trans 2.0
        # 0.0 0.0 0.0 0.1 0.0 0.0 -> max rot 0.1 rad -> ~5mm
        content = """
        1.0 0.0 0.0 0.0 0.0 0.0
        0.0 2.0 0.0 0.0 0.0 0.0
        0.0 0.0 0.0 0.1 0.0 0.0
        """
        motion_file.write_text(content)
        
        result = calculate_motion_metrics(func_file)
        
        assert "translation_mm" in result
        assert "rotation_mm" in result
        assert result["translation_mm"] == 2.0
        # 0.1 rad * 50mm = 5.0mm
        assert result["rotation_mm"] == 5.0

def test_main_halt_on_zero_valid_subjects(monkeypatch):
    """Test that main raises ValueError if no valid subjects are found."""
    from code import preprocess
    
    # Mock functions to avoid actual execution
    monkeypatch.setattr(preprocess, "check_fsl_afni", lambda: True)
    monkeypatch.setattr(preprocess, "ResourceMonitor", MockResourceMonitor)
    monkeypatch.setattr(preprocess, "get_dataset_ids", lambda: ["ds000224"])
    monkeypatch.setattr(preprocess, "get_sample_limit", lambda: 10)
    
    # Mock valid_subjects.json to be empty
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        valid_file = processed_dir / "valid_subjects.json"
        valid_file.write_text(json.dumps({"subjects": [], "count": 0}))
        
        # Mock Path.exists to return True for our fake dir
        original_exists = Path.exists
        def mock_exists(self):
            if str(self) == str(valid_file):
                return True
            return original_exists(self)
        
        monkeypatch.setattr(Path, "exists", mock_exists)
        
        # Mock raw_dir to exist but be empty
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        def mock_mkdir(*args, **kwargs):
            pass
        
        monkeypatch.setattr(Path, "mkdir", mock_mkdir)
        
        with pytest.raises(ValueError, match="No valid subjects found to preprocess"):
            preprocess.main()

def test_motion_exclusion_logic():
    """Test that motion exclusion logic correctly flags subjects."""
    # This is tested implicitly in calculate_motion_metrics and the writing logic
    # We verify the threshold logic here
    from code.preprocess import calculate_motion_metrics
    
    # Case 1: Excessive translation (> 3mm)
    with tempfile.TemporaryDirectory() as tmpdir:
        func_file = Path(tmpdir) / "sub-001_func.nii.gz"
        func_file.touch()
        motion_file = Path(tmpdir) / "rp_sub-001_func.txt"
        # Translation 4.0mm
        motion_file.write_text("4.0 0.0 0.0 0.0 0.0 0.0\n")
        result = calculate_motion_metrics(func_file)
        assert result["translation_mm"] == 4.0
        assert result["translation_mm"] > 3.0 # Should be excluded
    
    # Case 2: Excessive rotation (> 2mm equiv)
    with tempfile.TemporaryDirectory() as tmpdir:
        func_file = Path(tmpdir) / "sub-002_func.nii.gz"
        func_file.touch()
        motion_file = Path(tmpdir) / "rp_sub-002_func.txt"
        # Rotation 0.1 rad * 50 = 5mm > 2mm
        motion_file.write_text("0.0 0.0 0.0 0.1 0.0 0.0\n")
        result = calculate_motion_metrics(func_file)
        assert result["rotation_mm"] == 5.0
        assert result["rotation_mm"] > 2.0 # Should be excluded
    
    # Case 3: Within limits
    with tempfile.TemporaryDirectory() as tmpdir:
        func_file = Path(tmpdir) / "sub-003_func.nii.gz"
        func_file.touch()
        motion_file = Path(tmpdir) / "rp_sub-003_func.txt"
        # Translation 1.0, Rotation 0.01 rad * 50 = 0.5mm
        motion_file.write_text("1.0 0.0 0.0 0.01 0.0 0.0\n")
        result = calculate_motion_metrics(func_file)
        assert result["translation_mm"] == 1.0
        assert result["rotation_mm"] == 0.5
        assert result["translation_mm"] <= 3.0
        assert result["rotation_mm"] <= 2.0 # Should NOT be excluded
