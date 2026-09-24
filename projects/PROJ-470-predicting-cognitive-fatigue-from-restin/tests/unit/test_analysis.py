"""
Unit tests for the analysis pipeline (T020).
Verifies correlation computation functionality.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in str(__import__('sys').path):
    __import__('sys').path.insert(0, str(sys_path))

from code.analysis import validate_inputs, calculate_deltas, compute_correlations


def create_test_data(temp_dir: Path):
    """Create mock test data files."""
    # Create complexity metrics
    complexity_data = {
        'participant_id': ['P001', 'P001', 'P002', 'P002', 'P003', 'P003'],
        'channel': ['Cz', 'Cz', 'Cz', 'Cz', 'Cz', 'Cz'],
        'segment_id': ['pre', 'post', 'pre', 'post', 'pre', 'post'],
        'lzc_value': [0.45, 0.42, 0.48, 0.44, 0.46, 0.43],
        'pe_value': [0.72, 0.70, 0.75, 0.73, 0.73, 0.71]
    }
    complexity_df = pd.DataFrame(complexity_data)
    complexity_path = temp_dir / "complexity_metrics.csv"
    complexity_df.to_csv(complexity_path, index=False)

    # Create fatigue scores
    fatigue_data = {
        'participant_id': ['P001', 'P002', 'P003'],
        'pre_fatigue': [2.0, 2.5, 1.8],
        'post_fatigue': [4.5, 4.0, 3.8]
    }
    fatigue_df = pd.DataFrame(fatigue_data)
    fatigue_path = temp_dir / "fatigue_scores.csv"
    fatigue_df.to_csv(fatigue_path, index=False)

    return complexity_path, fatigue_path


def test_validate_inputs_valid():
    """Test validation with valid input files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        complexity_path, fatigue_path = create_test_data(temp_dir)

        # Create a dummy delta file
        delta_path = temp_dir / "delta_scores.csv"
        pd.DataFrame({'participant_id': ['P001'], 'fatigue_delta': [1.0], 'lzc_delta': [0.0], 'pe_delta': [0.0]}).to_csv(delta_path, index=False)

        is_valid, message = validate_inputs(
            complexity_file=str(complexity_path),
            fatigue_file=str(fatigue_path),
            delta_file=str(delta_path)
        )

        assert is_valid is True
        assert "validated" in message.lower()


def test_validate_inputs_missing_file():
    """Test validation with missing input file."""
    is_valid, message = validate_inputs(
        complexity_file="nonexistent.csv",
        fatigue_file="nonexistent.csv",
        delta_file="nonexistent.csv"
    )

    assert is_valid is False
    assert "not found" in message.lower()


def test_calculate_deltas():
    """Test delta calculation logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        complexity_path, fatigue_path = create_test_data(temp_dir)

        output_path = temp_dir / "delta_scores.csv"
        delta_df = calculate_deltas(
            complexity_file=str(complexity_path),
            fatigue_file=str(fatigue_path),
            output_file=str(output_path)
        )

        assert os.path.exists(output_path)
        assert 'fatigue_delta' in delta_df.columns
        assert 'lzc_delta' in delta_df.columns
        assert 'pe_delta' in delta_df.columns
        assert len(delta_df) == 3  # 3 participants

        # Verify delta calculation (post - pre)
        assert all(delta_df['fatigue_delta'] > 0)  # All post > pre in test data


def test_compute_correlations():
    """Test correlation computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        complexity_path, fatigue_path = create_test_data(temp_dir)

        # Create delta file
        delta_path = temp_dir / "delta_scores.csv"
        delta_data = {
            'participant_id': ['P001', 'P002', 'P003'],
            'fatigue_delta': [2.5, 1.5, 2.0],
            'lzc_delta': [-0.03, -0.04, -0.03],
            'pe_delta': [-0.02, -0.02, -0.02]
        }
        pd.DataFrame(delta_data).to_csv(delta_path, index=False)

        output_path = temp_dir / "correlation_results.csv"
        corr_df = compute_correlations(
            delta_file=str(delta_path),
            complexity_file=str(complexity_path),
            output_file=str(output_path)
        )

        assert os.path.exists(output_path)
        assert 'channel' in corr_df.columns
        assert 'metric' in corr_df.columns
        assert 'correlation_type' in corr_df.columns
        assert 'coefficient' in corr_df.columns
        assert 'p_value' in corr_df.columns

        # Should have 4 correlations per channel (pearson/spearman for lzc/pe)
        # With 1 channel in test data: 4 rows
        assert len(corr_df) == 4

        # Coefficients should be between -1 and 1
        assert all(abs(corr_df['coefficient']) <= 1.0)
        assert all(corr_df['p_value'] >= 0)
        assert all(corr_df['p_value'] <= 1)