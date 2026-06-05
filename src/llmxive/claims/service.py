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
from dataclasses import replace
from pathlib import Path
from typing import Any

from llmxive.claims.canonical import subject_key
from llmxive.claims.extract import extract_claims
from llmxive.claims.gate import strip_claim_artifacts
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.claims.planning_scan import strip_empirical_values
from llmxive.claims.pointer import (
    GateReport,
    drop_orphan_pointers,
    pointer_ids,
    render,
    substitute_pointers,
)
from llmxive.claims.resolve import resolve
from llmxive.claims.smooth import strip_and_smooth
from llmxive.claims.stage import is_planning_stage
from llmxive.state import claims as _claim_store

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _source_hash_from_evidence(evidence: dict[str, Any] | None, value: str | None) -> str | None:
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
    # spec 020 FR-009/011: the frozen, value-independent index. A non-VERIFIED
    # claim whose (kind, subject_key) is already VERIFIED here adopts that frozen
    # value WITHOUT re-resolution — closing the gap where a claim left PENDING in
    # the registry (a prior round's transient failure / re-extraction) is
    # re-resolved every round and waffles.
    verified_by_subject = _claim_store.load_verified_by_subject(
        project_id, repo_root=repo_root
    )

    resolved: list[Claim] = []
    for claim in claims:
        # Reload from the registry (may be VERIFIED from a prior round).
        current = _claim_store.get(project_id, claim.claim_id, repo_root=repo_root) or claim

        if current.status != ClaimStatus.VERIFIED:
            sk = subject_key(current)
            twin = verified_by_subject.get((current.kind, sk)) if sk else None
            if twin is not None and twin.claim_id != current.claim_id:
                frozen = replace(
                    current,
                    status=ClaimStatus.VERIFIED,
                    resolved_value=twin.resolved_value,
                    evidence=twin.evidence,
                    resolver=twin.resolver,
                    source_hash=twin.source_hash,
                    updated_at=_now_iso(),
                )
                _claim_store.upsert(project_id, frozen, repo_root=repo_root)
                resolved.append(frozen)
                continue

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


def _process_planning_document(
    text: str,
    *,
    artifact_path: str,
    project_id: str,
    backend: Any,
    model: str | None,
    repo_root: Path,
    stage_label: str | None = None,
) -> tuple[str, list[Claim], GateReport]:
    """Planning-stage claim handling (spec 020 Part A): references-only + strip/smooth.

    In a planning stage (specify/clarify/plan/tasks) the claim layer MUST NOT
    fetch, fill, ground, or kick back on low-level claims (FR-002/003). References
    are verified by the separate reference path (F-18 / ``validate_artifact``) that
    runs BEFORE this function (FR-004), so here we only:

    - extract claims (to FIND any low-level assertion), and
    - replace each detected non-citation (low-level) claim's span with a
      higher-level statement via :func:`strip_and_smooth` (FR-002a),

    returning the smoothed text with NO ``[UNRESOLVED-CLAIM:]`` marker and an
    empty (non-blocking) GateReport. Nothing is resolved or registered — a
    planning low-level value is neither verified nor left asserted; it is removed.
    Never raises.
    """
    text = strip_claim_artifacts(text)
    try:
        new_claims = extract_claims(
            text, artifact_path=artifact_path, backend=backend,
            model=model, repo_root=repo_root, stage_label=stage_label,
        )
    except Exception as exc:
        logger.warning("claims.service: planning extraction failed (%s); no-op", exc)
        return text, [], GateReport()

    smoothed = text
    lowlevel = [c for c in new_claims if c.kind != ClaimKind.CITATION]
    for claim in lowlevel:
        span = claim.raw_text or ""
        if not span or span not in smoothed:
            continue
        try:
            replacement = strip_and_smooth(span, claim, backend=backend, model=model)
        except Exception as exc:  # never block a planning render on smoothing
            logger.warning("claims.service: strip/smooth failed for %s (%s)",
                           claim.claim_id, exc)
            continue
        if replacement != span:
            smoothed = smoothed.replace(span, replacement, 1)
    # spec 020 GUARANTEE: the LLM extractor's recall is non-deterministic, so a
    # final DETERMINISTIC pass removes any high-confidence empirical value (a
    # comma-grouped count, a percentage, a timed quantity) it missed — structural
    # numbers (versions, dates, indices, scope bounds) are preserved. Idempotent.
    try:
        smoothed = strip_empirical_values(smoothed)
    except Exception as exc:  # never block a planning render on the guarantee pass
        logger.warning("claims.service: deterministic empirical strip failed (%s)", exc)
    # No markers, no kickback, no resolution: planning never blocks on low-level.
    return smoothed, [], GateReport()


def process_document(
    text: str,
    *,
    artifact_path: str,
    project_id: str,
    backend: Any,
    model: str | None,
    repo_root: Path,
    stage_label: str | None = None,
) -> tuple[str, list[Claim], GateReport]:
    """Extract → register → substitute → resolve → render one document.

    Returns ``(rendered_text, claims, GateReport)``.

    ``stage_label`` (spec 020 FR-001) selects the regime: a *planning* stage
    (specify/clarify/plan/tasks — see :func:`claims.stage.is_planning_stage`)
    verifies references only and strips/smooths low-level claims (Part A); any
    other / ``None`` stage runs the full extract→resolve→render verification with
    the Part-B freeze. Defaulting to ``None`` preserves the prior behavior for
    every existing caller.

    Idempotency: if a claim with the same ``claim_id`` is already in the
    registry with status VERIFIED, it is reused without re-resolution.
    All other statuses (PENDING / NOT_ENOUGH_INFO / REFUTED / UNRESOLVABLE)
    are re-resolved so transient failures self-heal on the next round.

    Never raises — on extraction failure returns ``(text, [], GateReport())``.
    """
    if is_planning_stage(stage_label):
        return _process_planning_document(
            text, artifact_path=artifact_path, project_id=project_id,
            backend=backend, model=model, repo_root=repo_root,
            stage_label=stage_label,
        )

    # Step 0: Strip prior [UNRESOLVED-CLAIM:] markers so a re-run does NOT
    # re-extract its own output (idempotency). spec 020 FR-007: PRESERVE durable
    # {{claim:id}} placeholders — they carry a verified value in the canonical
    # stored form and must survive round-to-round (so the value is never baked
    # into prose and re-extracted as a new claim — SC-007).
    text = strip_claim_artifacts(text, preserve_pointers=True)

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
        # No NEW claims, but the doc may carry durable {{claim:id}} placeholders
        # from prior rounds (FR-007): keep those with a backing registered claim,
        # drop orphans, and re-render so placeholders stay placeholders.
        carried: dict[str, Claim] = {}
        for cid in pointer_ids(text):
            prior = _claim_store.get(project_id, cid, repo_root=repo_root)
            if prior is not None:
                carried[cid] = prior
        text = drop_orphan_pointers(text, set(carried))
        rendered, gate_report = render(text, carried, placeholder_verified=True)
        return rendered, [], gate_report

    # Step 2: Upsert each claim into the registry (dedup by claim_id), with a
    # subject-keyed VERIFIED reuse: a reviser REPHRASE yields a NEW claim_id for
    # the SAME fact (same (kind, subject_key)), which defeats the claim_id-keyed
    # reuse in resolve_registered_claims and re-resolves the fact from scratch
    # every round. If the registry already holds a VERIFIED claim with this
    # claim's (kind, subject_key), carry its verified value/evidence/source_hash
    # onto the new claim so the resolve step reuses it (FR-015). Value-identical:
    # resolution is by SUBJECT, so re-resolving would yield the same value — this
    # only skips the redundant work (and corrects a re-fabricated value for
    # free). Source-hash invalidation in resolve_registered_claims still applies,
    # so a changed underlying source re-resolves normally.
    verified_by_subject = _claim_store.load_verified_by_subject(
        project_id, repo_root=repo_root
    )
    for claim in new_claims:
        if _claim_store.get(project_id, claim.claim_id, repo_root=repo_root) is not None:
            continue
        sk = subject_key(claim)
        twin = verified_by_subject.get((claim.kind, sk)) if sk else None
        if twin is not None and twin.claim_id != claim.claim_id:
            claim = replace(
                claim,
                status=ClaimStatus.VERIFIED,
                resolved_value=twin.resolved_value,
                evidence=twin.evidence,
                resolver=twin.resolver,
                source_hash=twin.source_hash,
                updated_at=_now_iso(),
            )
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

    # Step 5: Render — keep VERIFIED claims as DURABLE placeholders in the canonical
    # stored form (FR-007); their value is substituted only in the rendered VIEW
    # (render_view) at review time + publish (FR-008).
    claims_by_id = {c.claim_id: c for c in resolved_claims}
    # Include claims referenced by durable placeholders carried over from prior
    # rounds: their prose is already a {{claim:id}} token, so they were NOT
    # re-extracted this round; load them from the registry so render keeps them as
    # placeholders rather than emitting an "unknown claim" marker.
    for cid in pointer_ids(text_with_pointers):
        if cid not in claims_by_id:
            prior = _claim_store.get(project_id, cid, repo_root=repo_root)
            if prior is not None:
                claims_by_id[cid] = prior
    # Drop orphan pointers (no backing registered claim) so they never render as a
    # spurious "unknown claim" marker — durable placeholders (with a claim) are kept.
    text_with_pointers = drop_orphan_pointers(text_with_pointers, set(claims_by_id))
    rendered_text, gate_report = render(
        text_with_pointers, claims_by_id, placeholder_verified=True
    )

    # Step 6 (T035): repair citations for filled claims so the rendered text
    # cites the authoritative fill source rather than a stale paper citation.
    # Import lazily to avoid circular imports (fill → claims → fill).
    try:
        from llmxive.fill.citation_repair import repair_citation
        from llmxive.fill.models import FillProvenance

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
            except Exception as exc:
                logger.debug(
                    "claims.service: citation repair skipped for %s: %s",
                    claim.claim_id, exc,
                )
    except ImportError:
        pass  # fill package not available; skip silently

    # Step 7 (spec 018 / canonical sweep): a verified fact is SUBJECT-keyed, so
    # EVERY mention of a verified subject is forced to its verified value —
    # closing the per-instance gap where one mention carries the verified value
    # (9988) while a rephrased mention still asserts the fabrication (27,635).
    # PURE STRENGTHENING: when there are no verified, sourced facts (or nothing
    # to correct), build returns {} and apply is a no-op → output is unchanged.
    try:
        from llmxive.claims.canonical import (
            apply_canonical_corrections,
            build_canonical_facts,
        )

        facts = build_canonical_facts(resolved_claims)
        if facts:
            rendered_text, _corrections = apply_canonical_corrections(
                rendered_text, facts
            )
            _persist_verified_facts(
                facts, artifact_path=artifact_path,
                project_id=project_id, repo_root=repo_root,
            )
    except Exception as exc:  # never crash a render on the trustworthiness sweep
        logger.warning("claims.service: canonical sweep skipped (%s)", exc)

    return rendered_text, resolved_claims, gate_report


def render_artifact_view(
    text: str, *, project_id: str, repo_root: Path
) -> str:
    """FR-008: the human/reviewer + published VIEW of a canonical artifact.

    Substitutes verified values for the durable ``{{claim:id}}`` placeholders the
    canonical stored form carries (FR-007), deterministically from the git-tracked
    ``state/claims/`` frozen store (FR-013). Used at review time (the artifact shown
    to the convergence panel) and for the final published artifact. The canonical
    stored form is unchanged; this is a pure read-time projection. No-op when the
    text carries no placeholders (e.g. a planning-stage artifact). Never raises.
    """
    from llmxive.claims.pointer import pointer_ids as _pids
    from llmxive.claims.pointer import render_view as _render_view

    try:
        ids = set(_pids(text))
        if not ids:
            return text
        by_id: dict[str, Claim] = {}
        for cid in ids:
            c = _claim_store.get(project_id, cid, repo_root=repo_root)
            if c is not None:
                by_id[cid] = c
        return _render_view(text, by_id)
    except Exception as exc:  # a view projection must never break a read
        logger.warning("claims.service: render_artifact_view failed (%s)", exc)
        return text


def _project_dir(artifact_path: str, project_id: str, repo_root: Path) -> Path | None:
    """Locate the project directory under ``repo_root`` for ``artifact_path``.

    ``artifact_path`` is conventionally ``projects/<project-slug>/...`` — we take
    the ``projects/<slug>`` prefix so the verified-fact memory lands beside the
    project's other ``.specify`` state. Falls back to a ``project_id`` match when
    the path does not start with ``projects/``. Returns None when no project
    directory can be determined.
    """
    parts = Path(artifact_path).parts
    if len(parts) >= 2 and parts[0] == "projects":
        return repo_root / "projects" / parts[1]
    projects_root = repo_root / "projects"
    if projects_root.is_dir():
        for child in projects_root.iterdir():
            if child.is_dir() and child.name.startswith(project_id):
                return child
    return None


def _persist_verified_facts(
    facts: dict[str, Any],
    *,
    artifact_path: str,
    project_id: str,
    repo_root: Path,
) -> None:
    """Best-effort: write the canonical verified facts to per-project memory.

    Target: ``projects/<id>/.specify/memory/verified_facts.yaml`` so later
    stages can read the authoritative subject→value map. Never raises — an IO
    failure must not break a render.
    """
    import yaml

    project_dir = _project_dir(artifact_path, project_id, repo_root)
    if project_dir is None:
        return
    out_path = project_dir / ".specify" / "memory" / "verified_facts.yaml"
    payload = {
        key: {
            "value": fact.value,
            "source_id": fact.source_id,
            "url": fact.url,
            "quote": fact.quote,
        }
        for key, fact in facts.items()
    }
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            yaml.safe_dump(payload, sort_keys=True), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("claims.service: verified_facts persist failed (%s)", exc)


__all__ = ["process_document", "render_artifact_view", "resolve_registered_claims"]
