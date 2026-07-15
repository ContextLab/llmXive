"""T026 — Per-project execution receipt store (spec 016, US2).

Persists / loads Receipt objects at
    state/results/<PROJECT-ID>/<result_id>.yaml

Mirrors state/claims.py — load/save/get, repo_root-aware.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmxive.config import repo_root as _repo_root
from llmxive.results.receipt import Receipt
from llmxive.state._io import atomic_write_text


def _state_root() -> Path:
    return _repo_root() / "state"


def _results_dir(project_id: str, *, repo_root: Path | None = None) -> Path:
    state_dir = (repo_root / "state") if repo_root else _state_root()
    return state_dir / "results" / project_id


def _receipt_path(project_id: str, result_id: str,
                  *, repo_root: Path | None = None) -> Path:
    return _results_dir(project_id, repo_root=repo_root) / f"{result_id}.yaml"


# ---------------------------------------------------------------------------
# Serialise / deserialise
# ---------------------------------------------------------------------------

def _receipt_to_dict(r: Receipt) -> dict[str, Any]:
    return {
        "result_id": r.result_id,
        "value": r.value,
        "kind": r.kind,
        "producer": r.producer,
        "inputs": r.inputs,
        "env_sha": r.env_sha,
        "captured": r.captured,
        "output_sha256": r.output_sha256,
        "created_at": r.created_at,
        "hmac": r.hmac,
    }


def _dict_to_receipt(d: dict[str, Any]) -> Receipt:
    return Receipt(
        result_id=d["result_id"],
        value=str(d["value"]),
        kind=str(d["kind"]),
        producer=dict(d["producer"]),
        inputs=dict(d["inputs"]),
        env_sha=str(d["env_sha"]),
        captured=dict(d["captured"]),
        output_sha256=str(d["output_sha256"]),
        created_at=str(d["created_at"]),
        hmac=str(d["hmac"]),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save(project_id: str, receipt: Receipt,
         *, repo_root: Path | None = None) -> Path:
    """Persist a receipt to state/results/<PROJECT-ID>/<result_id>.yaml."""
    path = _receipt_path(project_id, receipt.result_id, repo_root=repo_root)
    payload = _receipt_to_dict(receipt)
    atomic_write_text(path, yaml.safe_dump(payload, sort_keys=True))
    return path


def load(project_id: str, result_id: str,
         *, repo_root: Path | None = None) -> Receipt | None:
    """Load a receipt; returns None if not found."""
    path = _receipt_path(project_id, result_id, repo_root=repo_root)
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return None
    return _dict_to_receipt(data)


def load_all(project_id: str, *, repo_root: Path | None = None) -> list[Receipt]:
    """Load all receipts for a project."""
    d = _results_dir(project_id, repo_root=repo_root)
    if not d.exists():
        return []
    receipts = []
    for yaml_file in sorted(d.glob("*.yaml")):
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if data:
            receipts.append(_dict_to_receipt(data))
    return receipts


def get(project_id: str, result_id: str,
        *, repo_root: Path | None = None) -> Receipt | None:
    """Alias for load — mirrors claims.get naming."""
    return load(project_id, result_id, repo_root=repo_root)


__all__ = ["get", "load", "load_all", "save"]
