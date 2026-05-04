# Feature Specification: Phase 1 (Idea Lifecycle) End-to-End Testing & Diagnostics

**Feature Branch**: `003-phase1-idea-lifecycle-testing`
**Created**: 2026-05-04
**Status**: Draft
**Input**: User description: "work through issue 45 and all sub-issues. Comprehensive testing of pipeline step 1 (Idea Lifecycle): run each agent in sequence, examine outputs critically, produce a comprehensive report quoting artifacts verbatim with critical evaluation of issues, then use the report to identify and fix issues. Run agents ONE AT A TIME (no parallelism), use REAL API CALLS following the actual pipeline code. Part of larger pipeline diagnostic tracked in issue 107."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sequential agent execution with real API calls (Priority: P1)

A pipeline maintainer needs to verify that Phase 1 agents (`brainstorm` → `flesh_out` → `idea_selector`) work correctly when invoked through the actual production code path against real LLM backends. They run each agent on a fresh test project in the same sequential order the orchestrator would use, capturing every artifact written, every state transition, and every run-log entry. No mocks, no fakes, no skipping steps.

**Why this priority**: This is the foundational diagnostic. Without a faithful replay of the production sequence using real backends, every later test result is suspect. Running the agents one-at-a-time mirrors the orchestrator's actual behavior, which is single-task-per-invocation under cron, and surfaces interactions between agents that batch testing would hide.

**Independent Test**: Can be fully tested by initializing a fresh project at stage `brainstormed` (no Spec Kit scaffold yet, just a starter `state/projects/<PROJ-ID>.yaml`), invoking the orchestrator with `--max-tasks 1` three times in succession, and verifying after each invocation that exactly one stage advanced, exactly one agent ran, and exactly one run-log entry was appended.

**Acceptance Scenarios**:

1. **Given** a fresh test project at `current_stage: brainstormed` with no `idea/` directory, **When** the orchestrator is invoked with `--max-tasks 1`, **Then** the `brainstorm` agent runs against a real backend, writes `projects/<PROJ-ID>/idea/seed.md` with non-empty title/field/idea, advances state to `flesh_out_in_progress` (or `flesh_out_complete` if seed-only is sufficient), and appends one run-log entry recording outcome, started_at, ended_at.
2. **Given** a project at `current_stage: flesh_out_in_progress` with a valid `seed.md`, **When** the orchestrator is invoked with `--max-tasks 1`, **Then** the `flesh_out` agent runs, writes `projects/<PROJ-ID>/idea/idea.md` containing motivation/prior-work/hypothesis/evaluation-plan, every prior-work claim has at least one citation with a resolvable identifier (DOI/arXiv ID/HTTPS URL), and state advances to `flesh_out_complete`.
3. **Given** a project at `current_stage: flesh_out_complete` with a valid `idea.md`, **When** the orchestrator is invoked with `--max-tasks 1`, **Then** the `idea_selector` agent runs and either advances state to `project_initialized` (promoted) with a written rationale, or rolls state back to `brainstormed` (rejected) with a `failure_reason` recorded in the run-log entry.

---

### User Story 2 - Verbatim artifact capture and critical evaluation report (Priority: P1)

The same maintainer needs a permanent diagnostic record they can hand to a reviewer (or future-self) that quotes every artifact produced — `seed.md`, `idea.md`, the run-log JSONL entries, the state YAML before/after — verbatim, and critiques each one against the agent's stated acceptance criteria from the GitHub issues. The report must distinguish three categories: what works well, what needs improvement, what's outright broken.

**Why this priority**: A bare "tests pass" or "tests fail" verdict is useless for a diagnostic this sprawling. The point of issue 107's tracker is to surface latent quality issues that wouldn't show up in a green-light pass — vague prompts, hallucinated citations, silent stage-advancement on empty content, registry/prompt mismatches, schema drift. Verbatim quotes plus side-by-side critique is the only format that catches these.

**Independent Test**: Can be tested by reading the report and confirming each artifact appears in a fenced quote block, each quote is followed by an evaluation paragraph that references the relevant acceptance criterion verbatim from the corresponding GitHub issue (#59/#60/#61), and that issues identified are categorized into "well", "needs improvement", or "broken" tiers with severity tags.

**Acceptance Scenarios**:

1. **Given** all three Phase 1 agents have run, **When** the report is generated, **Then** every file written under `projects/<PROJ-ID>/idea/` is quoted in full (or — if >100 lines — quoted with explicit `[truncated lines N-M]` markers and content hash), every run-log entry is quoted verbatim as JSON, and the state YAML is quoted before/after each stage transition.
2. **Given** the report is generated, **When** a reviewer reads it, **Then** each artifact has an evaluation paragraph that explicitly cites the relevant acceptance-criteria checkbox from issue #59/#60/#61 and marks it pass/fail with rationale.
3. **Given** the report identifies issues, **When** the issues are summarized, **Then** they are bucketed into "well" / "needs improvement" / "broken" with severity (CRITICAL/HIGH/MEDIUM/LOW), and each issue names a specific file and line where the fix should land.

---

### User Story 3 - Defects identified in the report are fixed and re-verified (Priority: P2)

Once the report names specific defects with severity and file/line pointers, the maintainer fixes them — either prompt edits, code patches in `src/llmxive/agents/`, schema fixes, or registry adjustments — and re-runs the affected agent against a freshly-reset project to confirm the issue is gone.

**Why this priority**: Diagnostics that don't lead to fixes are deadweight. But the spec separates this from US1/US2 because (a) some report findings may be intentional / out-of-scope and only get filed as follow-up issues rather than fixed in this PR, and (b) a maintainer should be able to ship the report alone if the fixes turn out to be larger than expected. Fixing is therefore P2, not P1.

**Independent Test**: For each defect categorized "broken" or "HIGH" in the report, verify that a code/prompt/registry change exists addressing it, and that re-running the relevant agent against a fresh project no longer reproduces the defect (captured in a follow-up "after fix" report section).

**Acceptance Scenarios**:

1. **Given** a CRITICAL or HIGH defect is identified, **When** a fix is applied, **Then** the report's "After fix" section captures the same agent run on a fresh project and shows the defect resolved (or explicitly documents that the fix is deferred to a follow-up issue with rationale).
2. **Given** a fix is applied to a prompt in `agents/prompts/<agent>.md`, **When** the agent is re-run, **Then** the new artifact's quoted content shows the corrected behavior, and the report's "After fix" section quotes the diff between before and after.
3. **Given** a fix touches code in `src/llmxive/`, **When** the fix is committed, **Then** the commit message references the relevant issue (#59/#60/#61) and the report section that motivated it.

---

### Edge Cases

- **Backend unreachable**: What happens when Dartmouth Chat is down or rate-limited mid-test? The test must distinguish "agent failed because backend unreachable" (legitimate transient failure → report it but don't conclude the agent is buggy) from "agent failed because of a code bug" (must surface as CRITICAL).
- **Empty / placeholder artifacts**: What if `brainstorm` writes an empty `seed.md` or `flesh_out` writes `idea.md` with `[NEEDS CLARIFICATION]` placeholders left in place? Per the agent-native rule from issue #45, an agent that can't do its job must fail loudly (write `human_input_needed.yaml` or emit `verdict: failed`), not write a stub and mark the task complete.
- **Hallucinated citations**: Per issue #60's acceptance criteria, every prior-work claim must cite a resolvable identifier. The test plan must spot-check at least one citation per `idea.md` by actually fetching it.
- **Idempotency**: What if the orchestrator is invoked a second time on the same `current_stage`? Does it re-run the agent (clobbering the prior artifact), no-op, or fail loudly? The test must establish current behavior and check for unintended re-execution.
- **Cross-project contamination**: If the test project's slug collides with an existing project (e.g., `PROJ-024-bayesian-...-dete` vs `...-detect`), can the test still run cleanly? Must verify the test fixture creates a fresh slug.
- **Run-log gaps**: If an agent crashes (uncaught exception), is the run-log entry still appended with `outcome: failure`? Or is it silently lost? The test must induce at least one failure (e.g., by pointing the backend at an invalid URL) and confirm the failure is logged.
- **Verbatim quoting size cap**: If `idea.md` is several thousand words, blanket verbatim quoting may make the report unreadable. The test must establish a sensible cap (e.g., 100 lines) with content-hash + truncation markers above that.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run Phase 1 agents (`brainstorm`, `flesh_out`, `idea_selector`) one-at-a-time, in the same sequence the production orchestrator uses, on a single test project that begins at stage `brainstormed`.
- **FR-002**: System MUST use the production code path (`python -m llmxive run --project <PROJ-ID> --max-tasks 1`) for every agent invocation — no direct calls to agent classes, no test-only entry points, no mocked LLM backends.
- **FR-003**: System MUST issue real API calls against the configured backend (Dartmouth Chat by default per the project's existing setup) and gracefully distinguish backend-side failures (`TransientBackendError`, HTTP 5xx, timeout) from agent-side defects.
- **FR-004**: System MUST capture every artifact written by each agent — `seed.md`, `idea.md`, any `human_input_needed.yaml`, any `scope_rejected.yaml` — verbatim into the diagnostic report.
- **FR-005**: System MUST capture the project state YAML and the run-log JSONL entry before and after every agent invocation, quoted verbatim in the diagnostic report.
- **FR-006**: System MUST evaluate every artifact against the acceptance-criteria checkboxes from the relevant GitHub issues (#59 brainstorm, #60 flesh_out, #61 idea_selector), marking each criterion pass/fail with rationale referenced to specific quoted content.
- **FR-007**: System MUST verify at least one prior-work citation per `idea.md` by attempting to resolve it (HTTP HEAD or DOI lookup) and recording the result in the report.
- **FR-008**: System MUST categorize identified issues as "what works well" / "what needs improvement" / "what is broken" with severity tags (CRITICAL / HIGH / MEDIUM / LOW), each tied to a specific file and line where the fix should land.
- **FR-009**: System MUST persist the diagnostic report under `notes/2026-05-04-phase1-diagnostic.md` (or similar dated path), formatted in Markdown with fenced code blocks for every quoted artifact.
- **FR-010**: For each CRITICAL or HIGH defect identified, system MUST either (a) apply a fix in this PR with an "After fix" report section quoting the corrected behavior, or (b) explicitly defer it to a follow-up issue with rationale recorded in the report.
- **FR-011**: System MUST never advance state silently when an agent's content fails its acceptance criteria — if `seed.md` is empty, if `idea.md` lacks resolvable citations, the test must flag this as a CRITICAL defect (an agent shortcut bug analogous to the one already documented for the implementer in `notes/2026-05-04-pipeline-status.md`).
- **FR-012**: System MUST induce at least one deliberate failure mode (e.g., temporarily mis-route the backend, or run on an obviously infeasible field) to verify failure paths produce loud, recorded failures rather than silent state advancement or empty artifacts marked complete.
- **FR-013**: System MUST cap verbatim quotes at a reasonable size (suggested: 100 lines per file) with `[truncated lines N-M, sha256: <hash>]` markers above that, so the report stays human-readable without losing fidelity for fixed-size lookup.
- **FR-014**: System MUST be reproducible — the report names a specific test-project ID, lists every command run, captures backend model + version, and references the exact git commit each agent ran from.
- **FR-015**: All fixes applied as part of this work MUST land as separate commits with messages referencing both the parent issue (#45) and the specific sub-issue (#59/#60/#61) and the report section that motivated the fix.

### Key Entities *(include if feature involves data)*

- **Test project**: A throwaway project (suggested ID: `PROJ-TEST-PHASE1-<timestamp>`) created solely to drive Phase 1. Has its own state YAML and `projects/<id>/` directory. Deleted (or archived under a `tests/fixtures/` path) once the report is finalized.
- **Diagnostic report**: A single Markdown file under `notes/` quoting every artifact verbatim, evaluating each against issue acceptance criteria, and bucketing findings into well/needs-improvement/broken with severity tags and fix pointers.
- **Run-log entries**: One JSONL line per agent invocation under `state/run-log/<YYYY-MM>/<run-id>.jsonl`, with `agent`, `outcome`, `started_at`, `ended_at`, plus `failure_reason` when applicable. Quoted verbatim in the report.
- **Project state**: The `state/projects/<PROJ-ID>.yaml` capturing `current_stage`, `last_run_id`, etc. Quoted before/after each transition.
- **Idea artifacts**: `projects/<PROJ-ID>/idea/seed.md` (from brainstorm) and `projects/<PROJ-ID>/idea/idea.md` (from flesh_out). Optional: `human_input_needed.yaml`, `scope_rejected.yaml`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three Phase 1 agents (`brainstorm`, `flesh_out`, `idea_selector`) run end-to-end against real backends on a fresh test project with no manual intervention beyond the three `--max-tasks 1` invocations, and each produces the artifacts named in its parent issue's acceptance criteria.
- **SC-002**: The diagnostic report quotes at least one verbatim block per artifact written and at least one verbatim block per run-log entry produced, with no agent's output omitted.
- **SC-003**: Every acceptance-criterion checkbox from issues #59, #60, and #61 is explicitly marked pass or fail in the report, with rationale tied to a specific quoted artifact.
- **SC-004**: At least one prior-work citation in `idea.md` is resolved against the live web (or recorded as unreachable with explanation), so hallucinated-citation defects are surfaced rather than glossed.
- **SC-005**: At least one deliberate failure mode is induced and the resulting run-log entry is verified to record `outcome: failure` with a populated `failure_reason`, demonstrating that failure paths are not silent.
- **SC-006**: Every CRITICAL or HIGH defect identified in the report is either fixed in this PR (with an "After fix" report section that re-quotes the corrected behavior) or explicitly deferred with a follow-up issue link and rationale.
- **SC-007**: The report is reproducible — re-running the same commands against a fresh project on the same git commit produces artifacts that fall into the same well/needs-improvement/broken bucket structure (the specific text will differ because of LLM nondeterminism, but the categorization should be stable).

## Assumptions

- The Dartmouth Chat backend (`DARTMOUTH_CHAT_API_KEY`) is reachable for the duration of the test; if it is not, the test will surface that as a transient failure and stop, rather than fall back to a mock.
- The current orchestrator entry point is `python -m llmxive run --project <PROJ-ID> --max-tasks 1` (verified by reading `src/llmxive/__main__.py` / `pyproject.toml` console-scripts before running).
- Phase 1 is fully separable from later phases — the test project will not advance past `project_initialized`, so it does not need a Spec Kit scaffold or a paper-side pass.
- The agents' acceptance criteria as written in issues #59 / #60 / #61 are the authoritative checklist for "is this agent working." If those criteria themselves are wrong (too lax / too strict), the report will note that as a finding rather than rewriting them inline.
- Every artifact under `projects/<test-id>/idea/` is small enough that 100-line verbatim quoting captures it in full; if any artifact exceeds that, truncation with sha256 + line range is acceptable per FR-013.
- Test project artifacts and run-log entries can be committed to the repo so the report is reproducible (test fixture committed under `tests/fixtures/phase1/<test-id>/`); if the user prefers ephemeral, they can request that and the test artifacts will be `.gitignore`d instead.
- The diagnostic report file path will be `notes/2026-05-04-phase1-diagnostic.md` (mirroring the existing `notes/2026-05-04-pipeline-status.md` convention) unless the user prefers a different location.
- This work is sequential to (not blocked by) the implementer task-assertion-enforcer fix described in `notes/2026-05-04-pipeline-status.md` — Phase 1 has no dependency on the implementer, so we can diagnose it now and feed any findings into a parallel track.
