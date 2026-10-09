# Implementation exhaustion dispatched the wrong recovery agent

On main `8b7ec564bfd`, both research implementation recovery branches wrote a
planner-directed `kickback_feedback.md` after exhausting the model ladder, then
returned `Stage.PLANNED`. The dispatch table maps that stage to **TaskerAgent**;
**PlannerAgent** runs at `Stage.CLARIFIED`. Thus the documented attempt to change
the failed approach regenerated tasks without rerunning the planner. This
matches the repeated retasking observed in the isolated runs tracked by #1139,
but the code defect alone does not prove the cause of every added deliverable.

The two exhaustion branches now return `CLARIFIED`, and lifecycle validation
allows `IN_PROGRESS -> CLARIFIED`. The existing planner reads the persisted
feedback through `render_recent_comments_block`, includes the current spec and
prior planning documents in its prompt, and revises the existing plan. Its
normal convergence/revision path remains responsible for accepting the plan or
requesting an earlier specification correction. Once planning converges, the
normal `PLANNED -> tasker` dispatch generates tasks from that revised plan.

This preserves model escalation, free-only verifier retries, paid opt-in guards,
replan counts, the terminal blocked cap, and final execution/review gates.
Malformed task syntax still routes to `PLANNED`: the tasker owns that repair.
Other convergence, legacy human-marker, and paper recovery routes are outside
this focused change and retain their previous behavior. No existing scientific
project state or artifact is edited by this patch.

Validation:

- 48 focused tests passed across exhaustion, planner inputs, recovery, and
  persistent verifier feedback.
- Both new regression cases fail on the original source (wrong `PLANNED`
  destination) and pass with this change.
- The new tests use real execution/unverifiable stores, persist the recovered
  project, invoke `run_one_step`, and run the actual planner's mechanical step
  and prompt builder. They verify the exact saved rejection/run diagnosis and
  unchanged spec/prior plan reach the planner. They stop at the model boundary;
  no model-generated plan, scientific acceptance, or full-pipeline success is
  claimed by these tests.
