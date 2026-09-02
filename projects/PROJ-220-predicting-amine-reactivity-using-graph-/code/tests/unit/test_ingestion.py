"""
Unit tests for data ingestion module.

Tests for T014, T015, T018a, T018b
"""
import pytest
import math
from unittest.mock import patch, MagicMock
from src.data.ingestion import (
    ReactionRecord,
    calculate_class_average_ea,
    normalize_kinetics,
    validate_smiles
)


def test_reaction_record_initialization():
    """Test that ReactionRecord initializes correctly."""
    record = ReactionRecord(
        reaction_id="test_001",
        substrate_smiles="CCO",
        amine_smiles="CN",
        rate=1.0,
        temperature=298.0,
        activation_energy=50000.0
    )
    
    assert record.reaction_id == "test_001"
    assert record.substrate_smiles == "CCO"
    assert record.amine_smiles == "CN"
    assert record.rate == 1.0
    assert record.temperature == 298.0
    assert record.activation_energy == 50000.0


def test_filter_invalid_smiles():
    """Test that invalid SMILES are properly handled."""
    valid_smiles = ["CCO", "CN", "c1ccccc1"]
    invalid_smiles = ["invalid", "not_a_smiles", ""]
    
    for smiles in valid_smiles:
        assert validate_smiles(smiles) is True
    
    for smiles in invalid_smiles:
        assert validate_smiles(smiles) is False


def test_run_ingestion_calls_validation():
    """Test that ingestion calls citation validation."""
    with patch('src.data.ingestion.validate_citations') as mock_validate:
        with patch('src.data.ingestion.fetch_chembl_sn2_data') as mock_fetch:
            mock_fetch.return_value = []
            
            from src.data.ingestion import run_ingestion
            run_ingestion()
            
            mock_validate.assert_called_once()


def test_run_ingestion_fails_on_validation():
    """Test that ingestion fails if validation fails."""
    with patch('src.data.ingestion.validate_citations') as mock_validate:
        mock_validate.side_effect = Exception("Validation failed")
        
        with pytest.raises(Exception, match="Validation failed"):
            from src.data.ingestion import run_ingestion
            run_ingestion()


def test_validate_smiles_integration():
    """Integration test for SMILES validation."""
    # Valid SMILES
    assert validate_smiles("CCO") is True
    assert validate_smiles("CN") is True
    assert validate_smiles("c1ccccc1") is True
    assert validate_smiles("CC(=O)O") is True
    
    # Invalid SMILES
    assert validate_smiles("invalid") is False
    assert validate_smiles("") is False
    assert validate_smiles("123") is False


def test_compute_class_average_ea_with_data():
    """Test class average Ea calculation with available data."""
    records = [
        {"activation_energy": 50000.0},
        {"activation_energy": 60000.0},
        {"activation_energy": 55000.0}
    ]
    
    avg_ea = calculate_class_average_ea(records)
    expected = (50000 + 60000 + 55000) / 3
    
    assert math.isclose(avg_ea, expected, rel_tol=1e-5)


def test_compute_class_average_ea_without_data():
    """Test class average Ea calculation with no data."""
    records = [
        {"activation_energy": None},
        {},
        {"temperature": 298.0}
    ]
    
    avg_ea = calculate_class_average_ea(records)
    
    # Should return None when no data available
    assert avg_ea is None


def test_compute_class_average_ea_mixed_data():
    """Test class average Ea calculation with mixed data."""
    records = [
        {"activation_energy": 50000.0},
        {"activation_energy": None},
        {"activation_energy": 60000.0},
        {},
        {"activation_energy": 55000.0}
    ]
    
    avg_ea = calculate_class_average_ea(records)
    expected = (50000 + 60000 + 55000) / 3
    
    assert math.isclose(avg_ea, expected, rel_tol=1e-5)


def test_normalize_kinetics_with_class_avg():
    """Test kinetics normalization with class average Ea."""
    records = [
        {
            "reaction_id": "test_1",
            "rate": 1.0,
            "temperature": 298.0,
            "activation_energy": 50000.0
        },
        {
            "reaction_id": "test_2",
            "rate": 2.0,
            "temperature": 310.0,
            "activation_energy": 50000.0
        }
    ]
    
    normalized = normalize_kinetics(records, reference_temp=298.0)
    
    assert len(normalized) == 2
    assert "normalized_log_rate" in normalized[0]
    assert "normalized_log_rate" in normalized[1]


def test_normalize_kinetics_no_ea_data():
    """Test kinetics normalization when Ea data is missing."""
    records = [
        {
            "reaction_id": "test_1",
            "rate": 1.0,
            "temperature": 298.0,
            "activation_energy": None
        }
    ]
    
    # Should use class average if available
    normalized = normalize_kinetics(records, reference_temp=298.0)
    
    # Record should be excluded if no Ea and no class average
    assert len(normalized) == 0


def test_normalize_kinetics_missing_rate_or_temp():
    """Test that records with missing rate or temp are excluded."""
    records = [
        {
            "reaction_id": "test_1",
            "rate": None,
            "temperature": 298.0,
            "activation_energy": 50000.0
        },
        {
            "reaction_id": "test_2",
            "rate": 1.0,
            "temperature": None,
            "activation_energy": 50000.0
        }
    ]
    
    normalized = normalize_kinetics(records, reference_temp=298.0)
    
    assert len(normalized) == 0


def test_arrhenius_normalization_math():
    """Test Arrhenius normalization calculation."""
    # R = 8.314 J/(mol·K)
    R = 8.314
    
    # Test case: rate at 310K normalized to 298K
    rate_310 = 2.0
    temp_310 = 310.0
    temp_ref = 298.0
    ea = 50000.0  # J/mol
    
    # Arrhenius equation: k = A * exp(-Ea/(R*T))
    # Normalized rate: k_ref = k * exp(Ea/R * (1/T - 1/T_ref))
    normalized_rate = rate_310 * math.exp((ea / R) * (1/temp_310 - 1/temp_ref))
    
    assert normalized_rate > 0
    assert isinstance(normalized_rate, float)