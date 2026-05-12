---
description: "Task list — TheoremSearch backend for the librarian + mathematics as 9th default field (spec 006, amends spec 005)"
---

# Tasks: TheoremSearch backend for the librarian + mathematics as 9th default field

**Input**: Design documents from `specs/006-theoremsearch-backend/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)
**Branch**: `008-theoremsearch-backend` | **Tracking issue**: #113 (parent #111). Deferred sibling: #114 (Spec B).
**Type**: Amendment to spec 005 (the librarian agent) — extends an existing agent; no new agent.

**Tests**: Included — the spec requires them (FR-A02/A04/A11 reference test obligations; SC-A09 requires "all Phase 2 tests pass; lint clean"). Real-call tests are gated on `LLMXIVE_REAL_TESTS=1` + `DARTMOUTH_CHAT_API_KEY` (existing pattern); TheoremSearch real-API tests gated on network reachability — both skip cleanly when ungated.

**Organization**: Phase 1 Setup → Phase 2 Foundational (the field-list change — blocks US2's seed projects and is wired into US1's trigger) → Phase 3 US2 (`mathematics` as a first-class field + 5 seed projects) → Phase 4 US1 (TheoremSearch backend + math-classifier + wiring) → Phase 5 Polish (prompt bump, cache wipe, 9-field cross-domain re-run, PROJ-261/262 re-validation, docs, lint, commit/PR).

**Why US2 before US1**: US1's `field == "mathematics"` trigger and the cross-domain `mathematics` parametrization can't be exercised until `mathematics` is in the field lists AND ≥1 math project exists. US2 is the smaller story and a prerequisite, so it's MVP-first.

## Path Conventions

Single-project Python repo. New modules live inside the existing `src/llmxive/librarian/` package (alongside `search.py`, `verify.py`, `query_extractor.py`, `relevance_judge.py`). Tests in `tests/phase2/`. Prompts in `agents/prompts/`. Registry at `agents/registry.yaml`.

---

## Phase 1: Setup

**Purpose**: Confirm preconditions before any code change (Constitution Principle V — fail fast).

- [ ] T001 Preflight check (per quickstart.md §0): confirm TheoremSearch reachable (`curl -s -o /dev/null -w "%{http_code}" -X POST https://api.theoremsearch.com/search -H "Content-Type: application/json" -d '{"query":"composition series","limit":1}'` → expect 200), Dartmouth Chat key loadable (`python -c "from llmxive.credentials import load_dartmouth_key; assert load_dartmouth_key(prompt_if_missing=False)"`), Semantic Scholar key loadable, and `state/librarian-cache/` writable. Record results; abort if TheoremSearch or Dartmouth is unreachable (the implementation depends on both being available for the real-call tests + the cross-domain re-run).
- [ ] T002 Capture a real TheoremSearch `/search` response fixture: `POST https://api.theoremsearch.com/search` with `{"query":"sharp bound spectral gap random regular graphs","limit":8}`, save the raw JSON to `tests/phase2/fixtures/theoremsearch_search_response.json` (create the `fixtures/` dir if absent). Verify the saved JSON contains a mix of `paper.source == "arXiv"` hits (with versioned `paper_id` like `1306.5434v2`) and at least one non-arXiv hit if the query returns one (else add a second saved fixture from `{"query":"composition series","limit":3}` which is known to return ProofWiki hits — name it `theoremsearch_proofwiki_response.json`). This fixture is the basis for the offline parser tests in T020/T021.

---

## Phase 2: Foundational — `mathematics` in the field lists

**Purpose**: Add `mathematics` to every place the librarian's default-field list lives. This BLOCKS US2 (the seed math projects need `mathematics` to be a valid field) and is consumed by US1 (the `field == "mathematics"` trigger). Per the plan's structure section, the field list currently lives in TWO places — both must be updated consistently; do NOT introduce a third copy.

⚠️ **No story label** — foundational.

- [ ] T003 Add `"mathematics"` to `default_fields` in `src/llmxive/cli.py` (around line 208-212), inserted alphabetically: after `"materials science"`, before `"neuroscience"`. (List becomes 9 entries.)
- [ ] T004 [P] Add `"mathematics"` to `DEFAULT_FIELDS` in `tests/phase2/test_librarian_cross_domain.py` (around line 43-52), same alphabetical position. (List becomes 9 entries — the `@pytest.mark.parametrize("field", DEFAULT_FIELDS)` automatically gives `test_librarian_field_coverage` a `mathematics` case; the existing "no brainstormed project for field=X" skip handles the not-yet-brainstormed window — no new skip logic needed.)
- [ ] T005 [P] Add `mathematics` to the field-example list in the Inputs section of `agents/prompts/brainstorm.md` (it's prose: `e.g., \`biology\`, \`mathematics\`, \`materials-science\`, \`psychology\`, \`chemistry\``).
- [ ] T006 Sanity check: `grep -rn '"mathematics"\|mathematics' src/llmxive/cli.py tests/phase2/test_librarian_cross_domain.py agents/prompts/brainstorm.md` shows the addition in all three; `python -c "import ast; m=ast.parse(open('src/llmxive/cli.py').read()); print('cli ok')"` parses; `python -m pytest tests/phase2/test_librarian_cross_domain.py --collect-only -q` shows a `mathematics` parametrization. (No behavior change yet — TheoremSearch isn't wired in until Phase 4 — so the `mathematics` cross-domain case will *skip* with "no brainstormed project" until Phase 3 brainstorms one.)

**Checkpoint**: `mathematics` is a recognized default field everywhere; nothing else changed yet.

---

## Phase 3: User Story 2 — `mathematics` is a first-class default field (Priority: P1)

**Goal**: 5 seed math-theory projects exist so the cross-domain `mathematics` parametrization has real math content to run against.

**Independent test**: `grep -l 'field: mathematics' state/projects/PROJ-*.yaml | wc -l` → ≥5; the cross-domain test's `mathematics` parametrization picks the most-recently-brainstormed math project (existing per-field selection logic) and (once Phase 4 wires TheoremSearch) runs the librarian on it. (Before Phase 4, the `mathematics` case still skips — that's fine; this story's deliverable is the projects existing + the field being recognized.)

**Depends on**: Phase 2 (`mathematics` must be a valid field before the brainstorm step runs, so the seed projects carry `field: mathematics`).

- [ ] T007 [US2] Brainstorm 5 seed math-theory projects via the existing brainstorm agent with `field=mathematics` (use the project's standard brainstorm invocation — e.g. via `src/llmxive/cli.py` or `run_one_step` on a fresh project). Each produces a `projects/PROJ-###-<slug>/idea/<slug>.md` + `state/projects/PROJ-###-<slug>.yaml` with `field: mathematics`. Aim for genuinely theorem-shaped questions (the kind TheoremSearch helps with) — e.g. bounds/inequalities, structural classifications, existence/uniqueness results — not historiography or pure-software questions.
- [ ] T008 [US2] Verify: `grep -l 'field: mathematics' state/projects/PROJ-*.yaml | wc -l` → ≥5 (SC-A06); spot-check that each seed project's `idea/<slug>.md` has a research question and the YAML has `field: mathematics` and `current_stage: brainstormed` (or further); `git add projects/PROJ-*math*/  state/projects/PROJ-*.yaml  state/run-log/` and commit the seed projects (`spec-006: brainstorm 5 seed math projects (US2, #113)`).
- [ ] T009 [US2] Confirm the cross-domain test's `mathematics` parametrization now selects a math project (not skip): `python -m pytest tests/phase2/test_librarian_cross_domain.py -k mathematics --collect-only -q` shows it collected; running it will still fail/error until Phase 4 (no TheoremSearch + the librarian's existing SS+arXiv path may or may not return ≥1 on a math question — that's expected; don't fix it here). (No commit — this is just a confirmation step.)

**Checkpoint**: 5 math projects exist; `mathematics` is a fully first-class field. US2 done.

---

## Phase 4: User Story 1 — Math-theory question gets theorem-granularity citation discovery (Priority: P1)

**Goal**: The librarian queries TheoremSearch (always for `field == "mathematics"`, classifier-gated otherwise), resolves arXiv-sourced theorem hits to `Candidate`s, runs them through the unchanged verification chain, and records a `math_classifier` audit object in the output JSON.

**Independent test**: Invoke the librarian with `field="mathematics"` on a real math-theory question whose answer is a known arXiv-paper theorem → ≥1 verified citation with `verification_log.backend == "theoremsearch"`, resolving arXiv ID, title-overlap ≥0.7, summary-grounding pass, and `math_classifier == {"invoked": false, "verdict": null, "error": null}`. Invoke with a theorem-shaped question on a non-math project → classifier returns `true`, TheoremSearch fires. Invoke with a plainly-non-theorem question → classifier returns `false`, TheoremSearch not queried.

**Depends on**: Phase 2 (the `field == "mathematics"` trigger needs `mathematics` recognized) + Phase 3 (the cross-domain `mathematics` case needs a math project) for the *integration* test; the unit/parser tests (T020-T024) depend only on Phase 1's fixture.

### Tests for US1 (write before / alongside the implementation — TDD where practical)

- [ ] T020 [P] [US1] `tests/phase2/test_theoremsearch.py` — parser tests against `tests/phase2/fixtures/theoremsearch_search_response.json` (and the ProofWiki fixture): a `/search` response with mixed arXiv + ProofWiki hits → `TheoremSearchClient` (mocked HTTP returning the fixture) yields only the arXiv hits as `Candidate(backend="theoremsearch", primary_pointer=<normalized arXiv id>, claimed_title/authors/year/abstract from a stubbed `ArxivClient.get_by_id`, claimed_venue="arXiv")`; ProofWiki hits skipped; `1306.5434v2` → `primary_pointer` is the resolver-normalized short id; two hits → same paper → one `Candidate`; a hit whose stubbed `get_by_id` returns `None` → that hit produces no candidate (others still do). Per `contracts/theoremsearch-client.md` test obligations.
- [ ] T021 [P] [US1] `tests/phase2/test_theoremsearch.py` (same file, more tests) — failure handling: a mocked HTTP layer returning a non-2xx / non-JSON / timeout → `TheoremSearchClient.search()` raises `TransientBackendError` (not `PermanentBackendError`); the `_theoremsearch_candidates(...)` wrapper catches it and returns `[]`. Plus a real-API smoke test gated on network reachability: `TheoremSearchClient().search("sharp bound spectral gap random regular graphs", limit=5)` → ≥1 `Candidate` with `backend == "theoremsearch"` and a resolving arXiv ID (skip with a documented reason if the API is unreachable).
- [ ] T022 [P] [US1] `tests/phase2/test_math_classifier.py` — parser tests: `classify(...)`-style first-line parsing (`"YES\n..."` → `verdict True`; `"NO\n..."` → `verdict False`; `"maybe?"` unparseable → `verdict False, error None` + warning logged); the `MathClassifierResult` shape (`invoked / verdict / error / cached`). Per `contracts/math-classifier.md` test obligations. (Use a recording/monkeypatched backend so no real LLM call.)
- [ ] T023 [P] [US1] `tests/phase2/test_math_classifier.py` (same file) — cache behavior: two `classify(...)` calls with the same `(project_id, librarian_prompt_version)` → 2nd returns `cached=True`, no LLM call (assert via recording backend / cache-file inspection); same `project_id` + different `librarian_prompt_version` → 2nd is a miss (re-classifies); `project_id=None` → no cache read/write, classifier runs every call; a malformed `state/librarian-cache/math-classifier-verdicts.json` → treated as `{}` (logged), overwritten on next write. Backend-failure path: `classify(...)` with a backend that raises → `MathClassifierResult(invoked=True, verdict=False, error="<msg>", cached=False)`, stderr diagnostic emitted, no exception propagated, cache NOT written.
- [ ] T024 [P] [US1] `tests/phase2/test_math_classifier.py` (same file) — real-LLM smoke gated on `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1`: a plainly-math question ("what is the tightest known concentration inequality for sums of bounded independent random variables, and in which paper is it proved?") → `verdict True`; a plainly-non-math question ("how does code-clone density correlate with LLM perplexity on Python?") → `verdict False`.

### Implementation for US1

- [ ] T025 [US1] `src/llmxive/librarian/theoremsearch.py` (NEW) — `TheoremSearchClient` per `contracts/theoremsearch-client.md`: `API_URL = "https://api.theoremsearch.com/search"`; `__init__(self, *, min_interval_seconds=2.0, arxiv_client=None)` with a `threading.Lock` + last-call-timestamp rate limiter (same pattern as `ArxivClient._wait_for_slot`); `search(self, term, *, limit=10) -> list[Candidate]`: POST `{"query": term, "limit": limit}` with a 30s timeout → on HTTP error / network error / timeout / non-JSON → `raise TransientBackendError(...)`; parse `["theorems"]` (missing/not-a-list → `TransientBackendError`); sort by `score` desc; for each hit with `paper.source == "arXiv"` and a valid arXiv-ID `paper.paper_id`: `arxiv_id = re.sub(r"v\d+$", "", paper_id)`, `cand = arxiv_client.get_by_id(arxiv_id)`; if `None` → skip (log warning); else `cand = dataclasses.replace(cand, backend="theoremsearch")`, append (dedup by `primary_pointer` within this call); return the list. Use the existing `TransientBackendError` from `llmxive.backends.base` (or whatever the codebase uses).
- [ ] T026 [P] [US1] `agents/prompts/math_classifier.md` (NEW) — system+user prompt per `contracts/math-classifier.md` / quickstart §4: system message instructs the model to judge whether a research question is a pure-mathematics theorem/proof/formal-structure question (the kind where searching theorem statements helps), and to reply `YES` or `NO` on the first line then a one-sentence rationale; user message carries the question + idea-body excerpt. Mirror the format of `agents/prompts/librarian.md` / the query-extractor prompt for consistency.
- [ ] T027 [US1] `src/llmxive/librarian/math_classifier.py` (NEW) — per `contracts/math-classifier.md`: `MathClassifierResult` dataclass (`invoked / verdict / error / cached`); `classify(question, idea_body_excerpt, *, project_id, librarian_prompt_version, model, default_backend, fallback_backends, repo_root=None) -> MathClassifierResult`: cache check at `state/librarian-cache/math-classifier-verdicts.json` keyed `f"{project_id}::{librarian_prompt_version}"` (only if `project_id` is not None; absent/malformed file → `{}`, logged) → hit → return `cached=True` with no LLM call; else render `agents/prompts/math_classifier.md`, call via `chat_with_fallback` (same plumbing `query_extractor` uses), parse first-line `YES`/`NO` → `verdict` (unparseable → `verdict=False, error=None` + warning); on backend exception → `verdict=False, error="<msg>"` + loud stderr diagnostic `[math-classifier] backend failure; treating question as non-math (TheoremSearch skipped): <error>` + do NOT re-raise; on fresh successful verdict with a `project_id` → write the cache entry (`{"verdict": ..., "classified_at": "<ISO-8601 UTC>"}`); return the `MathClassifierResult`. Plus `is_math_theory_question(...) -> bool` thin wrapper returning `classify(...).verdict or False`.
- [ ] T028 [US1] `src/llmxive/agents/librarian.py` (MODIFIED) — wire the math branch into `LibrarianAgent.invoke()` per `research.md` D4 + quickstart §5: (a) add `project_id: str | None = None` to the `invoke()` signature (after the existing kwargs, before the clients); (b) after the existing extracted-query search loop (which builds `candidates` + `merged_pointers`), before `verified, failures = _verify_each(candidates, query=term)`, add: `math_audit = {"invoked": False, "verdict": None, "error": None}`; `ts_hits: list[Candidate] = []`; `if field == "mathematics": ts_hits = _theoremsearch_candidates(term, arxiv_client=arxiv_client)` `elif (...): verdict, math_audit = _maybe_math_question(term, idea_body_excerpt, project_id, prompt_ver, self.entry, repo_root); if verdict: ts_hits = _theoremsearch_candidates(term, arxiv_client=arxiv_client)`; then `for c in ts_hits: if c.primary_pointer not in merged_pointers: merged_pointers.add(c.primary_pointer); candidates.append(c)`; (c) add module-level helpers `_theoremsearch_candidates(term, *, arxiv_client) -> list[Candidate]` (wraps `TheoremSearchClient(arxiv_client=arxiv_client).search(term)`, catches `TransientBackendError` → `LOGGER.warning(...)` + `return []`) and `_maybe_math_question(term, idea_body_excerpt, project_id, prompt_ver, entry, repo_root) -> tuple[bool, dict]` (wraps `math_classifier.classify(...)`, returns `(bool(res.verdict), {"invoked": res.invoked, "verdict": res.verdict, "error": res.error})`); (d) add `math_classifier: dict[str, Any] = dataclasses.field(default_factory=dict)` to `LibrarianResult`, `"math_classifier": self.math_classifier` to `to_dict()`, and pass `math_classifier=math_audit` into the `LibrarianResult(...)` constructor (parallel to `relevance_judge=...`); (e) imports: `from llmxive.librarian import math_classifier` (module) and `from llmxive.librarian.theoremsearch import TheoremSearchClient`.
- [ ] T029 [P] [US1] `src/llmxive/agents/idea_lifecycle.py` (MODIFIED) — in `flesh_out`'s call to `librarian.invoke(...)`, pass `project_id=<the project's id>` (flesh_out already has it — the project context it's building the idea for). Per quickstart §5.
- [ ] T030 [P] [US1] `src/llmxive/agents/reference_validator.py` (MODIFIED) — in its call(s) to `librarian.invoke(...)` (or `librarian/verify.py` if that's the path), pass `project_id=...` if a project context is available; if `reference_validator` doesn't have a project_id in scope, leave the call as-is (the `None` default means the classifier just won't cache for that path — acceptable). Confirm by reading the file which case applies; document the choice in the commit message.
- [ ] T031 [US1] Run the US1 unit + parser + gated-real tests: `python -m pytest tests/phase2/test_theoremsearch.py tests/phase2/test_math_classifier.py -v` (offline tests must pass); then with `LLMXIVE_REAL_TESTS=1` + `DARTMOUTH_CHAT_API_KEY` exported, `python -m pytest tests/phase2/test_theoremsearch.py::test_real_api_smoke tests/phase2/test_math_classifier.py::test_real_llm_smoke -v` (gated smokes must pass when network/key available, skip cleanly otherwise). Fix any failures in the implementation (not the tests). Commit: `spec-006: TheoremSearch backend + math-classifier + librarian wiring (US1, #113)`.

**Checkpoint**: TheoremSearch is a working 3rd backend; the math-classifier gates it on non-math fields; the `math_classifier` audit object appears in the librarian's output JSON. US1's *unit* behavior is verified; the *integration* (cross-domain + re-validation) verification is in Phase 5.

---

## Phase 5: Polish & cross-cutting — prompt bump, cache wipe, re-runs, docs, lint, PR

**Purpose**: Bump the librarian prompt version (the classifier is a new LLM call), invalidate the result cache, re-run the full regression suite (9-field cross-domain + PROJ-261/262 re-validation) to confirm no regression on the 8 existing fields and on the carry-forward canonicals, update the docs, lint, and open the PR.

⚠️ **No story label** — cross-cutting.

- [ ] T032 Bump the librarian `prompt_version` `1.5.0` → `1.6.0` in `agents/registry.yaml`'s librarian entry; update the entry's `purpose`/comment to say "3 backends (Semantic Scholar + arXiv + TheoremSearch) + an LLM math-classifier for non-math fields" (keep the `purpose` under the 200-char Pydantic limit — trim if needed). (FR-A12, FR-A13.)
- [ ] T033 Full Phase 2 regression (no cross-domain — that's the slow one): `python -m pytest tests/phase2/ -q --ignore=tests/phase2/test_librarian_cross_domain.py` → ALL must pass (includes the new `test_theoremsearch.py` + `test_math_classifier.py`). Capture the count for the diagnostic. (SC-A09.)
- [ ] T034 Lint: `ruff check src/llmxive/librarian/ src/llmxive/agents/librarian.py tests/phase2/` → clean (auto-fix import-order / unicode-comment issues per the existing pattern). (SC-A09.)
- [ ] T035 Cache wipe + 9-field cross-domain re-run: `rm -f state/librarian-cache/*.json` (keeps the dir; `math-classifier-verdicts.json` will be recreated); then with `LLMXIVE_REAL_TESTS=1` + `DARTMOUTH_CHAT_API_KEY` + `SEMANTIC_SCHOLAR_API_KEY` exported, `python -m pytest tests/phase2/test_librarian_cross_domain.py -v` (~3h — run in background) → expect 9/9 PASS (or the `mathematics` case skips cleanly if, somehow, no math project ended up brainstormed — but Phase 3 created 5, so it should run). Assert: the 8 pre-existing fields still pass (no regression — SC-A08); every result has a `math_classifier` key of the right shape; `field == "mathematics"` → `{"invoked": false, "verdict": null, "error": null}`. Save the per-field results for the diagnostic. (FR-A12, SC-A07, SC-A08.)
- [ ] T036 PROJ-261 + PROJ-262 re-validation under v1.6.0 (the standard post-prompt-bump regression check — roll each back to `flesh_out_in_progress`, re-run flesh_out → research_question_validator → project_initializer; use the existing re-validation procedure from spec 005). Expect `judgment: verified` for both (no regression on the carry-forward canonicals); confirm their `math_classifier` audit object is `{"invoked": true, "verdict": false, "error": null}` (they're CS/chemistry questions — classifier correctly says non-math; zero `backend == "theoremsearch"` citations). (SC-A08.)
- [ ] T037 Manual output inspection (per quickstart §9, SC-A01/A02/A03): pick one Phase-3 math project, invoke the librarian on its research question with `field="mathematics"`, confirm ≥1 verified citation has `verification_log.backend == "theoremsearch"` and a resolving arXiv ID and `math_classifier == {"invoked": false, ...}`; confirm no ProofWiki/Stacks-Project entries appear in `verified_citations`; (optionally) construct a theorem-shaped question on a non-math project and confirm `math_classifier == {"invoked": true, "verdict": true, ...}` and TheoremSearch contributed candidates. Record the inspection in the diagnostic update (T038).
- [ ] T038 [P] Doc updates (FR-A13): (a) append a "spec-006 amendment: TheoremSearch backend + mathematics field" section to `notes/2026-05-07-spec-005-librarian-diagnostic.md` noting the 3rd backend, the math-classifier, the prompt bump 1.5.0→1.6.0, the new `math_classifier` audit field, the 9-field cross-domain re-run results, the PROJ-261/262 re-validation results, and the manual-inspection findings; (b) in `specs/005-librarian-agent/spec.md`, append "→ done in spec 006 (#113): added TheoremSearch" to the Q1 clarification line ("future spec may expand the backend list"); (c) update `specs/006-theoremsearch-backend/checklists/requirements.md` Feature Readiness checkboxes if any flipped.
- [ ] T039 [P] Tick all completed checkboxes in this `specs/006-theoremsearch-backend/tasks.md`; commit the doc + tasks updates (`spec-006: prompt bump 1.6.0 + diagnostic update + tasks tick (#113)`).
- [ ] T040 Push `008-theoremsearch-backend` and open a PR against `main` (`gh pr create --base main --head 008-theoremsearch-backend --title "Spec 006: TheoremSearch backend for the librarian + mathematics as 9th default field" --body-file <(...)` — body summarizing: the 3rd backend, the math-classifier with per-project verdict cache, `mathematics` as the 9th field + 5 seed projects, the `math_classifier` audit object, the prompt bump 1.5.0→1.6.0, the test plan, the 9-field cross-domain + PROJ-261/262 re-validation results, the SC-A01..A09 verdicts, and that #114 (Spec B — theorem-statement artifacts) is the deferred follow-up). Wait for CI (`real-call` workflow) to pass. Post the PR URL on issue #113; update the umbrella issue #111.

**Checkpoint**: PR open, CI green. Spec 006 done, awaiting review + merge.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup, T001-T002)**: no dependencies; preflight + fixture capture.
- **Phase 2 (Foundational, T003-T006)**: depends on Phase 1. **BLOCKS Phase 3** (seed projects need `mathematics` valid) and feeds Phase 4 (the `field == "mathematics"` trigger).
- **Phase 3 (US2, T007-T009)**: depends on Phase 2.
- **Phase 4 (US1, T020-T031)**: the *unit/parser* tests (T020-T024) depend only on Phase 1's fixture; the implementation (T025-T030) depends on Phase 2 (for the trigger constant); the *integration* verification (T031's gated smokes, and Phase 5's cross-domain) depends on Phase 3 (a math project must exist).
- **Phase 5 (Polish, T032-T040)**: depends on Phases 3 + 4 complete.

### Story dependencies

- **US2 (P1)**: after Phase 2. Standalone MVP — "math is a first-class field, 5 seed projects exist."
- **US1 (P1)**: unit behavior is independent (depends only on the Phase 1 fixture + Phase 2 trigger constant); the `mathematics`-trigger *integration* test needs US2's seed projects. So: implement US1's code + unit tests in parallel with US2's brainstorm, but run the cross-domain `mathematics` parametrization (Phase 5) only after both.

### Within-phase parallelism

- T004 ∥ T005 (different files: the test file vs the brainstorm prompt) — both after T003.
- T020 ∥ T021 ∥ T022 ∥ T023 ∥ T024 (the test files for US1 — `test_theoremsearch.py` for T020/T021, `test_math_classifier.py` for T022/T023/T024 — note T021 appends to the same file as T020 so they're sequential *within* that file but the two files are parallel; in practice: do T020+T021 together, T022+T023+T024 together, and those two groups in parallel).
- T026 ∥ T025 (the math-classifier prompt vs the TheoremSearch client — different files, no dependency).
- T029 ∥ T030 (flesh_out vs reference_validator — different files) — both after T028.
- T038 ∥ T039 (diagnostic/spec-005 docs vs this tasks.md) — both after T032-T037.

### Critical path

T001 → T002 → T003 → (T004 ∥ T005) → T006 → T007 → T008 → T025 → T027 → T028 → T031 → T032 → T033 → T034 → T035 → T036 → T037 → T038/T039 → T040.

---

## Implementation Strategy

**MVP-first**: Phase 2 + Phase 3 (US2) alone is a shippable increment — `mathematics` becomes a first-class field with 5 seed projects, even before TheoremSearch exists. But the *valuable* deliverable is US1 (theorem-granularity discovery), so the realistic MVP is **Phases 1-4** (US2 + US1 code + US1 unit tests), with Phase 5's heavy re-runs as the "ship it" gate.

**Incremental delivery within Phase 4**: T025 (TheoremSearch client) + T020/T021 (its tests) can land and pass independently of the math-classifier; T026/T027 (classifier + prompt) + T022-T024 (its tests) likewise; T028 (the wiring) is where they meet — but each half is testable in isolation first, then T028 stitches them in.

**Risk notes**:
- TheoremSearch is a small academic project (no SLA) — T025's `TransientBackendError`-on-failure + the librarian's fall-through (T028's `_theoremsearch_candidates` catch) is the mitigation; the gated real-API test (T021) skips cleanly if it's down.
- The math-classifier is non-deterministic (temperature > 0 — issue #112) — the per-project verdict cache (T023, T027) freezes a project's verdict for a given `prompt_version`, and fail-open-to-`false` means a flaky run just skips TheoremSearch (SS+arXiv still cover the question). Don't try to make T024's real-LLM smoke deterministic; the questions chosen are unambiguous enough that a single call should classify correctly, and the test tolerates a backend-failure verdict-`null` outcome.
- The 9-field cross-domain re-run (T035) takes ~3h — run it in the background; the rest of Phase 5's doc/lint work proceeds in parallel.

## Notes

- Tasks reference exact files from the plan's Project Structure section. New modules go inside `src/llmxive/librarian/` (not a new top-level tree). No new agent class.
- The `prompt_version` bump (1.5.0→1.6.0) is mandatory (FR-A12) because the classifier is a new LLM call — it invalidates the result cache, so the cross-domain + re-validation re-run is the standard regression check.
- The seed-math-project step (T007) MUST run after the field-list change (T003-T005) so the projects carry `field: mathematics` — this is the one hard ordering constraint flagged in the plan's "Notes."
- Spec B (#114 — theorem-statement artifacts, non-arXiv sources, the `theorem_searcher` agent) is explicitly out of scope here.
