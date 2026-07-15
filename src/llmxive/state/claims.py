"""Per-project claim store (spec 016 / T006).

state/claims/<PROJ-ID>.yaml is a flat list of Claim records.
Mirrors state/citations.py — load/save/upsert/get, repo_root-aware.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.config import repo_root as _repo_root
from llmxive.state._io import atomic_write_text


def _state_root() -> Path:
    return _repo_root() / "state"


def _claims_path(project_id: str, *, repo_root: Path | None = None) -> Path:
    state_dir = (repo_root / "state") if repo_root else _state_root()
    return state_dir / "claims" / f"{project_id}.yaml"


def _claim_to_dict(c: Claim) -> dict[str, Any]:
    return {
        "claim_id": c.claim_id,
        "kind": c.kind.value if isinstance(c.kind, ClaimKind) else c.kind,
        "raw_text": c.raw_text,
        "canonical": c.canonical,
        "context": c.context,
        "artifact_path": c.artifact_path,
        "source_type": c.source_type,
        "status": c.status.value if isinstance(c.status, ClaimStatus) else c.status,
        "resolved_value": c.resolved_value,
        "evidence": c.evidence,
        "resolver": c.resolver,
        "attempts": c.attempts,
        "updated_at": c.updated_at,
        "source_hash": c.source_hash,
    }


def _dict_to_claim(d: dict[str, Any]) -> Claim:
    return Claim(
        claim_id=d["claim_id"],
        kind=ClaimKind(d["kind"]),
        raw_text=d["raw_text"],
        canonical=d["canonical"],
        context=d["context"],
        artifact_path=d["artifact_path"],
        source_type=d["source_type"],
        status=ClaimStatus(d["status"]),
        resolved_value=d.get("resolved_value"),
        evidence=d.get("evidence"),
        resolver=d.get("resolver"),
        attempts=int(d.get("attempts", 0)),
        updated_at=d.get("updated_at", ""),
        source_hash=d.get("source_hash"),
    )


def load(project_id: str, *, repo_root: Path | None = None) -> list[Claim]:
    path = _claims_path(project_id, repo_root=repo_root)
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return [_dict_to_claim(item) for item in raw]


def save(project_id: str, claims: list[Claim], *, repo_root: Path | None = None) -> Path:
    payload = [_claim_to_dict(c) for c in claims]
    path = _claims_path(project_id, repo_root=repo_root)
    atomic_write_text(path, yaml.safe_dump(payload, sort_keys=True))
    return path


def upsert(project_id: str, claim: Claim, *, repo_root: Path | None = None) -> None:
    """Replace by claim_id (no duplicates); insert if not present."""
    existing = load(project_id, repo_root=repo_root)
    updated = [c for c in existing if c.claim_id != claim.claim_id]
    updated.append(claim)
    save(project_id, updated, repo_root=repo_root)


def get(project_id: str, claim_id: str, *, repo_root: Path | None = None) -> Claim | None:
    for c in load(project_id, repo_root=repo_root):
        if c.claim_id == claim_id:
            return c
    return None


def load_verified_by_subject(
    project_id: str, *, repo_root: Path | None = None
) -> dict[tuple[ClaimKind, str], Claim]:
    """Frozen-store view: ``(kind, subject_key) -> the VERIFIED Claim`` (spec 020).

    The single value-independent index the freeze reads (FR-009/013): a rephrased
    or corrected mention of the same fact shares the same ``(kind, subject_key)``
    and so maps to the one frozen VERIFIED record. Only VERIFIED records with a
    non-empty ``subject_key`` are included (a bare-number/empty-subject claim has
    key ``""`` and must never match anything); the first VERIFIED record for a key
    wins (the invariant is at most one VERIFIED per key).
    """
    from llmxive.claims.canonical import subject_key

    out: dict[tuple[ClaimKind, str], Claim] = {}
    for c in load(project_id, repo_root=repo_root):
        if c.status != ClaimStatus.VERIFIED:
            continue
        sk = subject_key(c)
        if sk:
            out.setdefault((c.kind, sk), c)
    return out


__all__ = ["get", "load", "load_verified_by_subject", "save", "upsert"]
