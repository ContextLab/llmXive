---
description: "Task list for spec 010: personality taste, real speckit artifacts, PDF audit"
---

# Tasks: Personality Taste, Real Speckit Artifacts, PDF Audit

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)
**Prerequisites**: all files present ✓

**Tests**: included throughout (Constitution Principle III requires real-call coverage).

## Path Conventions

Single Python package: `src/llmxive/`. Tests under `tests/unit/` (mock-OK) and `tests/real_call/` (real HTTP / real `pdf2image`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new top-level dependencies, scaffold new module files with docstrings + empty function signatures so subsequent tasks can run in parallel.

- [ ] T001 Add `pdf2image>=1.17` to [pyproject.toml](pyproject.toml) `[project.dependencies]` block and run `pip install -e .` to verify the install resolves
- [ ] T002 [P] Document `poppler` system dependency in [README.md](README.md) (install via `brew install poppler` on macOS or `apt-get install poppler-utils` on Linux) and add a fail-fast check in `src/llmxive/pipeline/pdf_pipeline/audit.py:__main__` that calls `shutil.which("pdftoppm")` and raises with an actionable message if missing
- [ ] T003 [P] Create [src/llmxive/audit/liveness.py](src/llmxive/audit/liveness.py) with module docstring, public function signatures (`check_pointer(kind: str, pointer: str) -> dict`, `_load_cache() / _save_cache()`), and `LIVENESS_CACHE_PATH = Path("state/audit/liveness-cache.json")` constant — empty bodies that `raise NotImplementedError`
- [ ] T004 [P] Create [src/llmxive/audit/speckit_prune.py](src/llmxive/audit/speckit_prune.py) with module docstring and public function signatures (`audit_artifacts(repo_root: Path) -> dict`, `prune_templates(repo_root: Path, dry_run: bool) -> dict`, `_walk_back_to_real_stage(history_path: Path) -> str`) — empty bodies raising `NotImplementedError`
- [ ] T005 [P] Create [src/llmxive/pipeline/pdf_pipeline/audit.py](src/llmxive/pipeline/pdf_pipeline/audit.py) with module docstring and public function signatures (`audit_pdf(pdf_path: Path, out_dir: Path) -> dict`, `audit_directory(papers_dir: Path, out_dir: Path) -> dict`, internal `_check_page(*) -> list[dict]`) — empty bodies raising `NotImplementedError`
- [ ] T006 [P] Create [src/llmxive/pipeline/pdf_pipeline/classify_failure.py](src/llmxive/pipeline/pdf_pipeline/classify_failure.py) with module docstring and public function `classify(failure_kind: str, evidence: str, source_available: bool) -> str` returning one of the four FR-018 classes — empty body raising `NotImplementedError`

**Checkpoint**: All modules exist as scaffolds; `python -c "from llmxive.audit import liveness, speckit_prune; from llmxive.pipeline.pdf_pipeline import audit, classify_failure"` imports without error.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure used by all three user stories.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [ ] T007 Implement [src/llmxive/audit/liveness.py](src/llmxive/audit/liveness.py) `check_pointer(kind, pointer)`:
  - For `kind == "arxiv"`: HEAD `https://arxiv.org/abs/<pointer>` with `allow_redirects=True, timeout=LIVENESS_TIMEOUT_SEC` (env, default 10)
  - For `kind == "doi"`: HEAD `https://doi.org/<pointer>`
  - For `kind == "url"`: HEAD `<pointer>` directly
  - Return `{status: "pass"|"fail", http_code: int, checked_at: ISO8601}`
  - 2xx/3xx after redirect → pass; otherwise fail
  - Persist + read JSON cache at `state/audit/liveness-cache.json` keyed by pointer string; honor 7-day TTL on hit; ensure parent dir is created.
- [ ] T008 [P] Add [tests/unit/test_liveness_check.py](tests/unit/test_liveness_check.py): cache hit within TTL skips HEAD (verified via `requests_mock` patching only the network layer); cache miss issues HEAD; expired cache entries trigger fresh HEAD; cache file is created on first miss; invalid `kind` raises.
- [ ] T009 [P] Add [tests/real_call/test_personality_liveness_real.py](tests/real_call/test_personality_liveness_real.py): real HEAD against `https://arxiv.org/abs/2202.01933` → status pass; real HEAD against `https://arxiv.org/abs/0000.00000` (nonexistent) → status fail. Gated by `os.environ.get("LLMXIVE_NETWORK_TESTS") == "1"` (skip otherwise).
- [ ] T010 Add [src/llmxive/audit/__init__.py](src/llmxive/audit/__init__.py) re-exports `check_pointer`, `audit_artifacts`, `prune_templates` for caller convenience.
- [ ] T011 Add state directories `state/audit/pdf/` and `state/audit/pdf/_quarantine/` to repo with a `.gitkeep` so the directories exist for the audit script to write into on fresh checkouts.

**Checkpoint**: Liveness check works end-to-end against real arXiv with cache persistence; foundation ready.

---

## Phase 3: User Story 1 — Personality contributions are real reviews (P1) 🎯 MVP

**Goal**: Every personality contribution carries a YAML-frontmatter `position`, a liveness-checked `adjacent_work` list, and an `interest_signal` anchor. Rubric rejects contributions missing any of these.

**Independent Test**: After this phase, picking 20 freshly generated contributions and validating their frontmatter via `contracts/personality_contribution.schema.json` should yield 100% schema-valid contributions.

### Tests for User Story 1 (write FIRST, expect FAIL)

- [ ] T012 [P] [US1] Contract test [tests/unit/test_personality_contribution_schema.py](tests/unit/test_personality_contribution_schema.py): validate fixture frontmatter (REAL + TEMPLATE samples) against `specs/010-.../contracts/personality_contribution.schema.json` using `jsonschema.validate`. REAL passes, TEMPLATE fails.
- [ ] T013 [P] [US1] Unit test [tests/unit/test_personality_rubric_axes.py](tests/unit/test_personality_rubric_axes.py): new rubric axes (`position_present`, `adjacent_work_verified`, `interest_signal_anchored`) score correctly on hand-crafted fixtures — pass case (all three present), fail-position, fail-adjacent-work (cite missing), fail-interest-signal (signal not in persona's declared list).
- [ ] T014 [P] [US1] Unit test [tests/unit/test_personality_rotation_diversity.py](tests/unit/test_personality_rotation_diversity.py): given a project with 3 prior `lean_against` contributions, the next prompt-building step prepends the diversity hint (FR-006); given a project with mixed positions, no hint is added.
- [ ] T015 [US1] Integration test [tests/real_call/test_personality_end_to_end.py](tests/real_call/test_personality_end_to_end.py) (NETWORK-gated): run `personality.tick(persona="ada-lovelace", project_id=fixture_project)` on a temp-copied project; assert the on-disk contribution validates against the schema and that `verified_at` is populated on every `adjacent_work` entry. Skip when `LLMXIVE_NETWORK_TESTS != "1"`.

### Implementation for User Story 1

- [ ] T016 [US1] Extend [src/llmxive/audit/personality_rubric.py](src/llmxive/audit/personality_rubric.py) with three new scoring axes: `position_present` (frontmatter has valid `position`), `adjacent_work_verified` (all entries have `verified_at` and at least one entry exists when position != abstain), `interest_signal_anchored` (frontmatter `interest_signal` matches one of the persona's declared `interest_signals`). Update the `passes(scored: dict) -> bool` function to require ALL THREE new axes ≥ 1 PLUS at least 3-of-4 existing axes ≥ 1.
- [ ] T017 [P] [US1] Update [src/llmxive/agents/prompts/personality.md](src/llmxive/agents/prompts/personality.md) (the umbrella prompt) to add a `## Required outputs` section at the top, naming the three required fields (`position`, `adjacent_work`, `interest_signal`) with one-line descriptions and a labeled few-shot example placeholder `{{example_contribution}}` filled per-persona at runtime.
- [ ] T018 [P] [US1] Extend every persona card under [src/llmxive/agents/prompts/personalities/](src/llmxive/agents/prompts/personalities/) (10 files) with an `example_contribution:` frontmatter block (position + adjacent_work + interest_signal + body_excerpt) following the data-model.md persona-card extension. Keep voice and `interest_signals` lists unchanged.
- [ ] T019 [US1] Modify [src/llmxive/agents/personality.py](src/llmxive/agents/personality.py) `dispatch()`/`tick()` to:
  (a) before the LLM call, read the persona card's `example_contribution` and inject into the umbrella prompt's `{{example_contribution}}` slot;
  (b) after the LLM call, parse YAML frontmatter from the contribution body;
  (c) for each `adjacent_work[].pointer`, call `liveness.check_pointer()`; on any fail, treat as rubric failure on the `adjacent_work_verified` axis (do NOT write the contribution to disk);
  (d) on pass, write `verified_at` back into the frontmatter and persist the contribution.
- [ ] T020 [US1] Add diversity-bias state to [state/personality_rotation.yaml](state/personality_rotation.yaml) schema and update `personality.py` to: (a) on persisted contribution, append `position` to `per_project_positions[project_id]`; (b) on next prompt-build for a project where last 3 contributions share a position, prepend a `Prior contributors all leaned <position>; consider whether you genuinely disagree` paragraph to the persona prompt.
- [ ] T021 [US1] Two-strike retry+escalation: when the rubric fails twice in a row on the same persona+project, persist the rejected body to `.audit/rejected-contributions.jsonl` with `failed_axes: [...]` (FR-005); advance the persona rotation pointer; do NOT auto-escalate to `human_input_needed` for the project itself (escalation is reserved for the speckit pipeline per FR-011).
- [ ] T022 [US1] Update [src/llmxive/web_data.py](src/llmxive/web_data.py) to expose each contribution's `position` field in `recent_activity` rows so the activity-page filter (already shipped on main) can offer a `position` filter.

**Checkpoint**: User Story 1 is fully functional. A `personality tick` produces a fully-compliant contribution end-to-end (verified via T015).

---

## Phase 4: User Story 2 — Speckit pipeline produces real artifacts (P1)

**Goal**: Every speckit artifact under `projects/**/specs/**/` and `projects/**/.specify/**/` is classified REAL via `_real_only_guard`. Existing TEMPLATE artifacts are deleted (transitively). Affected projects roll back to their latest surviving real stage. The pipeline scheduler advances up to `PIPELINE_PARALLELISM=8` distinct projects per tick.

**Independent Test**: After this phase, `python -m llmxive speckit audit-artifacts` reports zero TEMPLATE artifacts. Running the scheduler for a single tick advances multiple projects, not just one.

### Tests for User Story 2

- [ ] T023 [P] [US2] Contract test [tests/unit/test_speckit_audit_schema.py](tests/unit/test_speckit_audit_schema.py): validate fixture audit reports against `contracts/speckit_artifact_audit.schema.json`. REAL + TEMPLATE + empty cases.
- [ ] T024 [P] [US2] Unit test [tests/unit/test_speckit_prune.py](tests/unit/test_speckit_prune.py): set up a temp project with a TEMPLATE `spec.md` + a REAL `plan.md` and a TEMPLATE `tasks.md` AND an `analysis.md` (downstream of tasks.md). After `prune_templates(apply=True)`: spec.md + tasks.md deleted; analysis.md ALSO deleted transitively (FR-008 transitive deletion); plan.md retained; project state rolled back to the stage prior to `specified` (matching the latest surviving real artifact); `history.jsonl` contains a `template_artifact_purge` event listing every deleted path. Also test the recursive-rollback case: TEMPLATE plan.md too → roll all the way back to `flesh_out_complete`.
- [ ] T025 [P] [US2] Unit test [tests/unit/test_scheduler_parallelism.py](tests/unit/test_scheduler_parallelism.py): mock-OK test of `scheduler.tick(max_projects=8)` against a fixture of 20 projects at `flesh_out_complete`; verify exactly 8 distinct project IDs advance, no project file written to twice, and projects locked by another tick are skipped.
- [ ] T026 [P] [US2] Unit test [tests/unit/test_template_refused_escalation.py](tests/unit/test_template_refused_escalation.py): when a stage agent raises `TemplateRefused` twice in a row for the same project on the same stage, the project transitions to `human_input_needed` with `human_escalation_reason` containing the missing-context message from the guard (FR-011).
- [ ] T027 [US2] Integration test [tests/phase2/test_speckit_pipeline_real_artifacts.py](tests/phase2/test_speckit_pipeline_real_artifacts.py): run the speckit stage agent against a fixture project at `flesh_out_complete` with the real-call backend (Dartmouth API per project policy); assert the produced `spec.md` is REAL via `_real_only_guard.is_real()`. Skipped if no LLM key configured.

### Implementation for User Story 2

- [ ] T028 [US2] Implement [src/llmxive/audit/speckit_prune.py](src/llmxive/audit/speckit_prune.py) `audit_artifacts()`:
  - Glob `projects/**/specs/**/*.md` and `projects/**/.specify/**/*.md`
  - For each path: extract project_id from path; determine stage from path (e.g., `spec.md` → `specified`); call `_real_only_guard.is_real()`; on TEMPLATE, walk the project's expected stage outputs forward to compute `transitive_dependents` (plan.md/tasks.md/data-model.md/etc. produced AFTER this stage).
  - Return dict matching `contracts/speckit_artifact_audit.schema.json`.
- [ ] T029 [US2] Implement [src/llmxive/audit/speckit_prune.py](src/llmxive/audit/speckit_prune.py) `prune_templates(apply: bool)`:
  - Call `audit_artifacts()` first
  - In dry-run (`apply=False`): return the audit report with `would_delete` paths added; no filesystem changes
  - In apply mode: for each TEMPLATE, delete the artifact + its `transitive_dependents`; call `_walk_back_to_real_stage()` to find the new stage; update `state/projects/<id>.yaml` `current_stage`; append a `template_artifact_purge` event to `state/projects/<id>.history.jsonl`; log the operation to `state/run-log/<YYYY-MM>/<run-id>.jsonl` (FR-023).
- [ ] T030 [US2] Implement `_walk_back_to_real_stage(history_path: Path) -> str` per research.md R2: walk the JSONL backwards; for each historical stage, check whether its expected artifacts still exist on disk AND classify REAL; return the most recent surviving stage or `flesh_out_complete` if none.
- [ ] T031 [US2] Add CLI subcommand `python -m llmxive speckit audit-artifacts [--out PATH] [--dry-run]` and `python -m llmxive speckit prune-templates [--apply]` by extending [src/llmxive/cli.py](src/llmxive/cli.py) (or its speckit subcommand module). `--dry-run` is default for `audit-artifacts`; `--apply` is required for `prune-templates` to mutate.
- [ ] T032 [US2] Audit + prune the current repo: run `python -m llmxive speckit audit-artifacts --out /tmp/audit.json` then `python -m llmxive speckit prune-templates --apply`. Commit the resulting deletions and state-yaml rollbacks. Verify zero TEMPLATE remain via a second audit run (idempotence; FR-022).
- [ ] T033 [US2] Modify [src/llmxive/pipeline/scheduler.py](src/llmxive/pipeline/scheduler.py) to:
  - Read `PIPELINE_PARALLELISM` env var (default 8), validate `1 <= N <= 64`, raise on out-of-range
  - In each tick, select up to N distinct project IDs from the priority queue, advance each serially (the existing per-project lock at `pipeline/lock.py` already prevents same-project double-writes)
  - Add structured log entries per advance to `state/run-log/<YYYY-MM>/<id>.jsonl` so each appears on the activity page (already on main).
- [ ] T034 [US2] Implement FR-011 two-strike escalation in [src/llmxive/pipeline/graph.py](src/llmxive/pipeline/graph.py):
  - Track consecutive `TemplateRefused` failures per (project, stage) in `state/projects/<id>.yaml` `last_template_refused_stage` + `template_refused_count`
  - On 2nd consecutive failure: transition to `HUMAN_INPUT_NEEDED` with `human_escalation_reason` containing the guard's `missing_context` string; reset the counter
- [ ] T035 [US2] Update [src/llmxive/web_data.py](src/llmxive/web_data.py) `_recent_activity` to emit `template_artifact_purge` events (from history.jsonl) and `template_refused_escalation` events (from graph transitions) as activity rows so deletions/escalations appear on the public activity feed (FR-023).
- [ ] T035a [US2] **FR-010 coverage audit**: grep all `Path.write_text` and `.open("w")` calls under `src/llmxive/speckit/` and `src/llmxive/agents/{idea_lifecycle,paper_writing,advancement,runner}.py` (and any other agent that writes stage artifacts as `.md`). For each call site that writes a speckit `.md` artifact, verify it is preceded by an `_real_only_guard.assert_real_or_raise()` call against the same path. For any call site missing the guard, add the call AND add a regression unit test (one per call site) under `tests/unit/test_speckit_guard_coverage.py` that asserts `assert_real_or_raise` is called before the write.

**Checkpoint**: User Story 2 fully functional. Zero TEMPLATE artifacts in the repo; scheduler advances ≥8 projects/tick; every stage-artifact writer is guarded.

---

## Phase 5: User Story 3 — Every existing PDF passes a deterministic audit (P2)

**Goal**: `llmxive pdf-pipeline audit docs/papers/` exits zero across the current PDF pool. Failures are classified, source-fixable cases are fixed by extending the normalizers, unsupported-construct cases get restyle wrappers, source-missing cases are quarantined. Zero LLM calls anywhere in the pipeline.

**Independent Test**: After this phase, `python -m llmxive pdf-pipeline audit docs/papers/ --out-dir state/audit/pdf/` exits 0 and produces per-PDF JSON reports with `summary.total_failures == 0`.

### Tests for User Story 3

- [ ] T036 [P] [US3] Contract test [tests/unit/test_pdf_audit_report_schema.py](tests/unit/test_pdf_audit_report_schema.py): validate fixture reports against `contracts/pdf_audit_report.schema.json`. Pass case (zero failures), fail case (one of each failure kind).
- [ ] T037 [P] [US3] Unit test [tests/unit/test_pdf_audit_text_checks.py](tests/unit/test_pdf_audit_text_checks.py): for each text-level check (literal command, non-square-bracket cite, section-number gap), provide a fixture page-text string and assert the checker returns the expected failure or pass.
- [ ] T038 [P] [US3] Unit test [tests/unit/test_pdf_audit_figure_width.py](tests/unit/test_pdf_audit_figure_width.py): synthetic single-page PDFs with figure widths at the three canonical values pass; off-spec widths fail.
- [ ] T039 [P] [US3] Unit test [tests/unit/test_pdf_audit_classify_failure.py](tests/unit/test_pdf_audit_classify_failure.py): `classify(kind, evidence, source_available)` returns the expected class for each (kind, source_available) combination.
- [ ] T040 [P] [US3] Unit test [tests/unit/test_pdf_audit_quarantine.py](tests/unit/test_pdf_audit_quarantine.py): when `_check_page` raises an unexpected exception for a single PDF, the audit moves the PDF to `state/audit/pdf/_quarantine/<date>/` (preserving subpath), records an `audit_tool_crash` entry with a stack-trace excerpt, and continues to the next PDF; the run exits non-zero IFF any fail entry remained.
- [ ] T041 [P] [US3] Static-AST test [tests/unit/test_pdf_pipeline_no_llm.py](tests/unit/test_pdf_pipeline_no_llm.py) (already exists per spec 009): re-run after adding `audit.py` and `classify_failure.py` to confirm the AST scan still passes (no LLM imports). EXTEND the test if needed to cover the new files explicitly.
- [ ] T042 [US3] Real-call test [tests/real_call/test_pdf_audit_real.py](tests/real_call/test_pdf_audit_real.py): pick 3 representative PDFs from `docs/papers/`, run `audit_pdf()` against each, assert a valid report is produced. NOT gated by network (uses local PDFs); gated by `pdftoppm` availability.

### Implementation for User Story 3

- [ ] T042a [US3] Add `PAPER_REVIEW_QUARANTINED = "paper_review_quarantined"` to the `Stage` enum in [src/llmxive/pipeline/graph.py](src/llmxive/pipeline/graph.py) (and any mirrors under `src/llmxive/state/` / `pyproject.toml`-installed pydantic validators). Update the project-state Pydantic model to allow this stage. Update [STAGE_TO_AGENT](src/llmxive/pipeline/graph.py) to map it to `None` (no agent runs against quarantined projects). Add a regression unit test [tests/unit/test_stage_enum_paper_review_quarantined.py](tests/unit/test_stage_enum_paper_review_quarantined.py) that asserts a project yaml with `current_stage: paper_review_quarantined` parses cleanly and the scheduler skips it.
- [ ] T043 [US3] Implement [src/llmxive/pipeline/pdf_pipeline/classify_failure.py](src/llmxive/pipeline/pdf_pipeline/classify_failure.py) `classify(kind, evidence, source_available)`:
  - `kind == "audit_tool_crash"` → always `audit_tool_crash`
  - `kind == "literal_command_text"` and `source_available` → `source_fixable` (normalizer extension); else `unsupported_construct`
  - `kind == "non_square_bracket_cite"` → `source_fixable` (normalize_references)
  - `kind == "non_canonical_authorblock"` → `source_fixable` (normalize_authors)
  - `kind == "off_spec_figure_width"` → `source_fixable` (normalize_figures)
  - `kind == "section_number_gap"` → `unsupported_construct` (publisher class override)
  - `not source_available` → `source_missing` (regardless of kind)
- [ ] T044 [US3] Implement [src/llmxive/pipeline/pdf_pipeline/audit.py](src/llmxive/pipeline/pdf_pipeline/audit.py) `audit_pdf(pdf_path, out_dir)`:
  - Extract text with `pdfminer.six.extract_text` page-by-page
  - For each page, run text-level checks: literal LaTeX commands (`re.search(r'\\\w+\{', text)`), non-numeric-square-bracket cites (regex pattern matching `[1]` PASS vs. `(Smith, 2024)` FAIL vs. `²` FAIL), section-number gap detection (extract heading numbers, check monotonic)
  - For figure-bearing pages (caption regex `Figure \d+`), rasterize via `pdf2image.convert_from_path(pdf, first_page=N, last_page=N)`; measure figure bounding box widths; compare against the three canonical widths
  - Catch any exception per-page; on crash, quarantine the entire PDF + record `audit_tool_crash`
  - Write the JSON report matching `pdf_audit_report.schema.json` to `out_dir/<paper-id>.json`
- [ ] T045 [US3] Implement [src/llmxive/pipeline/pdf_pipeline/audit.py](src/llmxive/pipeline/pdf_pipeline/audit.py) `audit_directory(papers_dir, out_dir)`:
  - Glob `<papers_dir>/PROJ-*/*.pdf` (or single PDF if `papers_dir` is a file)
  - Call `audit_pdf` for each; aggregate per-class totals
  - Print a summary table to stdout
  - Exit non-zero IFF any report contains a fail entry (FR-014/Q3)
- [ ] T046 [US3] Wire the audit into the CLI [src/llmxive/pipeline/pdf_pipeline/cli.py](src/llmxive/pipeline/pdf_pipeline/cli.py): add a `audit` subcommand (`llmxive pdf-pipeline audit <path> [--out-dir DIR]`) that calls `audit_directory()`.
- [ ] T047 [US3] Run the audit against `docs/papers/` and triage every failure:
  - For each `source_fixable` failure: identify the offending source file under `papers/PROJ-*/main.tex`; verify the existing normalizer covers the case; if not, extend the relevant `normalize_*.py` module; re-compile via the existing pipeline; re-run audit on the affected PDF.
  - For each `unsupported_construct` failure: add a restyle wrapper to `src/llmxive/pipeline/pdf_pipeline/restyle.py` that either rewrites the construct to an `llmxive.cls`-supported equivalent or drops it deterministically; document the new wrapper in `restyle.report.json`.
  - For each `source_missing` failure: check `state/projects/<id>.yaml` for an `arxiv_id`; if present, re-fetch via the existing `pdf_pipeline ingest` path; if absent or fetch fails, move the PDF to `state/audit/pdf/_quarantine/` and mark the project's `current_stage` as `paper_review_quarantined`.
  - Re-run audit until zero fail entries remain.
- [ ] T048 [US3] Add CI workflow `.github/workflows/audit-pdf.yml` (if not already present) that runs `pip install -e . && apt-get install poppler-utils && python -m llmxive pdf-pipeline audit docs/papers/` on every PR. Step also runs `pytest tests/unit/test_pdf_pipeline_no_llm.py -v` to confirm the AST guard still passes (FR-013/SC-007). Use `env: {}` to clear any LLM API keys for the run (FR-020).

**Checkpoint**: User Story 3 fully functional. `python -m llmxive pdf-pipeline audit docs/papers/` exits 0; CI workflow gates PRs.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T049 [P] Update [README.md](README.md) with a "PDF audit" section describing the new audit command, expected output format, and the failure classification scheme.
- [ ] T050 [P] Update [README.md](README.md) "Personality contributions" section with the new `position` / `adjacent_work` / `interest_signal` frontmatter contract.
- [ ] T051 [P] Update [docs/architecture.md](docs/architecture.md) (or equivalent) — if it doesn't exist, create it — documenting the speckit prune flow and the scheduler `PIPELINE_PARALLELISM` knob.
- [ ] T052 Update [requirements.txt](requirements.txt) (or `pyproject.toml`) to reflect `pdf2image>=1.17` per T001; commit the lockfile if any.
- [ ] T053 Run the full verification suite from the repo root: `pytest tests/unit/ tests/phase2/ -x -q`, then `LLMXIVE_NETWORK_TESTS=1 pytest tests/real_call/ -x -q --tb=short`. Any failures MUST be fixed by changing CODE not by simplifying tests (Constitution Principle III).
- [ ] T053a Early network-reachability fail-fast (Constitution V): in `personality.tick()`, before invoking the LLM, issue a single HEAD against `https://arxiv.org/` with a 5s timeout; on failure, raise a structured `NetworkUnreachable` error naming the cron tick ID so the run-log surfaces it. Skip in test environments via `LLMXIVE_OFFLINE=1`.
- [ ] T053b SC-002 manual-validation harness: after Phase 3 lands, run the personality cron for two full ticks against real projects. Sample the 20 most-recently-written personality contributions. For each, score binary "contains specific, evidence-grounded judgement I can act on" (no rubric peek). Record results to `state/audit/sc002-blind-review-<YYYY-MM-DD>.json`. Pass criterion: ≥18/20 score TRUE. If <18/20, file follow-up issues citing the prompt phrasing that produced the failures (the prompt is the lever; the tests are not).
- [ ] T054 Run `python -m llmxive web_data` to regenerate `web/data/projects.json` so the new `position` filter on the activity page picks up the new contribution data.
- [ ] T055 Run the three quickstart scenarios end-to-end (see `quickstart.md`); each MUST exit successfully. Document any deviations in `state/audit/quickstart-validation.json`.
- [ ] T056 Final idempotence check (FR-022): re-run `python -m llmxive speckit prune-templates --apply` and `python -m llmxive pdf-pipeline audit docs/papers/`; both MUST produce zero file diffs and zero non-zero exits.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No deps — T001 sequential (pip install); T002-T006 parallel
- **Foundational (Phase 2)**: depends on Phase 1; T007 sequential; T008-T011 can run alongside as tests
- **User Story 1 (Phase 3)**: depends on Phase 2 (needs `liveness.check_pointer`); tests T012-T015 first, then implementation T016-T022
- **User Story 2 (Phase 4)**: depends on Phase 2 (uses `_real_only_guard` and run-log); tests T023-T027 first, then implementation T028-T035
- **User Story 3 (Phase 5)**: depends on Phase 2 (state/audit/ dirs created in T011); tests T036-T042 first, then implementation T043-T048
- **Polish (Phase 6)**: depends on all user stories complete

### Within Each User Story

- Tests first; expect FAIL before implementation lands
- Implementation order: model/state → core function → CLI/wiring → end-to-end run
- Commit after each task or logical group

### Parallel Opportunities

- All [P] tasks in Phase 1 (T002-T006) — different files
- All [P] tests in each user-story phase — independent test files
- Phase 3, 4, and 5 *implementations* can run in parallel once Phase 2 lands (different modules — `audit/speckit_prune.py`, `audit/personality_rubric.py`, `pipeline/pdf_pipeline/audit.py`)

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 + Phase 2 (~11 tasks)
2. Phase 3 (T012–T022, ~11 tasks)
3. **VALIDATE**: T015 produces a compliant contribution on a fixture project via real network call
4. Ship MVP — already addresses the user's most-visible complaint

### Incremental

- After MVP: Phase 4 (speckit prune + scheduler parallelism) → measurable jump in queue throughput
- Then: Phase 5 (PDF audit) → public artifact quality bar lifted
- Polish last

### Parallel Team Strategy (if multiple devs)

- Dev A: Phase 3 (personalities)
- Dev B: Phase 4 (speckit)
- Dev C: Phase 5 (PDF audit)

Each story is independently testable; no cross-story coupling.

---

## Notes

- [P] = different files / no dependencies
- [US1/US2/US3] = traces to user stories from spec.md
- Real-call tests are gated by env vars; unit tests run on every CI invocation
- The activity-page UI (PR #147, already merged) already exposes `project_stage` — T022/T035 add `position` and `template_artifact_purge` rows to keep parity with new pipeline events
- Constitution: NO test simplification on failure; fix the CODE to make the original tests pass
