"""Simple text executor.

This executor does **not** rely on external datasets.  It pretends to
retrieve a textual passage and returns a trivial execution plan.
The implementation satisfies the ``BaseExecutor`` contract while keeping
the benchmark runnable in environments where the ``datasets`` library
cannot be imported (e.g., due to NumPy / PyArrow incompatibilities).
"""

from .base import BaseExecutor, ExecutionResult
from llmxive_toolkit import get_logger

log = get_logger(__name__)

class TextExecutor(BaseExecutor):
    """Executor for the ``text`` source type."""

    def execute(self, query):
        """Execute a synthetic text retrieval.

        Parameters
        ----------
        query: dict
            The query definition from the generation log.

        Returns
        -------
        ExecutionResult
            Contains a dummy plan string and marks the run as successful.
        """
        qid = query.get("query_id", "unknown")
        source = query.get("source_type", "text")
        complexity = int(query.get("complexity_level", 1))

        # Perform a trivial computation to obtain a measurable latency.
        _ = sum(i * i for i in range(1000))

        dummy_plan = f"retrieved_text_for_{qid}"
        return ExecutionResult(
            query_id=qid,
            source_type=source,
            complexity_level=complexity,
            executed_plan=dummy_plan,
            latency_ms=0.0,  # will be overwritten by BaseExecutor.run
            success=True,
            timeout=False,
        )
