"""
Contract tests for data validation schema.

These tests verify that the data validation schema correctly handles
musical_genre fields and falls back to STOMP-R when necessary.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile

from data.validate import check_behavioral_variables, DataValidationError


class TestDataValidationSchema:
    """Contract tests for data validation schema."""
    
    def test_schema_validates_musical_genre_field(self):
        """Test that the schema validates the presence of musical_genre field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a participants.tsv with musical_genre
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            participants_file.write_text("sub-001\trock\t25\tM\n")
            participants_file.write_text("sub-002\tpop\t30\tF\n")
            
            # This should pass validation
            result = check_behavioral_variables(Path(tmpdir))
            assert "musical_genre" in result["available_variables"]
            assert result["has_primary_variable"] is True
    
    def test_schema_falls_back_to_stomp_r(self):
        """Test that the schema falls back to STOMP-R when musical_genre is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a participants.tsv without musical_genre but with STOMP-R
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("participant_id\tSTOMP-R\tage\tsex\n")
            participants_file.write_text("sub-001\t15\t25\tM\n")
            participants_file.write_text("sub-002\t18\t30\tF\n")
            
            # This should pass validation with fallback
            result = check_behavioral_variables(Path(tmpdir))
            assert "STOMP-R" in result["available_variables"]
            assert result["has_primary_variable"] is False
            assert result["has_fallback_variable"] is True
    
    def test_schema_fails_when_both_missing(self):
        """Test that the schema fails when both musical_genre and STOMP-R are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a participants.tsv without either variable
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("participant_id\tage\tsex\n")
            participants_file.write_text("sub-001\t25\tM\n")
            participants_file.write_text("sub-002\t30\tF\n")
            
            # This should raise DataValidationError
            with pytest.raises(DataValidationError) as exc_info:
                check_behavioral_variables(Path(tmpdir))
            
            assert exc_info.value.code == "ERR_DATA_MISSING"
            assert "musical_genre" in str(exc_info.value) or "STOMP-R" in str(exc_info.value)
    
    def test_schema_handles_empty_participants_file(self):
        """Test that the schema handles an empty participants file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an empty participants.tsv
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("")
            
            # This should raise DataValidationError
            with pytest.raises((DataValidationError, ValueError)):
                check_behavioral_variables(Path(tmpdir))
    
    def test_schema_handles_malformed_participants_file(self):
        """Test that the schema handles a malformed participants file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a malformed participants.tsv
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("participant_id,musical_genre,age,sex\n")
            participants_file.write_text("sub-001,rock,25,M\n")
            
            # This should raise DataValidationError or handle gracefully
            # The exact behavior depends on the implementation
            try:
                result = check_behavioral_variables(Path(tmpdir))
                # If it doesn't raise, it should at least report the issue
                assert "error" in result or "warning" in result
            except (DataValidationError, ValueError, pd.errors.ParserError):
                # This is also acceptable
                pass
    
    def test_schema_validates_sample_size(self):
        """Test that the schema validates sample size requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a participants.tsv with insufficient sample size
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            for i in range(1, 10):  # Only 9 subjects
                participants_file.write_text(f"sub-0{i}\trock\t2{i}\tM\n")
            
            # This should raise DataValidationError for underpowered sample
            with pytest.raises(DataValidationError) as exc_info:
                check_behavioral_variables(Path(tmpdir))
            
            assert exc_info.value.code == "ERR_UNDERPOWERED"
    
    def test_schema_validates_with_sufficient_sample_size(self):
        """Test that the schema passes with sufficient sample size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a participants.tsv with sufficient sample size
            participants_file = Path(tmpdir) / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            for i in range(1, 100):  # 99 subjects
                genre = "rock" if i % 2 == 0 else "pop"
                participants_file.write_text(f"sub-{i:03d}\t{genre}\t{20+i}\t{'M' if i % 2 == 0 else 'F'}\n")
            
            # This should pass validation
            result = check_behavioral_variables(Path(tmpdir))
            assert result["sample_size"] >= 85
            assert result["has_primary_variable"] is True
