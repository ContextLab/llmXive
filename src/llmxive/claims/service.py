"""T017 — Claim-layer service (spec 016, US1).

process_document(text, *, artifact_path, project_id, backend, model, repo_root)
    -> tuple[str, list[Claim], GateReport]

Orchestrates the full extract → register → substitute → resolve → render
pipeline for one document pass. Idempotent: a claim already VERIFIED in the
registry is reused without re-resolution.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Any

from llmxive.claims.extract import extract_claims
from llmxive.claims.models import Claim, ClaimStatus
from llmxive.claims.pointer import GateReport, render, substitute_pointers, to_pointer
from llmxive.claims.resolve import resolve
from llmxive.state import claims as _claim_store

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def process_document(
    text: str,
    *,
    artifact_path: str,
    project_id: str,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> tuple[str, list[Claim], GateReport]:
    """Extract → register → substitute → resolve → render one document.

    Returns ``(rendered_text, claims, GateReport)``.

    Idempotency: if a claim with the same ``claim_id`` is already in the
    registry with status VERIFIED, it is reused without re-resolution.
    All other statuses (PENDING / NOT_ENOUGH_INFO / REFUTED / UNRESOLVABLE)
    are re-resolved so transient failures self-heal on the next round.

    Never raises — on extraction failure returns ``(text, [], GateReport())``.
    """
    # Step 1: Extract claims from the document.
    try:
        new_claims = extract_claims(
            text,
            artifact_path=artifact_path,
            backend=backend,
            model=model,
            repo_root=repo_root,
        )
    except Exception as exc:
        logger.warning("claims.service: extraction failed (%s); no-op pass", exc)
        return text, [], GateReport()

    if not new_claims:
        return text, [], GateReport()

    # Step 2: Upsert each claim into the registry (dedup by claim_id).
    # Load registry once; upsert individually so we pick up prior VERIFIED state.
    for claim in new_claims:
        existing = _claim_store.get(project_id, claim.claim_id, repo_root=repo_root)
        if existing is None:
            _claim_store.upsert(project_id, claim, repo_root=repo_root)

    # Step 3: Substitute claim spans with {{claim:<id>}} pointers.
    spans = [(c.raw_text, c.claim_id) for c in new_claims]
    text_with_pointers = substitute_pointers(text, spans)

    # Step 4: Resolve each PENDING claim (skip already-VERIFIED ones).
    resolved_claims: list[Claim] = []
    for claim in new_claims:
        # Reload from registry to get the current status (may be VERIFIED from a prior round).
        current = _claim_store.get(project_id, claim.claim_id, repo_root=repo_root) or claim

        if current.status == ClaimStatus.VERIFIED:
            resolved_claims.append(current)
            continue

        # Re-resolve (self-heals transient failures).
        verdict = resolve(current, backend=backend, model=model, repo_root=repo_root)

        updated = Claim(
            claim_id=current.claim_id,
            kind=current.kind,
            raw_text=current.raw_text,
            canonical=current.canonical,
            context=current.context,
            artifact_path=current.artifact_path,
            source_type=current.source_type,
            status=verdict.status,
            resolved_value=verdict.value,
            evidence=verdict.evidence,
            resolver=verdict.resolver,
            attempts=current.attempts + 1,
            updated_at=_now_iso(),
        )
        _claim_store.upsert(project_id, updated, repo_root=repo_root)
        resolved_claims.append(updated)

    # Step 5: Render — substitute pointers with verified values or markers.
    claims_by_id = {c.claim_id: c for c in resolved_claims}
    rendered_text, gate_report = render(text_with_pointers, claims_by_id)

    return rendered_text, resolved_claims, gate_report


__all__ = ["process_document"]
