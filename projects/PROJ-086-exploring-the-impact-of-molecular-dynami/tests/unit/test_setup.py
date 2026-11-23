"""
Unit tests for code/simulation/setup.py

Tests solvation logic, force field loading, and basic topology generation.
Does NOT run the full MD simulation (that is integration testing).
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We assume the project root is in sys.path or we run from project root
from code.simulation.setup import (
    load_pdb_structure,
    create_system,
    run_setup,
    SetupError
)

from openmm import unit
from openmm.app import PDBFile

# Test fixtures
@pytest.fixture
def temp_pdb_dir(tmp_path):
    """Create a temporary directory with a minimal valid PDB file."""
    pdb_content = """HEADER    TEST
    ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N  
    ATOM      2  CA  ALA A   1       1.000   0.000   0.000  1.00  0.00           C  
    ATOM      3  C   ALA A   1       1.500   1.000   0.000  1.00  0.00           C  
    ATOM      4  O   ALA A   1       2.500   1.000   0.000  1.00  0.00           O  
    TER
    END
    """
    pdb_file = tmp_path / "1J22.pdb"
    pdb_file.write_text(pdb_content)
    return tmp_path, pdb_file

@pytest.fixture
def invalid_pdb_dir(tmp_path):
    """Create a temporary directory with an empty/invalid PDB file."""
    pdb_file = tmp_path / "empty.pdb"
    pdb_file.write_text("HEADER    EMPTY\nEND\n")
    return tmp_path, pdb_file

class TestLoadPdbStructure:
    def test_load_valid_pdb(self, temp_pdb_dir):
        _, pdb_path = temp_pdb_dir
        traj, pdb_id = load_pdb_structure(pdb_path)
        
        assert traj is not None
        assert len(traj) > 0
        assert pdb_id == "1J22"
    
    def test_load_missing_file(self, temp_pdb_dir):
        _, pdb_path = temp_pdb_dir
        fake_path = pdb_path.parent / "nonexistent.pdb"
        
        with pytest.raises(SetupError, match="not found"):
            load_pdb_structure(fake_path)
    
    def test_load_empty_pdb(self, invalid_pdb_dir):
        _, pdb_path = invalid_pdb_dir
        
        # Should raise because no heavy atoms or no frames
        with pytest.raises(SetupError):
            load_pdb_structure(pdb_path)

class TestCreateSystem:
    def test_solvation_and_neutralization(self, temp_pdb_dir):
        _, pdb_path = temp_pdb_dir
        
        topology, system, metadata = create_system(
            pdb_path=pdb_path,
            force_field_name="ff14SB",
            padding=1.0 * unit.nanometer
        )
        
        assert topology is not None
        assert system is not None
        assert metadata["solvated"] is True
        assert metadata["force_field"] == "ff14SB"
        # Check that atom count increased (due to water)
        # Original PDB has 4 atoms. Solvated should have many more.
        assert metadata["num_atoms"] > 10
    
    def test_invalid_force_field(self, temp_pdb_dir):
        _, pdb_path = temp_pdb_dir
        
        with pytest.raises(SetupError, match="Unsupported force field"):
            create_system(pdb_path, force_field_name="FakeFF")

class TestRunSetup:
    def test_run_setup_success(self, temp_pdb_dir):
        _, pdb_path = temp_pdb_dir
        output_dir = temp_pdb_dir / "output"
        
        result = run_setup(
            pdb_path=pdb_path,
            force_field="ff14SB",
            output_dir=output_dir
        )
        
        assert result["status"] == "success"
        assert result["pdb_id"] == "1J22"
        assert Path(result["output_pdb"]).exists()
    
    def test_run_setup_missing_file(self, temp_pdb_dir):
        _, pdb_path = temp_pdb_dir
        output_dir = temp_pdb_dir / "output"
        fake_path = pdb_path.parent / "missing.pdb"
        
        with pytest.raises(SetupError):
            run_setup(pdb_path=fake_path, output_dir=output_dir)
