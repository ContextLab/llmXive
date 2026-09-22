"""
Unit tests for the GFN2-xTB wrapper in code/data/energy_calc.py.

This test verifies that the wrapper correctly invokes the xtb binary on a real
molecule (benzene) and returns an XtbResult object with the expected structure.

It relies on the 'xtb' binary being available in the system PATH.
"""
import os
import tempfile
import subprocess
import pytest
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem

# Import the module under test
from data.energy_calc import run_xtb_optimization, XtbResult
from data.xtb_metadata import archive_calculation, get_xtb_version
from utils.logging import get_project_logger
from utils.seeds import set_global_seed

# Set a fixed seed for any random operations in the test setup
set_global_seed(42)

# Logger for the test
logger = get_project_logger("test_energy_calc")

def create_benzene_xyz(temp_dir: Path) -> Path:
    """
    Creates a benzene molecule and writes it to an XYZ file in temp_dir.
    Returns the path to the XYZ file.
    """
    # Create benzene SMILES
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Failed to create benzene molecule from SMILES")

    # Add hydrogens
    mol = Chem.AddHs(mol)

    # Generate 3D coordinates using ETKDG
    params = AllChem.ETKDGv3()
    params.seed = 42
    success = AllChem.EmbedMolecule(mol, params)
    if success == -1:
        # Fallback to basic embedding if ETKDG fails
        success = AllChem.EmbedMolecule(mol)
        if success == -1:
            raise RuntimeError("Failed to generate 3D conformer for benzene")

    # Optimize geometry with MMFF94 to get a reasonable starting point
    AllChem.MMFFOptimizeMolecule(mol)

    # Write to XYZ
    xyz_path = temp_dir / "benzene.xyz"
    with open(xyz_path, "w") as f:
        # Write number of atoms
        f.write(f"{mol.GetNumAtoms()}\n")
        f.write("Benzene initial geometry\n")
        # Write atoms
        conf = mol.GetConformer()
        for atom in mol.GetAtoms():
            pos = conf.GetAtomPosition(atom.GetIdx())
            symbol = atom.GetSymbol()
            f.write(f"{symbol} {pos.x:.6f} {pos.y:.6f} {pos.z:.6f}\n")

    return xyz_path

@pytest.fixture
def benzene_xyz_path():
    """Fixture to create a temporary benzene XYZ file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        xyz_file = create_benzene_xyz(temp_path)
        yield xyz_file

def test_xtb_binary_available():
    """Check if the xtb binary is available in the system PATH."""
    try:
        result = subprocess.run(["xtb", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            pytest.fail("xtb binary exists but returned non-zero for --version")
        logger.info(f"xtb version found: {result.stdout.strip()}")
    except FileNotFoundError:
        pytest.skip("xtb binary not found in PATH. Skipping xtb integration test.")
    except subprocess.TimeoutExpired:
        pytest.skip("xtb --version timed out. Skipping xtb integration test.")

def test_run_xtb_optimization_benzene(benzene_xyz_path):
    """
    Test run_xtb_optimization on benzene.
    Verifies that:
    1. The function returns an XtbResult object.
    2. The energy is a float.
    3. The status is 'converged' or 'success' (depending on xtb output).
    4. The output file exists.
    """
    # Ensure xtb is available before running the main test logic
    try:
        subprocess.run(["xtb", "--version"], capture_output=True, timeout=10, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("xtb not available, skipping optimization test")

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        out_prefix = "benzene_opt"

        logger.info(f"Running xtb optimization on {benzene_xyz_path} -> {out_dir}")

        try:
            result = run_xtb_optimization(
                input_path=str(benzene_xyz_path),
                out_dir=str(out_dir),
                out_prefix=out_prefix,
                max_iterations=50,
                timeout_seconds=120
            )
        except subprocess.TimeoutExpired:
            pytest.fail("xtb optimization timed out")
        except Exception as e:
            pytest.fail(f"xtb optimization failed with unexpected error: {e}")

        # Assertions
        assert isinstance(result, XtbResult), f"Expected XtbResult, got {type(result)}"
        assert isinstance(result.energy, float), f"Expected energy to be float, got {type(result.energy)}"
        assert result.status in ["converged", "success"], f"Unexpected status: {result.status}"
        assert result.energy < 0, "Energy should be negative for a stable molecule"

        # Check that the output file was created
        expected_output = out_dir / f"{out_prefix}.xyz"
        assert expected_output.exists(), f"Output file {expected_output} was not created"

        logger.info(f"Optimization successful. Energy: {result.energy:.4f} Ha, Status: {result.status}")

def test_run_xtb_optimization_invalid_input():
    """Test that run_xtb_optimization raises an error for invalid input file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = Path(tmpdir) / "nonexistent.xyz"
        out_dir = Path(tmpdir)

        with pytest.raises((FileNotFoundError, subprocess.CalledProcessError)):
            run_xtb_optimization(
                input_path=str(invalid_path),
                out_dir=str(out_dir),
                out_prefix="test",
                timeout_seconds=10
            )

def test_run_xtb_optimization_metadata_archived(benzene_xyz_path):
    """
    Test that xtb metadata is archived correctly after a successful run.
    This depends on T009b implementation.
    """
    try:
        subprocess.run(["xtb", "--version"], capture_output=True, timeout=10, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("xtb not available, skipping metadata test")

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        out_prefix = "benzene_meta"

        result = run_xtb_optimization(
            input_path=str(benzene_xyz_path),
            out_dir=str(out_dir),
            out_prefix=out_prefix,
            timeout_seconds=120
        )

        # Archive the metadata
        metadata_path = archive_calculation(
            result=result,
            input_path=str(benzene_xyz_path),
            out_dir=str(out_dir),
            flags="--gfn 2"
        )

        assert metadata_path.exists(), f"Metadata file {metadata_path} was not created"

        import json
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        assert "calculation_id" in metadata
        assert "timestamp" in metadata
        assert "xtb_version" in metadata
        assert "energy" in metadata
        assert "status" in metadata
        assert "input_file" in metadata
        assert "output_file" in metadata

        logger.info(f"Metadata archived successfully: {metadata_path}")