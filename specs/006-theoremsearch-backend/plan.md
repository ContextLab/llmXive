# Implementation Plan: TheoremSearch backend for the librarian + mathematics as 9th default field

**Branch**: `008-theoremsearch-backend` | **Date**: 2026-05-12 | **Spec**: [spec.md](spec.md)
**Type**: Amendment to spec 005 (the librarian agent) — NOT a new spec/agent. The librarian's Q1 clarification explicitly anticipated "future spec may expand the backend list if these two prove insufficient"; this is that spec.
**Input**: Feature specification from `specs/006-theoremsearch-backend/spec.md` (clarified 2026-05-12).
**Tracking issue**: #113 (parent #111). Deferred sibling: #114 (Spec B — theorem-statement artifacts).

## Summary

The llmXive `librarian` agent (spec 005, merged in PR #110, currently `prompt_version: 1.5.0`) is the single canonical literature-search-and-citation-verification agent. It searches two candidate-source backends (Semantic Scholar Graph API + arXiv API), decomposes a research question into 5 keyword queries via an LLM extractor, runs them in parallel, unions the candidates, and runs each through a verification chain (URL resolves → title-token-overlap ≥0.7 → summary-grounding ≥0.5 → LLM topical-relevance judge), returning structured JSON.

This amendment:

1. **Adds [TheoremSearch](https://www.theoremsearch.com/) as a third candidate-source backend** — a candidate *source* feeding the existing verification chain, NOT a competing agent (Constitution Principle I: the librarian stays the single entry point + single verifier). For each arXiv-sourced theorem hit it returns, the librarian resolves the source paper's arXiv ID to its existing `Candidate` shape (via `ArxivClient.get_by_id`), tags it `backend="theoremsearch"`, and runs it through the unchanged chain. Non-arXiv-sourced hits (ProofWiki, Stacks Project — no DOI/arXiv ID) are skipped (reserved for Spec B / #114).
2. **Adds an LLM math-classifier** — `field ∈ {"mathematics", "statistics"}` always queries TheoremSearch; other fields consult a one-LLM-call classifier ("is this a pure-mathematics theorem/proof/formal-structure question? yes/no"), fail-open to `false`, verdict cached keyed by `(project_id, librarian_prompt_version)`.
3. **Adds `mathematics` as the 9th default field** — to `src/llmxive/cli.py`'s `default_fields`, `tests/phase2/test_librarian_cross_domain.py`'s `DEFAULT_FIELDS`, and the brainstorm prompt's field-example prose — and brainstorms 5 seed math projects so the cross-domain test has math content.
4. **Adds one new output-JSON field** — a `math_classifier` audit object `{invoked, verdict, error}`, parallel to the existing `relevance_judge` / `pdf_sample` audit objects (the only schema change in this amendment, per Clarifications 2026-05-12).
5. **Bumps the librarian `prompt_version`** (1.5.0 → 1.6.0 — the classifier is a new LLM call) → cache-invalidating → re-runs cross-domain coverage (now 9 fields) + PROJ-261/262 re-validation to confirm no regression on non-math projects.

## Technical Context

**Language/Version**: Python 3.11 (existing llmXive codebase)
**Primary Dependencies**: `requests`/`httpx` (existing — for the TheoremSearch POST and arXiv resolution), `pypdf` (existing — unchanged), the existing `llmxive.backends` router (for the math-classifier LLM call). No new third-party packages.
**External services**: TheoremSearch API (`https://api.theoremsearch.com/search`, POST, no auth, no documented rate limits, OpenAPI at `/openapi.json`) — NEW; Semantic Scholar Graph API + arXiv API — existing; Dartmouth Chat (+ HF + local fallback) — existing, used for the math-classifier call.
**Storage**: `state/librarian-cache/` (existing sha256-keyed result cache — unchanged); NEW: a math-classifier verdict cache keyed by `(project_id, librarian_prompt_version)` (small JSON, can live under `state/librarian-cache/` or a sibling — implementation choice in research.md).
**Testing**: pytest (existing). New: `tests/phase2/test_theoremsearch.py`, `tests/phase2/test_math_classifier.py`; modified: `tests/phase2/test_librarian_cross_domain.py` (9 fields). Real-call tests gated on `LLMXIVE_REAL_TESTS=1` + `DARTMOUTH_CHAT_API_KEY` (existing pattern); TheoremSearch real-API tests gated on network reachability.
**Target Platform**: macOS / Linux developer workstation + GitHub Actions CI (the existing `real-call` workflow). TheoremSearch + arXiv + Dartmouth Chat reachable.
**Project Type**: research-pipeline infrastructure amendment — extends an existing agent with one new backend + one new pre-step (classifier) + one config change (9th field). No new agent, no new top-level module tree.
**Performance Goals**: per-citation verification ≤2s abstract / ≤30s PDF-sample (unchanged); the TheoremSearch backend adds one POST per librarian invocation (when triggered) plus one `ArxivClient.get_by_id` per arXiv-sourced hit (subject to the existing arXiv rate limiter); the math-classifier adds at most one LLM call per librarian invocation on non-math fields (cached per-project). Total librarian invocation stays under the existing **1800s soft target** (Q4, raised in spec-005 fix-up #5; not enforced).
**Constraints**: TheoremSearch is a candidate *source* only — it MUST NOT alter the verification chain, expansion logic, PDF-sample logic, or relevance judge. The only output-JSON change is the `math_classifier` audit object. Verification stays deterministic for fixed cache state (inherits spec-005's FR-023 / SC-012, modulo the known judge non-determinism tracked in #112). The librarian MUST complete normally when TheoremSearch is unreachable (fall through to SS+arXiv). `mathematics` MUST be in the field list before the brainstorm step runs (so seed projects carry `field: mathematics`).
**Scale/Scope**: 9 default fields × ~most-recently-brainstormed-project-per-field cross-domain coverage; 5 new seed math projects; ~3 new source modules (`theoremsearch.py`, `math_classifier.py`, plus wiring in `agents/librarian.py`); ~3 new/modified test files; ~4 doc updates (registry comment, spec-005 diagnostic, spec-005 spec Q1, this spec's contracts).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-|-|-|
| **I. Single Source of Truth (NON-NEGOTIABLE)** | **PASS** | TheoremSearch is a *backend* (a `Candidate`-producing client alongside `SemanticScholarClient`/`ArxivClient`), not a competing agent — the librarian remains the single entry point + verifier. Before adding `TheoremSearchClient`, confirm no existing TheoremSearch client; before adding `math_classifier.py`, confirm the classification logic isn't already somewhere (it isn't — this is new behavior). The field-list constant currently lives in TWO places (`cli.py` `default_fields`, `test_librarian_cross_domain.py` `DEFAULT_FIELDS`) — that's a pre-existing duplication; this amendment updates both consistently but does NOT introduce a third copy. Consolidating them into a single canonical constant is **out of scope for this amendment** (it would expand the blast radius) and is tracked as a separate hygiene follow-up in **GitHub issue #116** (to be done after #113 lands). No forked prompts: the math-classifier prompt is new; the librarian prompt gets a `prompt_version` bump. |
| **II. Verified Accuracy (NON-NEGOTIABLE)** | **PASS** | TheoremSearch-sourced candidates go through the *exact same* verification chain (URL resolves → title-overlap ≥0.7 → summary-grounding ≥0.5 → LLM topical-relevance judge) as arXiv candidates — they're paper-level records keyed by arXiv ID. No new "trust the source" path. Non-arXiv TheoremSearch hits (ProofWiki etc.) are *skipped* precisely because they lack a verifiable primary-source pointer. The math-classifier verdict is an internal routing signal, not a user-facing claim. |
| **III. Robustness & Reliability (Real-World Testing)** | **PASS** | New real-call tests: a TheoremSearch real-API smoke (POST `/search`, assert JSON shape + arXiv-vs-non-arXiv branching), a math-classifier real-LLM smoke (math question → True, non-math → False), and a `mathematics` parametrization in the existing cross-domain coverage test (real librarian invocation against a real brainstormed math project). Parser-level unit tests use a *recorded* `/search` response, but the recorded response was captured from the live API (notes on #111) — not synthetic. Mock-only tests are secondary fast-feedback only, per the constitution. |
| **IV. Cost Effectiveness (Free-First)** | **PASS** | TheoremSearch is free, no auth, no paid tier. The math-classifier uses the existing free Dartmouth Chat tier (with HF + local fallback). The classifier verdict is cached per-project so a re-run doesn't re-spend the LLM call. arXiv resolution is free. No paid service introduced. |
| **V. Fail Fast** | **PASS** | TheoremSearch failure → `TransientBackendError` → the librarian falls through to SS+arXiv immediately, no retry-forever. The math-classifier fails open to `false` immediately on any backend error (with a loud stderr diagnostic + a recorded `math_classifier` audit object — observable, not silent). The `mathematics`-must-precede-brainstorm ordering is a documented precondition (Phase 1 / tasks). The librarian's existing preflight checks (SS key, arXiv reachable, Dartmouth creds, cache dir writable) are unchanged. |

**Gate result: PASS — no violations, no Complexity Tracking entries needed.**

## Project Structure

### Documentation (this feature)

```text
specs/006-theoremsearch-backend/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature specification (clarified 2026-05-12)
├── research.md          # Phase 0 output (/speckit-plan)
├── data-model.md        # Phase 1 output (/speckit-plan)
├── quickstart.md        # Phase 1 output (/speckit-plan)
├── contracts/           # Phase 1 output (/speckit-plan)
│   ├── theoremsearch-client.md        # TheoremSearchClient.search() contract — input/output, the arXiv-only filter, the Candidate mapping, the rate-limit, the TransientBackendError-on-failure behavior
│   ├── math-classifier.md             # is_math_theory_question() contract — input/output, fail-open semantics, the (project_id, prompt_version) cache key, the math_classifier audit object
│   ├── librarian-json-output-delta.md # The ONE schema change: the math_classifier audit object {invoked, verdict, error}; everything else unchanged from spec-005's librarian-json-output.md
│   └── cross-domain-coverage-9fields.md  # The mathematics parametrization addition to the existing cross-domain coverage contract (soft-skip when no math project brainstormed)
├── checklists/
│   └── requirements.md  # Spec-quality checklist (created + updated post-clarify)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
# Production code — NEW (this amendment)
src/llmxive/librarian/
├── theoremsearch.py               # NEW — TheoremSearchClient: POST /search → for arXiv-sourced hits, extract+strip arXiv ID, ArxivClient.get_by_id() for full record, emit Candidate(backend="theoremsearch", ...); skip non-arXiv; token-bucket rate limiter (~1 req/2s, same pattern as ArxivClient); errors → TransientBackendError
└── math_classifier.py             # NEW — is_math_theory_question(question, idea_body_excerpt, *, model, ...) -> bool via one LLM call; fail-open to False with loud stderr diagnostic; verdict cache keyed by (project_id, librarian_prompt_version); plus a small MathClassifierResult record carrying {invoked, verdict, error} for the audit object

agents/prompts/
└── math_classifier.md             # NEW — the math-classifier system+user prompt ("Is this a pure-mathematics theorem/proof/formal-structure question? Reply YES or NO on the first line, then a one-line rationale.")

# Production code — MODIFIED (this amendment)
src/llmxive/agents/
└── librarian.py                   # MODIFIED — invoke(): after the existing extracted-query searches, branch:
                                    #   if field in ("mathematics", "statistics"): candidates += TheoremSearchClient().search(term)  [math_classifier audit = {invoked: false, ...}]
                                    #   elif is_math_theory_question(...): candidates += TheoremSearchClient().search(term)  [audit = {invoked: true, verdict: true/false/null, ...}]
                                    # thread new candidates into the existing merge → verify → judge chain (no chain changes);
                                    # add `math_classifier` to LibrarianResult + to_dict() (parallel to relevance_judge/extracted_queries);
                                    # accept an optional project_id arg so the classifier cache can be keyed by it (flesh_out already knows the project_id; pass it through)

src/llmxive/
└── cli.py                         # MODIFIED — add "mathematics" to default_fields (line ~208-212)

agents/prompts/
└── brainstorm.md                  # MODIFIED — add `mathematics` to the field-example list in the Inputs section (prose, not a hard enum)

agents/
└── registry.yaml                  # MODIFIED — bump librarian prompt_version 1.5.0 → 1.6.0; update the librarian entry comment (now 3 backends + a math classifier)

# Tests — NEW / MODIFIED (this amendment)
tests/phase2/
├── test_theoremsearch.py          # NEW — parser tests on a recorded /search response (arXiv hit → Candidate; ProofWiki hit → skipped; version-suffix stripping; dedup by arXiv ID); the Candidate-mapping shape; real-API smoke (gated on network — POST /search, assert {theorems: [...]} shape, assert ≥1 arXiv-sourced hit for a known math query); TransientBackendError on a forced-unreachable host
├── test_math_classifier.py        # NEW — parser tests (YES/NO first-line → bool; unparseable → fail-open False); the cache behavior (second call on same (project_id, prompt_version) is a cache hit, no LLM call); the MathClassifierResult shape; real-LLM smoke gated on DARTMOUTH_CHAT_API_KEY (a plainly-math question → True; a plainly-non-math question → False)
└── test_librarian_cross_domain.py # MODIFIED — add "mathematics" to DEFAULT_FIELDS (now 9); the existing "no brainstormed projects found for field=X" skip handles the case where no math project exists yet (no new skip logic needed)

# Diagnostic / spec-005 doc updates (this amendment)
notes/2026-05-07-spec-005-librarian-diagnostic.md   # MODIFIED — append a "spec-006 amendment: TheoremSearch backend + mathematics field" section noting the 3rd backend, the math classifier, the prompt bump 1.5.0→1.6.0, the new math_classifier audit object, and the re-run results
specs/005-librarian-agent/spec.md                   # MODIFIED — the Q1 clarification ("future spec may expand the backend list") gains a "→ done in spec 006 (#113): added TheoremSearch" cross-reference
```

**Structure Decision**: This is a **single-project Python amendment** (Option 1 in the template, but minimal). No new top-level directory tree — the new modules live inside the existing `src/llmxive/librarian/` package alongside `search.py`, `verify.py`, etc., exactly as spec-005 organized them. No new agent class (TheoremSearch is a backend client, the math-classifier is a helper function — both consumed by the existing `LibrarianAgent`). The seed-math-project step produces 5 project directories under the existing `projects/` / `state/projects/` layout via the existing brainstorm agent — no special structure. The two pre-existing copies of the default-fields list (`cli.py`, `test_librarian_cross_domain.py`) are both updated by this amendment; consolidating them into a single canonical constant is **out of scope here** — tracked as a separate hygiene follow-up in **GitHub issue #116** (to be done after #113 lands, to avoid conflicting with this amendment's diff).

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |

## Phase 0: Outline & Research

No `NEEDS CLARIFICATION` markers remain in the spec (resolved at /speckit-clarify). Research tasks are dependency/integration patterns, not unknowns:

1. **TheoremSearch `/search` response shape — full schema confirmation.** The notes on #111 captured a partial shape from live probing. Phase 0 records the full per-theorem record (`{theorem_id, name, body, slogan, theorem_type, link, paper: {paper_id, source, title, authors, link, summary, journal_ref, primary_category, categories, citations, year, journal_published}, similarity, score, has_metadata}`), confirms the `paper.source` enum values seen (`"arXiv"`, `"ProofWiki"`, ...), confirms `paper.paper_id` is the versioned arXiv ID for arXiv-sourced hits, and notes the `limit` request parameter behavior. Decision: consume only `paper` (for `source == "arXiv"`) + `score`; ignore the theorem body/slogan (Spec B's territory).
2. **arXiv-ID version-suffix handling.** `paper.paper_id` is `1306.5434v2`; `ArxivClient.get_by_id` expects... what — bare `1306.5434`, or does it accept the version suffix? Phase 0 confirms by reading `search.py:get_by_id` and testing. Decision: strip the `vN` suffix with `re.sub(r"v\d+$", "", id)` before calling `get_by_id`; if `get_by_id` returns `None`, drop the candidate (logged).
3. **Math-classifier cache location + format.** The verdict cache is keyed by `(project_id, librarian_prompt_version)`. Phase 0 decides: a single JSON file `state/librarian-cache/math-classifier-verdicts.json` mapping `f"{project_id}::{prompt_version}"` → `{verdict, classified_at}`, or one small file per key under a `state/librarian-cache/math-classifier/` subdir. Decision (lean): single JSON file (a few math projects → tiny; matches the "small per-project cache" intent; easy to inspect). Stale-on-prompt-bump is automatic because the key includes `librarian_prompt_version`.
4. **Where the math branch goes in `LibrarianAgent.invoke()`.** Phase 0 confirms the existing flow (cache check → extracted-query searches → merge → verify → expand-if-under-target → relevance judge → PDF sample → cache write → search trail → return) and decides the math branch slots in *after* the extracted-query searches and *before* `merge_candidates` so TheoremSearch candidates participate in dedup. Decision: append TheoremSearch candidates to the same `candidates` list the SS+arXiv loop builds, then `merge_candidates` (already dedups by `primary_pointer`).
5. **`project_id` plumbing.** `LibrarianAgent.invoke()` currently takes `term`, `field`, `idea_body_excerpt`, `target_n`, `repo_root`, clients, `relevance_judge_disabled`. The classifier cache needs `project_id`. Phase 0 confirms `flesh_out` (the main caller, `src/llmxive/agents/idea_lifecycle.py`) has the project_id and decides to add `project_id: str | None = None` to `invoke()` (None → classifier runs without caching). Decision: add the optional param; flesh_out passes it; tests can omit it.

**Output**: `research.md` with the 5 decisions above (Decision / Rationale / Alternatives-considered format).

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete.

1. **`data-model.md`** — the entities (extending spec-005's data model):
   - **E-TS1 TheoremSearch theorem hit**: the `/search` response record; the librarian consumes `paper` (for arXiv-sourced) + `score`.
   - **E-TS2 TheoremSearch-sourced Candidate**: a `Candidate` with `backend="theoremsearch"`, `primary_pointer` = bare arXiv ID, other fields from `ArxivClient.get_by_id`. Indistinguishable downstream from an arXiv candidate except by backend tag.
   - **E-TS3 MathClassifierResult**: `{invoked: bool, verdict: bool | None, error: str | None, cached: bool}` — the in-memory record; the JSON-serialized form (dropping `cached`) is the `math_classifier` audit object in `LibrarianResult`.
   - **E-TS4 Math-classifier verdict cache entry**: `{key: "{project_id}::{prompt_version}", verdict: bool, classified_at: ISO-8601}`.
   - **E-TS5 Seed math project**: a brainstormed project with `field: mathematics` — same shape as any project; 5 of them.
   - Note the *unchanged* entities (`LibrarianResult` gains one field; `Candidate`, the verification chain records, the search-trail record, the cross-domain-test-row record are all unchanged except the test-row may gain a `theoremsearch_hit_count`).
2. **`contracts/`** (4 files, listed in the structure tree above): the `TheoremSearchClient.search()` contract; the `is_math_theory_question()` contract; the `librarian-json-output-delta.md` (just the `math_classifier` field, referencing spec-005's full `librarian-json-output.md` for everything else); the `cross-domain-coverage-9fields.md` (the `mathematics` parametrization + soft-skip behavior).
3. **`quickstart.md`** — a runbook: (a) preflight (TheoremSearch reachable, Dartmouth creds for the classifier); (b) add `mathematics` to the field lists; (c) brainstorm 5 seed math projects; (d) invoke the librarian on a math project, observe TheoremSearch-sourced verified citations; (e) bump `prompt_version`, wipe cache, re-run cross-domain (9 fields) + PROJ-261/262 re-validation; (f) confirm the `math_classifier` audit object in the output JSON.
4. **Agent context update** — update the `<!-- SPECKIT START -->`…`<!-- SPECKIT END -->` block in `CLAUDE.md` to reference `specs/006-theoremsearch-backend/plan.md`.

**Output**: `data-model.md`, `contracts/*` (4 files), `quickstart.md`, updated `CLAUDE.md`.

## Re-evaluate Constitution Check (post-design)

No design decision introduces a paid dependency, a duplicate implementation, a mock-only test path, a silent failure, or a late-failing entry point. The one output-JSON schema change (the `math_classifier` audit object) is a deliberate, clarified, narrowly-scoped exception consistent with the existing `relevance_judge`/`pdf_sample` audit objects. **Gate result after Phase 1: PASS (re-confirmed).**

## Notes

- This plan ends after Phase 2 *planning*; the actual `tasks.md` is produced by `/speckit-tasks`, and implementation by `/speckit-implement`.
- The `prompt_version` bump (1.5.0 → 1.6.0) invalidates the librarian's result cache — the cross-domain coverage tests and the PROJ-261/PROJ-262 re-validation re-run is mandatory (FR-A12 / SC-A08) and is the standard regression check, same as every prior librarian fix-up.
- Open task-ordering detail (not a spec decision): the seed-math-project brainstorm step MUST run *after* `mathematics` is added to the field lists, so the seed projects carry `field: mathematics`. `/speckit-tasks` will order this.
- Known residual issue carried from spec 005: the LLM relevance judge (and now the math-classifier) is non-deterministic (temperature > 0) — tracked in GitHub issue #112. This amendment does not fix it; the math-classifier's fail-open-to-`false` + per-project cache mitigates the impact (a missed trigger just means TheoremSearch isn't consulted that run; SS+arXiv still cover the question; and the cache freezes the verdict per project).
