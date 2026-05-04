# Tasks: Phase 1 (Idea Lifecycle) End-to-End Testing & Diagnostics

**Feature**: Phase 1 (Idea Lifecycle) End-to-End Testing & Diagnostics
**Branch**: `003-phase1-idea-lifecycle-testing`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md) | **Data model**: [data-model.md](./data-model.md) | **Contracts**: [contracts/](./contracts/) | **Quickstart**: [quickstart.md](./quickstart.md)

This task list is organized by user story so each story can be implemented and verified independently. The diagnostic itself is mostly maintainer-driven (running the orchestrator, evaluating outputs, iterating prompts), so most "tasks" are runbook steps with verification gates rather than code-only work. Code tasks (resolver, sibling spawner, validator) are clearly marked with file paths.

---

## Phase 1: Setup

Project-wide preconditions that must be true before any user-story work begins.

- [X] T001 Verify branch + clean tree: run `git status --short` from repo root and confirm output is empty (or only OMC tooling files); if not clean, commit or stash any in-progress work first. **Done**: spec-kit artifacts committed in dd27cfe.
- [X] T002 Verify Dartmouth Chat key: run `test -n "$DARTMOUTH_CHAT_API_KEY" && echo OK` from repo root; if MISSING, set the env var from the GitHub repo secret before continuing. **Done**: env var unset, but `~/.config/llmxive/credentials.toml` (mode 0600) contains `dartmouth_chat_api_key`; `src/llmxive/credentials.py` resolves env-var-then-file, so the orchestrator works as-is. See `notes/credentials-location.md`.
- [X] T003 Verify orchestrator entrypoint: run `python -m llmxive run --help | head -5` from repo root and confirm the usage line names `--max-tasks`. **Done**: `usage: llmxive run [-h] [--max-tasks MAX_TASKS] [--project PROJECT] [--stage STAGE]`.
- [X] T004 Create test directory: `mkdir -p tests/phase1` and add empty `tests/phase1/__init__.py`. **Done** in dd27cfe.

## Phase 2: Foundational (blocking prerequisites for all user stories)

Diagnostic-only helpers that every user story depends on. These MUST be implemented and self-tested before any agent run.

- [X] T005 [P] Implement citation resolver script per `specs/003-phase1-idea-lifecycle-testing/contracts/citation-resolver.md` in `tests/phase1/citation_resolver.py` — argparse CLI with `<idea_md_path>`, `--timeout`, `--self-test`; regex extraction of arxiv/doi/url/inline_url citations; per-kind resolution rules (arxiv API, doi.org HEAD with redirect-follow, url HEAD with GET-fallback on 405); thread-pool `Future.result(timeout=N)` per citation; JSON stdout with `ResolutionResult` records; stderr progress lines; exit codes 0/1/2/64. **Done**.
- [X] T006 [P] Implement citation resolver pytest suite in `tests/phase1/test_citation_resolver.py` — at minimum: (a) self-test passes (b) known-good arXiv (`1706.03762`) returns `resolved` (c) known-bad URL (`https://example.invalid/never-existed`) returns `unreachable` (d) DOI redirect resolves (e) timeout fires cleanly on a deliberately-slow URL. Use real HTTP per Constitution principle III. **Done — 11 tests, all pass.**
- [X] T007 [P] Implement sibling project spawner script per `specs/003-phase1-idea-lifecycle-testing/contracts/sibling-project.md` in `tests/phase1/sibling_project.py` — argparse CLI with `<canonical_project_id>`, `--iter N`, `--start-stage`; validation that canonical exists and sibling does not; idea-seed copy with sha256 verify; fresh state YAML write; stdout = sibling project ID; stderr = verbose progress; exit codes 0/1/2/64. **Done**.
- [X] T008 [P] Implement carry-forward validator script (informative, optional per contract) in `tests/phase1/validate_carry_forward.py` — load `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`, walk each `project_id`, confirm project dir + state YAML at `project_initialized` + idea file parses to ≥1 citation; print pass/fail per project; exit non-zero only on parse errors. **Done**.
- [X] T009 Run citation-resolver self-test: `python tests/phase1/citation_resolver.py --self-test` — confirm exit 0 and stderr `[self-test] A: resolved; B: unreachable`. **Done — exit=0, stderr matched.**
- [X] T010 Run citation-resolver pytest: `pytest tests/phase1/test_citation_resolver.py -v` — confirm all tests pass against real HTTP. **Done — 11/11 passed in 11.29s. Note: fixed a real-world failure case where DOI redirects ending in 401/403/429 with non-empty redirect history are now classified as `ambiguous` (paywall/login-wall — Stage 2 territory) rather than `unreachable` — improves resolver accuracy and aligns with the contract's intent.**
- [X] T011 Initialize empty diagnostic report at `notes/2026-05-04-phase1-diagnostic.md` with the Section 1 header per `contracts/diagnostic-report.md` (date range placeholder, branch name, final-commit-at-report-time placeholder, backend = Dartmouth Chat). **Done**.
- [ ] T012 Commit foundational work: `git add tests/phase1/ notes/2026-05-04-phase1-diagnostic.md && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: foundational helpers + diagnostic report skeleton (#45)"`.

**Checkpoint**: Foundational phase complete. T005-T011 must all be green before starting any user story.

---

## Phase 3: User Story 1 — Brainstorm pool quality, iterated to a usable bar (P1)

**Goal**: Build a brainstorm pool of 8 seeds per cohort, iterate the prompt until at least 2-3 seeds clearly meet issue #59 + FR-003a scope filter.

**Independent test**: Each cohort can be evaluated independently — read the 8 seeds, render pass/fail per acceptance criterion in the report.

- [X] T013 [US1] Apply FR-003a scope content tightening to `agents/prompts/brainstorm.md` — review existing SCOPE CONSTRAINTS (lines 50-79), add explicit in-scope clause naming literature review / locally-simulable ≤1h / analyzable on small-medium datasets ≤1h / single core question; ensure out-of-scope clause covers external data collection, external experimentation, trivial/non-impactful. Bump `prompt_version` in `agents/registry.yaml` for `brainstorm` from `1.0.0` to `1.1.0`. Commit as `phase1: brainstorm prompt — encode FR-003a scope filter (#45 #59)`. **Done in commit `be4bee0`** — added IDEA-TYPE SCOPE subsection (45 lines) below the existing infrastructure-envelope section.
- [X] T014 [US1] Run cohort 1: `python -m llmxive brainstorm --count 8` from repo root. **Defect D0 fix**: the original command `python -m llmxive run --max-tasks 1 --stage brainstormed` was wrong — `run` advances *existing* projects rather than creating new ones. The correct entry point for fresh cohort generation is the dedicated `_cmd_brainstorm` subcommand (per `src/llmxive/cli.py`), which calls the same Brainstorm agent with the same prompt+backend stack but writes a fresh `Project` state row at `current_stage: brainstormed`. Verify 8 new `projects/PROJ-NNN-<slug>/` directories appear; verify each has `idea/<slug>.md`; verify 8 new `state/projects/<id>.yaml` entries exist. **Done in commit `f2dcf9f`** — cohort 1 produced PROJ-261..268 across 6 fields.
- [X] T015 [US1] Commit cohort 1: `git add projects/ state/ && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: brainstorm cohort 1 (8 seeds)"`. Capture the resulting short-SHA for the report. **Done in commit `f2dcf9f`**.
- [X] T016 [US1] Cohort 1 review: read all 8 `idea/<slug>.md` files; for each, render pass/fail against issue #59 acceptance criteria (4 items) + FR-003a scope filter; record per-seed verdict + per-cohort defect summary in `notes/2026-05-04-phase1-diagnostic.md` Section 3 (Brainstorm — Cohort 1) with verbatim quotes per FR-006 and per-project state-YAML before/after quotes per FR-007. **Done** — see `notes/2026-05-04-phase1-diagnostic.md` Section 3 (Brainstorm — Cohort 1). 3 strong candidates (PROJ-262/267/268), 3 reject (PROJ-263/264/265), 2 borderline (PROJ-261/266). Defects D0-D4 logged.
- [X] T017 [US1] Decision gate: if ≥3 cohort-1 seeds clearly meet both bars, skip to T024 (write provisional carry-forward candidate list); otherwise continue with T018 (iterate). **Skipping iteration** — cohort 1 yielded 3 strong candidates (PROJ-262, 267, 268). Defect-driven prompt patches D2/D3/D4 are deferred to follow-up issues per the spec's bounded-iteration rule.
- [ ] T018 [US1] Iterate brainstorm prompt for cohort 2: identify the most common defect from T016, draft ONE focused patch to `agents/prompts/brainstorm.md`, bump `prompt_version` to `1.2.0` in `agents/registry.yaml`. Commit as `phase1: brainstorm prompt patch — <defect> (#45 #59)`.
- [ ] T019 [US1] Run cohort 2: same commands as T014 — generate 8 fresh seeds.
- [ ] T020 [US1] Commit cohort 2: same pattern as T015.
- [ ] T021 [US1] Cohort 2 review: same pattern as T016, plus quote the iteration diff (`git diff <cohort1-prompt-sha> <cohort2-prompt-sha> -- agents/prompts/brainstorm.md`) verbatim in the report's Section 5 per FR-008.
- [ ] T022 [US1] Iteration gate: if cohort 2 clears the bar, advance to T024; if not, continue iterating up to **5 cohorts total per FR-005**. Each cohort follows the T018-T021 pattern (patch → run → commit → review → diff). On cohort 5 if still failing, mark residual defects "deferred" and proceed with the best 2-3 seeds available; file a follow-up issue per FR-013(b).
- [ ] T023 [US1] Induced-failure brainstorm run (FR-015): `DARTMOUTH_CHAT_API_KEY=invalid_test_$RANDOM python -m llmxive run --max-tasks 1`. Verify orchestrator exits non-zero; verify run-log entry under `state/run-log/2026-05/` shows `outcome: "failure"` with non-null `failure_reason`; verify no new project state advances past `brainstormed`. Quote the failure run-log entry verbatim in report Section 3 ("Induced failure-mode run") per FR-015.
- [ ] T024 [US1] Provisional carry-forward candidate list: hand-select 2-3 projects from the most recent quality cohort whose seeds meet both bars; record in the diagnostic report's "Carry-forward candidates" subsection with project IDs + short rationale (note this is provisional pending US2/US3 outcomes). **SC-008 record (C4)**: also record per-candidate the number of brainstorm cohorts run (`brainstorm_iterations: <int>`, must be 1 ≤ N ≤ 5 per FR-005); this value is the source for the brainstorm row of `agents_run` in `carry-forward.yaml` (T049).

**Independent verification (US1)**: read `notes/2026-05-04-phase1-diagnostic.md` Section 3 (Brainstorm) and confirm: every cohort has 8 seeds quoted verbatim; every per-seed acceptance criterion is marked pass/fail with rationale; every iteration diff is quoted; the induced-failure run is quoted; 2-3 candidates are named.

---

## Phase 4: User Story 2 — Flesh_out runs on each selected project, iterated to a usable bar (P1)

**Goal**: Run flesh_out on each US1-selected project; verify all citations resolve at 100% via the two-stage pipeline; iterate flesh_out prompt up to 5 sibling iterations per project until quality bar met.

**Independent test**: Each selected project's flesh_out output can be audited independently (citation resolution per project, acceptance-criteria evaluation per project).

- [ ] T025 [US2] For each US1-candidate project (call this loop iteration k of 2-3), invoke `python -m llmxive run --project <PROJ-id-k> --max-tasks 1` and verify state advances to `flesh_out_complete`; the same `idea/<slug>.md` file is rewritten with motivation/related-work/expected-results/methodology sections; one fresh run-log entry appears.
- [ ] T026 [US2] Commit per-project flesh_out (one commit per project): `git add projects/<PROJ-id-k>/ state/ && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: flesh_out <PROJ-id-k> (iter1)"`.
- [ ] T027 [US2] Stage 1 citation resolution per project: `python tests/phase1/citation_resolver.py projects/<PROJ-id-k>/idea/<slug>.md > projects/<PROJ-id-k>/idea/citation_resolution.json` for each k. Quote the resulting JSON verbatim in the diagnostic report Section 4 (Citation resolution audit) per FR-010.
- [ ] T028 [US2] Stage 2 citation verifier (agent) per ambiguous citation: for any citation with `stage1_status == "ambiguous"` in the JSON from T027, dispatch an agent verifier (scientist agent with web access; use the `Agent` tool with `subagent_type: "oh-my-claudecode:scientist"`). **Use this exact prompt template per citation (U3)** — substitute the bracketed slots with values from the citation's `ResolutionResult` record:

  ```text
  You are verifying a single academic citation produced by another LLM agent.

  Citation raw text: [citation.raw_text]
  Citation kind: [citation.kind]
  Citation identifier: [citation.identifier]
  Stage 1 (mechanical) status: [stage1_status]
  Stage 1 evidence (URL checked, HTTP status, redirect chain, API snippet): [stage1_evidence verbatim]

  Your task: confirm whether the cited paper, dataset, or repository actually exists at the indicated source AND matches the title/year/authors implied by the citation's raw text. You may fetch the URL, query the relevant API, or search for the paper title.

  Respond with EXACTLY one of:
    - VERIFIED: <1-3 sentences citing what you found that confirms the source>
    - REJECTED: <1-3 sentences citing what you found that contradicts the source (e.g., URL 404s, paper title at the URL doesn't match, the cited author is not on the paper)>
    - UNCLEAR: <1-3 sentences citing why you can't confidently confirm or refute>

  Do NOT guess. UNCLEAR is acceptable. Do NOT include preamble.
  ```

  Record the agent's verdict (VERIFIED / REJECTED / UNCLEAR) and the 1-3 sentence evidence per citation in the report Section 4 ("Stage 2 (agent verifier) output"). Per FR-010, only `VERIFIED` advances `final_verdict` to `verified`; both `REJECTED` and `UNCLEAR` cause the citation to fail the 100% gate.
- [ ] T029 [US2] Per-project verdict gate: for each k, every citation MUST end with `final_verdict: "verified"` (per FR-010 / SC-005 — 100% threshold). If any citation fails, advance to T030 (iterate flesh_out for that project); otherwise, project k passes and moves to US3.
- [ ] T030 [US2] Spawn sibling for failing project: `python tests/phase1/sibling_project.py <PROJ-id-k> --iter 2` — capture the new sibling project ID. Commit the new sibling: `git add projects/ state/ && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: spawn flesh_out iter2 sibling for <PROJ-id-k>"`.
- [ ] T031 [US2] Patch `agents/prompts/flesh_out.md` (or the lit_search code under `src/llmxive/`) to address the citation-resolution defect class (e.g., add stronger "verify before citing" imperative; add tool-use example; require `[unverified]` tags when the agent can't find a source). Bump flesh_out's `prompt_version` in `agents/registry.yaml`. Commit as `phase1: flesh_out prompt patch — <defect> (#45 #60)`.
- [ ] T032 [US2] Run flesh_out on sibling: `python -m llmxive run --project <PROJ-id-k>-iter2 --max-tasks 1`. Commit as `phase1: flesh_out <PROJ-id-k>-iter2 (iter2)`.
- [ ] T033 [US2] Re-run citation resolution on the sibling (T027 + T028). If still failing, spawn iter3 (T030-T032 pattern) — cap at **5 iterations per project per FR-005**.
- [ ] T034 [US2] Per-project iteration diff: quote `git diff <iter1-commit>:projects/<PROJ-id-k>/idea/<slug>.md <iterN-commit>:projects/<PROJ-id-k>-iterN/idea/<slug>.md` verbatim in the report Section 5 per FR-008. **SC-008 record (C4)**: also record per-project the final flesh_out iteration count (`flesh_out_iterations: <int>`, 1 ≤ N ≤ 5 per FR-005) — this is the source for the flesh_out row of `agents_run` in `carry-forward.yaml` (T049).
- [ ] T035 [US2] Per-project acceptance-criteria evaluation: render pass/fail against issue #60's 5 criteria (reads seed → writes idea.md; every prior-work claim has resolvable citation; hypothesis is testable; evaluation plan names datasets/metrics that exist; emits scope_rejected.yaml on infeasibility) plus the citation-resolution verdict from T029. Record in report Section 3 (Flesh_out subsection) per FR-009.

**Independent verification (US2)**: read `notes/2026-05-04-phase1-diagnostic.md` Section 3 (Flesh_out) and Section 4 (Citation resolution audit) and confirm: every selected project has at least one flesh_out run quoted verbatim; every citation has both Stage 1 and Stage 2 verdicts (where applicable) quoted; the 100% citation-verification gate passes for at least 2-3 projects (else they don't advance to US3).

---

## Phase 5: User Story 3 — Idea_selector runs on each flesh_out'd project, iterated to a usable bar (P1)

**Goal**: For each project that passed US2 (all citations verified), run idea_selector; iterate up to 5 sibling iterations per project until the maintainer endorses the agent's verdict.

**Independent test**: Each project's idea_selector verdict + rationale can be audited independently.

- [ ] T036 [US3] For each project that passed US2 (call this final iteration ID `<PROJ-id-final-k>`), invoke `python -m llmxive run --project <PROJ-id-final-k> --max-tasks 1` and verify state advances to `project_initialized` (promote) or rolls back to `brainstormed` (reject). Verify a run-log entry appears with the verdict.
- [ ] T037 [US3] Commit per-project idea_selector run: `git add projects/<PROJ-id-final-k>/ state/ && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: idea_selector <PROJ-id-final-k> (iter1)"`.
- [ ] T038 [US3] Per-project verdict review: read the agent's verdict (state YAML transition) AND rationale (from run-log `outputs` or `idea/selection_decision.md` if present). Render an independent maintainer verdict: would I have made the same call with the same reasoning? **Format (U1)**: record the comparison in report Section 3 (Idea_selector subsection) as an inline fenced-block markdown table with these exact columns and one row per project:

```markdown
| Project | Agent verdict | Agent rationale (verbatim quote) | Maintainer verdict | Maintainer rationale | Match |
|-|-|-|-|-|-|
| PROJ-NNN-<slug>[-iterN] | promote \| reject | <quoted from run-log or selection_decision.md> | promote \| reject | <maintainer's reasoning> | yes \| no |
```

  Quote the agent rationale verbatim (truncated per FR-013 if >100 lines). The "Match" column drives whether T039 (iterate) is required: any `no` → spawn sibling per T039.
- [ ] T039 [US3] If `match: no` for any project, iterate idea_selector: (a) spawn sibling at default start-stage `brainstormed` — `python tests/phase1/sibling_project.py <PROJ-id-final-k> --iter <N>`. The sibling will have only the brainstorm seed; this is intentional so the iteration trail is a fully fresh replay (per spec US3 / U2/I1 fix). (b) Patch `agents/prompts/idea_selector.md` to address the rationale defect (boilerplate, mismatch, missing engagement with hypothesis); bump `prompt_version` per A3 policy in spec Clarifications. (c) Commit the prompt patch. (d) Drive the sibling through the orchestrator with **two** sequential `python -m llmxive run --project <SIBLING> --max-tasks 1` invocations: the first runs flesh_out (re-using the unchanged flesh_out prompt), the second runs idea_selector (under the patched prompt). (e) Re-evaluate the new sibling's verdict using the T038 format. Cap at **5 iterations per project per FR-005**.
- [ ] T040 [US3] Per-project iteration diff: quote `git diff <iter1-commit>:agents/prompts/idea_selector.md <iterN-commit>:agents/prompts/idea_selector.md` verbatim in report Section 5 per FR-008.
- [ ] T041 [US3] Per-project acceptance-criteria evaluation against issue #61: state advances correctly; rationale is specific (not boilerplate); engages with hypothesis + evaluation plan; correctly handles `scope_rejected.yaml` if present. Record in report Section 3 per FR-009.
- [ ] T042 [US3] Final carry-forward decision per project: only projects where (a) all citations verified, (b) idea_selector verdict is `project_initialized`, (c) maintainer endorses the rationale qualify for `carry-forward.yaml`. Aim for 2-3 final qualifying projects. **SC-008 record (C4)**: also record per-project the final idea_selector iteration count (`idea_selector_iterations: <int>`, 1 ≤ N ≤ 5 per FR-005); together with T024 and T034's records, these three counts populate the `agents_run` list in `carry-forward.yaml` (T049). If any agent's count exceeds 5, the project MUST NOT be carried forward — file a deferral issue per FR-013(b) instead.

**Independent verification (US3)**: read `notes/2026-05-04-phase1-diagnostic.md` Section 3 (Idea_selector) and confirm: every project has its agent vs maintainer verdict comparison quoted; every iteration diff is quoted; 2-3 projects pass the maintainer-endorsement gate.

---

## Phase 6: User Story 4 — Verbatim artifact capture and critical evaluation report (P1)

**Goal**: Ensure the diagnostic report is structurally complete per `contracts/diagnostic-report.md`. Most content was added incrementally during US1-US3 tasks; this phase is the final pass to fill in summary/cross-reference sections.

**Independent test**: Read the report top-to-bottom; confirm every contract-required section is filled in.

- [ ] T043 [US4] Section 2 (Executive summary): write ≤1-page summary with three subsections (What worked well / What needs improvement / What's broken). Each bullet cites a specific Section 3+ subsection by anchor link. End with the carry-forward verdict ("N projects carried forward — see Section 8 / `carry-forward.yaml`").
- [ ] T044 [US4] Section 6 (Defects categorized): consolidate every defect identified during US1-US3 into the single defects table per the contract — columns: ID, Severity, Category, Description, File:line, Status. Each defect MUST have: (a) severity tag CRITICAL/HIGH/MEDIUM/LOW, (b) file+line where the fix should land, (c) status of `resolved (commit <sha>)` or `deferred (issue #NNN)` or `accepted (not addressed)` per FR-011 / FR-013. **SC-007 verification (C3)**: after the table is built, scan every row whose Severity is CRITICAL or HIGH and confirm its Status field is non-empty and one of the three allowed values — never blank, never "TODO", never "see Section X". If any CRITICAL/HIGH row has an unresolved Status, the spec considers a defect silently dropped → block the report-finalize commit until that defect is either fixed-with-commit, deferred-with-issue, or explicitly accepted with rationale.
- [ ] T045 [US4] Section 7 (After-fix re-runs): for every defect with `Status: resolved (commit <sha>)`, ensure an "After fix" subsection quotes the corresponding sibling-iteration artifact + run-log + acceptance-criteria evaluation showing the defect is gone per FR-013(a). Cross-link from each Section 6 row.
- [ ] T046 [US4] Truncation pass per FR-013: any quoted file >100 lines must use the `[truncated lines N-M, sha256: <hash>]` marker convention. Run `find projects/ -name '*.md' -exec wc -l {} \; | awk '$1 > 100'` and verify any oversize files are truncated in the report.
- [ ] T047 [US4] Cross-reference pass: ensure every report section that names an artifact links to the file path (markdown-link style) so reviewers can browse the source. Confirm every spec acceptance-criteria checkbox from #59/#60/#61 has at least one explicit pass/fail mark in Section 3 per FR-009.
- [ ] T048 [US4] Final commit-time stamp: update report Section 1 with the final-commit-at-report-time short SHA (will be the next commit in T053). Will be stamped right before the report-finalize commit.

**Independent verification (US4)**: open `notes/2026-05-04-phase1-diagnostic.md` and confirm Sections 1-7 all populated per the contract; defects table has at least one row per identified defect; every CRITICAL/HIGH defect has either an After-fix subsection or a follow-up issue link.

---

## Phase 7: User Story 5 — Carrying-forward gate (P2)

**Goal**: Write `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` with the 2-3 qualifying projects from US3.

**Independent test**: Run the validator from T008; confirm all named projects exist + are at `project_initialized` + have valid idea files with citations.

- [ ] T049 [US5] Write `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` per the schema in `contracts/carry-forward.md`. Required fields per project: `project_id`, `final_state: project_initialized`, `final_commit`, `agents_run` (list of 3: brainstorm/flesh_out/idea_selector with `iterations` + `final_iter_id`), `justification` (≥120 chars, references at least one specific feature of `idea/<slug>.md`).
- [ ] T050 [US5] Run validator: `python tests/phase1/validate_carry_forward.py` — confirm exit 0 (informative; non-zero only on parse errors). Quote the validator's per-project pass/fail output verbatim into report Section 8 (Carry-forward summary).
- [ ] T051 [US5] Add report Section 8: quote the full `carry-forward.yaml` content verbatim, then add a one-paragraph commentary per project explaining selection (can re-use the YAML's `justification` field expanded).

**Independent verification (US5)**: `cat specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` shows 2-3 entries; `python tests/phase1/validate_carry_forward.py` exits 0; report Section 8 quotes the YAML verbatim.

---

## Phase 8: Polish & Cross-cutting

- [ ] T052 Spec hygiene: run a final pass through `specs/003-phase1-idea-lifecycle-testing/spec.md` and confirm the Clarifications section's filename-convention note (the `idea/<slug>.md` canonicalization) is referenced wherever else a bare `seed.md` or `idea.md` appears, so no future reader is confused.
- [ ] T052a FR-016 verification (C1): run `git status --short` from repo root and confirm output is empty (no uncommitted real-project artifacts) before T053. If non-empty, identify which `projects/` / `state/projects/` / `state/run-log/` files were missed in the per-step commits (T015/T020/T026/T032/T037) and commit them with a message like `phase1: catch-up commit for FR-016 (#45)`. This is the explicit "all artifacts committed" gate per FR-016.
- [ ] T052b FR-018 commit-message audit (C2): for every prompt-patch commit on this branch (those touching `agents/prompts/*.md` or `agents/registry.yaml`), run `git log --grep "agents/prompts" --oneline 003-phase1-idea-lifecycle-testing ^main` and confirm each commit message references (a) parent issue `#45`, (b) the relevant sub-issue (`#59`/`#60`/`#61`), AND (c) the diagnostic-report Section that motivated the patch (e.g., `(Section 3 Cohort 1)`). If any commit is missing the Section reference, amend it with `git commit --amend -m "..."` (only safe if not yet pushed; if already pushed, add a `git notes` annotation referencing the Section instead — never force-push to a shared branch).
- [ ] T053 Final report stamp: update report Section 1 final-commit-at-report-time field with the upcoming commit's SHA (compute via `git log --oneline -1` after the report-finalize commit; OR use a placeholder and amend).
- [ ] T054 Commit final report + carry-forward: `git add notes/2026-05-04-phase1-diagnostic.md specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: finalize diagnostic report + carry-forward manifest (#45 #107)"`.
- [ ] T055 Push branch + open PR: `git push -u origin 003-phase1-idea-lifecycle-testing` then `gh pr create --title "[Phase 1] Idea Lifecycle diagnostic + 2-3 carry-forward projects" --body "$(cat <<'EOF'`...`EOF` ... `)" --repo ContextLab/llmXive`. PR body must reference issues #45, #59, #60, #61, #107.
- [ ] T056 Update issue #107 with link to the PR + a one-paragraph status update naming the carry-forward projects + listing any deferred defects (with their follow-up issue numbers).
- [ ] T057 For each deferred CRITICAL/HIGH defect from Section 6, create a follow-up issue: `gh issue create --repo ContextLab/llmXive --title "[Phase 1 follow-up] <defect description>" --body "<rationale + report section reference>" --label pipeline-followup`.

---

## Dependencies

- **Phase 1 (Setup)** has no dependencies; can start immediately.
- **Phase 2 (Foundational)** depends on Phase 1 (T001-T004 done). T005-T008 are parallelizable [P]; T009-T012 are sequential within Phase 2.
- **Phase 3 (US1 — Brainstorm)** depends on Phase 2 complete (resolver self-test + sibling-spawner ready).
- **Phase 4 (US2 — Flesh_out)** depends on Phase 3 complete (selected candidates exist).
- **Phase 5 (US3 — Idea_selector)** depends on Phase 4 complete (citation-verified projects exist).
- **Phase 6 (US4 — Report)** depends on Phases 3-5 (all artifacts to quote exist); however, content is **added incrementally** during US1-US3 tasks, so US4 phase tasks (T043-T048) are mostly summary/cross-reference work.
- **Phase 7 (US5 — Carry-forward)** depends on Phase 5 (US3 final qualifications) and Phase 6 (report Section 8 ready to populate).
- **Phase 8 (Polish)** depends on Phases 1-7.

## Parallel-execution opportunities

**Within Phase 2 (Foundational)** — T005, T006, T007, T008 all touch different files and can run in parallel:

```text
- [ ] T005 [P] Implement citation resolver (tests/phase1/citation_resolver.py)
- [ ] T006 [P] Implement citation resolver pytest (tests/phase1/test_citation_resolver.py)
- [ ] T007 [P] Implement sibling project spawner (tests/phase1/sibling_project.py)
- [ ] T008 [P] Implement carry-forward validator (tests/phase1/validate_carry_forward.py)
```

T009 (resolver self-test) depends on T005; T010 (resolver pytest run) depends on T005+T006.

**Within Phase 4 (US2)** — T025-T035 are mostly per-project loops. Each project's flesh_out cycle (T025→T026→T027→T028→T029) is sequential within itself but **independent across projects**. With 2-3 selected projects, the cycles can theoretically run in parallel, but per the spec's sequential constraint (FR-001: "agents run one-at-a-time"), the diagnostic invokes them serially.

**Within Phase 5 (US3)** — same as Phase 4: per-project loops are independent across projects but invoked serially per FR-001.

## Implementation strategy

**MVP scope** (US1 alone): even just running US1 (Phase 3) produces a meaningful artifact — the brainstorm cohort + iteration-diff + induced-failure run is itself a diagnostic of the brainstorm agent. The carry-forward gate (US5) is what makes the spec "complete," but US1's output alone is sufficient for issue #59 closeout and a partial Phase-2-input gate.

**Recommended order**: Phase 1 → Phase 2 (do T005-T008 in parallel) → Phase 3 (sequential, with iteration loops) → Phase 4 (per-project sequential) → Phase 5 (per-project sequential) → Phase 6+7 (mostly bookkeeping) → Phase 8 (commit + push + PR).

**Wall-clock budget reminder** (from quickstart.md): worst-case ~5h 35min backend wall-clock + ~half-day to full-day maintainer wall-clock for review/iteration. Most of the maintainer time is in Phase 3 (cohort review + prompt iteration) and Phase 5 (idea_selector verdict review).
