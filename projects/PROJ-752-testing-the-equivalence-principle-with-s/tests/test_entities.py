"""
Unit tests for the data model entities defined in code/models/entities.py.
"""
import pytest
import numpy as np
from datetime import datetime
import json

# Import the entities
from models.entities import NormalPoint, OrbitSolution, EotvosResult


class TestNormalPoint:
    def test_normal_point_creation(self):
        """Test that a NormalPoint can be created with valid data."""
        np_obs = NormalPoint(
            timestamp=datetime(2023, 10, 27, 12, 0, 0),
            range=23500000.5,
            satellite_id="LAGEOS",
            station_id="7110",
            quality_flag=0
        )
        
        assert np_obs.satellite_id == "LAGEOS"
        assert np_obs.quality_flag == 0
        assert np_obs.range > 0

    def test_normal_point_to_dict(self):
        """Test serialization of NormalPoint."""
        np_obs = NormalPoint(
            timestamp=datetime(2023, 10, 27, 12, 0, 0),
            range=23500000.5,
            satellite_id="LAGEOS",
            station_id="7110",
            quality_flag=0
        )
        
        data = np_obs.to_dict()
        
        assert "timestamp" in data
        assert data["range"] == 23500000.5
        assert data["satellite_id"] == "LAGEOS"
        # Verify JSON serializability
        json_str = json.dumps(data)
        assert len(json_str) > 0


class TestOrbitSolution:
    def test_orbit_solution_creation(self):
        """Test that an OrbitSolution can be created with valid data."""
        state = np.zeros(6)
        accel = np.zeros(3)
        cov = np.eye(6)
        
        sol = OrbitSolution(
            state_vector=state,
            non_gravitational_acceleration=accel,
            covariance_matrix=cov,
            chi2=1.5,
            residuals=np.array([0.01, -0.02, 0.005]),
            converged=True,
            iterations=10
        )
        
        assert sol.converged is True
        assert sol.chi2 > 0
        assert len(sol.state_vector) == 6

    def test_orbit_solution_to_dict(self):
        """Test serialization of OrbitSolution."""
        state = np.array([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])
        accel = np.array([1e-6, 0, 0])
        cov = np.eye(6)
        
        sol = OrbitSolution(
            state_vector=state,
            non_gravitational_acceleration=accel,
            covariance_matrix=cov,
            chi2=1.2,
            residuals=np.array([0.01, -0.02])
        )
        
        data = sol.to_dict()
        
        assert "state_vector" in data
        assert isinstance(data["state_vector"], list)
        assert data["converged"] is True
        
        # Verify JSON serializability
        json_str = json.dumps(data)
        assert len(json_str) > 0


class TestEotvosResult:
    def test_eotvos_result_creation(self):
        """Test that an EotvosResult can be created with valid data."""
        result = EotvosResult(
            eta_value=1e-14,
            confidence_interval=[0.5e-14, 1.5e-14],
            p_value=0.03,
            status="Valid"
        )
        
        assert result.eta_value > 0
        assert result.p_value >= 0
        assert result.confidence_interval[0] < result.confidence_interval[1]

    def test_eotvos_result_to_dict(self):
        """Test serialization of EotvosResult."""
        result = EotvosResult(
            eta_value=2.5e-13,
            confidence_interval=[2.0e-13, 3.0e-13],
            p_value=0.001,
            delta_chi2=15.5,
            f_statistic=4.2,
            status="Valid"
        )
        
        data = result.to_dict()
        
        assert "eta_value" in data
        assert "delta_chi2" in data
        assert data["status"] == "Valid"
        
        # Verify JSON serializability
        json_str = json.dumps(data)
        assert len(json_str) > 0

    def test_eotvos_result_with_sensitivity(self):
        """Test serialization with optional sensitivity sweep data."""
        sweep_data = {
            "model_GGM": 1.2e-13,
            "model_EGM2008": 1.3e-13
        }
        
        result = EotvosResult(
            eta_value=1.25e-13,
            confidence_interval=[1.0e-13, 1.5e-13],
            p_value=0.05,
            sensitivity_sweep_data=sweep_data
        )
        
        data = result.to_dict()
        
        assert "sensitivity_sweep_data" in data
        assert data["sensitivity_sweep_data"]["model_GGM"] == 1.2e-13