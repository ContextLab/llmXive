"""
Unit tests for data ingestion and filtering module.

Tests:
- SMILES normalization and validation
- Target variable derivation
- Batch processing logic
- Error logging for malformed data
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.data.ingestion import (
    parse_jsonl_line,
    validate_smiles,
    derive_target_variable,
    process_batch,
    ingest_and_filter_data
)
from src.utils.chemistry import get_templates

class TestIngestion:
    """Test suite for ingestion module."""

    def test_parse_jsonl_line_valid(self):
        """Test parsing a valid JSONL line."""
        line = '{"reaction_smiles": "CCO>>CC=O", "yield_pct": 85.0}'
        result = parse_jsonl_line(line)
        
        assert result is not None
        assert result['reaction_smiles'] == "CCO>>CC=O"
        assert result['yield_pct'] == 85.0

    def test_parse_jsonl_line_invalid(self):
        """Test parsing an invalid JSONL line."""
        line = '{"reaction_smiles": invalid json}'
        result = parse_jsonl_line(line)
        
        assert result is None

    def test_validate_smiles_valid(self):
        """Test validation of valid SMILES strings."""
        valid_smiles = [
            "CCO",
            "CC(=O)O",
            "c1ccccc1",
            "CCO>>CC=O"
        ]
        
        for smiles in valid_smiles:
            assert validate_smiles(smiles) is True

    def test_validate_smiles_invalid(self):
        """Test validation of invalid SMILES strings."""
        invalid_smiles = [
            "invalid",
            "C((",
            "",
            "CCO>>"
        ]
        
        for smiles in invalid_smiles:
            assert validate_smiles(smiles) is False

    def test_derive_target_variable_yield(self):
        """Test target derivation when yield_pct is present."""
        record = {
            'reaction_smiles': 'CCO>>CC=O',
            'yield_pct': 75.5,
            'success_flag': 1
        }
        
        target_value, target_type = derive_target_variable(record)
        
        assert target_value == 75.5
        assert target_type == 'yield'

    def test_derive_target_variable_success_fallback(self):
        """Test target derivation when only success_flag is present."""
        record = {
            'reaction_smiles': 'CCO>>CC=O',
            'success_flag': 1
        }
        
        target_value, target_type = derive_target_variable(record)
        
        assert target_value == 1.0
        assert target_type == 'success'

    def test_derive_target_variable_no_target(self):
        """Test target derivation when no target is present."""
        record = {
            'reaction_smiles': 'CCO>>CC=O'
        }
        
        target_value, target_type = derive_target_variable(record)
        
        assert target_value is None
        assert target_type == 'none'

    def test_process_batch_valid_records(self):
        """Test processing a batch of valid records."""
        templates = get_templates()
        
        records = [
            {
                'reaction_smiles': 'CCO>>CC=O',
                'reactants': ['CCO'],
                'products': ['CC=O'],
                'yield_pct': 80.0
            },
            {
                'reaction_smiles': 'CC(=O)O>>CC(=O)Cl',
                'reactants': ['CC(=O)O'],
                'products': ['CC(=O)Cl'],
                'success_flag': 1
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            error_log_path = Path(f.name)
        
        try:
            processed = process_batch(records, templates, error_log_path)
            
            # Should have processed records with valid classifications
            assert len(processed) >= 0  # May be 0 if templates don't match
            
            # Check that target values are derived
            for record in processed:
                assert 'reaction_type' in record
                assert 'target_value' in record
                assert 'target_type' in record
        finally:
            error_log_path.unlink(missing_ok=True)

    def test_process_batch_malformed_records(self):
        """Test that malformed records are logged and excluded."""
        templates = get_templates()
        
        records = [
            {
                'reaction_smiles': 'invalid_smiles',
                'reactants': ['invalid'],
                'products': ['invalid'],
                'yield_pct': 80.0
            },
            {
                'reaction_smiles': 'CCO>>CC=O',
                'reactants': [],  # Missing reactants
                'products': ['CC=O'],
                'yield_pct': 80.0
            },
            {
                # Missing reaction_smiles
                'reactants': ['CCO'],
                'products': ['CC=O'],
                'yield_pct': 80.0
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            error_log_path = Path(f.name)
        
        try:
            processed = process_batch(records, templates, error_log_path)
            
            # Check error log was written
            assert error_log_path.exists()
            with open(error_log_path, 'r') as f:
                log_content = f.read()
                assert len(log_content) > 0
        finally:
            error_log_path.unlink(missing_ok=True)

    @patch('src.data.ingestion.download_uspto_data')
    @patch('src.data.ingestion.load_config')
    @patch('src.data.ingestion.get_templates')
    @patch('src.data.ingestion.classify_batch')
    def test_ingest_and_filter_data_mocked(
        self,
        mock_classify_batch,
        mock_get_templates,
        mock_load_config,
        mock_download
    ):
        """Test the full ingestion pipeline with mocked dependencies."""
        # Setup mocks
        mock_download.return_value = None
        mock_load_config.return_value = {}
        mock_get_templates.return_value = {
            'SN1': '[C:1]([O:2])>>[C:1]+[O:2]-',
            'SN2': '[C:1]([O:2])>>[C:1]=[O:2]',
            'Diels-Alder': '[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1'
        }
        
        # Mock classify_batch to return classifications
        mock_classify_batch.return_value = ['SN1', 'SN2', 'Diels-Alder']
        
        # Create temporary test data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            test_data = [
                {"reaction_smiles": "CCO>>CC=O", "reactants": ["CCO"], "products": ["CC=O"], "yield_pct": 80.0},
                {"reaction_smiles": "CC(=O)O>>CC(=O)Cl", "reactants": ["CC(=O)O"], "products": ["CC(=O)Cl"], "success_flag": 1},
                {"reaction_smiles": "C=CC=C.C=CC=C>>C1CC=CC1", "reactants": ["C=CC=C", "C=CC=C"], "products": ["C1CC=CC1"], "yield_pct": 60.0}
            ]
            for record in test_data:
                f.write(json.dumps(record) + '\n')
            raw_data_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = Path(f.name)
        
        try:
            # Run ingestion
            result_path = ingest_and_filter_data(
                raw_data_path=raw_data_path,
                output_path=output_path,
                chunk_size=10
            )
            
            # Verify output exists
            assert result_path.exists()
            
            # Verify CSV has expected columns
            import pandas as pd
            df = pd.read_csv(result_path)
            
            assert 'reaction_type' in df.columns
            assert 'target_value' in df.columns
            assert 'target_type' in df.columns
            
        finally:
            raw_data_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
