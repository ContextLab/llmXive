# Feature Specification: Pipeline End-to-End Completion

**Feature Branch**: `023-pipeline-e2e-completion`
**Created**: 2026-06-10
**Status**: Draft
**Input**: User description: "let's address issue 303 deeply and comprehensively. important: if any issues or additional problems are encountered along the way, they must be considered IN scope as opposed to deferred. the outcome of this spec is a 100% functional and tested high quality llmxive pipeline with at least one example of a project going through every phase from brainstormed idea to published paper."

llmXive currently tracks 696 projects and has never completed one: no project
has ever reached a published (`posted`) state, and no paper has ever been
accepted by its review panel (issue #303). The pipeline is busy — ~150 LLM
agent runs/day — but structurally cannot finish anything: review decisions
are made and then discarded, the research-idea queue is starved by the
scheduler, papers silently ship un-restyled or defective PDFs, and projects
routinely park themselves waiting for a human. This feature makes the
pipeline actually produce its product: completed, reviewed, published
research — demonstrated by at least one real project traversing **every**
phase from brainstormed idea to published paper with a DOI.

**Scope rule (per maintainer, verbatim intent):** any defect, gap, or
quality problem encountered while delivering this feature — whether or not
it is listed in issue #303 — is IN scope and must be fixed (generally, so
the fix applies to all projects), not deferred. Encountered-issue handling
follows the issue-#239 part-7 discipline: examine every artifact a stage
produces, fix the *stage* (code, prompts, agents) until its outputs are high
quality, then move on.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review decisions take effect (Priority: P1)

The paper-review panel's verdicts must actually move papers. Today the
advancement evaluator correctly decides "accept" or "needs revision (here is
the revision work-spec)" on every tick, but the decision is discarded before
it is saved, so the 92 papers under review loop forever and reviewers
re-review the same papers daily. After this story, a paper whose specialist
panel demands revisions gets a persisted revision work-spec that the
revision implementer picks up on a later tick; a paper whose panel fully
accepts advances toward publication.

**Why this priority**: This is the single severed link that makes
completion impossible for the entire paper track, and it also frees the
scheduler capacity that currently burns ~83% of all runs on no-op
re-reviews. Nothing can ever publish until this works.

**Independent Test**: Drive one pipeline step for a project under paper
review whose stored verdicts demand revisions; verify the saved project
state now carries the revision work-spec reference and the revision
artifacts exist and are persisted (committed) — then drive a later step and
verify the revision implementer consumes that work-spec instead of
reviewers being re-dispatched.

**Acceptance Scenarios**:

1. **Given** a project at paper review with a complete, current set of
   specialist verdicts demanding revisions, **When** the pipeline evaluates
   it, **Then** the saved project state references the generated revision
   work-spec and the next pipeline pass dispatches the revision implementer
   (not another round of reviewers).
2. **Given** a project at paper review whose every required specialist's
   most-recent verdict is "accept" against the current artifact, **When**
   the pipeline evaluates it, **Then** the project advances out of paper
   review toward publication sign-off.
3. **Given** a project with a fresh, complete, non-stale verdict set,
   **When** the scheduler picks it again before anything changed, **Then**
   no redundant reviewer calls are made (the existing verdicts are reused).
4. **Given** any pipeline pass that generates revision work-specs, **When**
   its progress is persisted, **Then** the revision artifacts are included
   in what gets committed (nothing generated is silently lost).

---

### User Story 2 - The research funnel flows (Priority: P1)

Brainstormed ideas must progress. Today 589 projects (85%) sit at the
fleshed-out-idea stage with effectively zero advancement, because scheduling
weight concentrates on late-stage projects (which, per Story 1, never
exited) and no scheduled job targets the idea-validation stage. After this
story, the idea queue demonstrably drains: ideas are validated (or honestly
rejected) at a rate that exceeds intake, and every pipeline stage receives
scheduled attention.

**Why this priority**: The research track is the project's core purpose;
85% of all projects are stuck at its entrance. Even with Story 1 fixed, the
funnel never fills the later stages without this.

**Independent Test**: Run the scheduler over the real project population
and verify pick distribution gives the idea-validation backlog meaningful
coverage; run scheduled passes and verify the fleshed-out queue shrinks
(advancements + honest rejections > new intake) over a measured window.

**Acceptance Scenarios**:

1. **Given** the current population (hundreds at idea stages, dozens at
   paper review), **When** scheduled pipeline passes run for a day,
   **Then** idea-stage projects receive a substantial share of picks
   (not the current ~2%) and the fleshed-out queue trends down.
2. **Given** a fleshed-out idea that passes validation, **When** its next
   stages run, **Then** it proceeds through initialization and the
   specification stages without manual intervention.
3. **Given** continued hourly idea intake, **When** drain rate is below
   intake rate, **Then** intake is automatically throttled until the queue
   trends down (no unbounded backlog growth).

---

### User Story 3 - One project, every phase, to a published paper (Priority: P1)

A maintainer can point to at least one project that started as a
brainstormed idea and finished as a published paper with a DOI — having
genuinely passed through every lifecycle phase: idea flesh-out and
validation, project initialization, specification, clarification, planning,
task breakdown, analysis, implementation, research review, paper drafting
(spec/clarify/plan/tasks/write), paper review with convergence, publication
sign-off, and posting. Every stage's artifacts are high quality, produced
by the pipeline itself (no hand-edited content), with the full transition
history and review provenance on record.

**Why this priority**: This is the product. It is the maintainer-stated
outcome of the feature and the only honest proof that the pipeline is
"100% functional": every phase exercised for real, in sequence, on the same
project.

**Independent Test**: Inspect the completed project's recorded stage
history: it contains every phase in order (kickbacks/retries permitted) and
terminates at the published state; the published artifact (PDF + DOI +
publication record) exists; each stage's artifacts pass that stage's
quality gates; no content artifact was manually edited.

**Acceptance Scenarios**:

1. **Given** a brainstormed idea, **When** the pipeline runs it through all
   phases (with bounded automatic kickback/retry loops as designed),
   **Then** the project reaches the published state with a minted DOI and a
   compiled, audit-passing paper.
2. **Given** any stage in the traversal produces a defective or low-quality
   artifact, **When** the defect is observed, **Then** the responsible
   stage (its code/prompts/gates) is fixed generally and the stage re-run —
   the defect is never patched by hand-editing the artifact and never
   deferred.
3. **Given** the completed traversal, **When** a maintainer reviews the
   project's history, **Then** every phase transition, review verdict,
   kickback, and sign-off is present and attributable.

---

### User Story 4 - Humans are asked rarely, and asked well (Priority: P2)

Routine human escalation is a deal-breaker for an automated-science system.
Projects must stop parking themselves in a human-input state for situations
automation can handle: an idea judged infeasible must be automatically
archived and re-brainstormed with the feasibility constraint applied (with a
bounded retry count before honest termination to a rejected/backlog state);
infrastructure outages must never escalate (retry later instead); genuine
engine failures must file a tracked issue automatically rather than silently
parking the project. When a bounded automated loop is truly exhausted, the
escalation must carry evidence that automation was exhausted, and such
escalations are surfaced as a periodic digest rather than per-project
stalls.

**Why this priority**: Maintainer-stated requirement ("human decisions can
be requested *rarely*"). Three projects are currently parked on an
instruction the system itself printed and could have executed.

**Independent Test**: Re-run the three currently-parked "idea out of
feasible scope" projects through the new automation and verify they
re-brainstorm (or honestly terminate) without human input; audit every code
path that can park a project for a human and verify each is either (a)
removed/automated, (b) bounded-with-evidence, or (c) the sanctioned
publication sign-off gate.

**Acceptance Scenarios**:

1. **Given** a flesh-out verdict of "infeasible for the execution
   environment", **When** the verdict lands, **Then** the idea is archived
   and a constrained re-brainstorm is produced automatically; after N
   failed regenerations the project is honestly terminated to the backlog,
   never parked for a human.
2. **Given** a model/endpoint outage of any shape (single model, full
   chain, mid-call), **When** a pipeline step fails on it, **Then** the
   project stays at its current stage for a later retry — never a human
   escalation (extends the fix landed in PR #302).
3. **Given** an unexpected engine failure, **When** it would previously
   have parked the project, **Then** a tracked issue is filed automatically
   with the failure evidence and the project remains schedulable once the
   issue is resolved.
4. **Given** the steady state after this feature, **When** the
   human-escalation population is measured, **Then** it is approximately
   zero outside the sanctioned publication sign-off gate.

---

### User Story 5 - Publication sign-off by lightweight maintainer vote (Priority: P2)

The one sanctioned human decision is publication: before a DOI is minted,
maintainers get an easy up/down call. When a paper has passed every
automated check, the system opens a tracking issue tagging all maintainers
with links to the paper and a one-glance summary, and maintainers decide by
emoji reaction (or a short command comment). The system parses the
responses automatically: approval proceeds to mint the DOI and publish;
rejection routes the stated reason back into the revision loop; no response
triggers periodic reminders without blocking the rest of the pipeline.
The issue itself becomes the durable sign-off record.

**Why this priority**: Maintainer-specified exception and design. Required
for Story 3's final step (nothing can post without sign-off), but
independent machinery.

**Independent Test**: Drive a paper to the sign-off stage in a test
context; verify the issue is opened with the correct content and tags;
apply an approval reaction with a maintainer account and verify the
publisher proceeds and the issue closes with the DOI; apply a rejection
comment on another run and verify the reason enters the revision loop.

**Acceptance Scenarios**:

1. **Given** a paper reaching sign-off with all checks green, **When** the
   gate activates, **Then** an issue is opened tagging all maintainers with
   the artifact links, summary, and voting instructions.
2. **Given** an approval reaction/comment from a maintainer, **When** the
   parser runs, **Then** the DOI is minted, the publication record written,
   the project posted, and the issue closed with the DOI.
3. **Given** a rejection with a reason, **When** the parser runs, **Then**
   the reason is converted to review feedback and the paper re-enters the
   revision loop.
4. **Given** a non-maintainer reaction, **When** the parser runs, **Then**
   it is ignored for decision purposes.
5. **Given** no maintainer response, **When** the reminder window elapses,
   **Then** a reminder is posted and the project keeps waiting without
   consuming scheduler capacity.

---

### User Story 6 - The public paper shelf is trustworthy (Priority: P3)

Every paper shown on the public site either passed the full
restyle-compile-audit chain or is clearly marked otherwise. Today 18 of 94
papers silently fall back to the original un-restyled PDF with no recorded
reason, and only 2 restyled PDFs pass the rendering-quality audit; there is
no repair loop. After this story, restyle/compile failures leave a
machine-readable failure report that feeds a bounded automatic repair loop
(reusing the revision machinery), the audit's defect findings likewise feed
repair, and the site distinguishes audited papers from fallbacks.

**Why this priority**: Usefulness/credibility of the public output surface.
It does not block the end-to-end traversal (Story 3 needs only its own
paper to pass), so it follows the P1/P2 work.

**Independent Test**: Force a restyle failure and verify a failure report
artifact is persisted and a repair round is generated; run the audit on a
defective PDF and verify defects convert to repair work; verify the site
data marks each paper's status accurately.

**Acceptance Scenarios**:

1. **Given** a paper whose restyle/compile fails, **When** the compile job
   finishes, **Then** a per-paper failure report (reason + stage) is
   persisted instead of a silent fallback, and a bounded repair round is
   scheduled.
2. **Given** a compiled PDF with audit defects, **When** the audit runs,
   **Then** the defect list is converted into repair work and the paper is
   re-audited after repair.
3. **Given** the public site data, **When** it is regenerated, **Then**
   each paper's entry reflects its true status (audited / restyled-unaudited /
   fallback-original) with zero unmarked fallbacks.

---

### Edge Cases

- A paper-review verdict set is complete but computed against a stale
  artifact version (artifact changed after reviews): the evaluator must
  treat it as stale and request re-review of the changed artifact only —
  never accept or revise based on stale verdicts, and never loop without
  recording why.
- Two scheduled jobs (or a scheduled job and a manual dispatch) process the
  same project concurrently: per-project locking must hold across the new
  dedicated lanes; the loser retries later without corrupting state.
- A revision round itself fails repeatedly (implementer cannot satisfy the
  work-spec): the bounded kickback/escalation discipline applies — after
  the cap, the project takes the honest terminal route (fundamental-flaws /
  backlog) rather than looping or parking silently.
- The sign-off issue is edited, deleted, or receives conflicting reactions
  (approve and reject from different maintainers): the parser must apply a
  defined precedence (any maintainer rejection blocks; record the conflict
  in the issue) and never double-mint a DOI.
- DOI minting succeeds but the final state write fails (or vice versa):
  publication must be idempotent and resumable — re-running the publisher
  must not mint a second DOI and must converge to a consistent posted
  state.
- The end-to-end demonstration project hits the kickback cap legitimately
  (real unresolvable content concern): that is a correct bounded outcome —
  the demonstration must then proceed with a different project, while the
  capped project's terminal state is verified to be honest and evidenced.
- Intake throttling (Story 2) must not starve legitimate new submissions
  permanently: throttling is proportional and recovers when the queue
  drains.
- The fleshed-out queue contains hundreds of pre-existing ideas of varying
  quality: validation at scale must reject weak ideas honestly (negative
  control: a weak idea is rejected, not rubber-stamped through).

## Requirements *(mandatory)*

### Functional Requirements

**Review-decision persistence and consumption (US1)**

- **FR-001**: Every advancement decision made for a project under review
  (paper or research track) MUST be durably persisted in the project's
  saved state — including the revision work-spec reference when the
  decision is "needs revision" — such that the decision survives the end of
  the pipeline pass.
- **FR-002**: A project whose saved state carries an unconsumed revision
  work-spec MUST have the revision implementer (not reviewers) dispatched
  on its next scheduled pick, and the implementer MUST consume exactly that
  work-spec.
- **FR-003**: All artifacts generated during a pipeline pass — including
  revision work-specs — MUST be included in the pass's persisted/committed
  output. A pass MUST NOT generate durable-intent artifacts that are then
  excluded from persistence.
- **FR-004**: When a complete, current (non-stale) verdict set already
  exists for a project under review, the pipeline MUST NOT re-dispatch
  reviewers for that artifact version; it MUST proceed directly to
  evaluation of the existing verdicts.
- **FR-005**: A paper whose every required specialist's most-recent
  non-stale verdict is "accept" (with no blocking citation or unresolved
  markers) MUST advance out of review toward publication sign-off in the
  same pass that observes this condition.

**Funnel throughput and fairness (US2)**

- **FR-006**: The scheduler MUST give every active (non-terminal,
  non-human-gated) stage a non-vanishing share of picks: stage preference
  weighting MUST be counterbalanced by queue depth and/or time-since-last-
  attention so that no stage with eligible projects receives a near-zero
  share over a day of scheduled passes.
- **FR-007**: The idea-validation backlog (fleshed-out ideas awaiting
  validation) MUST receive dedicated scheduled coverage (its own lane or an
  explicitly targeted share), sized so that sustained drain rate can exceed
  current intake rate.
- **FR-008**: New-idea intake MUST be automatically throttled when the
  idea-stage backlog is growing (drain < intake), and automatically resume
  as the backlog drains; throttling state MUST be observable.
- **FR-009**: Idea validation at scale MUST preserve honesty: weak ideas
  are rejected/kicked back per the existing convergence rules, and at least
  one deliberately weak idea MUST be observed taking the rejection path
  during validation of this feature (negative control).

**End-to-end traversal (US3)**

- **FR-010**: The pipeline MUST be able to take a single project from
  `brainstormed` through every lifecycle phase to `posted` without any
  human action other than the sanctioned publication sign-off, with all
  transitions recorded in the project's history.
- **FR-011**: Each stage of the traversal MUST produce artifacts that pass
  that stage's existing quality gates (claim verification, citation
  validation, convergence panels, compile/audit gates); any gate failure
  encountered MUST be addressed by fixing the responsible stage generally
  and re-running it — hand-editing pipeline-produced content artifacts to
  pass a gate is prohibited.
- **FR-012**: Any defect, bug, or quality problem discovered anywhere in
  the system while delivering this feature MUST be treated as in-scope:
  fixed generally (applying to all projects), with a regression test, in
  the same effort — not deferred, not worked around for the demonstration
  project only.
- **FR-013**: The demonstrated traversal MUST be reproducible end-to-end by
  the scheduled automation alone (cron-driven progression must be able to
  carry a comparable project through the same phases without manual
  dispatches being required for correctness — manual dispatches may
  accelerate but never substitute for broken automation).

**Escalation minimization (US4)**

- **FR-014**: A flesh-out "infeasible scope" verdict MUST trigger automatic
  idea archival and a constrained re-brainstorm; after a bounded number of
  failed regenerations the project MUST be honestly terminated to the
  backlog/rejected state. No human escalation on this path.
- **FR-015**: No infrastructure failure of any shape (single-model outage,
  full-chain outage, mid-call drop, rate limiting) may result in a human
  escalation; all MUST resolve to retry-later with state preserved.
- **FR-016**: Unexpected engine failures that previously parked a project
  MUST instead automatically file a tracked issue containing the failure
  evidence, leaving the project schedulable after the underlying fix.
- **FR-017**: Every remaining human-escalation writer MUST attach evidence
  that its bounded automated loop was exhausted (counts, rounds, last
  attempts); escalations MUST be aggregated into a periodic digest, and the
  steady-state escalation population (outside publication sign-off) MUST
  trend to approximately zero.
- **FR-018**: The three currently-parked "infeasible idea" projects MUST be
  re-processed through the FR-014 automation as part of delivery.

**Publication sign-off gate (US5)**

- **FR-019**: When a paper reaches the publication sign-off stage with all
  automated checks passing, the system MUST open a tracking issue that tags
  all maintainers, links the compiled paper and key artifacts, summarizes
  the work, and states the voting protocol (approve / reject with reason).
- **FR-020**: The system MUST automatically parse maintainer responses:
  approval from a maintainer proceeds to publication (DOI mint +
  publication record + posted state + issue closed with the DOI);
  rejection converts the stated reason into review feedback and re-enters
  the revision loop. Responses from non-maintainers MUST be ignored for
  decision purposes; any maintainer rejection takes precedence over
  approvals; decisions MUST be idempotent (no double-minted DOIs).
- **FR-021**: Absent a response, the system MUST post periodic reminders
  and keep the project parked without consuming scheduler capacity; the
  sign-off issue MUST serve as the durable, attributable sign-off record.

**Paper-shelf integrity (US6)**

- **FR-022**: Every restyle/compile failure MUST persist a per-paper,
  machine-readable failure report (stage + reason); silent fallback to the
  original PDF without a report is prohibited.
- **FR-023**: Rendering-audit defects and compile-failure reports MUST feed
  a bounded automatic repair loop; papers MUST be re-audited after repair.
- **FR-024**: The public site data MUST accurately reflect each paper's
  status (audit-passing / restyled-unaudited / original-fallback), with
  zero unmarked fallbacks.

### Key Entities

- **Project**: A unit of research work with a lifecycle stage, full stage-
  transition history, and links to its artifacts (idea, specs, plans,
  tasks, code, paper, reviews).
- **Review verdict set**: The per-specialist review records for a project's
  current artifact version; has staleness (artifact-hash currency) and
  completeness (all required specialists) properties that gate evaluation.
- **Revision work-spec**: The durable unit of "what must change", generated
  from non-accepting verdicts; carries rounds, is consumed by the revision
  implementer, and bounded by the kickback cap.
- **Escalation record**: Evidence-bearing record of an exhausted automated
  loop; aggregated into digests; approximately-zero steady state.
- **Sign-off issue**: The maintainer-facing publication vote (tagged
  maintainers, artifact links, parsed reactions/comments); the durable
  sign-off record tied to a minted DOI.
- **Paper status record**: Per-paper compile/restyle/audit outcome
  (passing, defect list, or failure report) surfaced on the public site.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least one project's recorded history shows every lifecycle
  phase from `brainstormed` to `posted`, terminating with a minted DOI and
  a compiled paper that passes the rendering audit — verified against the
  project's stage-transition history and publication record.
- **SC-002**: Papers with complete current verdict sets exit the review
  stage (accept, revision round, or honest terminal) — measured against the
  review-stage population and transition history, where the pre-feature
  baseline is zero exits ever.
- **SC-003**: The fleshed-out-idea backlog trends downward over a sustained
  scheduled-operation window (drain exceeds intake), measured against the
  recorded stage population over time, versus the pre-feature baseline of
  ~zero advancement per day.
- **SC-004**: Redundant review work is eliminated: scheduled passes no
  longer re-dispatch reviewers against unchanged artifacts with complete
  verdict sets — measured against the run log, where the pre-feature
  baseline is ~83% of all agent runs.
- **SC-005**: The steady-state human-escalation population outside the
  publication sign-off gate is approximately zero, and every escalation
  that does occur carries machine-checkable exhaustion evidence — measured
  against the escalation records after the de-escalation automation lands.
- **SC-006**: A maintainer can complete a publication decision end-to-end
  (vote on the sign-off issue → automatic publication or routed rejection)
  with a single reaction or short comment — verified by a real sign-off
  round-trip.
- **SC-007**: The public paper shelf contains zero silent fallbacks: every
  paper entry's displayed status matches its actual compile/audit outcome —
  verified by cross-checking site data against the per-paper status
  records.
- **SC-008**: The full offline and real-call verification gates pass with
  the feature's regression tests included, with zero failures — measured
  against the repository's existing test gates.

## Assumptions

- The existing lifecycle stage machine, convergence protocol (unanimous
  panel within the 3-round cap, spec 015), claim-verification stack (specs
  016–020), and per-project locking are sound and remain the foundation;
  this feature repairs flow *through* them rather than redesigning them.
- The existing free-model backends (with the credit-managed opt-in from
  spec 022 available where already sanctioned) provide sufficient quality
  for every stage; if a stage proves quality-limited, fixing that stage
  (prompts/gates/models within sanctioned policy) is in scope per FR-012.
- Zenodo (or the already-integrated DOI provider, sandbox where
  appropriate for tests) remains the publication channel; a sandbox DOI is
  acceptable for test runs, and the demonstration project's real DOI mint
  goes through the sanctioned sign-off gate.
- "Maintainers" are the repository's collaborators with write access (or
  an explicitly configured list); the sign-off parser validates voter
  identity against that list.
- The demonstration project may be any genuinely pipeline-generated idea
  (including PROJ-552, currently mid-traversal at planning, if it
  converges); the negative-control weak idea may be drawn from the
  existing backlog.
- The end-to-end traversal is wall-clock long (multi-day across scheduled
  passes); delivery includes monitoring it to completion, not just landing
  the code.
- GitHub remains the platform for issues, reactions, scheduled jobs, and
  the public site; per-stage scheduled lanes continue to run within the
  existing CI budget model.
