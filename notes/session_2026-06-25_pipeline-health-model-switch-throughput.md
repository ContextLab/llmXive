# Session 2026-06-25 — pipeline health audit, qwen model switch, throughput, GPU research

## Goal (unchanged)
≥1 brainstorm-origin project goes brainstorm → paper_complete via the fully
automated pipeline (demonstrate ALL phases work). Driver candidate: **PROJ-492**
(statistical p-value validity — CPU-tractable SciPy stats). Make GENERAL fixes
only; never hand-edit a project's own artifacts.

## Where 492 is
Crossed the **spec gate** and **plan gate** earlier (run 17: spec-020 [20,19,2,0]→0,
plan-006 [8,8,8,0]→0). Now cycling clarified↔planned↔tasked on qwen. The two
hardest convergence walls are solved; the **untested frontier** is the late half
(research_complete → research_review → research_accepted → paper_* → paper_complete
→ posted) — NO genuine project has ever reached it. `in_progress`/execute_and_gate
is the wall (262 failed it on its own broken generated code; 262/261 are GPU
dead-ends — see issue #367).

## Fixes shipped this session (all on main, all projects)
- **#42** coerce_severity: panels emitting generic severities ('low'/'overreach'/…)
  no longer crash the stage panel (map into the safe in-place-revision band).
- **#43 (+#43b)** MODEL SWITCH: default gpt-oss-120b → **qwen.qwen3.5-122b** for all
  52 agents; fallback chain qwen→gemma-3-27b→gpt-oss→claude-haiku(PAID, guarded);
  `LLMXIVE_PAID_OPT_IN=1` + `LLMXIVE_PAID_BUDGET_FRACTION=0.9` (~$1.8/day, $0-cost
  renewing credits) across all 10 agent workflows. Fixed the "tons of job failures"
  (gpt-oss was hanging). User-authorized ($2/day haiku).
- **#44** strip a leading ```yaml/```json review fence before frontmatter parse
  (qwen wraps + truncates its review output). Verified recovers truncated cases.
- **#45** per-run WALL-CLOCK BUDGET in `_cmd_run` (`LLMXIVE_RUN_WALL_BUDGET_S`,
  default 16200s=270min < 330min CI timeout): slow qwen runs now commit progress
  before the job timeout instead of losing the whole run's work.
- Constitution **1.1.0 → 1.2.0**: codified the two-tier acceptance bar already in
  engine.py (review stages strict / doc stages writing-residue-OK; science gate
  unchanged). Docs aligned: README (was #43), web/index.html about page, CLAUDE.md.

## Verified pipeline-health truth (direct evidence; the 4 deep-dive agents over-reported from PRE-FIX logs)
- Severity crash #361 ('overreach') = FIXED by #42 (fired 08:13 UTC, fix pushed
  11:32 UTC — stale). CLOSED #361.
- qwen frontmatter crash = FIXED by #44 (tested recovers truncated-in-fence + json).
- ```json fences = handled (reviewer JSON fallback + reviser BEGIN_ARTIFACT markers).
- Convergence oscillation = BOUNDED by CONVERGENCE_KICKBACK_CAP=3 (per-stage,
  escalates when exceeded) — NOT infinite. My earlier manual resets were legit
  post-fix recovery. With bugs fixed, no oscillation change warranted.
- Compute/GPU dead-end routing ALREADY exists: `_COMPUTE_INFRA_RE` in
  execution/stage.py re-scopes bitsandbytes/cuda/OOM failures to CPU.
- #360/#355 (open) = rare gpt-oss-era model-FORMAT-confusion glitches, not systematic.

## Model reality (DATA — see memory dartmouth-model-catalog-2026-06)
qwen is healthy (probe 4-7s) but a multi-gate run = ~1-4.3h (reasoning CoT volume,
not flapping; run 20 ~50min, run 21 ~4.3h+). **Decision: KEEP qwen for reviews.**
Experiment on 492's spec: qwen 61s → major_revision/4 concerns (rigorous) vs gemma
3s → accept/1 concern (LENIENT). Swapping reviews to gemma would LOWER the quality
bar — rejected. #45 (wall budget) is the quality-preserving throughput fix.

## GPU research → issue #367 (documented, NOT implemented)
Viable free + ToS-permitted + CI-automatable paths EXIST: **Kaggle Notebooks**
(free `kaggle kernels push/status/output` API, ~30 GPU-h/wk) and **Modal** ($30/mo
recurring free credit, headless). NOT implemented because: not goal-critical (492
is CPU), CPU re-scoping is the strategy (#27), 262's science is fabricated anyway,
substantial scope, + 2 unverified ToS gaps. Colab=ToS-prohibits-automation;
GitHub GPU runners=paid; Discovery=Duo-VPN+academic-AUP blocked; k8s=over-engineered.
Kaggle-first design captured in #367 if ever greenlit.

## NEXT STEPS (resume here)
1. Check run 21 (id 28172154275) outcome; push #45 once suite green.
2. Keep driving 492 forward (`gh workflow run llmxive-pipeline.yml --ref main -f
   project_id=PROJ-492-...`). With #45, runs commit progress reliably. Reset its
   kickback counters ONLY after a real fix (operational recovery).
3. The frontier is research_complete→posted — UNTESTED. Drive 492 there; fix REAL
   bugs as hit (do NOT pre-build speculative late-stage fixes). Likely candidates
   when reached: implementer emitting runnable analysis code (execute_and_gate),
   generator-aware revision for placeholder-in-generated-artifact (552 class),
   research_review code-authenticity/fabrication lens (262 class). Defer until hit.
4. 261/262: GPU dead-ends; leave to natural escalation or archive later. Not goal.

## Process learning
Sub-agents return TERSE sign-offs ("done") not their findings — read the full
report from `~/.claude/projects/-Users-jmanning-llmXive/<session>/subagents/agent-<id>.jsonl`
(longest assistant text). VERIFY agent claims against direct evidence before
acting (several "still broken" claims were already-fixed/stale).
