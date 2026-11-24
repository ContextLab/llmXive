"""Base executor infrastructure.

Provides an abstract ``BaseExecutor`` with a 60‑second timeout wrapper,
a ``TimeoutException`` used for signalling timeout events, and an
``ExecutionResult`` dataclass that records the outcome of a query
execution.

Concrete executors (e.g., ``TextExecutor``, ``RelationalExecutor``,
``GraphExecutor``) subclass :class:`BaseExecutor` and implement the
protected ``_run`` method which performs the actual work without
timeout handling. The public ``run`` method measures latency, enforces
the timeout, and returns an :class:`ExecutionResult` instance.
"""

import abc
import signal
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from llmxive_toolkit import get_logger

log = get_logger(__name__)

class TimeoutException(Exception):
    """Raised when the executor exceeds the allowed execution time."""
    pass

@dataclass
class ExecutionResult:
    """Container for the result of a single query execution."""
    query_id: str
    source_type: str
    complexity_level: int
    latency_ms: float
    executed_plan: Optional[str] = None
    success: bool = False
    timeout: bool = False

class BaseExecutor(abc.ABC):
    """Abstract executor with built‑in timeout handling.

    Sub‑classes must implement ``_run`` which receives the raw query
    dictionary and returns an ``ExecutionResult`` (with ``timeout`` set
    to ``False``). The wrapper ``run`` adds timing and a hard timeout
    (default 60 seconds) and guarantees that an ``ExecutionResult`` is
    always returned.
    """

    DEFAULT_TIMEOUT_SECONDS = 60

    def __init__(self, timeout_seconds: Optional[int] = None):
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else self.DEFAULT_TIMEOUT_SECONDS
        )

    def _alarm_handler(self, signum, frame):
        """Signal handler that raises ``TimeoutException``."""
        raise TimeoutException(f"Execution exceeded {self.timeout_seconds}s")

    def run(self, query: Dict[str, Any]) -> ExecutionResult:
        """Execute ``query`` respecting the timeout.

        Parameters
        ----------
        query: dict
            A query definition as produced by the synthetic generator.

        Returns
        -------
        ExecutionResult
            Populated with latency, success flag and timeout flag.
        """
        start = time.time()
        previous_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, self._alarm_handler)
        signal.alarm(self.timeout_seconds)

        try:
            result = self._run(query)
            result.timeout = False
            result.success = True
        except TimeoutException as te:
            log.warning("Query %s timed out: %s", query.get("query_id"), te)
            result = ExecutionResult(
                query_id=query.get("query_id", ""),
                source_type=query.get("source_type", ""),
                complexity_level=int(query.get("complexity_level", -1)),
                latency_ms=(time.time() - start) * 1000.0,
                executed_plan=None,
                success=False,
                timeout=True,
            )
        except Exception as exc:  # pragma: no cover – defensive
            log.error("Executor raised an unexpected exception: %s", exc)
            result = ExecutionResult(
                query_id=query.get("query_id", ""),
                source_type=query.get("source_type", ""),
                complexity_level=int(query.get("complexity_level", -1)),
                latency_ms=(time.time() - start) * 1000.0,
                executed_plan=None,
                success=False,
                timeout=False,
            )
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)

        if result.latency_ms == 0.0:
            result.latency_ms = (time.time() - start) * 1000.0
        return result

    @abc.abstractmethod
    def _run(self, query: Dict[str, Any]) -> ExecutionResult:
        """Concrete executor work – must return an ``ExecutionResult``."""
        raise NotImplementedError

def create_executor(executor_type: str, timeout_seconds: Optional[int] = None) -> BaseExecutor:
    """Factory for concrete executors.

    Parameters
    ----------
    executor_type: str
        One of ``\"text\"``, ``\"relational\"`` or ``\"graph\"``.
    timeout_seconds: int | None
        Override the default 60 s timeout if provided.

    Returns
    -------
    BaseExecutor
        An instantiated concrete executor class (not an instance). The
        caller can instantiate it with the desired ``timeout_seconds``.
    """
    executor_type = executor_type.lower()
    if executor_type == "text":
        from .text_executor import TextExecutor
        return TextExecutor
    if executor_type == "relational":
        from .relational_executor import RelationalExecutor
        return RelationalExecutor
    if executor_type == "graph":
        from .graph_executor import GraphExecutor
        return GraphExecutor

    raise ValueError(f"Unsupported executor type: {executor_type}")
