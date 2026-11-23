import os
import tempfile
import h5py
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord
from data.save_dataset import serialize_polymer_graph, save_to_hdf5

class TestSerializePolymerGraph:
    def test_serialize_basic_graph(self):
        """Test serialization of a basic PolymerGraph."""
        graph = MagicMock(spec=PlymerGraph)
        graph.node_features = {
            "atom_types": ["C", "C", "O"],
            "hybridizations": ["sp3", "sp3", "sp2"],
            "atomic_masses": [12.0, 12.0, 16.0],
        }
        graph.edge_features = {
            "bond_types": ["single", "single"],
            "bond_lengths": [1.54, 1.43],
            "is_conjugated": [False, False],
        }
        graph.metadata = {
            "smiles": "CCO",
            "mol_weight": 46.0,
            "source": "test",
            "inchi_key": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
        }

        result = serialize_polymer_graph(graph)

        assert result is not None
        assert "node_features" in result
        assert "edge_features" in result
        assert "graph_metadata" in result
        assert result["graph_metadata"]["smiles"] == "CCO"

    def test_serialize_none_graph(self):
        """Test serialization of a None graph."""
        result = serialize_polymer_graph(None)
        assert result is None

class TestSaveToHdf5:
    def test_save_empty_list(self):
        """Test saving an empty list of graphs."""
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_to_hdf5([], [], tmp_path)
            assert os.path.exists(tmp_path)
            with h5py.File(tmp_path, "r") as f:
                assert f.attrs["record_count"] == 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_save_single_graph(self):
        """Test saving a single graph and record."""
        graph = MagicMock(spec=PlymerGraph)
        graph.node_features = {
            "atom_types": ["C"],
            "hybridizations": ["sp3"],
            "atomic_masses": [12.0],
        }
        graph.edge_features = {
            "bond_types": [],
            "bond_lengths": [],
            "is_conjugated": [],
        }
        graph.metadata = {
            "smiles": "C",
            "mol_weight": 16.0,
            "source": "test",
            "inchi_key": "OKKJLVBELUTLKV-UHFFFAOYSA-N",
        }

        record = PermeabilityRecord(
            smiles="C",
            log_permeability=-5.0,
            source="test",
        )

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_to_hdf5([graph], [record], tmp_path)
            assert os.path.exists(tmp_path)
            with h5py.File(tmp_path, "r") as f:
                assert f.attrs["record_count"] == 1
                assert "smiles" in f["graph_metadata"]
                assert "permeability" in f
                assert f["graph_metadata"]["smiles"][0] == "C"
                assert f["permeability"][0] == -5.0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_save_multiple_graphs(self):
        """Test saving multiple graphs and records."""
        graphs = []
        records = []
        for i in range(3):
            graph = MagicMock(spec=PlymerGraph)
            graph.node_features = {
                "atom_types": ["C"] * (i + 1),
                "hybridizations": ["sp3"] * (i + 1),
                "atomic_masses": [12.0] * (i + 1),
            }
            graph.edge_features = {
                "bond_types": ["single"] * i,
                "bond_lengths": [1.54] * i,
                "is_conjugated": [False] * i,
            }
            graph.metadata = {
                "smiles": f"C{i}",
                "mol_weight": 16.0 * (i + 1),
                "source": "test",
                "inchi_key": f"KEY{i}",
            }
            graphs.append(graph)

            record = PermeabilityRecord(
                smiles=f"C{i}",
                log_permeability=-5.0 - i,
                source="test",
            )
            records.append(record)

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_to_hdf5(graphs, records, tmp_path)
            assert os.path.exists(tmp_path)
            with h5py.File(tmp_path, "r") as f:
                assert f.attrs["record_count"] == 3
                assert f["graph_metadata"]["smiles"].len() == 3
                assert f["permeability"].len() == 3
                # Check specific values
                assert f["graph_metadata"]["smiles"][0] == "C0"
                assert f["permeability"][0] == -5.0
                assert f["graph_metadata"]["smiles"][2] == "C2"
                assert f["permeability"][2] == -7.0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)