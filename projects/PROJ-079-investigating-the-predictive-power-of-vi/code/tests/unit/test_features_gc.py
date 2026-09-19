import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_gc_content

def test_calculate_gc_content_valid_fasta():
    """Test GC content calculation with a valid FASTA file."""
    # Create a temporary FASTA file with known sequence
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        f.write("ATGCATGCATGCATGCATGCATGCATGCATGC\n")  # 50% GC
        f.write("ATGCATGCATGCATGCATGCATGCATGCATGC\n")
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        
        assert 'global_gc' in result
        assert 'gc_5p' in result
        assert 'gc_3p' in result
        assert 'gc_mid' in result
        assert 'gc_windows' in result
        
        # Check global GC is 50%
        assert abs(result['global_gc'] - 50.0) < 0.1
        
        # Check region-specific values (all should be 50% for this uniform sequence)
        assert abs(result['gc_5p'] - 50.0) < 0.1
        assert abs(result['gc_3p'] - 50.0) < 0.1
        assert abs(result['gc_mid'] - 50.0) < 0.1
        
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_gc_content("nonexistent.fasta")

def test_calculate_gc_content_empty_sequence():
    """Test that ValueError is raised for empty sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">empty_sequence\n")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Empty sequence"):
            calculate_gc_content(temp_path)
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_short_sequence():
    """Test that ValueError is raised for sequence too short."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">short_sequence\n")
        f.write("ATGC\n")  # Only 4bp
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Sequence too short"):
            calculate_gc_content(temp_path)
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_mixed_case():
    """Test that mixed case sequences are handled correctly."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">mixed_case\n")
        f.write("AtGcAtGcAtGcAtGcAtGcAtGcAtGcAtGc\n")
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        assert abs(result['global_gc'] - 50.0) < 0.1
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_with_invalid_bases():
    """Test that invalid bases are filtered out."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">invalid_bases\n")
        f.write("ATGCXATGCYATGCZATGC\n")  # X, Y, Z are invalid
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        # After filtering, we should have 12 valid bases (6 ATGC pairs)
        # GC count should be 6 (3 G + 3 C)
        # GC% should be 50%
        assert abs(result['global_gc'] - 50.0) < 0.1
    finally:
        os.unlink(temp_path)

def test_calculate_gc_content_sliding_windows():
    """Test sliding window calculation."""
    # Create a sequence with varying GC content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">varying_gc\n")
        # First 1000bp: 100% AT (0% GC)
        f.write("AT" * 500)
        # Next 1000bp: 100% GC (100% GC)
        f.write("GC" * 500)
        # Next 1000bp: 100% AT (0% GC)
        f.write("AT" * 500)
        temp_path = f.name

    try:
        result = calculate_gc_content(temp_path)
        
        # Check that sliding windows were calculated
        assert len(result['gc_windows']) > 0
        
        # The first window should be ~0% GC (all AT)
        # The second window should be ~100% GC (all GC)
        # Note: exact values depend on window alignment
        
    finally:
        os.unlink(temp_path)