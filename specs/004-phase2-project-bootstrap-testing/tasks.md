---

description: "Task list for Phase 2 (Project Bootstrap) end-to-end testing & diagnostics"
---

# Tasks: Phase 2 (Project Bootstrap) End-to-End Testing & Diagnostics

**Input**: Design documents from `specs/004-phase2-project-bootstrap-testing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Yes — pytest harness for FR-011 / SC-009 (idempotency check) is part of FR-007 / Decision 4 in research.md. The diagnostic itself is a manual procedure but the idempotency-check harness MUST have automated tests.

**Organization**: Tasks are grouped by user story. The MVP is US1 (clean run on iter2 siblings); US2-US6 build on US1's substrate.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- File paths are absolute relative to repo root

## Path Conventions

Single project; all paths relative to `/Users/jmanning/llmXive/`:
- Production code: `src/llmxive/`
- Diagnostic helpers + tests: `tests/phase1/`
- Spec artifacts: `specs/004-phase2-project-bootstrap-testing/`
- Diagnostic report: `notes/`
- Real-project artifacts: `projects/`, `state/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preflight verification + the two production-code prerequisite fixes that ALL user stories depend on. No work in any user-story phase can begin until Phase 1 + Phase 2 complete.

- [X] T001 Run preflight checks per quickstart.md Step 0: verify `cat specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` succeeds, `python -m llmxive run --help` succeeds, `python -c "from llmxive.credentials import load_dartmouth_key; print('ok' if load_dartmouth_key(prompt_if_missing=False) else 'missing')"` prints `ok`, and `git status --short` is clean (or only modified `.omc/`/cron files).
- [X] T002 Confirm carry-forward substrate exists: `ls projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/idea/` and `ls projects/PROJ-262-predicting-molecular-dipole-moments-with/idea/` both list a `<slug>.md` file.
- [X] T003 Confirm spec 004 directory layout is in place: `ls specs/004-phase2-project-bootstrap-testing/{spec.md,plan.md,research.md,data-model.md,quickstart.md,contracts,checklists}` succeeds.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The two production-code patches + the test harness that ALL user stories depend on. Per research.md Decisions 1, 2, 4 + spec.md FR-003a / FR-011.

**⚠️ CRITICAL**: No US1-US6 task can begin until T004-T010 complete and committed.

- [X] T004 Patch [tests/phase1/sibling_project.py:36](tests/phase1/sibling_project.py#L36) to extend `ALLOWED_START_STAGES` from `{"brainstormed", "flesh_out_in_progress", "flesh_out_complete"}` to `{"brainstormed", "flesh_out_in_progress", "flesh_out_complete", "validated"}`. Per spec.md FR-003a / research.md Decision 1.
- [X] T005 Verify the spawner change: run `python tests/phase1/sibling_project.py --help` and confirm the `--start-stage` choices include `validated`.
- [X] T006 Commit T004 with message referencing FR-003a, #46, #62: `git add tests/phase1/sibling_project.py && git commit -m "phase2/spec-004: add 'validated' to sibling spawner allowlist (FR-003a, #46 #62)"`
- [X] T007 Patch [src/llmxive/agents/project_initializer.py:84-104](src/llmxive/agents/project_initializer.py#L84-L104) to add a skip-if-exists guard before the constitution write: at the top of `handle_response`, if `(project_dir / ".specify" / "memory" / "constitution.md").is_file()`, call `init_speckit_in(project_dir)` (still idempotent on dirs) and return `[str(constitution_path.relative_to(repo))]` without invoking the LLM-output write. Per spec.md FR-011 / Q3 / research.md Decision 2.
- [X] T008 Patch [src/llmxive/agents/project_initializer.py:60](src/llmxive/agents/project_initializer.py#L60) to upgrade the silent `if idea_path.exists():` defensive guard into a fail-fast `raise FileNotFoundError(f"idea seed not found: {idea_path}")`. Per spec.md US4 scenario 2 / research.md Decision 5 / Constitution Principle V.
- [X] T009 [P] Implement [tests/phase1/test_idempotency.py](tests/phase1/test_idempotency.py) per `contracts/idempotency-check.md` — four pytest tests: `test_init_speckit_in_idempotent_on_complete_tree`, `test_project_initializer_skips_existing_constitution`, `test_project_initializer_writes_on_first_invocation`, `test_full_tree_idempotent_after_two_agent_invocations`. Use real `tmp_path` fixtures; no mocks per Constitution Principle III.
- [X] T010 Run `pytest tests/phase1/test_idempotency.py -v` and confirm all 4 tests pass. If any fail, fix the agent patches in T007/T008 (do NOT loosen the test).
- [X] T011 Commit T007/T008/T009 with message referencing FR-011, Q3, P2-D03, #46, #62: `git add src/llmxive/agents/project_initializer.py tests/phase1/test_idempotency.py && git commit -m "phase2/spec-004: idempotency + fail-fast guards on project_initializer (FR-011 Q3 P2-D03, #46 #62)"`
- [X] T012 Verify the existing backend retry policy at [src/llmxive/backends/router.py:96-100](src/llmxive/backends/router.py#L96-L100) (`attempts = 3 if model_idx == 0 else 1`) satisfies Q4's "2 retries / 3 total attempts" minimum. Per research.md Decision 3, no code change is expected; record verification in the diagnostic report's §1 as evidence FR-002 is satisfied by inheritance. **Contingency**: if the policy at L96-L100 has been weakened to <3 attempts on the primary model (e.g., reduced to `attempts = 2`) since spec 003 merged, file as defect P2-D04 with HIGH severity and patch in this PR before continuing to US1.

**Checkpoint**: Foundation ready. The two prerequisite production fixes are committed; idempotency tests are green; retry policy verified. User-story phases may now begin.

---

## Phase 3: User Story 1 - project_initializer runs cleanly on each iter2 sibling (Priority: P1) 🎯 MVP

**Goal**: Run `project_initializer` end-to-end against the real Dartmouth Chat backend on one iter2 sibling per canonical (PROJ-261, PROJ-262), capturing every input/output/state-transition for audit.

**Independent Test**: Spawn the sibling, run `python -m llmxive run --project <sibling-id> --max-tasks 1`, open `projects/<sibling-id>/.specify/memory/constitution.md`. The run-log must record `outcome: success`; the constitution must start with `# <title> — Research Project Constitution` and end with `**Project ID**: …` footer; no literal `{{token}}` strings remain; state YAML's `current_stage` advances to `project_initialized`. Per spec.md US1 acceptance scenarios 1-3.

### Implementation for User Story 1

- [X] T013 [P] [US1] Spawn PROJ-261-iter2 by running `python tests/phase1/sibling_project.py PROJ-261-evaluating-the-impact-of-code-duplicatio --iter 2 --start-stage validated`. Confirm output prints `PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2`. Confirm `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2/idea/evaluating-the-impact-of-code-duplicatio.md` exists and is byte-identical to the canonical's idea file (the spawner sha256-verifies; capture its stderr for the report).
- [X] T014 [P] [US1] Spawn PROJ-262-iter2 by running `python tests/phase1/sibling_project.py PROJ-262-predicting-molecular-dipole-moments-with --iter 2 --start-stage validated`. Confirm output prints `PROJ-262-predicting-molecular-dipole-moments-with-iter2`. Confirm `projects/PROJ-262-…-iter2/idea/<slug>.md` exists and is byte-identical to the canonical's.
- [X] T015 [US1] Snapshot the pre-run state YAMLs: `cat state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2.yaml > /tmp/pre-261.yaml` and `cat state/projects/PROJ-262-predicting-molecular-dipole-moments-with-iter2.yaml > /tmp/pre-262.yaml`. Both MUST show `current_stage: validated`.
- [X] T016 [US1] Commit the two iter2 spawn artifacts: `git add projects/PROJ-261-…-iter2/ projects/PROJ-262-…-iter2/ state/projects/PROJ-26{1,2}-…-iter2.yaml && git commit -m "phase2/spec-004: spawn iter2 siblings of PROJ-261, PROJ-262 (US1, FR-001, #46 #62)"`
- [X] T017 [US1] Run `project_initializer` on PROJ-261-iter2: `python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2 --max-tasks 1`. Capture stdout, stderr, and exit code into `/tmp/run-261.log`. Expected exit code: 0.
- [X] T018 [US1] Run `project_initializer` on PROJ-262-iter2: `python -m llmxive run --project PROJ-262-predicting-molecular-dipole-moments-with-iter2 --max-tasks 1`. Capture stdout, stderr, and exit code into `/tmp/run-262.log`. Expected exit code: 0.
- [X] T019 [US1] Snapshot post-run state YAMLs: `cat state/projects/PROJ-261-…-iter2.yaml > /tmp/post-261.yaml` and same for 262. Both MUST show `current_stage: project_initialized` and `last_run_status: success`.
- [X] T020 [US1] Capture run-log JSONL entries: locate the new line(s) in `state/run-log/2026-05/<run_id>.jsonl` corresponding to T017 and T018. Each must have `agent: project_initializer`, `outcome: success`, populated `started_at`/`ended_at`, `stage_before: validated`, `stage_after: project_initialized`.
- [X] T020a [US1] Capture verbatim rendered system prompt for each iter2 run (per FR-008 / SC-010 evidence). Run a Python harness that reconstructs the prompt EXACTLY as the agent built it, then write it to `/tmp/prompt-<sibling-id>.txt`: `python -c "from pathlib import Path; from llmxive.agents.base import AgentContext; from llmxive.agents.project_initializer import ProjectInitializerAgent; from llmxive.agents.registry import load_registry; reg = load_registry(); entry = next(e for e in reg.agents if e.name == 'project_initializer'); agent = ProjectInitializerAgent(entry); slug = '<slug>'; ctx = AgentContext(project_id='<sibling-id>', metadata={'title': '<title>', 'field': '<field>', 'principal_agent_name': 'flesh_out'}, inputs=[f'projects/<sibling-id>/idea/{slug}.md']); msgs = agent.build_messages(ctx); print('=== SYSTEM ==='); print(msgs[0].content); print('=== USER ==='); print(msgs[1].content)" > /tmp/prompt-<sibling-id>.txt`. Substitute `<title>`, `<field>` from the canonical's state YAML. The captured file is quoted verbatim in the diagnostic report's § 2.X.2 / § 2.X.3.
- [X] T021 [US1] Verify both iter2 siblings have a complete `.specify/` tree: `find projects/PROJ-261-…-iter2/.specify -type f | sort` and same for 262. Each must list 10 files (1 constitution + 4 scripts + 5 templates) per data-model.md E3.
- [X] T022 [US1] Commit the iter2 run artifacts: `git add projects/PROJ-26{1,2}-…-iter2/.specify/ state/projects/PROJ-26{1,2}-…-iter2.yaml state/run-log/ && git commit -m "phase2/spec-004: project_initializer happy-path runs on iter2 siblings (US1, #46 #62)"`

**Checkpoint**: At this point, US1 is fully exercised. PROJ-261-iter2 and PROJ-262-iter2 are at `current_stage: project_initialized` with audited-able artifacts.

---

## Phase 4: User Story 2 - Constitution-quality audit against the system prompt's contract (Priority: P1)

**Goal**: For each iter2 sibling, audit `.specify/memory/constitution.md` against the six output-contract items in `agents/prompts/project_initializer.md`. Record per-item PASS/FAIL with quoted excerpts.

**Independent Test**: Read each iter2 constitution alongside `agents/templates/research_project_constitution.md`, mark each contract item (a)-(f) per data-model.md E2, confirm no `{{token}}` survives, confirm the chemistry constitution's Reproducibility Requirements names QM9 / MD17 (or whichever data source the idea cites). Per spec.md US2 acceptance scenarios 1-3.

### Implementation for User Story 2

- [X] T023 [P] [US2] Audit PROJ-261-iter2's constitution: open `projects/PROJ-261-…-iter2/.specify/memory/constitution.md` side-by-side with `agents/templates/research_project_constitution.md`. Fill in the six-row audit table from `contracts/diagnostic-report.md` § 3.X.1 (heading / footer / inherited principles / added principles ≤2 / no external citations / Reproducibility-Requirements adapted). Record verdict per row with quoted excerpts.
- [X] T024 [P] [US2] Audit PROJ-262-iter2's constitution: same procedure as T023 against `projects/PROJ-262-…-iter2/.specify/memory/constitution.md`. Pay special attention to row (f) — the Reproducibility-Requirements section MUST name a real chemistry data source (QM9, MD17, or whichever is cited in the iter2's idea body).
- [X] T025 [P] [US2] Token-leak check: `grep -F '{{' projects/PROJ-261-…-iter2/.specify/memory/constitution.md projects/PROJ-262-…-iter2/.specify/memory/constitution.md`. MUST be empty. Per spec.md SC-010.
- [X] T026 [P] [US2] Source-of-truth verification for both siblings: for each of the 9 mechanical files (4 scripts + 5 templates), compute `sha256sum projects/<sibling-id>/.specify/<path>` and compare to `sha256sum .specify/<path>` at repo root. Build the table from `contracts/diagnostic-report.md` § 3.X.4 — all 18 rows (9 files × 2 siblings) MUST show ✓ match.
- [X] T027 [US2] If T023 or T024 surfaces any contract violation: file as defect P2-D## with severity per data-model.md E6 § 4 (CRITICAL for heading/footer/inherited-principles/citations; HIGH for added-principles count; MEDIUM for Reproducibility-Requirements adaptation). Either fix in-PR (with prompt or template patch — see Phase 7 iteration loop) or defer to a follow-up issue. Per spec.md FR-014.

**Checkpoint**: Each iter2 constitution has been audited against its six-item output contract. All deviations are recorded as defects.

---

## Phase 5: User Story 3 - Idempotency audit on init_speckit_in (Priority: P1)

**Goal**: Empirically verify FR-011 / SC-009 — the full `.specify/` tree is byte-identical after a second `init_speckit_in` invocation on a sibling already at `project_initialized`.

**Independent Test**: Compute sha256-per-file manifest before and after second invocation; assert lists are identical. Per spec.md US3 acceptance scenarios 1-3.

### Implementation for User Story 3

- [X] T028 [US3] Before the second invocation, capture the pre-rerun manifest on PROJ-261-iter2: `find projects/PROJ-261-…-iter2/.specify -type f -exec sha256sum {} \; | sort > /tmp/sha-before-261.txt`.
- [X] T029 [US3] Run a direct second invocation of `init_speckit_in`: `python -c "from pathlib import Path; from llmxive.speckit.runner import init_speckit_in; init_speckit_in(Path('projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2'))"`. Expected: completes silently, no exceptions.
- [X] T030 [US3] Compute the post-rerun manifest: `find projects/PROJ-261-…-iter2/.specify -type f -exec sha256sum {} \; | sort > /tmp/sha-after-261.txt`. Diff: `diff /tmp/sha-before-261.txt /tmp/sha-after-261.txt`. MUST be empty. Per data-model.md E8 cross-entity invariants.
- [X] T031 [US3] Quote the pytest output from `pytest tests/phase1/test_idempotency.py::test_project_initializer_skips_existing_constitution -v` (run during T010) verbatim into the diagnostic report's § 3.X.5 as the primary evidence for US3 acceptance scenario 2.
- [X] T032 [US3] If T030 shows ANY divergence (i.e., diff is non-empty): file as CRITICAL defect P2-D## with the specific changed file path and proposed fix. Per spec.md SC-009 — the constitution skip-if-exists fix MUST be in place for SC-009 to pass.

**Checkpoint**: Idempotency is empirically verified at file-content level for at least one iter2 sibling. The pytest harness corroborates the manual sha256 evidence.

---

## Phase 6: User Story 4 - Failure-path induction (Priority: P2)

**Goal**: Induce all three deliberate failure modes per Q2 clarification (backend-unreachable, idea-missing, template-missing) on dedicated sibling iters; verify each produces a loud + recorded failure with state unchanged. Per spec.md US4 / FR-012 / SC-005.

**Independent Test**: After each scenario, the run-log entry MUST have `outcome: failure` with non-empty `failure_reason`, the state YAML's `current_stage` MUST remain `validated`, and no `.specify/memory/constitution.md` MUST exist on the failure-iter sibling. Per spec.md US4 acceptance scenarios 1-2.

### Implementation for User Story 4

- [X] T033 [P] [US4] Scenario 1 (backend unreachable): follow `contracts/induced-failure-runs.md § Scenario 1` exactly. Spawn `PROJ-261-…-iterFAIL-backend` (use `--iter 6` or first available unused iter), export `LLMXIVE_BACKEND_BASE_URL=https://invalid.example.com` for the duration of one orchestrator run, capture stderr / run-log / post-run state, then restore the env. Pass criterion: per spec.md US4 acceptance scenario 2 — failure classified as `TransientBackendError`, state unchanged.
- [X] T034 [P] [US4] Scenario 2 (idea file missing): follow `contracts/induced-failure-runs.md § Scenario 2` exactly. Spawn `PROJ-262-…-iterFAIL-idea` (use `--iter 7`), `rm projects/<sibling-id>/idea/<slug>.md`, run the orchestrator. Per research.md Decision 5: with the T008 fix in place, the agent MUST raise `FileNotFoundError`; the run-log MUST record `outcome: failure` with the exception's repr.
- [X] T035 [P] [US4] Scenario 3 (template file missing): follow `contracts/induced-failure-runs.md § Scenario 3` exactly. Spawn `PROJ-261-…-iterFAIL-template` (use `--iter 8`), `mv agents/templates/research_project_constitution.md agents/templates/research_project_constitution.md.bak`, run the orchestrator, restore the template. Per `project_initializer.py:44`, the agent MUST raise `FileNotFoundError` BEFORE the LLM is invoked (fail-fast on missing template per Constitution Principle V).
- [X] T036 [US4] Cleanup verification: `echo "${LLMXIVE_BACKEND_BASE_URL:-(unset)}"` shows the original value or `(unset)`; `ls -la agents/templates/research_project_constitution.md` shows the file is back in place; `git status agents/templates/` shows clean. Per `contracts/induced-failure-runs.md § Cleanup checklist`.
- [X] T037 [US4] For each of the three induced-failure siblings, set `archived_at: <ISO-8601 UTC>` in their state YAMLs (per spec.md FR-019). The state files remain committed; only the `archived_at` field is added.
- [X] T038 [US4] Commit the three failure-iter siblings + cleanup: `git add projects/PROJ-26{1,2}-…-iterFAIL-*/ state/projects/PROJ-26{1,2}-…-iterFAIL-*.yaml state/run-log/ && git commit -m "phase2/spec-004: induced-failure scenarios + archive (US4, FR-012, #46 #62)"`

**Checkpoint**: All three induced-failure scenarios pass: failures are loud, recorded, state-preserving, and atomic-or-absent on filesystem writes.

---

## Phase 7: Iteration loop (conditional on US2 / US3 / US4 defects)

**Purpose**: Apply prompt/template/code patches if any audit phase surfaced a defect; spawn iter3+ siblings to verify the fix; repeat up to 5 cycles per spec.md FR-005.

**Trigger**: ANY of T023, T024, T025, T026, T030, T033, T034, T035 reveals a defect that warrants in-PR fix per spec.md FR-014. Skip Phase 7 entirely if no defects surfaced.

### Implementation for Iteration loop (conditional)

- [X] T039 [US2] [conditional] If T023/T024 surfaced a constitution-content defect (e.g., dropped principle, fabricated citation, missing data-source adaptation): patch the affected source — `agents/prompts/project_initializer.md` (most common) or `agents/templates/research_project_constitution.md` — bumping the agent's `prompt_version` in `agents/registry.yaml` per the spec-003 semver policy (MAJOR/MINOR/PATCH per the change kind). Same commit MUST include both the prompt/template patch AND the version bump. **Verify the bump landed**: after each iteration commit, run `git show --stat HEAD -- agents/registry.yaml` and confirm the `prompt_version` line for `project_initializer` shows the version diff. If the registry didn't change but a prompt/template did, the commit violates FR-020 — amend the commit to include the bump before pushing.
- [X] T040 [US2] [conditional] After T039: spawn iter3 siblings of the affected canonicals (`python tests/phase1/sibling_project.py <canonical> --iter 3 --start-stage validated`). Re-run `project_initializer` on each. Re-audit per T023/T024. If still failing AND iteration count <5: return to T039 for another patch. If iteration count = 5 and still failing: file follow-up issue, mark defect `Deferred to issue #<N>` in §4 of report, exit the loop. Per FR-005.
- [X] T041 [US3] [conditional] If T030 showed sha256 divergence: investigate. Either the T007 skip-if-exists guard isn't working (revert + re-investigate) or `init_speckit_in` is mutating an unexpected file (file as defect against `src/llmxive/speckit/runner.py`). Patch + commit + re-run T028-T030.
- [X] T042 [US4] [conditional] If T033/T034/T035 surfaced any failure-handling defect (silent state advancement, empty `failure_reason`, partial constitution write): patch the relevant agent or orchestrator code, commit with version bump if a registry-tracked prompt was patched, re-run the affected scenario.
- [X] T043 [conditional] For each iteration, capture a §5 subsection in the diagnostic report with the verbatim `git diff <prev-SHA> <curr-SHA> -- <path>` block per spec.md FR-008 / `contracts/diagnostic-report.md § Section 5`.

**Checkpoint**: Either all defects fixed (and iter3+ siblings exist with passing audits) or all unresolved defects deferred to follow-up issues. Iteration count never exceeds 5 per agent (FR-005 hard cap).

---

## Phase 8: User Story 5 - Verbatim diagnostic report (Priority: P1)

**Goal**: Author a single Markdown file at `notes/2026-05-05-phase2-diagnostic.md` quoting every artifact verbatim from US1-US4 + iteration loops, evaluating each against issue #62's three acceptance criteria with severity-tagged defects. Per spec.md US5 / FR-013 / `contracts/diagnostic-report.md`.

**Independent Test**: Reading the report top-to-bottom, every checkbox in issue #62 has an explicit pass/fail verdict tied to a quoted artifact, every defect has severity + file:line + status, every CRITICAL defect has `Fixed in PR <SHA>` or `Deferred to issue #<N>`. Per spec.md US5 acceptance scenarios 1-3.

### Implementation for User Story 5

- [X] T044 [US5] Create `notes/2026-05-05-phase2-diagnostic.md` with the frontmatter block per `contracts/diagnostic-report.md`'s "Frontmatter" section (spec link, generation timestamp, branch name, final commit, parent issue, tracker).
- [X] T045 [US5] Write Section 1 (Inputs): tables per `contracts/diagnostic-report.md § Section 1` covering both canonicals and both iter2 siblings; quote spawner stderr from T013/T014 as sha256-clone evidence.
- [X] T046 [US5] Write Section 2 (Agent behavior): six subsections per sibling × N siblings (2 happy-path + ≥3 induced-failure + ≥0 iter3+). Each contains pre-run state YAML, rendered system prompt, rendered user prompt, LLM response, run-log JSONL line, post-run state YAML — all verbatim. Per `contracts/diagnostic-report.md § Section 2`.
- [X] T047 [US5] Write Section 3 (Outputs): for each happy-path sibling, the constitution audit table (T023/T024), the full constitution quote (with `[truncated…]` markers if >100 lines), the token-leak check (T025), the source-of-truth verification table (T026), and the idempotency check (T028-T031 for the chosen US3 sibling). Per `contracts/diagnostic-report.md § Section 3`.
- [X] T048 [US5] Write Section 4 (Defects table) with the running list of P2-D## defects from US2 / US3 / US4 / iteration loops. P2-D01 (constitution skip-if-exists, fixed by T007), P2-D02 (sibling allowlist extension, fixed by T004), P2-D03 (idea-missing fail-fast, fixed by T008) are pre-known; append any new defects discovered during US1-US4. Per `contracts/diagnostic-report.md § Section 4`.
- [X] T049 [US5] Write Section 5 (Iteration diffs) — only if Phase 7 ran. Otherwise this section is the single line `No iteration loops fired; iter2 happy-path was sufficient on first pass.` per `contracts/diagnostic-report.md § Section 5`.
- [X] T050 [US5] Write Section 6 (Per-issue acceptance-criteria summary): two tables, one for issue #62 (3 checkboxes) and one for issue #46 (5 checkboxes). Each row marked PASS / FAIL with rationale tied to a quoted artifact from §2 or §3. Per `contracts/diagnostic-report.md § Section 6`.
- [X] T051 [US5] Write Section 7 (Recommendations): bulleted lists of recommended Phase-2 changes going forward, follow-up issues opened/recommended, items deliberately accepted-as-is. Per `contracts/diagnostic-report.md § Section 7`.
- [X] T052 [US5] Verify all artifacts referenced in §1-§6 exist on disk and the quotes are exact (run `diff <(grep -A 100 "constitution.md" notes/2026-05-05-phase2-diagnostic.md | head -100) <(head -100 projects/PROJ-261-…-iter2/.specify/memory/constitution.md)` etc. spot-checks for ≥3 random quoted artifacts).
- [X] T053 [US5] Commit the diagnostic report: `git add notes/2026-05-05-phase2-diagnostic.md && git commit -m "phase2/spec-004: diagnostic report (US5, FR-013, #46 #62)"`

**Checkpoint**: Single report at `notes/2026-05-05-phase2-diagnostic.md` covers everything Phase 2 produced + verdict per issue #62 / #46 acceptance criterion.

---

## Phase 9: User Story 6 - Carry-forward gate (Priority: P2)

**Goal**: Author `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` naming 1-2 iter2 siblings (or canonicals + iter2 IDs) that pass the US2 audit cleanly, providing the input substrate for spec 005 (Phase 3 — Specifier + Clarifier).

**Independent Test**: Read the manifest; confirm each named project ID corresponds to a real `projects/<id>/` directory at `current_stage: project_initialized` with a complete `.specify/` scaffold; confirm each named commit hash resolves to a real commit on the feature branch; confirm `phase2_iter2_id` field names a real iter2 sibling whose constitution passed the US2 audit. Per spec.md US6 acceptance scenarios 1-3.

### Implementation for User Story 6

- [X] T054 [US5/US6] Decide carry-forward selection based on the diagnostic report's §6 verdicts: pick 1-2 iter2 siblings whose constitutions passed all six US2 audit items at PASS (no FAIL on any row). If both iter2 siblings have unresolved CRITICAL defects, fall back to carrying forward the canonical PROJ-261/PROJ-262 from spec 003 (with the iter2 sibling's audited constitution copied in) — record this as a sub-decision in §8 of the report. Per spec.md US6.
- [X] T055 [US6] Author `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` per `contracts/carry-forward.md` schema: `spec`, `generated_at`, `final_commit`, `projects[*]` with `project_id`, `final_state`, `final_commit`, `phase2_iter2_id`, `agents_run`, `justification`. The `agents_run` list MUST include all four Phase-1 agents (brainstorm / flesh_out / research_question_validator / project_initializer) plus the iteration counts from spec 003 + this spec. Per spec.md FR-017.
- [X] T056 [US6] Validate the manifest manually against the schema in `contracts/carry-forward.md`: every cross-field invariant satisfied (each `phase2_iter2_id` resolves to a real iter2 sibling at `project_initialized`; each `final_commit` resolves on the branch; no >2 entries; no <1 entry). Document the validation in §6 of the report under "Schema validation" row.
- [X] T057 [US6] Write Section 8 (Carry-forward decision) of the diagnostic report: name the selected sibling IDs, quote each named project's full state YAML, write a ≤200-word justification per selection covering whether the constitution passed US2 cleanly + whether idempotency held + which domain principles the LLM added + caveats for spec 005. Per `contracts/diagnostic-report.md § Section 8`.
- [X] T058 [US6] Commit the carry-forward manifest + report update: `git add specs/004-phase2-project-bootstrap-testing/carry-forward.yaml notes/2026-05-05-phase2-diagnostic.md && git commit -m "phase2/spec-004: carry-forward manifest + report § 8 (US6, FR-017, #46 #62)"`
- [X] T058a [US6] Archive any iter2 happy-path siblings NOT named in `carry-forward.yaml` (per FR-019 — non-selected siblings MUST be marked archived, not deleted). For each unselected `<sibling-id>` from {PROJ-261-…-iter2, PROJ-262-…-iter2, plus any iter3+ from Phase 7}: append an `archived_at: <ISO-8601 UTC>` field to its `state/projects/<sibling-id>.yaml` (same pattern as T037 for failure-iter siblings). Confirm with `grep archived_at state/projects/PROJ-26*-iter*.yaml`. Commit: `git add state/projects/ && git commit -m "phase2/spec-004: archive non-selected iter2 siblings (FR-019, US6, #46 #62)"`. Skip this task entirely if every spawned iter2 sibling appears in `carry-forward.yaml`.

**Checkpoint**: spec 005 can `cat specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` and pick its substrate without re-discovering anything.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Run the full test suite, close issues, update tracker #107, push, open PR.

- [X] T059 [P] Run the full pytest suite to confirm no regression: `pytest tests/phase1/ -v`. All spec-003 tests (citation_resolver) must still pass; new spec-004 tests (idempotency) must all pass. If any test fails: stop, fix the underlying code (do NOT loosen tests per CLAUDE.md), commit the fix, retry.
- [X] T060 [P] Run any project linters: `ruff check .` and `pyright` (or whatever the project's existing lint/type-check toolchain is). Any new errors introduced by T004-T011 fixes MUST be resolved before continuing.
- [ ] T061 Tick the Phase 2 box in tracking issue #107. Note: GitHub's issue body may have whitespace variations after rendering, so prefer a Python regex over a fragile `sed` literal: `gh issue view 107 --json body -q .body > /tmp/issue107.md && python3 -c "import re,sys; t=open('/tmp/issue107.md').read(); open('/tmp/issue107.md','w').write(re.sub(r'- \[ \] #46\b', '- [x] #46', t, count=1))" && gh issue edit 107 --body-file /tmp/issue107.md`. Verify the edit by re-fetching the issue body and confirming `- [x] #46` appears.
- [ ] T062 Close issue #62 (project_initializer agent): `gh issue close 62 --comment "Resolved via spec 004 (commit <SHA>). See diagnostic report at notes/2026-05-05-phase2-diagnostic.md and carry-forward manifest at specs/004-phase2-project-bootstrap-testing/carry-forward.yaml. All three acceptance criteria pass per § 6 of the report."` — substitute `<SHA>` with the final commit hash.
- [ ] T063 Close issue #46 (Phase 2 parent): `gh issue close 46 --comment "Phase 2 verified end-to-end via spec 004 (commit <SHA>). All five acceptance-criterion checkboxes in this issue pass per § 6 of the diagnostic report. Carry-forward manifest names <K> sibling(s) for spec 005."`
- [ ] T064 Push the feature branch: `git push origin 008-phase2-project-bootstrap-testing`.
- [ ] T065 Open the PR: use `gh pr create --base main --head 008-phase2-project-bootstrap-testing --title "Spec 004: Phase 2 (Project Bootstrap) end-to-end testing" --body "$(cat <<'EOF'`...heredoc...`EOF`...`)"`. The full PR body block is defined verbatim in [quickstart.md § Step 10](./quickstart.md) — copy it inline into the heredoc. Confirm the PR body renders correctly on GitHub before continuing (any unescaped backticks or special chars will display as raw markup).
- [ ] T066 [P] Add the PR URL to a comment on tracking issue #107 for easy navigation.
- [X] T067 Update spec.md's `**Status**` line from `Draft` to `In Review` (or `Merged` after merge). Recommended approach is a manual edit (open the file, change the literal `**Status**: Draft` to `**Status**: In Review`) since `sed` on macOS BSD can mishandle markdown asterisks; alternatively use `python3 -c "import re,sys; p='specs/004-phase2-project-bootstrap-testing/spec.md'; t=open(p).read(); open(p,'w').write(re.sub(r'^\*\*Status\*\*: Draft\s*$', '**Status**: In Review', t, count=1, flags=re.MULTILINE))"`. Verify with `head -10 specs/004-phase2-project-bootstrap-testing/spec.md | grep Status`.

**Checkpoint**: PR open. All issues updated. Tracker reflects Phase 2 complete pending merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup, T001-T003)**: No dependencies — preflight only
- **Phase 2 (Foundational, T004-T012)**: Depends on Phase 1 completion. **BLOCKS US1-US6.**
- **Phase 3 (US1, T013-T022)**: Depends on Phase 2 complete. P1 / MVP.
- **Phase 4 (US2, T023-T027)**: Depends on Phase 3 complete (audits the iter2 outputs).
- **Phase 5 (US3, T028-T032)**: Depends on Phase 3 complete + T009/T010 idempotency tests passing. Can run in parallel with Phase 4.
- **Phase 6 (US4, T033-T038)**: Depends on Phase 2 complete (independent of Phase 3-5; spawns its own dedicated failure-iter siblings).
- **Phase 7 (Iteration loop, T039-T043)**: CONDITIONAL — only if Phase 4 / 5 / 6 surfaced defects. Iterates per FR-005 5-cycle cap.
- **Phase 8 (US5 report, T044-T053)**: Depends on Phases 3-7 complete (report quotes their artifacts).
- **Phase 9 (US6 carry-forward, T054-T058)**: Depends on Phase 8 complete (selection driven by report verdicts).
- **Phase 10 (Polish, T059-T067)**: Depends on Phase 9 complete.

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no inter-story dependencies.
- **US2 (P1)**: After US1 — audits US1's outputs.
- **US3 (P1)**: After US1 + T009 idempotency tests passing — verifies idempotency on US1's iter2 output.
- **US4 (P2)**: After Phase 2 — independent of US1-US3 (spawns its own dedicated failure-iter siblings, using the T004 spawner extension and the T008 fail-fast guard).
- **US5 (P1)**: After US1-US4 (+ Phase 7 if it ran) — quotes everything.
- **US6 (P2)**: After US5 — selection driven by §6 verdicts of the report.

### Within Each User Story

- Spawn siblings before running the orchestrator on them.
- Run the orchestrator before snapshotting state YAML / run-log entries.
- Audit before filing defects.
- Tests pass before committing the patch they cover.
- Commit after each task or logical group, per CLAUDE.md guidance.

### Parallel Opportunities

- T013, T014 (spawn PROJ-261-iter2 + PROJ-262-iter2) can run in parallel — different sibling IDs.
- T009 (test_idempotency.py) and T012 (router verification) are independent and can run in parallel.
- T023, T024, T025, T026 (US2 audit subtasks) are different files / different commands — fully parallel.
- T028-T030 (US3 sha256 sequence) is sequential per sibling, but can run in parallel for PROJ-262-iter2 if you want to audit both (the spec's MVP only requires one US3 sibling).
- T033, T034, T035 (US4 induced-failure scenarios) can run in parallel — different sibling-iter IDs and different precondition mutations. **WARNING**: T035 (template rename) is mutually exclusive with T033/T034 if those need the template too. Suggest sequential execution of US4 with explicit setup/teardown per scenario.
- T044-T053 (US5 report sections) are independent within the same file — can be drafted in parallel but committed together at T053.
- T059, T060 (test + lint) can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Spawn both iter2 siblings in parallel:
python tests/phase1/sibling_project.py PROJ-261-evaluating-the-impact-of-code-duplicatio --iter 2 --start-stage validated &
python tests/phase1/sibling_project.py PROJ-262-predicting-molecular-dipole-moments-with --iter 2 --start-stage validated &
wait

# Then run project_initializer SEQUENTIALLY on each (the orchestrator
# isn't designed for concurrent invocations on different projects, and
# Dartmouth's free tier rate-limits concurrent calls anyway):
python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2 --max-tasks 1
python -m llmxive run --project PROJ-262-predicting-molecular-dipole-moments-with-iter2 --max-tasks 1
```

## Parallel Example: User Story 2 audits

```bash
# All four subtasks operate on different files / different commands:
diff <(cat agents/templates/research_project_constitution.md) <(cat projects/PROJ-261-…-iter2/.specify/memory/constitution.md) > /tmp/audit-261-side-by-side.diff &
diff <(cat agents/templates/research_project_constitution.md) <(cat projects/PROJ-262-…-iter2/.specify/memory/constitution.md) > /tmp/audit-262-side-by-side.diff &
grep -F '{{' projects/PROJ-261-…-iter2/.specify/memory/constitution.md projects/PROJ-262-…-iter2/.specify/memory/constitution.md > /tmp/token-leak-check.log &
# T026 source-of-truth verification (loop over 9 mechanical files × 2 siblings)
wait
```

---

## Implementation Strategy

### MVP First (US1 only, with Phase 1+2 prerequisites)

1. Phase 1 (T001-T003): preflight checks
2. Phase 2 (T004-T012): the two production-code patches + idempotency tests + retry policy verification — **most-critical chunk of the spec**
3. Phase 3 (T013-T022): two iter2 siblings spawned + project_initializer run on each
4. **STOP and VALIDATE**: `cat projects/PROJ-26{1,2}-…-iter2/.specify/memory/constitution.md` and inspect manually
5. If both look reasonable: continue to Phase 4-9 for the full audit + report. If either looks broken: skip to Phase 7 iteration loop on the affected canonical.

### Incremental Delivery

1. Phase 1+2 → Foundation ready (the two production fixes are the most reusable artifact this spec produces; once they land, future phase-test specs (005-007) inherit them)
2. Phase 3 → MVP: project_initializer demonstrably runs end-to-end on real iter2 siblings
3. Phase 4-5 → Audit verdict: do the iter2 outputs pass their content + idempotency contracts?
4. Phase 6 → Failure paths verified: Constitution Principle V satisfied for Phase 2
5. Phase 8-9 → Diagnostic report + carry-forward manifest (the substrate spec 005 will read)
6. Phase 10 → Issues closed, PR open, tracker updated

### Parallel Team Strategy (single-developer fallback)

This spec is designed for a single maintainer. The parallel opportunities listed above are advisory — single-threaded execution is fully supported and is the expected primary path. The estimated total wall-clock with single-threaded execution is ~3.5h on the happy path (per quickstart.md Step 10), up to ~9h if Phase 7 iteration triggers.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks within the same phase
- [Story] label maps task to specific user story for traceability per `/speckit-tasks` rules
- Each user story can be independently demonstrated to a reviewer (per spec.md's "Independent Test" sections)
- Tests in T009-T010 must pass BEFORE T011 commits — verify failure path is detected (negative control test in test_idempotency.py)
- Commit after each Phase checkpoint or logical group, per CLAUDE.md "frequent commits" guidance
- Stop at any checkpoint to validate; resume by re-reading the current Phase's task list
- Avoid: vague tasks (every task has a concrete file path), same-file conflicts (P-marked tasks verified independent), cross-story dependencies that break independence (US1-US6 mostly independent except where audit depends on output)
- Defects discovered during US1-US4 auto-trigger Phase 7 iteration loop; once Phase 7 exits (either fix or defer), Phase 8 report generation can begin
- The diagnostic report is the single source of truth for "what Phase 2 did" — every artifact, every verdict, every defect, every selection rationale lives in one Markdown file at `notes/2026-05-05-phase2-diagnostic.md`
