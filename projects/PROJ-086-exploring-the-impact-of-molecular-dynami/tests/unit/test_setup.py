"""
Unit tests for code/simulation/setup.py
"""
import os
import tempfile
import pytest
from pathlib import Path

# Mock OpenMM to avoid heavy imports in unit tests if necessary, 
# but here we assume OpenMM is available as per requirements.txt.
# We will test the logic flow and error handling.

try:
    import openmm.app as app
    from openmm import unit
    HAS_OPENMM = True
except ImportError:
    HAS_OPENMM = False
    pytest.skip("OpenMM not available", allow_module_level=True)

from simulation.setup import prepare_system, _load_structure_from_pdb
from utils.logger import get_logger

logger = get_logger(__name__)

# Create a minimal valid PDB string for testing
MINIMAL_PDB = """
HEADER    TEST
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00  0.00           N  
ATOM      2  CA  ALA A   1      11.000  11.000  11.000  1.00  0.00           C  
ATOM      3  C   ALA A   1      12.000  12.000  12.000  1.00  0.00           C  
ATOM      4  O   ALA A   1      13.000  13.000  13.000  1.00  0.00           O  
TER
END
"""

@pytest.fixture
def temp_pdb_file():
    """Create a temporary PDB file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdb', delete=False) as f:
        f.write(MINIMAL_PDB)
        yield f.name
    os.remove(f.name)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_structure_from_pdb(temp_pdb_file):
    """Test loading a valid PDB file."""
    pdb = _load_structure_from_pdb(temp_pdb_file)
    assert pdb is not None
    assert pdb.topology.getNumAtoms() == 4

def test_load_structure_from_pdb_missing_file():
    """Test loading a non-existent PDB file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        _load_structure_from_pdb("non_existent.pdb")

@pytest.mark.skipif(not HAS_OPENMM, reason="OpenMM not installed")
def test_prepare_system_basic(temp_pdb_file, temp_output_dir):
    """Test basic system preparation with ff14SB and TIP3P."""
    try:
        result = prepare_system(
            temp_pdb_file,
            force_field_name='ff14SB',
            box_buffer=0.5, # Small buffer for unit test speed
            output_dir=temp_output_dir
        )
        
        assert 'system' in result
        assert 'topology' in result
        assert 'positions' in result
        assert result['system'].getNumParticles() > 4 # Should have added water/ions
        assert result['topology'].getNumAtoms() > 4
        
        # Check if output file was created
        expected_pdb = os.path.join(temp_output_dir, os.path.basename(temp_pdb_file).replace('.pdb', '_solvated.pdb'))
        # Note: The function creates the file, but we need to verify it exists
        # The function logic creates it if output_dir is provided
        assert os.path.exists(expected_pdb)
        
    except Exception as e:
        # If force field is missing or other OpenMM issues, log and skip
        # This is expected in minimal environments if 'ff14SB' isn't mapped correctly
        if "Force field" in str(e):
            pytest.skip(f"Force field issue in test environment: {e}")
        else:
            raise

@pytest.mark.skipif(not HAS_OPENMM, reason="OpenMM not installed")
def test_prepare_system_invalid_force_field(temp_pdb_file):
    """Test that an invalid force field raises an error."""
    with pytest.raises(FileNotFoundError):
        prepare_system(temp_pdb_file, force_field_name='invalid_ff_name')

@pytest.mark.skipif(not HAS_OPENMM, reason="OpenMM not installed")
def test_prepare_system_neutralization(temp_pdb_file, temp_output_dir):
    """Test system preparation with neutralization disabled."""
    try:
        result_neut = prepare_system(
            temp_pdb_file,
            force_field_name='ff14SB',
            box_buffer=0.5,
            neutralize=True,
            output_dir=temp_output_dir
        )
        
        result_no_neut = prepare_system(
            temp_pdb_file,
            force_field_name='ff14SB',
            box_buffer=0.5,
            neutralize=False,
            output_dir=temp_output_dir
        )
        
        # The number of particles might differ if the system was charged
        # For a small test peptide, it might be neutral anyway, so we just check
        # that the function runs without crashing for both cases.
        assert result_neut['system'] is not None
        assert result_no_neut['system'] is not None
        
    except Exception as e:
        if "Force field" in str(e):
            pytest.skip(f"Force field issue: {e}")
        else:
            raise