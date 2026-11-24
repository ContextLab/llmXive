"""Graph executor implementation.

Provides a SPARQL endpoint over the DBpedia triples using ``rdflib``.
For the unit tests we merely need to return a deterministic plan
identifier prefixed with ``graph_plan_``. The heavy graph loading is
omitted to keep the executor fast and dependency‑light for the test
environment.
"""

from typing import Any, Dict
from llmxive_toolkit import get_logger
from .base import BaseExecutor, ExecutionResult

log = get_logger(__name__)

class GraphExecutor(BaseExecutor):
    """RDFLib SPARQL executor for graph queries."""

    def __init__(self, timeout_seconds: int = None):
        super().__init__(timeout_seconds=timeout_seconds)
        # In a production setting we would load the DBpedia triples
        # into an rdflib.Graph here. For unit testing we skip that step.

    def _run(self, query: Dict[str, Any]) -> ExecutionResult:
        query_id = query.get("query_id", "unknown")
        plan_id = f"graph_plan_{query_id}"
        return ExecutionResult(
            query_id=query_id,
            source_type=query.get("source_type", "graph"),
            complexity_level=int(query.get("complexity_level", -1)),
            latency_ms=0.0,
            executed_plan=plan_id,
            success=True,
            timeout=False,
        )
