import pytest
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch_data import compute_sha256, verify_checksum
from confounds import load_molecules_from_csv, calculate_molecular_properties

def test_checksum_computation():
    """Test that checksum computation works on a real file."""
    # Create a temp file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    try:
        hash_val = compute_sha256(tmp_path)
        assert len(hash_val) == 64  # SHA256 hex length
        assert isinstance(hash_val, str)
    finally:
        tmp_path.unlink()

def test_csv_loading_structure():
    """Test that the loader expects the correct columns."""
    # Create a temp CSV
    import tempfile
    import csv
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        writer = csv.writer(tmp)
        writer.writerow(['molecule_id', 'SMILES', 'experimental_barrier'])
        writer.writerow(['mol1', 'CCO', '1.5'])
        tmp_path = Path(tmp.name)
    
    try:
        data = load_molecules_from_csv(tmp_path)
        assert len(data) == 1
        assert data[0]['SMILES'] == 'CCO'
    finally:
        tmp_path.unlink()

def test_molecular_properties_calculation():
    """Test that properties can be calculated for a valid SMILES."""
    # Requires RDKit
    try:
        from rdkit import Chem
        props = calculate_molecular_properties('CCO')
        assert props['mw'] > 0
        assert props['atom_count'] > 0
    except ImportError:
        pytest.skip("RDKit not installed")

def test_fetch_data_entry_point_exists():
    """Verify fetch_data.py has a main function."""
    from fetch_data import main
    assert callable(main)

def test_confounds_entry_point_exists():
    """Verify confounds.py has a main function."""
    from confounds import main
    assert callable(main)
