"""
Unit tests for SMILES normalization and error logging in ingestion module.

Tests:
- SMILES normalization (removing spaces, handling whitespace)
- Error logging for malformed records
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.ingestion import parse_jsonl_line, process_chunk
from src.data.schemas import validate_reaction_record

class TestSMILESNormalization:
    """Tests for SMILES string normalization logic."""
    
    def test_normalize_spaces_in_reactants(self):
        """Test that spaces in reactant SMILES are removed."""
        raw_data = {
            "reactants": " C C C ",
            "products": "C1=CC=CC=C1",
            "reagents": "H2O"
        }
        
        result = parse_jsonl_line(raw_data)
        
        assert result is not None
        assert result["reactants"] == "CCC"
        assert " " not in result["reactants"]
        
    def test_normalize_spaces_in_products(self):
        """Test that spaces in product SMILES are removed."""
        raw_data = {
            "reactants": "CCO",
            "products": " C C O ",
            "reagents": "H+"
        }
        
        result = parse_jsonl_line(raw_data)
        
        assert result is not None
        assert result["products"] == "CCO"
        assert " " not in result["products"]
        
    def test_normalize_spaces_in_reagents(self):
        """Test that spaces in reagent SMILES are removed."""
        raw_data = {
            "reactants": "CC",
            "products": "CCO",
            "reagents": " O H "
        }
        
        result = parse_jsonl_line(raw_data)
        
        assert result is not None
        assert result["reagents"] == "OH"
        assert " " not in result["reagents"]
        
    def test_preserves_valid_smiles(self):
        """Test that valid SMILES without spaces are preserved."""
        raw_data = {
            "reactants": "CCO",
            "products": "C(=O)O",
            "reagents": "H2SO4"
        }
        
        result = parse_jsonl_line(raw_data)
        
        assert result is not None
        assert result["reactants"] == "CCO"
        assert result["products"] == "C(=O)O"
        assert result["reagents"] == "H2SO4"

class TestErrorLogging:
    """Tests for error logging of malformed records."""
    
    def test_missing_required_fields(self):
        """Test that records missing required fields are handled."""
        # Missing 'products'
        raw_data = {
            "reactants": "CCO",
            "reagents": "H+"
        }
        
        result = parse_jsonl_line(raw_data)
        assert result is None
        
    def test_process_chunk_logs_errors(self):
        """Test that process_chunk writes errors to the error log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log_path = Path(tmpdir) / "errors.log"
            target_path = Path(tmpdir) / "output.jsonl"
            
            # Create a list with one valid and one invalid record
            valid_record = {
                "reactants": "CCO",
                "products": "CCO",
                "reagents": "H+"
            }
            invalid_record = {
                "reactants": "CCO"
                # Missing products
            }
            
            records = [valid_record, invalid_record]
            
            count = process_chunk(records, error_log_path, target_path)
            
            # Only the valid record should be counted
            assert count == 1
            
            # Check error log exists and contains the invalid record info
            assert error_log_path.exists()
            with open(error_log_path, 'r') as f:
                error_content = f.read()
                assert "Parse failed" in error_content or "Validation failed" in error_content
                
            # Check output file contains only the valid record
            assert target_path.exists()
            with open(target_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                parsed_line = json.loads(lines[0])
                assert parsed_line["reactants"] == "CCO"
                
    def test_empty_record_handling(self):
        """Test handling of empty or null records."""
        raw_data = {}
        result = parse_jsonl_line(raw_data)
        assert result is None
        
        raw_data = None
        # This should be handled by the caller or raise an error if passed directly
        # but parse_jsonl_line expects a dict. We test the logic path.
        try:
            result = parse_jsonl_line(raw_data)
            assert result is None
        except (TypeError, AttributeError):
            # Expected if None is passed and we try to access keys
            pass
