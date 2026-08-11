"""
Unit tests for the provenance validator module.
"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import json
from cleaning.provenance_validator import (
    is_valid_source_reference,
    validate_provenance,
    filter_valid_provenance,
    save_validation_report
)

class TestIsValidSourceReference:
    """Tests for is_valid_source_reference function."""
    
    def test_valid_nist_reference(self):
        """Test valid NIST reference."""
        assert is_valid_source_reference("NIST Crystal Data") is True
        assert is_valid_source_reference("National Institute of Standards and Technology") is True
    
    def test_valid_doi_reference(self):
        """Test valid DOI reference."""
        assert is_valid_source_reference("doi:10.1063/1.4812345") is True
        assert is_valid_source_reference("https://doi.org/10.1021/acs.chemmater.1c01234") is True
    
    def test_valid_journal_reference(self):
        """Test valid journal reference."""
        assert is_valid_source_reference("J. Chem. Phys. 145, 123456 (2016)") is True
        assert is_valid_source_reference("Phys. Rev. B 98, 12345 (2018)") is True
        assert is_valid_source_reference("Nature 580, 123 (2020)") is True
    
    def test_valid_arxiv_reference(self):
        """Test valid arXiv reference."""
        assert is_valid_source_reference("arXiv:2103.12345") is True
        assert is_valid_source_reference("https://arxiv.org/abs/2103.12345") is True
    
    def test_valid_author_year_reference(self):
        """Test valid author-year reference."""
        assert is_valid_source_reference("Smith et al. 2021") is True
        assert is_valid_source_reference("Johnson, A. 2019") is True
    
    def test_invalid_empty_reference(self):
        """Test invalid empty reference."""
        assert is_valid_source_reference("") is False
        assert is_valid_source_reference("   ") is False
        assert is_valid_source_reference(None) is False
    
    def test_invalid_generic_reference(self):
        """Test invalid generic reference."""
        assert is_valid_source_reference("Some random text") is False
        assert is_valid_source_reference("website.com") is False

class TestValidateProvenance:
    """Tests for validate_provenance function."""
    
    def test_validate_with_valid_references(self):
        """Test validation with all valid references."""
        df = pd.DataFrame({
            'source_reference': [
                "doi:10.1063/1.4812345",
                "NIST Crystal Data",
                "J. Chem. Phys. 145, 12345 (2016)"
            ]
        })
        
        df_validated, errors = validate_provenance(df)
        
        assert 'provenance_valid' in df_validated.columns
        assert all(df_validated['provenance_valid'] == True)
        assert len(errors) == 0
    
    def test_validate_with_invalid_references(self):
        """Test validation with invalid references."""
        df = pd.DataFrame({
            'source_reference': [
                "doi:10.1063/1.4812345",
                "invalid reference",
                "NIST Crystal Data"
            ]
        })
        
        df_validated, errors = validate_provenance(df)
        
        assert 'provenance_valid' in df_validated.columns
        assert df_validated['provenance_valid'].sum() == 2
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'invalid_source_reference'
    
    def test_validate_missing_column(self):
        """Test validation when source_reference column is missing."""
        df = pd.DataFrame({
            'other_column': [1, 2, 3]
        })
        
        df_validated, errors = validate_provenance(df)
        
        assert 'provenance_valid' in df_validated.columns
        assert all(df_validated['provenance_valid'] == False)
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'missing_column'

class TestFilterValidProvenance:
    """Tests for filter_valid_provenance function."""
    
    def test_filter_valid_entries(self):
        """Test filtering keeps only valid entries."""
        df = pd.DataFrame({
            'source_reference': [
                "doi:10.1063/1.4812345",
                "invalid reference",
                "NIST Crystal Data"
            ],
            'provenance_valid': [True, False, True]
        })
        
        df_filtered = filter_valid_provenance(df)
        
        assert len(df_filtered) == 2
        assert all(df_filtered['provenance_valid'] == True)
    
    def test_filter_insufficient_samples(self):
        """Test filtering raises error when too few valid samples."""
        # Create exactly 49 valid entries
        valid_refs = ["doi:10.1063/1.4812345"] * 49
        df = pd.DataFrame({
            'source_reference': valid_refs,
            'provenance_valid': [True] * 49
        })
        
        with pytest.raises(ValueError, match="Insufficient valid samples"):
            filter_valid_provenance(df)
    
    def test_filter_missing_column(self):
        """Test filtering raises error when provenance_valid column is missing."""
        df = pd.DataFrame({
            'source_reference': ["doi:10.1063/1.4812345"]
        })
        
        with pytest.raises(ValueError, match="DataFrame must have 'provenance_valid' column"):
            filter_valid_provenance(df)

class TestSaveValidationReport:
    """Tests for save_validation_report function."""
    
    def test_save_report_creates_file(self):
        """Test that save_report creates the expected file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results" / "validation_report.json"
            errors = [
                {'error_type': 'invalid_source_reference', 'message': 'Test error'}
            ]
            
            save_validation_report(errors, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert 'validation_timestamp' in report
            assert 'total_errors' in report
            assert report['total_errors'] == 1
            assert 'errors' in report
            assert len(report['errors']) == 1
    
    def test_save_report_empty_errors(self):
        """Test saving report with no errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results" / "validation_report.json"
            errors = []
            
            save_validation_report(errors, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report['total_errors'] == 0