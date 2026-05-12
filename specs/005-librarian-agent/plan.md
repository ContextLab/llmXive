# Implementation Plan: Librarian Agent + Phase 1 Re-Validation

**Branch**: `008-librarian-agent` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/005-librarian-agent/spec.md`

## Summary

Build a `librarian` agent that consolidates literature-search-and-citation-verification into a single canonical implementation, replacing three duplicated implementations (`agents/tools/lit_search.py`, `src/llmxive/agents/reference_validator.py`'s primary-source comparison, `tests/phase1/citation_resolver.py`'s Stage-1 mechanical resolver). Per Q1 the librarian uses Semantic Scholar API + arXiv API only; per Q2 it does adaptive verification (abstract for bulk + ≥10% PDF-sample audit); per Q3 it returns a partial list with `outcome: "exhausted"` when expansion can't reach 5 verified citations; per Q4 its `wall_clock_budget_seconds` is 600.

When the initial search returns fewer than 5 verified citations, the librarian triggers a multi-step expanded search: LLM-brainstorms 10-20 alternative phrasings ranked by relevance, iterates over them performing ≥10 distinct queries, and accumulates verified citations until ≥5 are found OR the term list is exhausted. The agent updates the calling project's `idea/<slug>.md` with a `## Search trail` subsection documenting expanded terms + per-term hit counts.

After the librarian is built, re-validate Phase 1's `flesh_out` and `research_question_validator` agents in place (per spec 004's iteration convention) on the carry-forward canonicals (PROJ-261-evaluating-the-impact-of-code-duplicatio, PROJ-262-predicting-molecular-dipole-moments-with). The re-runs use librarian-backed lit search; verdict shifts (if any) are documented as findings, not regressions.

Technical approach: implement the librarian as a Python module at `src/llmxive/agents/librarian.py` plus `agents/prompts/librarian.md` plus a registry entry. A single shared verification helper at `src/llmxive/librarian/verify.py` consolidates the title-token-overlap + URL-resolves + summary-grounding checks (replacing the duplicated logic). `flesh_out` and `reference_validator` are rewired to call the librarian via the agent runtime; `tests/phase1/citation_resolver.py` is preserved as a thin deprecation wrapper. Caching uses the disk-based JSON pattern documented in spec.md (`state/librarian-cache/<sha256>.json`). Real-call testing covers all 8 default fields by selecting one already-brainstormed project per field from the cron-driven cohort.

## Technical Context

**Language/Version**: Python 3.11 (matches `pyproject.toml`)
**Primary Dependencies**: existing `llmxive` package, `requests` (for HTTP HEAD + GET), `pypdf` or `pdfplumber` for PDF text extraction (used in the 10% PDF sample only — adds ~5MB to deps), Semantic Scholar's public API at `https://api.semanticscholar.org/`, arXiv API at `http://export.arxiv.org/api/query`. No new LLM library — librarian's brainstorm step uses the existing `chat_with_fallback` router.
**Storage**: filesystem — `state/librarian-cache/<sha256>.json` (cached results, committed to git for diagnostic reproducibility), `state/run-log/<YYYY-MM>/*.jsonl` (existing pattern), `projects/<id>/idea/<slug>.md` (Search trail subsection appended in place)
**Testing**: pytest with real-network HTTP calls to Semantic Scholar + arXiv (Constitution Principle III); per-field cross-domain test suite at `tests/phase2/test_librarian_cross_domain.py`; PDF-sample audit verified by spot-checking the `summary_grounded_pdf: true` flag on at least one citation per test invocation
**Target Platform**: macOS / Linux (developer workstation), Semantic Scholar + arXiv reachable, Dartmouth Chat backend reachable for the brainstorm-expansion step
**Project Type**: research-pipeline infrastructure consolidation (replaces 3 existing duplicate implementations + adds 1 new behavior — multi-step expansion)
**Performance Goals**: per-citation verification ≤2s on abstract path, ≤30s on PDF-sample path; total librarian invocation ≤1800s wall_clock_budget per FR-010 / Q4 (soft target, revised up from 600s post fix-ups #3/#4; not enforced — worst case: 1 LLM query-extraction + 5 parallel initial searches + 20 expanded searches + per-candidate LLM relevance-judge + 5+ PDF samples + retries)
**Constraints**: every search call goes through Semantic Scholar+arXiv only (Q1); no Google Scholar, no Dartmouth-web-search, no general-purpose web search; verification is deterministic for fixed cache state (FR-023 / SC-012); Phase 1 re-validation happens **in place** on the canonicals (no sibling-iter dirs, per spec 004's convention change)
**Scale/Scope**: 8 cross-domain test projects (one per default field) + 2 carry-forward canonicals re-fleshed + ~5-20 expanded search terms per invocation × ~20 invocations during testing = ~100-400 cached search results. Worst-case backend usage: 100-400 Semantic Scholar/arXiv calls + ~50 LLM brainstorm calls + ~10 PDF downloads. Well within free-tier quotas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` v1.0.0 names five non-negotiable principles. Each is evaluated below.

### I. Single Source of Truth (NON-NEGOTIABLE)

- **Compliance**: PASS. **This entire spec exists to satisfy Principle I**: it consolidates three duplicated lit-search/verification implementations into one canonical librarian. After implementation: `flesh_out`, `reference_validator`, `tests/phase1/citation_resolver.py`, and any future paper-side agent (`paper_writing`, `paper_implementer`) all call the librarian. The shared verification helper at `src/llmxive/librarian/verify.py` is the canonical home for title-token-overlap + URL-resolves + summary-grounding logic. New duplicate implementations are explicitly forbidden by FR-022.

### II. Verified Accuracy (NON-NEGOTIABLE)

- **Compliance**: PASS. The librarian is *itself* a Verified Accuracy mechanism: every returned citation has been verified against its primary source (URL resolves AND title-token-overlap AND summary-grounded). The PDF-sample (Q2) catches the worst hallucination cases. Per FR-016 the librarian fails loudly on any verification mismatch — no silent inclusion of unverified citations. The `summary_grounded_pdf: bool` flag in the JSON output makes the verification provenance audit-able.

### III. Robustness & Reliability (Real-World Testing)

- **Compliance**: PASS. All search calls go to real APIs (Semantic Scholar + arXiv); all PDF downloads are real HTTP GETs; all verification reads real fetched content. No mocks. The cross-domain test suite covers 8 fields, exercising the librarian against the actual cron-brainstormed projects (real idea bodies, real research questions). The induced-failure scenarios per SC-007 cover backend-unreachable, DOI-redirects-to-wrong-paper, and paywall edge cases.

### IV. Cost Effectiveness (Free-First)

- **Compliance**: PASS. Semantic Scholar API + arXiv API are both free + public. No paid web-search service introduced. Dartmouth Chat (also free per registry) handles the brainstorm-expansion step. Caching mitigates repeat costs. Worst-case per-test-invocation: ~25 free API calls + ~5 free PDF downloads + 1 free LLM brainstorm. Total spec budget across all testing: <500 free API calls, well under any rate-limit threshold.

### V. Fail Fast

- **Compliance**: PASS. Preflight checks before any librarian invocation: (a) `SEMANTIC_SCHOLAR_API_KEY` loadable via `llmxive.credentials.load_semantic_scholar_key()` (env var or credentials file) AND a real `/graph/v1/paper/search?query=test&limit=1` call returns 200 not 429 (proves the key works, not just that it exists); (b) arXiv API reachable (no key needed); (c) Dartmouth Chat credentials valid for the brainstorm-expansion step; (d) `state/librarian-cache/` directory writable. Failures surface within seconds. The 600s wall_clock_budget per Q4 caps run-away invocations. The expansion-exhausted path (Q3) is fail-fast: returns partial list immediately, doesn't retry indefinitely. Backend retry policy inherits the existing router (3 attempts on primary + 1 on each peer per backend), already verified during spec 004.

**Verdict**: All five principles satisfied. No Complexity Tracking entries needed. The spec actively *strengthens* alignment with Principle I (the primary motivation for this work).

## Project Structure

### Documentation (this feature)

```text
specs/005-librarian-agent/
├── plan.md              # This file
├── spec.md              # Feature specification (clarified)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── librarian-json-output.md       # Output JSON schema
│   ├── search-trail-md.md             # idea.md ## Search trail subsection contract
│   ├── cross-domain-coverage.md       # US4 per-field test contract
│   └── revalidation-runs.md           # US3 in-place re-fleshing procedure
├── checklists/
│   └── requirements.md   # Spec-quality checklist (already created + clarified)
├── carry-forward.yaml    # Output of US6 — produced during /speckit-implement
└── tasks.md              # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
# Production code (NEW, this spec)
src/llmxive/agents/
└── librarian.py                   # NEW — librarian agent class

src/llmxive/librarian/
├── __init__.py                    # NEW — package init
├── search.py                      # NEW — Semantic Scholar + arXiv search clients (Q1)
├── verify.py                      # NEW — canonical title-token-overlap + URL-resolves + summary-grounded checks
├── pdf_sample.py                  # NEW — PDF download + text extraction for ≥10% sample (Q2)
├── expand.py                      # NEW — LLM-driven multi-step term-expansion logic (Q3)
├── cache.py                       # NEW — sha256-keyed disk cache (state/librarian-cache/)
└── search_trail.py                # NEW — owns E6 (SearchTrail) Markdown writer; idempotent in-place insert/replace of `## Search trail` subsection in calling project's idea/<slug>.md per FR-005

agents/
├── prompts/
│   └── librarian.md               # NEW — librarian prompt
└── registry.yaml                  # MODIFIED — add librarian entry with 600s budget

# Production code (REWIRED, this spec)
src/llmxive/agents/
├── idea_lifecycle.py              # MODIFIED — flesh_out lit_search call → librarian invocation (line 173-177)
└── reference_validator.py         # MODIFIED — verification logic delegates to librarian/verify.py

agents/tools/
└── lit_search.py                  # DEPRECATED — banner + redirect to librarian (or DELETED if no callers remain)

# Test code (NEW, this spec)
tests/phase1/
└── citation_resolver.py           # MODIFIED — thin wrapper delegating to librarian/verify.py (or DEPRECATED with banner)

tests/phase2/
├── __init__.py                    # NEW
├── test_librarian_search.py       # NEW — Semantic Scholar + arXiv search unit tests
├── test_librarian_verify.py       # NEW — verification helper unit tests
├── test_librarian_expand.py       # NEW — multi-step expansion unit tests
├── test_librarian_pdf_sample.py   # NEW — PDF-sample audit unit tests
├── test_librarian_cache.py        # NEW — disk-cache TTL + invalidation tests
├── test_librarian_cross_domain.py # NEW — 8-field cross-domain coverage (US4)
└── test_librarian_revalidation.py # NEW — Phase 1 re-validation orchestration test (US3)

# Diagnostic outputs (NEW, this spec)
notes/2026-05-NN-spec-005-librarian-diagnostic.md    # FR-014 — the report itself

# Real-project artifacts (re-fleshed in place; per spec 004's convention)
projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/idea/<slug>.md  # MODIFIED — Search trail subsection added
projects/PROJ-262-predicting-molecular-dipole-moments-with/idea/<slug>.md  # MODIFIED — same
state/projects/PROJ-26{1,2}-*.yaml  # MODIFIED — state YAMLs reflect the re-validation iteration count
state/librarian-cache/*.json        # NEW — committed cache entries for reproducibility
state/run-log/2026-05/*.jsonl       # APPENDED — librarian + flesh_out + validator run-log entries
```

**Structure Decision**: Single-project layout (Option 1). The librarian is a substantial new sub-package (`src/llmxive/librarian/`) with 5 modules, but each module has a single tight responsibility. Three production-code rewirings (idea_lifecycle, reference_validator, citation_resolver) all delegate to the new librarian. New `tests/phase2/` directory mirrors spec 003's `tests/phase1/` for clarity. Note that `lit_search` currently lives at top-level `agents/tools/lit_search.py` (NOT under `src/llmxive/`) — see research.md Decision 1 for the deprecation strategy that handles this.

## Complexity Tracking

> No Constitution-Check violations to justify. Table omitted.

The librarian sub-package introduces 5 new modules + 1 new test directory. Each module is single-purpose (search.py = backend clients only; verify.py = verification helper only; etc.) and the cross-module API surface is small. The complexity is justified because:

1. The 5 modules replace ~5 redundant implementations across `agents/tools/lit_search.py`, `src/llmxive/agents/reference_validator.py`, and `tests/phase1/citation_resolver.py`. Net code count likely DECREASES once the rewirings land.
2. Splitting search/verify/sample/expand/cache into separate modules makes each independently testable (US1's contract test, US4's cross-domain test, etc.) without hitting all backends in every test.
3. The single shared verification helper (`verify.py`) is the entry point future paper-side agents will use — keeping it isolated makes that integration cleaner.

No alternative was rejected for being too complex; the alternative ("one giant librarian.py module") was rejected for being too monolithic + harder to test in isolation.
