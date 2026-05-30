"""Orchestrator: cache -> classify -> resolve -> retrieve -> assess -> decide."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from llmxive.agents.grounding_guard import CitedClaim, GroundingVerdict
from llmxive.grounding import cache
from llmxive.grounding.entailment import Verdict, assess
from llmxive.grounding.full_text import RetrievedDoc, retrieve

logger = logging.getLogger(__name__)


def decide(doc: RetrievedDoc, verdict: Verdict) -> tuple[bool, str]:
    """Apply the maintainer-confirmed policy to a retrieval + entailment result."""
    if verdict.status == "grounded":
        return True, ""
    if verdict.status == "contradicted":
        return False, f"cited source contradicts the claim ({verdict.note or verdict.evidence})"[:300]
    # not_found
    if doc.full_text:
        return False, "claim not found in the cited source's full text"
    return False, "claim not found in the cited source's abstract (full text unavailable)"


def ground_cited_claim(claim: CitedClaim, *, backend: Any, model: str | None,
                       repo_root: Path) -> GroundingVerdict:
    """Full-text grounding of one source-attributed claim."""
    kind, value = claim.source_kind, claim.source_value
    if kind is None or value is None:
        return GroundingVerdict(
            claim=claim, ok=False,
            reason="cited source is free-text only (no resolvable DOI/arXiv/URL); cannot substantiate",
        )
    source_id = f"{kind.value}:{value}"

    cached = cache.get_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                               number=claim.number)
    if cached is not None:
        return GroundingVerdict(claim=claim, ok=bool(cached["ok"]), reason=cached.get("reason", ""))

    ft = cache.get_fulltext(repo_root, kind.value, value)
    if ft is not None:
        doc = RetrievedDoc(kind.value, value, ft.get("tier"), ft.get("full_text"),
                           ft.get("abstract"), ft.get("title"), ft.get("final_url", ""))
    else:
        doc = retrieve(kind.value, value)
        cache.put_fulltext(repo_root, kind.value, value, {
            "tier": doc.tier, "full_text": doc.full_text, "abstract": doc.abstract,
            "title": doc.title, "final_url": doc.final_url})

    if not doc.readable:
        verdict_obj = GroundingVerdict(
            claim=claim, ok=False,
            reason=f"cited source unreadable ({doc.error or 'no open-access text'}); cannot substantiate",
        )
        cache.put_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                          number=claim.number,
                          verdict={"status": "not_found", "ok": False, "reason": verdict_obj.reason})
        return verdict_obj

    verdict = assess(claim.claim_text, doc, backend=backend, model=model, repo_root=repo_root)
    ok, reason = decide(doc, verdict)
    cache.put_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                      number=claim.number,
                      verdict={"status": verdict.status, "ok": ok, "reason": reason})
    return GroundingVerdict(claim=claim, ok=ok, reason=reason)
