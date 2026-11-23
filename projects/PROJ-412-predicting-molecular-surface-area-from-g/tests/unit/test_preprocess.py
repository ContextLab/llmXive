"""
Unit tests for T015a: 3D conformer generation and failure logging.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.preprocess import (
    map_exception_to_reason,
    generate_conformer,
    process_molecule_3d,
    process_chunk_3d,
    write_failures_to_csv,
    load_conformer_params
)
from rdkit import Chem

class TestExceptionMapping:
    """Test exception to failure reason mapping."""
    
    def test_value_error_valence(self):
        """Test that ValueError maps to INVALID_VALENCE."""
        exc = ValueError("Valence error in molecule")
        assert map_exception_to_reason(exc) == 'INVALID_VALENCE'
    
    def test_runtime_error_etkdg(self):
        """Test that RuntimeError with ETKDG maps to ETKDG_FAIL."""
        exc = RuntimeError("ETKDG generation failed")
        assert map_exception_to_reason(exc) == 'ETKDG_FAIL'
    
    def test_runtime_error_minimization(self):
        """Test that RuntimeError with minimization maps to MINIMIZATION_FAIL."""
        exc = RuntimeError("Energy minimization failed")
        assert map_exception_to_reason(exc) == 'MINIMIZATION_FAIL'
    
    def test_generic_exception(self):
        """Test that unknown exceptions map to UNKNOWN_FAIL."""
        exc = Exception("Unknown error")
        assert map_exception_to_reason(exc) == 'UNKNOWN_FAIL'

class TestConformerGeneration:
    """Test conformer generation logic."""
    
    def test_valid_molecule_success(self):
        """Test that a valid molecule generates a conformer successfully."""
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)
        
        params = load_conformer_params()
        result_mol, reason = generate_conformer(mol, params)
        
        assert result_mol is not None, "Valid molecule should generate conformer"
        assert reason == '', "Success should have empty reason"
        assert result_mol.GetNumConformers() > 0, "Should have at least one conformer"
    
    def test_invalid_smiles_failure(self):
        """Test that invalid SMILES fails appropriately."""
        # This is handled at the SMILES parsing level, not in generate_conformer
        # We test the process_molecule_3d function instead
        pass

class TestProcessMolecule3D:
    """Test single molecule processing."""
    
    def test_success_case(self):
        """Test successful processing of a molecule."""
        row = {
            'smiles': "CCO",
            'atom_count': 9  # C2H6O with hydrogens
        }
        params = load_conformer_params()
        
        result = process_molecule_3d(row, params)
        
        assert result['status'] == 'success'
        assert 'conformer_coords' in result
        assert len(result['conformer_coords']) % 3 == 0  # 3 coordinates per atom
    
    def test_excluded_atom_count(self):
        """Test that molecules with too many atoms are excluded."""
        # Create a molecule with > 100 atoms (simulated)
        row = {
            'smiles': "CCO",
            'atom_count': 150
        }
        params = load_conformer_params()
        
        result = process_molecule_3d(row, params)
        
        assert result['status'] == 'excluded'
        assert result['failure_reason'] == 'ATOM_COUNT_EXCEEDED'

class TestProcessChunk3D:
    """Test chunk processing."""
    
    def test_mixed_results(self):
        """Test processing a chunk with mixed success/failure."""
        chunk_data = [
            {'smiles': 'CCO', 'atom_count': 9},
            {'smiles': 'CCCC', 'atom_count': 13},
            {'smiles': 'invalid_smiles', 'atom_count': 0}
        ]
        chunk = pd.DataFrame(chunk_data)
        params = load_conformer_params()
        
        success_df, failures = process_chunk_3d(chunk, params)
        
        # Should have some successes and some failures
        assert len(success_df) + len(failures) == len(chunk)

class TestWriteFailuresToCSV:
    """Test failure report writing."""
    
    def test_write_failures(self):
        """Test writing failure report to CSV."""
        failures = [
            {
                'smiles': 'CCO',
                'failure_reason': 'ETKDG_FAIL',
                'atom_count': 9,
                'params': {'numThreads': -1, 'maxAttempts': 200, 'energyMinimizationSteps': 200, 'random_seed': 42}
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "failures.csv"
            params = load_conformer_params()
            write_failures_to_csv(failures, output_path, params)
            
            assert output_path.exists()
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df['smiles'].iloc[0] == 'CCO'
            assert df['failure_reason'].iloc[0] == 'ETKDG_FAIL'
            assert 'numThreads' in df.columns
            assert 'maxAttempts' in df.columns

class TestConformerParams:
    """Test conformer parameter handling."""
    
    def test_params_schema(self):
        """Test that conformer params have required keys."""
        params = load_conformer_params()
        
        required_keys = ['numThreads', 'maxAttempts', 'energyMinimizationSteps', 'random_seed']
        for key in required_keys:
            assert key in params, f"Missing required key: {key}"
        
        # Check types
        assert isinstance(params['numThreads'], int)
        assert isinstance(params['maxAttempts'], int)
        assert isinstance(params['energyMinimizationSteps'], int)
        assert isinstance(params['random_seed'], int)