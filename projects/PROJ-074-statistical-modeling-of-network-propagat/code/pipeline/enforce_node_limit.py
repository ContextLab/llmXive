"""Demonstrate and verify node-limit enforcement in ``load_cascade`` (T014).

This script creates two validation-fixture cascade files (one within the
node limit, one exceeding it), runs the cascade loader over them, and
verifies that:

1. The oversized cascade is skipped (``load_cascade`` returns None).
2. Its cascade ID is recorded in ``results/skipped_cascades.log``.
3. The valid cascade is loaded successfully.

The fixtures exercise the validation logic only; they are not analysis
data and are written under a dedicated fixture directory.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.utils import load_cascade, setup_logger

NODE_LIMIT = 2000


def make_cascade(cascade_id: str, n_nodes: int, base: datetime) -> dict:
    """Build a JSON edge-list cascade document with n_nodes nodes."""
    nodes = []
    for i in range(n_nodes):
        nodes.append(
            {
                "node_id": f"{cascade_id}_n{i}",
                "timestamp": (base + timedelta(seconds=i)).isoformat(),
                "cascade_id": cascade_id,
                "user_id": f"user_{i % 50}",
                "message_id": f"{cascade_id}_msg",
                "platform_id": "platform_0",
                "historical_degree": (i % 5) + 1,
                "historical_shares": i % 3,
                "cascade_label": 1 if n_nodes > 100 else 0,
            }
        )
    return {"nodes": nodes}


def main() -> int:
    from llmxive_toolkit import paths

    logger = setup_logger("pipeline.enforce_node_limit")

    fixture_dir = paths.data("node_limit_fixtures")
    skipped_log = paths.results("skipped_cascades.log")
    # Start fresh so this run's log is deterministic.
    if skipped_log.exists():
        skipped_log.unlink()

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)

    valid_file = fixture_dir / "cascade_small.json"
    oversized_file = fixture_dir / "cascade_oversized.json"
    with open(valid_file, "w", encoding="utf-8") as f:
        json.dump(make_cascade("cascade_small", 10, base), f)
    with open(oversized_file, "w", encoding="utf-8") as f:
        json.dump(
            make_cascade("cascade_oversized", NODE_LIMIT + 1, base), f
        )

    df_valid = load_cascade(
        str(valid_file),
        node_limit=NODE_LIMIT,
        logger=logger,
        skipped_log_path=str(skipped_log),
    )
    df_oversized = load_cascade(
        str(oversized_file),
        node_limit=NODE_LIMIT,
        logger=logger,
        skipped_log_path=str(skipped_log),
    )

    assert df_valid is not None, "Valid cascade should load successfully."
    assert (
        df_oversized is None
    ), "Oversized cascade should be skipped (return None)."

    log_text = skipped_log.read_text(encoding="utf-8")
    assert (
        "cascade_id=cascade_oversized" in log_text
    ), "Oversized cascade ID must appear in skipped_cascades.log"
    assert "node_limit_exceeded" in log_text

    print(f"skipped_cascades.log written to: {skipped_log}")
    print("Node-limit enforcement verified: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
