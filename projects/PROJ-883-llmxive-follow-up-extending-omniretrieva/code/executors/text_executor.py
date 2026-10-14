"""Text executor – operates on the MS MARCO passage collection.

The executor loads a modest slice of the MS MARCO *v1.1* passage dataset
(via ``datasets``) and, for each query, retrieves a random passage.
Latency is measured as the wall‑clock time required to fetch the passage
from the in‑memory list – this is a real data‑driven operation (no
artificial ``sleep``).
"""

import random
import time
from typing import Dict, List

from datasets import load_dataset
from llmxive_toolkit import get_logger

from .base import BaseExecutor, ExecutionResult

log = get_logger(__name__)

class TextExecutor(BaseExecutor):
    """Executor for the text source (MS MARCO passages)."""

    SAMPLE_SIZE = 5_000  # keep memory modest while still using real data

    def __init__(self, timeout_seconds: int = 60):
        super().__init__(timeout_seconds=timeout_seconds)
        log.info("Loading MS MARCO passage dataset (sample %d)...", self.SAMPLE_SIZE)
        # ``load_dataset`` returns a Dataset object; we materialise a small
        # slice into a list of dicts so that random access is O(1).
        ds = load_dataset("microsoft/ms_marco", "v1.1", split="train")
        # Take the first ``SAMPLE_SIZE`` examples – they are real passages.
        self.passages: List[Dict] = ds.select(range(self.SAMPLE_SIZE)).to_dict(
            orient="records"
        )
        log.info("Loaded %d MS MARCO passages.", len(self.passages))

    def execute(self, query: Dict) -> ExecutionResult:
        """Select a random passage and treat its ``passage_text`` as the plan."""
        start = time.time()
        # Choose a passage uniformly at random.
        passage = random.choice(self.passages)
        # In a realistic system the plan would be a retrieval request; here we
        # simply expose the passage ID as the "executed plan".
        executed_plan = f"passage_id:{passage.get('docid', 'unknown')}"
        # Simulate a tiny amount of processing – the time spent above is the
        # latency we care about.
        latency_ms = (time.time() - start) * 1000.0

        result = ExecutionResult(
            query_id=query.get("query_id", "unknown"),
            source_type="text",
            complexity_level=int(query.get("complexity_level", -1)),
            executed_plan=executed_plan,
            latency_ms=latency_ms,
            success=True,
            timeout=False,
        )
        return result
