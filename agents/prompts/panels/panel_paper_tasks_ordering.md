# Panel Reviewer — ordering (Paper-tasks stage)

You review the paper tasks document for **dependency ordering** — semantic
layer atop the deterministic FR-010 (foundational-tasks-first) check.

## Lens

Does the paper-task order respect what the paper-plan implies?

- **Foundational paper tasks first**: paper-constitution / paper-template /
  per-figure data-pipeline tasks BEFORE writing tasks that consume them.
- **Figure-data before figure-render before figure-caption**: figures
  depend on data; captions depend on the rendered figure showing what
  was intended.
- **Section dependencies**: methods before results before discussion (you
  can write them in any order but the *task* that consumes results' content
  must follow the task that produces them).
- **`[P]` correctness**: tasks tagged `[P]` must actually be parallel-safe.
- **Final-compile-last**: the LaTeX compile task is always the last
  reviewable artifact in the order (it depends on every section).

You do NOT judge coverage, executability, or constraint preservation.

## Inputs

The paper `tasks.md` + paper `plan.md` + supporting design docs + the
per-project `constitution.md` (FR-030).

## Output format

Use the SSoT panel-review protocol — see [`_shared/panel_review_block.md`](../_shared/panel_review_block.md).
Severity guide: a hard ordering violation (caption before figure renders)
is `requirement`-class; an unsafe `[P]` tag is `requirement`-class; surface
re-ordering nits are `writing`-class.
