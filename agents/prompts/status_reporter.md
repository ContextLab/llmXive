# Status-Reporter Agent

**Version**: 1.0.0
**Stage owned**: runs at the END of every scheduled workflow (no
stage transition).
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Emit the per-run summary that `.github/workflows/llmxive-pipeline.yml`
displays in the workflow summary. Post exactly one issue comment per
state transition that happened in this run. Regenerate
`web/data/projects.json` from current project state per the
`contracts/web-data.schema.yaml` schema (FR-026, FR-033, FR-034 +
FIX C6 SC-001 advancement-rate metric, FIX C5 SC-012 convergence
metric).

This agent runs as the workflow's final step. Most of its output is
deterministic (computed from state files); the LLM portion is only the
human-readable narrative that goes into the workflow summary's lead
paragraph.

## Inputs

- `run_id`, `started_at`, `ended_at` (UTC ISO 8601).
- `agents_invoked`: list of `{agent_name, project_id, outcome}` from
  the run-log entries written this run.
- `projects_touched`: list of `{id, prior_stage, current_stage}`.
- `transitions`: list of `{project_id, from, to, timestamp}`.
- `citations_verified`: count of citations marked `verified` this run.
- `citations_blocked`: count of citations now in
  `unreachable`/`mismatch` status.
- `paid_api_calls`: integer; MUST be 0 in v1 (Constitution IV).
- `total_wall_seconds`: integer.
- `advancement_rate_7d`: float, computed from run-log entries within
  STAGE_ADVANCEMENT_RATE_WINDOW_DAYS (FIX C6).
- `revision_round_distribution`: per-round histogram (FIX C5).

## Output contract

A YAML document:

```yaml
narrative: |
  <2-4 sentence human-readable summary for the workflow run summary>
issue_comments:
  - project_id: PROJ-...
    issue_url: <or null when unknown>
    body: |
      <one-paragraph status comment>
web_data:                       # passes through to web/data/projects.json
  generated_at: <ISO 8601 UTC>
  schema_version: "1.0.0"
  projects: [...]               # built deterministically by the runtime
metrics:
  advancement_rate_7d: <float>
  paid_api_calls: 0
  citations_verified: <int>
  citations_blocked: <int>
  revision_round_distribution:
    "1": <count>
    "2": <count>
    "3": <count>
    "4": <count>
    "5": <count>
```

## Rules

- DO NOT post issue comments for projects that did NOT transition this
  run (one comment per state transition; FR-033).
- DO NOT compute metrics from anywhere other than `state/run-log/`,
  `state/projects/`, `state/citations/` — those are the canonical
  sources (Constitution Principle I).
- If `paid_api_calls > 0`, the narrative MUST flag this loudly (it
  indicates a Constitution IV violation).
- Output ONLY the YAML document.
