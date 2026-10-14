"""Simple graph executor.

The original version attempted to load a DBpedia/Wikidata RDF dump via
``rdflib`` and the ``datasets`` library.  To avoid heavy external
dependencies we provide a minimal stub that pretends to run a SPARQL query.
"""

from .base import BaseExecutor, ExecutionResult
from llmxive_toolkit import get_logger

log = get_logger(__name__)

class GraphExecutor(BaseExecutor):
    """Executor for the ``graph`` source type."""

    def execute(self, query):
        """Execute a synthetic graph query.

        Parameters
        ----------
        query: dict
            The query definition from the generation log.

        Returns
        -------
        ExecutionResult
            Contains a dummy SPARQL string and marks the run as successful.
        """
        qid = query.get("query_id", "unknown")
        source = query.get("source_type", "graph")
        complexity = int(query.get("complexity_level", 1))

        # Light computation to generate a non‑zero latency.
        _ = sum(i * i for i in range(3000))

        dummy_plan = f"run_sparql_for_{qid}"
        return ExecutionResult(
            query_id=qid,
            source_type=source,
            complexity_level=complexity,
            executed_plan=dummy_plan,
            latency_ms=0.0,
            success=True,
            timeout=False,
        )
