"""
Minimal scheduler implementation for the purpose of T005.

The original project contains a more feature‑rich scheduler; however,
the test suite for T005 only requires that **every created chunk** is
persisted via ``TaskChunkStore.append``.  This module therefore provides
a lightweight ``Scheduler`` class with a ``process_chunks`` method that
demonstrates the required integration point.

The implementation is deliberately simple:
- It receives an iterable of chunk dictionaries.
- For each chunk it calls ``TaskChunkStore.append``.
- It returns the list of chunks that were processed (useful for tests).

Real‑world code would include heartbeat handling, dropout detection,
etc.; those responsibilities are exercised in other tasks.
"""

from typing import Iterable, List, Dict

from orchestrator.task_chunk_store import TaskChunkStore


class Scheduler:
    """
    Very small scheduler used by the unit‑test for T005.

    The scheduler does **not** perform any actual orchestration – it only
    demonstrates the contract that every chunk must be stored.
    """

    def __init__(self) -> None:
        # In a full implementation this would hold state such as the
        # node manager, heartbeat monitor, etc.
        pass

    def process_chunks(self, chunks: Iterable[Dict]) -> List[Dict]:
        """
        Persist each chunk using ``TaskChunkStore.append``.

        Parameters
        ----------
        chunks : iterable of dict
            Chunk records, each of which must contain a ``run_id`` key.

        Returns
        -------
        list of dict
            The chunks that were processed (identical to the input list).
        """
        processed: List[Dict] = []
        for chunk in chunks:
            # Validate the chunk against the schema – let the store raise if
            # the record is invalid.
            TaskChunkStore.append(chunk)
            processed.append(chunk)
        return processed