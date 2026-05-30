"""T017 — Claim-layer service (spec 016, US1).

process_document(text, *, artifact_path, project_id, backend, model, repo_root)
    -> tuple[str, list[Claim], GateReport]

Orchestrates the full extract → register → substitute → resolve → render
pipeline for one document pass. Idempotent: a claim already VERIFIED in the
registry is reused without re-resolution.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
from pathlib import Path
from typing import Any

from llmxive.claims.extract import extract_claims
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.claims.pointer import GateReport, render, substitute_pointers, to_pointer
from llmxive.claims.resolve import resolve
from llmxive.state import claims as _claim_store

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _source_hash_from_evidence(evidence: dict | None, value: str | None) -> str | None:
    """Fingerprint of the underlying artifact at resolution time (FR-015).

    For an internal-result claim, the receipt's ``output_sha256`` IS the
    artifact hash. For an external claim, fingerprint the source identity +
    resolved value, so re-resolution after a true content change (a different
    ``output_sha256`` / source identity) is detectable. Returns None when
    there is no source to fingerprint (an unresolved claim).
    """
    if not evidence:
        return None
    if evidence.get("output_sha256"):
        return str(evidence["output_sha256"])
    source = evidence.get("source_id") or evidence.get("source") or evidence.get("url")
    if not source:
        return None
    return hashlib.sha256(f"{source}\x00{value or ''}".encode()).hexdigest()


def _live_source_hash(claim: Claim, project_id: str, repo_root: Path) -> str | None:
    """Recompute the current underlying-artifact hash for a VERIFIED claim.

    Result claims re-look-up the backing receipt — its ``output_sha256``
    changes or vanishes when the execution artifact changes (FR-015). External
    claims keep their identity fingerprint; their resolver-level cache
    (grounding fulltext/verdict TTL) forces re-resolution when a source is
    purged or expires. Returns None when the artifact can no longer be found.
    """
    if claim.kind == ClaimKind.RESULT:
        from llmxive.results.harness import result_backed

        candidate = claim.resolved_value or claim.canonical or claim.raw_text
        receipt = result_backed(candidate, project_id, repo_root=repo_root)
        return receipt.output_sha256 if receipt is not None else None
    return _source_hash_from_evidence(claim.evidence, claim.resolved_value)


def resolve_registered_claims(
    claims: list[Claim],
    *,
    project_id: str,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> list[Claim]:
    """Resolve each registered claim, reusing verified ones (FR-015).

    For each claim, the current registry state is reloaded by ``claim_id``.
    A VERIFIED claim whose underlying source/receipt artifact is unchanged is
    REUSED without re-resolution (the resolver is not invoked). A VERIFIED
    claim whose live artifact hash differs from the one recorded at resolution
    time is INVALIDATED and re-resolved. Every other status is re-resolved so
    transient not-enough-info failures self-heal on the next round.
    """
    resolved: list[Claim] = []
    for claim in claims:
        # Reload from the registry (may be VERIFIED from a prior round).
        current = _claim_store.get(project_id, claim.claim_id, repo_root=repo_root) or claim

        if current.status == ClaimStatus.VERIFIED:
            live = _live_source_hash(current, project_id, repo_root)
            if current.source_hash is None:
                unchanged = True  # legacy entry without a recorded hash: trust prior verify
            elif live == current.source_hash:
                unchanged = True  # underlying artifact identical → reuse
            elif live is None and current.kind != ClaimKind.RESULT:
                unchanged = True  # external source not re-derivable here → trust prior verify
            else:
                # live differs, or a RESULT lost its backing receipt → invalidate.
                unchanged = False
            if unchanged:
                resolved.append(current)
                continue
            logger.info(
                "claims.service: invalidating %s (underlying source/receipt changed)",
                current.claim_id,
            )

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
            source_hash=_source_hash_from_evidence(verdict.evidence, verdict.value),
        )
        _claim_store.upsert(project_id, updated, repo_root=repo_root)
        resolved.append(updated)
    return resolved


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
    resolved_claims = resolve_registered_claims(
        new_claims,
        project_id=project_id,
        backend=backend,
        model=model,
        repo_root=repo_root,
    )

    # Step 5: Render — substitute pointers with verified values or markers.
    claims_by_id = {c.claim_id: c for c in resolved_claims}
    rendered_text, gate_report = render(text_with_pointers, claims_by_id)

    # Step 6 (T035): repair citations for filled claims so the rendered text
    # cites the authoritative fill source rather than a stale paper citation.
    # Import lazily to avoid circular imports (fill → claims → fill).
    try:
        from llmxive.fill.citation_repair import repair_citation  # noqa: PLC0415
        from llmxive.fill.models import FillProvenance  # noqa: PLC0415

        for claim in resolved_claims:
            ev = claim.evidence or {}
            if not ev.get("filled") and not ev.get("fill"):
                continue
            fill_d = ev.get("fill") or {}
            if not fill_d:
                continue
            try:
                provenance = FillProvenance(
                    value=fill_d.get("value", ""),
                    source_id=fill_d.get("source_id", ""),
                    url=fill_d.get("url", ""),
                    quote=fill_d.get("quote", ""),
                    channel=fill_d.get("channel", ""),
                    conflicts=fill_d.get("conflicts", []),
                )
                rendered_text = repair_citation(
                    rendered_text, claim=claim, provenance=provenance
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "claims.service: citation repair skipped for %s: %s",
                    claim.claim_id, exc,
                )
    except ImportError:
        pass  # fill package not available; skip silently

    return rendered_text, resolved_claims, gate_report


__all__ = ["process_document", "resolve_registered_claims"]
