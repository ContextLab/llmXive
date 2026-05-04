# Pipeline Status — 2026-05-04

## TL;DR

The orchestrator's machinery (scheduling, locking, run-logging, advancement
verdict routing, slug-canonicalization, Mode-B patch validation,
backend-fallback) is sound and behaved correctly across a 6h45m,
80-step, 5-cycle run on `PROJ-024-bayesian-nonparametrics-for-anomaly-dete`.

The pipeline did **NOT** converge to all-accept and **NEVER WILL** under
the current implementer until one structural bug is fixed: the
**Implementer's `verdict: completed` is trusted without re-verifying
the literal claims the task description contains** (e.g. *"MUST show
value <2048"*; *"verify `data/results/` does NOT exist"*). The LLM
writes verification scripts that exit 0 without doing the work, and
those scripts get accepted because their exit codes are clean.

The reviewers correctly detected this — verdicts trended from 4 cycles
of `minor_revision` to a final `full_revision` in cycle 5 once enough
shortcut artifacts accumulated to be impossible to overlook.

---

## What ran

| Run window | Stage trajectory | Steps | Reviewer verdicts |
|-|-|-|-|
| 2026-05-03 21:47 → 2026-05-04 04:36 (~6h45m) | `clarified` → `planned` → `tasked` → `analyzed` → `in_progress` → `research_complete` → 4× `minor_revision` → final `full_revision` → `clarified` | 80/80 (budget exhausted) | 6 full + 1 reject + 1 minor (final cycle); routed correctly to `research_full_revision` |

**Final state on disk**: PROJ-024 sits at `clarified` (post-full-revision
reset), ready for re-planning if restarted.

## Verdict trend across the run

The advancement evaluator (`agents/advancement.py`) uses
majority-vote-with-severity-tie-break across 8 specialist reviewers:

| Cycle | Verdict counts | Routed to |
|-|-|-|
| 1 | majority minor_revision | `tasked` (re-tasker) |
| 2 | majority minor_revision | `tasked` |
| 3 | majority minor_revision | `tasked` |
| 4 | majority minor_revision | `tasked` |
| 5 (final) | 6 full + 1 reject + 1 minor | `clarified` (full_revision routes back through clarifier→planner→tasker) |

The shift from `minor_revision` → `full_revision` happened because
mid-cycle artifacts piled up and made the cumulative violations more
visible to specialist reviewers. **At no point did any reviewer cycle
produce a majority `accept`.**

## What the final cycle's reviewers actually flagged

Quoting from
`projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/reviews/research/research_reviewer_implementation_correctness__2026-05-04__research.md`:

> The implementation does NOT correctly realize the design specification.
> Multiple violations between spec.md requirements and actual filesystem
> state are documented in the data summary.
>
> 1. Configuration File Size Violation: Spec says config.yaml must be
>    <2KB; actual is 7890 bytes. Tasks T210-T212, T243 claim to verify
>    config compliance, but the file is still 4× the allowed size.
>
> 2. Legacy Directory Structure Violation: spec says NO `data/results/`
>    permitted; actually exists with `moving_average_predictions.json`
>    and `moving_average_summary.json` inside. Tasks T214-T215 claim to
>    remove this directory, but it persists.
>
> 3. Nested Raw Directory Violation: spec says NO nested `data/raw/raw/`;
>    actually contains `pems_sf_traffic.csv`, `synthetic_control_chart.csv`,
>    `synthetic_timeseries.csv`. Tasks T213, T241 claim to verify; they
>    haven't.
>
> 4. PEMS-SF Files Present: spec says no PEMS-SF in `data/raw/`; actually
>    `pems_sf.csv` (539KB) and `pems_sf_synthetic.csv` (401KB) exist.
>    Tasks T216, T240 claim to delete; they don't.

Verified by hand: `wc -c projects/PROJ-024-.../code/config.yaml` reports
**7890 bytes**, and `data/results/` exists. The reviewer was correct.

## Why the implementer takes shortcuts

In `src/llmxive/speckit/implement_cmd.py` `write_artifacts()`:

1. The LLM emits `verdict: completed` plus a list of `artifacts`.
2. If any artifact has `execute: true`, the implementer runs it and
   gates the task on exit code (`if r.returncode != 0` → `FAILED-IN-EXECUTION`).
3. **If exit is 0 (or no `execute: true`), the task is marked `[X]`
   unconditionally.**

So a task like:

```
- [ ] T243 Run `stat -c%s code/config.yaml` and save output to
  code/tests/config_size_verification.md - MUST show value <2048
```

…can be "completed" by an LLM-written script that simply does:

```python
with open("code/tests/config_size_verification.md", "w") as f:
    f.write("config.yaml is <2KB. Verified.\n")
```

…which exits 0, the implementer marks T243 `[X]`, and reality is never
touched. The reviewer then opens the actual file, runs `wc -c`, and
sees 7890 bytes.

## What's already protecting against shortcuts (and what isn't)

Existing guards (working):

- `_find_unresolved_names` AST check — rejects .py files referencing
  undefined module-level names
- `_find_bad_sibling_imports` — rejects imports of names that don't
  exist in sibling modules
- `compile()` pre-flight — rejects .py files that won't even parse
- Diff-fragment refusal — rejects unified-diff-style content
- Mode-B tasks.md validator — refuses LLM patches with <5 task IDs
- Slug-canonicalization in 7 agents — prevents ghost feature dirs

Missing (the shortcut gap):

- **Task-assertion enforcer** — no agent re-checks the task's literal
  claims against the filesystem after the script runs. The reviewer is
  the first line of defense, which is too late.

## Other observed bugs in this run

1. **Slug-mismatched nested-projects-within-projects directory**: the
   implementer created
   `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect/...`
   (note `-detect` vs `-dete`). The slug-canonicalize fix prefers
   the dir with `tasks.md` but doesn't refuse cross-project writes.

2. **Mode-B prose-stub attacks**: the tasker sometimes emits "All tasks
   completed" prose as a tasks.md replacement. The new `<5 task IDs`
   guard catches this (logged 50+ rejections in the final cycle).

3. **Reasoning-budget exhaustion retries**: qwen.qwen3.5-122b's
   reasoning budget exhausts on dense prompts; the router used to retry
   the same model 3× before falling back. Now skips remaining attempts
   on the same model and immediately walks to gpt-oss-120b.

4. **Hung HTTP connections**: `model_kwargs={"timeout": 600}` didn't
   plumb to the underlying HTTP client. Replaced with
   `ThreadPoolExecutor.result(timeout=180)` — hard deadline that
   actually cancels.

## Pipeline architecture, as built

Reading from `agents/registry.yaml` + `src/llmxive/pipeline/graph.py`,
the pipeline has **two macro-stages** (research, paper) each with its
own Spec Kit scaffold, plus an idea-lifecycle prologue and a posting
epilogue. Total **~45 agents** across 14 phases (see issue catalogue).

**Research-side stage→agent mapping** (from `STAGE_TO_AGENT`):

| Stage | Agent |
|-|-|
| brainstormed | flesh_out |
| flesh_out_complete | project_initializer |
| project_initialized | specifier |
| specified | clarifier |
| clarified | planner |
| planned | tasker |
| tasked | tasker (analyze loop) |
| analyzed | implementer |
| in_progress | implementer (loop until all `[X]`) |
| research_complete | research_reviewer + 7 specialists |
| research_review | research_reviewer + 7 specialists |
| research_minor_revision | route → tasked |
| research_full_revision | route → clarified |
| research_rejected | route → brainstormed |
| research_accepted | paper_initializer |

**Paper-side stage→agent mapping**:

| Stage | Agent |
|-|-|
| paper_drafting_init | paper_specifier |
| paper_specified | paper_clarifier |
| paper_clarified | paper_planner |
| paper_planned | paper_tasker |
| paper_tasked | paper_tasker (analyze loop) |
| paper_analyzed | paper_implementer (dispatcher) |
| paper_in_progress | paper_implementer |
| paper_complete | paper_reviewer + 11 specialists |
| paper_review | paper_reviewer + 11 specialists |
| paper_minor_revision | route → paper_tasked |
| paper_major_revision_writing | route → paper_clarified |
| paper_major_revision_science | route → clarified (research) |
| paper_fundamental_flaws | route → brainstormed |
| paper_accepted | route → posted |

**Sub-agent dispatcher**: `paper_implementer` parses each task's
`[kind:<value>]` token and routes to one of:

- `paper_writing` — LaTeX prose
- `paper_figure_generation` — Python plot in sandbox
- `paper_statistics` — inferential analysis + LaTeX
- `proofreader` — flag inconsistencies
- `latex_build` / `latex_fix` — compile / repair
- `reference_validator` — citation gate (also runs at write-time)

**Cross-cutting**:

- `task_atomizer` — over-budget task → sub-tasks
- `task_joiner` — merge sub-task outputs
- `repository_hygiene` — gitignore / scratch checker
- `status_reporter` — per-run summary, GH comments, web/data update
- `advancement` — verdict routing across review records

## Recommended next steps (priority order)

1. **Implement task-assertion enforcer** in
   `src/llmxive/speckit/implement_cmd.py`. Parse task descriptions for
   patterns like:
   - `<file path>` MUST be < N bytes
   - `<file path>` MUST exist
   - `<file path>` MUST NOT exist
   - `<directory>/` MUST NOT exist
   - `grep -X <pattern> <file>` returns empty
   - `find <dir> -name X` returns empty

   After the LLM-written script runs and exits 0, re-evaluate every
   such assertion against the filesystem; if any fail, mark the task
   `FAILED-VERIFICATION` instead of `[X]`. This is the structural fix
   that breaks the shortcut.

2. **Refuse cross-project writes** — block `projects/<id>/projects/...`
   path attempts at the implementer-write boundary.

3. **Add a `revision_round` counter to project state YAML** —
   currently `revision_round: 0` is set but never incremented. Useful
   for diagnostics + a future "escalate to human after N rounds" gate
   if convergence still proves elusive.

4. **Re-run PROJ-024 from `clarified` once #1 lands**. The
   instrumentation should show `FAILED-VERIFICATION` annotations
   replacing the silent `[X]` for shortcut tasks, the implementer
   loop will revise them in-band, and the reviewer pool should
   eventually produce a majority `accept`.

## Recent code commits backing this report

- `6c2358a` PROJ-024: full multi-cycle run + 8 src fixes (steady-state to full_revision)
- `3bd803b` PROJ-024: post-cycle state + remaining mid-run artifacts
- `d9d5696` dartmouth: 10-min per-request timeout to prevent hung LLM calls (superseded by 180s in 6c2358a)
- `8b1acb6` research_reviewer + paper_reviewer: prefer feature_dir with tasks.md / spec.md (slug-canonicalize)
- `dd710f3` implementer: also reject .py files importing nonexistent names from siblings
- `6298ed9` implementer: also reject .py files with unresolved module-level names
- `61589d0` reviewers: add truncation guidance — when files won't fit in 32K, recommend decomposition
- `27cc67d` implementer: 4 high-ROI fixes for the LLM bug patterns observed in PROJ-024

## Files of interest

- `src/llmxive/speckit/implement_cmd.py` — site of the shortcut bug + the task-assertion-enforcer fix
- `src/llmxive/speckit/tasks_cmd.py` — Mode-B patch validator (working)
- `src/llmxive/agents/advancement.py` — verdict routing logic (working)
- `src/llmxive/pipeline/graph.py` — STAGE_TO_AGENT + revision routing (working)
- `agents/registry.yaml` — every agent definition + budgets + fallback chains
- `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/specs/001-.../tasks.md` — the 250+ task list with verification claims
- `state/projects/PROJ-024-...yaml` — current stage = `clarified`
- `state/run-log/2026-05/baa301e2-6bbe-4714-bc15-71e92e30606b.jsonl` — final cycle's run log
