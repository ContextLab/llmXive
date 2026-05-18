# Feature Specification: Paper Review Convergence

**Feature Branch**: `012-paper-review-convergence`
**Created**: 2026-05-17
**Status**: Draft
**Input**: User description: "redesign paper review acceptance + revision loop"

## Background

The current paper-review pipeline ties acceptance to a unanimous-specialists gate: a paper is published only if every one of the 12 specialist reviewers (jargon police, figure critic, statistical analysis, scientific evidence, code/data quality, claim accuracy, logical consistency, overreach, safety/ethics, text formatting, writing quality) records an `accept` verdict at least once. In practice the gate is unreachable — every specialist is calibrated to *find* issues, so at least one always flags a minor revision regardless of paper quality. Reviewed papers therefore ping-pong forever between `paper_review` and `paper_minor_revision`, never advancing to `paper_accepted`.

A second problem compounds this: on each re-review pass, specialists treat the paper as fresh and surface a *new* set of nits. There is no notion of "did the prior round's concerns get addressed?" — so even if every original action item is fixed, the next round simply produces a new list of equivalent quibbles and the loop continues.

A third gap: when a verdict *does* trigger a revision (minor or major), there is no automatic kickoff of the revision work itself. The project sits at a `*_revision` stage waiting for a human (or never-quite-wired-up agent) to construct a revision plan and execute it.

## Clarifications

### Session 2026-05-17

- Q: While the auto-planned revision-spec pipeline (specify→clarify→plan→tasks→analyze) is running, what should the project's `current_stage` be? → A: Add a new stage `paper_revision_in_progress`. The project moves there when auto-planning starts and stays until all five speckit stages complete; then it transitions to a flag/state indicating "ready for implementation".
- Q: When a project has prior reviews from some specialists but not others (e.g., a newly-added specialist), which protocol does each specialist use? → A: Per-specialist toggle. A specialist uses the re-review protocol only if THAT specialist has ≥1 prior review for this project; otherwise it runs the standard full-critique prompt.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — A genuinely-good paper converges to acceptance (Priority: P1)

A paper enters review, is critiqued, has the concrete action items addressed in a revision round, and on re-review the specialists confirm "yes, the prior items are addressed; nothing new is broken" → the paper advances to `paper_accepted` and is published.

**Why this priority**: This is the failing case today. Without it, no paper ever reaches `paper_accepted`, the pipeline produces no output, and the value of the entire review apparatus is zero.

**Independent Test**: Drive a fixture paper through one review → minor revision → re-implementation → re-review cycle. Assert that when every prior action item is addressed and no new issues are introduced, the project's stage transitions to `paper_accepted`. Verify a publication record is emitted.

**Acceptance Scenarios**:

1. **Given** a paper at `paper_review` with prior reviews recording specific action items, **When** the revision agent addresses every action item and re-review confirms (a) all prior items addressed AND (b) no new issues introduced, **Then** the project transitions to `paper_accepted` and is published.
2. **Given** a paper at `paper_review` with no prior reviews and the LLM is satisfied with the manuscript as-is, **When** every specialist returns `accept` in the first round, **Then** the project transitions to `paper_accepted` without any revision cycle.

---

### User Story 2 — Writing-only concerns trigger an auto-planned revision (Priority: P1)

A paper has issues that can be fixed by edits to the manuscript text (typos, clarity, missing citations, figure caption work, terminology consistency, etc.) — no new experiments needed. The system constructs a fresh revision spec, plans the work, decomposes into tasks, analyzes for gaps, and flags the project as ready for an implementation agent to pick up and edit the manuscript.

**Why this priority**: This is the most common revision class. Without auto-planning, projects stall at `paper_minor_revision` waiting for a human. With it, the pipeline self-feeds.

**Independent Test**: Drive a fixture paper through review with at least one writing-class verdict. Assert that a new paper-revision spec directory is generated, its plan/tasks/analyze stages complete automatically, and the project is flagged as ready for `speckit-implement`.

**Acceptance Scenarios**:

1. **Given** a paper at `paper_review` whose specialist verdicts include any of `minor_revision` / `major_revision_writing` (and no `*_science` or `reject`), **When** the advancement evaluator runs, **Then** the system kicks off `speckit-specify` → `speckit-clarify` → `speckit-plan` → `speckit-tasks` → `speckit-analyze` for a paper-revision spec rooted in the consolidated action items, addressing all analyzer findings with the recommended remediation.
2. **Given** the auto-planned revision pipeline has completed all five speckit stages, **When** the project state is inspected, **Then** the project is flagged `ready_for_implementation` with a reference to the new spec directory.
3. **Given** the project is flagged `ready_for_implementation`, **When** an implementation agent next picks up the project, **Then** it runs `speckit-implement` against the new spec; on completion, the project re-enters `paper_review` for re-review.

---

### User Story 3 — Mild science concerns trigger a major revision that re-enters research (Priority: P1)

A paper has issues that can't be fixed by writing alone — a methodological gap, a missing control condition, an unwarranted claim — but the core research idea is salvageable. The system constructs a research-revision spec and routes the project back to the research-spec phase so the experimental work can be redone. ("Mild" here means at least one action item has `severity: science`, AND no action item has `severity: fatal`.)

**Why this priority**: Without this path, science-class concerns either silently degrade to "minor revision" (insufficient — the writing pipeline can't fix them) or stall. Both outcomes hide real defects.

**Independent Test**: Drive a fixture paper through review with at least one `major_revision_science` verdict. Assert that a new research-revision spec is generated, the project's stage moves back to the research-spec phase, and the project is flagged ready for re-implementation.

**Acceptance Scenarios**:

1. **Given** a paper at `paper_review` whose specialist verdicts include `major_revision_science` (mild — not "fundamental flaws") and no `reject`, **When** the advancement evaluator runs, **Then** the system kicks off `speckit-specify` → `speckit-clarify` → `speckit-plan` → `speckit-tasks` → `speckit-analyze` for a research-revision spec, the project re-enters the research-spec phase, and is flagged `ready_for_implementation`.

---

### User Story 4 — Severe science concerns reject the paper back to the backlog (Priority: P1)

A paper has a fundamental flaw the system cannot work around — the central hypothesis was never supportable, the data is fabricated, the design has no scientific merit, or every claim depends on something unverifiable. The paper is rejected and the underlying idea returns to the backlog with a concrete explanation so a human (or future agent) can decide whether to flesh out a new approach. ("Severe" here means at least one action item has `severity: fatal`.)

**Why this priority**: Without a rejection path, fundamentally broken work consumes review/implementation resources forever. Without a concrete explanation attached, returning ideas to the backlog drops context.

**Independent Test**: Drive a fixture paper through review with at least one `fundamental_flaws` (or equivalent severe) verdict. Assert that the project transitions to `brainstormed`, the original idea is preserved, and a rejection rationale citing each fatal issue is attached to the idea.

**Acceptance Scenarios**:

1. **Given** a paper at `paper_review` whose aggregated specialist verdicts include `fundamental_flaws` or `reject`, **When** the advancement evaluator runs, **Then** the project transitions to `brainstormed`, the rejection rationale (citing each fatal action item) is appended to the idea record, and no revision pipeline is triggered.

---

### User Story 5 — Reviewers stop generating fresh critique on every round (Priority: P2)

When a paper is re-reviewed after a revision, the reviewer's prompt focuses it on two diff-style questions instead of starting from scratch: (a) have the prior action items been addressed? and (b) has the revision introduced any new issues? This prevents the "endless nit" failure mode where every round surfaces an equally-valid but different set of minor revisions.

**Why this priority**: Even with the new acceptance criterion (unanimous accept), without the re-review protocol the loop will still oscillate because each round produces new equivalent nits. P2 because the convergence guarantee comes from US1; this story makes convergence *fast* rather than *eventually*.

**Independent Test**: Construct a paper with N prior reviews each recording specific action items. Drive a re-review pass. Assert the reviewer's output references each prior action item by ID, classifies each as "addressed" / "partially addressed" / "not addressed", explicitly lists or denies new issues, and emits a verdict consistent with the two-question protocol.

**Acceptance Scenarios**:

1. **Given** a paper has ≥1 prior paper-review records with action items, **When** a reviewer runs, **Then** its prompt includes the prior action items verbatim and instructs the model to apply the two-question protocol.
2. **Given** the model judges every prior item addressed AND finds no new issues, **When** it emits a verdict, **Then** the verdict is `accept` (not "minor revision because there's always something").
3. **Given** the model judges some prior item NOT addressed, **When** it emits a verdict, **Then** the verdict explicitly references the unaddressed item(s) by ID, and the action_items list contains only the unaddressed (or newly-broken) items — not a fresh re-critique.

---

### User Story 6 — Every review record carries structured action items (Priority: P1)

Today reviews are free-form prose. The new pipeline can't apply the re-review protocol or auto-plan revisions without a structured list of concrete things the authors must do. Every review record gains an `action_items` field — a list of short, actionable statements, each with a stable ID and a severity classification.

**Why this priority**: This is a structural prerequisite for US1, US2, US3, US5. Without it, the rest of the convergence work has no machine-readable input.

**Independent Test**: Inspect any review record emitted by the new pipeline. Assert it contains an `action_items` field, the field is a list (possibly empty for an `accept`), each item has a stable ID + short text + severity classification (writing / science / fatal), and the union of action_items across the review record's verdict drives advancement.

**Acceptance Scenarios**:

1. **Given** a reviewer emits a verdict other than `accept`, **When** the review record is parsed, **Then** `action_items` is non-empty and each item has `id`, `text`, `severity` ∈ {writing, science, fatal}.
2. **Given** a reviewer emits `accept`, **When** the review record is parsed, **Then** `action_items` may be empty.

---

### User Story 7 — arXiv-intake papers don't get mutated by the writing-revision path (Priority: P2)

arXiv-intake papers are third-party submissions; their source tarball is frozen. The writing-revision path (which would modify the manuscript) cannot apply to them — there is no `paper/source/` for the system to edit. Their only legitimate outcomes are accept-as-is or reject. The science-revision path is even less applicable: the upstream authors aren't going to re-run their experiments on our behalf.

**Why this priority**: Without this distinction, the system would try to plan a writing revision for an arxiv-intake paper, fail (or worse, succeed and silently corrupt the source), and stall. P2 because the home-grown convergence work matters more in volume, but the arxiv-intake guardrail must exist to avoid a known foot-gun.

**Independent Test**: Construct an arxiv-intake fixture project and drive it through review with a `minor_revision` verdict. Assert that the system does NOT kick off a writing-revision pipeline against the frozen source — instead it records a "request changes from upstream" annotation against the project and either accepts-with-caveats or rejects.

**Acceptance Scenarios**:

1. **Given** an arxiv-intake paper at `paper_review` whose specialists yield writing-class verdicts, **When** the advancement evaluator runs, **Then** the system records the consolidated action items as an upstream-feedback annotation and either (a) advances the paper to `paper_accepted` with caveats noted, or (b) transitions to `brainstormed` with the rationale — but does NOT attempt to mutate `paper/source/`.

---

### Edge Cases

- **All specialists accept on a paper with prior unresolved action items**: should still accept (the prior items were judged addressed by every specialist; that's the convergence signal).
- **Mixed verdicts spanning writing AND science**: science class wins (worst-case routing — writing fixes can't address science gaps, but a science revision pass will also touch the writing).
- **Specialists hallucinate new "issues" not actually present in the paper**: out of scope here; covered by the existing real-call regression suite.
- **A revision spec auto-plan fails (analyzer can't reach zero findings)**: project stalls at a new `paper_revision_blocked` state with a diagnostic record. No silent advancement, no silent demotion.
- **The same action item appears in multiple specialists' reviews**: deduplicate by canonicalized text when consolidating to a revision-spec input.
- **A reviewer emits an `accept` verdict but their action_items list is non-empty**: the action items are recorded as informational notes but do not gate advancement; the verdict is what matters.
- **An auto-planned revision pipeline runs but the implementation agent is busy/missing**: the project stays flagged `ready_for_implementation` and the next available implementation tick picks it up.
- **A re-review judges some action item "partially addressed"**: counts as "not addressed" for the convergence test; the project goes back through another revision round.

## Requirements *(mandatory)*

### Functional Requirements

#### Acceptance gate (the convergence change)

- **FR-001**: System MUST advance a paper to `paper_accepted` when every required specialist reviewer's most-recent verdict is `accept`. No additional point threshold is required.
- **FR-002**: System MUST NOT advance a paper to `paper_accepted` if any required specialist's most-recent verdict is other than `accept`, regardless of cumulative points.
- **FR-003**: System MUST evaluate the "most-recent verdict per specialist" against the live artifact hash. Reviews of stale artifacts (hash mismatch) MUST be ignored for the gate.

#### Three-way revision classification

- **FR-004**: System MUST classify a non-accept aggregate verdict as exactly one of `writing_revision`, `science_revision`, or `reject` based on the highest-severity action item across all specialists' most-recent reviews.
- **FR-005**: Severity ordering for classification, lowest to highest: `writing` → `science` → `fatal`. The classification is the severity of the most severe action item.
- **FR-006**: `writing_revision` classification MUST transition the project to `PAPER_REVISION_IN_PROGRESS` with a `revision_kind="paper_writing"` discriminator that drives the auto-plan pipeline (FR-009). Intermediate stages such as `paper_minor_revision` and `paper_major_revision_writing` are NO LONGER reachable from `PAPER_REVIEW` directly — they are absorbed into `PAPER_REVISION_IN_PROGRESS`.
- **FR-007**: `science_revision` classification MUST transition the project to `PAPER_REVISION_IN_PROGRESS` with `revision_kind="paper_science"`. Intermediate stage `paper_major_revision_science` is similarly absorbed.
- **FR-008**: `reject` classification MUST transition the project to `BRAINSTORMED`. The rejection rationale (consolidated `fatal` action items) MUST be appended to the idea record so the backlog reflects why it was rejected.

#### Auto-planned revision

- **FR-009**: On entering `PAPER_REVISION_IN_PROGRESS`, the system MUST automatically kick off a revision-spec pipeline that runs `speckit-specify` → `speckit-clarify` → `speckit-plan` → `speckit-tasks` → `speckit-analyze`. While `current_stage == PAPER_REVISION_IN_PROGRESS`, the scheduler MUST NOT re-trigger the revision pipeline on subsequent ticks (idempotency).
- **FR-010**: The revision-spec pipeline MUST seed `speckit-specify`'s input with the consolidated action items from the triggering review round (deduplicated, severity-classified, mapped back to the specialist(s) that raised each).
- **FR-011**: The `speckit-analyze` stage of the revision-spec pipeline MUST address every finding it surfaces using its recommended remediation (no findings left unresolved). If after three remediation iterations the analyzer still surfaces findings, the project transitions to a `PAPER_REVISION_BLOCKED` state with a diagnostic record, NOT to acceptance or rejection.
- **FR-012**: On successful completion of all five revision-spec stages, the system MUST transition the project to stage `READY_FOR_IMPLEMENTATION` and set the project field `revision_spec_path` to the new spec directory.
- **FR-013**: The system MUST surface `READY_FOR_IMPLEMENTATION` projects via an index file (`state/revisions/index.yaml`) so that an implementation agent CAN discover them. The system MUST also commit to a transition rule: when an implementation agent reports successful completion of `speckit-implement` against a `READY_FOR_IMPLEMENTATION` project, the project's `current_stage` MUST be set to `PAPER_REVIEW` (and `revision_spec_path` cleared) so a re-review pass starts. The implementation agent itself is out of scope for this spec (see Assumptions); the spec's contract is the discovery index + the transition rule.

#### Re-review protocol

- **FR-014**: When a specialist reviewer runs against a project for which THAT SAME SPECIALIST has ≥1 prior review record of the same stage, its prompt MUST include that specialist's prior action items verbatim and the two-question protocol instruction: "(a) Have all prior action items been adequately addressed? (b) Have any new issues been introduced by this revision?" The per-specialist toggle keeps each reviewer-lens honest — a specialist with no prior view of the paper has nothing to "check addressed against" and would silently rubber-stamp if forced into re-review.
- **FR-015**: Under the re-review protocol, if the model judges every prior action item addressed AND finds no new issues, it MUST emit verdict `accept`. The system MUST NOT post-process this verdict to add nits.
- **FR-016**: Under the re-review protocol, if the model judges any prior action item not addressed, the new review's `action_items` list MUST contain those unaddressed items (with their original IDs preserved) plus any newly-discovered items — NOT a fresh independent critique.
- **FR-017**: A specialist with NO prior review record for this project (first-round or newly-added specialist) MUST NOT use the re-review protocol; it runs the standard full-critique prompt.

#### Action items on reviews

- **FR-018**: Every review record MUST include an `action_items` field. The field is a list (possibly empty when verdict = `accept`).
- **FR-019**: Each action item MUST have: a stable `id` (durable across re-reviews of the same project), a short `text` (≤500 chars), and a `severity` in {`writing`, `science`, `fatal`}.
- **FR-020**: Action item IDs MUST be stable across re-reviews: if a re-reviewer flags the same concern, it reuses the prior item's ID rather than minting a new one.

#### arXiv-intake guardrails

- **FR-021**: For arxiv-intake papers (detected by presence of `paper/metadata.json` and absence of a paper-feature-dir), the writing-revision and science-revision paths MUST NOT attempt to mutate `paper/source/`. Instead, the consolidated action items MUST be recorded as an upstream-feedback annotation file under the project, and the project's final outcome is restricted to `PAPER_ACCEPTED` (with caveats) or `BRAINSTORMED` (rejection).
- **FR-022**: An arxiv-intake paper that reaches `PAPER_ACCEPTED` with non-empty upstream-feedback annotations MUST still be marked `PAPER_ACCEPTED` — the caveats are surfaced on the published artifact but do not block publication.

#### Operator escape hatch (unblock)

- **FR-023**: The system MUST provide a CLI subcommand `llmxive project unblock <PROJ-ID>` that operators can run when a project is at `PAPER_REVISION_BLOCKED`. The command MUST: (a) verify the project's current stage is `PAPER_REVISION_BLOCKED`; (b) refuse to no-op-unblock — i.e., require that the operator has actually modified `state/revisions/<PROJ-ID>/round-<N>.yaml` since the block was recorded (mtime check); (c) transition the project back to `PAPER_REVIEW` (or `PAPER_MINOR_REVISION` if the operator passes a flag); (d) append a history entry recording the unblock action. The command MUST raise a clear error and exit non-zero on any precondition failure.

### Key Entities

- **ReviewRecord**: an immutable per-reviewer-per-round artifact. Existing fields (`verdict`, `score`, `feedback`, `reviewer_kind`, `reviewer_name`, `artifact_hash`, `artifact_path`, `reviewed_at`, `model_name`, `backend`, `prompt_version`, `github_authenticated`) plus the new `action_items` list.
- **ActionItem**: `{id, text, severity}`. Severity is one of `writing` / `science` / `fatal`. IDs are stable across re-reviews — the same concern keeps the same ID even when raised by different reviewers in different rounds.
- **RevisionSpec**: a generated spec directory rooted in the consolidated action items of a review round. Lives alongside (not inside) the original paper's source. Has its own spec.md / plan.md / tasks.md / analyze report.
- **UpstreamFeedbackAnnotation**: for arxiv-intake papers only. A per-project file recording consolidated action items that would have triggered a revision pipeline, but the source is frozen — so the items are surfaced as feedback rather than executed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least one paper that previously oscillated forever between `PAPER_REVIEW` and `paper_minor_revision` converges to `PAPER_ACCEPTED` (or, if its content genuinely warrants it, to `BRAINSTORMED`) within ≤3 revision rounds after the change ships.
- **SC-002**: All 8 previously-failing arxiv-intake fixture papers (PROJ-564, 565, 566, 568, 570, 571, 576, 578) reach a terminal state (`PAPER_ACCEPTED` with caveats, or `BRAINSTORMED`) under the test suite, with zero attempts to mutate `paper/source/` for any of them. (Verified by a parameterized real-call test that iterates over all 8 fixtures.)
- **SC-003**: No paper sits at `PAPER_REVISION_IN_PROGRESS` for more than 3 consecutive cron ticks without either advancing to `READY_FOR_IMPLEMENTATION` or transitioning to `PAPER_REVISION_BLOCKED` with a diagnostic record. (Enforced by scheduler-skip logic + the analyzer's 3-iteration cap.)
- **SC-004**: Every review record emitted after the change ships has a parseable, schema-valid `action_items` field.
- **SC-005**: When a re-review records that a prior action item has been "addressed", the re-review's record MUST NOT contain a new item with a different ID describing the same concern as a prior item. Operationally: in the parameterized test fixture that drives ≥2 review rounds, the ID-stability rate `same_id_for_same_concern / re-flagged_items` MUST be ≥0.8.
- **SC-006**: The end-to-end real-call test (T050) MUST drive a fixture through ≥1 successful auto-plan pipeline (all 5 speckit stages green) AND ≥1 simulated analyzer-stuck case (project lands in `PAPER_REVISION_BLOCKED` with a diagnostic). Both branches MUST be exercised; the per-fixture pass/fail rate is recorded but is not a release gate at v1.

## Assumptions

- The existing 12-specialist review pipeline stays intact; only the gate logic, the re-review prompt mode, and the post-verdict routing change.
- The advancement evaluator (currently `src/llmxive/agents/advancement.py`) is the single source of truth for stage transitions; this spec's logic lives there.
- The auto-planned revision pipeline reuses the existing speckit-specify/clarify/plan/tasks/analyze skills (no new skill is invented); it just invokes them programmatically with the action-item digest as input.
- Implementation agents that consume `ready_for_implementation` flags are out of scope here — this spec assumes such an agent exists or will be added separately; the spec's contract is "we set the flag; they pick it up."
- The home-grown paper pipeline (which generates `paper/source/` and lets agents edit it) remains the primary workflow; arxiv-intake is the special-case minority that needs the guardrail.
- For SC-005's "stable IDs": the canonical-text-hash approach (id = stable hash of normalized issue text) is acceptable as long as it produces stable IDs in practice for re-raised concerns; exact ID generation strategy is an implementation detail.
- "Fatal" severity is set by the LLM at review-emission time, not inferred post hoc. We trust the specialist to know the difference between "this paragraph is unclear" (writing), "this control condition is missing" (science), and "the entire central claim is unsupportable" (fatal).
