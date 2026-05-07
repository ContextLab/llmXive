---

description: "Task list for spec 005 — Librarian Agent + Phase 1 re-validation"
---

# Tasks: Librarian Agent + Phase 1 Re-Validation

**Input**: Design documents from `specs/005-librarian-agent/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Yes — pytest unit tests for each librarian sub-module are required by FR-001/004/011 + cross-domain tests (US4) + re-validation orchestration tests (US3). Test-first discipline applies to all new librarian code per Constitution Principle III.

**Commit-message convention**: Spec 005 is cross-cutting infrastructure (it doesn't operate on a single pipeline phase like specs 003 + 004 did). Commit messages use prefix `spec-005:` (no `phaseN/` prefix), reference the relevant US + FR identifiers, and end with `(... #107)` to tie to the tracking issue. Defects use `S5-D##` prefix (S=Spec) — distinguishes from spec 003/004's `P1-D##` / `P2-D##` which referenced pipeline phases.

**Organization**: Tasks grouped by user story. The MVP is US1 (librarian core capability); US2 (expansion), US4 (cross-domain), US3 (Phase 1 re-validation), US5 (report), US6 (carry-forward) build on US1's substrate.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1-US6
- File paths absolute relative to repo root

## Path Conventions

Single project; all paths relative to `/Users/jmanning/llmXive/`:
- Production code: `src/llmxive/librarian/` (NEW), `src/llmxive/agents/librarian.py` (NEW), `agents/prompts/librarian.md` (NEW), `agents/registry.yaml` (MODIFIED)
- Rewired modules: `src/llmxive/agents/idea_lifecycle.py`, `src/llmxive/agents/reference_validator.py`, `tests/phase1/citation_resolver.py`, `agents/tools/lit_search.py`
- Tests: `tests/phase2/` (NEW)
- Spec artifacts: `specs/005-librarian-agent/`
- Diagnostic: `notes/`
- Real-project artifacts: `projects/PROJ-261-...`, `projects/PROJ-262-...` (in place per spec 004 convention)
- Cache: `state/librarian-cache/<sha256>.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preflight + create the new directory layouts the librarian sub-package needs. No work in any user-story phase begins until Phase 1 + Phase 2 complete.

- [ ] T001 Run preflight per quickstart.md Step 0: verify branch is `008-librarian-agent`, both carry-forward canonicals exist at `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/` + `projects/PROJ-262-predicting-molecular-dipole-moments-with/`, Dartmouth credentials load, **Semantic Scholar API key loadable via `python -c "from llmxive.credentials import load_semantic_scholar_key; print('ok' if load_semantic_scholar_key(prompt_if_missing=False) else 'missing')"`, AND a real authenticated curl test returns 200 (not 429): `curl -s -o /dev/null -w "%{http_code}" -H "x-api-key: $SEMANTIC_SCHOLAR_API_KEY" "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"` should print `200`**, arXiv API reachable, `git status --short` clean (or only `.omc/`/cron files).
- [ ] T001a Install the Semantic Scholar API key (one-time setup; do this BEFORE T001 if not already done). Apply via the form at https://www.semanticscholar.org/product/api#api-key-form (free tier; ~1-3 business day approval). Once received: `python -c "from llmxive.credentials import save_semantic_scholar_key; save_semantic_scholar_key('<paste-key-here>')"`. Verify with `python -c "from llmxive.credentials import load_semantic_scholar_key, mask_key; print(mask_key(load_semantic_scholar_key()))"` — should print masked key, not `(unset)`. The key file at `~/.config/llmxive/credentials.toml` is mode 0600. **Do not commit the key**; it stays only in the user's home dir.
- [X] T002 Create the new directory layout: `mkdir -p src/llmxive/librarian tests/phase2 state/librarian-cache && touch src/llmxive/librarian/__init__.py tests/phase2/__init__.py`. Verify with `ls`. (Note: only the package skeleton + `__init__.py` files are created here; individual test modules under `tests/phase2/` are created per-user-story in their respective task ranges — T013-T016/T020/T024/T027/T031a/T047/T070a.)
- [X] T003 Add `pypdf` to project dependencies in `pyproject.toml` (the only new dep this spec introduces; ~5MB; needed for the ≥10% PDF-sample audit per Q2 / research.md Decision 4).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The 5-module librarian sub-package implementations + the LibrarianAgent class + the prompt + the registry entry. ALL user stories depend on these.

**⚠️ CRITICAL**: No US1-US6 task can begin until T004-T013 complete and pytest passes T015.

- [ ] T004 [P] Implement [src/llmxive/librarian/search.py](src/llmxive/librarian/search.py) with `SemanticScholarClient` + `ArxivClient` per research.md Decision 2. Token-bucket rate limiter (2/sec replenish, 5 burst) for Semantic Scholar; 3-sec inter-call sleep for arXiv. Both share the existing router-style retry logic (3 attempts on 429/5xx, exponential backoff). Returns `Candidate` records per data-model.md E2.
- [ ] T005 [P] Implement [src/llmxive/librarian/verify.py](src/llmxive/librarian/verify.py) with the canonical `verify_citation(candidate, *, fetch_pdf=False)` helper per research.md Decision 3. Three sequential checks (URL resolves → title-token-overlap ≥0.7 → summary grounded) each populating `verification_log` per data-model.md E3.
- [ ] T006 [P] Implement [src/llmxive/librarian/pdf_sample.py](src/llmxive/librarian/pdf_sample.py) with `sample_for_pdf_audit(verified, sample_rate=0.10)` returning ≥10% (min 1) random sample, plus `extract_pdf_text(url)` using `pypdf` for first-1000-words extraction. Handle paywall + corrupt-PDF + size-limit gracefully (each becomes `summary_grounded_pdf: None` in the citation).
- [ ] T007 [P] Implement [src/llmxive/librarian/cache.py](src/llmxive/librarian/cache.py) with `cache_key(term_normalized, field, target_n, prompt_version) -> sha256_hex`, `get(key) -> LibrarianResult | None` (TTL-respecting), `set(key, result)` (writes JSON to `state/librarian-cache/<sha256>.json`). TTLs per FR-011: 30d arXiv, 7d HTTP HEAD, 90d DOI bib.
- [ ] T008 [P] Implement [src/llmxive/librarian/expand.py](src/llmxive/librarian/expand.py) with `expand_terms(original, context, n=20)` (LLM brainstorm via existing `chat_with_fallback`) and `iterate_until_target(original, expanded, target_n)` that runs queries through search + verify modules until ≥5 verified accumulated OR list exhausted. Hard cap of 20 expanded terms.
- [ ] T009 Implement [agents/prompts/librarian.md](agents/prompts/librarian.md) v1.0.0 with two sections: (1) **Expansion brainstorm prompt** — gives the LLM a thin-result term + project context (field + idea body excerpt) and asks for 10-20 alternative phrasings ranked by relevance; (2) reserved space for future LLM-driven sub-tasks. Specifies output format the parser expects: numbered list, one term per line.
- [ ] T010 Implement [src/llmxive/agents/librarian.py](src/llmxive/agents/librarian.py): `LibrarianAgent` class subclassing `Agent` from `llmxive.agents.base`. `build_messages` emits the expansion prompt only when expansion fires. `handle_response` orchestrates: cache check → search → verify → maybe expand → PDF sample → cache write → return JSON per `contracts/librarian-json-output.md`.
- [ ] T011 Add the librarian to [agents/registry.yaml](agents/registry.yaml) per quickstart.md Step 1i: `name: librarian`, `purpose: ...`, `prompt_path: agents/prompts/librarian.md`, `prompt_version: 1.0.0`, `default_backend: dartmouth`, `fallback_backends: [huggingface, local]`, `default_model: qwen.qwen3.5-122b`, `wall_clock_budget_seconds: 600` (per Q4 / FR-010), `paid_opt_in: false`.
- [ ] T012 Commit Phase 2 substrate: `git add src/llmxive/librarian/ src/llmxive/agents/librarian.py agents/prompts/librarian.md agents/registry.yaml pyproject.toml && git commit -m "spec-005: librarian sub-package + agent + prompt v1.0.0 (US1, FR-001/010, #107)"`.

---

## Phase 3: User Story 1 - Librarian core capability (Priority: P1) 🎯 MVP

**Goal**: Verify the librarian's core search-and-verify path works end-to-end on a known-good arXiv query.

**Independent Test**: `pytest tests/phase2/test_librarian_search.py tests/phase2/test_librarian_verify.py tests/phase2/test_librarian_cache.py tests/phase2/test_librarian_pdf_sample.py -v` produces all green; a manual invocation of `LibrarianAgent` with `term="attention is all you need transformers"` returns ≥1 verified citation with `bibliographic_info.title` matching the Vaswani paper, `verification_log.url_resolves: True`, `summary_grounded_pdf: True` for the sampled subset.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement [tests/phase2/test_librarian_search.py](tests/phase2/test_librarian_search.py) with real-API tests: `test_semantic_scholar_real_search` (queries `"transformer attention"`, asserts ≥1 `Candidate` returned), `test_arxiv_real_search` (queries arXiv ID `1706.03762`, asserts the Vaswani paper resolves), `test_rate_limiter_token_bucket` (issues 10 quick queries, asserts no 429 retries fire). All use real HTTP, no mocks.
- [ ] T014 [P] [US1] Implement [tests/phase2/test_librarian_verify.py](tests/phase2/test_librarian_verify.py) with: `test_known_good_arxiv_verifies` (1706.03762 passes all three checks), `test_known_bad_url_fails` (`https://example.invalid/paper.pdf` fails URL-resolves check with reason `"url_not_resolves"`), `test_doi_redirect_handled` (DOI redirect → final URL captured in `redirect_chain`), `test_title_token_overlap_below_threshold_excludes` (synthetic candidate with mismatching title → reason `"title_mismatch"`).
- [ ] T015 [P] [US1] Implement [tests/phase2/test_librarian_cache.py](tests/phase2/test_librarian_cache.py) with: `test_cache_miss_then_hit` (first call writes, second reads from disk), `test_cache_invalidation_on_prompt_version_bump` (cache entry with `prompt_version: 1.0.0` is ignored when current registry says `1.1.0`), `test_cache_ttl_expiry` (mock-time-advance past 30d → entry treated as miss), and `test_cache_hit_returns_deterministic_result` (per SC-012 / FR-023: invoke twice on the same cache state; assert `verified_citations` lists are identical at JSON level modulo `verification_log.verified_at` timestamps).
- [ ] T016 [P] [US1] Implement [tests/phase2/test_librarian_pdf_sample.py](tests/phase2/test_librarian_pdf_sample.py) with: `test_pdf_extraction_on_arxiv` (downloads 1706.03762 PDF, asserts pypdf returns ≥1000 chars), `test_sample_size_calculation` (5 verified citations → sample_size_target == 1; 50 verified → sample_size_target == 5), `test_paywall_handling` (synthetic 401 response → citation gets `summary_grounded_pdf: None`).
- [ ] T017 [US1] Run all 4 unit-test modules: `pytest tests/phase2/test_librarian_search.py tests/phase2/test_librarian_verify.py tests/phase2/test_librarian_cache.py tests/phase2/test_librarian_pdf_sample.py -v`. ALL must pass before continuing. If any fail, fix the underlying module (NOT the test).
- [ ] T018 [US1] Manual smoke test: `python -c "from llmxive.agents.librarian import LibrarianAgent; from llmxive.agents import registry; lib = LibrarianAgent(registry.get('librarian')); print(lib.invoke(term='attention is all you need transformers', context={'field': 'computer science', 'target_n': 3}))"`. Verify the JSON output: `outcome: "success"`, ≥1 verified citation with `verification_log.url_resolves: True`, `summary_grounded_pdf: True` for at least one citation.
- [ ] T019 [US1] Commit US1 unit tests + smoke verification: `git add tests/phase2/test_librarian_{search,verify,cache,pdf_sample}.py state/librarian-cache/ && git commit -m "spec-005: US1 unit tests for librarian core capability (FR-001 SC-001/002, #107)"`.

**Checkpoint**: US1 fully tested. Librarian's core path proven against real Semantic Scholar + arXiv; verification helper consolidates spec-003's resolver logic; cache + PDF sampling work.

---

## Phase 4: User Story 2 - Multi-step expanded search (Priority: P1)

**Goal**: Verify the expansion path fires when initial search returns <5 verified citations, generates 10-20 alternatives ranked by relevance, iterates until target reached or exhausted.

**Independent Test**: Invoke the librarian with a deliberately thin-result term (e.g., `"ablation density LLM perplexity"`); assert that `expansion is not None`, `len(expansion.expanded_terms_ranked) >= 10`, `total_queries_issued >= 10`, `outcome in {"success_after_expansion", "exhausted"}`.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement [tests/phase2/test_librarian_expand.py](tests/phase2/test_librarian_expand.py) with: `test_thin_result_triggers_expansion` (term known to return 0 hits initially → expansion fires; final outcome is `"success_after_expansion"` or `"exhausted"`), `test_expanded_terms_count_ge_10` (asserts `len(expanded_terms_ranked) >= 10`), `test_total_queries_issued_ge_10` (asserts the iteration actually ran ≥10 distinct backend queries), `test_hard_cap_at_20_terms` (synthetic LLM response with 50 terms is truncated to 20).
- [ ] T021 [US2] Run `pytest tests/phase2/test_librarian_expand.py -v`. Must pass.
- [ ] T022 [US2] Manual end-to-end test: invoke librarian with the thin term `"ablation density LLM perplexity"`; capture the JSON output to `/tmp/expansion-smoke.json`; verify `outcome` ∈ {`success_after_expansion`, `exhausted`}, `expansion.total_queries_issued >= 10`, expansion-record well-formed.
- [ ] T023 [US2] Implement the SearchTrail subsection writer per `contracts/search-trail-md.md`: when the librarian receives an `idea_md_path` argument, after returning the result it appends (or replaces) a `## Search trail` subsection in that file. Logic lives in `src/llmxive/librarian/search_trail.py` (NEW); `LibrarianAgent.handle_response` calls it.
- [ ] T024 [US2] Add a unit test [tests/phase2/test_search_trail.py](tests/phase2/test_search_trail.py): given a tmp_path idea.md without a Search trail section, after `write_search_trail()` is called the file ends with the contract-conformant subsection (heading + frontmatter + table + numbered list); given an idea.md with an existing Search trail, the existing one is replaced (not duplicated).
- [ ] T025 [US2] Run `pytest tests/phase2/test_search_trail.py -v`. Must pass.
- [ ] T026 [US2] Commit US2: `git add tests/phase2/test_librarian_expand.py tests/phase2/test_search_trail.py src/llmxive/librarian/search_trail.py state/librarian-cache/ && git commit -m "spec-005: US2 multi-step expansion + Search trail subsection writer (FR-004/005/006, SC-003, #107)"`.

**Checkpoint**: US2 done. Expansion fires on thin terms, accumulates ≥10 queries, writes Search trail subsection on idea.md.

---

## Phase 5: User Story 4 - Cross-domain coverage (Priority: P1)

**Goal**: Test the librarian on at least 1 project per default field (8 fields total), confirming each field's research-question term produces verified citations + a manual audit verdict per `contracts/cross-domain-coverage.md`.

**Note**: US4 runs BEFORE US3 because the cross-domain audit is the broader sanity check; US3's narrow re-validation builds on confidence that the librarian works across fields.

**Independent Test**: `pytest tests/phase2/test_librarian_cross_domain.py -v` — 8 parametrized tests, one per field, each completes with `outcome != "failed"` and `len(verified_citations) >= 1`. Manual audit verdicts on a random sample per field are recorded in test artifacts.

### Implementation for User Story 4

- [ ] T027 [US4] Implement [tests/phase2/test_librarian_cross_domain.py](tests/phase2/test_librarian_cross_domain.py) per `contracts/cross-domain-coverage.md`. Parametrized over the 8 default fields; for each: (1) pick most-recently-brainstormed project in that field, (2) derive sample term from `idea/<slug>.md` `## Research question` first sentence, (3) invoke librarian, (4) assert outcome != "failed" + len(verified) >= 1, (5) write a CrossDomainTestRow record to `/tmp/cross-domain-results-{field}.json`.
- [ ] T028 [US4] Run `pytest tests/phase2/test_librarian_cross_domain.py -v --tb=short`. Allow ~30-60min wall-clock. ALL 8 must produce outcome ∈ {`success`, `success_after_expansion`, `exhausted`} (not `failed` for non-transient reasons). If any field fails on a non-transient reason: investigate + fix + re-run. **Per SC-003**: track which fields fired the expansion path (`outcome ∈ {success_after_expansion, exhausted}`). At least 3 of the 8 fields MUST fire expansion. If fewer than 3 fire, the test substrate's research questions are too easy (Semantic Scholar returns ≥5 hits on the initial query); this is a coverage gap, not a librarian defect — pick narrower sample terms in a follow-up iteration. Record per-field `expansion_fired` boolean in the CrossDomainTestRow + the report's § 4 table.
- [ ] T029 [US4] Manual audit on each of the 8 fields: pick 1 random verified citation per field (the test logs the random selection); manually visit the URL; verify (a) URL resolves, (b) title matches the librarian's claim, (c) summary is faithful (not hallucinated). Record the per-field verdict (`pass` / `fail` / `mixed`) in `/tmp/cross-domain-audit.md` for inclusion in the diagnostic report's § 4.
- [ ] T030 [US4] If T029 surfaces any `fail` or `mixed` verdict: file as defect P5-D## with severity per `contracts/cross-domain-coverage.md` defect-categorization table. Fix in this PR (likely a librarian prompt or verification-threshold tweak with prompt_version bump per FR-020) OR defer to a follow-up issue with rationale.
- [ ] T031 [US4] Commit US4: `git add tests/phase2/test_librarian_cross_domain.py state/librarian-cache/ && git commit -m "spec-005: US4 cross-domain coverage tests (8 fields, FR-012, SC-001/002, #107)"`.
- [ ] T031a [US4] Implement [tests/phase2/test_librarian_induced_failures.py](tests/phase2/test_librarian_induced_failures.py) — induced-failure smoke test backing SC-007. Three scenarios in one module: (1) `test_backend_unreachable_fails_loud` (set `LLMXIVE_HTTP_TIMEOUT=0.001` for the duration of one librarian invocation; assert `outcome == "failed"` with non-empty `failure_reason` AND no silent success in run-log); (2) `test_doi_redirects_to_wrong_paper` (synthetic candidate whose DOI redirects to an unrelated paper; assert `verification_failures` includes a `reason: "title_mismatch"` entry); (3) `test_paywall_handled_as_partial` (synthetic 401 response on PDF download; assert citation appears in verified_citations with `summary_grounded_pdf: None` and the `verification_failures` list logs `paywall_partial`). Run + assert pass. Commit: `git add tests/phase2/test_librarian_induced_failures.py && git commit -m "spec-005: induced-failure smoke tests (SC-007 / Constitution V, #107)"`.

**Checkpoint**: Librarian works across all 8 default fields. Per-field manual audit verdicts captured.

---

## Phase 6: Rewire flesh_out + reference_validator + citation_resolver (FR-007/008/009)

**Goal**: Three production-code rewirings that consolidate duplicated lit-search/verification logic into the canonical librarian, satisfying Constitution Principle I.

**Note**: This phase is between US4 and US3 because US3's re-validation MUST exercise the rewired paths. Without these rewirings, US3's flesh_out re-runs would still call the old `lit_search` tool.

- [ ] T032 [P] Rewire `src/llmxive/agents/idea_lifecycle.py:173-177` (the `flesh_out` agent's lit_search call): replace `from agents.tools.lit_search import lit_search; papers = lit_search(query=query, max_results=8)` with a librarian invocation per quickstart.md Step 3a. Pass `idea_md_path=ctx.inputs[0]` so the librarian writes the Search trail subsection.
- [ ] T033 [P] Rewire `src/llmxive/agents/reference_validator.py`: replace inline title-token-overlap + URL-resolves logic with `from llmxive.librarian.verify import verify_citation`. Per quickstart.md Step 3b.
- [ ] T034 [P] Soft-deprecate `agents/tools/lit_search.py` per quickstart.md Step 3c. This is a "deprecated AND functional" pattern: (a) add a deprecation banner at the top of the file naming the librarian as the canonical replacement and pointing to `notes/2026-05-NN-spec-005-librarian-diagnostic.md`; AND (b) rewrite the `lit_search` function body as a thin wrapper that delegates to `LibrarianAgent.invoke`. Existing callers (the deprecated test paths from spec 003) keep working via delegation; new callers see the banner first. Both states are simultaneously true: the file is deprecated for new use AND functional for legacy callers.
- [ ] T035 [P] Convert `tests/phase1/citation_resolver.py` to a thin shim per quickstart.md Step 3d. `extract_citations` and `resolve_one` keep their signatures but delegate to `llmxive.librarian.verify`.
- [ ] T036 Run regression: `pytest tests/phase1/ tests/phase2/ -v --tb=short`. All spec-003 + spec-004 tests AND new spec-005 tests must pass. If any spec-003 test fails: the citation_resolver shim is incomplete — patch + re-run.
- [ ] T037 Commit rewirings: `git add src/llmxive/agents/idea_lifecycle.py src/llmxive/agents/reference_validator.py agents/tools/lit_search.py tests/phase1/citation_resolver.py && git commit -m "spec-005: rewire flesh_out + reference_validator + citation_resolver to librarian (FR-007/008/009, SC-011, #107)"`.

**Checkpoint**: Three duplicated implementations consolidated. All spec-003 + spec-004 + spec-005 tests pass.

---

## Phase 7: User Story 3 - Phase 1 re-validation on the carry-forward canonicals (Priority: P1)

**Goal**: Re-run `flesh_out` and `research_question_validator` in place on PROJ-261 + PROJ-262 under the new librarian-backed lit search. Document any verdict shift per `contracts/revalidation-runs.md`.

**Independent Test**: After the procedure runs on each canonical: state YAML transitions match expectations (validated → flesh_out_in_progress → flesh_out_complete → validated → project_initialized); `idea/<slug>.md` has a new `## Search trail` subsection; the validator's verdict is captured + compared to spec 003's verdict; a RevalidationResult is generated with judgment ∈ {`verified`, `shifted_legitimate`, `shifted_regressed`}.

### Implementation for User Story 3

For each of `PROJ-261-evaluating-the-impact-of-code-duplicatio` and `PROJ-262-predicting-molecular-dipole-moments-with`, follow `contracts/revalidation-runs.md` step-by-step:

- [X] T038 [P] [US3] Capture prior state of PROJ-261: `cp state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio.yaml /tmp/PROJ-261-prior.yaml && cp projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/idea/evaluating-the-impact-of-code-duplicatio.md /tmp/PROJ-261-idea-prior.md && sha256sum projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/.specify/memory/constitution.md > /tmp/PROJ-261-constitution-prior.sha`.
- [X] T039 [P] [US3] Capture prior state of PROJ-262: same pattern.
- [X] T040 [US3] Roll PROJ-261 state back to `flesh_out_in_progress` via a **deliberate manual edit** (NOT a normal pipeline transition — `project_initialized → flesh_out_in_progress` is not in `ALLOWED_TRANSITIONS` per `src/llmxive/agents/lifecycle.py`). Edit `state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio.yaml` changing `current_stage: project_initialized` → `current_stage: flesh_out_in_progress`. The unusual jump will appear in `state/projects/PROJ-261-….history.jsonl` as a backwards transition; this is the audit signature of a re-validation re-entry. Commit message MUST explicitly call this out: `git add state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio.yaml && git commit -m "spec-005: deliberate state edit — roll PROJ-261 back to flesh_out_in_progress for spec-005 librarian re-validation (manual; not a pipeline transition) (US3, #107)"`.
- [X] T041 [US3] Re-run flesh_out on PROJ-261 with librarian-backed lit search: `python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio --max-tasks 1`. Expect: state advances to `flesh_out_complete`; `idea/<slug>.md` now has `## Search trail` subsection; librarian + flesh_out run-log entries appended. Commit: `git add projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/ state/projects/ state/run-log/ state/librarian-cache/ && git commit -m "spec-005: flesh_out re-run on PROJ-261 with librarian (US3, #107)"`.
- [X] T042 [US3] Run validator on PROJ-261: `python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio --max-tasks 1`. Capture verdict; commit: `git add ... && git commit -m "spec-005: research_question_validator on PROJ-261 (US3, #107)"`.
- [X] T043 [US3] If verdict was `validated`: run project_initializer (no-op via skip-if-exists guard). Verify constitution sha256 unchanged: `sha256sum projects/PROJ-261-...-/.specify/memory/constitution.md` matches `/tmp/PROJ-261-constitution-prior.sha`. Commit.
- [X] T044 [US3] Repeat T040-T043 for PROJ-262: roll back, re-flesh_out, run validator, run project_initializer (no-op). Each step its own commit.
- [X] T045 [US3] Compute RevalidationResult records per data-model.md E9 — one per canonical. Render judgment per `contracts/revalidation-runs.md`: `verified` / `shifted_legitimate` / `shifted_regressed`. Capture each as YAML in `/tmp/PROJ-26{1,2}-revalidation.yaml` for inclusion in the diagnostic report § 5.
- [X] T046 [US3] If either canonical's judgment is `shifted_regressed`: investigate (the librarian's better citation evidence may legitimately invalidate a previously-validated question, OR the validator may be regressing on the new evidence shape). Either fix in this PR (with appropriate prompt-version bump per FR-020) OR document as deferred + revert the canonical to spec-004 final state. CRITICAL severity per `contracts/revalidation-runs.md` defect table.
- [X] T047 [US3] Implement [tests/phase2/test_librarian_revalidation.py](tests/phase2/test_librarian_revalidation.py) — orchestration test that programmatically asserts the revalidation procedure invariants: state YAML transitions match expectations, Search trail subsection present, run-log entries populated. Skip-marker if Dartmouth backend unavailable. Idempotent (uses tmp_path-rooted fake repo to test the orchestration logic without modifying the real canonicals).
- [X] T048 [US3] Run `pytest tests/phase2/test_librarian_revalidation.py -v`. Must pass.

**Checkpoint**: Phase 1 re-validation complete. Both canonicals have new librarian-verified citations + Search trails; verdicts captured + compared.

---

## Phase 8: User Story 5 - Diagnostic report (Priority: P1)

**Goal**: Author `notes/2026-05-NN-spec-005-librarian-diagnostic.md` aggregating all evidence per `contracts/`. Mirrors spec 003 + 004's 8-section structure.

### Implementation for User Story 5

- [ ] T049 [US5] Create `notes/2026-05-NN-spec-005-librarian-diagnostic.md` (substitute the actual completion date for NN). Write the frontmatter block: spec link, generation timestamp, branch, final commit, parent issue (#107), consolidates issue context.
- [ ] T050 [US5] Write § 1 Inputs: cross-domain test substrate (8 picked projects), carry-forward canonicals (PROJ-261 + PROJ-262), librarian prompt version (`1.0.0` initially; if T030/T046 bumped, the bumped version + reason).
- [ ] T051 [US5] Write § 2 Librarian invocations: every invocation across US1 smoke + US2 expansion + US4 cross-domain + US3 flesh_out re-runs, quoted as JSON (truncated >100 lines with `[truncated, sha256: <hash>]` markers).
- [ ] T052 [US5] Write § 3 Outputs: per cross-domain field, the per-citation manual-audit verdict from T029. Per re-validation, the new `idea/<slug>.md` content + the validator's `idea/research_question_validation.md`.
- [ ] T053 [US5] Write § 4 Cross-domain coverage table: 8 rows from T027-T029 with `field`, `project_id`, `sample_term`, `outcome`, `verified_count`, `expansion_fired`, `pdf_sample_size`, `manual_audit_verdict`, `notes`.
- [ ] T054 [US5] Write § 5 Phase 1 re-validation: the 2 RevalidationResult records from T045 verbatim (YAML); the full `git diff <prev>:idea.md <curr>:idea.md` per canonical; side-by-side comparison table (prior vs new on validator verdict, citation count, expansion-term count).
- [ ] T055 [US5] Write § 6 Defects table: every defect (P5-D##) with severity + file:line + status (`Fixed in <SHA>` / `Deferred to issue #<N>` / `Accepted (not addressed) — rationale: …`). CRITICAL/HIGH MUST have non-`Accepted` status per FR-015.
- [ ] T056 [US5] Write § 7 Per-issue acceptance summary: cite SC-001 through SC-012, mark each PASS/FAIL with rationale tied to a quoted artifact.
- [ ] T057 [US5] Write § 8 Recommendations: bulleted list of changes for the librarian going forward; follow-up issues opened/recommended; items deliberately accepted as-is.
- [ ] T058 [US5] Verify all artifact references in §§ 1-7 exist on disk; spot-check ≥3 random quotes against actual files.
- [ ] T059 [US5] Commit: `git add notes/2026-05-NN-spec-005-librarian-diagnostic.md && git commit -m "spec-005: diagnostic report (US5, FR-014, #107)"`.

**Checkpoint**: Single Markdown file at `notes/2026-05-NN-...` covers everything spec 005 produced + verdict per SC-NNN.

---

## Phase 9: User Story 6 - Carry-forward gate (Priority: P2)

**Goal**: Author `specs/005-librarian-agent/carry-forward.yaml` selecting which canonicals advance to spec 006 (Phase 3 — Specifier + Clarifier testing).

### Implementation for User Story 6

- [ ] T060 [US6] Decide carry-forward selection based on T045 RevalidationResult judgments. If both canonicals were `verified` or `shifted_legitimate`: both carry forward unchanged. If either was `shifted_regressed` and not yet fixed/accepted: document the downgrade. If `shifted_regressed` was reverted to spec-004 final state: name the spec-004 canonical state.
- [ ] T061 [US6] Author [specs/005-librarian-agent/carry-forward.yaml](specs/005-librarian-agent/carry-forward.yaml) per data-model.md E10. The schema extends spec 004's manifest with **two** new fields beyond the spec-004 baseline (don't forget either): (1) a new `librarian` row in each project's `agents_run` list with `iterations: <N>` and `final_run_log_path: <state/run-log/...>`, and (2) a new top-level field `revalidation_judgment: <verified | shifted_legitimate | shifted_regressed>` per project entry. Justification (≤200 words) per project covers: did flesh_out produce a Search trail? did validator hold? any caveats for spec 006.
- [ ] T062 [US6] Validate manifest manually against schema: every named project_id resolves to a real `projects/<id>/` dir at `current_stage: project_initialized` (or whatever final state); `final_commit` resolves; `librarian.iterations >= 1`.
- [ ] T063 [US6] Commit: `git add specs/005-librarian-agent/carry-forward.yaml && git commit -m "spec-005: carry-forward manifest names canonicals for spec 006 (US6, FR-018, #107)"`.

**Checkpoint**: Spec 006 can `cat specs/005-librarian-agent/carry-forward.yaml` and pick its substrate.

---

## Phase 10: Polish + close

- [ ] T064 Run full pytest regression: `pytest tests/phase1/ tests/phase2/ -v`. ALL must pass. Capture output for the diagnostic report.
- [ ] T065 Run lint: `ruff check src/llmxive/librarian/ src/llmxive/agents/librarian.py tests/phase2/`. Auto-fix any I001/UP errors per spec-004's pattern.
- [ ] T066 Update spec.md `**Status**` from `Draft` to `In Review` per spec-004's pattern (use the Python regex one-liner from spec 004 T067).
- [ ] T067 Update `tasks.md` so all 67 task checkboxes reflect their completion state (mark `[X]` for done, leave `[ ]` only for conditional tasks that didn't fire). Commit.
- [ ] T068 Push the feature branch: `git push -u origin 008-librarian-agent`.
- [ ] T069 Open PR: `gh pr create --base main --head 008-librarian-agent --title "Spec 005: librarian agent + Phase 1 re-validation" --body-file <(cat <<'EOF' ...full body per spec-004 pattern... EOF)`. Body includes summary, defect table, test plan, per-issue verdict.
- [ ] T070 Post a comment on tracker issue #107 with the PR URL + a short summary of what the librarian consolidates and what the re-validation found.
- [ ] T070a Add an FR-022 enforcement guardrail. Implement [tests/phase2/test_no_duplicate_lit_search.py](tests/phase2/test_no_duplicate_lit_search.py) — a regression test that greps the entire `src/llmxive/` and `agents/` trees (excluding `src/llmxive/librarian/` and the deprecated `agents/tools/lit_search.py`) for the strings `api.semanticscholar.org` AND `arxiv.org/api/query`. If both appear in any other file, the test fails with a message pointing to FR-022 + Constitution Principle I. This catches future PRs that re-introduce duplicate lit-search implementations.
- [ ] T071 [optional] Open a new agent-tracking issue for the librarian (analogous to issues #62/#63/#64 from spec 003 era) so its lifecycle is captured in the tracker. Label `pipeline-agent`.

**Checkpoint**: PR open. Spec 005 done, awaiting CI + review + merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup, T001-T003)**: No dependencies; preflight only
- **Phase 2 (Foundational, T004-T012)**: Depends on Phase 1. **BLOCKS US1-US6.**
- **Phase 3 (US1, T013-T019)**: Depends on Phase 2. P1 / MVP.
- **Phase 4 (US2, T020-T026)**: Depends on Phase 3 (US2 needs the search/verify modules from Phase 2 + the orchestration logic from US1).
- **Phase 5 (US4, T027-T031)**: Depends on Phase 4 (US4 invokes the full librarian including expansion).
- **Phase 6 (Rewirings, T032-T037)**: Depends on Phase 5 (rewirings expose the librarian to existing tests; need confidence the librarian works).
- **Phase 7 (US3 re-validation, T038-T048)**: Depends on Phase 6 (re-validation exercises the rewired flesh_out).
- **Phase 8 (US5 report, T049-T059)**: Depends on Phases 3-7 complete (report quotes their artifacts).
- **Phase 9 (US6 carry-forward, T060-T063)**: Depends on Phase 8 (selection driven by report's verdicts).
- **Phase 10 (Polish + close, T064-T071)**: Depends on Phase 9.

### User Story Dependencies

- **US1 (P1)**: After Phase 2; no inter-story dependencies.
- **US2 (P1)**: After US1; uses the same librarian orchestration logic.
- **US4 (P1)**: After US2; cross-domain tests need expansion to handle thin-result fields.
- **US3 (P1)**: After Phase 6 rewirings; must exercise librarian-backed flesh_out (not the old lit_search).
- **US5 (P1)**: After US1-US4 + Phase 6-7; quotes everything.
- **US6 (P2)**: After US3 + US5; selection driven by re-validation judgments + report verdicts.

### Within Each User Story

- Test files BEFORE the production code they exercise (TDD discipline applied to all new librarian modules per Constitution III).
- Models (search clients, verify helper, etc.) before services (LibrarianAgent class).
- Library before integrations (librarian sub-package before the rewirings).
- Unit tests before manual verification.
- Commit after each task or logical group; reference US + FR + #107 in messages.

### Parallel Opportunities

- T004-T008 (5 librarian sub-modules) — different files, no within-phase deps; fully parallel.
- T013-T016 (4 unit-test modules in US1) — different files; fully parallel.
- T020 + T024 (US2 expansion test + Search trail test) — parallel.
- T027 (US4 cross-domain) is parametrized over 8 fields; pytest-xdist can parallelize the 8 invocations.
- T032-T035 (Phase 6 rewirings) — 4 different files; fully parallel.
- T038 + T039 (snapshot prior state of both canonicals) — parallel.
- T041 + T044's flesh_out re-runs are sequential per canonical (orchestrator is single-project per invocation; Dartmouth rate-limits concurrent calls anyway).
- T049-T058 (report sections) — independent within the same file; can be drafted in any order, committed together at T059.
- T064 + T065 (test + lint) — parallel.

---

## Implementation Strategy

### MVP First (Phase 1+2+3 only)

1. T001-T003 preflight + scaffolding.
2. T004-T012 the 5 librarian sub-modules + agent class + prompt + registry.
3. T013-T019 US1 unit tests + smoke.
4. **STOP and VALIDATE**: invoke the librarian by hand (`python -c "from llmxive.agents.librarian import LibrarianAgent; ..."`); confirm verified citations come back. ~3 days of work.
5. If solid: continue to Phase 4-9.

### Incremental Delivery

- Phase 1+2 → librarian sub-package present (foundation for all future phase-tests)
- Phase 3 → MVP: librarian works against real APIs
- Phase 4 → multi-step expansion verified
- Phase 5 → cross-domain coverage proven
- Phase 6 → rewirings land; spec-003 + spec-004 tests still pass (Principle I satisfied structurally)
- Phase 7 → Phase 1 re-validation captures any verdict shifts
- Phase 8-9 → diagnostic + carry-forward
- Phase 10 → close

### Parallel Team Strategy (single-developer fallback)

Single-threaded execution is the expected primary path. Parallel opportunities are advisory. Estimated total wall-clock: ~5 days happy path; up to ~1 week with iteration.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks within the same phase
- [Story] label maps task to specific user story for traceability per `/speckit-tasks` rules
- Each user story can be independently demonstrated to a reviewer (per spec.md "Independent Test" sections)
- Tests in T013-T016, T020, T024, T027, T047 must pass BEFORE the commit they cover — verify failure path is detected (negative-control tests are part of each suite)
- Commit after each Phase checkpoint or logical group, per CLAUDE.md "frequent commits" guidance
- Stop at any checkpoint to validate; resume by re-reading the current Phase's task list
- Avoid: vague tasks (every task has concrete file path), same-file conflicts (P-marked tasks verified independent), cross-story dependencies that break independence
- Per the spec-004 in-place iteration convention: NO `-iterN` sibling directories; all re-validation happens in place on canonical paths
- The librarian's first version is `prompt_version: 1.0.0`; any iteration during testing bumps per FR-020 semver
- The diagnostic report is the single source of truth for "what spec 005 did" — every artifact, every verdict, every defect, every selection rationale lives in `notes/2026-05-NN-spec-005-librarian-diagnostic.md`
