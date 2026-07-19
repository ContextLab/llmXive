import pytest
import json
from pathlib import Path
import tempfile
import os

from data.validation import (
    validate_smiles_syntax,
    process_single_molecule_with_validation,
    validate_and_process_dataset,
    FAILURE_THRESHOLD
)
from utils.conformer_config import generate_conformer_config

class TestSMILESValidation:
    """Tests for SMILES syntax validation."""
    
    def test_valid_smiles(self):
        """Test that valid SMILES strings are accepted."""
        valid_smiles = [
            "CCO",  # Ethanol
            "c1ccccc1",  # Benzene
            "CC(=O)O",  # Acetic acid
            "C1CCCCC1",  # Cyclohexane
        ]
        
        for smiles in valid_smiles:
            assert validate_smiles_syntax(smiles) is True, f"Failed for valid SMILES: {smiles}"
    
    def test_invalid_smiles(self):
        """Test that invalid SMILES strings are rejected."""
        invalid_smiles = [
            "",  # Empty string
            "INVALID",  # Invalid characters
            "C((",  # Unmatched parentheses
            "C1CC1CC1",  # Invalid ring numbering
            "C#C#C",  # Invalid bond specification
        ]
        
        for smiles in invalid_smiles:
            assert validate_smiles_syntax(smiles) is False, f"Accepted invalid SMILES: {smiles}"

class TestConformerGeneration:
    """Tests for conformer generation with error handling."""
    
    def test_successful_conformer_generation(self):
        """Test successful conformer generation for a valid molecule."""
        smiles = "CCO"  # Ethanol
        mol_id = "test_mol_1"
        
        # Generate default config
        config = generate_conformer_config()
        
        success, result, error = process_single_molecule_with_validation(smiles, mol_id, config)
        
        assert success is True, f"Conformer generation failed: {error}"
        assert result is not None
        assert result["mol_id"] == mol_id
        assert result["smiles"] == smiles
        assert "sasa" in result
        assert result["sasa"] > 0
        assert "molecular_weight" in result
        assert result["molecular_weight"] > 0
    
    def test_failed_conformer_generation_invalid_smiles(self):
        """Test that invalid SMILES results in failure."""
        smiles = "INVALID_SMILES"
        mol_id = "test_mol_2"
        
        config = generate_conformer_config()
        
        success, result, error = process_single_molecule_with_validation(smiles, mol_id, config)
        
        assert success is False
        assert result is None
        assert error is not None
        assert "Invalid SMILES" in error

class TestFailureRateThreshold:
    """Tests for failure rate threshold enforcement."""
    
    def test_halt_on_high_failure_rate(self):
        """Test that processing halts when failure rate exceeds threshold."""
        # Create a dataset with >10% invalid SMILES
        test_data = [
            {"mol_id": "valid_1", "smiles": "CCO"},
            {"mol_id": "valid_2", "smiles": "c1ccccc1"},
            {"mol_id": "invalid_1", "smiles": "INVALID"},
            {"mol_id": "invalid_2", "smiles": "BAD"},
            {"mol_id": "invalid_3", "smiles": "WRONG"},
            {"mol_id": "invalid_4", "smiles": "ERROR"},
            {"mol_id": "invalid_5", "smiles": "FAIL"},
            {"mol_id": "invalid_6", "smiles": "STOP"},
            {"mol_id": "invalid_7", "smiles": "HALT"},
            {"mol_id": "invalid_8", "smiles": "QUIT"},
            {"mol_id": "valid_3", "smiles": "CC(=O)O"},
        ]
        
        # 8 invalid out of 11 = ~72% failure rate > 10%
        with pytest.raises(RuntimeError, match="Failure rate.*exceeds threshold"):
            validate_and_process_dataset(test_data)
    
    def test_continue_on_low_failure_rate(self):
        """Test that processing continues when failure rate is below threshold."""
        # Create a dataset with <10% invalid SMILES
        test_data = [
            {"mol_id": "valid_1", "smiles": "CCO"},
            {"mol_id": "valid_2", "smiles": "c1ccccc1"},
            {"mol_id": "valid_3", "smiles": "CC(=O)O"},
            {"mol_id": "valid_4", "smiles": "C1CCCCC1"},
            {"mol_id": "invalid_1", "smiles": "INVALID"},
        ]
        
        # 1 invalid out of 5 = 20% failure rate > 10%
        # Let's make it 1 out of 11 = ~9%
        test_data = [
            {"mol_id": f"valid_{i}", "smiles": "CCO"} for i in range(10)
        ] + [{"mol_id": "invalid_1", "smiles": "INVALID"}]
        
        # Should not raise
        result = validate_and_process_dataset(test_data)
        assert result["statistics"]["failure_rate"] < FAILURE_THRESHOLD
        assert result["statistics"]["halt_required"] is False

class TestOutputPersistence:
    """Tests for output file persistence."""
    
    def test_output_file_created(self):
        """Test that output file is created when path is specified."""
        test_data = [
            {"mol_id": "valid_1", "smiles": "CCO"},
            {"mol_id": "valid_2", "smiles": "c1ccccc1"},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            
            result = validate_and_process_dataset(
                test_data,
                output_path=str(output_path)
            )
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert "successful_results" in saved_data
            assert "statistics" in saved_data
            assert saved_data["statistics"]["successful"] == 2
            assert saved_data["statistics"]["failed"] == 0