# Feature Specification: Phase 1 (Idea Lifecycle) End-to-End Testing & Diagnostics

**Feature Branch**: `003-phase1-idea-lifecycle-testing`
**Created**: 2026-05-04
**Status**: Draft
**Input**: User description: "work through issue 45 and all sub-issues. Comprehensive testing of pipeline step 1 (Idea Lifecycle): run each agent in sequence, examine outputs critically, produce a comprehensive report quoting artifacts verbatim with critical evaluation of issues, then use the report to identify and fix issues. Run agents ONE AT A TIME (no parallelism), use REAL API CALLS following the actual pipeline code. Part of larger pipeline diagnostic tracked in issue 107."

**Refinement (2026-05-04)**: Test on **real projects** (committed to `projects/`), not throwaway fixtures. Brainstorm produces a pool, we iterate on prompt/code quality until the pool is good, **select 2-3 ideas to carry forward**, then run `flesh_out` on each selected project, iterate on its quality, then run `idea_selector` on each flesh_out output and iterate on its quality. The projects that survive `idea_selector` become the input substrate for the next spec (Phase 2 testing).

## Clarifications

### Session 2026-05-04

- Q: Brainstorm pool-size target and iteration cadence → A: Target 8 seeds with batched iteration (run all 8 first, read them, then apply one prompt patch per cohort and re-run all 8 if needed). One full cohort per iteration cycle.
- Q: Field selection mechanism → A: No external field constraint — brainstorm picks freely. **But** the brainstorm prompt itself MUST encode pipeline-feasibility scope so the agent self-restricts to ideas this pipeline can actually address. Specifically:
  - **Good ideas** (in scope): literature review / research-only projects; ideas the pipeline can simulate locally with run time ≤1 hour; ideas the pipeline can analyze on small-to-medium datasets with analysis time ≤1 hour. Scope must stay focused on **one core question or one core idea**.
  - **Bad ideas** (out of scope): anything requiring external data collection, anything requiring external experimentation (human subjects, lab work, hardware deployment), trivial/uninteresting/non-impactful ideas.
  - The prompt must include enough contextual information about the pipeline's capabilities for the agent to apply this filter unaided.
- Q: Citation resolution mechanism + threshold → A: **Scripted resolver + agent verifier**, two-stage. Stage 1: a script under `tests/phase1/citation_resolver.py` does mechanical checks (HTTP HEAD, DOI lookup, arXiv API) and emits a per-citation JSON record. Stage 2: an agent (e.g., a scientist with web access) reviews any citation the script can't conclusively resolve — redirects, paywalled DOIs, ambiguous titles, HEAD-200 pages that may not contain the claimed paper — and renders a final pass/fail verdict. **100%** of citations per `idea.md` must end the two-stage pipeline as verified. Any citation that fails both stages is a CRITICAL defect that blocks its project from carrying forward.
- Q: Iteration-diff representation → A: Git history is canonical. Each fix-and-re-run cycle is a separate commit on the feature branch. The diagnostic report quotes `git diff <prev-hash> <curr-hash> -- <path>` blocks for every iteration and references the commit hashes (short SHA), so the iteration trail is browsable in GitHub and the report stays compact. No per-iteration shadow files under `tests/phase1/iterations/`.
- Q: Reset-state procedure for re-runs after a prompt/code patch → A: **Branch the iteration trail per project**: each new iteration spawns a new project ID with a suffix like `PROJ-NNN-<slug>-iter2`, `-iter3`, etc. State is never rewound or reset — every iteration is a fresh, independently-replayable run. The "diff between iterations" is a `git diff` between the two project directories' `idea/<slug>.md` files (or the corresponding state YAMLs), per FR-008. Non-promoted iteration projects remain committed alongside their canonical predecessor (kept-for-future or marked archived per FR-019).
- **Filename convention** (from research.md Decision 2): the idea artifact is `projects/<id>/idea/<slug>.md` (slug-named), NOT `idea.md` and NOT a separate `idea/seed.md`. The same file is created by brainstorm and edited in place by flesh_out. Where this spec uses bare `seed.md` or `idea.md` as shorthand, those are *stage-of-content* references to the same physical file: brainstorm's output is the "seed-stage" content; flesh_out rewrites the same file with "expanded" content.
- **Prompt-version semver policy** (per `agents/registry.yaml`'s `prompt_version` field): every prompt patch in this spec's iteration loops MUST bump the affected agent's `prompt_version` according to semver: **MAJOR** for structural rewrites that invalidate the prior output contract; **MINOR** for scope or behavior changes (e.g., adding new in-scope/out-of-scope clauses per FR-003a, adding a new required output section); **PATCH** for prose/typo fixes that don't change behavior. The bump must happen in the same commit as the prompt patch.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Brainstorm pool quality, iterated to a usable bar (Priority: P1)

A pipeline maintainer runs the `brainstorm` agent against the real Dartmouth Chat backend through the production code path (`python -m llmxive run --max-tasks 1`) **8 times in a row** to build a fresh cohort of `PROJ-NNN-<slug>` ideas. They then read all 8 seeds together, evaluate each against the acceptance criteria from issue #59 (non-empty title/field/idea, GHA-feasible, no prior-work claims, under 300s wall-clock) **and the scope filter from FR-003a** (in-scope: literature review / locally-simulable ≤1h / analyzable on small-medium datasets ≤1h, single core question; out-of-scope: external data collection, external experimentation, trivial/non-impactful), and — if defects are identified across the cohort (e.g., several seeds proposing impossible-to-run ideas, or non-impactful ideas) — draft **one** prompt/registry/code patch addressing the most common defect (often: tighten the scope content in `agents/prompts/brainstorm.md`), then re-run a full cohort of 8 to verify the fix. Iteration continues cohort-by-cohort (≤5 cohorts per FR-005) until at least 2-3 seeds in a single cohort clearly meet both the issue #59 bar and the scope filter and can be hand-selected to carry forward.

**Why this priority**: Brainstorm is the entry point for the whole pipeline. Every downstream agent inherits the quality bar that brainstorm sets. If brainstorm produces vague, infeasible, or duplicate-feeling ideas, every later phase wastes compute polishing junk. Getting brainstorm right first — and committing real projects so the iteration is reproducible — is the highest-leverage move in the diagnostic.

**Independent Test**: Can be fully tested by running `python -m llmxive run --max-tasks 1` from a clean working tree, finding the new `projects/PROJ-NNN-<slug>/idea/<slug>.md` file, reading it, and rendering a pass/fail verdict against issue #59's acceptance-criteria checklist. The next iteration of fixes is independently verifiable by re-running and seeing the defect resolved.

**Acceptance Scenarios**:

1. **Given** a fresh `python -m llmxive run --max-tasks 1` invocation with no in-progress projects, **When** the orchestrator picks `brainstorm` as the next task, **Then** a new project directory `projects/PROJ-NNN-<slug>/` is created, `state/projects/<id>.yaml` is initialized at `current_stage: brainstormed` (or `flesh_out_in_progress` if the registry advances on success), `idea/<slug>.md` is written with non-empty title/field/idea, and one run-log entry is appended with `outcome: success`.
2. **Given** the brainstorm pool currently contains `K` seeds (K growing toward target), **When** any new seed fails issue #59's acceptance criteria (e.g., empty content, infeasible scope, prior-work claims), **Then** the failure is recorded in the diagnostic report and a fix is drafted (prompt patch, code patch, or registry change) before the next iteration.
3. **Given** the brainstorm pool contains enough seeds that 2-3 candidates clearly stand above the rest on the criteria from issue #59, **When** the maintainer selects them, **Then** the selection is recorded in `notes/2026-05-04-phase1-diagnostic.md` with rationale, and the non-selected projects are either kept (for future use) or marked archived in their state YAML — never silently deleted.

---

### User Story 2 - Flesh_out runs on each selected project, iterated to a usable bar (Priority: P1)

For each of the 2-3 selected real projects from US1, the maintainer invokes `python -m llmxive run --project <id> --max-tasks 1` with the project at `current_stage: flesh_out_in_progress` (the brainstorm-output stage in the registry). The `flesh_out` agent runs against the real backend and writes `idea/<slug>.md` with motivation, prior work citations, hypothesis, and evaluation plan. The maintainer evaluates `idea.md` against issue #60's acceptance criteria — every prior-work claim has at least one citation with a resolvable identifier (DOI, arXiv ID, HTTPS URL), the hypothesis is testable, the evaluation plan names datasets/metrics that exist, and `scope_rejected.yaml` is emitted on infeasibility. If a defect is identified, the prompt at `agents/prompts/flesh_out.md`, lit_search code, or agent registry is patched, **a sibling project `PROJ-NNN-<slug>-iter2` is spawned** (cloning the seed.md from the original brainstormed project), and `flesh_out` is invoked on the sibling — never reset on the prior iteration's project.

**Why this priority**: `flesh_out` is the gating step where ideas get grounded in real literature. The shortcut bug pattern documented in `notes/2026-05-04-pipeline-status.md` (LLMs writing scripts that exit 0 without doing the work) is most likely to surface here in the form of citations that look real but don't resolve. Catching this on real projects — not on a synthetic fixture — surfaces real failure modes (e.g., stale arXiv IDs, paywalled DOIs, hallucinated author lists) that synthetic ideas wouldn't trigger.

**Independent Test**: Can be tested per-project by running `flesh_out` on one selected project, opening `idea/<slug>.md`, picking each cited identifier, and resolving it (HTTP HEAD on URLs, DOI lookup, arXiv API). Per-project pass/fail is independently verifiable, and the iteration cycle (patch → re-run → re-resolve) repeats until the bar is met.

**Acceptance Scenarios**:

1. **Given** a selected project at `current_stage: flesh_out_in_progress` with a valid `idea/<slug>.md`, **When** the orchestrator is invoked with `--project <id> --max-tasks 1`, **Then** `idea/<slug>.md` is written with the four required sections (motivation, prior work, hypothesis, evaluation plan), state advances to `flesh_out_complete`, and a run-log entry is appended.
2. **Given** `idea/<slug>.md` is generated, **When** every prior-work citation is resolved against the live web, **Then** at least 90% of citations resolve to a real source (the report records resolution results per citation, and any unresolved citation is flagged as a CRITICAL defect that must be fixed before the project can be carried forward).
3. **Given** an iteration has identified a defect (e.g., flesh_out is fabricating citations), **When** the prompt or code is patched and flesh_out is invoked on a sibling project (`PROJ-NNN-<slug>-iter2`) cloned from the same `seed.md`, **Then** the new sibling's `idea.md` is quoted in the diagnostic report alongside a verbatim `git diff <original-iter1>:idea.md <iter2>:idea.md` block, and the previously-failing acceptance criterion is re-checked on the sibling.

---

### User Story 3 - Idea_selector runs on each flesh_out'd project, iterated to a usable bar (Priority: P1)

For each project that survived `flesh_out` quality review, the maintainer invokes `python -m llmxive run --project <id> --max-tasks 1` with the project at `current_stage: flesh_out_complete`. The `idea_selector` agent makes a promote/reject decision and either advances state to `project_initialized` (with rationale recorded) or rolls back to `brainstormed` (with `failure_reason` recorded). The maintainer evaluates the decision and rationale against issue #61's acceptance criteria, including: was the rationale specific (not boilerplate)? Did it actually engage with the project's hypothesis and evaluation plan? Did it correctly reject ideas that flesh_out itself flagged with `scope_rejected.yaml`? If a defect is found, the prompt at `agents/prompts/idea_selector.md` (or agent code) is patched and idea_selector is invoked on a **sibling project** (`PROJ-NNN-<slug>-iterN+1`) — spawned via the standard sibling spawner (which copies only the brainstorm seed and starts the sibling at `current_stage: brainstormed`) and then driven through the orchestrator: the sibling re-runs flesh_out (using the same flesh_out prompt as the iter-1 project, since the iteration under test is for idea_selector), then runs idea_selector under the patched prompt. This is cheaper than copying the canonical's full flesh_out output and gives a fully fresh-replay iteration trail. State surgery on the prior iteration's project is **never** used.

**Why this priority**: `idea_selector` is the gate between Phase 1 and Phase 2. A bad idea_selector either lets junk through (defeating the whole point of the gate) or rejects perfectly good ideas (starving downstream phases). Both failure modes are silent unless a human reads the rationale. Iterating to a bar where rationales are specific and aligned with hypothesis/evaluation is what guarantees the projects we carry forward to spec 004 (Phase 2 testing) are actually worth the compute.

**Independent Test**: Can be tested per-project by inspecting the run-log entry, the rationale text, and the resulting state YAML. The maintainer renders an independent verdict: would I, knowing what's in `idea.md`, have made the same promote/reject call with the same reasoning? Discrepancies between the agent's verdict and a careful human reading are CRITICAL defects.

**Acceptance Scenarios**:

1. **Given** a project at `current_stage: flesh_out_complete` with a quality `idea/<slug>.md`, **When** idea_selector runs, **Then** state advances to `project_initialized` (promote) or rolls back to `brainstormed` (reject), the run-log records the decision, and a rationale is written somewhere agent-visible (e.g., as a YAML key in the state, or as `idea/selection_decision.md`) — not just thrown away.
2. **Given** idea_selector rejects a project, **When** the rationale is read, **Then** it cites a specific concern in `idea.md` (not boilerplate like "the idea is not novel"), and a human reader can either agree or articulate why it's wrong.
3. **Given** the iteration loop has produced 2-3 projects whose idea_selector verdicts the maintainer endorses, **When** they are recorded in the diagnostic report as "carried forward to Phase 2 testing", **Then** their state YAMLs are at `project_initialized`, their `projects/<id>/` directories are committed, and a follow-up note in the report names them as the input substrate for the next spec.

---

### User Story 4 - Verbatim artifact capture and critical evaluation report (Priority: P1)

Throughout US1-US3, the maintainer maintains a single diagnostic report that quotes every artifact verbatim — every `seed.md`, every `idea.md`, every state YAML before/after each transition, every run-log JSONL entry, every promote/reject rationale — and critiques each one against the corresponding GitHub-issue acceptance criteria. The report distinguishes "what works well" / "what needs improvement" / "what's broken" with severity tags, and for every CRITICAL or HIGH defect either captures the fix-and-re-run loop in an "After fix" subsection or explicitly defers it to a follow-up issue with rationale.

**Why this priority**: A bare "tests pass" or "tests fail" verdict is useless for a diagnostic this multi-agent. Verbatim quotes plus side-by-side critique are the only format that catches latent quality issues — vague prompts, hallucinated citations, silent stage-advancement on empty content, registry/prompt mismatches, schema drift. The report doubles as the source-of-truth for which projects are eligible to carry forward and as a permanent diagnostic record handed to issue #107.

**Independent Test**: Can be tested by reading the report and confirming each artifact appears in a fenced code block, each quote is followed by an evaluation paragraph that explicitly cites the relevant acceptance-criterion checkbox from issue #59/#60/#61 with pass/fail and rationale, and that issues identified are categorized into well/needs-improvement/broken tiers with severity (CRITICAL/HIGH/MEDIUM/LOW) and a fix pointer (file:line).

**Acceptance Scenarios**:

1. **Given** all three Phase 1 agents have run on at least 2 projects, **When** the report is generated, **Then** every file written under any committed `projects/<id>/idea/` is quoted in full (or — if >100 lines — quoted with explicit `[truncated lines N-M, sha256: <hash>]` markers), every relevant run-log entry is quoted verbatim as JSON, and the state YAML is quoted before/after each stage transition.
2. **Given** the report is generated, **When** a reviewer reads it, **Then** each artifact has an evaluation paragraph that explicitly cites the relevant acceptance-criteria checkbox from issue #59/#60/#61 and marks it pass/fail with rationale.
3. **Given** the report identifies issues, **When** the issues are summarized, **Then** they are bucketed into "well" / "needs improvement" / "broken" with severity, each names a specific file and line where the fix should land, and CRITICAL/HIGH defects either link to an "After fix" section in the report or to a follow-up GitHub issue.

---

### User Story 5 - Carrying-forward gate: 2-3 projects are tagged for Phase 2 testing (Priority: P2)

Once the iteration loops in US1-US3 have produced enough quality, the maintainer formally selects the 2-3 projects that will be the input substrate for spec 004 (Phase 2 — Project Bootstrap) and beyond. The selection is recorded in the diagnostic report and in a small structured file (e.g., `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`) that names each carried-forward project ID, the agents that ran on it, the final-iteration commit hash, and a one-paragraph justification. Future specs reference this file to know which projects to operate on, ensuring continuity of the substrate across the diagnostic chain.

**Why this priority**: Without this gate, "carry forward" is folklore — every future spec has to re-discover the substrate. With this gate, spec 004 starts with `cat specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` and knows exactly which `projects/PROJ-NNN-*` to operate on. P2 because it's the bridge to the next spec, not a self-contained capability.

**Independent Test**: Can be tested by reading `carry-forward.yaml`, confirming each named project ID corresponds to a real `projects/<id>/` directory at `current_stage: project_initialized`, and confirming the named commit hashes match the last touch of those project directories.

**Acceptance Scenarios**:

1. **Given** the iteration loops have completed, **When** `carry-forward.yaml` is written, **Then** it names 2-3 project IDs, each with: final state, final commit hash, justification, and a list of which Phase 1 agents ran on it (with how many iterations each).
2. **Given** spec 004 (or any later phase-test spec) starts work, **When** it reads `carry-forward.yaml`, **Then** it can pick any of those project IDs and find the project directory, state YAML, and idea artifacts in the expected committed state.

---

### Edge Cases

- **Backend unreachable**: What happens when Dartmouth Chat is down or rate-limited mid-iteration? The diagnostic must distinguish "agent failed because backend unreachable" (legitimate transient → log it, retry the run, do not patch the agent) from "agent failed because of a code bug" (CRITICAL defect, surface in report).
- **Empty / placeholder artifacts**: If `brainstorm` writes an empty `seed.md` or `flesh_out` writes `idea.md` with `[NEEDS CLARIFICATION]` placeholders left in place, per the agent-native rule from issue #45 the agent must fail loudly (write `human_input_needed.yaml` or emit `verdict: failed`), not write a stub and mark the task complete. The report must flag any silent stage-advancement on empty content as CRITICAL.
- **Hallucinated citations**: Per issue #60's acceptance criteria, every prior-work claim must cite a resolvable identifier. The diagnostic must spot-check at least 90% of citations per `idea.md` by actually fetching them.
- **Iteration via project branching, not state reset**: After a prompt/code patch, the next iteration spawns a **new project** with a suffixed ID (e.g., `PROJ-NNN-<slug>-iter2`); the prior project's state is never rewound. This sidesteps state-machine surgery entirely and makes every iteration independently replayable. The diff between iterations is a `git diff` between the two project directories' artifacts, per FR-008.
- **Iteration unbounded loop**: If a defect is fixed but the next iteration introduces a new defect, the iteration count can balloon. The diagnostic must cap iterations per agent (suggested: 5 fix-and-re-run cycles per agent before the maintainer decides "good enough" or "deferred to follow-up issue").
- **Out-of-scope idea generated by brainstorm**: If a seed proposes external data collection, external experimentation, or a trivial idea, that's a defect *in the brainstorm prompt's scope encoding* (FR-003a) and must drive a prompt patch in the next cohort — not a "throw the seed away" decision. The diagnostic report must record which prompt-content tweaks improved scope adherence cohort-over-cohort.
- **Selecting from too small a pool**: If brainstorm hasn't produced enough quality seeds for 2-3 to obviously stand out, the diagnostic must allow continuing to grow the pool (more brainstorm runs) rather than forcing selection from a weak pool.
- **Cross-iteration contamination**: When `flesh_out` is re-run after a patch, the new artifact replaces the old. The report must capture the **diff** between iterations (not just the final state) so the fix's effect is visible.
- **Selected projects fail downstream**: If a project we've carried forward fails Phase 2 testing in spec 004, the report from this spec must remain authoritative for "what Phase 1 thought was good." Spec 004 is responsible for catching Phase 1 quality issues that only surface downstream.
- **Run-log gaps**: If an agent crashes (uncaught exception), the run-log entry must still be appended with `outcome: failure` and a populated `failure_reason`. The diagnostic must induce at least one failure (e.g., point backend at invalid URL) and confirm the failure is logged.
- **Quote size cap**: Verbatim quoting >100 lines per file makes the report unreadable. Cap quotes at 100 lines with `[truncated lines N-M, sha256: <hash>]` markers above that.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run Phase 1 agents (`brainstorm`, `flesh_out`, `idea_selector`) one-at-a-time on **real projects** committed under `projects/PROJ-NNN-<slug>/`, using the production code path (`python -m llmxive run [--project <id>] --max-tasks 1`).
- **FR-002**: System MUST issue real API calls against the configured backend (Dartmouth Chat by default per the project's existing setup) and gracefully distinguish backend-side failures (`TransientBackendError`, HTTP 5xx, timeout) from agent-side defects.
- **FR-003**: System MUST grow a brainstorm pool to a target size of **8 seeds per cohort** by repeated `--max-tasks 1` invocations. Iteration is **batched**: run all 8, read every seed, draft at most one prompt/registry/code patch per cohort, re-run a fresh cohort of 8 if the patch was applied, then advance once at least 2-3 seeds clearly meet issue #59's acceptance criteria. The brainstorm agent picks the field freely (no external `fields.txt`); scope is enforced via prompt content per FR-003a.
- **FR-003a**: The brainstorm prompt at `agents/prompts/brainstorm.md` MUST encode pipeline-feasibility scope, defining (i) **in-scope** idea types — literature review / research-only, locally-simulable with ≤1h run time, analyzable on small-to-medium datasets with ≤1h analysis time, and scoped to one core question/idea; (ii) **out-of-scope** idea types — anything requiring external data collection, external experimentation, or that is trivial/non-impactful; (iii) sufficient contextual information about the pipeline's capabilities for the agent to apply this filter unaided. Iteration on the brainstorm prompt (per FR-005) is the place where this scope content gets refined.
- **FR-004**: System MUST allow iteration on each agent's prompt at `agents/prompts/<agent>.md`, registry entry at `agents/registry.yaml`, or implementation in `src/llmxive/agents/` between agent runs. Each iteration spawns a **new sibling project** with a suffixed ID (`PROJ-NNN-<slug>-iter2`, `-iter3`, …) — state is never rewound or reset on the prior iteration's project. For brainstorm, each cohort of 8 is itself a fresh batch of new projects per FR-003.
- **FR-005**: System MUST cap fix-and-re-run iterations per agent at 5 cycles. **Hitting the cap forces a deferral decision** — once the 5th cycle finishes, the maintainer MUST choose one of two outcomes for the residual defect: (a) "good enough" (accept current state, commit and move on; record `accepted (not addressed)` in the defects table) OR (b) "deferred" (file a follow-up GitHub issue describing the residual defect, link the issue from the defects table, do not block this spec). Continuing past the 5-cycle cap on the same defect is **prohibited** — the cap is non-negotiable to keep the spec converging in finite time.
- **FR-006**: System MUST capture every artifact written by each agent — `seed.md`, `idea.md`, any `human_input_needed.yaml`, any `scope_rejected.yaml`, any `selection_decision.md` — verbatim into the diagnostic report, with cap+hash truncation for files >100 lines.
- **FR-007**: System MUST capture the project state YAML and the run-log JSONL entry before and after every agent invocation, quoted verbatim.
- **FR-008**: System MUST capture the verbatim diff between iterations of the same artifact via **git history** as the canonical source. Each fix-and-re-run cycle MUST be a separate commit on the feature branch, and the diagnostic report MUST quote `git diff <prev-hash> <curr-hash> -- <path>` output verbatim per iteration, referencing the short SHAs so the iteration trail is browsable in GitHub. No shadow `tests/phase1/iterations/` directory is created.
- **FR-009**: System MUST evaluate every artifact against the acceptance-criteria checkboxes from issues #59 (brainstorm), #60 (flesh_out), and #61 (idea_selector), marking each criterion pass/fail with rationale tied to specific quoted content.
- **FR-010**: System MUST verify **100%** of prior-work citations per `idea.md` via a two-stage pipeline. Stage 1: a scripted resolver at `tests/phase1/citation_resolver.py` performs mechanical checks (HTTP HEAD, DOI lookup, arXiv API) and emits a per-citation JSON record. Stage 2: an agent verifier (scientist agent with web access) inspects every citation the script could not conclusively resolve — redirects, paywalls, ambiguous titles, HEAD-200 pages that may not host the claimed paper — and renders a final pass/fail verdict. The diagnostic report MUST quote both stages' outputs verbatim per citation. Any citation that fails both stages is a CRITICAL defect that blocks its project from being carried forward.
- **FR-011**: System MUST categorize identified issues as "what works well" / "what needs improvement" / "what is broken" with severity tags (CRITICAL / HIGH / MEDIUM / LOW), each tied to a specific file and line where the fix should land.
- **FR-012**: System MUST persist the diagnostic report under `notes/2026-05-04-phase1-diagnostic.md` (or similar dated path), formatted in Markdown with fenced code blocks for every quoted artifact.
- **FR-013**: For each CRITICAL or HIGH defect identified, system MUST either (a) apply a fix in this PR with an "After fix" report section quoting the corrected behavior, or (b) explicitly defer to a follow-up GitHub issue with rationale recorded in the report.
- **FR-014**: System MUST never advance state silently when an agent's content fails its acceptance criteria — empty `seed.md`, `idea.md` with unresolved placeholders, or empty/boilerplate selector rationales must be flagged as CRITICAL defects.
- **FR-015**: System MUST induce at least one deliberate failure mode (e.g., temporarily mis-route the backend, or run on an obviously infeasible field) to verify failure paths produce loud, recorded failures rather than silent state advancement or empty artifacts marked complete.
- **FR-016**: System MUST commit all real-project artifacts produced (`projects/PROJ-NNN-*/idea/*`, `state/projects/PROJ-NNN-*.yaml`, `state/run-log/<YYYY-MM>/*.jsonl`) so the report and the carry-forward gate are reproducible.
- **FR-017**: System MUST formally select 2-3 projects to carry forward (those that survive idea_selector with maintainer-endorsed verdicts) and record the selection in `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` with project IDs, final state, final commit hash, and a one-paragraph justification per project.
- **FR-018**: All fixes applied as part of this work MUST land as separate commits with messages referencing both the parent issue (#45) and the specific sub-issue (#59/#60/#61) and the report section that motivated the fix.
- **FR-019**: System MUST allow non-selected projects from the brainstorm pool to remain in `projects/` (kept for future use) or be marked archived by adding an `archived_at: <ISO-8601 UTC>` field to their `state/projects/<id>.yaml` (a separate field, not a `current_stage` enum value — `current_stage` retains its production value so the project can still be re-promoted later if desired). Non-selected projects MUST NOT be silently deleted from `projects/` or `state/projects/`.

### Key Entities *(include if feature involves data)*

- **Real project**: A `PROJ-NNN-<slug>` directory under `projects/` created by an actual brainstorm run. Has its own `state/projects/<id>.yaml`. Committed to the repo. Either selected for carry-forward, kept-for-future, or marked archived — never deleted.
- **Brainstorm pool**: The set of real projects produced by repeated brainstorm runs during US1. Grows until 2-3 clear winners emerge.
- **Selected projects**: 2-3 projects from the pool that pass all three agents' quality bars and become the input substrate for spec 004 (Phase 2 testing).
- **Diagnostic report**: A single Markdown file under `notes/` quoting every artifact verbatim, evaluating each against issue acceptance criteria, capturing iteration diffs, and bucketing findings into well/needs-improvement/broken with severity tags and fix pointers.
- **Carry-forward manifest**: A YAML file at `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` naming the 2-3 selected projects with metadata (final state, commit hash, justification) for reference by future-phase specs.
- **Run-log entries**: One JSONL line per agent invocation under `state/run-log/<YYYY-MM>/<run-id>.jsonl` with `agent`, `outcome`, `started_at`, `ended_at`, plus `failure_reason` when applicable. Quoted verbatim in the report.
- **Project state**: The `state/projects/PROJ-NNN-<slug>.yaml` capturing `current_stage`, `last_run_id`, etc. Quoted before/after each transition.
- **Idea artifacts**: `projects/PROJ-NNN-*/idea/<slug>.md` (from brainstorm), `projects/PROJ-NNN-*/idea/<slug>.md` (from flesh_out). Optional: `human_input_needed.yaml`, `scope_rejected.yaml`, `selection_decision.md`.
- **Iteration diff**: A `git diff` between the same artifact's content across two iterations — typically `git diff <iterN-commit>:projects/<base-id>/idea/<slug>.md <iterN+1-commit>:projects/<base-id>-iter<N+1>/idea/<slug>.md`. Quoted in the report so each fix's effect is visible.
- **Sibling iteration project**: A new project ID with a `-iterN` suffix (e.g., `PROJ-NNN-<slug>-iter2`), spawned to re-run an agent after a prompt/code patch. Its `seed.md` is cloned from the canonical iter1 project so all iterations share the same input. State machinery is never reset on the prior iteration's project; each sibling has its own state YAML and run-log entries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three Phase 1 agents (`brainstorm`, `flesh_out`, `idea_selector`) run end-to-end against the real backend on real committed projects, with zero mock/fake calls and zero direct calls bypassing the production orchestrator entry point.
- **SC-002**: At least 2-3 real projects survive all three agents' quality bars (including the scope filter from FR-003a — pipeline-feasible idea types only) and are recorded in `carry-forward.yaml` with full metadata.
- **SC-003**: The diagnostic report quotes every artifact written and every run-log entry produced — no agent's output omitted.
- **SC-004**: Every acceptance-criterion checkbox from issues #59, #60, and #61 is explicitly marked pass or fail in the report, with rationale tied to a specific quoted artifact (per agent run, per project).
- **SC-005**: **100%** of prior-work citations across all flesh_out outputs that survive into carry-forward are verified by the two-stage pipeline (scripted resolver + agent verifier per FR-010); citations that fail both stages block their project from carrying forward.
- **SC-006**: At least one deliberate failure mode is induced and the resulting run-log entry is verified to record `outcome: failure` with a populated `failure_reason`, demonstrating that failure paths are not silent.
- **SC-007**: For every CRITICAL or HIGH defect identified, either an "After fix" report section quotes the corrected behavior or a follow-up issue link is recorded with rationale — no defect is silently dropped.
- **SC-008**: Iteration is bounded per agent (≤5 fix-and-re-run cycles) so the spec converges in finite time; if the cap is hit without convergence, the agent's open issues are explicitly deferred to follow-up issues rather than blocking the spec.
- **SC-009**: The carry-forward manifest is concrete enough that spec 004 (or any later phase-test spec) can read it and pick up the named projects without re-discovering the substrate.

## Assumptions

- The Dartmouth Chat backend (`DARTMOUTH_CHAT_API_KEY`) is reachable for the duration of the test; if it is not, the test will surface that as a transient failure and stop, rather than fall back to a mock.
- The current orchestrator entry point is `python -m llmxive run [--project <id>] --max-tasks 1` (verified by reading `src/llmxive/__main__.py` and `pyproject.toml` console-scripts before running).
- Agent prompts at `agents/prompts/<agent>.md` and the agent registry at `agents/registry.yaml` are editable as part of the iteration loop; changes ship as part of this PR.
- Real projects produced by brainstorm runs are small (idea artifacts are well under 100 lines each), so committing them is bounded in size.
- Non-selected brainstorm-pool projects can stay in `projects/` indefinitely — they are not deleted as part of this spec. If the user later wants them archived, that's a separate cleanup task.
- The agents' acceptance criteria as written in issues #59/#60/#61 are the authoritative checklist; if they themselves are wrong (too lax / too strict), the report will note that as a finding rather than rewriting them inline.
- The diagnostic report file path will be `notes/2026-05-04-phase1-diagnostic.md` unless the user prefers a different location.
- The carry-forward manifest path is `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`; spec 004 and beyond can reference it.
- This work is sequential to (not blocked by) the implementer task-assertion-enforcer fix described in `notes/2026-05-04-pipeline-status.md` — Phase 1 has no dependency on the implementer.
- A maintainer (human in the loop) makes the final selection of which 2-3 projects carry forward; idea_selector's verdict informs but does not override that judgment, since this spec is also testing whether idea_selector's judgment is trustworthy.
