"""
Unit tests for merge_scaling_results.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.merge_scaling_results import load_w0_results, load_scaling_fits, merge_results, write_merged_results

def test_load_w0_results_sets_delocalized_flag():
    """Test that W=0 results get is_delocalized=True and xi=None."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"disorder_width": 0.0, "xi": 10.0, "uncertainty": 1.0}], f)
        temp_path = f.name
    
    try:
        results = load_w0_results(temp_path)
        assert len(results) == 1
        assert results[0]['is_delocalized'] is True
        assert results[0]['xi'] is None
        assert results[0]['uncertainty'] is None
    finally:
        os.unlink(temp_path)

def test_load_scaling_fits_filters_w0():
    """Test that W=0 entries are filtered out from scaling fits."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([
            {"disorder_width": 1.0, "xi": 5.0, "uncertainty": 0.5},
            {"disorder_width": 0.0, "xi": 100.0, "uncertainty": 10.0} # Should be filtered
        ], f)
        temp_path = f.name
    
    try:
        results = load_scaling_fits(temp_path)
        assert len(results) == 1
        assert results[0]['disorder_width'] == 1.0
        assert results[0]['is_delocalized'] is False
    finally:
        os.unlink(temp_path)

def test_merge_results_combines_lists():
    """Test that merge_results correctly combines W>0 and W=0 lists."""
    w0 = [{"disorder_width": 0.0, "xi": None, "uncertainty": None, "is_delocalized": True}]
    fits = [{"disorder_width": 1.0, "xi": 5.0, "uncertainty": 0.5, "is_delocalized": False}]
    
    merged = merge_results(w0, fits)
    
    assert len(merged) == 2
    # Check order: scaling fits first, then W=0
    assert merged[0]['disorder_width'] == 1.0
    assert merged[1]['disorder_width'] == 0.0
    assert merged[1]['is_delocalized'] is True

def test_write_merged_results_creates_file():
    """Test that write_merged_results creates the output file."""
    merged = [{"disorder_width": 1.0, "xi": 5.0, "is_delocalized": False}]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_output.json')
        write_merged_results(merged, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]['disorder_width'] == 1.0