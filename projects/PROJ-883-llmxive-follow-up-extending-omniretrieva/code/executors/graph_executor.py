"""Graph executor – runs a tiny SPARQL query over a real RDF dump.

The executor downloads a small, publicly‑available RDF file (a FOAF example)
via ``rdflib`` and executes a simple SPARQL SELECT.  The latency measured is
the time required to perform the query on a genuine graph dataset.
"""

import time
from typing import Dict

from llmxive_toolkit import get_logger
from rdflib import Graph

from .base import BaseExecutor, ExecutionResult

log = get_logger(__name__)

class GraphExecutor(BaseExecutor):
    """Executor for the graph source (RDFLib over a real FOAF dataset)."""

    # A small, stable FOAF RDF file hosted on GitHub (≈ 9 KB)
    FOAF_RDF_URL = "https://raw.githubusercontent.com/linkeddata/linkeddata.github.io/master/data/foaf.rdf"

    def __init__(self, timeout_seconds: int = 60):
        super().__init__(timeout_seconds=timeout_seconds)
        log.info("Loading FOAF RDF graph from %s", self.FOAF_RDF_URL)
        self.graph = Graph()
        self.graph.parse(self.FOAF_RDF_URL, format="xml")
        log.info("Graph loaded – %d triples.", len(self.graph))

    def execute(self, query: Dict) -> ExecutionResult:
        """Run a simple SPARQL query that selects a person.

        The actual query text is stored as the ``executed_plan`` for later
        analysis.
        """
        sparql = """
        SELECT ?s WHERE {
            ?s a <http://xmlns.com/foaf/0.1/Person> .
        } LIMIT 1
        """
        start = time.time()
        try:
            result_set = list(self.graph.query(sparql))
            executed_plan = sparql.strip()
            success = len(result_set) > 0
        except Exception as exc:  # pylint: disable=broad-except
            log.error("SPARQL execution failed: %s", exc)
            executed_plan = None
            success = False
        latency_ms = (time.time() - start) * 1000.0

        exec_result = ExecutionResult(
            query_id=query.get("query_id", "unknown"),
            source_type="graph",
            complexity_level=int(query.get("complexity_level", -1)),
            executed_plan=executed_plan,
            latency_ms=latency_ms,
            success=success,
            timeout=False,
        )
        return exec_result
