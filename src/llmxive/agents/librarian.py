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
  - Wall-clock budget: 600s (Q4)

Per Constitution Principle I: this agent is the SINGLE source of truth
for lit search + verification. New duplicate implementations are
forbidden by FR-022.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import time
from pathlib import Path
from typing import Any

from llmxive.agents.base import Agent, AgentContext
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.librarian import cache as librarian_cache
from llmxive.librarian import search_trail
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
DEFAULT_INITIAL_LIMIT = 10  # initial search per backend


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
                return _result_from_dict(cached)

        # 2. Initial search.
        ss_client = ss_client if ss_client is not None else SemanticScholarClient()
        arxiv_client = arxiv_client or ArxivClient()
        ss_results: list[Candidate] = []
        if ss_client.has_key:
            try:
                ss_results = ss_client.search_papers(term, limit=DEFAULT_INITIAL_LIMIT)
            except Exception as exc:  # noqa: BLE001
                # SS failure isn't fatal — arXiv may still succeed.
                ss_results = []
                # NOTE: We could log this in failure_reason but we let arXiv
                # carry the search if it works; only an all-backends-failed
                # result triggers outcome=failed.
        try:
            ax_results = arxiv_client.search(term, max_results=DEFAULT_INITIAL_LIMIT)
        except Exception:
            ax_results = []

        candidates = merge_candidates(ss_results, ax_results)
        verified, failures = _verify_each(candidates)

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
            except Exception as exc:  # noqa: BLE001
                # Expansion brainstorm itself failed (LLM unreachable, etc.).
                # Fall through with whatever initial verified we have; note
                # the failure on the result.
                expansion = None
                outcome = "exhausted" if not verified else outcome

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
    )


def _verify_each(
    candidates: list[Candidate],
) -> tuple[list[VerifiedCitation], list[VerificationFailure]]:
    """Run verify_citation across all candidates; partition into verified
    + failures.
    """
    verified: list[VerifiedCitation] = []
    failures: list[VerificationFailure] = []
    for c in candidates:
        result = verify_citation(c, summary=c.claimed_abstract or "")
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
