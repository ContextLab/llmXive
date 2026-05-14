# E2 Phase Timing Raw Data

This directory contains phase-timing evidence for the E2 GRPO sequential vs.
concurrent experiments currently used by the MinT paper.

Generated from local run artifacts listed in
`raw_data/e2_grpo_population_scaling/provenance.csv`.

## Files

- `provenance.csv`: measured run IDs and source artifact paths copied from the
  population-scaling raw data provenance.
- `run_phase_summary.csv` / `.jsonl`: one row per measured run, with run wall
  time, aggregate train/eval windows, and task-level rollout/update sums where
  the console format supports the split.
- `task_phase_summary.csv` / `.jsonl`: one row per GRPO policy task.
- `step_phase_summary.csv` / `.jsonl`: one row per task step, including rollout
  and update durations when a `++ train step` boundary exists in the console.
- `api_phase_summary.csv` / `.jsonl`: one row per HTTP API route and run,
  parsed from `server.log`.
- `extract_phase_timing.py`: reproducible extractor.

## Phase Definitions

Task-level phases are derived from each task's `console.log` and `run.json`.

- Train window: first `>> train step` to last `== train step`.
- Rollout segment: `>> train step` to `++ train step`.
- Update segment: `++ train step` to `== train step`.
- Export start: the `@@ checkpoint` boundary after the final train step.
- Eval window: `>> eval_start` to `eval/metrics.jsonl:completed_at_unix`.

API-level phases are parsed from `server.log` HTTP completion records.

- Rollout API: `/api/v1/asample`.
- Update API: `/api/v1/forward_backward` and `/api/v1/optim_step`.
- Save/export API: `/api/v1/save_weights` and
  `/api/v1/save_weights_for_sampler`.

## Caveats

The 30B N=9 run uses a `tail_timeout` console format without `++ train step`
rollout-complete lines, so its task-level rollout/update split is marked
`rollout_update_split_available=false`. Its API-level rollout/update/save
windows are still available in `api_phase_summary.csv`.
