# Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context — Paper Project Constitution

<!--
This file is templated from agents/templates/paper_project_constitution.md
by the Paper-Initializer Agent (T071). Substitution tokens:
  PROJ-575-training-long-context-vision-language-mo → e.g. PROJ-001-gene-regulation
  Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context      → human-readable paper title
  computer science      → e.g. biology, materials-science
  2026-06-30       → ISO-8601 ratification date (UTC)

This constitution governs the paper-stage Spec Kit pipeline at
projects/PROJ-575-training-long-context-vision-language-mo/paper/. It MUST NOT contradict the parent llmXive
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
`state/citations/PROJ-575-training-long-context-vision-language-mo.yaml` before the paper can advance to
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

### VII. Computational Efficiency & Hardware Transparency

Given the focus on long-context inference, every performance claim MUST
explicitly state the hardware constraints (e.g., CPU-only, specific GPU
memory limits) and the context length at which the measurement was taken.
Claims of "generalization beyond 128K" MUST be accompanied by a breakdown
of memory usage and inference latency at each tested context window (32K,
64K, 128K, 256K, 512K). The Efficiency-Agent validates these metrics
against the project's `FR-008` memory constraints.

### VIII. Scaling Law Rigor

Any claim regarding performance trends across context lengths MUST be
supported by a fitted regression model (linear, sublinear, or superlinear)
with the slope coefficient and confidence intervals reported. If multiple
hypothesis tests are performed across task categories (e.g., VQA, RAG,
Summ), the paper MUST explicitly state whether a multiple-comparison
correction (e.g., Bonferroni or Benjamini-Hochberg) was applied, or
acknowledge the lack thereof as a limitation. The Statistics-Agent
enforces this reporting standard.

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
- **ML/AI Venue Specific**: Prioritize brevity and density of information.
  Avoid narrative fluff in the Introduction; immediately establish the
  gap in long-context capability. In Methods, focus on architectural
  modifications and training/inference hyperparameters over general
  background. Use precise terminology for context-window mechanisms
  (e.g., RoPE scaling, sparse attention) without over-explaining
  foundational transformer concepts unless the paper introduces a novel
  variation.

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

**Project ID**: PROJ-575-training-long-context-vision-language-mo | **Field**: computer science | **Ratified**: 2026-06-30
