"""
services/executor.py
---------------------

This module provides a high‑level execution service that ties together three
core components of the project:

1. **Synthetic workflow definition** – the input JSON structure produced by
   ``code/generators/synthetic_workflow.py``.
2. **pm4py** – a process‑mining library used to turn a workflow graph into a
   proper ``EventLog`` (XES‑compatible) object.  The log is useful for downstream
   analysis and for demonstrating that the system can interoperate with a
   standard event‑log format.
3. **OraclePolicyEngine** – the independent rule‑based validator that checks
   each node (event) for policy compliance.

The public API mirrors the style of the existing ``engines`` modules: a class
``Executor`` exposing an ``execute`` method and a small CLI wrapper that writes
a JSON file containing the execution log and validation results.

The implementation purposefully stays lightweight – it does **not** attempt to
re‑implement the compression logic from ``compressed_context.py``; instead it
focuses on demonstrating the requested pm4py integration while still providing
the same output schema used by the rest of the pipeline.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# pm4py imports – the library is declared in ``requirements.txt``.
from pm4py.objects.log.obj import EventLog, Event

from engines.oracle_policy import OraclePolicyEngine


class Executor:
    """
    High‑level executor that:

    * Converts a workflow JSON into a ``pm4py`` :class:`EventLog`.
    * Validates each event (node) against the :class:`OraclePolicyEngine`.
    * Returns a dictionary compatible with the logs produced by the
      ``full_context`` and ``compressed_context`` engines.
    """

    def __init__(self):
        self.oracle = OraclePolicyEngine()

    # -----------------------------------------------------------------
    # Helper: turn workflow graph into a pm4py EventLog
    # -----------------------------------------------------------------
    def _workflow_to_eventlog(self, workflow: Dict[str, Any]) -> EventLog:
        """
        Create a pm4py ``EventLog`` where each node of the workflow becomes a
        single event.  Only a minimal set of attributes is stored – enough to
        illustrate the integration and to allow the Oracle to validate.

        Parameters
        ----------
        workflow: Dict[str, Any]
            The workflow dictionary produced by the generator.

        Returns
        -------
        EventLog
            A pm4py log containing one event per node, ordered as they appear
            in the ``nodes`` list.
        """
        log = EventLog()
        nodes = workflow.get("nodes", [])
        for node in nodes:
            ev = Event()
            # pm4py expects a ``concept:name`` attribute for the activity name.
            ev["concept:name"] = node.get("type", "unknown")
            ev["node_id"] = node.get("id")
            ev["constraints"] = node.get("constraints", [])
            # Store the raw node for possible downstream use.
            ev["raw_node"] = node
            log.append(ev)
        return log

    # -----------------------------------------------------------------
    # Core execution method
    # -----------------------------------------------------------------
    def execute(
        self,
        workflow: Dict[str, Any],
        depth: int | None = None,
        method: str = "bfs",
    ) -> Dict[str, Any]:
        """
        Execute a workflow, generate a pm4py ``EventLog`` and validate it.

        Parameters
        ----------
        workflow: Dict[str, Any]
            The workflow JSON object.
        depth: int | None, optional
            If supplied, the log is *conceptually* compressed to the given
            depth.  The current implementation does **not** alter the log
            (compression is handled by ``compressed_context.py``), but the
            argument is kept for API compatibility.
        method: str, optional
            Traversal method – kept for parity with the compressed engine.
            Accepted values are ``"bfs"`` or ``"dfs"``; it does not affect the
            current implementation.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:

            * ``workflow_id``
            * ``token_count`` – a rough token estimate.
            * ``policy_violations`` – list of violation messages.
            * ``context_reduction_pct`` – ``0.0`` for full context or a
              computed value when ``depth`` is provided.
            * ``is_valid`` – ``True`` only if the workflow is marked valid
              *and* no violations were found.
            * ``event_log`` – the pm4py ``EventLog`` serialized to a list of
              plain dictionaries (JSON‑serialisable).
        """
        workflow_id = workflow.get("id", "unknown")
        metadata = workflow.get("metadata", {})
        is_valid_flag = metadata.get("is_valid", True)

        # -----------------------------------------------------------------
        # 1. Build the pm4py log
        # -----------------------------------------------------------------
        event_log = self._workflow_to_eventlog(workflow)

        # -----------------------------------------------------------------
        # 2. Validate each event using the OraclePolicyEngine
        # -----------------------------------------------------------------
        violations: List[Dict[str, Any]] = []
        for ev in event_log:
            node = ev["raw_node"]
            node_valid, node_violations = self.oracle.validate_node(node)
            if not node_valid:
                for v in node_violations:
                    violations.append(
                        {
                            "node_id": ev["node_id"],
                            "rule_id": v,
                        }
                    )

        # -----------------------------------------------------------------
        # 3. Token count – keep the same rough heuristic used elsewhere.
        # -----------------------------------------------------------------
        full_token_count = len(str(workflow)) // 4
        compressed_token_count = full_token_count
        reduction_pct = 0.0
        if depth is not None and depth > 0:
            # Very simple proxy: assume each depth level removes an equal
            # fraction of tokens.  This is *only* to provide a numeric field;
            # real compression is performed by ``compressed_context``.
            reduction_pct = min(100.0, (depth / max(1, workflow.get("depth", 1))) * 100.0)
            compressed_token_count = int(full_token_count * (1 - reduction_pct / 100.0))

        # -----------------------------------------------------------------
        # 4. Assemble the result dictionary
        # -----------------------------------------------------------------
        result: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "compression_depth": depth if depth is not None else 0,
            "token_count": compressed_token_count,
            "policy_violations": [v["rule_id"] for v in violations],
            "violation_details": violations,
            "context_reduction_pct": reduction_pct,
            "is_valid": is_valid_flag and len(violations) == 0,
            "status": "normal" if len(violations) == 0 else "edge_case",
            # Serialize the EventLog – pm4py objects are not JSON serialisable.
            "event_log": [
                {
                    "concept:name": ev["concept:name"],
                    "node_id": ev["node_id"],
                    "constraints": ev["constraints"],
                }
                for ev in event_log
            ],
        }

        return result

    # -----------------------------------------------------------------
    # CLI entry point – mirrors the style of the other engine scripts.
    # -----------------------------------------------------------------
    def run_cli(self) -> None:
        """
        Parse command‑line arguments and write the execution result to a JSON
        file.  The CLI expects the same arguments as the other engine scripts
        to keep the quick‑start documentation consistent.
        """
        import argparse

        parser = argparse.ArgumentParser(
            description="Execute a workflow and produce a pm4py EventLog with Oracle validation"
        )
        parser.add_argument(
            "--workflow",
            type=str,
            required=True,
            help="Path to the input workflow JSON file (single workflow or list)",
        )
        parser.add_argument(
            "--output",
            type=str,
            required=True,
            help="Path where the execution log JSON will be written",
        )
        parser.add_argument(
            "--depth",
            type=int,
            default=None,
            help="Optional compression depth (numeric only, for reporting purposes)",
        )
        parser.add_argument(
            "--method",
            type=str,
            default="bfs",
            choices=["bfs", "dfs"],
            help="Traversal method – kept for API compatibility",
        )

        args = parser.parse_args()

        workflow_path = Path(args.workflow)
        if not workflow_path.exists():
            print(f"Error: workflow file not found: {args.workflow}", file=sys.stderr)
            sys.exit(1)

        with open(workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # The generator may emit a list or a single dict.
        workflows = data if isinstance(data, list) else [data]

        all_results: List[Dict[str, Any]] = []
        for wf in workflows:
            res = self.execute(wf, depth=args.depth, method=args.method)
            all_results.append(res)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        print(f"Executed {len(workflows)} workflow(s); results written to {args.output}")



def main() -> None:
    """
    Entry point used by ``python -m services.executor`` or the ``if __name__ == '__main__'``
    guard at the bottom of the file.
    """
    executor = Executor()
    executor.run_cli()


if __name__ == "__main__":
    main()
