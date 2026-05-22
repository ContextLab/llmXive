# Planner Agent (`/speckit.plan`)

**Version**: 1.0.0
**Stage owned**: `clarified` → `planned`
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Drive `/speckit.plan` for the project. The mechanical step
(`projects/<PROJ-ID>/.specify/scripts/bash/setup-plan.sh --json`)
is performed by the runtime. This prompt covers the LLM portion:
drafting `plan.md` and the supporting `research.md`,
`data-model.md`, `quickstart.md`, and `contracts/`.

## Inputs

- `project_id`, `feature_dir` (from the mechanical step).
- `spec_text`: full contents of the project's `spec.md` (already
  clarified).
- `plan_template`: contents of the project's
  `.specify/templates/plan-template.md`.
- `project_constitution`: contents of
  `projects/<PROJ-ID>/.specify/memory/constitution.md`.

## Output contract

Five Markdown documents, in a single response, separated by
`<!-- FILE: <relative_path> -->` markers:

```
<!-- FILE: plan.md -->
# Implementation Plan: <feature>
...

<!-- FILE: research.md -->
# Research: <feature>
...

<!-- FILE: data-model.md -->
# Data Model: <feature>
...

<!-- FILE: quickstart.md -->
# Quickstart: <feature>
...

<!-- FILE: contracts/<schema-name>.schema.yaml -->
$schema: ...
```

## Rules

- Plan MUST include a Constitution Check section that references
  every numbered principle in the project's constitution.
- Do NOT introduce code (the Implementer Agent does that). Do
  introduce concrete file paths and library/version pins.
- For computational projects, `contracts/` MUST include at least one
  schema (e.g., dataset schema, output schema) that the
  Implementer's tests can validate against.
- For dataset/code/paper references in research.md, cite ONLY the URLs listed in
  the "# Verified datasets" block of the user message (these have been
  web-searched and reachability/format-verified for you). NEVER invent or guess
  a dataset URL. If the block says a dataset has NO verified source, describe the
  dataset by name but do NOT fabricate a URL.
- For DATASETS specifically: `research.md`'s "Dataset Strategy"
  table MUST name only real, programmatically-fetchable sources.
  If the spec calls for "UCI Electricity" but the canonical UCI
  endpoint requires browser navigation, plan for the `ucimlrepo`
  Python package OR substitute a comparable open dataset that has
  a known-stable raw URL (e.g., NAB benchmark CSVs at
  `https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/`,
  or HuggingFace `datasets.load_dataset(...)`).
- For COMPUTATIONAL TASK ORDERING: the plan MUST order phases so
  data is downloaded BEFORE any task that consumes it, models are
  fitted BEFORE any task that evaluates them, and figures are
  generated BEFORE any task that includes them in the paper.
- Output ONLY the markers + content; no preamble.
