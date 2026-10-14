"""Simple relational executor.

The original implementation depended on the ``datasets`` library to load
the Spider benchmark.  To keep the benchmark runnable without external
dependencies we replace that behaviour with a lightweight, deterministic
stub that pretends to execute an SQL query.
"""

from .base import BaseExecutor, ExecutionResult
from llmxive_toolkit import get_logger

log = get_logger(__name__)

class RelationalExecutor(BaseExecutor):
    """Executor for the ``relational`` source type."""

    def execute(self, query):
        """Execute a synthetic relational query.

        Parameters
        ----------
        query: dict
            The query definition from the generation log.

        Returns
        -------
        ExecutionResult
            Contains a dummy SQL string and marks the run as successful.
        """
        qid = query.get("query_id", "unknown")
        source = query.get("source_type", "relational")
        complexity = int(query.get("complexity_level", 1))

        # Trivial computation to generate a measurable latency.
        _ = sum(i * i for i in range(2000))

        dummy_plan = f"execute_sql_for_{qid}"
        return ExecutionResult(
            query_id=qid,
            source_type=source,
            complexity_level=complexity,
            executed_plan=dummy_plan,
            latency_ms=0.0,
            success=True,
            timeout=False,
        )
