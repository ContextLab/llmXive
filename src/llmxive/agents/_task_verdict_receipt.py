"""Authenticate verifier decisions independently of model-writable project files.

The signing secret stays in the orchestrator, outside analysis_environment.
This protects cached verdict integrity, not the host against hostile processes:
the current research execution environment is not an OS filesystem sandbox.
"""
from __future__ import annotations

import hmac
from pathlib import Path

from llmxive.credentials import MissingCredentialError
from llmxive.results.receipt import load_signing_key, sign_receipt


def _payload(project_dir: Path, tasks_path: Path, task_key: str, verdict: dict) -> dict:
    return {
        "domain": "llmxive.independent-task-verdict.v1",
        "project_id": project_dir.name,
        "tasks_path": tasks_path.resolve().relative_to(project_dir.resolve()).as_posix(),
        "task_key": task_key,
        "verdict": {k: v for k, v in verdict.items() if k != "sig"},
    }


def signed_verdict(project_dir: Path, tasks_path: Path, task_key: str, verdict: dict) -> dict | None:
    """Mint only after an independent decision; missing keys disable caching."""
    try:
        signature = sign_receipt(_payload(project_dir, tasks_path, task_key, verdict),
                                 key=load_signing_key())
    except (MissingCredentialError, PermissionError, OSError):
        return None
    return {**verdict, "sig": signature}


def authentic_verdict(project_dir: Path, tasks_path: Path, task_key: str, verdict: object) -> bool:
    """Unsigned legacy data, tampering, replay and missing keys are cache misses."""
    if not isinstance(verdict, dict) or not isinstance(verdict.get("sig"), str):
        return False
    if not isinstance(verdict.get("h"), str) or type(verdict.get("c")) is not bool:
        return False
    try:
        expected = sign_receipt(_payload(project_dir, tasks_path, task_key, verdict),
                                key=load_signing_key())
        return hmac.compare_digest(expected, verdict["sig"])
    except (MissingCredentialError, PermissionError, OSError, ValueError, TypeError, RecursionError):
        return False
