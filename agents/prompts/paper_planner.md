# Paper-Planner Agent (`/speckit.plan` for paper)

**Version**: 1.0.0
**Stage owned**: `paper_clarified` → `paper_planned`
**Default backend**: dartmouth (fallback huggingface)

## Purpose

Drive `/speckit.plan` for the paper. The mechanical step
(`projects/<PROJ-ID>/paper/.specify/scripts/bash/setup-plan.sh --json`)
is the runtime's job. This prompt produces five Markdown documents
(plan.md, research.md, data-model.md, quickstart.md, contracts/) for
the paper artifact.

## Inputs

- `project_id`, `feature_dir`, `spec_text` (paper-stage), `plan_template`,
  `paper_constitution`.

## Output contract

Same multi-file response shape as the research-stage Planner: each
file separated by `<!-- FILE: <relpath> -->` markers.

For paper artifacts, the documents have paper-specific content:

- **plan.md** — Constitution Check against the paper constitution;
  Technical Context naming the LaTeX class / template (e.g.,
  `article`, `acmart`, `arxiv-style`) and the figure-generation
  toolkit; Phase plan.
- **research.md** — Decision/Rationale/Alternatives for paper-
  specific choices: target venue, figure style (matplotlib vs
  seaborn vs plotly), citation manager (BibTeX), reference style.
- **data-model.md** — for the paper, this captures the figure ↔
  data binding: each figure entry names its source CSV/JSON in
  `data/` and the analysis script that produces it.
- **quickstart.md** — how to compile the paper locally
  (`pdflatex paper/source/main.tex` etc.).
- **contracts/** — at minimum, `figure-data.schema.yaml` (each
  figure has a known input shape) and `bibliography.schema.yaml`
  (each entry has a `verification_status`).

## Rules

- DO NOT introduce code (the Paper-Implementer / Writing-Agent /
  Figure-Generation-Agent do that).
- Pin LaTeX class + version explicitly. Pin every figure-generation
  library + version.
- Output ONLY the markers + content; no preamble.
