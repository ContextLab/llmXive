"""
Unit tests for data models defined in code/data_models.py.
"""
import pytest
import numpy as np
from data_models import PolymerRecord, MolecularGraph

class TestPolymerRecord:
    def test_create_valid_record(self):
        """Test creation of a valid PolymerRecord."""
        record = PolymerRecord(
            polymer_id="P001",
            smiles="CC(=O)O",
            degradation_pathway="hydrolysis",
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0
        )
        assert record.polymer_id == "P001"
        assert record.degradation_pathway == "hydrolysis"
        assert record.temperature == 25.0

    def test_missing_environmental_data(self):
        """Test that records can be created with None for environmental data (to be filtered later)."""
        record = PolymerRecord(
            polymer_id="P002",
            smiles="CCO",
            degradation_pathway="oxidation",
            temperature=None,
            ph=7.0,
            uv_exposure=0.0
        )
        assert record.temperature is None

class TestMolecularGraph:
    def test_create_graph(self):
        """Test creation of a MolecularGraph."""
        nodes = np.array([[1.0, 0.5], [0.5, 1.0]])
        edges = np.array([[0, 1], [1, 0]])
        graph = MolecularGraph(
            nodes=nodes,
            edges=edges,
            source_smiles="CC"
        )
        assert graph.source_smiles == "CC"
        assert graph.nodes.shape == (2, 2)
        assert graph.edges.shape == (2, 2)
