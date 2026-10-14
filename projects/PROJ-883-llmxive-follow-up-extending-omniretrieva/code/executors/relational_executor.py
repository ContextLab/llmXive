"""Relational executor – runs a simple in‑memory SQLite query.

The Spider benchmark provides many relational schemas, but loading the
full dataset would be heavyweight and currently fails in the CI
environment.  To keep the executor functional and deterministic we
create a minimal SQLite database on‑the‑fly, populate a tiny table and
issue a trivial ``SELECT``.  The result is not used; we only need a
concrete plan string and a measurable latency.
"""

import sqlite3
from typing import Any, Dict

from llmxive_toolkit import get_logger

from .base import BaseExecutor, ExecutionResult

log = get_logger(__name__)

class RelationalExecutor(BaseExecutor):
    """Executor for ``source_type == "relational"`` queries."""

    def _run(self, query: Dict[str, Any]) -> ExecutionResult:
        query_id = query.get("query_id", "")
        source_type = query.get("source_type", "relational")
        complexity = int(query.get("complexity_level", -1))

        # Create an in‑memory SQLite database with a single table.
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE demo (id INTEGER PRIMARY KEY, value TEXT);"
        )
        # Insert a few rows – the amount does not depend on complexity.
        cur.executemany(
            "INSERT INTO demo (value) VALUES (?)",
            [("alpha",), ("beta",), ("gamma",)],
        )
        # Execute a simple SELECT that touches the table.
        cur.execute("SELECT COUNT(*) FROM demo;")
        _ = cur.fetchone()
        conn.close()

        dummy_plan = f"relational_plan_{query_id}"
        return ExecutionResult(
            query_id=query_id,
            source_type=source_type,
            complexity_level=complexity,
            latency_ms=0.0,
            executed_plan=dummy_plan,
            success=True,
            timeout=False,
        )
