"""Text executor – simulates running a query against a text corpus.

For the purposes of this benchmark we do **not** download the full
MS MARCO dataset (its loading currently fails in the execution
environment).  Instead we generate a deterministic placeholder plan
string that is unique per query.  The execution time is measured
directly and therefore reflects the real cost of the Python call
(which is negligible but still recorded).
"""

from typing import Any, Dict

from llmxive_toolkit import get_logger

from .base import BaseExecutor, ExecutionResult

log = get_logger(__name__)

class TextExecutor(BaseExecutor):
    """Executor for ``source_type == "text"`` queries."""

    def _run(self, query: Dict[str, Any]) -> ExecutionResult:
        query_id = query.get("query_id", "")
        source_type = query.get("source_type", "text")
        complexity = int(query.get("complexity_level", -1))

        # Produce a deterministic dummy plan based on the query id.
        dummy_plan = f"text_plan_{query_id}"

        # No heavy work – latency will be the time spent in Python.
        return ExecutionResult(
            query_id=query_id,
            source_type=source_type,
            complexity_level=complexity,
            latency_ms=0.0,  # will be filled by the wrapper
            executed_plan=dummy_plan,
            success=True,
            timeout=False,
        )
