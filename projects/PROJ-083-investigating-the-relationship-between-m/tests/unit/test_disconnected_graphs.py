import pytest
import pandas as pd
from pathlib import Path
import csv
import hashlib
import tempfile
import os

from rdkit import Chem
from code.descriptors import is_connected, calculate_descriptors_for_smiles, log_disconnected_graphs

class TestDisconnectedGraphs:
    
    def test_is_connected_true(self):
        """Test that a valid connected molecule returns True."""
        smiles = "c1ccccc1" # Benzene
        mol = Chem.MolFromSmiles(smiles)
        assert is_connected(mol) is True

    def test_is_connected_false(self):
        """Test that a disconnected molecule returns False."""
        # Two separate benzene rings
        smiles = "c1ccccc1.c2ccccc2"
        mol = Chem.MolFromSmiles(smiles)
        assert is_connected(mol) is False

    def test_calculate_descriptors_disconnected_raises_none(self):
        """Test that calculate_descriptors_for_smiles returns None for disconnected graphs."""
        smiles = "c1ccccc1.c2ccccc2"
        result = calculate_descriptors_for_smiles(smiles, reaction_id="test-001")
        assert result is None

    def test_log_disconnected_graphs_creates_file(self):
        """Test that log_disconnected_graphs creates the CSV with correct schema."""
        records = [
            {"smiles": "c1ccccc1.c2ccccc2", "reaction_id": "rxn-1", "error_type": "disconnected"},
            {"smiles": "CC.CC", "reaction_id": "rxn-2", "error_type": "disconnected"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "disconnected_graphs.csv"
            checksum = log_disconnected_graphs(records, str(output_path))
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]["smiles"] == "c1ccccc1.c2ccccc2"
            assert rows[0]["reaction_id"] == "rxn-1"
            assert rows[0]["error_type"] == "disconnected"
            
            # Verify checksum
            expected_checksum = hashlib.md5(output_path.read_bytes()).hexdigest()
            assert checksum == expected_checksum

    def test_log_disconnected_graphs_empty_list(self):
        """Test logging an empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_disconnected.csv"
            checksum = log_disconnected_graphs([], str(output_path))
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
            # Should have header only
            assert "smiles,reaction_id,error_type" in content
            assert len(content.splitlines()) == 1