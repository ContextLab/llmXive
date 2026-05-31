"""LLM-based topical-relevance judge (spec 005 fix-up #2).

The earlier token-overlap relevance gate (spec 005 P5-D08) caught
gross stop-token false positives but is **field-level**, not
topic-level: a query about "GNN dipole-moment prediction" still
admits an unrelated "GNN social-influence prediction" paper because
they share the bag-of-words {graph, neural, network, prediction}.

This module adds a *semantic* gate: for each candidate that survives
the existing URL + title + summary + token-overlap chain, ask an LLM
"is this paper actually about the user's research question?" The
judge returns yes/no + a short justification. Only `yes` candidates
flow through to the final verified list.

Design notes:
  - One LLM call per candidate (target_n is small, usually 5-10)
  - Hard timeout per call; on backend failure the candidate is
    admitted (fail-open — we already passed the cheaper checks, and a
    flaky LLM shouldn't drop legitimate work)
  - Caches the verdict in the per-citation log so cache-hit replays
    don't repeat the call
  - Post-filter, NOT pre-filter: the order of checks is intentionally
    cheap-to-expensive (URL HEAD < token-overlap < HTTP fetch <
    summary-grounding < LLM judge)
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Sequence

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback
from llmxive.librarian.verify import VerifiedCitation

LOGGER = logging.getLogger(__name__)

_JUDGE_SYSTEM_PROMPT = """\
You are a research-librarian relevance judge for a literature search.
The user asked a research question and the search engine returned a
candidate paper. Decide whether the paper would belong in a literature
review for the user's question.

You are evaluating for INCLUSION in a related-work / literature-review
section, NOT for being a paper that already answers the user's exact
question. The user is doing NEW research on this question — they need
the canonical prior work that a reviewer would expect to see cited.

ACCEPT (VERDICT: YES) if ANY of these hold:

  (a) Same-mechanism evidence: the paper measures the same biological
      pathway, physical observable, algorithmic property, social
      construct, or causal mechanism the user is asking about — even
      if it uses different terminology, a different population, a
      different methodology, or studies only one variable from the
      user's question rather than the full correlation.

  (b) Independent-or-dependent variable on the same domain: the paper
      measures at least ONE of the user's independent OR dependent
      variables on the user's domain (data type / population / system).
      Example: for "how does code-clone density correlate with LLM
      perplexity", a paper that measures perplexity-as-a-function-of-
      duplication on code corpora is YES, even if it doesn't compute
      "clone density" as a metric — it measures the underlying
      mechanism in canonical alt-vocabulary (deduplication,
      memorization, contamination).

  (c) Empirical baseline: the paper establishes the empirical baseline
      for the quantity under study (e.g., for "planned vs achieved
      power in preregistered studies", a paper documenting median
      achieved power across 10,000 published studies is YES — that's
      the baseline against which preregistration would be evaluated).

  (d) Foundational methodology / canonical reference: the paper is the
      foundational methods paper that anyone writing about the user's
      question would cite for the technique or framework being applied
      (e.g., Gilmer 2017 "Neural Message Passing for Quantum Chemistry"
      for any GNN-molecular-property question; Watts & Strogatz 1998
      for any small-world-network question).

  (e) Empirical-population canonical study: the paper studies the
      empirical population the question abstractly refers to. Example:
      for "sensory deprivation rs-fMRI modularity", a study of rs-fMRI
      in early-deaf or congenitally-blind humans is YES — those ARE
      the canonical sensory-deprivation populations the question is
      about, even if the paper doesn't use the phrase "sensory
      deprivation".

  (f) Cross-vocabulary alt-cluster: the paper is in the canonical
      alternative-vocabulary cluster for the user's question (e.g.,
      "deduplication / memorization / contamination" for "code
      duplication"; "homophily / heterophily" for "graph topology in
      GNNs"; "Type II error / sample size justification" for
      "statistical power").

REJECT (VERDICT: NO) only if:

  - Distinct construct sharing only homonym keywords (e.g., "intraocular
    lens power" for "statistical power"; "social network" for
    "graph neural network"; "small-world architecture wiring" for
    "small-world graph topology as input data").

  - Off-domain entirely: an astrophysics paper for a gut-microbiome
    question; a social-influence-on-Facebook paper for a
    code-duplication question.

  - The paper has no measurable connection to the user's mechanism,
    domain, variables, or empirical setting.

CRITICAL: a paper does NOT need to address the FULL correlation or
the FULL triple-intersection in the user's question to count. Lit-
review references are individually partial — a review SECTION uses
many partial-match papers to triangulate the gap. If the paper
satisfies any one of (a)-(f), accept it.

Return your verdict as the FIRST line of your response in this exact
format:

VERDICT: YES   (or)   VERDICT: NO

Then on subsequent lines, give a 1-2 sentence justification citing
which acceptance category (a-f) applies, or which rejection rule
applies.
"""


@dataclasses.dataclass(frozen=True)
class JudgeVerdict:
    """One judge call result."""
    relevant: bool
    rationale: str
    backend_error: str | None = None  # populated only if backend failed


def judge_one(
    *,
    query: str,
    candidate_title: str,
    candidate_abstract: str,
    model: str = "qwen.qwen3.5-122b",
    default_backend: str = "dartmouth",
    fallback_backends: Sequence[str] = ("local",),
) -> JudgeVerdict:
    """Judge a single candidate's relevance to the user's query.

    Fail-open on backend errors: returns relevant=True with a
    `backend_error` annotation. Reasoning: the candidate already
    passed the cheaper URL + title + summary + token-overlap checks,
    so we'd rather admit it with a flag than drop it because an LLM
    backend was momentarily unreachable.
    """
    user_payload = (
        f"# User's research question\n\n{query.strip()}\n\n"
        f"# Candidate paper\n\n"
        f"**Title**: {candidate_title.strip()}\n\n"
        f"**Abstract**: {candidate_abstract.strip() or '(no abstract available)'}\n\n"
        f"# Task\n\n"
        f"Does this paper directly address the user's specific research "
        f"question? Apply the rules in the system prompt strictly."
    )
    try:
        response = chat_with_fallback(
            [
                ChatMessage(role="system", content=_JUDGE_SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_payload),
            ],
            default_backend=default_backend,
            fallback_backends=list(fallback_backends),
            model=model,
        )
    except Exception as exc:
        LOGGER.warning("[relevance-judge] backend failure on %r: %s", candidate_title[:50], exc)
        return JudgeVerdict(
            relevant=True,
            rationale=f"(judge unreachable: {type(exc).__name__})",
            backend_error=str(exc),
        )

    return _parse_verdict(response.text)


def _parse_verdict(text: str) -> JudgeVerdict:
    """Parse the judge's free-form text. Tolerates malformed output by
    falling back to a yes/no keyword scan; defaults to relevant=True
    (fail-open) if the response is genuinely uninterpretable.
    """
    if not text or not text.strip():
        return JudgeVerdict(relevant=True, rationale="(empty judge response — fail-open)")
    cleaned = text.strip()
    first_line = cleaned.splitlines()[0].strip().upper()
    rest = "\n".join(cleaned.splitlines()[1:]).strip() or first_line
    if first_line.startswith("VERDICT: YES") or first_line == "YES":
        return JudgeVerdict(relevant=True, rationale=rest[:500])
    if first_line.startswith("VERDICT: NO") or first_line == "NO":
        return JudgeVerdict(relevant=False, rationale=rest[:500])
    # Soft fallback: scan first 200 chars for unambiguous yes/no.
    head = cleaned[:200].lower()
    if "verdict: no" in head or head.startswith("no,") or "answer: no" in head:
        return JudgeVerdict(relevant=False, rationale=cleaned[:500])
    if "verdict: yes" in head or head.startswith("yes,") or "answer: yes" in head:
        return JudgeVerdict(relevant=True, rationale=cleaned[:500])
    # Genuinely uninterpretable — fail-open with annotation.
    return JudgeVerdict(
        relevant=True,
        rationale=f"(unparseable judge response, fail-open) {cleaned[:200]}",
    )


def filter_by_relevance(
    citations: list[VerifiedCitation],
    *,
    query: str,
    model: str = "qwen.qwen3.5-122b",
    default_backend: str = "dartmouth",
    fallback_backends: Sequence[str] = ("local",),
) -> tuple[list[VerifiedCitation], list[tuple[VerifiedCitation, JudgeVerdict]]]:
    """Apply the relevance judge to each VerifiedCitation; return
    ``(kept, rejected)`` where rejected items carry the judge's
    rationale for the diagnostic report's audit trail.
    """
    if not query or not citations:
        return list(citations), []

    kept: list[VerifiedCitation] = []
    rejected: list[tuple[VerifiedCitation, JudgeVerdict]] = []
    for c in citations:
        title = (c.bibliographic_info.get("title") or "").strip()
        # Prefer the librarian's grounded summary; fall back to nothing.
        abstract = (c.summary or "").strip()
        verdict = judge_one(
            query=query,
            candidate_title=title,
            candidate_abstract=abstract,
            model=model,
            default_backend=default_backend,
            fallback_backends=fallback_backends,
        )
        if verdict.relevant:
            kept.append(c)
        else:
            rejected.append((c, verdict))
    return kept, rejected


__all__ = [
    "JudgeVerdict",
    "filter_by_relevance",
    "judge_one",
]
