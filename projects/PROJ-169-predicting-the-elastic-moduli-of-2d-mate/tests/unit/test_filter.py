"""
Unit tests for the 2D filter and tensor validator logic.
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_models.material_graph import MaterialGraph
from ingest.filter import is_valid_6_component_tensor, is_2d_material, filter_graphs

class TestTensorValidation:
    """Tests for is_valid_6_component_tensor"""

    def test_valid_6x6_matrix(self):
        """Test valid 6x6 symmetric matrix"""
        tensor = np.eye(6)
        assert is_valid_6_component_tensor(tensor) is True

    def test_valid_6x6_non_symmetric(self):
        """Test invalid 6x6 non-symmetric matrix (fails symmetry check)"""
        tensor = np.ones((6, 6))
        tensor[0, 1] = 0.0
        tensor[1, 0] = 1.0
        # The function checks for symmetry if it's a 2D array
        assert is_valid_6_component_tensor(tensor) is False

    def test_valid_10_component(self):
        """Test valid 10-component vector (Voigt unique for 3D)"""
        tensor = np.ones(10)
        assert is_valid_6_component_tensor(tensor) is True

    def test_valid_6_component_2d(self):
        """Test valid 6-component vector for 2D materials"""
        tensor = np.ones(6)
        assert is_valid_6_component_tensor(tensor) is True

    def test_invalid_size(self):
        """Test invalid size tensor"""
        assert is_valid_6_component_tensor(np.ones(5)) is False
        assert is_valid_6_component_tensor(np.ones(7)) is False
        assert is_valid_6_component_tensor(np.ones(11)) is False

    def test_none_input(self):
        """Test None input"""
        assert is_valid_6_component_tensor(None) is False

    def test_list_input(self):
        """Test list input (should convert to numpy)"""
        tensor = [[1.0]*6 for _ in range(6)]
        assert is_valid_6_component_tensor(tensor) is True

    def test_invalid_6x6_non_symmetric_list(self):
        """Test invalid 6x6 non-symmetric list input"""
        tensor = [[1.0]*6 for _ in range(6)]
        tensor[0][1] = 0.0
        tensor[1][0] = 1.0
        assert is_valid_6_component_tensor(tensor) is False

class Test2DIdentification:
    """Tests for is_2d_material"""

    def test_explicit_flag_true(self):
        """Test explicit is_2d flag"""
        info = {"is_2d": True}
        assert is_2d_material(info) is True

    def test_explicit_flag_false(self):
        """Test explicit is_2d flag false"""
        info = {"is_2d": False}
        assert is_2d_material(info) is False

    def test_dimensionality_tag(self):
        """Test dimensionality tag"""
        info = {"dimensionality": 2}
        assert is_2d_material(info) is True

    def test_dimensionality_not_2(self):
        """Test dimensionality tag not equal to 2"""
        info = {"dimensionality": 3}
        assert is_2d_material(info) is False

    def test_tag_contains_2d(self):
        """Test tags string containing 2d"""
        info = {"tags": "2d material, layered"}
        assert is_2d_material(info) is True

    def test_tag_no_2d(self):
        """Test tags string not containing 2d"""
        info = {"tags": "bulk, 3d crystal"}
        assert is_2d_material(info) is False

    def test_vacuum_heuristic(self):
        """Test vacuum heuristic (large c-axis relative to a,b)"""
        info = {
            "lattice": {"a": 3.0, "b": 3.0, "c": 20.0}
        }
        assert is_2d_material(info) is True

    def test_no_vacuum_heuristic(self):
        """Test no vacuum heuristic (c-axis similar to a,b)"""
        info = {
            "lattice": {"a": 3.0, "b": 3.0, "c": 3.0}
        }
        assert is_2d_material(info) is False

    def test_empty_info(self):
        """Test empty structure info"""
        info = {}
        assert is_2d_material(info) is False

    def test_missing_lattice_keys(self):
        """Test missing lattice keys"""
        info = {"lattice": {"a": 3.0}}
        assert is_2d_material(info) is False

class TestFilterGraphs:
    """Tests for filter_graphs function"""

    def test_filter_2d_valid(self):
        """Test filtering a valid 2D material"""
        graph = MaterialGraph(
            material_id="test_2d",
            nodes=[],
            edges=[],
            properties={
                "elastic_tensor": np.eye(6).tolist(),
                "structure_info": {"is_2d": True}
            }
        )
        filtered, stats = filter_graphs([graph])
        assert len(filtered) == 1
        assert stats.passed == 1

    def test_filter_non_2d(self):
        """Test filtering a non-2D material"""
        graph = MaterialGraph(
            material_id="test_3d",
            nodes=[],
            edges=[],
            properties={
                "elastic_tensor": np.eye(6).tolist(),
                "structure_info": {"is_2d": False}
            }
        )
        filtered, stats = filter_graphs([graph])
        assert len(filtered) == 0
        assert stats.failed_non_2d == 1

    def test_filter_missing_tensor(self):
        """Test filtering a material with missing tensor"""
        graph = MaterialGraph(
            material_id="test_bad",
            nodes=[],
            edges=[],
            properties={
                "elastic_tensor": None,
                "structure_info": {"is_2d": True}
            }
        )
        filtered, stats = filter_graphs([graph])
        assert len(filtered) == 0
        assert stats.failed_missing_tensor == 1

    def test_filter_invalid_tensor_shape(self):
        """Test filtering a material with invalid tensor shape (5 components)"""
        graph = MaterialGraph(
            material_id="test_bad_shape",
            nodes=[],
            edges=[],
            properties={
                "elastic_tensor": np.ones(5).tolist(),
                "structure_info": {"is_2d": True}
            }
        )
        filtered, stats = filter_graphs([graph])
        assert len(filtered) == 0
        assert stats.failed_invalid_tensor == 1

    def test_filter_mixed(self):
        """Test filtering a mixed list"""
        graphs = [
            MaterialGraph(
                material_id="good_2d",
                nodes=[],
                edges=[],
                properties={"elastic_tensor": np.eye(6).tolist(), "structure_info": {"is_2d": True}}
            ),
            MaterialGraph(
                material_id="bad_3d",
                nodes=[],
                edges=[],
                properties={"elastic_tensor": np.eye(6).tolist(), "structure_info": {"is_2d": False}}
            ),
            MaterialGraph(
                material_id="bad_tensor",
                nodes=[],
                edges=[],
                properties={"elastic_tensor": None, "structure_info": {"is_2d": True}}
            ),
            MaterialGraph(
                material_id="bad_shape",
                nodes=[],
                edges=[],
                properties={"elastic_tensor": np.ones(5).tolist(), "structure_info": {"is_2d": True}}
            )
        ]
        filtered, stats = filter_graphs(graphs)
        assert len(filtered) == 1
        assert filtered[0].material_id == "good_2d"
        assert stats.total_processed == 4
        assert stats.passed == 1
        assert stats.failed_non_2d == 1
        assert stats.failed_missing_tensor == 1
        assert stats.failed_invalid_tensor == 1