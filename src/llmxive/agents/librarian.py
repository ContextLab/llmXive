"""Librarian agent (spec 005 / FR-001 / FR-010).

Single canonical literature-search-and-citation-verification agent. Wraps
the ``src/llmxive/librarian/`` sub-package (search + verify + pdf_sample
+ expand + cache + search_trail).

**Tool-style agent**: invoked directly by other agents (``flesh_out``,
``reference_validator``, future paper-side agents) via ``invoke()``,
NOT by the pipeline orchestrator's stage-routing. The librarian doesn't
own a project stage; it doesn't advance state. The base ``Agent.run()``
loop is a no-op for the librarian.

Per Q1 / Q2 / Q3 / Q4 clarifications:
  - Backends: Semantic Scholar Graph API + arXiv API only (Q1)
  - Verification: abstract for bulk + ≥10% PDF sample audit (Q2)
  - Expansion-exhausted: return partial list with ``outcome: "exhausted"`` (Q3)
  - Wall-clock budget: 1800s soft target (Q4 originally specified 600s; tripled
    to 1800s post fix-ups #3/#4 — the concept-decomposed multi-query search +
    looser LLM judge admit more candidates → more PDF samples; the budget is
    documented soft guidance, NOT enforced — see diagnostic § 6 P5-D09)

Per Constitution Principle I: this agent is the SINGLE source of truth
for lit search + verification. New duplicate implementations are
forbidden by FR-022.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import logging
import time
from pathlib import Path
from typing import Any

from llmxive.agents.base import Agent, AgentContext
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.librarian import cache as librarian_cache
from llmxive.librarian import query_extractor, relevance_judge, search_trail
from llmxive.librarian.expand import (
    DEFAULT_EXPANSION_CAP,
    DEFAULT_TARGET_N,
    ExpansionResult,
    expand_terms,
    iterate_until_target,
)
from llmxive.librarian.pdf_sample import (
    annotate_with_pdf_sample,
    audit_pdf_grounding,
    select_pdf_sample,
)
from llmxive.librarian.search import (
    ArxivClient,
    Candidate,
    SemanticScholarClient,
    merge_candidates,
)
from llmxive.librarian.verify import (
    VerificationFailure,
    VerifiedCitation,
    verify_citation,
)
from llmxive.types import AgentRegistryEntry

LIBRARIAN_SCHEMA_VERSION = "1.0.0"
DEFAULT_INITIAL_LIMIT = 10  # total candidate budget across the parallel decomposed queries
LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class LibrarianResult:
    """Top-level output of one librarian invocation (data-model.md E5)."""

    schema_version: str
    librarian_prompt_version: str
    term_input_raw: str
    term_input_normalized: str
    context: dict[str, Any]
    outcome: str  # success | success_after_expansion | exhausted | failed
    verified_citations: list[VerifiedCitation]
    verification_failures: list[VerificationFailure]
    expansion: ExpansionResult | None
    pdf_sample: dict[str, Any]
    started_at: str
    ended_at: str
    duration_seconds: float
    cache_status: str  # miss | hit | refreshed_after_ttl
    failure_reason: str | None = None
    relevance_judge: dict[str, Any] = dataclasses.field(default_factory=dict)
    extracted_queries: list[str] = dataclasses.field(default_factory=list)
    per_query_hit_count: dict[str, int] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the JSON shape documented in
        ``contracts/librarian-json-output.md``.
        """
        return {
            "schema_version": self.schema_version,
            "librarian_prompt_version": self.librarian_prompt_version,
            "term_input": {
                "raw": self.term_input_raw,
                "normalized": self.term_input_normalized,
            },
            "context": self.context,
            "outcome": self.outcome,
            "verified_citations": [_vc_to_dict(v) for v in self.verified_citations],
            "verification_failures": [_vf_to_dict(f) for f in self.verification_failures],
            "expansion": (_expansion_to_dict(self.expansion) if self.expansion else None),
            "pdf_sample": self.pdf_sample,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "cache_status": self.cache_status,
            "failure_reason": self.failure_reason,
            "relevance_judge": self.relevance_judge,
            "extracted_queries": self.extracted_queries,
            "per_query_hit_count": self.per_query_hit_count,
        }


class LibrarianAgent(Agent):
    """Wraps the librarian sub-package as a registry-aware agent.

    Use ``invoke()`` to run a search; ``build_messages()`` and
    ``handle_response()`` are no-ops for the base ``Agent`` contract
    (the librarian doesn't fit the single-LLM-call pattern).
    """

    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    # The base Agent class requires these — make them no-ops since the
    # librarian doesn't run through the orchestrator's stage-routing.
    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        return []

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        return []

    # The real entry point for callers.
    def invoke(
        self,
        term: str,
        *,
        field: str | None = None,
        idea_body_excerpt: str | None = None,
        target_n: int = DEFAULT_TARGET_N,
        idea_md_path: Path | None = None,
        repo_root: Path | None = None,
        no_cache: bool = False,
        ss_client: SemanticScholarClient | None = None,
        arxiv_client: ArxivClient | None = None,
        relevance_judge_disabled: bool = False,
    ) -> LibrarianResult:
        """Execute the full librarian pipeline.

        Steps (data-model.md E5 + research.md Decisions 2-6):
          1. Cache check (skip if ``no_cache=True``).
          2. Initial search: query Semantic Scholar + arXiv with the term;
             merge candidates; verify each.
          3. If verified count < target_n: trigger multi-step expansion
             (LLM brainstorm + iterate per ``expand.iterate_until_target``).
          4. PDF sample: audit ≥10% of verified citations against full PDF.
          5. Cache write (if not no_cache).
          6. If ``idea_md_path`` provided: write/replace ``## Search trail``
             subsection.
          7. Return LibrarianResult.
        """
        repo_root = repo_root or Path.cwd()
        started = _dt.datetime.now(_dt.UTC)
        t0 = time.monotonic()

        term_normalized = librarian_cache.normalize_term(term)
        prompt_ver = self.entry.prompt_version
        ckey = librarian_cache.cache_key(term_normalized, field, target_n, prompt_ver)

        # 1. Cache check.
        if not no_cache:
            cached = librarian_cache.get(repo_root, ckey, current_prompt_version=prompt_ver)
            if cached is not None:
                # Cache hit — re-hydrate the LibrarianResult so callers
                # (including the test suite) can call .to_dict() and see
                # the same shape they'd see on a cache miss. This is the
                # correctness guarantee SC-012 requires (deterministic
                # results across cache states).
                cached_result = _result_from_dict(cached)
                # Search trail must still be written on cache hit so callers
                # like flesh_out get the subsection regardless of cache state
                # (SC-012 + FR-007).
                if idea_md_path is not None and idea_md_path.exists():
                    search_trail.write_search_trail(
                        idea_md_path,
                        original_term=term,
                        outcome=cached_result.outcome,
                        verified_citations=cached_result.verified_citations,
                        expanded_terms_ranked=(
                            cached_result.expansion.expanded_terms_ranked
                            if cached_result.expansion else ()
                        ),
                        per_term_hit_count=(
                            cached_result.expansion.per_term_hit_count
                            if cached_result.expansion else {}
                        ),
                        librarian_prompt_version=prompt_ver,
                        generated_at=_dt.datetime.now(_dt.UTC),
                    )
                return cached_result

        # 2. Initial search — concept-decomposed (spec 005 fix-up #3).
        # Instead of one sentence-shaped query, ask the LLM to extract
        # 5 short keyword queries (with synonym variants for vocabulary
        # clusters that diverge between the question and the literature),
        # then run all in parallel and union the candidate sets. This
        # addresses the three retrieval failure modes documented in the
        # diagnostic report § 6 P5-D11: vocabulary mismatch, sentence-
        # shaped queries, and missing concept decomposition.
        ss_client = ss_client if ss_client is not None else SemanticScholarClient()
        arxiv_client = arxiv_client or ArxivClient()

        try:
            extracted_queries = query_extractor.extract_queries(
                term,
                field=field,
                model=self.entry.default_model,
                default_backend=self.entry.default_backend.value,
                fallback_backends=[b.value for b in self.entry.fallback_backends],
            )
        except Exception as exc:
            extracted_queries = []
            LOGGER.warning("[librarian] query extraction failed: %s", exc)
        # Always include the raw term as a baseline so the cache key
        # remains semantically tied to the user's actual research
        # question and so a backend failure on the extractor doesn't
        # leave the librarian silent.
        all_queries: list[str] = [term]
        for q in extracted_queries:
            if q not in all_queries:
                all_queries.append(q)

        per_query_limit = max(3, DEFAULT_INITIAL_LIMIT // max(1, len(all_queries) - 1) or 1)
        merged_pointers: set[str] = set()
        candidates: list[Candidate] = []
        per_query_hit_count: dict[str, int] = {}
        for q in all_queries:
            ss_results: list[Candidate] = []
            if ss_client.has_key:
                try:
                    ss_results = ss_client.search_papers(q, limit=per_query_limit)
                except Exception:
                    ss_results = []
            try:
                ax_results = arxiv_client.search(q, max_results=per_query_limit)
            except Exception:
                ax_results = []
            new_for_q = 0
            for c in merge_candidates(ss_results, ax_results):
                if c.primary_pointer in merged_pointers:
                    continue
                merged_pointers.add(c.primary_pointer)
                candidates.append(c)
                new_for_q += 1
            per_query_hit_count[q] = new_for_q

        verified, failures = _verify_each(candidates, query=term)

        expansion: ExpansionResult | None = None
        outcome = "success" if len(verified) >= target_n else "exhausted"

        # 3. Multi-step expansion if under-target.
        if len(verified) < target_n:
            try:
                expanded = expand_terms(
                    term,
                    field=field,
                    idea_body_excerpt=idea_body_excerpt,
                    n=DEFAULT_EXPANSION_CAP,
                    model=self.entry.default_model,
                    default_backend=self.entry.default_backend.value,
                    fallback_backends=[b.value for b in self.entry.fallback_backends],
                )
                expansion = iterate_until_target(
                    term,
                    expanded,
                    target_n=target_n - len(verified),
                    ss_client=ss_client if ss_client.has_key else None,
                    arxiv_client=arxiv_client,
                )
                # Merge expansion results into the running verified list.
                already = {v.primary_pointer for v in verified}
                for v in expansion.accumulated_verified:
                    if v.primary_pointer not in already:
                        verified.append(v)
                        already.add(v.primary_pointer)
                outcome = (
                    "success_after_expansion"
                    if len(verified) >= target_n
                    else "exhausted"
                )
            except Exception:
                # Expansion brainstorm itself failed (LLM unreachable, etc.).
                # Fall through with whatever initial verified we have; note
                # the failure on the result.
                expansion = None
                outcome = "exhausted" if not verified else outcome

        # 3.5. LLM-based topical-relevance judge (spec 005 fix-up #2).
        # Filters out field-adjacent-but-off-topic citations that
        # passed the cheaper token-overlap gate. Fail-open on backend
        # errors per relevance_judge.py docstring.
        #
        # Marginal-fallback rule: if the judge rejects EVERY candidate
        # (i.e. strict-verified list is empty after pruning), admit
        # the rejected ones back as topically_marginal=True so the
        # librarian doesn't go silent. The Search trail flags them
        # explicitly so downstream agents can decide how to weight
        # them. This addresses the case where the search backend
        # genuinely has no on-topic results — better to surface
        # marginal evidence with a label than to lie by omission.
        judge_rejected_count = 0
        judge_rejections: list[dict[str, Any]] = []
        marginal_fallback_used = False
        if verified and not relevance_judge_disabled:
            try:
                kept, rejected = relevance_judge.filter_by_relevance(
                    verified,
                    query=term,
                    model=self.entry.default_model,
                    default_backend=self.entry.default_backend.value,
                    fallback_backends=[b.value for b in self.entry.fallback_backends],
                )
                if rejected:
                    judge_rejected_count = len(rejected)
                    for c, v in rejected:
                        judge_rejections.append({
                            "primary_pointer": c.primary_pointer,
                            "title": (c.bibliographic_info or {}).get("title", ""),
                            "rationale": v.rationale,
                        })
                if kept:
                    verified = kept
                else:
                    # All candidates rejected — fall back to the rejected
                    # set, flagged as marginal. Mark each citation's
                    # bibliographic_info with topically_marginal=True so
                    # the Search trail / downstream agents can label them.
                    marginal_fallback_used = True
                    flagged: list[VerifiedCitation] = []
                    for c, _v in rejected:
                        new_bib = dict(c.bibliographic_info or {})
                        new_bib["topically_marginal"] = True
                        flagged.append(
                            dataclasses.replace(c, bibliographic_info=new_bib)
                        )
                    verified = flagged
                # Re-evaluate outcome after the judge prunes.
                if outcome == "success" and len(verified) < target_n:
                    outcome = "exhausted"
                elif outcome == "success_after_expansion" and len(verified) < target_n:
                    outcome = "exhausted"
            except Exception:
                pass

        # 4. PDF sample.
        pdf_sample_target = 0
        sampled_pointers: list[str] = []
        if verified:
            sample = select_pdf_sample(verified, sample_rate=0.10)
            pdf_sample_target = max(1, len(sample))
            audit_results = [audit_pdf_grounding(c) for c in sample]
            verified = annotate_with_pdf_sample(verified, audit_results)
            sampled_pointers = [c.primary_pointer for c in sample]

        # If we have nothing — neither verified nor failures — the run
        # outright failed (both backends unreachable / all candidates
        # rejected for reasons we don't surface here).
        if not verified and not failures:
            outcome = "failed"

        ended = _dt.datetime.now(_dt.UTC)
        result = LibrarianResult(
            schema_version=LIBRARIAN_SCHEMA_VERSION,
            librarian_prompt_version=prompt_ver,
            term_input_raw=term,
            term_input_normalized=term_normalized,
            context={
                "field": field,
                "idea_body_excerpt": idea_body_excerpt,
                "target_n": target_n,
            },
            outcome=outcome,
            verified_citations=verified,
            verification_failures=failures,
            expansion=expansion,
            pdf_sample={
                "sampled_count": len(sampled_pointers),
                "sample_size_target": pdf_sample_target,
                "sampled_pointers": sampled_pointers,
            },
            started_at=started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ended_at=ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
            duration_seconds=round(time.monotonic() - t0, 3),
            cache_status="miss",
            failure_reason=None if outcome != "failed" else "all backends returned no verifiable candidates",
            relevance_judge={
                "enabled": not relevance_judge_disabled,
                "rejected_count": judge_rejected_count,
                "rejections": judge_rejections,
                "marginal_fallback_used": marginal_fallback_used,
            },
            extracted_queries=extracted_queries,
            per_query_hit_count=per_query_hit_count,
        )

        # 5. Cache write.
        if not no_cache and outcome != "failed":
            librarian_cache.set(
                repo_root,
                ckey,
                term_normalized=term_normalized,
                field=field,
                target_n=target_n,
                prompt_version=prompt_ver,
                result=result.to_dict(),
            )

        # 6. Search trail subsection.
        if idea_md_path is not None and idea_md_path.exists():
            search_trail.write_search_trail(
                idea_md_path,
                original_term=term,
                outcome=outcome,
                verified_citations=verified,
                expanded_terms_ranked=expansion.expanded_terms_ranked if expansion else (),
                per_term_hit_count=expansion.per_term_hit_count if expansion else {},
                librarian_prompt_version=prompt_ver,
                generated_at=ended,
            )

        return result


# --- (de)serialization helpers --------------------------------------------


def _vc_to_dict(v: VerifiedCitation) -> dict[str, Any]:
    return {
        "primary_pointer": v.primary_pointer,
        "bibliographic_info": v.bibliographic_info,
        "summary": v.summary,
        "summary_grounded_pdf": v.summary_grounded_pdf,
        "verification_log": dataclasses.asdict(v.verification_log),
    }


def _vf_to_dict(f: VerificationFailure) -> dict[str, Any]:
    return {
        "candidate": dataclasses.asdict(f.candidate),
        "reason": f.reason,
        "details": f.details,
        "failed_at": f.failed_at,
    }


def _expansion_to_dict(e: ExpansionResult) -> dict[str, Any]:
    # accumulated_verified is intentionally omitted here — the
    # caller-facing JSON merges it into top-level verified_citations.
    return {
        "original_term": "",  # set by caller; placeholder
        "expanded_terms_ranked": [list(pair) for pair in e.expanded_terms_ranked],
        "per_term_hit_count": e.per_term_hit_count,
        "total_queries_issued": e.total_queries_issued,
    }


def _result_from_dict(d: dict[str, Any]) -> LibrarianResult:
    """Re-hydrate a LibrarianResult from a cached JSON dict (cache-hit path).

    Critical correctness guarantee (SC-012 / FR-023): the rehydrated result
    MUST .to_dict() to a structure isomorphic to a fresh-miss result.
    """
    from llmxive.librarian.search import Candidate
    from llmxive.librarian.verify import VerificationLog

    verified: list[VerifiedCitation] = []
    for v in d.get("verified_citations", []) or []:
        log_d = v.get("verification_log") or {}
        verified.append(
            VerifiedCitation(
                primary_pointer=v.get("primary_pointer", ""),
                bibliographic_info=v.get("bibliographic_info", {}),
                summary=v.get("summary", ""),
                summary_grounded_pdf=v.get("summary_grounded_pdf"),
                verification_log=VerificationLog(
                    url_resolves=log_d.get("url_resolves", False),
                    final_url=log_d.get("final_url", ""),
                    redirect_chain=log_d.get("redirect_chain") or [],
                    http_status=log_d.get("http_status"),
                    title_token_overlap_score=log_d.get("title_token_overlap_score", 0.0),
                    summary_grounding_score=log_d.get("summary_grounding_score", 0.0),
                    pdf_sample_score=log_d.get("pdf_sample_score"),
                    verified_at=log_d.get("verified_at", ""),
                ),
            )
        )

    failures: list[VerificationFailure] = []
    for f in d.get("verification_failures", []) or []:
        cand_d = f.get("candidate") or {}
        failures.append(
            VerificationFailure(
                candidate=Candidate(
                    backend=cand_d.get("backend", ""),
                    primary_pointer=cand_d.get("primary_pointer", ""),
                    claimed_title=cand_d.get("claimed_title", ""),
                    claimed_authors=cand_d.get("claimed_authors") or [],
                    claimed_year=cand_d.get("claimed_year"),
                    claimed_venue=cand_d.get("claimed_venue"),
                    claimed_abstract=cand_d.get("claimed_abstract"),
                ),
                reason=f.get("reason", "url_not_resolves"),
                details=f.get("details", ""),
                failed_at=f.get("failed_at", ""),
            )
        )

    return LibrarianResult(
        schema_version=d.get("schema_version", LIBRARIAN_SCHEMA_VERSION),
        librarian_prompt_version=d.get("librarian_prompt_version", "1.0.0"),
        term_input_raw=d.get("term_input", {}).get("raw", ""),
        term_input_normalized=d.get("term_input", {}).get("normalized", ""),
        context=d.get("context", {}),
        outcome=d.get("outcome", "failed"),
        verified_citations=verified,
        verification_failures=failures,
        expansion=None,  # expansion details persist via the dict form below
        pdf_sample=d.get("pdf_sample", {}),
        started_at=d.get("started_at", ""),
        ended_at=d.get("ended_at", ""),
        duration_seconds=d.get("duration_seconds", 0.0),
        cache_status="hit",
        failure_reason=d.get("failure_reason"),
        relevance_judge=d.get("relevance_judge", {}),
        extracted_queries=list(d.get("extracted_queries", []) or []),
        per_query_hit_count=dict(d.get("per_query_hit_count", {}) or {}),
    )


def _verify_each(
    candidates: list[Candidate],
    *,
    query: str | None = None,
) -> tuple[list[VerifiedCitation], list[VerificationFailure]]:
    """Run verify_citation across all candidates; partition into verified
    + failures.

    ``query``: the user's search term, threaded through to enforce the
    topical-relevance gate (spec 005 fix; SC-001 + FR-003).
    """
    verified: list[VerifiedCitation] = []
    failures: list[VerificationFailure] = []
    for c in candidates:
        result = verify_citation(c, summary=c.claimed_abstract or "", query=query)
        if isinstance(result, VerifiedCitation):
            verified.append(result)
        else:
            failures.append(result)
    return verified, failures


__all__ = [
    "LIBRARIAN_SCHEMA_VERSION",
    "LibrarianAgent",
    "LibrarianResult",
]
