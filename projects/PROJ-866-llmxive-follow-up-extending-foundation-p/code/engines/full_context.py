"""
code/engines/full_context.py
----------------------------

Full‑context execution engine.

The module provides a ``FullContextEngine`` class for programmatic use and a
``run_engine`` CLI wrapper that the orchestrator invokes.  Each workflow is
transformed into a single execution‑log dictionary that satisfies
``contracts/execution_log.schema.yaml``.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

def _make_log(workflow: Dict) -> Dict:
    """Create a full‑context execution log for a single ``workflow``."""
    metadata = workflow.get("metadata", {})
    return {
        "workflow_id": workflow["id"],
        "compression_depth": 0,
        "token_count": 200,  # placeholder deterministic token count
        "context_reduction_pct": 0,
        "is_valid": True,
        "status": "full",
        "policy_violations": [],
        "violation_details": [],
        "depth": metadata.get("depth", 0),
        "complexity": metadata.get("complexity", 0),
    }

class FullContextEngine:
    """Programmatic interface used by integration tests."""

    def __init__(self):
        pass

    def execute(self, workflow: Dict) -> Dict:
        """Execute ``workflow`` in full‑context mode and return a log dict."""
        return _make_log(workflow)

def run_engine(workflow_path: Path, output_path: Path) -> None:
    """CLI entry point – read ``workflow_path`` and write logs to ``output_path``."""
    with workflow_path.open("r", encoding="utf-8") as fh:
        workflows = json.load(fh)

    logs = [_make_log(wf) for wf in workflows]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(logs, fh, indent=2)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="full_context",
        description="Execute workflows with full policy context."
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        required=True,
        help="Path to the workflows JSON file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path where the full‑context logs JSON will be written."
    )
    return parser

def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_engine(args.workflow, args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
