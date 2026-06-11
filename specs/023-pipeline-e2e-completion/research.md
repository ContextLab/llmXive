# Phase 0 Research: Pipeline End-to-End Completion

**Date**: 2026-06-10 | **Feature**: [spec.md](spec.md)

All root causes below were verified empirically against the live repository
during the issue-#303 audit (2026-06-10) — by reading the cited code, by
querying the canonical state (`projects/`, `state/run-log/`), and in the
decisive case by executing the evaluator directly against a real stuck
project. Nothing here is inferred from memory.

## R1. Why no paper has ever been accepted: the discard bug

**Decision**: Fix `src/llmxive/pipeline/graph.py` so the advancement
evaluation's full result is saved and committed, not reduced to a stage
name.

**Evidence**: `graph.py:726-728` handles `PAPER_COMPLETE`/`PAPER_REVIEW`
as:

```python
evaluated = advancement_evaluate(project, repo_root=repo_root)
return evaluated.current_stage
```

`advancement.evaluate` (`agents/advancement.py:470-640`) works correctly:
it applies the all-specialists-accept gate (with live artifact-hash
staleness checks), severity-routes concerns into a `KickbackRecord`,
generates a revision work-spec via `kickback_to_revision_spec`, and returns
a `model_copy` of the project carrying `revision_spec_path` — but it does
**not** save; the caller keeps only `.current_stage`. The work-spec
reference and any stage decision are discarded every tick. The same shape
exists at `graph.py:722-724` for `RESEARCH_COMPLETE`/`RESEARCH_REVIEW`.
Proof the evaluator is sound: running it directly on PROJ-565 produced a
round-1 revision spec instantly (artifacts then reverted — diagnostic
only). Consequences in canonical state: zero `paper_accepted` transitions
ever; only PROJ-578 ever carried a `revision_spec_path` (from a manual
run); 92 papers loop at review; ~83% of June agent runs were reviewer
re-dispatches against unchanged artifacts.

**Rationale**: The downstream machinery already exists and is gated only on
the discarded field — `agents/implementer.py:343-354` dispatches the
revision implementer for `{PAPER_REVIEW, RESEARCH_REVIEW, AGENT_BLOCKED}`
*only when* `project.revision_spec_path` is set. Persisting the evaluated
project (and gating reviewer fan-out on an existing current verdict set)
completes the severed link with minimal new surface.

**Alternatives considered**: (a) Have `evaluate` save internally — rejected:
it would hide a state write inside a pure-looking evaluator and diverge
from how every other graph node persists (the graph saves);
(b) re-architect review dispatch — rejected: spec assumes the convergence
machinery is sound; only the persistence link is broken.

## R2. Why revision work-specs would vanish even once persisted

**Decision**: Add `specs/` to every CI workflow persist step (currently
`git add state/ projects/ web/data/`).

**Evidence**: Revision work-specs are written under
`specs/auto-revisions/<project>/...` (observed live when the evaluator ran:
`specs/auto-revisions/PROJ-565...` plus `upstream_feedback.yaml` and
`state/revisions/index.yaml`). The scheduled workflows' persist steps
enumerate paths and omit `specs/`, so even a fixed graph would commit the
project pointer but lose the work-spec body (FR-003 violation).

**Alternatives considered**: moving work-specs under `state/` — rejected:
they are speckit feature artifacts consumed as specs by the implementer;
relocation would touch many consumers for no benefit (Constitution I:
modify the persist list in place).

## R3. Why the funnel starves: scheduler weighting and lane coverage

**Decision**: Counterbalance the exponential stage preference with queue
depth and time-since-last-attention in `pipeline/scheduler.py`, and add a
dedicated scheduled lane for `flesh_out_complete` validation; throttle
hourly intake when drain < intake.

**Evidence**: `scheduler.py` weights stages by `STAGE_GROWTH_BASE **
stage_rank` with `STAGE_GROWTH_BASE = 1.5`; `paper_review` at rank 18 gets
≈1478× the weight of early stages, so 589 `flesh_out_complete` projects
(85% of the population) received ~2% of picks while 92 looping papers
absorbed the rest. Cron lane map confirms no lane targets
`flesh_out_complete`: `pipeline-brainstorm` (1h) and `pipeline-flesh-out`
(2h) both feed the queue's *intake* side; `pipeline-research-speckit` (4h)
runs the roulette with no `--stage`; nothing drains validation.
`STAGE_TO_AGENT[FLESH_OUT_COMPLETE] = "research_question_validator"`
(`graph.py:79`) — the drain agent exists and is simply never scheduled.

**Rationale**: Keeping a late-stage preference is correct (finish what's
started) — the defect is the *unbounded* exponent with no demand term. A
depth/staleness counterweight preserves the intent while guaranteeing
FR-006's non-vanishing share; the dedicated lane gives FR-007's sized
drain; intake throttling (FR-008) closes the loop against unbounded
backlog growth.

**Alternatives considered**: flat uniform sampling — rejected (late-stage
projects would thrash and WIP would explode); per-stage round-robin only —
rejected (ignores queue depth, starves deep queues the same way).

## R4. De-escalation: which human-input paths exist and what replaces them

**Decision**: Replace each non-sanctioned `human_input_needed` writer with
bounded automation; the only sanctioned human gate is publication sign-off.

**Evidence**: Audit of escalation writers (issue #303 findings 4/5):
(a) flesh-out "idea out of feasible scope" verdicts park the project with
an instruction the system itself printed — three live projects (PROJ-545,
PROJ-553, PROJ-557) are parked exactly there; (b) infrastructure outages
escalated via the generic engine-failure handler until PR #302's router
fix (`saw_transient` → `BackendUnavailable`, commit 4daafe58) made
all-transient chain exhaustion a clean abort — the remaining shapes
(rate limiting, mid-call drops) must be classified the same way;
(c) unexpected engine failures park projects silently with no tracking
artifact.

**Replacement design**: (a) archive idea + auto re-brainstorm with the
feasibility constraint injected into the prompt, bounded retry count, then
honest terminal to backlog/rejected (FR-014, re-run the three parked
projects per FR-018); (b) all infra failures → retry-later, state
preserved (FR-015, extends PR #302); (c) engine failures → auto-file a
tracked GitHub issue with evidence, project stays schedulable (FR-016);
(d) any surviving escalation writer must attach exhaustion evidence and
feed a digest (FR-017).

**Alternatives considered**: a global "never escalate" switch — rejected:
honest bounded terminals require evidence-carrying escalation as the last
resort; the goal is *rare and well-evidenced*, not impossible.

## R5. Publication sign-off and DOI minting

**Decision**: Implement the maintainer vote as a GitHub issue + reaction/
comment parsing, polled by a scheduled lane; publication flows through the
existing `pipeline/zenodo.py` + `agents/publisher.py` with idempotence
keyed on a stored deposition/DOI record. Zenodo sandbox for tests; the
real mint only after a real maintainer approval.

**Evidence**: The lifecycle already defines
`awaiting_publication_signoff` and `speckit/_publication_signoff.py`
exists as the gate's stub-stage; `pipeline/zenodo.py` and
`agents/publisher.py` exist but have never been exercised to `posted`
(zero `posted` transitions in canonical state). No webhook receiver exists
anywhere in the platform — all GitHub interaction is via Actions cron +
REST, so polling matches the platform (Constitution IV: no new hosted
service).

**Vote protocol** (maintainer-specified): issue tags all maintainers with
artifact links + summary; 👍 reaction or `approve` comment from a
maintainer approves; 👎 or `reject: <reason>` rejects, reason routed into
the revision loop; non-maintainer responses ignored; any maintainer
rejection takes precedence; decisions idempotent (no double mint);
reminders on silence; the issue is the durable sign-off record.

**Alternatives considered**: GitHub webhook + server — rejected (paid/
hosted surface, Constitution IV); PR-based approval — rejected (heavier
than the maintainer's requested one-reaction flow).

## R6. Paper-shelf integrity: failure reports, repair loop, honest status

**Decision**: Persist a machine-readable per-paper status record at every
compile/restyle/audit outcome; convert audit defects and compile failures
into revision work (reusing the US1 revision machinery) with a bounded
repair loop; make `web_data.py` surface the true status.

**Evidence**: The paper-compile lane (30 min cadence) silently falls back
to the original un-restyled PDF on failure — 18 of 94 shelf papers are
unmarked fallbacks with no recorded reason; the rendering audit
(`src/llmxive/audit/`) finds defects (only 2 restyled PDFs currently pass)
but nothing consumes its findings; `web/data/projects.json` (built by
`web_data.py`) carries no compile/audit status distinction.

**Alternatives considered**: a separate repair agent family — rejected
(Constitution I: the revision work-spec machinery from US1 is the
canonical "what must change" carrier; repair is a producer of work-specs,
not a new consumer).

## R7. Demonstration project and traversal monitoring

**Decision**: PROJ-552 is the designated demonstration project
(Clarification 2026-06-10), continuing from its current planning-stage
position; its recorded history already contains the earlier phases with
real kickback/recovery evidence (13-concern methodology kickback, 4-round
trail, kickback cap 1/3). If it hits an honest bounded terminal, a
substitute pipeline-generated project completes the demonstration (spec
Edge Cases). The traversal is multi-day across scheduled lanes; delivery
includes monitoring to `posted` (reconciliation dispatch 27315363219 was
in flight at plan time).

**Paid-model ladder** (Clarification 2026-06-10): fix prompts/gates first;
a specific agent may flip to `paid_opt_in` within the daily credit budget
(guard from PR #302, `backends/credits.py`) with a written
Constitution-IV justification per flip; free remains the default.

## Resolved unknowns

Technical Context contains no NEEDS CLARIFICATION markers; both spec-level
clarifications (paid-flip policy, demonstration project) were resolved in
the 2026-06-10 clarify session and are reflected above.
