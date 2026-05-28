# Tasks: Pipeline-Wide Convergence Protocol + Recursive Summarizer + Review-Model Overhaul

**Input**: Design documents from `specs/015-pipeline-convergence-protocol/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: INCLUDED — the spec mandates TDD, real-call testing (Const. III), and manual QC (FR-046). Real-model tests run under `LLMXIVE_REAL_TESTS=1`.

**Organization**: grouped by user story. Phases are ordered by the dependency chain in plan.md (summarizer first; calibration/e2e last). All user stories except US7 are P1; US7 is P2.

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: parallelizable (different files, no incomplete dependency)
- **[US#]**: user-story phase tasks only (Setup/Foundational/Polish have no label)

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create new package skeletons with `__init__.py`: `src/llmxive/tools/` (ensure exists), `src/llmxive/convergence/` (`__init__,types,engine,kickback,triage,reviewspecs`), `src/llmxive/calibration/` (`__init__,injectors,differential,domains`), and `agents/prompts/panels/` directory
- [X] T002 Create `specs/015-pipeline-convergence-protocol/STATUS.md` living progress doc (FR-052): per-workstream status table with direct file references, updated as work proceeds
- [X] T003 [P] Add `AWAITING_PUBLICATION_SIGNOFF` to the `Stage` enum in `src/llmxive/types.py`; add a per-round wall-clock budget constant to `src/llmxive/config.py` (point-threshold removal happens in US3)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: blocks all user stories.

- [X] T004 Implement all convergence pydantic models (Severity, Concern, ConcernResponse, Verdict, ProgressRecord, ConvergenceResult, ReviewSpec, KickbackRecord, TriageRecord) per data-model.md in `src/llmxive/convergence/types.py`
- [X] T005 [P] Implement `Severity` ordering + back-compat mapping from the existing `ActionItem.severity` (`writing|science|fatal`) in `src/llmxive/convergence/types.py`
- [X] T006 [P] Contract test: schema validation + Severity ordering for all convergence models in `tests/contract/test_convergence_types.py`
- [X] T007 Constitution amendment: rewrite the point-based "Review thresholds" clause in `.specify/memory/constitution.md` to convergence-based unanimous-acceptance AND encode the new convergence principle (FR-053: every step producing reviewable work runs identify→revise→re-review with its panel; 3-round non-convergence kicks the project back with full provenance); bump version (MINOR), add a Sync Impact Report, update the README cross-link

**Checkpoint**: foundation ready.

---

## Phase 3: User Story 1 — Context-safe summarizer (Priority: P1) 🎯 MVP — validated FIRST

**Goal**: `summarize`/`desummarize` inode-table primitive that never silently drops a check-critical element.
**Independent Test**: round-trip real over-budget artifacts under each preservation contract; 100% verbatim recovery of URLs/DOIs/ids/numbers, no element cut mid-token, same reviewer verdicts on reduced vs full form.

### Tests (write FIRST, must fail)

- [X] T008 [P] [US1] Unit edge-case tests (all 7: atomic-unit splitting, cross-chunk refs, cross-chunk logic, numbers, ordering, output cut-off, recursion-loss) in `tests/unit/test_summarize_edge_cases.py`
- [X] T009 [P] [US1] Real-call fidelity test (verbatim recovery + same critical verdicts on reduced vs full) in `tests/real_call/test_summarize_fidelity.py`
- [X] T010 [P] [US1] Contract test for `SummaryManifest`/`SummaryEntry` + no-dangling-pointer invariant in `tests/contract/test_summary_manifest.py`

### Implementation

- [X] T011 [US1] Implement `estimate_tokens` + model→budget map (qwen→32768, completion headroom) in `src/llmxive/tools/summarize.py`
- [X] T012 [US1] Implement deterministic extraction of check-critical elements (URLs/DOIs/arXiv-ids/citation-keys/FR-SC-task-ids/numbers) in `src/llmxive/tools/summarize.py`
- [X] T013 [US1] Implement boundary-aware chunking (generalize `paper_reviewer._chunk_corpus`) in `src/llmxive/tools/summarize.py`
- [X] T014 [US1] Implement on-disk inode-table manifest writer (`SummaryManifest`/`SummaryEntry`, content files, nested pointers) in `src/llmxive/tools/summarize.py`
- [X] T015 [US1] Implement `summarize()` (fit→verbatim; overflow→recursive pointer hierarchy carrying criticals verbatim at every level; goal-targeted prose summary reusing the cached chunk call) in `src/llmxive/tools/summarize.py`
- [X] T016 [US1] Implement `desummarize()` (recursive pointer resolution, `want` filter, depth cap, no dangling refs) in `src/llmxive/tools/summarize.py`
- [X] T017 [US1] Re-point `paper_reviewer._build_corpus_with_summaries` to call `tools/summarize`; DELETE the forked single-pass logic (SSoT, Const. I) in `src/llmxive/agents/paper_reviewer.py`
- [X] T018 [US1] Run edge-case + real-call fidelity tests with real qwen; confirm zero critical-element loss; update STATUS.md

**Checkpoint**: summarizer trusted — downstream overflow handling unblocked.

---

## Phase 4: User Story 2 — Convergence engine (Priority: P1)

**Goal**: generic identify→revise→re-review engine + adaptive kickback + honest reporting.
**Independent Test**: drive one step (Tasks) through the engine; structured R1 concerns, per-concern R2 change-log, anchored R3, converge-or-kickback, `converged` flag matches reality.

### Tests (write FIRST)

- [X] T019 [P] [US2] Unit tests for the round loop (R1/R2/R3, 3-round cap, honest `converged`, stale-verdict + self-review detection, per-round budget) in `tests/unit/test_convergence_engine.py`
- [X] T020 [P] [US2] Unit tests for kickback routing (worst-severity→stage, full-provenance record) in `tests/unit/test_kickback.py`
- [ ] T021 [P] [US2] Integration test: single-step convergence on a real project (Tasks step) in `tests/integration/test_convergence_tasks_step.py`

### Implementation

- [X] T022 [US2] Implement `Reviewer`/`Reviser` Protocols + adapters wrapping existing agents (8-panel, 12-panel, speckit revisers) in `src/llmxive/convergence/engine.py`
- [X] T023 [US2] Implement `run_convergence` round loop (R1→R2→R3, per-round budget, route overflow inputs through `summarize`, constitution input) in `src/llmxive/convergence/engine.py`
- [X] T024 [US2] Implement unanimous-accept test + honest `ConvergenceResult` + per-round inspection record & run-log entry in `src/llmxive/convergence/engine.py`
- [X] T025 [US2] Implement stale-verdict detection + self-review prevention (fix the `_produced_by` stub at `advancement.py:177`) in `src/llmxive/convergence/engine.py` and `src/llmxive/agents/advancement.py`
- [X] T026 [US2] Implement `route_kickback` (adaptive severity→stage, `KickbackRecord` with unresolved concerns + artifact/review links + plain-language reason) AND emit a `ProgressRecord` per kickback so non-improving cycles are inspectable (FR-017) in `src/llmxive/convergence/kickback.py`
- [ ] T027 [US2] Refactor the tasker Mode-A/Mode-B analyze loop INTO the engine (Mode-A=authoring, Mode-B=reviser with change-log) in `src/llmxive/speckit/tasks_cmd.py`
- [X] T028 [US2] Verify honest reporting: a non-converging step records `converged:false` + a kickback (no masked "passed"); confirm via test; update STATUS.md

**Checkpoint**: engine usable by every step.

---

## Phase 5: User Story 8 — Audit bug fixes (Priority: P1)

**Goal**: fix all 10 audit bugs + arXiv resilience + the manual DOI sign-off gate (several unblock US4/US6).
**Independent Test**: per bug, direct code inspection + a real run shows it fixed.

### Tests (write FIRST)

- [X] T029 [P] [US8] Integration tests asserting each bug is fixed (publisher invoked at `paper_accepted`; research implementer uses a research prompt; no `PAPER_ACCEPT_THRESHOLD`/points read; dead escalations now branch; prompt input/stage drift resolved) in `tests/integration/test_audit_bugfixes.py`

### Implementation

- [X] T030 [P] [US8] Author a real research-code implementer prompt `agents/prompts/implementer_research.md`; point the research implementer at it (registry + stop hardcoding the LaTeX prompt) in `src/llmxive/speckit/implement_cmd.py`
- [X] T031 [P] [US8] Fix dead `ANALYZE_SYSTEM_PROMPT_PATH`; give the paper analyze loop a paper-appropriate prompt; pass `project_dir` so comments are injected in the live loop in `src/llmxive/speckit/analyze_cmd.py`
- [X] T032 [P] [US8] Fix dead escalation paths (`clarifier.attempts_so_far` no longer hardcoded 0; `paper_clarifier` branches on `escalate`) in `src/llmxive/speckit/clarify_cmd.py` and `paper_clarify_cmd.py`
- [X] T033 [P] [US8] Resolve `code_summary`/`data_summary` prompt input drift (supply or remove) and stage-header drift in `agents/prompts/paper_specifier.md`, `paper_clarifier.md`, and other drifted headers
- [X] T034 [P] [US8] arXiv/theoremsearch graceful degradation on transient 429/503/timeout (retry+backoff → recorded "unavailable" notice; non-transient still raises) in `src/llmxive/librarian/theoremsearch*.py`
- [X] T035 [US8] Implement the manual DOI sign-off gate (FR-054): publisher writes `pending_publication.yaml` + halts at `awaiting_publication_signoff`; `llmxive publish-approve <PROJ-ID>` writes `publication_signoff.yaml`; mint only on matching `content_hash` in `src/llmxive/agents/publisher.py` and `src/llmxive/cli.py`
- [X] T036 [US8] Verify all 10 bugs fixed by direct inspection + a real partial run; update STATUS.md

**Checkpoint**: pipeline mechanically sound for real runs.

---

## Phase 6: User Story 3 — Review-model overhaul (Priority: P1)

**Goal**: remove points; unanimous-panel gate; advisory human/personality triage; status re-expression + in-flight migration.
**Independent Test**: no advancement path reads points; only quality+safe+on-topic reviews reach a lens + the publication log; an in-flight project re-evaluates under convergence.

### Tests (write FIRST)

- [X] T037 [P] [US3] Integration test for triage (quality + safety/on-topic filter + stage-aware aspect-mapping + preservation) in `tests/integration/test_triage.py`
- [X] T038 [P] [US3] Test: no advancement path reads accumulated points (grep guard + behavioral) in `tests/integration/test_no_points.py`

### Implementation

- [X] T039 [US3] Implement `triage()` (quality filter + safety/on-topic + stage-aware aspect-mapping + preservation/exclusion) in `src/llmxive/convergence/triage.py`
- [ ] T040 [US3] Route the personality cron (`agents/personality.py`) AND human GitHub comments through `triage` as advisory inputs (one SSoT path; preserve the `(simulated)` suffix)
- [X] T041 [US3] Remove the point system: delete `_award_review_points`, the `RESEARCH_ACCEPT_THRESHOLD`/`PAPER_ACCEPT_THRESHOLD` comparisons and the majority-vote, in `src/llmxive/agents/advancement.py`; remove the thresholds from `src/llmxive/config.py`; make `advancement` a thin `ConvergenceResult` reader
- [ ] T042 [US3] Collapse the two revision-routing schemes (graph transient-stage block + spec-012 dual scheme) into the engine outcome (#51) in `src/llmxive/pipeline/graph.py` and `src/llmxive/agents/advancement.py`
- [X] T043 [US3] Re-express the public status model (Backlog→Ready→Done) in convergence terms in `README.md` + the web about page; update `src/llmxive/agents/status_reporter.py` (retain `projects.json` regen + issue comment + issue close on `posted`); update `src/llmxive/agents/repository_hygiene.py` to keep asserting the line-count-delta + gitignore patterns under the new status model (FR-026)
- [X] T044 [US3] Implement in-flight project migration (re-evaluate under unanimous convergence on next tick); confirm the no-`posted`/`done`-projects assumption holds in `state/projects/`
- [X] T045 [US3] Verify points removed (full-repo grep) + triage advisory-only; update STATUS.md

**Checkpoint**: one clean convergence-based gate everywhere.

---

## Phase 7: User Story 4 — Per-step panels (Priority: P1)

**Goal**: every reviewable step supplies a `ReviewSpec`; new early panels + paper twins; constitution as input; publisher wired.
**Independent Test**: each reviewable step runs its panel on a real project; exempt steps run no loop; constitution present from `specified` onward.

### Tests (write FIRST)

- [ ] T046 [P] [US4] Integration tests: idea/spec/plan/tasks panels run on a real project in `tests/integration/test_panels_research.py`
- [ ] T047 [P] [US4] Integration tests: paper-spec/paper-plan/paper-tasks/paper-implement panels in `tests/integration/test_panels_paper.py`

### Implementation

- [X] T048 [US4] Implement the `reviewspec_for(stage)` registry (per-stage ReviewSpec + EXEMPT set) per contracts/reviewspec-registry.md in `src/llmxive/convergence/reviewspecs.py`
- [X] T049 [P] [US4] Author idea panel prompts (`rq_validity`, `novelty`, `feasibility`, optional `idea_quality`) in `agents/prompts/panels/`
- [X] T050 [P] [US4] Author spec panel prompts (`requirements_coverage`, `internal_consistency`, `testability`, `scope`) in `agents/prompts/panels/`
- [X] T051 [P] [US4] Author plan panel prompts (`methodology`, `spec_coverage`, `data_resources`, `plan_consistency`) in `agents/prompts/panels/`
- [X] T052 [P] [US4] Author tasks panel prompts (`coverage`, `ordering`, `executability`, `constraint_preservation`) in `agents/prompts/panels/`
- [X] T053 [P] [US4] Author paper-track panel prompts (paper-spec/paper-plan/paper-tasks lenses) in `agents/prompts/panels/`
- [X] T054 [US4] Collapse `specifier`+`clarifier` into ONE spec convergence unit (reviewed once after clarify); route oversized authoring inputs (all `idea/*.md` + comments) through `tools/summarize` (FR-006) in `src/llmxive/speckit/specify_cmd.py` + `clarify_cmd.py`
- [X] T055 [US4] Collapse `paper_specifier`+`paper_clarifier` into ONE paper-spec unit; route oversized authoring inputs (full research spec+plan+tasks + comments) through `tools/summarize` (FR-006) in `src/llmxive/speckit/paper_specify_cmd.py` + `paper_clarify_cmd.py`
- [X] T056 [US4] Wire `planner` (and its paper twin `paper_planner`) as reviser + plan panel; keep deterministic guards as a pre-filter; route oversized authoring inputs (spec+constitution+template+dataset+comments) through `tools/summarize` (FR-006) in `src/llmxive/speckit/plan_cmd.py` + `paper_plan_cmd.py`
- [X] T057 [US4] Wire the tasks panel (4 lenses) for `tasker` (and its paper twin `paper_tasker`) + constitution input + deterministic pre-filter; fold spec-014 honest-reporting + per-round budget; route oversized inputs (full spec+plan+tasks+reviews each round) through `tools/summarize` (FR-006) in `src/llmxive/speckit/tasks_cmd.py` + `paper_tasks_cmd.py` + `analyze_cmd.py`
- [X] T058 [US4] Research-unit: `implementer` revises code in-loop + re-verifies task assertions against the filesystem (#49); reuse the 8-panel as R1/R3; adaptive kickback in `src/llmxive/speckit/implement_cmd.py`
- [X] T059 [US4] Paper-implement: 12-panel as R1/R3 on the assembled paper; `paper_implementer` re-dispatches the right sub-agent (figure/stat/section) as reviser in `src/llmxive/speckit/paper_implement_cmd.py`
- [X] T060 [US4] Add the per-project `constitution.md` as a standard panel + analyze input from `specified` onward (fix the `run_analyze` omission) in `src/llmxive/speckit/analyze_cmd.py` + engine
- [X] T061 [US4] Wire the publisher into the graph (`paper_accepted → publisher → awaiting_publication_signoff → posted`); remove the direct `paper_accepted→posted` edge in `src/llmxive/pipeline/graph.py`
- [ ] T062 [US4] Verify every reviewable step runs its panel; exempt steps run no loop; constitution present from `specified` onward; update STATUS.md

**Checkpoint**: convergence reaches every reviewable step.

---

## Phase 8: User Story 5 — Reviewer calibration (Priority: P1)

**Goal**: differential clean-vs-injected calibration across all 9 domains + held-out generality + manual adjudication.
**Independent Test**: per panel, the injected flaw is caught by the correct lens (and absent on the clean run); extra findings manually adjudicated; held-out field meets targets un-tuned.

### Tests (write FIRST)

- [ ] T063 [P] [US5] Unit tests for the 6 flaw injectors (correct flaw + expected lens) in `tests/unit/test_injectors.py`

### Implementation

- [ ] T064 [US5] Implement `calibration/injectors.py` (trivial/circular RQ, FR-without-task, gutted requirement, fabricated data, nonexistent citation, plan↔tasks contradiction; each tagged with expected lens)
- [ ] T065 [US5] Implement `calibration/differential.py` (run clean+injected, diff verdicts, write a markdown adjudication report for extra findings)
- [ ] T066 [US5] Implement `calibration/domains.py` (≥1 real peer-reviewed anchor paper per 9 `LIBRARIAN_DEFAULT_FIELDS` + HF-daily + backlog sample + held-out flag)
- [ ] T067 [US5] Build per-panel labeled calibration sets (positives + injected negatives) for each reviewable step under `specs/015-pipeline-convergence-protocol/calibration/`
- [ ] T068 [US5] Run differential calibration per panel per domain with REAL qwen calls (repeated for noise-robustness); produce adjudication reports; tune sensitivity adaptively with manual QC
- [ ] T069 [US5] Validate domain-generality on the held-out field with un-tuned prompts in `tests/real_call/test_calibration_heldout.py`
- [ ] T070 [US5] Record calibration + manual adjudication outcomes in STATUS.md and the calibration reports

**Checkpoint**: panels calibrated and domain-general.

---

## Phase 9: User Story 6 — End-to-end traversal in all 9 domains (Priority: P1)

**Goal**: a real high-quality project per domain reaches `posted`; weak projects rejected; every artifact directly inspected.
**Independent Test**: golden project → `posted` (real DOI after manual sign-off) per domain; weak project rejected/kicked back; direct artifact inspection clean.

### Tests (write FIRST)

- [ ] T071 [P] [US6] E2E harness (drive to `posted`; weak-project rejection; artifact inspection assertions) in `tests/e2e/test_domain_traversal.py`

### Implementation

- [ ] T072 [US6] Prepare a real high-quality golden project per domain (9 fields, reverse-engineered from the anchor papers) + ≥1 weak project under `state/projects/` / project folders
- [ ] T073 [US6] Run end-to-end traversal to `posted` for each of the 9 domains with REAL calls, repeated for noise-robustness — **PAUSES at the manual DOI sign-off (FR-054); the maintainer approves each before the real DOI mints**
- [ ] T074 [US6] Directly inspect every produced artifact per domain (spec/plan/tasks/code/data/paper/PDF/DOI/`publication.yaml`): no truncation, no missing artifact, no broken-tool placeholder, no task marked done with placeholder content
- [ ] T075 [US6] Confirm the weak project is rejected/kicked back; record results + manual QC co-evaluation against the anchor papers in STATUS.md

**Checkpoint**: goal property demonstrated across all 9 domains.

---

## Phase 10: User Story 7 — Living-document discussion board (Priority: P2)

**Goal**: post-`posted` triaged comments → log → batched recompile → Discussion section → version DOI (sign-off gated).
**Independent Test**: on a real `posted` project, an on-topic comment recompiles + mints a version DOI (post sign-off); off-topic/unsafe is excluded and triggers no recompile.

### Tests (write FIRST)

- [ ] T076 [P] [US7] Integration test: comment → log → recompile → Discussion section → version-DOI gate (and off-topic exclusion) in `tests/integration/test_living_document.py`

### Implementation

- [ ] T077 [US7] Implement post-`posted` comment ingestion via `triage` → project log + batched recompile queue in `src/llmxive/agents/publisher.py` (or a `living_document.py` module)
- [ ] T078 [US7] Implement Discussion-section render/update + material-PDF-change detection; mint a NEW Zenodo version DOI via the same FR-054 sign-off gate, only on material change in `src/llmxive/agents/publisher.py`
- [ ] T079 [US7] Verify on a real `posted` project (post US6): on-topic comment recompiles + version DOI after sign-off; off-topic excluded, no recompile; update STATUS.md

**Checkpoint**: published papers are living documents.

---

## Phase 11: Polish & Cross-Cutting Concerns

- [ ] T080 Add an inspection hook to the non-speckit `Agent` base so `flesh_out`/validator capture inspection records (close design §9 gap) + tests in `src/llmxive/agents/base.py`
- [ ] T081 [P] Verify every agent invocation + convergence round writes a run-log entry; schema-validate every written artifact; project state never silently stalls — verification test in `tests/integration/test_invariants.py`
- [ ] T082 [P] SSoT grep audit: confirm the old forked summarizer, point-scoring, and dual routing are deleted/re-pointed (Const. I) — record evidence in STATUS.md
- [ ] T083 Documentation parity: update READMEs, docstrings, web docs for all changed behavior; update `requirements.txt`/`pyproject.toml` if deps changed
- [ ] T084 Full verification suite: `ruff check .` + `mypy src/llmxive` + `pytest tests/unit tests/contract tests/integration` + `LLMXIVE_REAL_TESTS=1 pytest tests/real_call tests/e2e` + `python -m llmxive.checks.prompts`; fix CODE until green (never weaken tests)
- [ ] T085 Final manual QC sign-off recorded; STATUS.md marked complete

---

## Dependencies & Execution Order

- **Setup (P1) → Foundational (P2)** block everything.
- **US1 (summarizer)** must complete first (overflow handling depends on it).
- **US2 (engine)** depends on Foundational types + US1 (overflow inputs).
- **US8 (bug fixes)** mostly independent; T030–T034 can run in parallel after Setup; T035 (sign-off) + T061 (publisher wiring) feed US6.
- **US3 (review model)** depends on US2 (engine is the new gate).
- **US4 (per-step panels)** depends on US2 + US3 (+ US8 publisher wiring at T061).
- **US5 (calibration)** depends on US4 (panels exist) + US1 (summarizer).
- **US6 (e2e)** depends on US1–US5 + US8.
- **US7 (living-doc, P2)** depends on US6 (posted projects) + US8 (publisher sign-off).
- **Polish** last; re-run full suite after any fix (Const. pre-push gate).

## Parallel Execution Examples

- After Setup: T005/T006 (types + contract test) ∥ T030–T034 (standalone bug fixes) ∥ T007 (constitution).
- US1 tests T008/T009/T010 in parallel before implementation T011–T017.
- US4 panel prompts T049–T053 fully parallel (different files).

## Implementation Strategy

MVP = US1 (summarizer) — independently valuable and the validated foundation. Then incrementally: engine (US2) → bug fixes (US8) → review model (US3) → panels (US4) → calibration (US5) → e2e (US6) → living-doc (US7) → polish. Commit per task/checkpoint; keep STATUS.md current; the manual DOI sign-off (US6/US7) and manual QC adjudication (US5) are deliberate human checkpoints that will pause autonomous execution.
