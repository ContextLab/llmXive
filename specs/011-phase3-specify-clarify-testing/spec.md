# Feature Specification: Phase 3 Pipeline Validation — Specifier + Clarifier

**Feature Branch**: `011-phase3-specify-clarify-testing`
**Created**: 2026-05-16
**Status**: Draft
**Input**: User description: "Phase 3: issue 47 + all sub-issues + any related agents. Validate each step of the llmXive pipeline; examine the inputs and outputs produced by any agents related to this phase; use REAL projects as inputs. Currently we're using projects 261 and 262 as ideal for carrying forward into this next phase."

## Background

Phase 3 of the llmXive agentic pipeline (tracked in [#47](https://github.com/ContextLab/llmXive/issues/47), umbrella [#107](https://github.com/ContextLab/llmXive/issues/107)) covers the **Spec Kit Specify → Clarify** transition. Two agents participate:

- **`specifier`** ([#64](https://github.com/ContextLab/llmXive/issues/64)) — drives `/speckit.specify`; takes a project at stage `project_initialized` and produces `projects/<PROJ-ID>/specs/<n>-<slug>/spec.md` with `FR-NNN`, `SC-NNN`, and User Scenarios sections. Advances the project to stage `specified`.
- **`clarifier`** ([#63](https://github.com/ContextLab/llmXive/issues/63)) — drives `/speckit.clarify`; takes a project at stage `specified` and resolves every `[NEEDS CLARIFICATION: …]` marker in `spec.md` in-place. Advances the project to stage `clarified`.

The validation must use **real projects** — `PROJ-261-evaluating-the-impact-of-code-duplicatio` (Computer Science) and `PROJ-262-predicting-molecular-dipole-moments-with` (Chemistry), both currently parked at `project_initialized` after passing Phase 2 cleanly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Run the full Phase 3 pipeline on a single fresh real project (Priority: P1)

A maintainer wants to know whether Phase 3 works end-to-end on a single real project they choose. They invoke the pipeline runner against `PROJ-261` (or `PROJ-262`), specifying a `--max-tasks 2` budget (one for each phase-3 agent). The runner picks the project, runs the Specifier, then the Clarifier, and reports `clarified` as the final stage. All artifacts (spec.md, the project's state YAML, run-log entries) are inspectable side-effects on disk.

**Why this priority**: This is the smallest end-to-end smoke test that proves Phase 3 is not silently broken. It is also the only test that can run cheaply on demand (two LLM calls) and the only one that surfaces integration bugs between Specifier and Clarifier (e.g., the Clarifier failing to parse spec.md that the Specifier just wrote).

**Independent Test**: Can be fully validated by `python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio --max-tasks 2` and confirming the project state transitions to `clarified` with a non-template `spec.md` that has zero `[NEEDS CLARIFICATION]` markers.

**Acceptance Scenarios**:

1. **Given** PROJ-261 at `project_initialized`, **When** the runner is invoked with `--max-tasks 2 --project PROJ-261`, **Then** the project ends at `clarified`, with a `spec.md` written under `projects/PROJ-261-…/specs/001-…/spec.md` containing real Functional Requirements (`FR-001`+), real Success Criteria (`SC-001`+), real User Scenarios, and zero `[NEEDS CLARIFICATION]` markers.
2. **Given** PROJ-262 at `project_initialized`, **When** the same runner invocation is repeated for PROJ-262, **Then** PROJ-262 also ends at `clarified` with a substantively different `spec.md` reflecting its chemistry domain (Graph Neural Networks for molecular dipoles).
3. **Given** a phase-3 run completes (success OR failure), **When** the maintainer reads `state/run-log/YYYY-MM/<run-id>.jsonl`, **Then** every Specifier and Clarifier invocation appears with `started_at`, `ended_at`, `outcome`, and (on failure) `error` or `human_input_needed` fields.

### User Story 2 — Inspect inputs + outputs at every Phase 3 step (Priority: P1)

A maintainer auditing the pipeline wants to see exactly what each Phase 3 agent received as input and what it produced as output, on each of the two reference projects. They run an instrumented dry / inspect variant that captures the prompt the agent received, the LLM response, and the diff applied to the project state. Each agent invocation produces a structured inspection record under `specs/011-phase3-specify-clarify-testing/inspections/<project_id>/<agent>.json`.

**Why this priority**: The user's explicit ask is "examine the inputs and outputs produced by any agents related to this phase". Without capturable I/O records, a green pipeline can still be silently wrong (e.g., the Clarifier replaces clarification markers with text that quotes the question instead of answering it — a known past failure mode). The inspection records make the validation reproducible and reviewable without re-running the LLM.

**Independent Test**: Can be fully validated by running the Phase 3 pipeline for PROJ-261 and PROJ-262, then opening the four resulting inspection records (Specifier+Clarifier × 2 projects) and confirming each one contains: (a) the system+user prompt verbatim, (b) the LLM raw response, (c) the parsed/structured output applied to the project, (d) before/after file diffs for every file modified.

**Acceptance Scenarios**:

1. **Given** PROJ-261 completes Phase 3, **When** the inspection record at `specs/011-…/inspections/PROJ-261/specifier.json` is opened, **Then** it contains the full prompt the Specifier sent to the LLM, the full LLM response, and the resulting `spec.md` content (or a diff vs the prior state).
2. **Given** the same project completes the Clarifier step, **When** the corresponding `clarifier.json` is opened, **Then** it lists every `[NEEDS CLARIFICATION: …]` marker that was present, the answer text the Clarifier produced for each, and a before/after diff of `spec.md`.
3. **Given** both PROJ-261 and PROJ-262 finish, **When** the maintainer compares the two pairs of inspection records, **Then** the prompts visibly differ in their `# Idea Markdown` section (PROJ-261's code-duplication idea vs PROJ-262's GNN-dipole idea) AND the recently-recompiled paper PDFs / personality-comment context (if any) appear in the user prompt as intended.

### User Story 3 — Quality gates that catch silent shortcuts (Priority: P1)

The pipeline must refuse to mark phase-3 stages complete when the agents have produced template-only or evasive output. Specifically: a `spec.md` that is byte-equal (modulo trivial whitespace) to the project's `.specify/templates/spec-template.md` must be rejected; a Clarifier run that "resolves" a `[NEEDS CLARIFICATION]` marker by repeating the question as the answer (or with text like "TBD", "see plan.md", or any sub-string of the marker's question) must be rejected. In every rejection case, the agent's outcome is `failed` (run-log) and the project state HOLDS at the prior stage (no false advance).

**Why this priority**: Spec 010 (#9 acceptance criterion) and the Phase 3 issue's acceptance criterion both call this out as the dominant failure mode of earlier passes. Without these gates, the pipeline silently produces unusable artifacts and the maintainer only discovers the rot during paper compile or review.

**Independent Test**: Can be fully validated by (a) confirming the project at `clarified` is genuinely past both gates on the reference projects, (b) running a targeted unit test that injects a synthetic "template-only spec" or "echo-the-question clarification" response and asserts the pipeline returns `failed` + the stage doesn't advance.

**Acceptance Scenarios**:

1. **Given** the Specifier returns content that is structurally identical to the template (e.g., still has `**FR-001**: System MUST [specific capability, …]` placeholder), **When** `write_artifacts` runs, **Then** the file is deleted, the outcome is `failed`, the project stays at `project_initialized`, and the run-log records an actionable error message.
2. **Given** the Clarifier returns a patch whose `replacement` field is identical to the question text (or starts with "TBD" / "see "), **When** `write_artifacts` runs, **Then** the marker is left in place, the outcome is `failed`, the project stays at `specified`, and the run-log records which marker(s) were rejected.
3. **Given** any agent in Phase 3 raises an unhandled exception, **When** the runner catches it, **Then** the project state is HELD at the prior stage (not advanced) and the run-log records the exception type + message.

### User Story 4 — Carry-forward checklist for downstream phases (Priority: P2)

After Phase 3 validation is complete on both reference projects, a `carry-forward.yaml` file lists the project IDs and exact stage they are parked at, ready for Phase 4 (Plan → Tasks) testing. The file follows the same shape as `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`.

**Why this priority**: The user's direction (paraphrased): "we're using projects 261 and 262 as ideal for carrying forward into this next phase". Phase 3 must explicitly hand them to Phase 4 in the same canonical, machine-readable way the prior phases used.

**Independent Test**: Can be fully validated by opening `specs/011-…/carry-forward.yaml` after Phase 3 completes and confirming both projects appear with stage `clarified` (or `human_input_needed` with a documented reason — the file MUST distinguish).

**Acceptance Scenarios**:

1. **Given** PROJ-261 and PROJ-262 successfully reach `clarified`, **When** `carry-forward.yaml` is generated, **Then** both project IDs appear under a `passed` (or equivalent) key with stage `clarified`.
2. **Given** one project fails Phase 3, **When** `carry-forward.yaml` is generated, **Then** the failing project appears under a `failed` (or `held`) key with the stage it stopped at and a one-line reason.

### Edge Cases

- **Idea has no clarification-worthy ambiguity.** Some ideas are concrete enough that the Specifier produces zero `[NEEDS CLARIFICATION]` markers. The Clarifier MUST detect this and advance straight from `specified` to `clarified` without making an LLM call (and the run-log MUST record a `no-op` outcome rather than `failed`).
- **Clarifier produces more patches than there are markers.** Past failure mode — the LLM hallucinates extra patches for markers that don't exist. The Clarifier MUST drop unmatched patches and log a warning; it MUST NOT silently insert hallucinated content into `spec.md`.
- **The Specifier's underlying `create-new-feature.sh` script fails or returns no JSON.** The script is a project-local shell script; if it crashes, the Specifier MUST surface the crash (not bury it) and HOLD the project at `project_initialized` with an actionable error.
- **The Specifier's response contains a unified-diff prefix** (`--- a/spec.md\n+++ b/spec.md\n@@ …`). Past failure mode — 8 production files were corrupted before this was caught. The diff-guard MUST already reject this; the validation must include a regression test that asserts the guard is still active.
- **Phase 3 is invoked on a project NOT at `project_initialized`** (e.g., already at `clarified`). The runner MUST decline to re-run and either no-op cleanly or report the project as "already past this phase".
- **Concurrent invocations on the same project.** Phase 3 acquires the project lock for the duration of each agent. A second runner trying the same project MUST block (or skip) — never produce a torn write to `spec.md`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The validation MUST be runnable end-to-end with a single command per project, with no manual steps between Specifier and Clarifier.
- **FR-002**: PROJ-261 and PROJ-262 (current stage: `project_initialized`) MUST be the canonical real-project inputs; any future re-run MUST be reproducible from those same starting states.
- **FR-003**: For each agent invocation, the validation MUST capture and persist an inspection record containing: system prompt, user prompt, raw LLM response, parsed output, and a unified diff of every file the agent wrote.
- **FR-004**: Inspection records MUST be written under `specs/011-phase3-specify-clarify-testing/inspections/<project_id>/<agent>.json` and MUST be commit-safe (no secrets, no API keys, no full credentials — only model id + truncated request id).
- **FR-005**: The Specifier MUST produce a `spec.md` with at minimum one `FR-001` line, one `SC-001` line, and a non-template `## User Scenarios` section. Empty/template output MUST be rejected (see FR-008).
- **FR-006**: The Specifier MUST cap `[NEEDS CLARIFICATION]` markers at 3 (per the speckit-specify skill's stated policy); if the LLM produces more, the validation MUST flag this in the inspection record but MUST NOT silently drop markers.
- **FR-007**: The Clarifier MUST resolve every `[NEEDS CLARIFICATION]` marker in `spec.md`. Zero unresolved markers MUST remain after success.
- **FR-008**: When either agent's output classifies as TEMPLATE (per `_real_only_guard.assert_real_or_raise`), the artifact MUST be deleted, the outcome MUST be `failed`, the project stage MUST NOT advance, and the run-log MUST record the rejection reason.
- **FR-009**: When the Clarifier's replacement for a marker is identical to (or a sub-string of) the marker's question text, the replacement MUST be rejected and the marker MUST stay in place. The outcome MUST be `failed` (so the next tick can retry) — NOT `committed` with a fake resolution.
- **FR-010**: Every agent invocation MUST appear in the per-run JSONL run-log with: `agent`, `project_id`, `started_at`, `ended_at`, `outcome ∈ {committed, abstained, failed, held, no-op}`, `error` (if any). No silent advancements.
- **FR-011**: After Phase 3 completes, a `carry-forward.yaml` MUST be generated under the spec directory listing each reference project, its final stage, and (on failure) a one-line reason. Format MUST match the precedent set in `specs/004-…/carry-forward.yaml`.
- **FR-012**: The validation MUST include regression unit tests for: (a) the diff-leak guard (spec 010's bug — `\\---\\n\\+\\+\\+` leak), (b) the template-rejection guard, (c) the echo-the-question clarifier guard. These tests MUST live under `tests/integration/test_phase3_specify_clarify.py` and MUST run as part of the standard unit-test pass.
- **FR-013**: The validation MUST NOT require any code changes to the Specifier or Clarifier agent classes themselves UNLESS a real bug is found; in that case, the bug fix MUST be a separate, justified commit and MUST cite the failing inspection record by path.
- **FR-014**: Per-agent wall-clock budget MUST be enforced at 600 seconds (the `wall_clock_budget_seconds` value from the registry); a timeout MUST classify as `failed`, NOT `committed`.

### Key Entities

- **Reference Project**: A real project ID + slug at a known starting stage. Used as the input to a phase-validation run. PROJ-261 and PROJ-262 are the Phase 3 reference projects.
- **Inspection Record**: A JSON file capturing the verbatim prompts, raw response, parsed output, and file diff produced by a single agent invocation. Lives under the spec directory; one per `(project, agent)` pair.
- **Carry-forward Manifest**: A YAML file listing each reference project, the stage it ended at after this phase, and whether it `passed`, `failed`, or was `held` for human input. Hands the projects off to the next phase's validation.
- **Run-log Entry**: An existing pipeline concept — one JSONL line per agent invocation under `state/run-log/YYYY-MM/<run-id>.jsonl`. Phase 3 validation reads these (does not modify the format).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both PROJ-261 and PROJ-262 reach stage `clarified` within a single phase-3 run (≤ 2 LLM calls per project = 4 total) with NO human intervention.
- **SC-002**: Every `spec.md` produced by Phase 3 contains at least 4 `FR-NNN` lines, at least 3 `SC-NNN` lines, and at least 2 user stories with explicit priority labels — verified by automated check, not manual reading.
- **SC-003**: Zero `[NEEDS CLARIFICATION]` markers remain in either project's `spec.md` after Phase 3 completes successfully.
- **SC-004**: 100% of agent invocations in the run produce an inspection record on disk. If any are missing, the validation FAILS.
- **SC-005**: At least one regression unit test exists for each of the three known historical bug classes (diff-leak, template-only, echo-the-question), and all three tests pass.
- **SC-006**: A maintainer with no prior context can read `specs/011-…/inspections/PROJ-261/specifier.json` and reconstruct what the Specifier was asked + what it returned, without consulting any other file.
- **SC-007**: The carry-forward manifest correctly identifies both projects as `passed` (or accurately reports any failure), with the recorded final stages matching the on-disk state YAMLs.
- **SC-008**: The validation surfaces (in a phase report) any silently-broken behavior caught — e.g., if the Clarifier produces extra patches for nonexistent markers, the phase report calls this out by inspection-record path.

## Assumptions

- **Dartmouth Chat backend is reachable.** PROJ-261 and PROJ-262 will be processed by whatever model the `specifier` and `clarifier` registry entries name as their default backend. If the backend is down, the run is expected to `fail` cleanly (per FR-014) — the validation does not retry indefinitely.
- **The `.specify/scripts/bash/create-new-feature.sh` script in each project's `.specify/` directory works.** Phase 2 (project bootstrap) is the upstream contract that puts this script in place; if it's missing for PROJ-261 or PROJ-262, that's a Phase 2 regression — Phase 3 surfaces but does not fix it.
- **Recently-merged PR #183 + #184 fixes are on `main`.** Those PRs touched `extract_paper_content.py` and `submission_intake.py`, but did NOT modify the Specifier or Clarifier classes — Phase 3 should be unaffected. The validation will confirm this assumption by running cleanly.
- **15-persona pool is current.** PR #185 added 7 new personalities. The `_comments_context.render_recent_comments_block` helper that injects personality comments into the Specifier/Clarifier prompts will reach into PROJ-261's and PROJ-262's `reviews/research/*.md` directories (currently empty for both). This is expected — the comments block will be empty, which the prompts handle.
- **`state/projects/PROJ-26[12]-*.yaml` files are NOT modified by anything else during the validation.** The runner holds the project lock for the duration, so concurrent cron ticks must defer.
- **`agents/registry.yaml`'s `specifier` and `clarifier` entries reflect the deployed prompts and budgets.** Phase 3 reads these and uses them; it does not patch them.
