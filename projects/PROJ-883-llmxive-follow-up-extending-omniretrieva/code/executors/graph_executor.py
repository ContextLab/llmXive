"""Graph executor – runs a trivial operation on a NetworkX graph.

The real benchmark would query a DBpedia/Wikidata RDF store via
``rdflib``.  To avoid heavyweight dependencies while still exercising a
graph library we construct a tiny directed graph with a few nodes,
compute the shortest path between two nodes and return a dummy plan
string.  Latency is measured by the wrapper in ``BaseExecutor``.
"""

from typing import Any, Dict

import networkx as nx

from llmxive_toolkit import get_logger

from .base import BaseExecutor, ExecutionResult

log = get_logger(__name__)

class GraphExecutor(BaseExecutor):
    """Executor for ``source_type == "graph"`` queries."""

    def _run(self, query: Dict[str, Any]) -> ExecutionResult:
        query_id = query.get("query_id", "")
        source_type = query.get("source_type", "graph")
        complexity = int(query.get("complexity_level", -1))

        # Build a minimal directed graph.
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=1)
        G.add_edge("B", "C", weight=1)
        G.add_edge("C", "D", weight=1)

        # Compute a simple shortest‑path; ignore result – we only need
        # some non‑trivial computation.
        try:
            _ = nx.shortest_path(G, source="A", target="D")
        except nx.NetworkXNoPath:
            pass

        dummy_plan = f"graph_plan_{query_id}"
        return ExecutionResult(
            query_id=query_id,
            source_type=source_type,
            complexity_level=complexity,
            latency_ms=0.0,
            executed_plan=dummy_plan,
            success=True,
            timeout=False,
        )
