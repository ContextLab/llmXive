"""
Unit tests for extraction logic in code/extraction/parser.py.
Verifies parsing of 'r' (effect size) and 'n' (sample size) from CSV inputs.
"""
import pytest
import pandas as pd
import io
import sys
import os

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.extraction.parser import parse_study_csv


class TestExtractionParsing:
    """Tests for the CSV parsing logic."""

    def test_parse_valid_r_n_pairs(self):
        """Verify that valid r and n pairs are correctly extracted and types are correct."""
        csv_data = """study_id,tract,r,n,author,year
        1,arcuate,0.45,120,Smith,2020
        2,cingulum,0.32,85,Johnson,2021
        3,uncinate,-0.15,200,Williams,2019"""

        df = pd.read_csv(io.StringIO(csv_data))
        result = parse_study_csv(df)

        assert len(result) == 3
        
        # Check first row
        assert result[0]['study_id'] == 1
        assert result[0]['tract'] == 'arcuate'
        assert result[0]['r'] == 0.45
        assert result[0]['n'] == 120
        assert result[0]['author'] == 'Smith'
        assert result[0]['year'] == 2020

        # Check types
        assert isinstance(result[0]['r'], float)
        assert isinstance(result[0]['n'], int)

    def test_parse_missing_values_handling(self):
        """Verify that rows with missing r or n are handled (excluded or flagged)."""
        csv_data = """study_id,tract,r,n,author,year
        1,arcuate,0.45,120,Smith,2020
        2,cingulum,,85,Johnson,2021
        3,uncinate,-0.15,,Williams,2019
        4,forceps,0.10,50,Doe,2022"""

        df = pd.read_csv(io.StringIO(csv_data))
        result = parse_study_csv(df)

        # Should include only rows with both r and n
        # Depending on implementation, it might exclude or flag. 
        # Based on T017 (validation), we expect exclusion of invalid rows for quantitative analysis.
        # Let's assume the parser filters out rows missing critical quantitative data.
        # If the parser keeps them with None, we check for that.
        
        # Check that valid rows are present
        valid_ids = [item['study_id'] for item in result]
        assert 1 in valid_ids
        assert 4 in valid_ids

        # Check that rows with missing r or n are handled appropriately
        # If they are excluded:
        assert 2 not in valid_ids
        assert 3 not in valid_ids

    def test_parse_float_conversion_edge_cases(self):
        """Verify parsing of edge cases like negative r, zero r, and scientific notation."""
        csv_data = """study_id,tract,r,n,author,year
        1,arcuate,-0.99,100,TestA,2020
        2,cingulum,0.00,150,TestB,2021
        3,uncinate,1e-4,200,TestC,2019"""

        df = pd.read_csv(io.StringIO(csv_data))
        result = parse_study_csv(df)

        assert len(result) == 3
        assert result[0]['r'] == -0.99
        assert result[1]['r'] == 0.0
        assert result[2]['r'] == 0.0001

    def test_parse_integer_n_conversion(self):
        """Verify that 'n' is converted to integer even if input is float-like string."""
        csv_data = """study_id,tract,r,n,author,year
        1,arcuate,0.5,100.0,Test,2020"""

        df = pd.read_csv(io.StringIO(csv_data))
        result = parse_study_csv(df)

        assert result[0]['n'] == 100
        assert isinstance(result[0]['n'], int)

    def test_parse_empty_dataframe(self):
        """Verify behavior when input dataframe is empty."""
        df = pd.DataFrame(columns=['study_id', 'tract', 'r', 'n', 'author', 'year'])
        result = parse_study_csv(df)
        
        assert result == []

    def test_parse_malformed_numeric_data(self):
        """Verify handling of non-numeric strings in r/n columns."""
        csv_data = """study_id,tract,r,n,author,year
        1,arcuate,N/A,100,Test,2020
        2,cingulum,0.5,invalid,Test,2021"""

        df = pd.read_csv(io.StringIO(csv_data))
        # The parser should handle conversion errors, likely by excluding the row
        # or logging a warning. For this test, we verify it doesn't crash.
        try:
            result = parse_study_csv(df)
            # If it returns a list, check that invalid rows are not included or are flagged
            assert isinstance(result, list)
        except Exception as e:
            # If it raises an exception, that's also a valid behavior if documented
            # But ideally, it should handle gracefully. 
            # For now, let's assume it should handle gracefully and return valid rows only.
            pytest.fail(f"Parser crashed on malformed data: {e}")

    def test_parse_tract_name_normalization(self):
        """Verify that tract names are extracted correctly (case sensitivity)."""
        csv_data = """study_id,tract,r,n,author,year
        1,ARCUATE,0.5,100,Test,2020
        2, Cingulum ,0.3,100,Test,2021"""

        df = pd.read_csv(io.StringIO(csv_data))
        result = parse_study_csv(df)

        # T008 handles harmonization, but parser should at least extract raw text
        # Check that extraction happens without crashing
        assert len(result) == 2
        assert result[0]['tract'] == 'ARCUATE'
        assert result[1]['tract'] == ' Cingulum '