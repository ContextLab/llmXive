# Tasks: Paper Revision Implementer + Publisher

**Input**: Design documents from `/specs/013-paper-revision-implementer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests ARE in scope. The spec mandates SC-005 (real-call E2E for the implementer) and SC-006 (real-call sandbox test for the publisher); the constitution mandates real-call coverage per Principle III. Each user story phase therefore includes both unit-test and real-call-test tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

Single-project Python layout per [plan.md](plan.md#project-structure):
- `src/llmxive/...` — production code
- `tests/unit/...` — fast deterministic tests
- `tests/real_call/...` — gated on `LLMXIVE_REAL_TESTS=1`, hits real APIs

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization tasks shared across every user story.

- [X] T001 Add `load_zenodo_token(sandbox: bool = False)` to [src/llmxive/credentials.py](src/llmxive/credentials.py) mirroring the existing `load_dartmouth_key()` pattern — reads `~/.config/llmxive/credentials.toml::[zenodo].api_token` (or `[zenodo_sandbox].api_token` when sandbox=True), falls back to `ZENODO_API_TOKEN` / `ZENODO_SANDBOX_API_TOKEN` env, raises `MissingCredentialError` on absence.
- [X] T002 Pull `READY_FOR_IMPLEMENTATION` and `paper_accepted` OUT of [src/llmxive/scheduler.py](src/llmxive/scheduler.py)'s `_NEVER_PICK` set so the scheduler picks up these stages for the new agents.
- [X] T003 [P] Add `PAPER_REVISION_BLOCKED` and `publish_blocked` values to the Stage enum in [src/llmxive/types.py](src/llmxive/types.py) (FR-015, FR-030).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema and state-management infrastructure that every user story depends on.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T004 [P] Add `ImplementerLogEntry`, `RevisionRound`, `RevisionHistory` pydantic v2 models to [src/llmxive/types.py](src/llmxive/types.py) matching the schemas in [contracts/implementer-log-yaml.md](specs/013-paper-revision-implementer/contracts/implementer-log-yaml.md) and [contracts/revision-history-yaml.md](specs/013-paper-revision-implementer/contracts/revision-history-yaml.md).
- [X] T005 [P] Extend `AuthorEntry` in [src/llmxive/types.py](src/llmxive/types.py) with `kind: Literal["human", "llm"]`, `agent_version`, `model_name`, `backend`, `first_contributed_at` fields per [data-model.md](specs/013-paper-revision-implementer/data-model.md) §4; existing untyped entries deserialize as `kind="human"`.
- [X] T006 [P] Add `Publication`, `DOIVersion`, `VolumeIssue`, `ZenodoDeposition` pydantic models to [src/llmxive/types.py](src/llmxive/types.py) per [contracts/publication-yaml.md](specs/013-paper-revision-implementer/contracts/publication-yaml.md) and [data-model.md](specs/013-paper-revision-implementer/data-model.md) §6–8.
- [X] T007 Create [src/llmxive/state/revision_history.py](src/llmxive/state/revision_history.py) with `load(project_id, *, repo_root)`, `append_round(project_id, round, *, repo_root)`, `last_n_rounds(project_id, n, *, repo_root)`, `load_round(project_id, round_number, *, repo_root)`, `save_round(project_id, round_number, log, *, repo_root)`, `list_rounds(project_id, *, repo_root)`. Atomic-write via tmpfile + rename. Raises `ValueError("round N already recorded")` on duplicate append.
- [X] T008 Create [src/llmxive/state/publication.py](src/llmxive/state/publication.py) with `load(project_id, *, repo_root)`, `save(project_id, pub, *, repo_root)`, `append_version(project_id, version, *, repo_root)`. Atomic-write via tmpfile + rename.
- [X] T009 Create [src/llmxive/pipeline/authors.py](src/llmxive/pipeline/authors.py) with `add_implementer(metadata_path, agent_identity, *, model_name, backend, agent_version, first_contributed_at)` (append-only, deduplicated by `(name, agent_version)` per FR-008), `update_latex_author_block(tex_path, authors)` (preserves originals, appends `\par\hrule\par \textit{Revised by:}` block + LLM contributors per FR-007).
- [X] T010 Create [src/llmxive/pipeline/zenodo.py](src/llmxive/pipeline/zenodo.py) with `ZenodoClient` class: `__init__(*, sandbox=False)`, `create_deposition(metadata) -> Deposition`, `upload_file(bucket, name, content)`, `publish(deposition_id) -> PublishedDeposition`, `new_version(deposition_id) -> Deposition`. Raises `ZenodoAPIError(status_code, message)` on non-2xx. Implements the operations in [contracts/zenodo-api.md](specs/013-paper-revision-implementer/contracts/zenodo-api.md).
- [X] T011 Promote [specs/013-paper-revision-implementer/prototypes/gen_appendix.py](specs/013-paper-revision-implementer/prototypes/gen_appendix.py) to [src/llmxive/pipeline/post_paper_appendix.py](src/llmxive/pipeline/post_paper_appendix.py): same `render_inline`, `render_markdown_body`, `parse_review_file`, `render_reviews`, `render_history` functions. CLI entry preserved as `python -m llmxive.pipeline.post_paper_appendix <project_dir>`. Add a `render_spacer(project_id) -> str` helper that emits the spacer page with the **GitHub project-directory link** `https://github.com/ContextLab/llmXive/tree/main/projects/<project_id>/` (FR-033 — the link points to the project's GitHub directory, NOT the dashboard root). Add a unit test in [tests/unit/test_post_paper_appendix.py](tests/unit/test_post_paper_appendix.py) (NEW) asserting the spacer output contains exactly this URL form (closes finding F5).

**Checkpoint**: Foundation ready — schemas, state I/O, and Zenodo client all in place. User-story work can begin.

---

## Phase 3: User Story 1 — Writing-class implementer (Priority: P1) 🎯 MVP

**Goal**: An LLM-driven agent applies writing-severity tasks from a revision spec to `paper/source/main.tex`, rolls back any edit that breaks LaTeX compilation, and re-routes the project to `paper_review`.

**Independent Test**: Drive the implementer against a fixture project at `READY_FOR_IMPLEMENTATION` with a 3-task writing-only revision spec. Assert: (a) `paper/source/main.tex` is modified, (b) the modifications correspond to the action items, (c) `lualatex` still compiles, (d) `current_stage` is now `paper_review`.

### Tests for User Story 1

- [X] T012 [P] [US1] Unit tests for edit-application helpers in [tests/unit/test_implementer.py](tests/unit/test_implementer.py): `search_and_replace` single-match success, multi-match rejection (skipped), no-match rejection (skipped), `unified_diff` apply success, `git apply --check` failure (skipped), file-not-found handling. **FR-017 invariant** (closes finding F4): assert that a `search_and_replace` whose `replace` is empty AND whose `search` matches `\begin{abstract}…\end{abstract}` or `\bibliography{…}` is rejected as `skipped` (whole-section / bibliography deletions are forbidden).
- [X] T013 [P] [US1] Unit tests for per-task snapshot + rollback in [tests/unit/test_implementer.py](tests/unit/test_implementer.py): `before_bytes` captured, restore-on-fail returns file to exact prior bytes, `before_hash`/`after_hash` recorded correctly.
- [X] T014 [US1] Real-call end-to-end test in [tests/real_call/test_implementer_e2e.py](tests/real_call/test_implementer_e2e.py) for SC-001: a 3-task writing fixture (Dartmouth API), wall-clock ≤10 min, assert stage transition + log shape.

### Implementation for User Story 1

- [X] T015 [P] [US1] Create LLM system prompt at [src/llmxive/agents/prompts/implementer.md](src/llmxive/agents/prompts/implementer.md): "You revise an existing LaTeX paper; you do NOT rewrite it. Output structured `search_and_replace` or `unified_diff` blocks only." (FR-018)
- [X] T016 [P] [US1] Create per-task edit-generation prompt at [src/llmxive/agents/prompts/implementer_edit.md](src/llmxive/agents/prompts/implementer_edit.md) with action-item text + windowed manuscript view + edit-format spec.
- [X] T017 [US1] Create [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py) — `LLMXiveImplementer(Agent)` class with `build_messages(ctx)` and `handle_response(ctx, response)` per the existing Agent contract. Read `Project.revision_spec_path`, iterate tasks in document order.
- [X] T018 [P] [US1] Implement `_apply_search_and_replace(file_path, search, replace) -> EditResult` in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): assert single match, write replacement, return path + hashes. Reject ambiguous/no-match as `skipped`.
- [X] T019 [P] [US1] Implement `_apply_unified_diff(file_path, diff) -> EditResult` in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): `git apply --check` (in-process via subprocess), then `git apply` if check passed. Reject as `skipped` if check fails.
- [X] T020 [US1] Implement `_snapshot_and_apply` per-task helper in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): capture `before_bytes` + `before_hash`, apply edit, call `_compile_paper` (existing pipeline), on success record `done`, on failure restore bytes + record `compile-failed`.
- [X] T021 [US1] Wire the per-task loop in `LLMXiveImplementer.run()` in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): iterate tasks, accumulate outcomes, persist `implementer-log.yaml` via `state.revision_history.save_round()`.
- [X] T022 [US1] Implement post-loop stage transition + `consecutive_zero_round_count` failsafe in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): clear `Project.revision_spec_path` (FR-014), transition `READY_FOR_IMPLEMENTATION → PAPER_REVIEW` (FR-013), increment per-project counter on zero-success round, transition to `PAPER_REVISION_BLOCKED` after 3 consecutive (FR-015). Counter stored at `state/<id>.implementer.yaml`.
- [X] T023 [US1] Register `llmXive-implementer-v1.0` in [agents/registry.yaml](agents/registry.yaml): `default_backend: dartmouth`, `default_model: qwen.qwen3.5-122b`, `fallback_backends: [huggingface]`, `wall_clock_budget_seconds: 1800`.

**Checkpoint**: US1 complete — writing-class revisions land in production.

---

## Phase 4: User Story 2 — Science-class implementer extension (Priority: P1)

**Goal**: The same implementer agent handles `science`-severity tasks that may touch files outside `paper/source/` (research code, data files, analysis notebooks). After science-class edits land, the manuscript still recompiles AND any referenced analysis scripts run without errors (best-effort).

**Independent Test**: Fixture project with one `science`-severity task that modifies `projects/<id>/code/analysis.py` AND a referencing section in `main.tex`. Assert: (a) both files are modified consistently, (b) PDF rebuilds, (c) project transitions to `paper_review`.

- [X] T024 [US2] Extend `_validate_edit_path()` in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py) to permit `projects/<id>/code/` and `projects/<id>/data/` paths when the task's severity is `science`. Writing-class tasks remain limited to `paper/source/` (FR-019).
- [X] T025 [P] [US2] Add `needs-external-data` to the `status` Literal in `ImplementerLogEntry` ([src/llmxive/types.py](src/llmxive/types.py)) — the implementer marks a science-class task this way when an analysis script needs data that isn't checked in (FR-019 best-effort clause).
- [X] T026 [US2] Implement `_run_referenced_analysis_scripts(task, modified_paths)` in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): when a science-class task modifies a `.py` file, exec it in a subprocess with a 5-min budget; non-zero exit → rollback + record `compile-failed`; missing-data exception → record `needs-external-data` (do NOT rollback the manuscript edit).
- [X] T027 [US2] Unit tests in [tests/unit/test_implementer.py](tests/unit/test_implementer.py): science-class file-path validation (allows code/, data/; rejects projects/<id>/notes/), analysis-script success path, analysis-script failure rollback path, `needs-external-data` non-rollback path.

**Checkpoint**: US2 complete — science-class verdicts are reachable in practice.

---

## Phase 5: User Story 3 — Authors join author list (Priority: P1)

**Goal**: Every implementer that lands ≥1 successful task joins the paper's author list (in `paper/metadata.json::authors` AND the LaTeX `\author{}` macro), append-only, deduplicated by `(name, agent_version)`. Re-runs of the same agent never duplicate.

**Independent Test**: Drive the implementer twice on the same fixture. Inspect `metadata.json` and the `\author{}` block. Assert: (a) original authors preserved, (b) implementer added exactly once across both runs, (c) `\author{}` has a "Revised by:" sub-block, (d) regenerated PDF title page shows the new author block.

- [X] T028 [P] [US3] Implement `authors.add_implementer()` in [src/llmxive/pipeline/authors.py](src/llmxive/pipeline/authors.py): read `metadata.json::authors`, dedupe by `(name, agent_version)` per FR-008, append `AuthorEntry(kind="llm", ...)` on first contribution. Original entries untouched per FR-006.
- [X] T029 [P] [US3] Implement `authors.update_latex_author_block()` in [src/llmxive/pipeline/authors.py](src/llmxive/pipeline/authors.py): parse the existing `\author{...}` arg with a brace-balanced scanner, preserve original-author content verbatim, append `\par\hrule\par \textit{Revised by:}` then LLM-contributor names in chronological order (FR-007). Handles malformed/empty original entries per Edge Case 5.
- [X] T030 [US3] Wire `authors.add_implementer()` + `authors.update_latex_author_block()` into [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py)'s post-loop step (after ≥1 successful task, before final recompile).
- [X] T031 [P] [US3] Unit tests in [tests/unit/test_authors.py](tests/unit/test_authors.py): single-author paper extended; multi-author paper preserved + extended; same-agent re-run no-ops; different agent_version creates new entry; empty original author list → implementer is sole author; malformed entries don't crash; LaTeX `\author{}` parsing handles nested braces in affiliations. **FR-016 invariant** (closes finding F3): assert `add_implementer()` does NOT modify `arxiv_id`, `arxiv_url`, `title`, `submitter`, or any non-`authors` field of `metadata.json`.

**Checkpoint**: US3 complete — LLM authors visible on the byline + in metadata.

---

## Phase 6: User Story 4 — PDF status badge via existing class (Priority: P1)

**Goal**: After every successful implementer round, the regenerated PDF's title-page byline shows `\paperstatus{Auto-Reviewed}` (or the appropriate state). No coversheet, no per-page footer overlay. Status is owned by the existing `llmxive.cls` typographic system.

**Independent Test**: Inspect the regenerated `paper/pdf/main.pdf`. Assert title-page byline reflects current state via `paperstatus`; no coversheet prepended.

- [X] T032 [P] [US4] Verify `\paperstatus`, `\paperdoi`, `\papervolume`, `\paperissue` are present and functional in [papers/.style/llmxive.cls](papers/.style/llmxive.cls). These shipped in commit `3817c32b`; this task is a regression check via a 1-page synthetic doc that exercises all four commands.
- [X] T033 [P] [US4] Implement `_resolve_paperstatus_for_revision_round(round_number, total_tasks_done) -> str` helper in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): returns `"Auto-Reviewed"` when ≥1 task succeeded in this round; `"Preprint"` when 0 (no badge change).
- [X] T034 [US4] Wire the resolved status into the implementer's recompile path in [src/llmxive/agents/implementer.py](src/llmxive/agents/implementer.py): inject `\paperstatus{<value>}` into `main.tex` preamble (or update existing line) prior to `lualatex`. If `\paperstatus` is absent, append a search-and-replace before `\begin{document}`.
- [X] T035 [US4] Unit test in [tests/unit/test_implementer.py](tests/unit/test_implementer.py): `_resolve_paperstatus_for_revision_round(1, 5) == "Auto-Reviewed"`; `_resolve_paperstatus_for_revision_round(1, 0) == "Preprint"`. Integration test using a minimal `main.tex` confirming the `\paperstatus{...}` line lands correctly after a round.

**Checkpoint**: US4 complete — readers can tell from the title page that a paper has been auto-reviewed.

---

## Phase 7: User Story 6 — Publisher + Zenodo DOI + post-paper appendix (Priority: P1)

**Goal**: Accepted papers go through a deterministic `paper_publisher` agent that registers a real DOI via Zenodo, regenerates the PDF with the final byline + post-paper appendix (reviews + revision changelog), and transitions the project to `posted`.

**Independent Test**: Drive a fixture from `paper_accepted` through the publisher. Assert: (a) PDF byline shows `Auto-Reviewed | Auto-Revised | Published` + DOI + `26.05`, (b) `paper/publication.yaml` exists with canonical fields, (c) post-paper appendix present (spacer + reviews + changelog), (d) stage = `posted`, (e) activity-log entry emitted, (f) `#published` lists the project, (g) no coversheet.

### Tests for User Story 6

- [X] T036 [P] [US6] Unit tests in [tests/unit/test_publisher.py](tests/unit/test_publisher.py): badge resolution (2-state vs 3-state per FR-022), VolumeIssue.from_datetime("2026-05-19") → ("26", "05"), publish_blocked counter increments on simulated Zenodo failure, counter resets on success.
- [X] T037 [P] [US6] Unit tests in [tests/unit/test_publication.py](tests/unit/test_publication.py): publication.yaml round-trips through pydantic, doi_versions appends correctly on re-publication. **metadata.json mirror assertion (closes finding F9, SC-007)**: after `publication.save()`, assert `metadata.json::doi == publication.yaml::doi`, `metadata.json::doi_url == publication.yaml::doi_url`, `metadata.json::zenodo_id == publication.yaml::zenodo_id`, `metadata.json::volume == publication.yaml::volume`, `metadata.json::issue == publication.yaml::issue`. All mirror fields populated and non-empty.
- [X] T038 [US6] Real-call test in [tests/real_call/test_publisher_zenodo_sandbox.py](tests/real_call/test_publisher_zenodo_sandbox.py) for SC-006 + SC-008: minimal fixture at `paper_accepted`, point at Zenodo Sandbox, assert DOI begins with `10.5072/zenodo.`, publication.yaml written, stage = `posted`, HTTP HEAD on DOI returns 200/302 within 2 min. **DOI-versioning sub-test (closes finding F6, SC-008)**: drive a SECOND publication on the same fixture (set stage back to `paper_accepted`, re-run the publisher), assert (a) a new DOI is minted that differs from the first, (b) `publication.yaml::doi_versions` has 2 entries with `version_index == 1` and `== 2`, (c) HTTP HEAD on the ORIGINAL DOI URL still returns 200/302 (original version preserved per FR-027).

### Implementation for User Story 6

- [X] T039 [US6] Implement `VolumeIssue.from_datetime()` classmethod in [src/llmxive/types.py](src/llmxive/types.py) per [data-model.md](specs/013-paper-revision-implementer/data-model.md) §6.
- [X] T040 [P] [US6] Implement `ZenodoClient.create_deposition()` in [src/llmxive/pipeline/zenodo.py](src/llmxive/pipeline/zenodo.py) per [contracts/zenodo-api.md](specs/013-paper-revision-implementer/contracts/zenodo-api.md) O1 — pre-reserves a DOI, returns Deposition with `id`, `doi`, `bucket_url`, `publish_url`.
- [X] T041 [P] [US6] Implement `ZenodoClient.upload_file()` in [src/llmxive/pipeline/zenodo.py](src/llmxive/pipeline/zenodo.py) per O2 (PUT to bucket URL).
- [X] T042 [P] [US6] Implement `ZenodoClient.publish()` in [src/llmxive/pipeline/zenodo.py](src/llmxive/pipeline/zenodo.py) per O3, returning PublishedDeposition with `doi`, `doi_url`, `concept_doi`.
- [X] T043 [P] [US6] Implement `ZenodoClient.new_version()` in [src/llmxive/pipeline/zenodo.py](src/llmxive/pipeline/zenodo.py) per O4 for FR-027 DOI versioning.
- [X] T044 [US6] Create [src/llmxive/agents/publisher.py](src/llmxive/agents/publisher.py) — `PaperPublisher(Agent)` class. Determinism: no LLM calls. Implements the step sequence in [contracts/publisher-agent.md](specs/013-paper-revision-implementer/contracts/publisher-agent.md) §Steps.
- [X] T045 [US6] Implement `_resolve_badge(revision_history) -> str` in [src/llmxive/agents/publisher.py](src/llmxive/agents/publisher.py) per FR-022: 3-state when ≥1 round succeeded, 2-state otherwise.
- [X] T046 [US6] Wire post-paper appendix in [src/llmxive/agents/publisher.py](src/llmxive/agents/publisher.py) — call `pipeline.post_paper_appendix.render_to_file(project_dir, out_path)`, `\input` it before `\end{document}` of `main.tex`.
- [X] T047 [US6] Implement DOI-versioning branch in [src/llmxive/agents/publisher.py](src/llmxive/agents/publisher.py): if `metadata.json::zenodo_id` is set, call `new_version()` per FR-027; append to `doi_versions`.
- [X] T048 [US6] Implement `publish_blocked` failsafe in [src/llmxive/agents/publisher.py](src/llmxive/agents/publisher.py): on `ZenodoAPIError` or `ConnectionError`, increment per-project `consecutive_publish_failures` (stored at `state/<id>.publisher.yaml`). On 5 consecutive failures, transition to `publish_blocked` per FR-030. Counter resets on success.
- [X] T049 [US6] Implement stage transition + activity-log emit in [src/llmxive/agents/publisher.py](src/llmxive/agents/publisher.py): `paper_accepted → posted` (FR-021), emit run-log entry `agent_name: paper_publisher` (FR-028).
- [X] T050 [US6] Register `paper_publisher` in [agents/registry.yaml](agents/registry.yaml): `default_backend: deterministic` (no LLM), `wall_clock_budget_seconds: 300`. No fallback backends.
- [X] T051 [P] [US6] Create [scripts/publish_paper.py](scripts/publish_paper.py) implementing `llmxive project republish <PROJ-ID>` per FR-030 — rolls `publish_blocked` back to `paper_accepted` and zeros the failure counter.
- [X] T052 [P] [US6] Update [web/](web/) — the dashboard's `papers` tab filter MUST surface `posted` (already in place from earlier work). Remove `paper_accepted` from the filter per FR-029 (`paper_accepted` is now a transient pre-publication state).

**Checkpoint**: US6 complete — accepted papers actually become public, citable artifacts.

---

## Phase 8: User Story 5 — Re-review honors prior items (Priority: P2)

**Goal**: After the implementer returns control to `paper_review`, the per-specialist re-review (spec 012's diff-check protocol) fires. Every specialist accepts → `paper_accepted`. Any specialist re-flags an unaddressed item → new revision round.

**Independent Test**: Drive a fixture through round 1 (implementer with 4/5 tasks succeeding, 1 compile-failed) + round 2 (re-review). Assert: the compile-failed task's specialist re-flags it, project re-enters `READY_FOR_IMPLEMENTATION` for round 2 with the un-addressed item.

- [X] T053 [US5] Integration test in [tests/real_call/test_implementer_e2e.py](tests/real_call/test_implementer_e2e.py): extend the existing E2E to drive round 1 (implementer) + round 2 (re-review) on the same fixture. Assert FR-014..FR-017 behaviors hold (round increments, re-review fires, transitions per spec 012). No new code required — this verifies spec 012's per-specialist re-review correctly activates after the implementer's transition.

**Checkpoint**: US5 complete — the convergence loop closes via the re-existing re-review machinery.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T054 [P] Add `PAPER_REVISION_BLOCKED` and `publish_blocked` badges to [web/](web/) status renderer with operator-facing diagnostic text.
- [X] T055 [P] Update activity-log renderer in [web/](web/) to display new agents (`llmXive-implementer-v1.0`, `paper_publisher`) with appropriate icons/labels.
- [X] T056 [P] Add dashboard modal section for `revision_history.yaml` + per-round `implementer-log.yaml` per FR-020 — round number, agent identity, tasks done/failed, link to new PDF, link to changelog.
- [X] T057 [P] Update [README.md](README.md) — add a short paragraph in the Workflow section describing US6 (publication step + Zenodo DOI). Mention the `[zenodo]` credentials.toml section. Per the constitution's Documentation-parity rule.
- [X] T058 Run the full test suite: `pytest -q` (deterministic) + `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/ -q` (real-call). All tests MUST pass per Principle III; any failures must be diagnosed and fixed before the spec is considered shipped. **SC-002 operational check (closes finding F7)**: after driving the implementer through up to 5 rounds against PROJ-578, assert `current_stage` is one of `{PAPER_ACCEPTED, posted, PAPER_REVISION_BLOCKED}` — endless oscillation between `paper_review` and `READY_FOR_IMPLEMENTATION` is a regression. Inspect via `yq '.rounds | length' projects/PROJ-578-*/paper/revision_history.yaml` and the project's stage field.

---

## Dependencies & Execution Order

```
Phase 1 (Setup: T001-T003)
   ↓
Phase 2 (Foundational: T004-T011)   ◄── BLOCKS every user story
   ↓
Phase 3 (US1: writing implementer, T012-T023)   ◄── MVP target
   ↓
Phase 4 (US2: science extension, T024-T027)   ◄── depends on US1
   ↓
Phase 5 (US3: authors, T028-T031)   ◄── depends on US1 (implementer must exist before it can self-add)
   ↓
Phase 6 (US4: PDF badge, T032-T035)   ◄── can run in parallel with Phase 5
   ↓
Phase 7 (US6: publisher, T036-T052)   ◄── depends on US3 (publisher needs the author list to format citations)
   ↓
Phase 8 (US5: re-review verification, T053)   ◄── depends on US1
   ↓
Phase 9 (Polish, T054-T058)
```

## Parallel Opportunities

- **Phase 2**: T004, T005, T006 are 3 independent type definitions and can run in parallel. T007, T008, T009, T010, T011 each touch different files and can run in parallel after the types are defined.
- **Phase 3 (US1)**: T012, T013, T015, T016 are independent (different files) and can run in parallel. T018, T019 can run in parallel.
- **Phase 5 (US3) & Phase 6 (US4)**: completely independent. Run in parallel after US1 completes.
- **Phase 7 (US6)**: T040, T041, T042, T043 (Zenodo client methods) are independent and can run in parallel.
- **Phase 9**: T054, T055, T056, T057 are independent.

## Implementation Strategy

1. **MVP cut**: ship US1 (writing implementer) + US3 (authors) + US4 (PDF badge). This produces revised papers with proper attribution and a clear visual indicator, even before the publisher is ready.
2. **Convergence cut**: add US5 (re-review verification) so the loop closes.
3. **Publication cut**: add US6 (publisher + Zenodo) so accepted papers actually become public.
4. **Optional**: US2 (science-class extension) can ship later if all of PROJ-578's action items turn out to be writing-class. Verify the action-item distribution first via `yq '.task_outcomes[].severity' specs/auto-revisions/PROJ-578-*/round-1/*.yaml`.

## Independent test criteria per user story

| Story | Test criterion |
|-|-|
| US1 | 3-task writing fixture: `main.tex` modified, compiles, stage transitions to `paper_review` (≤10 min, SC-001) |
| US2 | 1 science-class task fixture: `code/analysis.py` + `main.tex` both modified consistently, PDF rebuilds |
| US3 | After 2 implementer runs: author list has originals + exactly one LLM entry; LaTeX byline has "Revised by:" |
| US4 | Regenerated PDF byline shows `\paperstatus{Auto-Reviewed}`; no coversheet, no per-page footer overlay |
| US5 | Round 1 (4/5 tasks) + round 2 (re-review re-flags the failed task) → project loops back to `READY_FOR_IMPLEMENTATION` |
| US6 | Sandbox publication: `10.5072/zenodo.<n>` DOI, publication.yaml present, stage = `posted`, HEAD on DOI resolves (≤2 min, SC-006) |

## Total task count

- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 8 tasks
- Phase 3 (US1): 12 tasks
- Phase 4 (US2): 4 tasks
- Phase 5 (US3): 4 tasks
- Phase 6 (US4): 4 tasks
- Phase 7 (US6): 17 tasks
- Phase 8 (US5): 1 task
- Phase 9 (Polish): 5 tasks

**Total: 58 tasks across 9 phases.**
