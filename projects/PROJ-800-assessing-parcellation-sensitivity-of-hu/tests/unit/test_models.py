"""
Unit tests for the data models defined in code/models/.
"""
import pytest
import numpy as np
from scipy.sparse import csr_matrix

from code.models.adjacency_matrix import AdjacencyMatrix
from code.models.hub_set import HubSet
from code.models.centrality_score import CentralityScore
from code.utils.logger import ProcessingError


class TestAdjacencyMatrix:
    def test_init_valid_dense(self):
        """Test initialization with a dense numpy array."""
        matrix = np.random.rand(10, 10)
        node_ids = [f"Node_{i}" for i in range(10)]
        adj = AdjacencyMatrix(
            matrix=matrix,
            node_ids=node_ids,
            resolution="test_res",
            subject_id="sub_001"
        )
        assert adj.n_nodes == 10
        assert adj.shape == (10, 10)

    def test_init_valid_sparse(self):
        """Test initialization with a sparse matrix."""
        data = np.array([1.0, 2.0, 3.0])
        indices = np.array([0, 1, 2])
        indptr = np.array([0, 1, 2, 3])
        matrix = csr_matrix((data, indices, indptr), shape=(3, 3))
        node_ids = ["A", "B", "C"]
        adj = AdjacencyMatrix(
            matrix=matrix,
            node_ids=node_ids,
            resolution="test_res",
            subject_id="sub_001"
        )
        assert adj.n_nodes == 3
        assert adj.symmetric  # Default

    def test_init_mismatched_nodes(self):
        """Test that mismatched node count raises error."""
        matrix = np.random.rand(10, 10)
        node_ids = [f"Node_{i}" for i in range(5)]  # Wrong count
        with pytest.raises(ProcessingError):
            AdjacencyMatrix(
                matrix=matrix,
                node_ids=node_ids,
                resolution="test_res",
                subject_id="sub_001"
            )

    def test_serialization_roundtrip(self):
        """Test to_dict and from_dict consistency."""
        matrix = np.random.rand(5, 5)
        node_ids = [f"Node_{i}" for i in range(5)]
        original = AdjacencyMatrix(
            matrix=matrix,
            node_ids=node_ids,
            resolution="test_res",
            subject_id="sub_001",
            metadata={"source": "test"}
        )
        data = original.to_dict()
        restored = AdjacencyMatrix.from_dict(data)
        assert np.allclose(original.matrix, restored.matrix)
        assert original.node_ids == restored.node_ids
        assert original.resolution == restored.resolution


class TestHubSet:
    def test_init_valid(self):
        """Test valid HubSet creation."""
        hub_indices = {0, 1, 2}
        hub_ids = ["Node_0", "Node_1", "Node_2"]
        hs = HubSet(
            subject_id="sub_001",
            resolution="test_res",
            hub_indices=hub_indices,
            hub_ids=hub_ids,
            threshold=0.1,
            threshold_type="proportional",
            total_nodes=10
        )
        assert hs.n_hubs == 3
        assert hs.hub_ratio == 0.3

    def test_init_out_of_bounds(self):
        """Test that out-of-bounds indices raise error."""
        hub_indices = {0, 1, 15}  # 15 is out of bounds for total_nodes=10
        hub_ids = ["A", "B", "C"]
        with pytest.raises(ProcessingError):
            HubSet(
                subject_id="sub_001",
                resolution="test_res",
                hub_indices=hub_indices,
                hub_ids=hub_ids,
                threshold=0.1,
                threshold_type="proportional",
                total_nodes=10
            )

    def test_serialization(self):
        """Test serialization consistency."""
        hs = HubSet(
            subject_id="sub_001",
            resolution="test_res",
            hub_indices={0, 1},
            hub_ids=["A", "B"],
            threshold=0.1,
            threshold_type="proportional",
            total_nodes=10
        )
        data = hs.to_dict()
        restored = HubSet.from_dict(data)
        assert restored.hub_indices == hs.hub_indices
        assert restored.hub_ids == hs.hub_ids


class TestCentralityScore:
    def test_init_valid(self):
        """Test valid CentralityScore creation."""
        node_ids = [f"N{i}" for i in range(5)]
        degree = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        cs = CentralityScore(
            subject_id="sub_001",
            resolution="test_res",
            node_ids=node_ids,
            degree_centrality=degree,
            threshold=0.1
        )
        assert len(cs.get_hub_indices()) == 0  # No flags set yet

    def test_init_with_hubs(self):
        """Test creation with hub flags."""
        node_ids = [f"N{i}" for i in range(5)]
        degree = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        hubs = np.array([False, False, False, True, True])
        cs = CentralityScore(
            subject_id="sub_001",
            resolution="test_res",
            node_ids=node_ids,
            degree_centrality=degree,
            hub_flags=hubs,
            threshold=0.1
        )
        assert cs.get_hub_indices() == [3, 4]

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise error."""
        node_ids = [f"N{i}" for i in range(5)]
        degree = np.array([1.0, 2.0])  # Too short
        with pytest.raises(ProcessingError):
            CentralityScore(
                subject_id="sub_001",
                resolution="test_res",
                node_ids=node_ids,
                degree_centrality=degree
            )

    def test_serialization(self):
        """Test serialization consistency."""
        node_ids = [f"N{i}" for i in range(3)]
        degree = np.array([1.0, 2.0, 3.0])
        hubs = np.array([False, True, True])
        original = CentralityScore(
            subject_id="sub_001",
            resolution="test_res",
            node_ids=node_ids,
            degree_centrality=degree,
            hub_flags=hubs
        )
        data = original.to_dict()
        restored = CentralityScore.from_dict(data)
        assert np.array_equal(restored.degree_centrality, original.degree_centrality)
        assert np.array_equal(restored.hub_flags, original.hub_flags)