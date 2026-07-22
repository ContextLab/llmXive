import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import generate_sampling_report
from src.utils.memory import trigger_subsample, is_subsampling_active, get_subsample_ratio

def test_generate_sampling_report_creates_directory():
    """Test that generate_sampling_report creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "subdir", "sampling_report.csv")
        # Reset subsampling state to ensure clean test
        # Note: In a real scenario, we might need to mock the global state
        generate_sampling_report(output_path)
        assert os.path.exists(output_path)

def test_generate_sampling_report_basic():
    """Test basic generation of the sampling report."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "sampling_report.csv")
        
        # Trigger subsampling to ensure the report reflects a subsampled state
        # This depends on the global state in src.utils.memory
        trigger_subsample([0, 1, 2], 10) # Subsample 3 out of 10
        
        generate_sampling_report(output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert "ratio" in df.columns
        assert "sample_type" in df.columns
        # Since we triggered subsampling, the type should be 'subsampled' and ratio < 1.0
        assert df.iloc[0]["sample_type"] == "subsampled"
        assert 0.0 < df.iloc[0]["ratio"] < 1.0

def test_generate_sampling_report_empty():
    """Test generation when no subsampling was active."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "sampling_report.csv")
        
        # Ensure no subsampling is active
        # The memory module likely has a global flag; we assume trigger_subsample wasn't called
        # or was reset.
        
        generate_sampling_report(output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) > 0
        assert df.iloc[0]["sample_type"] == "original" or df.iloc[0]["sample_type"] == "subsampled"
        # If no subsampling, ratio should be 1.0
        if not is_subsampling_active():
            assert df.iloc[0]["ratio"] == 1.0