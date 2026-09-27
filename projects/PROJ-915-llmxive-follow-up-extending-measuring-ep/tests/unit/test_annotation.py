import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the module under test
# We assume the module is 'annotation' in the code directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from annotation import compute_correlations, DataFlowError

def test_compute_correlations_valid_data():
    """Test that compute_correlations correctly calculates Pearson/Spearman on valid data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create mock features
        features_path = tmp_path / "features.csv"
        features_df = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
            'modal_freq': [0.1, 0.5, 0.8, 0.2, 0.9], # Increasing trend
            'imperative_ratio': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        features_df.to_csv(features_path, index=False)

        # Create mock annotations (perfect correlation with modal_freq)
        annotations_path = tmp_path / "annotations.csv"
        annotations_df = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
            'rater_id': ['r1', 'r1', 'r1', 'r1', 'r1'],
            'authority_density_score': [1.0, 2.0, 3.0, 4.0, 5.0] # Perfect linear match
        })
        annotations_df.to_csv(annotations_path, index=False)

        output_path = tmp_path / "result.json"

        # Run function
        result = compute_correlations(
            features_path=str(features_path),
            annotations_path=str(annotations_path),
            output_path=str(output_path)
        )

        # Verify output file exists
        assert output_path.exists()
        
        # Verify result content
        assert 'correlation_coefficient' in result
        # With perfect linear correlation, Pearson should be 1.0
        assert abs(result['correlation_coefficient']['pearson'] - 1.0) < 1e-6
        assert abs(result['correlation_coefficient']['spearman'] - 1.0) < 1e-6
        assert result['sample_size'] == 5

def test_compute_correlations_missing_file():
    """Test that the function raises DataFlowError if input files are missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        output_path = tmp_path / "result.json"

        with pytest.raises(DataFlowError):
            compute_correlations(
                features_path=str(tmp_path / "missing.csv"),
                annotations_path=str(tmp_path / "missing.csv"),
                output_path=str(output_path)
            )

def test_compute_correlations_no_match():
    """Test that the function raises DataFlowError if prompt IDs do not match."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        features_path = tmp_path / "features.csv"
        pd.DataFrame({'prompt_id': ['p1', 'p2'], 'modal_freq': [1.0, 2.0]}).to_csv(features_path, index=False)
        
        annotations_path = tmp_path / "annotations.csv"
        pd.DataFrame({
            'prompt_id': ['p3', 'p4'],
            'rater_id': ['r1', 'r1'],
            'authority_density_score': [1.0, 2.0]
        }).to_csv(annotations_path, index=False)
        
        output_path = tmp_path / "result.json"

        with pytest.raises(DataFlowError):
            compute_correlations(
                features_path=str(features_path),
                annotations_path=str(annotations_path),
                output_path=str(output_path)
            )