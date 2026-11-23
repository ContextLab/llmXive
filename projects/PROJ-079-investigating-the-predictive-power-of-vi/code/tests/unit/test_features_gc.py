import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_gc_content

def test_calculate_gc_content_valid_fasta():
    """Test GC content calculation on a known sequence."""
    # Sequence: ACGTACGT -> 50% GC
    # Length 8
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\nACGTACGT\n")
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        assert abs(result['global_gc'] - 50.0) < 0.01
        assert result['gc_first_quartile'] == 50.0 # First 2 bases: AC -> 50%
        assert result['gc_last_quartile'] == 50.0  # Last 2 bases: GT -> 50%
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_gc_content("/nonexistent/path/file.fasta")

def test_calculate_gc_content_empty_sequence():
    """Test that ValueError is raised for empty sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\n\n")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Sequence is empty"):
            calculate_gc_content(temp_path)
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_short_sequence():
    """Test behavior on sequence shorter than window size."""
    # Sequence: ACGT (4bp) -> 50% GC
    # Windows (1kb, 5kb) should be empty
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\nACGT\n")
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        assert abs(result['global_gc'] - 50.0) < 0.01
        assert len(result['gc_window_1kb']) == 0
        assert len(result['gc_window_5kb']) == 0
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_mixed_case():
    """Test that mixed case sequences are handled correctly."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\nAcGtAcGt\n")
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        assert abs(result['global_gc'] - 50.0) < 0.01
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_with_invalid_bases():
    """Test that invalid bases (N, etc.) are ignored."""
    # ACGTNACGT -> ACGTACGT (8bp) -> 50% GC
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\nACGTNACGT\n")
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        assert abs(result['global_gc'] - 50.0) < 0.01
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_sliding_windows():
    """Test sliding window calculations."""
    # Create a sequence where GC varies
    # 10kb sequence: 5kb ATAT, 5kb GCGC
    # Global should be 50%
    # 1kb windows: first 5 should be 0%, last 5 should be 100%
    # 5kb windows: first 1 should be 0%, last 1 should be 100%
    
    seq_1 = "ATAT" * 1250 # 5000 bp
    seq_2 = "GCGC" * 1250 # 5000 bp
    full_seq = seq_1 + seq_2

    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\n")
        f.write(full_seq)
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        assert abs(result['global_gc'] - 50.0) < 0.01
        
        # 1kb windows
        # First 5000bp are AT, so 5 windows of 0%
        # Next 5000bp are GC, so 5 windows of 100%
        # Total 10 windows
        assert len(result['gc_window_1kb']) == 10
        for i in range(5):
            assert abs(result['gc_window_1kb'][i] - 0.0) < 0.01
        for i in range(5, 10):
            assert abs(result['gc_window_1kb'][i] - 100.0) < 0.01

        # 5kb windows
        # First window (0-5000): 0%
        # Second window (2500-7500): Mixed? 
        # 2500-5000 is AT, 5000-7500 is GC -> 50%
        # Third window (5000-10000): 100%
        # Wait, step is 2500.
        # Window 1: 0-5000 (AT) -> 0%
        # Window 2: 2500-7500 (2500 AT + 2500 GC) -> 50%
        # Window 3: 5000-10000 (GC) -> 100%
        assert len(result['gc_window_5kb']) == 3
        assert abs(result['gc_window_5kb'][0] - 0.0) < 0.01
        assert abs(result['gc_window_5kb'][1] - 50.0) < 0.01
        assert abs(result['gc_window_5kb'][2] - 100.0) < 0.01

    finally:
        os.unlink(temp_path)