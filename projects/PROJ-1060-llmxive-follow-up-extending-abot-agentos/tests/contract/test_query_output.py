"""
Contract Test: Query Output Schema Compliance.

Verifies that the query engine returns results matching the expected 
data structure defined in the specification.
"""
import pytest
import networkx as nx

# Import from code/
from query_engine import query_graph, Node
from graph_builder import SymbolicGraphBuilder

class TestQueryOutputSchema:
    """Tests ensuring query output matches the required schema."""

    def _build_sample_graph(self) -> nx.DiGraph:
        """Helper to build a deterministic sample graph."""
        builder = SymbolicGraphBuilder()
        # Create a mock trace for graph generation
        trace = {
            "task_id": "schema_test",
            "observations": [
                {"observation": "key on table", "action": "go to table"},
                {"observation": "table near sofa", "action": "go to sofa"}
            ],
            "goal": "find key"
        }
        return builder.build_from_trace(trace)

    def test_query_result_is_list_of_nodes(self):
        """
        Contract: query_graph must return a list of Node objects.
        """
        graph = self._build_sample_graph()
        result = query_graph(graph, "find key")

        assert isinstance(result, list), "Query result must be a list"
        if result:
            assert all(isinstance(item, Node) for item in result), \
                "All items in result must be Node instances"

    def test_node_dataclass_fields(self):
        """
        Contract: Each Node in the result must have 'id', 'token', and 'predicates' fields.
        """
        graph = self._build_sample_graph()
        result = query_graph(graph, "find key")

        for node in result:
            assert hasattr(node, "id"), "Node must have 'id' attribute"
            assert hasattr(node, "token"), "Node must have 'token' attribute"
            assert hasattr(node, "predicates"), "Node must have 'predicates' attribute"
            
            # Type checks
            assert isinstance(node.id, str), "Node ID must be string"
            assert isinstance(node.token, str), "Node token must be string"
            assert isinstance(node.predicates, list), "Node predicates must be a list"

    def test_null_result_on_missing_path(self):
        """
        Contract: Query for non-existent entity must return empty list (not crash).
        """
        graph = self._build_sample_graph()
        # Query for something definitely not in the graph
        result = query_graph(graph, "find non_existent_object_xyz")

        assert isinstance(result, list), "Result must be a list even when empty"
        assert len(result) == 0, "Result must be empty for non-existent query"

    def test_query_output_serializable(self):
        """
        Contract: Query results must be JSON serializable (for logging/reporting).
        """
        import json
        graph = self._build_sample_graph()
        result = query_graph(graph, "find key")

        # Convert to dict representation for JSON check
        serializable_result = [
            {
                "id": n.id,
                "token": n.token,
                "predicates": n.predicates
            }
            for n in result
        ]

        try:
            json.dumps(serializable_result)
        except TypeError as e:
            pytest.fail(f"Query result is not JSON serializable: {e}")
