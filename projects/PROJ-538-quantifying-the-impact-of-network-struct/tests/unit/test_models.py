"""
Unit tests for code/models.py.
Verifies Pydantic model validation.
"""
import pytest
import numpy as np
from code.models import AtomicSnapshot, DefectGraph
from code.utils import DataAvailabilityError


class TestAtomicSnapshot:
    """Tests for AtomicSnapshot model."""

    def test_create_snapshot(self):
        """Test creating a valid AtomicSnapshot."""
        snapshot = AtomicSnapshot(
            species=["Cu", "Ni", "Cu"],
            positions=[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
            cell=[[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
            thermal_conductivity_W_m_K=10.5
        )
        assert len(snapshot.species) == 3
        assert snapshot.thermal_conductivity_W_m_K == 10.5

    def test_missing_thermal_conductivity(self):
        """Test that missing thermal conductivity raises an error."""
        # Note: The model definition in code/models.py should handle this validation.
        # If the field is required, Pydantic will raise ValidationError.
        # If it's optional but we want to enforce it later, we test the logic.
        # Assuming it's required based on task T013 description.
        with pytest.raises(Exception): # Pydantic ValidationError or similar
            AtomicSnapshot(
                species=["Cu"],
                positions=[[0.0, 0.0, 0.0]],
                cell=[[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]]
                # thermal_conductivity_W_m_K is missing
            )


class TestDefectGraph:
    """Tests for DefectGraph model."""

    def test_create_graph(self):
        """Test creating a valid DefectGraph."""
        import networkx as nx
        G = nx.Graph()
        G.add_node(0, species="Cu")
        G.add_node(1, species="Ni")
        G.add_edge(0, 1)
        
        graph = DefectGraph(
            graph_data=G,
            source_snapshot_id="test-123"
        )
        assert graph.source_snapshot_id == "test-123"
        assert graph.graph_data.number_of_nodes() == 2
