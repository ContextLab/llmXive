"""Orchestrator: cache -> classify -> resolve -> retrieve -> assess -> decide."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from llmxive.agents.grounding_guard import (
    CitedClaim,
    GroundingVerdict,
    number_appears_in,
)
from llmxive.grounding import cache
from llmxive.grounding.entailment import Verdict, assess
from llmxive.grounding.full_text import RetrievedDoc, retrieve

logger = logging.getLogger(__name__)


def number_substantiated(number: str | None, doc_text: str | None) -> bool:
    """Deterministic number gate (design §5, defense-in-depth).

    When a cited claim hinges on a NUMBER, that exact number (or an
    obviously-equivalent form) MUST literally appear in the retrieved source
    text — otherwise the claim is NOT grounded even if the LLM entailment said
    ``grounded``. This guards against an LLM false-positive on a fabricated
    figure. Returns ``True`` when there is no number to check (gate not
    applicable) or when the number is present; ``False`` only when a non-empty
    number is absent from the (possibly empty) source text.
    """
    if not number:
        return True
    return number_appears_in(number, doc_text or "")


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
        # Only cache READABLE sources. An unreadable doc (transient retrieval
        # failure / paywall hiccup) is NOT cached so it self-heals on the next
        # round instead of being stuck flagged for the 90d full-text TTL.
        if doc.readable:
            cache.put_fulltext(repo_root, kind.value, value, {
                "tier": doc.tier, "full_text": doc.full_text, "abstract": doc.abstract,
                "title": doc.title, "final_url": doc.final_url})

    if not doc.readable:
        # Do NOT cache the verdict either — a transient retrieval failure must
        # self-heal, not be pinned to a flag for the verdict TTL.
        return GroundingVerdict(
            claim=claim, ok=False,
            reason=f"cited source unreadable ({doc.error or 'no open-access text'}); cannot substantiate",
        )

    verdict = assess(claim.claim_text, doc, backend=backend, model=model, repo_root=repo_root)
    ok, reason = decide(doc, verdict)
    status = verdict.status

    # Deterministic number gate (design §5): even when the LLM said ``grounded``,
    # a NUMBER-bearing claim is only grounded if that number literally appears in
    # the retrieved source text. Override an LLM false-positive to a flag.
    if ok and claim.number and not number_substantiated(
        claim.number, doc.full_text or doc.abstract or ""
    ):
        ok = False
        reason = f"cited source does not contain the claimed number {claim.number}"
        status = "not_found"

    cache.put_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                      number=claim.number,
                      verdict={"status": status, "ok": ok, "reason": reason})
    return GroundingVerdict(claim=claim, ok=ok, reason=reason)
