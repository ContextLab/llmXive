# Implementation Plan: Authoritative-Fill / Claim Auto-Correction

**Branch**: `017-claim-auto-correction` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/017-claim-auto-correction/spec.md`

## Summary

Add a **fill/correct** step on top of spec 016's check-only external resolvers. When an external claim resolves to `not_enough_info`/`refuted` (the model's value can't be verified as written), the layer **searches authoritative source channels for the claim's subject → fetches a resolvable source → extracts the candidate value → verifies that value is literally present in the fetched text → sets the claim's `resolved_value` + provenance → repairs the surrounding citation to the authoritative source**. A fabricated value (27,635) is replaced by a sourced one (9,988, cited to OEIS A002863), or the claim stays blocked when no authoritative value is found. The filled value can NEVER come from model memory — only from text actually fetched from a resolvable source (reusing spec 016's deterministic presence gate). v1 covers **numeric + entity/definitional** claims; magnitude/relational are a fast-follow. Channels: librarian paper search + **OEIS + Wikipedia + Wikidata** + **theorem search** (math claims). On a source conflict, a fixed channel-authority order (curated reference > paper) decides, and the disagreement is recorded in provenance.

## Technical Context

**Language/Version**: Python 3.11 (repo standard)
**Primary Dependencies**: existing `llmxive` — `claims/resolve.py` (the NEI/REFUTED wire-in points: `resolve_numeric_or_citation` line 89/125/127, `resolve_entity_fact` line 287/321), `claims/{models,pointer,service,gate}.py`, `state/claims.py`; `librarian/{search,query_extractor,relevance_judge,theoremsearch,math_classifier}.py` (search + candidate flow + math routing); `grounding/{full_text,service,entailment,cache}.py` (fetch + `number_substantiated` presence gate + cache); `agents/citation_guard.py` + `agents/reference_validator.py` (citation-repair occurrence helpers). External: `httpx`/`requests` (reuse `librarian/search._retry_request` + `_TokenBucket`), `PyYAML`. Models via the free-first Dartmouth backend.
**New external sources (all FREE — Constitution IV)**: OEIS (`oeis.org/search?q=…&fmt=json`), Wikipedia (REST/`api.php`), Wikidata (`wbsearchentities` + entity API). Semantic Scholar / arXiv / TheoremSearch already wired.
**Storage**: fill resolutions cached under the existing `state/librarian-cache/` (grounding `cache.py` pattern, TTL + atomic write); resolved values + provenance persist on the spec-016 `Claim` in `state/claims/<PROJ>.yaml` (`evidence` holds provenance; `resolved_value` holds the corrected value).
**Testing**: `pytest` across `tests/{unit,contract,integration,real_call}`; real-call gated by `LLMXIVE_REAL_TESTS=1` + Dartmouth key (FR-013, Constitution III). Offline gate: `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`.
**Target Platform**: local pipeline runtime (darwin/linux).
**Project Type**: single project (Python library + automated pipeline).
**Performance Goals**: fills cached by claim/subject (TTL) and reused across rounds/documents (FR-009); a verified claim never re-searches.
**Constraints**: **no value from model memory** (every fill located in fetched source text); **no mocks** of search/retrieval/extraction; free APIs only; fail-fast precondition checks; the fill is env-gated (`LLMXIVE_CLAIM_FILL=1`, mirroring `LLMXIVE_CLAIM_LAYER`/`LLMXIVE_GROUNDING_GUARD`) so offline tests stay network-free; `cli.run` enables it for real runs.
**Scale/Scope**: per-claim fill attempts (a handful of channel calls each); v1 = numeric + entity claim types.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Assessment |
|-|-|
| **I. Single Source of Truth** (NON-NEGOTIABLE) | PASS — reuses librarian search/query/judge, grounding fetch+presence gate+cache, citation_guard repair helpers, the spec-016 Claim registry/pointer/render rather than re-implementing (FR-012). New `fill/` package + per-channel clients are the only new code; each channel follows the existing `Candidate`/HTTP/cache patterns. |
| **II. Verified Accuracy** (NON-NEGOTIABLE) | PASS — this layer *strengthens* verified accuracy: the corrected value is located in a fetched primary/reference source and carries provenance (FR-003/004); references introduced into spec/code are WebFetch-verified before use (FR-013). The "never from model memory" gate is the core of this principle. |
| **III. Robustness & Real-World Testing** | PASS — FR-013 mandates real-call tests against real searches/sources; the headline 27,635→9,988 e2e (FR-014) is a real-call acceptance test; offline pure-logic tests are the secondary layer. |
| **IV. Cost Effectiveness (Free-First)** | PASS — OEIS, Wikipedia, Wikidata, Semantic Scholar (free tier), arXiv, TheoremSearch are all free; fills are cached aggressively to avoid repeat calls. No paid service. |
| **V. Fail Fast** | PASS — a fill is attempted only after the cheap check-only resolver fails; presence gate fails fast on absent values; a missing/empty fetched source yields no fill (block), never a guess. |
| **VI. Convergent Review** (NON-NEGOTIABLE) | PASS — unchanged: a filled (now VERIFIED) claim advances; an unfillable claim stays blocked by the spec-016 unified marker + gate. No new review mechanics; no point system. |

**Result: PASS — no violations. Complexity Tracking omitted.**

## Project Structure

### Documentation (this feature)

```text
specs/017-claim-auto-correction/
├── plan.md            # This file
├── research.md        # Phase 0 output
├── data-model.md      # Phase 1 output
├── quickstart.md      # Phase 1 output
├── contracts/
│   └── fill-layer.md
└── tasks.md           # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
src/llmxive/
├── fill/                         # NEW package — the authoritative-fill layer
│   ├── __init__.py
│   ├── models.py                 # FetchedSource, FillProvenance, FillResult
│   ├── subject_query.py          # derive a subject query from a claim (strip the asserted value)
│   ├── channels/                 # source-channel clients (each → list[FetchedSource])
│   │   ├── __init__.py           # channel registry + authority order (curated > paper)
│   │   ├── oeis.py               # NEW: OEIS search + fetch (integer-sequence/combinatorial counts)
│   │   ├── wikipedia.py          # NEW: Wikipedia search + fetch (general reference)
│   │   ├── wikidata.py           # NEW: Wikidata search + entity fetch (relational/entity facts)
│   │   ├── papers.py             # reuse librarian search (SemanticScholar + arXiv) → FetchedSource
│   │   └── theorem.py            # reuse librarian TheoremSearch for math-classified claims
│   ├── extract.py                # extract candidate value from fetched text + present-in-source gate
│   ├── conflict.py               # channel-priority resolution + record disagreement (FR-008)
│   ├── citation_repair.py        # repair the citation near a filled value to the authoritative source
│   └── service.py                # fill_claim(...) orchestrator (search→retrieve→extract→verify→provenance)
├── claims/resolve.py             # MODIFY — call fill on the NEI/REFUTED branches (numeric, entity) when LLMXIVE_CLAIM_FILL=1
├── claims/service.py             # MODIFY — after render, repair citations for filled claims
├── cli.py                        # MODIFY — cli.run sets LLMXIVE_CLAIM_FILL=1 for real runs
├── librarian/…                   # REUSE (search, query_extractor, relevance_judge, theoremsearch, math_classifier)
├── grounding/…                   # REUSE (full_text.retrieve, service.number_substantiated, entailment.assess, cache)
└── agents/{citation_guard,reference_validator}.py  # REUSE (occurrence regexes for citation repair)

tests/
├── unit/        test_fill_subject_query.py, test_fill_extract.py, test_fill_conflict.py, test_fill_citation_repair.py, test_fill_channels_parse.py
├── contract/    test_fill_channel_contract.py (FetchedSource shape per channel)
├── integration/ test_fill_resolve_wireup.py (resolve.py NEI→fill→VERIFIED), test_fill_render_repairs_citation.py
└── real_call/   test_fill_oeis_real.py (27,635→9,988), test_fill_wikipedia_real.py, test_fill_wikidata_real.py, test_fill_no_source_blocks_real.py, test_fill_e2e_real.py (chokepoint, headline)
```

**Structure Decision**: Single project. A new `src/llmxive/fill/` package holds the fill orchestrator + per-channel clients + extraction/conflict/citation-repair; it is invoked from `claims/resolve.py`'s existing NEI/REFUTED branches (numeric + entity in v1) and `claims/service.py` (citation repair after render). All search/retrieval/presence-gate/cache/citation machinery is reused from `librarian/`, `grounding/`, and `agents/citation_guard.py`. The only genuinely new integrations are the OEIS/Wikipedia/Wikidata channel clients, each following the existing librarian HTTP (`_retry_request` + `_TokenBucket`) and cache patterns.
