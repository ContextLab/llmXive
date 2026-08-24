"""Main pipeline execution with DAG enforcement.

This module provides:
- DependencyValidationError: raised when a task's dependencies are not met.
- DAGExecutor: loads a DAG definition (YAML), validates it, and executes
  tasks respecting the declared dependencies.
- parse_args: CLI argument parser for the pipeline.
- main: entry point used by the quick‑start script.

The executor does **not** implement the scientific tasks themselves; it
merely guarantees that they are invoked in a dependency‑correct order.
Individual tasks are expected to be supplied as a mapping of task name →
callable (e.g. ``{'download': download_main, ...}``).  The quick‑start
currently only validates the DAG, but the executor can be reused by other
scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Set

import yaml  # PyYAML – added to requirements.txt

from code.logging_config import get_logger

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
class DependencyValidationError(Exception):
    """Raised when a task is attempted before its dependencies are satisfied."""
    pass

# ----------------------------------------------------------------------
# DAG Executor
# ----------------------------------------------------------------------
class DAGExecutor:
    """Execute tasks respecting a directed‑acyclic graph of dependencies.

    Parameters
    ----------
    dag_path : str | Path
        Path to a YAML file describing the DAG.  The file must contain a
        mapping where each key is a task name and its value is a list of
        task names that must complete before the key can run.

    Example YAML
    ------------
    .. code-block:: yaml

        download: []
        preprocess: [download]
        metrics: [preprocess]
        analysis: [metrics]
    """

    def __init__(self, dag_path: str | Path) -> None:
        self.logger = get_logger(__name__)
        self.dag_path = Path(dag_path)
        self.dag: Dict[str, List[str]] = self._load_dag()
        self._validate_acyclic()
        self.completed: Set[str] = set()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _load_dag(self) -> Dict[str, List[str]]:
        """Load the DAG definition from a YAML file."""
        if not self.dag_path.is_file():
            raise FileNotFoundError(f"DAG file not found: {self.dag_path}")
        with self.dag_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        if not isinstance(raw, dict):
            raise ValueError("DAG YAML must define a mapping of task → dependencies")
        # Normalise: ensure every value is a list
        dag: Dict[str, List[str]] = {}
        for task, deps in raw.items():
            if deps is None:
                deps = []
            if not isinstance(deps, list):
                raise ValueError(f"Dependencies for task '{task}' must be a list")
            dag[str(task)] = [str(d) for d in deps]
        self.logger.debug("Loaded DAG with %d tasks", len(dag))
        return dag

    def _validate_acyclic(self) -> None:
        """Detect cycles in the DAG using Kahn's algorithm."""
        # Copy of the adjacency list
        incoming: Dict[str, Set[str]] = {t: set() for t in self.dag}
        outgoing: Dict[str, Set[str]] = {t: set() for t in self.dag}
        for task, deps in self.dag.items():
            for dep in deps:
                if dep not in self.dag:
                    raise ValueError(f"Task '{task}' lists unknown dependency '{dep}'")
                incoming[task].add(dep)
                outgoing[dep].add(task)

        # Kahn's algorithm
        no_incoming = [t for t, deps in incoming.items() if not deps]
        visited: List[str] = []

        while no_incoming:
            n = no_incoming.pop()
            visited.append(n)
            for m in list(outgoing[n]):
                incoming[m].remove(n)
                outgoing[n].remove(m)
                if not incoming[m]:
                    no_incoming.append(m)

        if len(visited) != len(self.dag):
            raise ValueError("Cycle detected in DAG definition")
        self.logger.debug("DAG validation passed – no cycles detected")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate_task(self, task_name: str) -> None:
        """Ensure that all dependencies of *task_name* have been completed."""
        if task_name not in self.dag:
            raise KeyError(f"Task '{task_name}' not defined in DAG")
        missing = [dep for dep in self.dag[task_name] if dep not in self.completed]
        if missing:
            raise DependencyValidationError(
                f"Task '{task_name}' cannot run; missing dependencies: {missing}"
            )
        self.logger.debug("All dependencies satisfied for task '%s'", task_name)

    def run_task(
        self,
        task_name: str,
        func: Callable[..., None],
        *args,
        **kwargs,
    ) -> None:
        """Run *func* after validating its dependencies.

        The function is called with the supplied ``*args`` and ``**kwargs``.
        Upon successful execution the task is marked as completed.
        """
        self.validate_task(task_name)
        self.logger.info("Running task '%s'...", task_name)
        start = time.time()
        try:
            func(*args, **kwargs)
        except Exception as exc:
            self.logger.error("Task '%s' failed: %s", task_name, exc)
            raise
        finally:
            elapsed = time.time() - start
            self.logger.info("Task '%s' finished in %.2f s", task_name, elapsed)
        self.completed.add(task_name)

    def execute_all(self, task_funcs: Dict[str, Callable[..., None]]) -> None:
        """Execute *all* tasks defined in the DAG in a valid order.

        Parameters
        ----------
        task_funcs : dict
            Mapping from task name → callable.  Every task in the DAG must
            have an entry; missing entries raise ``KeyError``.
        """
        # Verify that every DAG task has a corresponding callable
        missing = set(self.dag) - set(task_funcs)
        if missing:
            raise KeyError(f"No callable supplied for tasks: {sorted(missing)}")

        # Simple topological execution loop
        remaining = set(self.dag)
        while remaining:
            runnable = [
                t for t in remaining if all(dep in self.completed for dep in self.dag[t])
            ]
            if not runnable:
                raise DependencyValidationError(
                    f"Circular or unsatisfied dependencies among remaining tasks: {remaining}"
                )
            for task in sorted(runnable):  # deterministic order
                self.run_task(task, task_funcs[task])
                remaining.remove(task)

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments for the pipeline.

    The quick‑start script uses ``--batch-size`` and ``--mode``; they are
    retained here for backward compatibility even though the executor
    itself does not act on them.
    """
    parser = argparse.ArgumentParser(
        description="Execute the analysis pipeline respecting the DAG."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size for downstream processing (unused by DAG executor).",
    )
    parser.add_argument(
        "--mode",
        choices=["cpu", "gpu"],
        default="cpu",
        help="Execution mode (unused by DAG executor).",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Entry point used by ``python code/main_pipeline.py``."""
    args = parse_args()
    logger = get_logger(__name__)

    # Locate the DAG definition – it lives in ``code/utils/pipeline_dag.yaml``.
    dag_file = Path(__file__).parent / "utils" / "pipeline_dag.yaml"
    logger.info("Loading pipeline DAG from %s", dag_file)

    try:
        executor = DAGExecutor(dag_file)
    except Exception as exc:
        logger.error("Failed to initialise DAGExecutor: %s", exc)
        sys.exit(1)

    # At this stage we only validate the DAG; actual task callables are
    # registered elsewhere (e.g. in higher‑level scripts).  For the purpose
    # of the quick‑start we simply report success.
    logger.info("DAG validation successful – all tasks have satisfiable dependencies.")
    # If downstream scripts wish to use the executor they can import this
    # module and call ``executor.execute_all(task_mapping)``.
    sys.exit(0)

if __name__ == "__main__":
    main()
