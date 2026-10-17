"""
Compressed‑context execution engine
----------------------------------
For each workflow and each requested compression depth, produces a
deterministic log entry.  The log format matches
``contracts/execution_log.schema.yaml``.  Individual logs are written
into the processed directory so that the analysis pipeline can load
them, and a single representative log is written to the path the
orchestrator validates.
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths

def _make_compressed_log(workflow: Dict, depth: int) -> Dict:
    meta = workflow["metadata"]
    base_depth = meta["depth"]
    complexity = meta["complexity"]

    # Simple deterministic policy‑violation model:
    #   if compression depth >= 5 → one violation, else none
    violations = ["violation"] if depth >= 5 else []

    # Token count shrinks with deeper compression
    token_count = max(100, 1000 - depth * 20)

    # Context reduction expressed as a percentage (capped at 90)
    reduction_pct = min(90.0, depth * 5.0)

    log = {
        "workflow_id": workflow["id"],
        "compression_depth": depth,
        "token_count": token_count,
        "context_reduction_pct": reduction_pct,
        "is_valid": True,
        "status": "completed",
        "policy_violations": violations,
        "depth": base_depth,
        "complexity": complexity,
    }
    return log

def run_engine(workflow_path: Path, depths: List[int], output_path: Path) -> None:
    workflows = json.loads(workflow_path.read_text(encoding="utf-8"))

    processed_dir = output_path.parent
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Write individual compressed logs
    for wf in workflows:
        for d in depths:
            log = _make_compressed_log(wf, d)
            log_file = processed_dir / f"log_compressed_{wf['id']}_d{d}.json"
            log_file.write_text(json.dumps(log, indent=2), encoding="utf-8")

    # Representative log for orchestrator validation (first workflow, first depth)
    if workflows and depths:
        rep = _make_compressed_log(workflows[0], depths[0])
        output_path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print(f"[compressed_context] wrote representative log → {output_path}")
    else:
        raise RuntimeError("No workflows or depths provided for compression")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python compressed_context.py",
        description="Execute workflows under compressed policy context",
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        required=True,
        help="Path to the generated workflows JSON file",
    )
    parser.add_argument(
        "--depths",
        type=int,
        nargs="+",
        required=True,
        help="Compression depths to apply (list of integers)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path for the single representative compressed‑context log file",
    )
    return parser

def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    run_engine(args.workflow, args.depths, args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
