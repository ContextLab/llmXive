# Feature Specification: Phase 2 (Project Bootstrap) End-to-End Testing & Diagnostics

**Feature Branch**: `008-phase2-project-bootstrap-testing` *(spec dir is `specs/004-phase2-project-bootstrap-testing/` — branch number diverges from spec number per `/speckit-specify` allowance because the git-feature hook counts branches across the repo, not spec dirs)*
**Created**: 2026-05-05
**Status**: In Review
**Input**: User description: "next let's work on phase 2: issue 46 + all sub-issues + any related agents. for context, also see issue 107. critical details and considerations: our goal here is to validate *each step* of the llmXive pipeline; we need to examine the *inputs* and *outputs* produced by any agents related to this phase; use *REAL* projects as inputs. currently we're using projects 261 and 262 as ideal for carrying forward into this next phase."

## Context (carried from spec 003)

This spec is a direct continuation of spec 003 (Phase 1 Idea Lifecycle Testing, closed via PR #108). It uses the carry-forward manifest at `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` as its canonical input substrate. Both named projects already exist on `main` at `current_stage: project_initialized` because spec 003's diagnostic ran the full Phase 1 pipeline (including `project_initializer`) end-to-end on them — the Phase 1 spec's success criterion was "carry-forward at `project_initialized`".

The **current pipeline graph** wires Phase 2 as a single-agent transition: `validated → project_initializer → project_initialized`. The validator (added by spec 003 / D10) sits in Phase 1, so by the time a project enters Phase 2 it has already passed all four research-question-quality checks. Phase 2's only job is to produce the per-project Spec Kit scaffold and the LLM-rendered constitution.

**Implication for this spec**: PROJ-261 and PROJ-262 are already past Phase 2's exit stage on `main` (their `.specify/` scaffolds already exist, with constitutions, templates, and scripts written). This spec therefore tests Phase 2 by spawning **`-iter2` siblings** of each carry-forward project (starting at `current_stage: validated`) using the same sibling-iteration pattern spec 003 introduced (FR-004 of spec 003). State surgery on the canonical PROJ-261/PROJ-262 is never used; each iteration is a fresh, independently replayable run on a new project ID.

## Clarifications

### Session 2026-05-05

- Q: Target iter2 sibling count per canonical project (PROJ-261, PROJ-262) → A: One iter2 sibling per canonical (2 runs total). Independent evidence across both research domains (CS + chemistry) without redundant audits; further iterations only spawn if a defect surfaces.
- Q: Induced-failure scenario choice for US4 → A: All three (backend-unreachable + idea file missing + template file missing). Full failure-path audit — each scenario exercises a distinct precondition that Phase 2 depends on, so a per-scenario verdict gives the most defensible Constitution-Principle-V coverage.
- Q: Idempotency-overwrite policy for LLM constitution re-render on second `project_initializer` invocation → A: Skip-if-exists. The agent MUST detect a pre-existing `.specify/memory/constitution.md` and skip re-rendering (matching the `init_speckit_in` skip-if-dir-exists pattern at `src/llmxive/speckit/runner.py:114`). Re-rendering a governance document silently mutates downstream Constitution Checks — fix `src/llmxive/agents/project_initializer.py:84-102` as part of this PR.
- Q: Transient-backend-error retry budget per agent run → A: 2 retries with exponential backoff (3 total attempts), then `TransientBackendError` → `human_input_needed`. Counted as one cycle against the FR-005 5-cycle iteration cap. Verify the backend client at `src/llmxive/backends/dartmouth.py` implements this; if it doesn't, fix as part of this PR's prerequisite work.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - project_initializer runs cleanly on each carry-forward sibling, audited end-to-end (Priority: P1)

A pipeline maintainer reads `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`, picks each named project (PROJ-261 + PROJ-262), and uses `tests/phase1/sibling_project.py` (the spec-003 sibling spawner) to spawn an `-iter2` sibling per project at `--start-stage validated`. The sibling's `idea/<slug>.md` is byte-for-byte cloned from the canonical (sha256-verified by the spawner), and a fresh `state/projects/<sibling-id>.yaml` is written at `current_stage: validated`. The maintainer then invokes `python -m llmxive run --project <sibling-id> --max-tasks 1` against the real Dartmouth Chat backend. The orchestrator picks `project_initializer` as the next agent (per `STAGE_TO_AGENT[VALIDATED]`). The maintainer captures every input the agent saw (system prompt after token substitution, rendered constitution template, idea body) and every output it produced (`.specify/memory/constitution.md`, plus any artifacts under `.specify/{scripts,templates}/` written by the mechanical `init_speckit_in` step), state YAML before/after, and the run-log JSONL entry. They evaluate each artifact against issue #62's acceptance criteria.

**Why this priority**: This is the entirety of Phase 2. Without this story, nothing in Phase 2 is actually tested. Every other story in this spec depends on at least one successful clean run from this story.

**Independent Test**: Can be fully tested per project by spawning the sibling, running `--max-tasks 1`, opening `projects/<sibling-id>/.specify/memory/constitution.md`, and verifying it (a) starts with `# <title> — Research Project Constitution`, (b) ends with the `**Project ID**: …` footer, (c) names the actual project field (not the literal `{{field}}` token), and (d) adapts at most two domain-specific principles per the prompt's constraint. State must end at `project_initialized`. The run-log must record `outcome: success` with `started_at`/`ended_at`.

**Acceptance Scenarios**:

1. **Given** PROJ-261-iter2 staged at `current_stage: validated` with a verified-clone `idea/evaluating-the-impact-of-code-duplicatio.md`, **When** `python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2 --max-tasks 1` is invoked, **Then** `projects/PROJ-261-…-iter2/.specify/{memory,scripts,templates}/` is created, `memory/constitution.md` is written with project-specific tokens fully substituted (no literal `{{…}}` placeholders survive), state advances to `project_initialized`, and one run-log entry is appended with `outcome: success`.
2. **Given** PROJ-262-iter2 staged identically, **When** the same orchestrator command runs, **Then** the same set of artifacts is produced and the constitution adapts to the chemistry domain (e.g., adds a domain-specific principle around quantum-chemistry validation, molecular-feature reproducibility, or similar — per the prompt's "add at most two domain-specific principles" rule).
3. **Given** either iter2 run completes, **When** the maintainer reads `.specify/memory/constitution.md` and `.specify/templates/`, **Then** `templates/{constitution,plan,spec,tasks,checklist}-template.md` are present and byte-identical to `.specify/templates/*` at the repo root (idempotent mechanical step), AND `scripts/bash/{common,create-new-feature,setup-plan,check-prerequisites}.sh` are present and executable.

---

### User Story 2 - Constitution-quality audit against the system prompt's contract (Priority: P1)

For each iter2 constitution produced in US1, the maintainer audits its content against the explicit output contract in `agents/prompts/project_initializer.md`. The contract requires: (a) literal `# <title> — Research Project Constitution` heading, (b) literal `**Project ID**: …` footer, (c) at most TWO added domain-specific principles (numbered VI/VII), (d) all five inherited principles (I–V) preserved verbatim, (e) no external citations introduced, (f) `Reproducibility Requirements` section adapted to the project's actual data sources. The audit is line-by-line, and any deviation is recorded as a defect with severity (CRITICAL / HIGH / MEDIUM / LOW) per spec-003's defect-categorization convention. The maintainer also confirms the constitution does not contradict or weaken any principle in the parent `.specify/memory/constitution.md` (per the parent-template's explicit instruction in line 13).

**Why this priority**: A constitution that fails its output contract (e.g., LLM dropped Principle V, fabricated a citation, or invented a sixth and seventh principle) breaks every downstream slash command (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`) inside the project, because they read this file to apply Constitution Checks. Phase 2's correctness IS the constitution's correctness — there's nothing else to test.

**Independent Test**: Can be tested per project by reading the produced constitution side-by-side with `agents/templates/research_project_constitution.md`, marking each contractual requirement (a)-(f) pass/fail with the specific text quoted, and verifying no literal `{{token}}` strings survive substitution.

**Acceptance Scenarios**:

1. **Given** PROJ-261-iter2's constitution, **When** the audit runs, **Then** every contract item (a)-(f) is marked pass with a quoted excerpt, OR any failure is recorded as a defect with severity, file:line pointer, and proposed fix.
2. **Given** PROJ-262-iter2's constitution, **When** the audit runs, **Then** the chemistry-specific adaptation in `Reproducibility Requirements` is verified — e.g., it MUST name a real chemistry data source (QM9, MD17, etc., or whichever the idea cites) rather than the generic placeholder language from the template.
3. **Given** either constitution introduces a defect (e.g., dropped a principle, invented a citation, contradicted parent principle II), **When** the defect is identified, **Then** it is logged with severity and either fixed in this PR (per spec 003 FR-013) or deferred to a follow-up issue.

---

### User Story 3 - Idempotency audit on `init_speckit_in` (Priority: P1)

The maintainer re-invokes `init_speckit_in` directly via a small Python harness on a sibling that is *already* at `current_stage: project_initialized` (i.e., immediately after US1's run). The orchestrator-level approach won't work — running `python -m llmxive run --project <sibling-id> --max-tasks 1` from `project_initialized` would advance to Phase 3's `specifier`, not re-run Phase 2 — so direct invocation is the only way to test issue #62's third acceptance criterion: **"Idempotent: running twice doesn't duplicate or corrupt files"**. The maintainer compares the `.specify/{scripts,templates}/` tree's sha256 hashes before and after the second invocation; they must match exactly.

**Why this priority**: Idempotency is one of three explicit acceptance criteria in issue #62. Cron-driven pipelines re-run agents on the same project frequently; a non-idempotent `init_speckit_in` would corrupt the project's own constitution on every re-run, silently invalidating every downstream slash command's behavior.

**Independent Test**: Can be tested by computing `sha256sum projects/<sibling-id>/.specify/{scripts,templates}/**/*` before and after the second invocation and confirming the hash list is identical. If any file's hash changed, the test fails — note that this is a stricter test than "the file still exists" because a re-rendered constitution with different LLM output would still pass a file-existence check while failing idempotency.

**Acceptance Scenarios**:

1. **Given** PROJ-261-iter2 at `project_initialized` with a complete `.specify/` tree, **When** `init_speckit_in` is invoked a second time directly (bypassing the orchestrator's stage-routing), **Then** all template/scripts files are unchanged (sha256 identical) and no exception is raised.
2. **Given** the LLM-rendered constitution at `.specify/memory/constitution.md` exists from US1, **When** the agent itself is re-invoked via a Python harness with the project at `validated` (impossible in production — would require sibling-iter3 — but tested via direct agent invocation), **Then** the agent MUST detect the pre-existing constitution, skip re-rendering, and leave the file byte-for-byte unchanged (sha256 identical before/after). Per Q3 clarification, the current overwrite-unconditional behavior at `src/llmxive/agents/project_initializer.py:84-102` is a HIGH defect; the fix lands in this PR and US3 verifies it.
3. **Given** the idempotency check completes, **When** the diagnostic report is generated, **Then** issue #62's checkbox "Idempotent: running twice doesn't duplicate or corrupt files" is marked pass or fail with the sha256 evidence quoted verbatim.

---

### User Story 4 - Failure-path induction: agent fails loudly when prerequisites are missing (Priority: P2)

The maintainer induces all three deliberate failure modes (per Q2 clarification) to verify Phase 2's failure paths are loud (per spec 003's FR-015 / SC-006 pattern). The three scenarios:

1. **Backend unreachable**: temporarily set `LLMXIVE_BACKEND_BASE_URL` to an invalid host and confirm the run-log records `outcome: failure` with a populated `failure_reason` quoting the backend exception, and that the sibling's state YAML is NOT advanced past `validated`.
2. **Idea file missing**: spawn a sibling-iter3 manually but delete its `idea/<slug>.md` before invoking the orchestrator; confirm the agent fails fast (per llmXive Constitution Principle V) with a clear message rather than producing a constitution that lacks idea-grounding.
3. **Template file missing**: rename `agents/templates/research_project_constitution.md` to a backup name and run the agent; confirm it raises a clear `FileNotFoundError`, not a silent fallback to a generic constitution.

**All three** scenarios MUST be exercised (per Q2 clarification). The diagnostic report quotes, for each scenario independently, the run-log entry, the exception trace (or stderr block), and the post-failure state YAML to prove the failure is recorded and state is not silently advanced. The three failures cover three distinct preconditions Phase 2 depends on (backend reachability, idea-grounding input, constitution-template input) and must each be exercised on their own dedicated sibling iter (e.g., -iter3 for backend-fail, -iter4 for missing idea, -iter5 for missing template) so the failures don't contaminate each other.

**Why this priority**: P2 because it's not the happy path, but the cron-driven pipeline absolutely depends on failures being loud and recorded — silent failure with state advancement is the most damaging bug class in this whole system. P2 (not P1) because spec 003 already exercised induced-failure paths for Phase 1 and we have substantial evidence that the failure recording machinery works generically — Phase 2 only needs a smoke test, not a full audit.

**Independent Test**: Can be tested by running the induced-failure scenario, then reading `state/run-log/<YYYY-MM>/<run-id>.jsonl` and `state/projects/<sibling-id>.yaml`. The run-log entry must have `outcome: failure` with `failure_reason` populated, and the state YAML's `current_stage` must remain at `validated` (not advanced).

**Acceptance Scenarios**:

1. **Given** each of the three induced-failure scenarios (backend unreachable, missing idea file, missing template) has been exercised on a dedicated sibling iter, **When** the orchestrator is invoked under each condition, **Then** the run-log entry for that scenario has `outcome: failure` with a non-empty `failure_reason`, the state YAML's `current_stage` is unchanged, and no `.specify/memory/constitution.md` is partially written. Each of the three scenarios must produce its own pass verdict independently.
2. **Given** the backend-unreachable scenario specifically, **When** the failure occurs, **Then** the failure is classified as a `TransientBackendError` (per spec 003 FR-002's distinction between backend-side and agent-side failures), and the diagnostic report explicitly notes that this is NOT a Phase 2 agent defect.

---

### User Story 5 - Verbatim artifact capture and critical evaluation report (Priority: P1)

Throughout US1-US4, the maintainer maintains a single diagnostic report under `notes/2026-05-05-phase2-diagnostic.md` (mirroring spec 003's `notes/2026-05-04-phase1-diagnostic.md` structure). The report quotes every artifact verbatim — every system prompt sent to the agent (with tokens already substituted), every constitution produced, every state YAML before/after, every run-log JSONL line — and critiques each one against issue #62's acceptance criteria with severity tags. The report's structure mirrors spec 003's: Sections 1-8 covering inputs, agent behavior, outputs, defects table, iteration diffs (if any), per-issue acceptance-criteria summary, recommendations, and carry-forward decision for spec 005.

**Why this priority**: A bare "tests pass" verdict is useless. Verbatim quotes plus side-by-side critique are the only format that catches latent quality issues — partially substituted constitutions, dropped principles, idempotency violations that don't surface as exceptions but as silent file mutation. The report doubles as the source-of-truth handed to issue #107 to advance Phase 2's checkbox from `[ ]` to `[x]`.

**Independent Test**: Can be tested by reading the report and confirming each artifact appears in a fenced code block, each quote is followed by an evaluation paragraph that explicitly cites issue #62's checkbox(es) (the three acceptance-criterion lines: rendering, scripts/runners, idempotency), each marked pass/fail with rationale, and that issues identified are bucketed into well/needs-improvement/broken with severity (CRITICAL/HIGH/MEDIUM/LOW) and file:line fix pointers.

**Acceptance Scenarios**:

1. **Given** project_initializer has run on at least one iter2 sibling, **When** the report is generated, **Then** the rendered system prompt (with all `{{token}}` substitutions visible) is quoted in full, the constitution is quoted in full (or with `[truncated lines N-M, sha256: <hash>]` markers if >100 lines), the state YAML is quoted before/after, and the run-log entry is quoted as JSON.
2. **Given** the report is generated, **When** a reviewer reads it, **Then** every checkbox in issue #62's acceptance-criteria block is explicitly marked pass/fail with rationale tied to a quoted artifact.
3. **Given** the report identifies any defect, **When** the defect is summarized, **Then** it has a severity (CRITICAL / HIGH / MEDIUM / LOW), a file:line pointer to where the fix should land, and either an "After fix" subsection quoting corrected behavior (if fixed in-PR) OR a follow-up issue link (if deferred).

---

### User Story 6 - Carry-forward gate: 1-2 projects tagged for Phase 3 testing (Priority: P2)

Once US1-US5 have produced quality output on at least one sibling per canonical project, the maintainer formally selects 1-2 iter2 siblings (or, if all iter2 siblings have audit-blocking defects, the original PROJ-261/PROJ-262 from spec 003's carry-forward) that will become the input substrate for spec 005 (Phase 3 — Spec Kit: Specify → Clarify, parent issue #47). The selection is recorded in `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` with each project ID, final state (`project_initialized`), final commit hash, the agents that ran on it (in this spec: just `project_initializer`), and a one-paragraph justification covering whether its constitution passes the US2 audit cleanly. Future specs reference this file to know which projects to operate on.

**Why this priority**: Without this gate, "carry forward to Phase 3" is folklore. With this gate, spec 005 starts with `cat specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` and knows exactly which projects to run `specifier` and `clarifier` on. P2 because it's the bridge to the next spec, not a self-contained capability.

**Independent Test**: Can be tested by reading `carry-forward.yaml`, confirming each named project ID corresponds to a real `projects/<id>/` directory at `current_stage: project_initialized`, and confirming the named commit hashes match the last touch of those project directories.

**Acceptance Scenarios**:

1. **Given** the diagnostic in US5 has identified at least one constitution that passes the US2 audit cleanly, **When** `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` is written, **Then** it names 1-2 project IDs with metadata: `final_state: project_initialized`, final commit hash, agents-run summary, justification.
2. **Given** spec 005 (or any later phase-test spec) starts work, **When** it reads this carry-forward manifest, **Then** it can pick any named project ID and find the project directory, `state/projects/<id>.yaml`, idea artifacts, AND `.specify/memory/constitution.md` in the expected committed state.
3. **Given** the carry-forward is written, **When** the spec is closed, **Then** the matching parent issue checkbox in #107 (`#46 [Phase 2] Project Bootstrap`) is ticked.

---

### Edge Cases

- **Backend unreachable mid-run**: project_initializer needs the backend to render the constitution. If it's down, the run must surface a `TransientBackendError` (per spec 003 FR-002), the run-log records `outcome: failure`, and state remains at `validated`. The diagnostic must distinguish this from agent-side defects.
- **Constitution is partially written if backend dies mid-stream**: The current implementation writes the constitution AFTER the response is fully received (per `project_initializer.py` L84-L102), so a mid-stream backend failure should leave NO `.specify/memory/constitution.md`. Spec must verify this. If a partial file is found after a forced backend failure, that's a CRITICAL defect (file write should be atomic-or-absent).
- **LLM output is malformed**: `project_initializer.py` L94-L101 has a defensive fallback — if the LLM output doesn't start with `#`, it falls back to a pre-rendered template substitution. The spec must induce this case (e.g., prompt the agent in a way that returns a non-Markdown response — though this is hard to force naturally). At minimum the fallback path must be documented and either tested or accepted as best-effort.
- **`init_speckit_in` is non-idempotent on a corrupted scaffold**: If the project already has a `.specify/templates/` dir but it contains stale or partial files, `init_speckit_in` does NOT overwrite (per `runner.py` L114 — `if dst.is_dir(): continue`). This is the documented idempotent behavior, but it means a corrupted scaffold is NEVER auto-repaired. Spec must surface this — either as accepted behavior or as a HIGH defect needing a fix to make `init_speckit_in` checksum-aware (similar to how `_resync_project_scripts` already is, per `runner.py` L42-L55).
- **Domain-specific principles fabricated to look real**: The prompt allows up to two domain-specific principles. The LLM might fabricate principles with no actual basis in the project's research domain (e.g., a "Quantum Coherence Preservation" principle for a chemistry project that has nothing to do with coherence). The audit (US2) must spot-check this against the project's idea body.
- **Token substitution leaks**: If any of `{{project_id}}`, `{{title}}`, `{{field}}`, `{{date}}`, `{{principal_agent_name}}` survives in the final constitution, that's a CRITICAL defect — the parent template explicitly says these are substituted before the LLM is called, but the LLM might echo a token literally in its response.
- **Constitution contradicts the parent constitution's principles**: The project-level constitution explicitly inherits parent Principles I–V (per the parent template's design). If the LLM writes domain-specific principles that contradict a parent principle (e.g., a "Mocks Acceptable for Speed" principle would contradict parent Principle III), that's a CRITICAL defect.
- **Stage advancement when the constitution is empty/malformed**: Per llmXive Constitution Principle V (Fail Fast), if the LLM returns an empty response or malformed Markdown that fails the defensive fallback, the agent must NOT advance state. If `current_stage` becomes `project_initialized` despite an empty constitution, that's the most severe defect class in this spec — silent state advancement on broken content.
- **Run-log gap on uncaught exception**: If project_initializer crashes (uncaught Python exception), the run-log entry must still be appended with `outcome: failure` and a populated `failure_reason`. US4's induced-failure scenarios verify this.
- **Quote size cap**: Constitutions are roughly 100 lines; that's right at spec 003's verbatim-quote cap. Cap quotes at 100 lines with `[truncated lines N-M, sha256: <hash>]` markers above that.
- **Sibling spawner doesn't accept `--start-stage validated`**: Spec 003's spawner declared `ALLOWED_START_STAGES = {"brainstormed", "flesh_out_in_progress", "flesh_out_complete"}` — none of which is `validated`. This is a known prerequisite covered by **FR-003a / T004** (extend the allowlist to include `validated`); not a defect — the spawner was written before the validator stage existed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run the Phase 2 agent (`project_initializer`) one-at-a-time on **real projects** spawned as `-iter2` siblings of the carry-forward projects from `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`. Exactly **one iter2 sibling per canonical** (PROJ-261 and PROJ-262) — 2 successful runs total under the happy path, plus any iter3+ spawned only on defect — using the production code path (`python -m llmxive run --project <sibling-id> --max-tasks 1`) against the real Dartmouth Chat backend.
- **FR-002**: System MUST issue real API calls against the configured backend (no mocks, no fakes — per spec 003 FR-002 and llmXive Constitution Principle III) and gracefully distinguish backend-side failures from agent-side defects. Per Q4 clarification, a single agent run MUST retry transient backend errors **at least** 2 times (3 total attempts minimum) before raising `TransientBackendError` and routing the project to `human_input_needed`. The retried-then-failed run counts as one cycle against the FR-005 5-cycle iteration cap. The canonical retry policy is implemented in `src/llmxive/backends/router.py:96-100` (3 attempts on primary model + 1 attempt on each peer model in `MODEL_FALLBACKS` per backend × the entire fallback-backend chain). This already EXCEEDS the 2-retry minimum — see research.md Decision 3. The dartmouth backend at `src/llmxive/backends/dartmouth.py:163-180` only classifies transient vs permanent errors; the retry loop itself lives in the router. Verification (no fix expected) lands as task T012.
- **FR-003**: System MUST spawn each iter2 sibling using `tests/phase1/sibling_project.py` from spec 003 (already merged) at `--start-stage validated`, NOT at `brainstormed` — because Phase 2 testing presumes the project has already passed Phase 1's validator (per the current pipeline graph wiring at `STAGE_TO_AGENT[VALIDATED]`). **FR-003 depends on FR-003a's allowlist extension**: the spawner does NOT accept `validated` until that fix lands (covered by T004); FR-003a MUST be completed before any sibling-spawn task in US1 / US4 runs.
- **FR-003a**: System MUST extend `tests/phase1/sibling_project.py`'s `ALLOWED_START_STAGES` to include `validated` (currently only contains `{brainstormed, flesh_out_in_progress, flesh_out_complete}`). This is a known prerequisite of FR-003 and lands as the first commit of this spec's implementation.
- **FR-004**: System MUST accept that the canonical PROJ-261 and PROJ-262 on `main` already have `.specify/` scaffolds (because spec 003 ran project_initializer on them). State surgery on the canonical projects is **never** used; each iter2 sibling is a fresh, independently replayable run.
- **FR-005**: System MUST cap fix-and-re-run iterations per agent at 5 cycles (per spec 003 FR-005). Hitting the cap forces a deferral decision — either accept current state (record `accepted (not addressed)`) or file a follow-up GitHub issue. Continuing past the cap on the same defect is prohibited.
- **FR-006**: System MUST capture every artifact written by the agent — the LLM-rendered `.specify/memory/constitution.md`, the mechanical `.specify/{scripts,templates}/` tree contents (or sha256 manifest if too large to quote in full), and any sentinel files written under `.specify/memory/` — verbatim into the diagnostic report, with cap+hash truncation for files >100 lines.
- **FR-007**: System MUST capture the project state YAML and the run-log JSONL entry before and after every agent invocation, quoted verbatim.
- **FR-008**: System MUST capture the verbatim system prompt sent to the LLM (with all `{{token}}` substitutions resolved to concrete values), so the audit can verify (a) substitution worked, (b) the prompt sent the correct title/field/idea-body, (c) no tokens leaked.
- **FR-009**: System MUST evaluate every artifact against the acceptance-criteria checkboxes from issue #62 (project_initializer): (1) renders constitution.md with project-specific principles (not template placeholders), (2) creates the scripts/bash/ runners, (3) idempotent on second run.
- **FR-010**: System MUST audit the rendered constitution against the explicit output contract in `agents/prompts/project_initializer.md`: literal heading and footer, ≤2 added principles, no removed inherited principles, no external citations, Reproducibility Requirements adapted to actual data sources. Any deviation is a defect with severity.
- **FR-011**: System MUST verify full idempotency of `project_initializer` by computing sha256 hashes of every file under `projects/<id>/.specify/` (including `memory/constitution.md`, scripts, and templates) before and after a second agent invocation; the hash lists must be identical at the file-content level. Per Q3 clarification: the current overwrite-unconditional behavior on `.specify/memory/constitution.md` at `src/llmxive/agents/project_initializer.py:84-102` is a HIGH defect that MUST be fixed in this PR — the agent MUST detect a pre-existing constitution and skip re-rendering, matching the `init_speckit_in` skip-if-dir-exists pattern at `src/llmxive/speckit/runner.py:114`.
- **FR-012**: System MUST induce **all three** deliberate failure modes (backend unreachable, idea file missing, template file missing) — per Q2 clarification — and verify each one's failure path produces a loud, recorded failure rather than silent state advancement, per llmXive Constitution Principle V. Each scenario runs on its own dedicated sibling iter so the failures don't contaminate each other.
- **FR-013**: System MUST persist the diagnostic report under `notes/2026-05-05-phase2-diagnostic.md`, formatted in Markdown with fenced code blocks for every quoted artifact, mirroring spec 003's report structure.
- **FR-014**: For each CRITICAL or HIGH defect identified, system MUST either (a) apply a fix in this PR with an "After fix" report section quoting the corrected behavior, or (b) explicitly defer to a follow-up GitHub issue with rationale recorded in the report, per spec 003 FR-013's pattern.
- **FR-015**: System MUST never advance state silently when the constitution fails its content contract — empty file, partially substituted tokens, missing inherited principles, fabricated citations, or contradictions with the parent constitution must be flagged as CRITICAL defects.
- **FR-016**: System MUST commit all real-project artifacts produced (`projects/PROJ-261-…-iter2/**`, `projects/PROJ-262-…-iter2/**`, `state/projects/PROJ-…-iter2.yaml`, `state/run-log/<YYYY-MM>/*.jsonl`) so the report and the carry-forward gate are reproducible.
- **FR-017**: System MUST formally select 1-2 projects to carry forward (those whose constitutions pass the US2 audit cleanly) and record the selection in `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` with project IDs, final state, final commit hash, agents-run summary, and a one-paragraph justification per project.
- **FR-018**: All fixes applied as part of this work MUST land as separate commits with messages referencing both the parent issue (#46) and the specific sub-issue (#62) and the report section that motivated the fix.
- **FR-019**: System MUST allow non-selected iter2 siblings to remain in `projects/` (kept for future reference) or be marked archived by adding `archived_at: <ISO-8601 UTC>` to their state YAML. Non-selected siblings MUST NOT be silently deleted.
- **FR-020**: Iteration on the agent's prompt at `agents/prompts/project_initializer.md`, the constitution template at `agents/templates/research_project_constitution.md`, the registry entry at `agents/registry.yaml`, or the implementation in `src/llmxive/agents/project_initializer.py` MUST follow spec 003's prompt-version semver policy (MAJOR for output-contract-breaking, MINOR for behavior, PATCH for prose), with the version bump in the same commit as the patch.
- **FR-021**: Each new iteration after a prompt/code patch MUST spawn a new sibling (`PROJ-NNN-<slug>-iter3`, `-iter4`, …) — never reset state on the prior iteration's sibling — per spec 003's iteration discipline (FR-004).

### Key Entities *(include if feature involves data)*

- **Carry-forward sibling**: An iter2 (or iterN) project spawned via `tests/phase1/sibling_project.py` from a canonical carry-forward project. Has a fresh `state/projects/<sibling-id>.yaml` at `current_stage: validated`, byte-identical `idea/<slug>.md` (sha256-verified), and no `.specify/` scaffold yet. Distinct from the canonical: state surgery on the canonical is never used.
- **Project_initializer agent run**: A single invocation of `python -m llmxive run --project <sibling-id> --max-tasks 1` against a sibling at `validated`. Produces (a) a rendered system prompt (LLM input), (b) `.specify/memory/constitution.md` (LLM output), (c) `.specify/{scripts,templates}/` tree (mechanical via `init_speckit_in`), (d) state YAML transition `validated → project_initialized`, (e) run-log JSONL line.
- **Constitution artifact**: `projects/<sibling-id>/.specify/memory/constitution.md`. Audited against the explicit output contract in `agents/prompts/project_initializer.md`.
- **Spec Kit scaffold**: `projects/<sibling-id>/.specify/{scripts,templates}/` produced by the mechanical `init_speckit_in` step. Verified for completeness and idempotency.
- **Diagnostic report**: A single Markdown file at `notes/2026-05-05-phase2-diagnostic.md` quoting every artifact verbatim, evaluating each against issue #62's acceptance criteria, capturing iteration diffs (if any), and bucketing findings into well/needs-improvement/broken with severity tags.
- **Carry-forward manifest**: `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` naming the 1-2 selected projects with metadata for reference by spec 005 (Phase 3 testing).
- **Idempotency hash list**: A sha256-per-file manifest computed over `projects/<sibling-id>/.specify/{scripts,templates}/` before and after a second `init_speckit_in` invocation. Diff between the two lists is the test result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `project_initializer` agent runs end-to-end against the real Dartmouth Chat backend on at least one iter2 sibling per carry-forward project (at least 2 successful runs total), with zero mock/fake calls and zero direct calls bypassing the production orchestrator entry point.
- **SC-002**: At least 1 iter2 sibling has a constitution that passes the US2 audit (all six output-contract items pass) and is recorded in `carry-forward.yaml`.
- **SC-003**: The diagnostic report quotes every artifact written and every run-log entry produced — no agent's output omitted, no induced failure's failure path omitted.
- **SC-004**: Every acceptance-criterion checkbox from issue #62 is explicitly marked pass or fail in the report, with rationale tied to a specific quoted artifact (per agent run, per project).
- **SC-005**: All three deliberate failure modes (backend unreachable, idea file missing, template file missing) are induced on dedicated sibling iters, and each one's run-log entry is verified to record `outcome: failure` with a populated `failure_reason`. State YAML's `current_stage` remains unchanged in all three cases — demonstrating Phase 2's failure paths are not silent under any of the three precondition violations Constitution Principle V requires us to guard.
- **SC-006**: For every CRITICAL or HIGH defect identified, either an "After fix" report section quotes the corrected behavior or a follow-up issue link is recorded with rationale — no defect is silently dropped.
- **SC-007**: Iteration is bounded per agent (≤5 fix-and-re-run cycles, per spec 003 FR-005 / SC-008) so the spec converges in finite time.
- **SC-008**: The carry-forward manifest is concrete enough that spec 005 can read it and pick up the named projects without re-discovering the substrate.
- **SC-009**: Full idempotency is empirically verified: the sha256-per-file manifest of `projects/<sibling-id>/.specify/` (including `memory/constitution.md`, `scripts/`, `templates/`) after a second `project_initializer` invocation matches the first byte-for-byte. Per Q3 clarification, the constitution skip-if-exists fix MUST be applied in this PR before SC-009 can be marked pass — failure mode where re-render produces a different governance document is a HIGH defect this spec is responsible for fixing, not deferring.
- **SC-010**: No `.specify/memory/constitution.md` produced by Phase 2 contains any literal `{{token}}` strings (substitution must be complete before the LLM is invoked, per `project_initializer.py` L43-L54). Any token leak is a CRITICAL defect.
- **SC-011**: No `.specify/memory/constitution.md` produced by Phase 2 introduces an external citation, removes any of the inherited Principles I-V, or contradicts any parent constitution principle. Any of those is a CRITICAL defect.
- **SC-012**: At the end of this spec, the parent issue checkbox `#46 [Phase 2] Project Bootstrap` in tracking issue #107 is ticked (`[x]`) and issue #62 is closed with a comment referencing the diagnostic report and the carry-forward manifest.

## Assumptions

- The Dartmouth Chat backend (`DARTMOUTH_CHAT_API_KEY` in `~/.config/llmxive/credentials.toml`) is reachable for the duration of the test; if not, the test will surface that as a transient failure and stop, rather than fall back to a mock.
- The orchestrator entry point is `python -m llmxive run --project <id> --max-tasks 1` (verified during spec 003).
- The carry-forward manifest from spec 003 (`specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`) is authoritative and unmodified — PROJ-261 and PROJ-262 remain valid carry-forward inputs.
- The sibling spawner `tests/phase1/sibling_project.py` from spec 003 is reusable for Phase 2 with one extension (FR-003a: add `validated` to `ALLOWED_START_STAGES`). No separate sibling tooling is built.
- Agent prompts at `agents/prompts/project_initializer.md`, the constitution template at `agents/templates/research_project_constitution.md`, the registry entry, and the agent code are all editable as part of this iteration loop; changes ship as part of this PR.
- The existing PROJ-261 and PROJ-262 scaffolds on `main` are NOT modified by this spec. They serve as a reference for what "good output" should look like (since spec 003 already audited them through the Phase 1 lens), but iter2 siblings are the actual subject of this spec's testing.
- Real-project artifacts produced by iter2 sibling runs are small (constitutions are ~100 lines, scaffold trees are <30 files, idea files are <100 lines), so committing them is bounded in size.
- The agent's acceptance criteria as written in issue #62 are the authoritative checklist; if they themselves are wrong (too lax / too strict), the report will note that as a finding rather than rewriting them inline.
- The diagnostic report file path will be `notes/2026-05-05-phase2-diagnostic.md` unless the user prefers a different location.
- The carry-forward manifest path is `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`; spec 005 (Phase 3) and beyond can reference it.
- This work is sequential to (not blocked by) any other open Phase issue in #107 — Phase 2 has no dependency on Phases 3-14.
- A maintainer (human in the loop) makes the final selection of which iter2 sibling(s) carry forward; no agent's verdict overrides that judgment, since this spec is also testing whether project_initializer's output is trustworthy enough to feed into Phase 3.
