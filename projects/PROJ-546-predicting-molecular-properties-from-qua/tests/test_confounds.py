import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
from rdkit import Chem

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from confounds import (
    load_molecules_from_csv,
    parse_functional_groups,
    calculate_molecular_properties,
    process_molecule,
    write_confounds_csv,
    verify_distribution_stats,
    generate_coverage_report
)

@pytest.fixture
def sample_csv(tmp_path):
    csv_path = tmp_path / "test_input.csv"
    data = {
        "molecule_id": ["mol1", "mol2", "mol3"],
        "SMILES": ["CCO", "c1ccccc1", "CC(=O)O"],
        "experimental_barrier": [10.0, 15.0, 20.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_load_molecules_from_csv(sample_csv):
    df = load_molecules_from_csv(sample_csv)
    assert "molecule_id" in df.columns
    assert "SMILES" in df.columns
    assert len(df) == 3
    assert df.iloc[0]["molecule_id"] == "mol1"

def test_parse_functional_groups():
    # Ethanol: H-Donor, H-Acceptor
    mol = Chem.MolFromSmiles("CCO")
    groups = parse_functional_groups(mol)
    assert "H-Donor" in groups
    assert "H-Acceptor" in groups

    # Benzene: AromaticRing
    mol = Chem.MolFromSmiles("c1ccccc1")
    groups = parse_functional_groups(mol)
    assert "AromaticRing" in groups

    # Acetic Acid: CarboxylicAcid, H-Donor, H-Acceptor
    mol = Chem.MolFromSmiles("CC(=O)O")
    groups = parse_functional_groups(mol)
    assert "CarboxylicAcid" in groups

def test_calculate_molecular_properties():
    mol = Chem.MolFromSmiles("CCO")
    props = calculate_molecular_properties(mol)
    assert props["mw"] is not None
    assert props["atom_count"] == 9  # C2H6O
    assert "functional_groups" in props

def test_process_molecule():
    res = process_molecule("CCO", "test_id", None) # Logger can be None for this test
    assert res is not None
    assert res["molecule_id"] == "test_id"
    assert res["mw"] is not None

def test_process_molecule_invalid_smiles(caplog):
    # We can't easily capture caplog without a real logger setup, but we can check return
    res = process_molecule("invalid_smiles", "test_id", None)
    assert res is None

def test_write_confounds_csv(tmp_path):
    data = [
        {"molecule_id": "mol1", "mw": 46.07, "atom_count": 9, "functional_groups": "H-Donor"},
        {"molecule_id": "mol2", "mw": 78.11, "atom_count": 12, "functional_groups": "AromaticRing"}
    ]
    output_path = tmp_path / "output.csv"
    write_confounds_csv(data, output_path)

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert list(df.columns) == ["molecule_id", "mw", "atom_count", "functional_groups"]

def test_verify_distribution_stats():
    data = [
        {"mw": 10.0, "atom_count": 5},
        {"mw": 20.0, "atom_count": 10},
        {"mw": 30.0, "atom_count": 15}
    ]
    stats = verify_distribution_stats(data, None)
    assert "mw_mean" in stats
    assert stats["mw_mean"] == 20.0
    assert "atom_mean" in stats
    assert stats["atom_mean"] == 10.0

def test_generate_coverage_report(tmp_path):
    data = [
        {"mw": 10.0, "atom_count": 5, "functional_groups": "Group1"},
        {"mw": 20.0, "atom_count": 10, "functional_groups": "Group2"}
    ]
    stats = {"mw_mean": 15.0, "atom_mean": 7.5}
    report_path = tmp_path / "report.md"
    generate_coverage_report(stats, report_path, None)

    assert report_path.exists()
    content = report_path.read_text()
    assert "Confounds Coverage Verification Report" in content
    assert "Status: PASS" in content