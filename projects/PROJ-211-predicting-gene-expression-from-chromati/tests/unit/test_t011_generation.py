"""
Unit tests for T011: Synthetic data generation and checksums.

Tests:
- Data generation produces correct file formats
- Dimensions match requirements
- Checksums are computed correctly
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils import checksum_file

class TestT011Generation:
    """Tests for synthetic data generation task T011."""
    
    def test_generate_data_creates_files(self):
        """Test that generate_data.py creates the expected output files."""
        from generate_data import main
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change directories
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Create required directories
                os.makedirs('data/raw', exist_ok=True)
                os.makedirs('logs', exist_ok=True)
                
                # Run generation
                counts_path, peaks_path = main()
                
                # Verify files exist
                assert os.path.exists(counts_path), f"Counts file not created: {counts_path}"
                assert os.path.exists(peaks_path), f"Peaks file not created: {peaks_path}"
                
            finally:
                os.chdir(original_dir)
    
    def test_counts_matrix_dimensions(self):
        """Test that counts matrix has correct dimensions."""
        from generate_data import generate_counts_matrix
        
        counts_df, peaks_df = generate_counts_matrix(
            num_genes=10000,
            num_peaks=10000,
            cell_lines=['GM12878', 'K562', 'HMEC', 'IMR90', 'HepG2'],
            seed=42
        )
        
        assert counts_df.shape[0] == 10000, f"Expected 10000 genes, got {counts_df.shape[0]}"
        assert counts_df.shape[1] == 5, f"Expected 5 cell lines, got {counts_df.shape[1]}"
        
        expected_columns = ['GM12878', 'K562', 'HMEC', 'IMR90', 'HepG2']
        assert list(counts_df.columns) == expected_columns
    
    def test_peaks_matrix_dimensions(self):
        """Test that peaks matrix has correct dimensions."""
        from generate_data import generate_counts_matrix
        
        counts_df, peaks_df = generate_counts_matrix(
            num_genes=10000,
            num_peaks=10000,
            cell_lines=['GM12878', 'K562', 'HMEC', 'IMR90', 'HepG2'],
            seed=42
        )
        
        assert peaks_df.shape[0] == 10000, f"Expected 10000 peaks, got {peaks_df.shape[0]}"
        assert peaks_df.shape[1] == 5, f"Expected 5 cell lines, got {peaks_df.shape[1]}"
    
    def test_checksum_computation(self):
        """Test that checksum_file works correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content for checksum")
            temp_path = f.name
        
        try:
            checksum = checksum_file(temp_path)
            assert len(checksum) == 64, f"SHA256 checksum should be 64 hex chars, got {len(checksum)}"
            assert all(c in '0123456789abcdef' for c in checksum), "Checksum should be hex"
            
            # Verify determinism
            checksum2 = checksum_file(temp_path)
            assert checksum == checksum2, "Checksums should be identical for same file"
        finally:
            os.unlink(temp_path)
    
    def test_bed_file_format(self):
        """Test that peaks BED file has correct format."""
        from generate_data import generate_peak_coordinates, write_peaks_bed
        
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                os.makedirs('data/raw', exist_ok=True)
                
                peak_coords = generate_peak_coordinates(num_peaks=100)
                write_peaks_bed(None, 'data/raw/test_peaks.bed', peak_coords)
                
                # Read and verify BED format
                with open('data/raw/test_peaks.bed', 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) == 100, f"Expected 100 lines, got {len(lines)}"
                
                # Check first line format (chrom, start, end, name, score, strand)
                first_line = lines[0].strip().split('\t')
                assert len(first_line) == 6, f"BED line should have 6 columns, got {len(first_line)}"
                assert first_line[0].startswith('chr'), f"First column should be chromosome, got {first_line[0]}"
                assert first_line[1].isdigit(), f"Second column should be start position"
                assert first_line[2].isdigit(), f"Third column should be end position"
            finally:
                os.chdir(original_dir)
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        from generate_data import generate_counts_matrix
        
        counts1, peaks1 = generate_counts_matrix(
            num_genes=100,
            num_peaks=100,
            cell_lines=['GM12878', 'K562'],
            seed=42
        )
        
        counts2, peaks2 = generate_counts_matrix(
            num_genes=100,
            num_peaks=100,
            cell_lines=['GM12878', 'K562'],
            seed=42
        )
        
        assert np.array_equal(counts1.values, counts2.values), "Counts should be identical with same seed"
        assert np.array_equal(peaks1.values, peaks2.values), "Peaks should be identical with same seed"
    
    def test_different_seed_produces_different_data(self):
        """Test that different seeds produce different results."""
        from generate_data import generate_counts_matrix
        
        counts1, _ = generate_counts_matrix(
            num_genes=100,
            num_peaks=100,
            cell_lines=['GM12878', 'K562'],
            seed=42
        )
        
        counts2, _ = generate_counts_matrix(
            num_genes=100,
            num_peaks=100,
            cell_lines=['GM12878', 'K562'],
            seed=123
        )
        
        assert not np.array_equal(counts1.values, counts2.values), "Different seeds should produce different data"
    
    def test_file_not_found_error(self):
        """Test that checksum_file raises appropriate error for missing file."""
        with pytest.raises(FileNotFoundError):
            checksum_file('nonexistent_file.txt')
    
    def test_data_types_in_counts(self):
        """Test that counts data contains non-negative integers."""
        from generate_data import generate_counts_matrix
        
        counts_df, _ = generate_counts_matrix(
            num_genes=100,
            num_peaks=100,
            cell_lines=['GM12878'],
            seed=42
        )
        
        # Check all values are non-negative
        assert (counts_df >= 0).all().all(), "All counts should be non-negative"
        
        # Check data type (should be integer-like)
        assert counts_df.dtypes.apply(lambda x: np.issubdtype(x, np.integer) or np.issubdtype(x, np.floating)).all()