# {{title}} — Paper Project Constitution

<!--
This file is templated from agents/templates/paper_project_constitution.md
by the Paper-Initializer Agent (T071). Substitution tokens:
  {{project_id}} → e.g. PROJ-001-gene-regulation
  {{title}}      → human-readable paper title
  {{field}}      → e.g. biology, materials-science
  {{date}}       → ISO-8601 ratification date (UTC)

This constitution governs the paper-stage Spec Kit pipeline at
projects/{{project_id}}/paper/. It MUST NOT contradict the parent llmXive
constitution or the per-project research constitution.
-->

## Core Principles

### I. Writing Quality (NON-NEGOTIABLE)

Every section of the paper MUST be free of repeated prose, internal
inconsistencies, jargon used without definition, and logical
contradictions. The Proofreader-Agent flags violations; an empty flag
list is a precondition for `paper_complete`.

### II. Figure Quality

Every figure MUST be regenerated from real data by the
Figure-Generation-Agent in the code sandbox; no hand-drawn or
externally-generated figures may appear in the LaTeX source. Every figure
MUST have a caption that names the data source, the statistical test (if
any), and the units of measure.

### III. Citation Verification (inherits parent Principle II)

Every citation in the bibliography MUST have
`verification_status=verified` in the project's
`state/citations/{{project_id}}.yaml` before the paper can advance to
`paper_review`. The Reference-Validator Agent enforces this gate.

### IV. Statistical Interpretation Discipline

Every inferential claim in Results MUST cite a specific test, the test's
assumptions, the realized statistic, the sample size, the effect size,
and the test's p-value (where applicable). The Statistics-Agent produces
the prose; the Proofreader-Agent verifies the discipline.

### V. Reproducibility

The paper's LaTeX source MUST compile to PDF on a fresh GitHub Actions
runner using only the LaTeX distribution declared in the project's
`paper/requirements.txt` (or its TeX-Live equivalent). The LaTeX-Build
Agent compiles; the LaTeX-Fix Agent repairs failures; repeated failure
escalates the project to `human_input_needed`.

### VI. Jargon Discipline

Domain terms used more than once MUST be defined on first appearance.
Acronyms MUST be expanded on first use, then used consistently.

## Required Sections

The paper MUST contain, in order:

1. **Abstract** — under the venue's word limit.
2. **Introduction** — motivation, prior work summary, contribution
   statement.
3. **Methods** — sufficient detail to reproduce.
4. **Results** — figures + captions + statistical interpretations.
5. **Discussion** — interpretation, limitations, future work.
6. **References** — every entry verified by the Reference-Validator Agent.

## Style & Voice

- Active voice preferred; passive only when it clarifies.
- Concrete numbers preferred over qualitative claims ("36% reduction"
  beats "substantial reduction").
- One claim per sentence in Results; multi-part claims belong in
  Discussion.

## Reference-Verification Gate

A paper MUST NOT transition `paper_review` → `paper_accepted` while any
citation has `verification_status` of `unreachable` or `mismatch`.

## LaTeX Build Gate

A paper MUST NOT transition to `paper_complete` while `pdflatex` returns
a non-zero exit code on the project's LaTeX source.

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
paper-stage `current_stage`. Amendments to this constitution follow the
parent llmXive constitution's amendment procedure.

**Project ID**: {{project_id}} | **Field**: {{field}} | **Ratified**: {{date}}
