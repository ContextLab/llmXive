"""
Unit tests for dftb_calculator.py.

These tests verify the logic of SMILES conversion, input creation, and output parsing.
They do NOT run the actual DFTB+ binary to avoid external dependencies in unit tests.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Import the module under test
from code.dftb_calculator import (
    smiles_to_xyz,
    create_dftb_input,
    parse_dftb_output,
    calculate_descriptors_for_molecule,
    HARTREE_TO_EV
)
from code.utils.error_utils import ConvergenceError, OOMError


class TestSmilesToXyz:
    def test_invalid_smiles_raises_error(self):
        """Test that an invalid SMILES string raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test.xyz"
            with pytest.raises(ValueError):
                smiles_to_xyz("INVALID_SMILES", out_path)

    @patch('code.dftb_calculator.Chem')
    @patch('code.dftb_calculator.AllChem')
    def test_valid_smiles_creates_xyz(self, mock_allchem, mock_chem):
        """Test that a valid SMILES string creates an XYZ file."""
        # Mock RDKit objects
        mock_mol = MagicMock()
        mock_mol.GetNumAtoms.return_value = 2
        mock_conf = MagicMock()
        mock_atom = MagicMock()
        mock_atom.GetSymbol.return_value = "C"
        mock_mol.GetAtomWithIdx.return_value = mock_atom
        mock_conf.GetAtomPosition.return_value = MagicMock(x=0.0, y=0.0, z=0.0)
        mock_mol.GetConformer.return_value = mock_conf
        
        mock_chem.MolFromSmiles.return_value = mock_mol
        mock_chem.AddHs.return_value = mock_mol
        mock_allchem.ETKDGv3.return_value = MagicMock()
        mock_allchem.EmbedMolecule.return_value = 0
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test.xyz"
            smiles_to_xyz("CC", out_path)
            
            assert out_path.exists()
            with open(out_path, 'r') as f:
                content = f.read()
            assert "2" in content.split('\n')[0]  # Number of atoms


class TestCreateDftbInput:
    def test_creates_required_files(self):
        """Test that create_dftb_input creates geometry.gen and dftb_in.hsd."""
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            # Create a dummy geometry.gen
            (work_dir / "geometry.gen").touch()
            
            inputs = create_dftb_input(work_dir / "geometry.gen", work_dir)
            
            assert "geometry" in inputs
            assert "hsd" in inputs
            assert inputs["geometry"].exists()
            assert inputs["hsd"].exists()
            
            # Check content of dftb_in.hsd
            with open(inputs["hsd"], 'r') as f:
                content = f.read()
            assert "Hamiltonian = GFN2-xTB" in content
            assert "MaxCycles = 100" in content


class TestParseDftbOutput:
    def test_missing_output_file_raises_error(self):
        """Test that parse_dftb_output raises ValueError if dftb_out is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            with pytest.raises(ValueError):
                parse_dftb_output(work_dir)

    def test_parses_homo_lumo_from_text(self):
        """Test parsing HOMO/LUMO from a mock dftb_out content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            out_file = work_dir / "dftb_out"
            
            mock_content = """
            Total energy = -100.5 Hartree
            HOMO energy = -0.45
            LUMO energy = -0.10
            Some other text...
            """
            with open(out_file, 'w') as f:
                f.write(mock_content)
            
            result = parse_dftb_output(work_dir)
            
            assert result["homo_energy"] == -0.45 * HARTREE_TO_EV
            assert result["lumo_energy"] == -0.10 * HARTREE_TO_EV
            assert result["total_energy"] == -100.5 * HARTREE_TO_EV

    def test_parses_mayer_bonds_from_text(self):
        """Test parsing Mayer bond orders from a mock dftb_out content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            out_file = work_dir / "dftb_out"
            
            mock_content = """
            Mayer Bond Order Matrix:
            1 2 0.50
            1 3 0.10
            2 3 0.00
            """
            with open(out_file, 'w') as f:
                f.write(mock_content)
            
            result = parse_dftb_output(work_dir)
            
            # Check that we got some bonds
            assert len(result["mayer_bond_orders"]) >= 3
            # Check specific values
            bond_map = {(b[0], b[1]): b[2] for b in result["mayer_bond_orders"]}
            assert (1, 2) in bond_map
            assert abs(bond_map[(1, 2)] - 0.50) < 1e-6


class TestCalculateDescriptorsForMolecule:
    @patch('code.dftb_calculator.smiles_to_xyz')
    @patch('code.dftb_calculator.create_dftb_input')
    @patch('code.dftb_calculator.run_dftb_work')
    @patch('code.dftb_calculator.parse_dftb_output')
    def test_success_path(self, mock_parse, mock_run, mock_create, mock_xyz):
        """Test the full success path with mocked dependencies."""
        mock_parse.return_value = {
            "homo_energy": -0.5,
            "lumo_energy": -0.1,
            "mayer_bond_orders": [],
            "total_energy": -100.0
        }
        
        result = calculate_descriptors_for_molecule("CC", "test_001")
        
        assert result["status"] == "success"
        assert result["molecule_id"] == "test_001"
        assert result["smiles"] == "CC"
        mock_run.assert_called_once()
        mock_parse.assert_called_once()

    @patch('code.dftb_calculator.smiles_to_xyz')
    @patch('code.dftb_calculator.create_dftb_input')
    @patch('code.dftb_calculator.run_dftb_work')
    def test_convergence_failure_propagates(self, mock_run, mock_create, mock_xyz):
        """Test that ConvergenceError is propagated."""
        mock_run.side_effect = ConvergenceError("Did not converge")
        
        with pytest.raises(ConvergenceError):
            calculate_descriptors_for_molecule("CC", "test_001")

    @patch('code.dftb_calculator.smiles_to_xyz')
    @patch('code.dftb_calculator.create_dftb_input')
    @patch('code.dftb_calculator.run_dftb_work')
    def test_oom_failure_propagates(self, mock_run, mock_create, mock_xyz):
        """Test that OOMError is propagated."""
        mock_run.side_effect = OOMError("Out of memory")
        
        with pytest.raises(OOMError):
            calculate_descriptors_for_molecule("CC", "test_001")