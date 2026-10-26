"""
code.services.executor_full
---------------------------

Full‑context execution engine.

This script reads the synthetic workflows generated at
``data/raw/workflows.json``, evaluates each workflow with the
independent Oracle Policy Engine, tokenizes the entire workflow
(using the project's tokenizer wrapper), and writes a list of
execution‑log dictionaries to ``data/processed/full_context_logs.json``.
The output conforms to ``contracts/execution_log.schema.yaml`` with
``compression_depth = 0`` and ``context_reduction_pct = 0``.

The script is intended to be invoked via the module flag:

    python -m code.services.executor_full --n 5

where ``--n`` limits the number of workflows processed (useful for
quick tests).  If ``--n`` is omitted, all workflows are processed.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

# The tokenizer wrapper is defined in ``code/lib/utils.py``.
# It provides ``count_tokens(text: str) -> int`` using the ``tiktoken``
# model ``cl100k_base``.
try:
    from code.lib.utils import count_tokens
except ImportError as exc:
    raise ImportError(
        "Tokenizer wrapper not found. Ensure that ``code/lib/utils.py`` defines "
        "``count_tokens`` and that the package ``tiktoken`` is installed."
    ) from exc

# The independent Oracle Policy Engine lives in ``code/engines/oracle_policy.py``.
try:
    from code.engines.oracle_policy import OraclePolicyEngine
except ImportError as exc:
    raise ImportError(
        "OraclePolicyEngine not found. Ensure that ``code/engines/oracle_policy.py`` "
        "exposes the class ``OraclePolicyEngine``."
    ) from exc

log = get_logger(__name__)

def _load_workflows(workflow_path: Path) -> List[Dict]:
    """Load the list of workflow dictionaries from ``workflow_path``."""
    if not workflow_path.is_file():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
    with workflow_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON array of workflows in {workflow_path}, got {type(data)}"
        )
    return data

def _make_full_context_log(
    workflow: Dict,
    token_cnt: int,
    violations: List[Dict],
    oracle_details: List[Dict],
) -> Dict:
    """
    Construct a single execution‑log dictionary that satisfies the contract.

    Parameters
    ----------
    workflow: Dict
        The original workflow dictionary (must contain at least ``id`` and optionally
        ``metadata`` with ``depth`` and ``complexity``).
    token_cnt: int
        Token count for the *entire* workflow (including its policy graph).
    violations: List[Dict]
        List of violation identifiers (e.g. ``[\"budget_exceeded\"]``).  The schema
        expects a list of strings; we therefore extract the ``rule_id`` if present.
    oracle_details: List[Dict]
        Detailed information about each violation (as returned by the Oracle).
    """
    metadata = workflow.get("metadata", {})
    # The schema requires ``workflow_id``, ``compression_depth``, ``token_count``,
    # and ``policy_violations``.  All other fields are optional but useful for
    # downstream analysis.
    return {
        "workflow_id": workflow.get("id", "unknown"),
        "compression_depth": 0,                     # full‑context → no compression
        "token_count": token_cnt,
        "context_reduction_pct": 0,                  # no reduction
        "is_valid": True,
        "status": "full_context",
        "policy_violations": [v.get("rule_id", str(v)) for v in violations],
        "violation_details": oracle_details,
        "depth": metadata.get("depth", 0),
        "complexity": metadata.get("complexity", 0),
    }

def _process_workflow(
    workflow: Dict,
    oracle: OraclePolicyEngine,
) -> Dict:
    """
    Evaluate a single workflow with the Oracle and compute its token count.

    Returns the execution‑log dictionary.
    """
    # Token count – we serialize the *entire* workflow (including any embedded
    # policy graph) and count tokens using the shared tokenizer.
    workflow_json = json.dumps(workflow, separators=(",", ":"))
    token_cnt = count_tokens(workflow_json)

    # Oracle evaluation – the OraclePolicyEngine is expected to expose a method
    # ``evaluate`` that returns a tuple ``(violations, details)`` where
    # ``violations`` is a list of dicts (or strings) and ``details`` is a list
    # of dicts describing each violation.  If the concrete implementation differs,
    # adapt the call accordingly.
    try:
        violations, details = oracle.evaluate(workflow)
    except Exception as exc:
        # Guard against unexpected Oracle implementations – we log and treat the
        # workflow as having no violations.
        log.error("Oracle evaluation failed for workflow %s: %s", workflow.get("id"), exc)
        violations, details = [], []

    return _make_full_context_log(workflow, token_cnt, violations, details)

def run_full_context(
    workflow_path: Path,
    output_path: Path,
    limit: int | None = None,
) -> None:
    """
    Core driver for the full‑context engine.

    Parameters
    ----------
    workflow_path: Path
        Path to ``data/raw/workflows.json``.
    output_path: Path
        Destination for the JSON array of execution logs.
    limit: int | None
        Optional maximum number of workflows to process (used by the ``--n`` CLI flag).
    """
    log.info("Loading workflows from %s", workflow_path)
    workflows = _load_workflows(workflow_path)

    if limit is not None:
        workflows = workflows[:limit]
        log.info("Limiting processing to %d workflows", limit)

    oracle = OraclePolicyEngine()

    logs: List[Dict] = []
    for wf in workflows:
        logs.append(_process_workflow(wf, oracle))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(logs, fh, indent=2)
    log.info("Wrote %d full‑context logs to %s", len(logs), output_path)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="executor_full",
        description="Full‑context execution engine (mode=full_context).",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Maximum number of workflows to process (default: all).",
    )
    return parser

def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    workflow_file = paths.data("raw", "workflows.json")
    output_file = paths.data("processed", "full_context_logs.json")

    run_full_context(workflow_file, output_file, limit=args.n)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
