---
description: "Task list for feature 009 — Quality Fixes (personality curation, speckit real-output enforcement, PDF pipeline hardening, feedback-loop activity feed)"
---

# Tasks: Quality Fixes — Personality Curation, Speckit Real-Output Enforcement, PDF Pipeline Hardening, Feedback-Loop Activity Feed

**Input**: Design documents from `/specs/009-quality-fixes-pass/`
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Tests are REQUIRED for this feature. Constitution Principle III (Real-World Testing) mandates real-call tests for all core functions; mock-only verification is prohibited. Every task that adds production code MUST be paired with a test task in the same user-story phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1 = personality curation, US2 = speckit real-output enforcement, US3 = PDF pipeline hardening, US4 = feedback-loop activity feed)
- All paths shown are repository-relative

## Path Conventions

- Single project layout: `src/llmxive/`, `tests/`, `papers/`, `agents/`, `projects/` at repository root (per [plan.md §Project Structure](plan.md))

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory skeletons and the shared auditor scaffold (Principle I — Single Source of Truth).

- [X] T001 Create `src/llmxive/audit/` package skeleton with `__init__.py` exporting the four auditor entry points and one shared `run_audit(name, …)` dispatcher per [plan.md §Project Structure](plan.md)
- [X] T002 Create `src/llmxive/feed/` package skeleton with `__init__.py` exporting `FeedStore` and `ManifestValidator` per [plan.md §Project Structure](plan.md)
- [X] T003 Create `src/llmxive/pipeline/pdf_pipeline/` package skeleton with `__init__.py` (no LLM imports anywhere in this subtree — enforce via a module-level import guard that raises on `anthropic`/`openai`/`google.generativeai`/`llmxive.backends`) per [plan.md §Project Structure](plan.md)
- [X] T004 [P] Add new open-source dependencies (`pdfplumber`, `markdown-it-py`, `python-ulid`) to `requirements.txt` (Constitution Principle IV — verify all are permissively licensed)
- [X] T005 [P] Create `tests/fixtures/audit/` subtree with `speckit_template/`, `speckit_real/`, `pdf_clean/`, `pdf_defective/` placeholders per [plan.md §Project Structure](plan.md)
- [X] T006 [P] Create `tests/fixtures/feedback/seeded_project/` and `tests/fixtures/feedback/expected_manifests/` placeholders per [plan.md §Project Structure](plan.md)
- [X] T007 [P] Add `.github/workflows/audit.yml` skeleton that runs all four auditors on every push (FR-023, SC-009) — initial step is a no-op `echo`; real wiring lands in each user story's polish task

**Checkpoint**: Package skeletons exist; CI workflow file is present but inert.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared auditor scaffold, the activity feed store, and the manifest validator — every user story depends on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T008 Implement shared `src/llmxive/audit/manifest.py` (Audit Manifest writer + JSON Schema validator against `contracts/audit-manifest.schema.json`); manifest path convention `.audit/<auditor>/<ISO8601>.json` per [data-model.md §Audit Manifest](data-model.md)
- [X] T009 [P] Implement `src/llmxive/audit/cli.py` argparse skeleton with `personality`, `speckit`, `pdf`, `feedback_loop` subcommands; each subcommand currently dispatches to a stub that writes an empty manifest (real logic lands in story phases). **Fail-fast preconditions per Constitution Principle V**: verify the relevant input directory exists and is readable BEFORE any scan begins; for the `pdf` subcommand verify `lualatex`, `pdftotext`, and the `pdfplumber` python package are present on PATH / installed; for the `personality` subcommand verify `agents/prompts/personalities/` exists and is non-empty; raise a clear actionable error and exit non-zero otherwise.
- [X] T010 [P] Implement `src/llmxive/feed/store.py` — `FeedStore` class with `append(item)`, `read(project_id, snapshot_at=None)`, `pack_for_dispatch(project_id, budget_chars, snapshot_at)` (truncate-from-oldest with `[truncated N earlier items]` marker per FR-031); validates each appended item against `contracts/activity-feed-item.schema.json` per [data-model.md §Activity Feed Item](data-model.md)
- [X] T011 [P] Implement `src/llmxive/feed/manifest.py` — `ManifestValidator` that parses the trailing ```json comments-considered``` block from an agent's output, validates against `contracts/comments-considered-manifest.schema.json`, and resolves every `feed_item_id` against the project's feed at `feed_snapshot_at` per [research.md §7](research.md)
- [X] T012 [P] Add `tests/unit/test_feed_store.py` — exercises append, read, snapshot, pack-with-truncation, schema-validation-rejects-bad-input (Constitution III: real filesystem, no mocks)
- [X] T013 [P] Add `tests/unit/test_comments_considered_manifest.py` — positive (valid manifest accepted) + negative (bogus feed_item_id rejected, missing truncation_acknowledged rejected when marker was present) per FR-028
- [X] T014 Add module-level import-guard test `tests/unit/test_pdf_pipeline_no_llm.py` — uses `importlib` + `ast` to verify that no module under `src/llmxive/pipeline/pdf_pipeline/` imports any LLM client (FR-019, SC-007); test FAILS LOUDLY if any LLM import is added later
- [X] T015 Add `tests/unit/test_audit_manifest_schema.py` — round-trip a manifest through writer + JSON Schema validator; verify rejected on missing required fields

**Checkpoint**: Auditor scaffold, feed store, and manifest validator exist with passing unit tests. CI's `audit.yml` workflow can now exercise stubs without failing.

---

## Phase 3: User Story 1 — Personalities express critical taste, not just stylistic commentary (Priority: P1) 🎯 MVP

**Goal**: Personality contributions show real curation/taste (objections, questions, adjacent-work pointers, specific praise) instead of stylistic commentary; manufactured-praise is rare; rubric-rejected contributions after one retry convert to `abstain` with rotation advancing (Clarification Q3).

**Independent Test**: Run 30 fresh personality ticks (full rotation × 3 cycles) against the current backlog and confirm rubric scores improve from baseline; ≥80% of non-abstain contributions "show critical judgement" and ≥60% "name adjacent work" (SC-001). Manufactured-praise rate <10%.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation per Constitution Principle III (real-call testing).

- [X] T016 [P] [US1] `tests/unit/test_audit_personality_rubric.py` — verifies the rubric scores each of the four axes (Voice / Critical Judgement / Curatorial Pointer / Honesty) per [research.md §4](research.md) using positive fixtures (real contributions with all four markers) and negative fixtures (one marker each missing, plus a manufactured-praise example)
- [X] T017 [P] [US1] `tests/unit/test_persona_card_frontmatter.py` — validates every persona card under `agents/prompts/personalities/*.md` against `contracts/persona-card-frontmatter.schema.yaml` (≥3 interest signals, each with ≥1 evidence source — FR-003 + Constitution II)
- [X] T018 [P] [US1] `tests/integration/test_personality_rubric_retry_then_abstain.py` — seeds a persona that produces deliberately rubric-failing output twice; asserts (a) one retry happened, (b) `abstain` recorded with `reason: rubric_failure_after_retry`, (c) rejected contribution body persisted to `projects/<id>/.audit/rejected-contributions.jsonl`, (d) rotation pointer advanced (Q3 + FR-004)
- [X] T019 [US1] `tests/real_call/test_personality_rotation_with_feed.py` — runs a real rotation through `runner.py` against the actual backlog with the new umbrella prompt; asserts ≥80% critical-judgement rate over a sampled cycle (SC-001) using a deterministic rubric scorer, not an LLM judge

### Implementation for User Story 1

- [X] T020 [P] [US1] Implement `src/llmxive/audit/personality_rubric.py` — deterministic scorer per [research.md §4](research.md); exposes `score(contribution) -> RubricScores` and `is_manufactured(contribution) -> (bool, missing_axes[])` per FR-005
- [X] T021 [P] [US1] Rewrite `agents/prompts/personality.md` — add explicit taste/curation pass instruction (FR-001), forbid manufactured enthusiasm (FR-002), require one `curatorial_pointer` field on `comment`/`contribute` actions, instruct agent to lean on persona-card `interest_signals` (FR-003), instruct agent to reference prior feed items by ID (FR-029); preserve spec-008 rotation/"(simulated)"/dartmouth-backend invariants verbatim
- [X] T022 [P] [US1] Add YAML frontmatter with ≥3 `interest_signals` to each persona card under `agents/prompts/personalities/*.md`. Ten cards total: `ada-lovelace.md`, `aristotle.md`, `dan-rockmore.md`, `daniel-kahneman.md`, `david-krakauer.md`, `geoffrey-west.md`, `john-von-neumann.md`, `marie-curie.md`, `rosalind-franklin.md`, `socrates.md`. Each signal MUST cite at least one primary-source URL or work (Constitution II). Tasks are parallel-safe because each card is a distinct file.
- [X] T022a [P] [US1] Implement `scripts/verify_persona_evidence.py` — for every persona card, parse the YAML frontmatter and for each `evidence_sources[]` URL: fetch the URL, confirm HTTP 200, and grep the response body for at least one content noun phrase from the signal's `label`. URLs that fail to resolve OR whose content does not match MUST cause the script to exit non-zero with a clear error naming the persona + signal + URL. Add this script as a CI step under `audit-personality` (T024 wires it). Constitution Principle II: no hallucinated interests.
- [X] T023 [US1] Modify `src/llmxive/agents/personality.py` — after each tick output is generated, call `personality_rubric.score(...)`; on failure retry ONCE; on second failure (a) write contribution body to `projects/<id>/.audit/rejected-contributions.jsonl`, (b) emit an `abstain` action with `reason: rubric_failure_after_retry` + `rubric_scores`, (c) signal runner to advance the rotation pointer (Q3 / FR-004). Infrastructure failures (network, model unavailable, parse error) preserve spec-008 FR-017 hold-on-failure semantics — DO NOT collapse the two paths.
- [X] T024 [US1] Wire `audit personality` CLI subcommand in `src/llmxive/audit/cli.py` to walk `agents/prompts/personalities/`, validate every card, then walk every project's `activity.jsonl` (when present from US4) and score every recent contribution. Outputs `.audit/personality_rubric/<ts>.json`.
- [X] T025 [US1] Add `scripts/audit_personalities.sh` thin wrapper that invokes the CLI (Principle V — fail fast with a clear error if the venv is not active)

**Checkpoint**: Persona cards have interest signals; umbrella prompt enforces critical taste; rubric validator is wired into the tick loop; CI's personality auditor reports against fresh ticks. User Story 1 is independently testable and shippable.

---

## Phase 4: User Story 2 — Speckit pipeline produces real, filled-out artifacts, not template stubs (Priority: P1)

**Goal**: Every `projects/PROJ-*/specs/**/*.md` artifact is classified `real` by the auditor; legacy template-stub artifacts are pruned in one atomic commit; the in-repo speckit pipeline refuses to commit `template` or `partial` artifacts going forward (and refuses to accrue project progression points on non-emission).

**Independent Test**: Run the speckit auditor on `projects/`; confirm 0 `template`-classified artifacts after prune (SC-002). Run the in-repo speckit pipeline against 100 real project contexts; confirm 0 `template` artifacts emitted (SC-003); aborted invocations do not accrue progression points (SC-004).

### Tests for User Story 2

- [X] T026 [P] [US2] `tests/unit/test_audit_template_vs_real.py` — exercises each rule from [research.md §3](research.md) using `tests/fixtures/audit/speckit_template/` (known-template fixtures) and `tests/fixtures/audit/speckit_real/` (known-real fixtures, including the legacy-migration discriminator from [research.md §10](research.md))
- [X] T027 [P] [US2] `tests/unit/test_speckit_emitter_real_only_guard.py` — verifies `src/llmxive/speckit/_real_only_guard.py` rejects writes classified as `template` or `partial` and emits an actionable error naming the missing context (FR-009 + FR-010)
- [X] T028 [P] [US2] `tests/integration/test_speckit_emitter_refuses_template.py` — invokes the real emitter against a project context that lacks enough information to produce a real artifact; asserts (a) no file written, (b) actionable error logged, (c) project progression points NOT incremented (FR-009 + FR-010 + SC-004)
- [X] T029 [P] [US2] `tests/integration/test_audit_speckit_finds_existing_templates.py` — runs the auditor against the current `projects/` tree (real filesystem, real artifacts) and asserts the classification manifest contains at least the known-template stubs we expect (sanity check that the auditor finds them; the prune task removes them)

### Implementation for User Story 2

- [X] T030 [P] [US2] Implement `src/llmxive/audit/template_vs_real.py` per [research.md §3](research.md) — three-rule deterministic classifier; loads template strings from `.specify/templates/*.md` once at startup; emits `{path, classification, rules_fired}` for each artifact; includes the legacy-migration discriminator from [research.md §10](research.md)
- [X] T031 [US2] Wire `audit speckit` CLI subcommand in `src/llmxive/audit/cli.py` to walk `projects/PROJ-*/specs/**/*.md` plus `projects/PROJ-*/specs/**/*.yaml` plus any other speckit emission locations; emit manifest to `.audit/template_vs_real/<ts>.json` and a human-readable markdown sibling
- [X] T032 [US2] Add `--prune --confirm` mode to `audit speckit` — deletes every artifact classified `template`, removes empty parent directories, commits a single atomic git commit with the manifest attached (FR-008)
- [X] T033 [US2] Implement `src/llmxive/speckit/_real_only_guard.py` — `assert_real_or_raise(artifact_path)` that calls `template_vs_real.classify(...)` before any commit and raises `TemplateRefused` with the rule(s) that fired when classification is `template` or `partial` (FR-009)
- [X] T034 [P] [US2] Modify `src/llmxive/speckit/specify_cmd.py` to call `_real_only_guard.assert_real_or_raise(...)` on every artifact before writing; on `TemplateRefused`, log structured failure and DO NOT increment project progression points (FR-009, FR-010, SC-004)
- [X] T035 [P] [US2] Modify `src/llmxive/speckit/plan_cmd.py` identically — same guard, same non-emission semantics (FR-009)
- [X] T036 [P] [US2] Modify `src/llmxive/speckit/tasks_cmd.py` identically (FR-009)
- [X] T037 [P] [US2] Modify `src/llmxive/speckit/clarify_cmd.py` identically (FR-009)
- [X] T038 [P] [US2] Modify `src/llmxive/speckit/implement_cmd.py` identically (FR-009)
- [X] T039 [P] [US2] Modify `src/llmxive/speckit/analyze_cmd.py` identically (FR-009)
- [X] T040 [P] [US2] Modify `src/llmxive/speckit/paper_specify_cmd.py`, `paper_plan_cmd.py`, `paper_tasks_cmd.py`, `paper_clarify_cmd.py`, `paper_implement_cmd.py` — same guard pattern (FR-009 applies to all speckit emitters, not just core commands)
- [X] T041 [US2] Run the prune step on the current repository: `python -m llmxive.audit.cli speckit --prune --confirm` — produces the one-time atomic prune commit per quickstart §2. The commit message and manifest are co-authored documentation of what was removed.
- [X] T042 [P] [US2] Add `scripts/audit_speckit.sh` thin wrapper (Principle V — fail fast on missing venv or missing `.specify/templates/`)
- [X] T043 [US2] Add `audit-speckit` CI job to `.github/workflows/audit.yml` — fails the build if any `template`-classified artifact exists anywhere under `projects/` on main (FR-011)

**Checkpoint**: No template stubs exist under `projects/`; new speckit emissions are guarded; CI breaks on regression. User Story 2 is independently shippable.

---

## Phase 5: User Story 3 — Every PDF page is correct; the arxiv→PDF pipeline is fully scripted (Priority: P1)

**Goal**: Page-level PDF auditor finds zero defects across the supported-PDFs registry; references render `[N]` cite-order (Clarification Q1); figures, author blocks, sections, and links are uniform; the arxiv→PDF pipeline is 100% LLM-free (SC-007) and byte-deterministic on rebuild (SC-008).

**Independent Test**: Auditor reports 0 defects across the registry on a clean rebuild (SC-005); 100% references are `[N]` style (SC-006); a code+CI audit confirms 0 LLM invocations (SC-007); byte-deterministic rebuilds (SC-008).

### Tests for User Story 3

- [X] T044 [P] [US3] `tests/unit/test_pdf_pipeline_normalize_references.py` — input arXiv source with `\cite{...}`, `\citet{...}`, `\citep{...}`, `\cite*{...}`, and `(Smith 2024)` author-year forms; assert all normalize to consistent `\cite{}` + `\bibliographystyle{unsrt}`; resulting bibliography ordered by first-citation appearance (FR-014, Q1)
- [X] T045 [P] [US3] `tests/unit/test_pdf_pipeline_normalize_figures.py` — input with `\includegraphics[width=0.3\textwidth]{...}`, `\includegraphics[width=8cm]{...}`, etc.; assert all rewrite to one of `\figwidth{narrow|column|full}` per [research.md §8](research.md) (FR-015)
- [X] T046 [P] [US3] `tests/unit/test_pdf_pipeline_normalize_authors.py` — input with several author-macro variants; assert all rewrite to one canonical `\authorblock{}` (FR-016)
- [X] T047 [P] [US3] `tests/unit/test_audit_pdf.py` — uses `tests/fixtures/audit/pdf_defective/` (one PDF per defect type from FR-012) and `tests/fixtures/audit/pdf_clean/` (zero-defect PDFs); asserts each defect is detected with correct `paper_id`/`page`/`defect_type`/`evidence_snippet` (FR-013)
- [X] T048 [P] [US3] `tests/real_call/test_audit_pdf_on_corpus.py` — runs the auditor against actual `papers/*.pdf`; outputs the current manifest; on first run before fixes, this test is informational (records baseline defect count); after fixes, this test asserts 0 defects across the registry (SC-005)
- [X] T049 [P] [US3] `tests/real_call/test_pdf_pipeline_e2e_on_corpus.py` — for each paper in `papers/sources/`, runs the deterministic pipeline end-to-end; asserts (a) build succeeds, (b) resulting PDF is auditor-clean OR pipeline failed-loudly with the specific unsupported construct named (FR-019, FR-020), (c) rebuild produces byte-identical PDF modulo timestamps (SC-008)

### Implementation for User Story 3

- [X] T050 [P] [US3] Implement `src/llmxive/pipeline/pdf_pipeline/normalize_references.py` — converts every in-text citation macro to a uniform `\cite{}`, switches bibliography to `unsrt` style; per [research.md §5](research.md). NO LLM imports.
- [X] T051 [P] [US3] Implement `src/llmxive/pipeline/pdf_pipeline/normalize_figures.py` — rewrites `\includegraphics[width=…]{...}` to `\figwidth{narrow|column|full}` based on source-width-vs-textwidth thresholds per [research.md §8](research.md). NO LLM imports.
- [X] T052 [P] [US3] Implement `src/llmxive/pipeline/pdf_pipeline/normalize_authors.py` — rewrites any `\author{}`, `\affiliation{}`, custom author macros into a canonical `\authorblock{}` call (FR-016). NO LLM imports.
- [X] T053 [P] [US3] Implement `src/llmxive/pipeline/pdf_pipeline/restyle.py` — orchestrates the three normalizers + injects `\documentclass{llmxive}`; replaces the legacy LLM-based `scripts/restyle_arxiv_paper.py` logic with deterministic Python (FR-019)
- [X] T054 [P] [US3] Implement `src/llmxive/pipeline/pdf_pipeline/compile.py` — invokes `lualatex` + `bibtex` with deterministic options (fixed `SOURCE_DATE_EPOCH` for byte-determinism per SC-008); fail-fast precondition check that `lualatex` is on PATH (Principle V)
- [X] T055 [US3] Implement `src/llmxive/pipeline/pdf_pipeline/cli.py` — single `build` entrypoint that chains restyle → compile; emits the built PDF plus a build manifest; the import-guard test (T014) keeps this LLM-free
- [X] T056 [US3] Extend `papers/.style/llmxive.cls` — add `\figwidth{narrow|column|full}` macro (FR-015), `\authorblock{}` canonical layout (FR-016), `\unsupportedblock{name}{...}` that emits `\@latex@error` (FR-020), set bibliography style to `unsrt` and ensure `\autoref`/`\ref` defaults are robust (FR-017 — no leaked commands); section-numbering counters set to monotonic (FR-018); per [research.md §8](research.md)
- [X] T056a [P] [US3] `tests/unit/test_pdf_pipeline_unsupported_block.py` — feed a fixture source containing `\unsupportedblock{my-custom-construct}{...}` through the deterministic pipeline; assert (a) `lualatex` exits non-zero, (b) the construct name `my-custom-construct` appears in stderr, (c) the pipeline's CLI exit code is non-zero and the error names the affected paper (FR-020 — silent fallback rendering is forbidden).
- [X] T057 [P] [US3] Implement `src/llmxive/audit/pdf_auditor.py` — page-by-page scan against the FR-012 taxonomy; uses `pdftotext -layout` for text scans and `pdfplumber` for figure geometry per [research.md §2](research.md); emits manifest items with `paper_id`, `page`, `defect_type`, `evidence_snippet`, `auto_fixable`, `rule_id` (FR-013)
- [X] T058 [US3] Wire `audit pdf` CLI subcommand in `src/llmxive/audit/cli.py` — walks `papers/*.pdf`, emits manifest, rewrites `papers/.supported.json` (FR-022 auto-include rule from Clarification Q2) per [contracts/supported-pdfs-registry.schema.json](contracts/supported-pdfs-registry.schema.json)
- [X] T059 [US3] Run the new pipeline against every paper in `papers/sources/` and commit the resulting PDFs; commit the resulting `papers/.supported.json` registry as the initial auto-populated state (FR-022)
- [X] T060 [P] [US3] Delete or quarantine the legacy `scripts/restyle_arxiv_paper.py` if it contained LLM imports; replace with a thin shim that delegates to `python -m llmxive.pipeline.pdf_pipeline.cli build` (Principle I — one canonical entry point)
- [X] T061 [P] [US3] Add `scripts/audit_pdfs.sh` thin wrapper (Principle V — fail-fast on missing `lualatex` / `pdftotext` / `pdfplumber`)
- [X] T062 [US3] Add `audit-pdf` CI job to `.github/workflows/audit.yml` — runs the auditor on every push and fails the build if any registered paper now has defects (SC-005, SC-009); also runs the e2e pipeline test (T049) to ensure byte-determinism on rebuild (SC-008)

**Checkpoint**: Every paper in `papers/.supported.json` builds with zero defects; pipeline is 100% LLM-free; CI gates regressions. User Story 3 is independently shippable.

---

## Phase 6: User Story 4 — Comments and artifacts close the feedback loop (Priority: P1)

**Goal**: Every project has a persisted activity feed; every downstream agent dispatched against the project receives the feed; every agent's output includes a "comments considered" manifest that the runner validates; follow-up personality ticks acknowledge prior contributions; rejected contributions stay in `.audit/`.

**Independent Test**: Seed a project with three known comments; run a revision agent; verify the agent's input context contained the full feed and its output's manifest names all three (SC-010, SC-011, SC-012); rejected contributions absent from agent context (SC-013).

### Tests for User Story 4

- [X] T063 [P] [US4] `tests/unit/test_audit_feedback_loop.py` — exercises the feedback-loop auditor against sampled dispatches; positive (valid manifest, real feed_item_ids) and negative (bogus IDs, missing manifest, truncation_acknowledged false when marker present) per [research.md §7](research.md) (FR-034)
- [X] T064 [P] [US4] `tests/integration/test_runner_injects_feed.py` — seed a project with 5 feed items; invoke the runner against a stub agent; assert the agent's `input_context` contained all 5 items in chronological order with attribution; assert `feed_snapshot_at` was captured (FR-026, FR-033)
- [X] T065 [P] [US4] `tests/integration/test_runner_rejects_missing_manifest.py` — invoke runner against a stub agent that returns no manifest; assert retry-once happened; on second failure, assert a `dispatch_failure` feed item was written, NOT a sham success (FR-028)
- [X] T066 [P] [US4] `tests/integration/test_runner_filters_rejected_contributions.py` — seed a project's `.audit/rejected-contributions.jsonl` with one item; assert that this item is NEVER present in any downstream agent's input context (FR-030, SC-013)
- [X] T067 [P] [US4] `tests/integration/test_runner_truncates_from_oldest.py` — seed a project with 200 feed items exceeding the test budget; assert delivery includes `[truncated N earlier items]` marker and `N` matches the omitted count; agent's manifest must set `truncation_acknowledged: true` (FR-031)
- [X] T068 [P] [US4] `tests/integration/test_feed_concurrent_dispatch.py` — fire two dispatches against the same project at the same `feed_snapshot_at`; assert each agent sees the same feed snapshot; assert both outputs land in feed in commit order with no silent drops (FR-033)
- [X] T069 [P] [US4] `tests/integration/test_feed_edit_history.py` — append an edit to an existing feed item; assert agent context sees only the current text with `[edited]` marker; assert the original is preserved in `.audit/edit-history.jsonl` (FR-032)
- [X] T070 [US4] `tests/real_call/test_seeded_project_revision_loop.py` — full end-to-end real-call test from [quickstart.md §5](quickstart.md): seed a project with three known prior comments (critical personality, positive personality, human flaw-naming), run real revision/review/follow-up personality dispatches through `runner.py`, assert manifest validity (SC-011) and material-addressed rate ≥80% for revision/review and ≥60% for follow-up personality (SC-012). **"Materially addresses" check uses the operational definition added to spec.md §SC-012**: lexical overlap (≥3 shared content noun phrases) OR explicit `rebutted`/`addressed`/`deferred` manifest entry referencing the seeded comment's `feed_item_id`.
- [X] T070a [P] [US4] `tests/integration/test_followup_persona_references_prior.py` — seed a project with one prior persona's `personality_tick` contribution; fire a follow-up persona tick (different persona); assert the new contribution's `comments_considered_manifest.items[]` references the prior item's ULID with response code `addressed|acknowledged|rebutted|deferred`, AND the new contribution body shows lexical or `parent_id` linkage to the prior item (FR-029 — no duplicate-from-scratch contributions).

### Implementation for User Story 4

- [X] T071 [US4] Modify `src/llmxive/agents/runner.py` — before invoking any agent's `run()`, (a) determine `project_id` from the dispatch target, (b) load + pack `projects/<project_id>/activity.jsonl` via `feed/store.py:pack_for_dispatch(...)`, (c) inject as the FIRST project-scoped block in the agent's input context (FR-026), (d) generate a `dispatch_id` ULID and pass it to the agent. NOTE: this is the SINGLE integration point per [research.md §9](research.md) — do not modify each agent individually. **Additional explicit subbullets**: (e) before packing, filter the feed to items where `audit_status == 'live'` — rejected (`audit_status == 'rejected'`) and superseded (`audit_status == 'superseded'`) items MUST NOT appear in the packed context (FR-030); (f) capture `feed_snapshot_at = utcnow_iso()` BEFORE pack so concurrent writes are ordered correctly (FR-033); (g) all feed reads/writes acquire `fcntl.flock` (LOCK_SH for read snapshot, LOCK_EX for append) over the JSONL file to serialise concurrent dispatches with no silent drops (FR-033); (h) record dispatch metadata to `projects/<project_id>/.audit/dispatches/<ts>.jsonl` for FR-034 auditor consumption.
- [X] T072 [US4] In the same `runner.py` modification — after the agent returns, call `feed/manifest.py:ManifestValidator.validate(output, dispatch_id, snapshot_at)`. On success: parse the contribution + manifest, append both to `activity.jsonl`. On failure: retry ONCE; on second failure append a `dispatch_failure` feed item with the reason (FR-028).
- [X] T072a [P] [US4] Implement `src/llmxive/feed/store.py:FeedStore.edit(item_id, new_body, editor)` and `retract(item_id, editor)` — the edit writer. `edit(...)`: (a) appends a new feed item of `kind: edit` with `parent_id = item_id`, `body = new_body`, `author = editor`, `created_at = utcnow_iso()`; (b) writes the original item's body + ISO timestamp to `projects/<project_id>/.audit/edit-history.jsonl`; (c) the reader resolves "current" body via a `parent_id` chain when packing (newest `kind: edit` for a given `parent_id` chain wins, original's body becomes a fallback if no edits exist); (d) `retract(...)` flips the original item's `audit_status` from `live` to `superseded` and writes the retraction reason to `.audit/edit-history.jsonl`. FR-032. Unit test in T069 wires against this API.
- [X] T073 [US4] Implement `src/llmxive/audit/feedback_loop.py` — walks runner dispatch records (logged to `.audit/dispatches/<ts>.jsonl` by runner) and validates each per FR-034: (a) input context contained the feed, (b) output contained a valid manifest referencing only real feed items
- [X] T074 [US4] Wire `audit feedback_loop` CLI subcommand in `src/llmxive/audit/cli.py` — `--projects-dir` + `--since` flags; emits manifest to `.audit/feedback_loop/<ts>.json`
- [X] T075 [P] [US4] Update `agents/prompts/personality.md` (lands on top of the US1 changes) — add explicit instruction to scan the delivered activity feed before choosing a target, acknowledge or differentiate from prior persona contributions visible in the feed (FR-029), end output with the structured `comments-considered` JSON block per [contracts/comments-considered-manifest.schema.json](contracts/comments-considered-manifest.schema.json)
- [X] T076 [P] [US4] Update `agents/prompts/` for every agent that emits a contribution (review, revision, paper writing, paper reviewer, etc.) — add the structured `comments-considered` JSON block requirement; the runner-level validator (T072) gates everything regardless, but explicit prompt instruction increases compliance
- [X] T077 [P] [US4] Add `scripts/audit_feedback_loop.sh` thin wrapper (Principle V — fail-fast on missing dispatch records directory)
- [X] T078 [US4] Add `audit-feedback-loop` CI job to `.github/workflows/audit.yml` — runs on every push against a 24-hour-since window; fails the build on SC-010 or SC-011 regression
- [X] T079 [US4] Backfill: write a one-time migration script `scripts/init_activity_feeds.py` that creates an empty `projects/<project_id>/activity.jsonl` for every existing project; idempotent (skip if file exists)

**Checkpoint**: Every dispatch receives the feed and is required to acknowledge it; rejected contributions stay out of agent context; CI gates regressions. User Story 4 is independently shippable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Wire CI fully, add documentation, verify no regressions on the existing test suite.

- [ ] T080 [P] Update `papers/.style/README.md` (or create) to document the `\figwidth`, `\authorblock`, and `\unsupportedblock` macros (FR-015, FR-016, FR-020); cross-link from [plan.md §Project Structure](plan.md)
- [ ] T081 [P] Update [README.md](README.md) "Development Guidelines" section to cross-link to the four auditors and the activity feed (constitution-driven follow-up TODO)
- [ ] T082 [P] Add `notes/009-quality-fixes-status.md` capturing the implementation summary (per project convention — global CLAUDE.md memory rule about session notes)
- [ ] T083 Run the full test suite per `tests/run_tests.py`; fix any regressions; re-run after each fix until all green (Constitution Principle III — never simplify tests; fix code)
- [ ] T084 [P] Verify Constitution Principle I — grep for duplicated logic: any module that re-implements feed read/write outside `src/llmxive/feed/`, any auditor that re-loads template strings outside `template_vs_real.py`, any LLM-banned import inside `pdf_pipeline/`. Fix any violations.
- [ ] T085 Run all four auditors against the live repo state per [quickstart.md](quickstart.md): personality, speckit, pdf, feedback_loop. Confirm zero outstanding `template` artifacts, zero PDF defects in the registry, valid manifests across recent dispatches.
- [ ] T086 Monitor spec-008 dartmouth-backend pinning during US1 rubric acceptance: review the first full rotation's rubric-failure log; if rubric failures cluster on a particular backend behaviour, open a follow-up GitHub issue referencing spec 008. **NO code change is performed in this task by default** — it is a monitoring/escalation checkpoint, not an edit.
- [ ] T087 [P] Update `CLAUDE.md` SPECKIT block to reference this plan (already done by Phase 1; verify in this task) and add a brief "implementation status: complete" line if all SC-001..SC-013 pass
- [ ] T088 Commit + push the entire 009 branch; open a PR; ensure all four CI auditor jobs are green before merge

---

## Dependencies

```text
Phase 1 (Setup) ──────────────────► Phase 2 (Foundational)
                                          │
            ┌────────────────┬─────────────┴────────────┬─────────────────┐
            ▼                ▼                          ▼                 ▼
       Phase 3 (US1)    Phase 4 (US2)             Phase 5 (US3)      Phase 6 (US4)
       personality      speckit                   PDF pipeline       feedback-loop
       curation         enforcement               hardening          activity feed
            │                │                          │                 │
            └────────────────┴─────────────┬────────────┴─────────────────┘
                                           ▼
                                    Phase 7 (Polish)
```

**Within each user story phase**:
- `[P]`-marked tasks within a phase can run in parallel (they touch different files).
- Non-`[P]` tasks must wait for upstream tasks in the same phase (e.g. T023 depends on T020+T021+T022; T024 depends on T023).

**Cross-story coupling**:
- US4 (feedback loop) provides the runner-feed infrastructure. US1's T024 (audit personality CLI walks `activity.jsonl`) **technically reads** this; if implementing strictly in order US1→US2→US3→US4, write a compatibility shim that returns an empty feed when `activity.jsonl` is missing — every US1 test still passes against the shim. Recommended order: implement US4 second (after US2) for the cleanest stack, then re-run US1's full real-call test. Acceptable order: US1→US2→US3→US4 with the shim; this is what the plan defaults to.

## Parallel Execution Examples

**Phase 1 Setup**: T004, T005, T006, T007 all parallel-safe (different files).

**Phase 2 Foundational**: T009, T010, T011 parallel-safe (different modules); T012, T013, T015 parallel-safe tests against different modules; T014 is a meta-test on the import structure of the `pdf_pipeline` package — parallel-safe.

**Phase 3 US1**:
- Parallel cluster A (tests, all different files): T016, T017, T018, T019
- Parallel cluster B (implementation files): T020, T021, T022 (note T022 internally branches into 10 parallel persona-card edits — each `personalities/*.md` is independent)
- Serial: T023 → T024 → T025

**Phase 4 US2**:
- Parallel cluster A (tests): T026, T027, T028, T029
- Parallel cluster B (speckit emitter modifications): T034, T035, T036, T037, T038, T039, T040 — each is a distinct file
- Serial: T030 → T031 → T032 → T033 (each depends on the prior) → T041 (one-shot prune) → T042 → T043

**Phase 5 US3**:
- Parallel cluster A (tests): T044, T045, T046, T047, T048, T049
- Parallel cluster B (normalizers): T050, T051, T052 — independent modules
- Serial: T053 (orchestrator) → T054 (compiler) → T055 (CLI) → T056 (class extension; depends on T050-T052 macros being known) → T057 (PDF auditor) → T058 (CLI wire) → T059 (one-shot build of corpus) → T060, T061, T062

**Phase 6 US4**:
- Parallel cluster A (tests): T063, T064, T065, T066, T067, T068, T069, T070
- Parallel cluster B (prompt updates): T075, T076 — different files
- Serial: T071 → T072 (both in `runner.py`; same file) → T073 → T074 → T077 → T078 → T079

## Implementation Strategy

**MVP scope** = Phase 1 + Phase 2 + Phase 3 (User Story 1 — personality curation). This is the headline user-visible improvement and is independently shippable.

**Incremental delivery**:
1. **Sprint A**: Phases 1, 2, 3 → ship personality curation. SC-001 measurable on day one of next rotation.
2. **Sprint B**: Phase 4 → ship speckit enforcement + prune. SC-002, SC-003, SC-004 measurable immediately.
3. **Sprint C**: Phase 5 → ship PDF auditor + deterministic pipeline. SC-005, SC-006, SC-007, SC-008 measurable on next paper build.
4. **Sprint D**: Phase 6 → ship feedback loop. SC-010, SC-011, SC-012, SC-013 measurable after one week of dispatches.
5. **Sprint E**: Phase 7 → polish, docs, CI green, merge.

Total: 92 tasks (88 original + 4 added by /speckit-analyze remediation — T022a, T056a, T070a, T072a), ~14 parallel clusters, 4 sprints + polish.

## Independent Test Criteria Recap

| Story | Independent Test |
|-|-|
| US1 | 30 fresh ticks scored by deterministic rubric; ≥80% critical-judgement, ≥60% adjacent-work, <10% manufactured-praise (SC-001). |
| US2 | 0 template-classified artifacts after prune (SC-002); 0 template artifacts emitted in 100 invocations (SC-003); 0 spurious progressions (SC-004). |
| US3 | 0 PDF defects across registry (SC-005); 100% `[N]` references (SC-006); 0 LLM calls in PDF pipeline (SC-007); byte-deterministic rebuilds (SC-008). |
| US4 | 100% dispatches receive feed (SC-010); ≥95% valid manifests (SC-011); ≥80% / ≥60% materially-addresses rate (SC-012); 0% rejected contributions delivered to agents (SC-013). |
