"""
Runtime path utilities for the mesh network supercomputer project.

This module provides two main components:

1. ``ProjectPaths`` – a thin wrapper around the ``llmxive_toolkit.paths``
   helpers.  It mirrors the original ``paths`` API (``data``, ``figures``,
   ``results`` etc.) but lives inside the project so that tests can import
   it without pulling the toolkit directly.

2. ``TaskChunkStore`` – a lightweight namespace that holds a mutable
   ``base_dir`` attribute.  The attribute points at the directory where
   ``TaskChunk`` JSON‑Lines are persisted.  Tests (and users) can monkey‑
   patch ``TaskChunkStore.base_dir`` to redirect storage to a temporary
   location, enabling isolated unit‑tests.

The ``base_dir`` attribute is **mutable** – it is a plain class variable,
not a property with a setter.  Changing it does not require any special
API; the test suite can simply assign a new ``Path`` object.

Example usage:

```python
from runtime.paths import TaskChunkStore

# Redirect to a temp directory in a test
TaskChunkStore.base_dir = Path("/tmp/my_test_chunks")

# Append a chunk (the store itself provides the ``append`` method)
TaskChunkStore.append({
    "run_id": "run_001",
    "chunk_id": "c1",
    "task_type": "monte_carlo",
    "payload": {"iterations": 1000},
    "status": "completed"
})
```
"""

from pathlib import Path
from llmxive_toolkit import paths as toolkit_paths

class ProjectPaths:
    """Facade for the llmxive_toolkit ``paths`` helpers.

    The class mirrors the original ``paths`` module but keeps the import
    surface inside the project, making it easier to mock or extend in
    tests.
    """

    @staticmethod
    def data(*parts: str) -> Path:
        """Return a ``Path`` inside the ``data`` folder."""
        return toolkit_paths.data(*parts)

    @staticmethod
    def figures(*parts: str) -> Path:
        """Return a ``Path`` inside the ``figures`` folder."""
        return toolkit_paths.figures(*parts)

    @staticmethod
    def results(*parts: str) -> Path:
        """Return a ``Path`` inside the ``results`` folder."""
        return toolkit_paths.results(*parts)

    @staticmethod
    def docs(*parts: str) -> Path:
        """Return a ``Path`` inside the ``docs`` folder."""
        return toolkit_paths.docs(*parts)

    @staticmethod
    def code(*parts: str) -> Path:
        """Return a ``Path`` inside the ``code`` folder."""
        return toolkit_paths.code(*parts)

    @staticmethod
    def root() -> Path:
        """Return the project root."""
        return toolkit_paths.root

class TaskChunkStore:
    """
    Namespace for the mutable ``base_dir`` used by the ``TaskChunkStore``
    implementation (see ``code/orchestrator/task_chunk_store.py``).

    Tests patch ``TaskChunkStore.base_dir`` directly; no setter method is
    required.  The default points at ``data/raw/task_chunks``.
    """
    # Default storage location – mutable by the test suite
    base_dir: Path = ProjectPaths.data("raw", "task_chunks")