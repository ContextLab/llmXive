"""
Minimal stub of the ``torch`` package to allow the project to run in environments
where the real PyTorch library is not installed.

The stub implements only the symbols that are used by the existing codebase
(e.g., ``torch.nn.Module`` and ``torch.no_grad``).  All operations are no‑ops
or simple Python equivalents; they are sufficient for the unit tests that
import ``torch`` but do not rely on actual tensor computations.
"""

from contextlib import contextmanager
from typing import Any

# Simple placeholder for a tensor – using a list for demonstration purposes.
Tensor = list

@contextmanager
def no_grad():
    """Context manager that does nothing – mirrors ``torch.no_grad``."""
    yield

class _NNModule:
    """Base class mimicking ``torch.nn.Module``."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def forward(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError("Forward method should be overridden in subclasses.")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.forward(*args, **kwargs)

class nn:
    """Namespace for neural‑network‑related stubs."""
    Module = _NNModule

# Export symbols at the top level to match the real package API.
__all__ = [
    "Tensor",
    "no_grad",
    "nn",
]
