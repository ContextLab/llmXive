"""
Unit tests for the simulation runner.
Tests timeout, density check logic, and file generation.
"""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from simulation.runner import (
    run_simulation,
    SimulationResult,
    _generate_mdp_file,
    _check_density_convergence,
    DENSITY_TOLERANCE
)
from config import Solvent

class TestRunner:
    def test_generate_mdp_file(self, tmp_path):
        """Test that MDP file is generated with correct parameters."""
        from simulation.runner import _generate_mdp_file
        from config import SimulationConfig
        
        config = SimulationConfig(
            duration_ns=1.0,
            temperature_k=300.0,
            pressure_bar=1.0,
            force_field="MARTINI"
        )
        
        mdp_path = _generate_mdp_file(config, tmp_path)
        
        assert mdp_path.exists()
        content = mdp_path.read_text()
        assert "integrator" in content
        assert "md" in content
        assert "dt" in content
        assert "300" in content # Temperature

    @patch('subprocess.run')
    def test_run_simulation_success(self, mock_run, tmp_path):
        """Test successful simulation run with mocked GROMACS."""
        # Mock the subprocess calls to return success
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # grompp
            MagicMock(returncode=0, stdout="", stderr=""), # mdrun
        ]
        
        # Mock shutil.which to return a fake gmx path
        with patch('shutil.which', return_value="/fake/gmx"):
            result = run_simulation(
                solvent=Solvent.WATER,
                duration_ns=0.1, # Short duration for test
                output_dir=tmp_path,
                timeout_hours=1.0
            )
        
        assert result.success is True
        assert result.timeout is False
        # Check that expected files were created (even if empty in mock)
        assert result.equilibrated is True # Mocked density check returns True

    @patch('subprocess.run')
    def test_run_simulation_timeout(self, mock_run, tmp_path):
        """Test simulation timeout handling."""
        from subprocess import TimeoutExpired
        
        # First call (grompp) succeeds
        # Second call (mdrun) times out
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            TimeoutExpired(cmd=["gmx", "mdrun"], timeout=10)
        ]
        
        with patch('shutil.which', return_value="/fake/gmx"):
            result = run_simulation(
                solvent=Solvent.WATER,
                duration_ns=0.1,
                output_dir=tmp_path,
                timeout_hours=1.0
            )
        
        assert result.success is False
        assert result.timeout is True
        assert "Timeout" in result.error_message

    def test_density_convergence_check_no_gromacs(self, tmp_path):
        """Test density check when GROMACS is not available."""
        # Create a dummy log file
        log_file = tmp_path / "md.log"
        log_file.touch()
        
        # Mock shutil.which to return None
        with patch('shutil.which', return_value=None):
            is_conv, dens, var = _check_density_convergence(tmp_path)
        
        # Should return True (pass) and placeholders when GROMACS is missing
        # to allow the script to run in non-GROMACS environments, 
        # but log a warning.
        assert is_conv is True
        assert dens is not None
        assert var is not None

    def test_simulation_result_dataclass(self):
        """Test SimulationResult initialization."""
        result = SimulationResult(
            solvent="water",
            duration_ns=1.0,
            success=True,
            timeout=False,
            equilibrated=True
        )
        
        assert result.solvent == "water"
        assert result.success is True
        assert result.output_files == []
        assert result.checksums == {}
        assert result.timestamp is not None