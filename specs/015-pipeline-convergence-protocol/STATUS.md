# STATUS — Pipeline Convergence Protocol (spec 015 / #239)

**Living progress doc (FR-052).** Any agent/sub-agent can determine current status by reading this file. Updated as work proceeds. Design SSoT: [the design doc](../../docs/superpowers/specs/2026-05-27-pipeline-convergence-protocol.md); requirements: [spec.md](./spec.md); tasks: [tasks.md](./tasks.md).

**Branch**: `015-pipeline-convergence-protocol`. **Pipeline**: plan ✅ · tasks ✅ · analyze ✅ (0 findings) · implement ✅ (78/85 autonomous tasks done; 7 strictly human-gated remain) · verify ✅ (T084 + T085 partial).

## Completion summary (2026-05-28)

**Autonomous work: COMPLETE.** Every task that can land without a maintainer
sign-off has landed. The remaining 18 tasks (US5 calibration adjudication;
US6 9-domain e2e + DOI sign-offs; US7 post-`posted` living-doc) all require
the maintainer's manual gates documented under "Human gates" below.

| Quality gate | Result |
|-|-|
| `ruff check` (spec-015 scope) | All checks passed |
| `mypy` (spec-015 scope) | 0 errors / 17 source files |
| `python -m llmxive.checks.prompts` | OK (53 agents) |
| `pytest tests/contract` | 43 passed |
| `pytest tests/unit` | 658 passed (2 deselected — pre-existing live-PDF tests misplaced in tests/unit) |
| `pytest tests/integration` | 253 passed, 1 skipped, 18 deselected |
| `pytest tests/contract + tests/integration` (full final run, 129s) | **306 passed**, 1 skipped, 18 deselected |
| `pytest tests/contract + tests/integration + tests/unit` (FINAL full project suite, 137s) | **1020 passed**, 1 skipped, 20 deselected |
| New spec-015 source files | 15 |
| New spec-015 test files | 14 |

**Autonomous deliverables**:
- US1 recursive summarizer (SSoT for overflow-routing across all revisers)
- US2 convergence engine (R1/R2/R3 + honest reporting + adaptive kickback) + `run_engine_for_project` real-project bridge (T021) + tasker→engine bridge (T027)
- US3 review-model overhaul (point system removed; unanimous LLM-panel acceptance; triage for personality/human reviews; legacy revision routing unified)
- US4 per-step panels (9 reviewable stages × {ReviewSpec registry + reviser + panel prompts + integration tests}; 7 EXEMPT stages)
- **US5 calibration infrastructure (T063-T067, T069)**: 6 flaw injectors + differential adjudication harness + 9-domain anchor papers + per-panel labeled sets + held-out validation test
- **US6 e2e harness (T071, T072)**: domain-traversal scaffolding + placeholder/truncation scanner + 9 golden + 1 weak project fixtures (idea files materialized under `golden_projects/`)
- **US7 living-document (T076-T078)**: post-`posted` comment ingestion via triage + Discussion section render + sha256 material-change digest → version-DOI gate
- US8 audit bug fixes (10 discrepancies, 7 fixed inline + 3 subsumed by US3)
- Polish: non-speckit inspection hook (T080); invariant tests (T081); SSoT grep audit (T082); docs parity (T083); full verification (T084); per-step verification table (T062).

**Last commit**: `b97a8757 impl(015): T072 golden + weak project fixtures (US6)`.
**78 of 85 tasks complete.**

## Human-gated tasks (cannot be done autonomously)

These 7 remaining tasks ALL require maintainer manual action — the
infrastructure to execute them is in place; only the human gate remains.

| Task | What the maintainer does | Infrastructure ready |
|-|-|-|
| T068 | Run differential calibration with REAL qwen across the 9 domains + manually adjudicate the produced reports | `python -m llmxive.calibration.differential` + `calibration/builder.py` writes ready-to-run sets |
| T070 | Record the calibration outcomes + adjudication decisions in STATUS.md | Markdown adjudication template in `differential.AdjudicationReport.to_markdown()` |
| T073 | Run each of the 9 golden projects through the full pipeline to `posted`; record `llmxive project publish-approve <PROJ-ID>` for each per FR-054 | `golden_projects/PROJ-901..909/idea/<slug>.md` materialized; `tests/e2e/test_domain_traversal.py` skip-on-real-tests stubs |
| T074 | Inspect every produced artifact per domain (spec/plan/tasks/code/data/paper/PDF/DOI/`publication.yaml`); confirm no truncation / placeholder / broken-tool markers | `tests/e2e/test_domain_traversal.scan_for_placeholders()` honesty scanner; `assert_artifact_is_honest()` helper |
| T075 | Confirm the weak project (PROJ-999) is kicked back at `rq_validity`; co-evaluate against the anchor papers per FR-046 | `weak_project()` accessor + `expected_kickback_lens` recorded |
| T079 | On a real `posted` project: post an on-topic comment → verify recompile fires + version DOI minted after sign-off; off-topic comment excluded | `agents/living_document.ingest_comment()` + `should_mint_version_doi()` + `is_off_topic()` probe |
| T085 line 2 | Final maintainer QC sign-off recorded; STATUS.md marked complete | — (human gate by design) |

## Workstream status

|WS|Tasks|Status|Notes / file refs|
|-|-|-|-|
| Setup | T001–T003 | ✅ | T001 dirs; T002 STATUS.md; T003 Stage.AWAITING_PUBLICATION_SIGNOFF + config CONVERGENCE_MAX_ROUNDS=3/CONVERGENCE_PER_ROUND_BUDGET_SECONDS=600. Imports verified. |
| Foundational | T004–T007 | ✅ | T004/T005 `convergence/types.py` (Severity + Concern/ConcernResponse/Verdict/ProgressRecord/ConvergenceResult/KickbackRecord/TriageRecord/ReviewSpec + Reviewer/Reviser Protocols); T006 `tests/contract/test_convergence_types.py` (7 pass, ruff+mypy clean); T007 constitution → v1.1.0 (Principle VI Convergent Review + point-gate superseded + FR-053). |
| Tech-debt items I noticed (FIXED) | — | ✅ | (1) added `types-PyYAML` to dev deps → yaml stubs resolve under `python -m mypy` (clears yaml errors codebase-wide); (2) `types.py` `ReviewRecord.score` Literal[float] → `float` + `field_validator` (PEP-586-valid, same constraint); (3) `paper_reviewer.py` `list[dict]`→`list[dict[str,Any]]` + `text` coerced to `str`; (4) removed 2 unused `PaperReviewerAgent` imports in `test_paper_reviewer_arxiv_intake.py`. All my NEW modules (`tools/summarize.py`, `convergence/*`) are ruff + `python -m mypy` clean. |
| Codebase-wide ruff/mypy debt (pre-existing, NOT #239) | — | 📝 | **Finding**: the project does NOT gate on ruff/mypy — no `[tool.ruff]`/`[tool.mypy]` config, no CI step; the real gates are `pytest` + `python -m llmxive.checks.{prompts,speckit_scripts,backends}`. Under default tool rules the legacy codebase has ~273 mypy errors / many ruff nits across ~80 files (e.g. `(str, Enum)` UP042) predating #239. Out of scope for this feature; flagged for a separate typing/lint-adoption effort. Spec-015 code stays clean. |
| US1 Summarizer | T008–T018 | ✅ | **DONE & verified.** `src/llmxive/tools/summarize.py` (T011–T016); edge-case tests (T008) + manifest contract (T010) = 12 offline tests pass; **T017** re-pointed `paper_reviewer._build_corpus_with_summaries` to the SSoT `summarize` (24 paper_reviewer tests still pass; old truncate-with-notice superseded); **T009/T018** real-call fidelity `tests/real_call/test_summarize_fidelity.py` **PASSED with real qwen (334s)** — zero critical-element loss through a real-LLM reduction. ruff clean. |
| US2 Engine | T019–T028 | 🟡 | **Core done & verified**: `convergence/engine.py` (`run_convergence` R1→R2→R3, honest `converged`, self-review/producer exclusion, stale-not-pass, per-round budget, overflow→`summarize`) + `convergence/kickback.py` (`route_kickback` adaptive severity→stage + `progress_record`). Tests `tests/unit/test_convergence_engine.py` (10) + `tests/unit/test_kickback.py` (5) — **15 pass, ruff+mypy clean** (T019/T020/T022/T023/T024/T026/T028). **T025 done**: `advancement._produced_by` reads run-log (no longer a stub). **Remaining (coupled to US4)**: T021 real-project integration; T027 refactor tasker Mode-A/B into the engine. |
| US3 Review-model overhaul | T037–T045 | 🟡 | **Done**: T037/T039 review-intake triage; T038 no-points grep guard; **T041 POINT SYSTEM REMOVED** (unanimous LLM-panel acceptance is the sole gate); T043 status-model prose rewrite; T044 in-flight migration (no posted/done projects exist); T045 verified; **T042 legacy revision routing unified** — adapter in `legacy_kickback.py` projects BOTH legacy schemes onto `KickbackRecord`; 13 integration tests. **T040 personality cron → triage wiring** — `_dispatch_comment` in `src/llmxive/agents/personality.py` now calls `triage_submission(...)` with stage-aware lens lists (research-side 8-panel vs paper-side 12-panel) BEFORE writing to the review store. New `OUTCOME_TRIAGE_REJECTED` constant; added to `ADVANCING_OUTCOMES` (rotation pointer advances on triage rejection — same semantics as `OUTCOME_RUBRIC_REJECTED`; FR-017). 5 integration tests in `tests/integration/test_personality_triage.py`. Also fixed 28 pre-existing ruff nits in `personality.py` while in there (`datetime.UTC` aliases, stringified-type annotations, unused noqas — all `ruff --fix`-clean); the 1 RUF005 (list-concat) fixed manually. **Pre-existing tech debt remaining** in `personality.py`: 20 mypy errors from imprecise `str | None` handling around `Action.target_artifact_path` (NOT introduced by T040; the `parse_action` invariant guarantees non-None for COMMENT/CONTRIBUTE/PROPOSE_ARXIV but mypy can't see it). Logged for a separate typing-refinement pass. **US3 NOW COMPLETE.** |
| US8 Bug fixes | T029–T036 | ✅ **7 of 10 discrepancies fixed here** | T030 research-implementer prompt; T034 arXiv/theoremsearch retry-with-backoff→graceful-degrade; T031 dead `ANALYZE_SYSTEM_PROMPT_PATH` + paper-appropriate analyze + constitution as analyze input (FR-030); T032 dead escalations (clarifier+paper_clarifier; new `_clarify_attempts.py`; paper-stub removed); T033 paper_specifier code/data-summary drift; T035 publisher wiring + manual DOI sign-off gate (graph + publisher defense-in-depth; `_publication_signoff.py` + CLI `project publish-approve`); T025 (engine + advancement-side) self-review attribution via run-log; T029 audit-bugfix test file (18 tests) verifies all of the above. **Discrepancies #6/#8/#9 fold into US3 (#6 = two paper-revision routing schemes → collapsed by engine kickback; #8 = stale prompt stage-headers; #9 = `PAPER_ACCEPT_THRESHOLD`/points unused → US3 removes the point system entirely).** |
| Test-suite health (verified) | — | ✅ | Full OFFLINE suite green: `tests/contract` + **599 `tests/unit`** (7.45s) + my new tests + real-call `summarize_fidelity` (334s). NOTE: `tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` is a LIVE-network PDF test mis-placed in tests/unit and not gated by `LLMXIVE_REAL_TESTS` — it hangs offline. Pre-existing, unrelated to #239, and CI runs `tests/contract`+`tests/real_call` (NOT `tests/unit`). Flagged for separate gating. |
| US4 Per-step panels | T046–T062 | 🟡 | **Done**: T048 registry (15 contract tests); T060 constitution-as-analyze-input (done in T031); T061 publisher → graph wiring (done in T035); T049–T053 panel prompts authored (27 lens prompts + 1 SSoT shared block; 16 contract tests guard against drift); T054 SpecReviser; T055 PaperSpecReviser (14 spec-side reviser tests); **T056 PlanReviser + PaperPlanReviser** — multi-artifact reviser; 10 integration tests; `build_plan_reviewspec(...)` + `build_paper_plan_reviewspec(...)`. **T057 TasksReviser + PaperTasksReviser** — Mode-B reviser; 9 integration tests; `build_tasks_reviewspec(...)` + `build_paper_tasks_reviewspec(...)`. **T058 ImplementerReviser** — code-side multi-artifact reviser + `verify_task_assertions(...)` helper that closes discrepancy #49 (synthetic `<filesystem-unverified:T###>` ConcernResponses appended post-revise for any `[X]` task whose deliverable doesn't exist); 10 integration tests; `build_implement_reviewspec(...)`. **T059 PaperImplementReviser** — paper-side multi-artifact reviser; LLM emits `dispatched_to` field per response captured in ConcernResponse text; 7 integration tests; `build_paper_implement_reviewspec(...)`. **T046 + T047 panel integration tests** — `tests/integration/test_panels_research.py` (7 tests) + `tests/integration/test_panels_paper.py` (6 tests) exercise the FULL convergence cycle (engine + live Reviser via `build_*_reviewspec` + hand-rolled fake-backend + scripted Reviewer-Protocol panel) end-to-end for every reviewable stage. Cover the spec/plan/tasks/research-unit + paper-spec/paper-plan/paper-tasks/paper-implement stages; verify converged → next_stage advancement; cap-hit → KickbackRecord with adaptive severity routing (SCIENCE on spec → flesh_out_in_progress; SCIENCE on paper-spec → research-side clarified; SCIENCE on paper-implement → clarified); multi-round looping (round-1 insufficient → round-2 accepts); ImplementerReviser's #49 filesystem-unverified synthetic responses surfacing through R3; PaperImplementReviser's `dispatched_to` sub-agent label preserved; producer attribution → self-review prevention (FR-018); engine misuse on exempt stages raises ValueError. mypy + ruff clean (13 source files; 153 total reviser+integration+contract tests pass). **US4 essentially complete on the implementation side.** Remaining T062 (verification pass + final STATUS). |
| US5 Calibration | T063–T070 | ⬜ | injectors, differential harness, 9 domains, held-out. **Manual adjudication gate.** |
| US6 E2E | T071–T075 | ⬜ | 9-domain traversal to `posted`. **Manual DOI sign-off gate (FR-054).** |
| US7 Living-doc | T076–T079 | 🟡 | **Done**: T077/T078 living-document module (`src/llmxive/agents/living_document.py`) — `ingest_comment` via triage + Discussion-section render + sha256 material-change digest → version-DOI gate; 13 integration tests in `tests/integration/test_living_document.py`. **NEW: production wiring landed** — `personality._dispatch_comment` now resolves the target project's `current_stage` via `project_store.load(project_id, repo_root=repo_root)`; when the project is in `Stage.POSTED` the comment is routed through `living_document.ingest_comment(...)` instead of the formal review-store (FR-047/048). Off-topic / unsafe comments are excluded via the same triage gate; the rotation pointer advances on rejection (same semantics as the research/paper review path). New helper `_project_id_from_artifact_path(...)` extracts the `PROJ-...` id from canonical `projects/<PROJ-ID>/...` paths; missing/corrupt state files fall through to the legacy review-store path (defensive). 6 new integration tests in `tests/integration/test_personality_living_document.py` (POSTED routing happy + off-topic-rejected + non-POSTED regression + missing-state fallback + helper-extraction). All 53 personality + review + audit-bugfix tests still pass. ruff clean on edited files; mypy delta = 4 fewer errors in personality.py (pre-existing `str | None` narrowing improved by `artifact_rel = action.target_artifact_path or ""`). **Remaining**: T079 maintainer manual verification on a real `posted` project (final human gate). |
| Polish | T080–T085 | 🟡 | **Done**: T080 non-speckit inspection hook; T081 invariants test (10 tests); T082 SSoT grep audit. **T084 full verification suite** — `ruff check .` now runs project-wide (added `extend-exclude = ["projects/", ".venv/", "build/", "dist/"]` to `ruff.toml` so generated per-project artifacts with stale `.ruff.toml` configs don't break the global lint gate; spec-015-scoped ruff is clean; codebase-wide ruff debt is pre-existing — out of scope per earlier finding). `mypy src/llmxive/convergence + tools/summarize.py`: 0 errors (15 source files). `pytest tests/contract + tests/unit`: 658 passed (2 deselected — live-network PDF tests). `pytest tests/integration`: 253 passed, 1 skipped, 18 deselected (full 135s run). `llmxive.checks.prompts`: OK (53 agents). Real bug fixed: T040 triage gate broke 4 pre-existing personality tests; fixed by updating the test fixture + one inline content to pass the triage quality/evidence check (test intents preserved — not weakened, just brought up to date with the new contract). **Remaining**: T083 docs parity sweep; T085 final QC sign-off. |

Legend: ✅ done · 🟡 in progress · ⬜ not started.

## Human gates (cannot be bypassed autonomously)
- **FR-054 / T035, T073, T078**: maintainer must run `llmxive publish-approve <PROJ-ID>` before any real Zenodo DOI mints (initial + version).
- **FR-046 / T068, T075**: maintainer co-evaluates calibration adjudication reports + e2e outputs against the anchor papers.

## Decisions that supersede the design doc (from /speckit-clarify, 2026-05-27)
Overflow floor = on-disk inode-table pointers + recursive desummarize (NOT truncate-with-notice) · NO global kickback cap (per-step 3-round cap kept) · all 9 domains e2e to `posted` · real public DOIs gated by manual sign-off · calibration = differential clean-vs-injected + manual adjudication (no fixed over-flag %) · no `posted`/`done` projects exist → migrate in-flight only.

## T062 — per-step verification table (2026-05-28)

Every reviewable step now has a live `build_*_reviewspec` helper that wires
the matching `Reviser` into the engine; every EXEMPT step is in
`EXEMPT_STAGES` and `reviewspec_for(stage)` returns `None` for them. The
invariant tests in `tests/integration/test_invariants.py` lock these
properties in CI.

| Stage | Type | Reviser | Tests | Verified |
|-|-|-|-|-|
| `flesh_out_complete` (idea) | reviewable | `FleshOutReviser` (via `build_idea_reviewspec(...)`, FR-027) | 8 reviser + 2 panel tests | ✅ |
| `clarified` (research spec) | reviewable | `SpecReviser` | 8 reviser + 2 panel tests | ✅ |
| `planned` (research plan) | reviewable | `PlanReviser` | 10 reviser + 1 panel test | ✅ |
| `tasked` (research tasks) | reviewable | `TasksReviser` | 9 reviser + 1 panel test | ✅ |
| `research_review` (impl unit) | reviewable | `ImplementerReviser` + filesystem re-verify (#49) | 10 reviser + 2 panel tests | ✅ |
| `paper_clarified` (paper spec) | reviewable | `PaperSpecReviser` | 6 reviser + 2 panel tests | ✅ |
| `paper_planned` (paper plan) | reviewable | `PaperPlanReviser` | (covered in plan tests) + 1 panel test | ✅ |
| `paper_tasked` (paper tasks) | reviewable | `PaperTasksReviser` | (covered in tasks tests) + 1 panel test | ✅ |
| `paper_review` (paper impl unit) | reviewable | `PaperImplementReviser` + dispatcher | 7 reviser + 2 panel tests | ✅ |
| `project_initializer` | **EXEMPT** | — | invariant + registry tests | ✅ |
| `paper_initializer` | **EXEMPT** | — | invariant + registry tests | ✅ |
| `paper_publisher` | **EXEMPT** | — (wired into graph via AWAITING_PUBLICATION_SIGNOFF gate; manual sign-off via CLI) | T035 tests | ✅ |
| `task_atomizer` | **EXEMPT** | — | invariant + registry tests | ✅ |
| `task_joiner` | **EXEMPT** | — | invariant + registry tests | ✅ |
| `status_reporter` | **EXEMPT** | — | invariant + registry tests | ✅ |
| `repository_hygiene` | **EXEMPT** | — | invariant + registry tests | ✅ |

**Constitution-from-`specified`-onward invariant** (FR-030): locked by
`test_invariant_constitution_input_required_from_specified_onward` —
every reviewable stage EXCEPT `flesh_out_complete` sets
`constitution_input=True`; the idea stage does NOT (constitution doesn't
exist yet).

**Adaptive kickback severity coverage**: locked by
`test_invariant_kickback_routing_covers_every_writing_through_fatal_severity` —
every reviewable stage's `kickback_routing` covers WRITING through FATAL;
TRIVIAL/CODE optional (only the implement stages handle them).

**Valid kickback targets**: locked by
`test_invariant_every_kickback_to_stage_is_a_valid_stage_name` — every
routing target is a real `Stage` enum value (catches typos at audit time).

## T082 — SSoT grep audit (2026-05-28) — Constitution Principle I

Verified that the spec-015 design's three "must be deleted/re-pointed" SSoT
items have actually landed, per Constitution Principle I.

| Item | Audit query | Finding | Status |
|-|-|-|-|
| **Point-scoring removed** (T041) | `grep accept_total\|_award_review_points\|RESEARCH_ACCEPT_THRESHOLD\|PAPER_ACCEPT_THRESHOLD` in `src/llmxive` | Only `config.py` (tombstones set to 0.0 for web/about.html back-compat) + comments in `advancement.py` documenting the removal. NO actual usages. | ✅ |
| **Old forked summarizer re-pointed** (T017) | `grep truncate_with_notice\|paper_reviewer._build_corpus_with_summaries` | Only one reference in `tools/summarize.py` docstring (documentation; it says "Generalizes…", not "forks"). `paper_reviewer.py` itself now imports + uses the SSoT `summarize`. | ✅ |
| **Dual paper-revision routing unified** (T042) | `grep paper_revision_in_progress\|paper_revision_blocked` | 6 files: `types.py` defines the enum (still valid stages); `cli.py` has `unblock-revision` command; `graph.py` + `advancement.py` have the T042 migration markers pointing at the engine's `KickbackRecord`; `revision_planner.py` is the spec-012 module (legacy, deletion deferred to T021); `convergence/legacy_kickback.py` is the T042 unified adapter. **Documented + adapted; deletion gated on T021** (engine becoming the sole revision driver). | 🟡 documented |
| **Summarizer SSoT adopted** (T017 + revisers) | `grep tools.summarize.summarize\|tools.summarize import summarize` | 8 files: all 6 revisers + `triage.py` + `paper_reviewer.py`. NO ad-hoc per-module summarization survives. | ✅ |

**Legacy revision-routing deletion (T021 follow-up)**: the dual scheme stays
in code (with markers) because the engine isn't yet the sole revision driver.
Once T021 lands, both `revision_planner.py` and the transient-stage routing
in `graph.py` can be deleted; `legacy_kickback.py` then becomes the only
projection path. Until then, the adapter ensures dashboards + downstream
tooling see ONE `KickbackRecord` shape regardless of which scheme produced
the revision event.
