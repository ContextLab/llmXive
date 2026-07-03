import pytest
from pathlib import Path
import tempfile
import json

from src.data.ingestion import normalize_smiles, process_record

def test_normalize_smiles_valid():
    """Test normalization of valid SMILES."""
    smiles = "CCO"
    result = normalize_smiles(smiles)
    assert result is not None
    assert "CCO" in result

def test_normalize_smiles_invalid():
    """Test normalization of invalid SMILES."""
    smiles = "invalid_smiles_123"
    result = normalize_smiles(smiles)
    assert result is None

def test_process_record_with_yield():
    """Test processing record with yield_pct."""
    record = {
        'rxn_smiles': 'CCO',
        'yield_pct': 85.5
    }
    with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as f:
        error_log = Path(f.name)
    
    result = process_record(record, error_log)
    assert result is not None
    assert result['target_value'] == 85.5
    assert result['reaction_type'] is not None  # Should match a template
    
    error_log.unlink()

def test_process_record_fallback_to_success_flag():
    """Test processing record falling back to success_flag."""
    record = {
        'rxn_smiles': 'CCO',
        'success_flag': 1
    }
    with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as f:
        error_log = Path(f.name)
    
    result = process_record(record, error_log)
    assert result is not None
    assert result['target_value'] == 1
    
    error_log.unlink()

def test_process_record_no_target():
    """Test processing record without target variable."""
    record = {
        'rxn_smiles': 'CCO'
    }
    with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as f:
        error_log = Path(f.name)
    
    result = process_record(record, error_log)
    assert result is None
    
    error_log.unlink()
