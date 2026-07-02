"""
Unit tests for the ParameterPoint schema.

Tests cover:
- Initialization with valid parameters
- Validation of invalid parameters (negative/zero/non-finite)
- Serialization and deserialization (to_dict/from_dict)
- Observable validation
- Comprehensive validation function
"""

import pytest
import math
from code.schemas.parameter_point import ParameterPoint, validate_parameter_point


class TestParameterPointInitialization:
    """Tests for basic initialization and input validation."""
    
    def test_valid_initialization(self):
        """Test that a valid parameter point can be created."""
        point = ParameterPoint(m_dm=10.0, m_v=100.0, g=1e-3)
        assert point.m_dm == 10.0
        assert point.m_v == 100.0
        assert point.g == 1e-3
        assert point.is_viable is False
        assert point.omega_dm_h2 is None
        
    def test_negative_mass_fails(self):
        """Test that negative dark matter mass raises ValueError."""
        with pytest.raises(ValueError, match="m_dm must be positive"):
            ParameterPoint(m_dm=-10.0, m_v=100.0, g=1e-3)
            
    def test_zero_mass_fails(self):
        """Test that zero mass raises ValueError."""
        with pytest.raises(ValueError, match="m_dm must be positive"):
            ParameterPoint(m_dm=0.0, m_v=100.0, g=1e-3)
            
        with pytest.raises(ValueError, match="m_v must be positive"):
            ParameterPoint(m_dm=10.0, m_v=0.0, g=1e-3)
            
    def test_negative_coupling_fails(self):
        """Test that negative coupling raises ValueError."""
        with pytest.raises(ValueError, match="g must be positive"):
            ParameterPoint(m_dm=10.0, m_v=100.0, g=-1e-3)
            
    def test_non_finite_values_fails(self):
        """Test that non-finite values raise ValueError."""
        with pytest.raises(ValueError, match="must be finite"):
            ParameterPoint(m_dm=float('inf'), m_v=100.0, g=1e-3)
            
        with pytest.raises(ValueError, match="must be finite"):
            ParameterPoint(m_dm=10.0, m_v=float('nan'), g=1e-3)

class TestSerialization:
    """Tests for dictionary conversion methods."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12,
            delta_a_mu=2.5e-9,
            is_viable=True,
            constraints={"planck": True, "xenon": True}
        )
        
        data = point.to_dict()
        
        assert data["m_dm"] == 10.0
        assert data["m_v"] == 100.0
        assert data["g"] == 1e-3
        assert data["omega_dm_h2"] == 0.12
        assert data["delta_a_mu"] == 2.5e-9
        assert data["is_viable"] is True
        assert data["constraints"]["planck"] is True
        
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "m_dm": 15.0,
            "m_v": 200.0,
            "g": 2e-3,
            "omega_dm_h2": 0.11,
            "delta_a_mu": 3.0e-9,
            "sigma_si": 1e-45,
            "is_viable": True,
            "constraints": {"planck": True, "xenon": False, "lep": True},
            "notes": "Test point"
        }
        
        point = ParameterPoint.from_dict(data)
        
        assert point.m_dm == 15.0
        assert point.m_v == 200.0
        assert point.g == 2e-3
        assert point.omega_dm_h2 == 0.11
        assert point.delta_a_mu == 3.0e-9
        assert point.sigma_si == 1e-45
        assert point.is_viable is True
        assert point.notes == "Test point"
        
    def test_from_dict_missing_optional_fields(self):
        """Test that from_dict handles missing optional fields gracefully."""
        data = {
            "m_dm": 10.0,
            "m_v": 100.0,
            "g": 1e-3
        }
        
        point = ParameterPoint.from_dict(data)
        
        assert point.m_dm == 10.0
        assert point.m_v == 100.0
        assert point.g == 1e-3
        assert point.omega_dm_h2 is None
        assert point.delta_a_mu is None
        assert point.is_viable is False
        assert point.constraints == {}
        
    def test_round_trip(self):
        """Test that to_dict and from_dict are inverses."""
        original = ParameterPoint(
            m_dm=25.0,
            m_v=150.0,
            g=5e-4,
            omega_dm_h2=0.115,
            delta_a_mu=1.8e-9,
            sigma_si=5e-46,
            is_viable=True,
            constraints={"planck": True},
            notes="Round trip test"
        )
        
        data = original.to_dict()
        restored = ParameterPoint.from_dict(data)
        
        assert restored.m_dm == original.m_dm
        assert restored.m_v == original.m_v
        assert restored.g == original.g
        assert restored.omega_dm_h2 == original.omega_dm_h2
        assert restored.delta_a_mu == original.delta_a_mu
        assert restored.sigma_si == original.sigma_si
        assert restored.is_viable == original.is_viable
        assert restored.constraints == original.constraints
        assert restored.notes == original.notes

class TestObservableValidation:
    """Tests for the validate_observables method."""
    
    def test_valid_observables(self):
        """Test validation of valid observables."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12,
            delta_a_mu=2.5e-9,
            sigma_si=1e-45
        )
        
        assert point.validate_observables() is True
        
    def test_negative_omega_fails(self):
        """Test that negative omega_dm_h2 fails validation."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=-0.12
        )
        
        assert point.validate_observables() is False
        
    def test_negative_sigma_fails(self):
        """Test that negative sigma_si fails validation."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            sigma_si=-1e-45
        )
        
        assert point.validate_observables() is False
        
    def test_non_finite_observables_fails(self):
        """Test that non-finite observables fail validation."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=float('inf')
        )
        
        assert point.validate_observables() is False
        
    def test_none_observables_pass(self):
        """Test that None observables pass validation."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3
        )
        
        assert point.validate_observables() is True

class TestValidateParameterPointFunction:
    """Tests for the standalone validate_parameter_point function."""
    
    def test_valid_point(self):
        """Test validation of a valid point."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12,
            sigma_si=1e-45
        )
        
        is_valid, error = validate_parameter_point(point)
        
        assert is_valid is True
        assert error == ""
        
    def test_invalid_mass(self):
        """Test validation catches invalid mass."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3
        )
        point.m_v = -50.0
        
        is_valid, error = validate_parameter_point(point)
        
        assert is_valid is False
        assert "m_v" in error
        
    def test_invalid_constraints_type(self):
        """Test validation catches invalid constraints type."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3
        )
        point.constraints = "not a dict"
        
        is_valid, error = validate_parameter_point(point)
        
        assert is_valid is False
        assert "dictionary" in error
        
    def test_invalid_omega(self):
        """Test validation catches invalid omega."""
        point = ParameterPoint(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=-0.5
        )
        
        is_valid, error = validate_parameter_point(point)
        
        assert is_valid is False
        assert "omega_dm_h2" in error

class TestStringRepresentation:
    """Tests for string representation."""
    
    def test_str_format(self):
        """Test that __str__ returns a formatted string."""
        point = ParameterPoint(m_dm=10.0, m_v=100.0, g=1e-3)
        s = str(point)
        
        assert "ParameterPoint" in s
        assert "10.0" in s
        assert "100.0" in s
        assert "1e-03" in s or "0.001" in s
        assert "is_viable=False" in s