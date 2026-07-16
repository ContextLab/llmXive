"""
Unit tests for sample-level pairing logic.

Tests FR-002: Pairing using biological sample identifiers.
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from code.pairing_logic import (
    load_expression_samples,
    load_metabolite_samples,
    pair_samples,
    run_pairing,
    create_paired_matrices
)
from code.exceptions import E_PAIRING

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_expression_data(temp_dir):
    """Create a sample expression CSV file."""
    data = {
        'sample_id': ['GSM123', 'GSM456', 'GSM789', 'GSM000'],
        'gene_id': ['AT1G01010', 'AT1G01010', 'AT1G01020', 'AT1G01030'],
        'expression_value': [10.5, 15.2, 8.7, 12.1],
        'treatment': ['herbivore', 'herbivore', 'control', 'herbivore']
    }
    df = pd.DataFrame(data)
    file_path = temp_dir / 'expression.csv'
    df.to_csv(file_path, index=False)
    return file_path, data

@pytest.fixture
def sample_metabolite_data(temp_dir):
    """Create a sample metabolite CSV file."""
    data = {
        'sample_id': ['GSM123', 'GSM456', 'GSM111', 'GSM789'],
        'metabolite_id': ['terpenoid_1', 'terpenoid_1', 'alkaloid_1', 'phenylpropanoid_1'],
        'concentration': [2.5, 3.2, 1.8, 4.1],
        'treatment': ['herbivore', 'herbivore', 'herbivore', 'control']
    }
    df = pd.DataFrame(data)
    file_path = temp_dir / 'metabolite.csv'
    df.to_csv(file_path, index=False)
    return file_path, data

def test_load_expression_samples(sample_expression_data):
    """Test loading expression samples from CSV."""
    file_path, _ = sample_expression_data
    samples = load_expression_samples(file_path)
    
    assert len(samples) == 4
    assert 'GSM123' in samples
    assert samples['GSM123']['source'] == 'expression'
    assert 'expression_value' in samples['GSM123']['metadata']

def test_load_metabolite_samples(sample_metabolite_data):
    """Test loading metabolite samples from CSV."""
    file_path, _ = sample_metabolite_data
    samples = load_metabolite_samples(file_path)
    
    assert len(samples) == 4
    assert 'GSM123' in samples
    assert samples['GSM123']['source'] == 'metabolite'
    assert 'concentration' in samples['GSM123']['metadata']

def test_pair_samples_basic(sample_expression_data, sample_metabolite_data):
    """Test basic sample pairing logic."""
    _, expr_data = sample_expression_data
    _, metab_data = sample_metabolite_data
    
    expr_samples = load_expression_samples(sample_expression_data[0])
    metab_samples = load_metabolite_samples(sample_metabolite_data[0])
    
    paired, mismatches = pair_samples(expr_samples, metab_samples)
    
    # Expected matches: GSM123, GSM456, GSM789 (3 samples)
    # Expected mismatches: GSM000 (expr only), GSM111 (metab only)
    assert len(paired) == 3
    assert len(mismatches) == 2
    
    matched_ids = [p['sample_id'] for p in paired]
    assert 'GSM123' in matched_ids
    assert 'GSM456' in matched_ids
    assert 'GSM789' in matched_ids
    
    mismatch_ids = [m['sample_id'] for m in mismatches]
    assert 'GSM000' in mismatch_ids
    assert 'GSM111' in mismatch_ids

def test_pair_samples_no_overlap(temp_dir):
    """Test pairing when there is no overlap."""
    # Create expression file with GSM100
    expr_data = {
        'sample_id': ['GSM100'],
        'gene_id': ['AT1G01010'],
        'expression_value': [10.0]
    }
    expr_path = temp_dir / 'expr_no_match.csv'
    pd.DataFrame(expr_data).to_csv(expr_path, index=False)
    
    # Create metabolite file with GSM200
    metab_data = {
        'sample_id': ['GSM200'],
        'metabolite_id': ['terpenoid_1'],
        'concentration': [2.0]
    }
    metab_path = temp_dir / 'metab_no_match.csv'
    pd.DataFrame(metab_data).to_csv(metab_path, index=False)
    
    expr_samples = load_expression_samples(expr_path)
    metab_samples = load_metabolite_samples(metab_path)
    
    paired, mismatches = pair_samples(expr_samples, metab_samples)
    
    assert len(paired) == 0
    assert len(mismatches) == 2

def test_pair_samples_complete_overlap(temp_dir):
    """Test pairing when all samples match."""
    # Create files with identical sample IDs
    sample_ids = ['GSM111', 'GSM222', 'GSM333']
    
    expr_data = {
        'sample_id': sample_ids,
        'gene_id': ['AT1G01010'] * 3,
        'expression_value': [10.0, 15.0, 12.0]
    }
    expr_path = temp_dir / 'expr_match.csv'
    pd.DataFrame(expr_data).to_csv(expr_path, index=False)
    
    metab_data = {
        'sample_id': sample_ids,
        'metabolite_id': ['terpenoid_1'] * 3,
        'concentration': [2.0, 3.0, 2.5]
    }
    metab_path = temp_dir / 'metab_match.csv'
    pd.DataFrame(metab_data).to_csv(metab_path, index=False)
    
    expr_samples = load_expression_samples(expr_path)
    metab_samples = load_metabolite_samples(metab_path)
    
    paired, mismatches = pair_samples(expr_samples, metab_samples)
    
    assert len(paired) == 3
    assert len(mismatches) == 0

def test_run_pairing_integration(sample_expression_data, sample_metabolite_data, temp_dir):
    """Test the full run_pairing function."""
    out_expr = temp_dir / 'paired_expression.csv'
    out_metab = temp_dir / 'paired_metabolite.csv'
    
    stats = run_pairing(
        expression_file=str(sample_expression_data[0]),
        metabolite_file=str(sample_metabolite_data[0]),
        output_expression_file=str(out_expr),
        output_metabolite_file=str(out_metab)
    )
    
    assert stats['expression_samples'] == 4
    assert stats['metabolite_samples'] == 4
    assert stats['paired_samples'] == 3
    assert stats['mismatched_samples'] == 2
    assert stats['pairing_rate'] == 0.75  # 3/4
    
    # Check output files exist
    assert out_expr.exists()
    assert out_metab.exists()
    
    # Check output content
    paired_expr = pd.read_csv(out_expr)
    paired_metab = pd.read_csv(out_metab)
    
    assert len(paired_expr) == 9  # 3 samples * 3 rows (multiple genes per sample)
    assert len(paired_metab) == 3  # 3 samples * 1 metabolite per sample

def test_pairing_rate_calculation(sample_expression_data, sample_metabolite_data):
    """Test that pairing rate is calculated correctly."""
    stats = run_pairing(
        expression_file=str(sample_expression_data[0]),
        metabolite_file=str(sample_metabolite_data[0])
    )
    
    # 3 paired out of 4 max(4, 4) = 0.75
    assert abs(stats['pairing_rate'] - 0.75) < 0.001

def test_empty_pairing(temp_dir):
    """Test pairing with empty files."""
    # Create empty files with headers
    expr_path = temp_dir / 'empty_expr.csv'
    pd.DataFrame(columns=['sample_id', 'gene_id', 'expression_value']).to_csv(expr_path, index=False)
    
    metab_path = temp_dir / 'empty_metab.csv'
    pd.DataFrame(columns=['sample_id', 'metabolite_id', 'concentration']).to_csv(metab_path, index=False)
    
    stats = run_pairing(
        expression_file=str(expr_path),
        metabolite_file=str(metab_path)
    )
    
    assert stats['expression_samples'] == 0
    assert stats['metabolite_samples'] == 0
    assert stats['paired_samples'] == 0
    assert stats['pairing_rate'] == 0.0