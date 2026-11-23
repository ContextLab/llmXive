"""
Unit tests for FDR correction module.
"""
import pytest
import numpy as np
import json
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models.fdr_correction import apply_fdr_to_results

def test_fdr_correction_basic():
    """Test basic FDR correction with known p-values."""
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Create mock results with known p-values
        # 5 hypotheses: 0.01, 0.02, 0.04, 0.10, 0.20
        # With FDR (alpha=0.05), we expect the first few to be rejected
        mock_data = {
            'results': [
                {'category': 'plot', 'p_value': 0.01, 'accuracy': 0.65},
                {'category': 'character', 'p_value': 0.02, 'accuracy': 0.60},
                {'category': 'theme', 'p_value': 0.04, 'accuracy': 0.58},
                {'category': 'setting', 'p_value': 0.10, 'accuracy': 0.52},
                {'category': 'misc', 'p_value': 0.20, 'accuracy': 0.50}
            ]
        }
        json.dump(mock_data, f)
        input_path = f.name

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out_f:
            output_path = out_f.name

        result = apply_fdr_to_results(input_path, output_path)

        # Verify output structure
        assert 'results' in result
        assert len(result['results']) == 5
        assert 'fdr_rejected' in result['results'][0]
        assert 'fdr_corrected_p_value' in result['results'][0]

        # Check that corrected p-values are monotonic and >= original
        for i, entry in enumerate(result['results']):
            assert entry['fdr_corrected_p_value'] >= mock_data['results'][i]['p_value']
        
        # Verify at least the first one is rejected (p=0.01 should survive FDR)
        assert result['results'][0]['fdr_rejected'] is True
        
        # Verify the last one is likely not rejected (p=0.20)
        assert result['results'][4]['fdr_rejected'] is False

    finally:
        os.unlink(input_path)
        if 'output_path' in locals():
            os.unlink(output_path)

def test_fdr_correction_single_entry():
    """Test FDR with a single entry."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        mock_data = {
            'category': 'plot',
            'p_value': 0.03,
            'accuracy': 0.65
        }
        json.dump(mock_data, f)
        input_path = f.name

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out_f:
            output_path = out_f.name

        result = apply_fdr_to_results(input_path, output_path)

        assert len(result['results']) == 1
        assert result['results'][0]['fdr_rejected'] is True # 0.03 < 0.05

    finally:
        os.unlink(input_path)
        if 'output_path' in locals():
            os.unlink(output_path)

def test_fdr_correction_missing_pvalue():
    """Test handling of entries missing p-values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        mock_data = {
            'results': [
                {'category': 'plot', 'p_value': 0.01},
                {'category': 'character'}, # Missing p_value
                {'category': 'theme', 'p_value': 0.04}
            ]
        }
        json.dump(mock_data, f)
        input_path = f.name

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out_f:
            output_path = out_f.name

        result = apply_fdr_to_results(input_path, output_path)

        # Should have 2 entries, not 3
        assert len(result['results']) == 2
        # The missing one should be skipped

    finally:
        os.unlink(input_path)
        if 'output_path' in locals():
            os.unlink(output_path)

def test_fdr_correction_file_not_found():
    """Test error handling for missing input file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'nonexistent.json')
        output_path = os.path.join(tmpdir, 'output.json')
        
        with pytest.raises(FileNotFoundError):
            apply_fdr_to_results(input_path, output_path)
