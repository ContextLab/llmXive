"""
Unit tests for energy parsing logic in run_psi4.py.

Tests the extraction of total energy and D3 dispersion contribution
from Psi4 output strings.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.run_psi4 import parse_psi4_output


class TestParsePsi4Output:
    """Tests for the parse_psi4_output function."""

    def test_parse_valid_output_with_d3(self):
        """Test parsing a valid Psi4 output containing D3 dispersion."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        ...
        Final Energy: -100.54321
        ...
        D3 dispersion energy: -0.12345
        ...
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is not None
        assert "total_energy" in result
        assert "d3_energy" in result
        assert np.isclose(result["total_energy"], -100.54321)
        assert np.isclose(result["d3_energy"], -0.12345)

    def test_parse_valid_output_without_d3(self):
        """Test parsing a valid Psi4 output without D3 dispersion."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        ...
        Final Energy: -100.54321
        ...
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is not None
        assert "total_energy" in result
        assert "d3_energy" in result
        assert np.isclose(result["total_energy"], -100.54321)
        assert result["d3_energy"] is None

    def test_parse_output_with_cp_correction(self):
        """Test parsing output with counterpoise correction."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        ...
        Counterpoise: BSSE correction applied
        Final Energy (CP): -100.54321
        ...
        D3 dispersion energy: -0.12345
        ...
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is not None
        assert "total_energy" in result
        assert "d3_energy" in result
        assert np.isclose(result["total_energy"], -100.54321)
        assert np.isclose(result["d3_energy"], -0.12345)

    def test_parse_output_with_missing_energy(self):
        """Test parsing output where energy is missing."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        ...
        Calculation failed
        ...
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is None

    def test_parse_output_with_different_energy_formats(self):
        """Test parsing output with various energy format representations."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        ...
        Final Energy: -1.234567e+02
        ...
        D3 dispersion energy: -1.234567e-01
        ...
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is not None
        assert "total_energy" in result
        assert "d3_energy" in result
        assert np.isclose(result["total_energy"], -123.4567)
        assert np.isclose(result["d3_energy"], -0.1234567)

    def test_parse_output_with_whitespace_variations(self):
        """Test parsing output with various whitespace patterns."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        
        Final Energy  :   -100.54321
        
        D3 dispersion energy  :  -0.12345
        
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is not None
        assert "total_energy" in result
        assert "d3_energy" in result
        assert np.isclose(result["total_energy"], -100.54321)
        assert np.isclose(result["d3_energy"], -0.12345)

    def test_parse_output_with_empty_string(self):
        """Test parsing an empty output string."""
        psi4_output = ""
        
        result = parse_psi4_output(psi4_output)
        
        assert result is None

    def test_parse_output_with_none(self):
        """Test parsing None input."""
        result = parse_psi4_output(None)
        
        assert result is None

    def test_parse_output_with_corrupted_data(self):
        """Test parsing corrupted or malformed output."""
        psi4_output = "This is not a valid Psi4 output file"
        
        result = parse_psi4_output(psi4_output)
        
        assert result is None

    def test_parse_output_with_partial_d3_info(self):
        """Test parsing output with partial D3 information."""
        psi4_output = """
        Psi4: An Ab Initio Quantum Chemistry Package
        ...
        Final Energy: -100.54321
        ...
        D3 dispersion: -0.12345
        ...
        """
        
        result = parse_psi4_output(psi4_output)
        
        assert result is not None
        assert "total_energy" in result
        # The parser should handle variations in D3 labeling
        assert "d3_energy" in result
        assert result["d3_energy"] is not None or np.isclose(result["d3_energy"], -0.12345)