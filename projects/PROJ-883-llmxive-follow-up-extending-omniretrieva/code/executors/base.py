"""Base classes and factory for executors.

This module defines:
- ``ExecutionResult``: a dataclass capturing the outcome of a query execution.
- ``BaseExecutor``: an abstract base class that provides timeout handling and a
  ``run`` method that concrete executors must implement.
- ``create_executor``: a simple factory that returns an executor instance based on a
  string identifier (``text``, ``relational`` or ``graph``).

The concrete executors live in ``text_executor.py``, ``relational_executor.py`` and
``graph_executor.py``.  They all inherit from ``BaseExecutor`` and implement the
``execute`` method.
"""

import abc
import signal
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from llmxive_toolkit import get_logger

log = get_logger(__name__)

class TimeoutException(Exception):
    """Raised when an executor exceeds the allowed time budget."""
    pass


@dataclass
class ExecutionResult:
    """Container for the result of a single query execution."""

    query_id: str
    source_type: str
    complexity_level: int
    executed_plan: Optional[str] = None
    latency_ms: float = 0.0
    success: bool = False
    timeout: bool = False
    # ``executed_plan`` may be a textual representation of the plan produced
    # by the native engine (e.g., SQL string, SPARQL query, or a passage ID).

    def as_dict(self) -> Dict[str, Any]:
        """Return a plain‑dict representation – useful for CSV/JSON serialization."""
        return {
            "query_id": self.query_id,
            "source_type": self.source_type,
            "complexity_level": self.complexity_level,
            "executed_plan": self.executed_plan,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "timeout": self.timeout,
        }


class BaseExecutor(abc.ABC):
    """Abstract executor providing a timeout wrapper.

    Concrete subclasses must implement :meth:`execute` which receives a
    ``query`` dictionary (the same shape that appears in
    ``generation_log.json``) and returns an :class:`ExecutionResult`.
    """

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds

    @abc.abstractmethod
    def execute(self, query: Dict[str, Any]) -> ExecutionResult:
        """Run the native engine for *query* and return an ``ExecutionResult``."""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Timeout handling utilities
    # ------------------------------------------------------------------ #
    def _handle_timeout(self, signum, frame):
        """Signal handler that converts an alarm into a Python exception."""
        raise TimeoutException("Execution exceeded %d seconds" % self.timeout_seconds)

    def run(self, query: Dict[str, Any]) -> ExecutionResult:
        """Public entry point used by the pipeline.

        It measures wall‑clock time, enforces the timeout, and guarantees that an
        ``ExecutionResult`` is always returned (even on error/timeout).
        """
        start = time.time()
        result: ExecutionResult
        try:
            # Install the alarm handler for the duration of the call.
            signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(self.timeout_seconds)

            result = self.execute(query)
            result.success = True
            result.timeout = False
        except TimeoutException as te:
            log.warning("Query %s timed out: %s", query.get("query_id"), te)
            result = ExecutionResult(
                query_id=query.get("query_id", "unknown"),
                source_type=query.get("source_type", "unknown"),
                complexity_level=int(query.get("complexity_level", -1)),
                executed_plan=None,
                latency_ms=0.0,
                success=False,
                timeout=True,
            )
        except Exception as e:  # pylint: disable=broad-except
            log.error("Execution error for query %s: %s", query.get("query_id"), e)
            result = ExecutionResult(
                query_id=query.get("query_id", "unknown"),
                source_type=query.get("source_type", "unknown"),
                complexity_level=int(query.get("complexity_level", -1)),
                executed_plan=None,
                latency_ms=0.0,
                success=False,
                timeout=False,
            )
        finally:
            # Cancel any pending alarm.
            signal.alarm(0)
            end = time.time()
            # Record wall‑clock latency even if we timed‑out (the time until the
            # alarm fired is the relevant figure).
            result.latency_ms = (end - start) * 1000.0

        return result


def create_executor(executor_type: str) -> BaseExecutor:
    """Factory that returns a concrete executor based on *executor_type*.

    Parameters
    ----------
    executor_type: str
        One of ``"text"``, ``"relational"``, ``"graph"``.

    Returns
    -------
    BaseExecutor
        An instantiated executor ready to ``run`` queries.
    """
    executor_type = executor_type.lower()
    if executor_type == "text":
        from .text_executor import TextExecutor

        return TextExecutor()
    if executor_type == "relational":
        from .relational_executor import RelationalExecutor

        return RelationalExecutor()
    if executor_type == "graph":
        from .graph_executor import GraphExecutor

        return GraphExecutor()
    raise ValueError(f"Unsupported executor type: {executor_type}")
