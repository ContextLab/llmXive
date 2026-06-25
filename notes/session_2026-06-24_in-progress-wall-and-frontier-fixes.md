# Session 2026-06-24 — the universal in_progress wall + frontier-failure fixes

## Goal (standing)
≥1 project brainstorm→complete-paper via the **fully automated** pipeline.
General fixes only — never one-off unsticking. Keep the unanimous-accept review
gate; make reviews reliable, do NOT lower the bar. Never drive a real project's
redo LOCALLY (corrupts its artifacts + tangles with CI) — operational recovery
+ committing agent output is fine; fixing platform/agents is the job.

## The decisive diagnosis (run-log + state analysis, not guessing)
Population = 784 projects. Stage distribution showed a hard cliff:
`validated 414 · project_initialized 69 · specified 13 · clarified 1 ·
in_progress 2 · {planned/tasked/analyzed/research_*/paper_*} = 0`.
(112 `paper_review` are the **arXiv-restyle** track — they START as papers, so
they do NOT prove the brainstorm→paper pipeline.)

**Zero projects had EVER crossed `in_progress` → research_complete.** That is the
universal wall. Root-caused it to TWO compounding structural facts (NOT a crash):
1. the speckit `ImplementerAgent` (implement_cmd.py) checks off **one task per
   run**; a research project carries 50–60 tasks (PROJ-261 = 3/55 done, PROJ-262
   = 5/57 done, both ~50 days old);
2. the load-balanced scheduler (scheduler.py `_stage_weights_with_floor`) drives
   every stage to an EQUAL share, so a 2-project in_progress queue gets only the
   `MIN_STAGE_SHARE`=5% floor while 414 validated-stage projects dominate.
One-task/tick × rarely-picked ⇒ months to drain in_progress ⇒ never happened.

Frontier-agent failures (run-log, last 250 runs) confirmed the agents ARE
scheduled but fail: implementer 26/37, clarifier 5/7, planner 4/5, tasker 1/1.
- implementer: 13× `FileNotFoundError: lualatex`, 11× `ValidationError
  ImplementerLogEntry after_hashes=''`, 2× round-already-recorded.
- clarifier/planner/tasker: mostly `StagePanelKickback: did not converge` =
  GENUINE methodology blocks on pre-FIX-#14 specs (e.g. PROJ-552 braid-index `b`
  collinear with crossing number `c`) — CORRECT to block; not a bug.
- 1× planner `PlanReviser` emitted `{responses:[...]}` (Part-1 change-log) with
  no `===BEGIN_ARTIFACT` Part-2 (truncation) → escalation. Infra
  (GENERATION_MAX_TOKENS + run_pass_with_artifact_retry) already exists; deferred
  as low-freq.

## Fixes shipped this session (all on origin/main, suite green 2533)
- **#16** `90640330c` reviews: parser tolerates a JSON-emitted review object
  (verdict-gated) + shared R3 contract forbids echoing the reviser `responses`
  format (deterministic temperature=0 made the mis-format recur permanently).
- **#17+#18** `1339ecf3c` implementer: `EditResult.__post_init__` drops any
  before/after hash entry that isn't 64-hex (one bad hash crashed the whole round
  → bricked PROJ-552); `_compile_paper` guards `shutil.which("lualatex")` →
  DEFER (keep the edit) instead of FileNotFoundError/rollback.
- **#19** `f0b99eeac` pipeline: **implement-stage BATCHING** — `run_one_step`
  drains up to `IMPLEMENT_TASK_BATCH`=12 tasks/tick within
  `IMPLEMENT_BATCH_BUDGET_SECONDS`=600s wall-clock + strict progress guard
  (remaining-task count must fall each pass, else stop — no spin). Both
  research (`implementer`@ANALYZED/IN_PROGRESS) and paper
  (`paper_implementer`@PAPER_ANALYZED/PAPER_IN_PROGRESS). THE linchpin fix.
  Tests: tests/unit/test_implement_batching.py (drain N, cap, no-progress guard).
- **#20** `4516ac937` ci: `scripts/ci/install-texlive.sh` SSoT for the LaTeX
  package set; paper-compile.yml / pipeline-paper-write.yml / pipeline-review.yml
  all call it (they had DIVERGED — only paper-compile carried
  texlive-plain-generic = soul.sty/ulem.sty → "soul.sty not found" in the other
  lanes).
(Earlier today, pre-this-session-window: #1–#15 reviewer-reliability +
generation-methodology (#14 specifier/planner rigor) + #15 empty-reply retry.)

## Why I did NOT touch the scheduler
The load-balancer is explicit "user policy". Batching (#19) multiplies per-tick
throughput WITHOUT changing the policy: in_progress still gets ~3.8% of picks,
but each pick now drains ~12 tasks. ~200 ticks/day × 3.8% ≈ 8 in_progress
picks/day × 12 = ~96 task-completions/day → 261/262 (~110 tasks total) drain in
~1 day. The review stages have no throughput wall (LLMXiveImplementer processes
ALL action-items per run).

## Verified facts
- execute_and_gate WORKS: only execution_status record is PROJ-552 = ok=True
  (it crossed in_progress when driven locally; kicked back to `specified` on
  GENUINE science, not an execution failure). So in_progress was purely a
  throughput wall.
- STAGE_TO_AGENT: IN_PROGRESS→"implementer"→speckit ImplementerAgent (initial
  impl). LLMXiveImplementer ("llmxive_implementer") is the REVISION implementer;
  it SKIPS non-review stages (only PAPER_REVIEW/RESEARCH_REVIEW/AGENT_BLOCKED).

## Realistic path to the goal now
in_progress (FIX #19 batching) → execute_and_gate → research_complete →
research_review (reliable panels + LLMXiveImplementer revisions, #17/#18) →
research_accepted → paper pipeline (paper_implementer batched too, #19) →
paper_complete (compile, #20 + #18 defer). 261/262 are standard empirical-ML
studies (code-duplication impact; dipole-moment GNN) — simpler science than
knot-theory collinearity → best goal candidates.

## Next actions / how to resume
- MONITOR CI: watch for the FIRST in_progress→research_complete crossing
  (261/262). Triggered pipeline-implement.yml run 28125238007 (2026-06-24
  19:47Z) to exercise batching; natural crons (implement /8h, main /3h,
  brainstorm /1h) will drain in_progress within ~1 day.
- If a NEW failure mode surfaces in run-logs, fix the platform/agent generally.
- Do NOT drive 261/262's in_progress LOCALLY (writes their project artifacts →
  tangles with CI). Validate via CI or a hermetic synthetic repo
  (LLMXIVE_REPO_ROOT + LLMXIVE_REAL_TESTS=1 + Dartmouth key).
- Deferred general fix worth doing: PlanReviser/doc-reviser truncation
  robustness (Part-1 change-log first exhausts budget before Part-2 artifacts) —
  causes wasted convergence rounds on plan/tasks panels.

## UPDATE (later same session) — validated the wall break + found 2 MORE walls

The in_progress wall fix (#19) was VALIDATED end-to-end in real CI: a stage/
project-targeted implement run drained PROJ-262 from 5/57 → 57/57 tasks (real
analysis code, persisted). Two further GENERAL walls surfaced and were fixed:

- **FIX #22 (be858b7f7) — silent work-loss on push.** All 14 cron workflows used
  `git pull --rebase origin main && git push` in a retry loop. On the routine
  conflict (every tick regenerates web/data/projects.json) the rebase left the
  tree CONFLICTED, every retry died "unmerged files", the tick's work was LOST,
  and the step STILL exited 0 (masked). Replaced by SSoT
  `scripts/ci/commit-and-push.sh`: `git rebase -X theirs origin/main`
  (resolve toward this tick, no markers), abort-before-each-attempt, emit
  `pushed` for the pages gate, FAIL LOUD on total failure. 2-worker local test:
  both workers' distinct work preserved.

- **FIX #23 (this commit) — dep install aborted the whole analysis.** The
  crossing test (262 execute_and_gate) died `ModuleNotFoundError: numpy` — NOT
  compute. The missing-import self-heal (_declare_missing_imports) auto-added a
  LOCAL package (`models`=code/models/) and matplotlib's `mpl_toolkits`
  namespace submodule to requirements.txt as if PyPI packages; `pip install -r`
  then aborted the WHOLE batch → numpy never installed. Fix: `ensure_venv` now
  installs RESILIENTLY (batch, then per-package fallback so good deps land
  despite a bad line); `mpl_toolkits`→matplotlib mapped. Unblocks
  execute_and_gate for every project without touching project artifacts.

### Operator capabilities added (general, for validation)
- pipeline-implement.yml: `stage` + `project` + `max_tasks` workflow_dispatch
  inputs (focused advance pass). llmxive-pipeline.yml ALREADY had project_id +
  stage (330-min lane — the right lane for execute_and_gate, whose run_analysis
  deadline is 5h; the 50-min implement cron only DRAINS tasks).

### Where 262 stands / next
262 = 57/57 tasks, stage=in_progress, execution_status ok=false fix_rounds=4/12
(burned on the now-fixed dep issue; 8 left). NEXT: push #23, then re-trigger
`gh workflow run llmxive-pipeline.yml -f project_id=PROJ-262-...` → fresh venv →
resilient install lands numpy/torch/rdkit/... → analysis runs (QM9 download +
GNN ≤50 epochs on a subset; heavy but within 330 min) → if ok → research_complete
(FIRST in_progress crossing). 262's analysis is compute-heavy; if it stalls on
QM9/GNN, a lighter project is the better goal candidate (the now-unblocked
pipeline will surface one). Commits this session: ~27.

## UPDATE 2 — the crossing's REAL limit: analysis-code quality, not a platform bug

After #23 (deps) + #24 (DATA-contract ground-truth) + #25 (regression flagging)
+ a fix-round budget RESET, PROJ-262 STILL does not converge execute_and_gate.
Errors evolve but whack-a-mole across LAYERED cross-file data contracts:
- train_rf.py: "Processed data must contain a 'dipole' column" (preprocess↔train
  contract)
- generate_performance_plots / generate_significance: "Metrics CSV missing
  columns {model, rmse, mae}" (evaluate↔plots contract)
- generate_summary: cascade (results/significance.csv absent)
The implementer fixes one stage's columns and another stage's break resurfaces.

DIAGNOSIS: 262's analysis (GNN + RandomForest + ~10 interdependent scripts) was
generated task-by-task with INCONSISTENT column/path contracts between stages.
The bounded auto-fix loop — even with the improved feedback — can't converge a
deeply-tangled multi-file analysis; it correctly heads toward escalation rather
than thrashing forever. This is a project CODE-QUALITY limit, NOT a general
platform bug. 262 is NOT a viable goal candidate.

### The path to the goal from here
The STRUCTURAL blockers (the reason NO project ever crossed in_progress) are all
removed + validated: batching (#19), robust push (#22), resilient deps (#23),
DATA-contract + regression fix-loop feedback (#24, #25). A SIMPLER project (fewer
analysis stages → fewer cross-file contracts) will converge and cross via the
now-unblocked natural crons. Candidates: 261 (code-duplication, lighter analysis,
at 15/55 tasks) or fresh projects flowing brainstorm→...→in_progress.

### NEXT GENERAL LEVER (for a future session) — generation-quality, not a bug
Complex analyses fail to converge because the implementer writes each stage's
script with its OWN column/path names, with no enforced SHARED SCHEMA. The
speckit pipeline already produces data-model.md; the lever is to make the
implementer (and the execution feedback) treat data-model.md's column/artifact
schema as the CANONICAL contract every script must adhere to — so intermediate
CSV columns are consistent producer↔consumer by construction. This is a
generation-quality effort (planner/implementer prompts + schema enforcement),
larger than a bug fix; deferred deliberately rather than rushed.

### STOP forcing 262
Do NOT keep throwing CI runs / fix-loop tweaks at 262 (diminishing returns on a
code-quality-limited project). Let the population flow; drive/observe a simpler
project for the first crossing. Commits this session: ~33.
