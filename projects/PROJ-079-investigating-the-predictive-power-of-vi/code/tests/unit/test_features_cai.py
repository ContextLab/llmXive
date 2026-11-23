import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_cai


class TestCalculateCAI:
    """Unit tests for the calculate_cai function."""

    def test_calculate_cai_valid_fasta(self, tmp_path):
        """Test CAI calculation with a valid FASTA file."""
        # Create a test FASTA file with a known sequence
        fasta_content = """>test_sequence
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        """
        fasta_file = tmp_path / "test.fasta"
        fasta_file.write_text(fasta_content)
        
        # Calculate CAI (should not raise)
        cai_value = calculate_cai(str(fasta_file), species='human')
        
        # CAI should be between 0 and 1
        assert 0 <= cai_value <= 1
        assert isinstance(cai_value, float)

    def test_calculate_cai_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_cai("/nonexistent/path/to/file.fasta")

    def test_calculate_cai_empty_sequence(self, tmp_path):
        """Test that appropriate error is raised for empty sequence."""
        fasta_content = """>empty_sequence
        """
        fasta_file = tmp_path / "empty.fasta"
        fasta_file.write_text(fasta_content)
        
        with pytest.raises(ValueError):
            calculate_cai(str(fasta_file))

    def test_calculate_cai_short_sequence(self, tmp_path):
        """Test that appropriate error is raised for sequence < 3 nucleotides."""
        fasta_content = """>short_sequence
        AT
        """
        fasta_file = tmp_path / "short.fasta"
        fasta_file.write_text(fasta_content)
        
        with pytest.raises(ValueError):
            calculate_cai(str(fasta_file))

    def test_calculate_cai_mixed_case(self, tmp_path):
        """Test that mixed case sequences are handled correctly."""
        fasta_content = """>mixed_case
        atgCGAtcgATCgATCgATCgATCgATCgATCgATCgATCgATCgATCgATCgATCgATCgATCg
        """
        fasta_file = tmp_path / "mixed.fasta"
        fasta_file.write_text(fasta_content)
        
        # Should not raise and should return valid CAI
        cai_value = calculate_cai(str(fasta_file), species='human')
        assert 0 <= cai_value <= 1

    def test_calculate_cai_multiple_sequences(self, tmp_path):
        """Test CAI calculation with multiple sequences in one file."""
        fasta_content = """>seq1
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        >seq2
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        """
        fasta_file = tmp_path / "multi.fasta"
        fasta_file.write_text(fasta_content)
        
        cai_value = calculate_cai(str(fasta_file), species='human')
        assert 0 <= cai_value <= 1

    def test_calculate_cai_mouse_species(self, tmp_path):
        """Test CAI calculation with mouse codon table."""
        fasta_content = """>test_sequence
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        """
        fasta_file = tmp_path / "mouse_test.fasta"
        fasta_file.write_text(fasta_content)
        
        cai_human = calculate_cai(str(fasta_file), species='human')
        cai_mouse = calculate_cai(str(fasta_file), species='mouse')
        
        # Both should be valid but may differ slightly due to different codon tables
        assert 0 <= cai_human <= 1
        assert 0 <= cai_mouse <= 1

    def test_calculate_cai_invalid_species(self, tmp_path):
        """Test that ValueError is raised for invalid species."""
        fasta_content = """>test_sequence
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        """
        fasta_file = tmp_path / "invalid_species.fasta"
        fasta_file.write_text(fasta_content)
        
        with pytest.raises(ValueError, match="Invalid species"):
            calculate_cai(str(fasta_file), species='invalid_species')

    def test_calculate_cai_with_stop_codons(self, tmp_path):
        """Test that stop codons are properly skipped in CAI calculation."""
        # Create a sequence with stop codons
        fasta_content = """>with_stops
        ATGCGATCGATCTAATAGTGAATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        """
        fasta_file = tmp_path / "with_stops.fasta"
        fasta_file.write_text(fasta_content)
        
        # Should not raise and should skip stop codons
        cai_value = calculate_cai(str(fasta_file), species='human')
        assert 0 <= cai_value <= 1

    def test_calculate_cai_with_invalid_bases(self, tmp_path):
        """Test that sequences with N bases are handled (N is skipped)."""
        fasta_content = """>with_n
        ATGCGATCGATCNATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        """
        fasta_file = tmp_path / "with_n.fasta"
        fasta_file.write_text(fasta_content)
        
        # Should handle N bases (skip them)
        cai_value = calculate_cai(str(fasta_file), species='human')
        assert 0 <= cai_value <= 1