import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import generate_sampling_report

def test_generate_sampling_report_basic():
    """Test basic generation of sampling report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "sampling_report.csv")
        subsampling_ratios = {
            "dataset_001": 0.5,
            "dataset_002": 0.8,
            "dataset_003": 1.0
        }
        
        generate_sampling_report(subsampling_ratios, output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        
        assert len(df) == 3
        assert 'dataset_id' in df.columns
        assert 'subsampling_ratio' in df.columns
        assert 'samples_kept_pct' in df.columns
        
        assert df.loc[0, 'dataset_id'] == "dataset_001"
        assert df.loc[0, 'subsampling_ratio'] == 0.5

def test_generate_sampling_report_empty():
    """Test generation with empty ratios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "sampling_report.csv")
        subsampling_ratios = {}
        
        generate_sampling_report(subsampling_ratios, output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 0

def test_generate_sampling_report_creates_directory():
    """Test that the function creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subdir", "sampling_report.csv")
        subsampling_ratios = {"test": 0.5}
        
        generate_sampling_report(subsampling_ratios, output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 1
