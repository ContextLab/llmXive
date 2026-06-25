# Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re-running the
project's `code/` against the project's `data/` on a fresh GitHub Actions
runner. Random seeds MUST be pinned in `code/`. External datasets MUST be
fetched from the same canonical source on every run.

### II. Verified Accuracy (inherits parent Principle II)

Every external citation in `idea/`, `technical-design/`,
`implementation-plan/`, or `paper/` MUST be verified by the
Reference-Validator Agent against the primary source before contributing
review points. Title-token-overlap with the cited source MUST be ≥
`CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7).

### III. Data Hygiene

Datasets MUST be checksummed and the checksum recorded under `data/`. No
data may be modified in place; every transformation MUST produce a new file
with a documented derivation. Personally identifying information MUST NOT
appear in committed data.

### IV. Single Source of Truth (inherits parent Principle I)

Every figure, statistic, or interpretation in the paper MUST trace back to
exactly one row in this project's `data/` and one block in this project's
`code/`. Derived numbers MUST NOT be hand-typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The
Advancement-Evaluator Agent invalidates stale review records when the
hashed artifact changes. Every research-stage artifact change updates this
project's `state/projects/PROJ-757-meta-analysis-of-trust-perception-in-dee.yaml` `updated_at` timestamp.

### VI. Systematic Review Transparency (project‑specific)

All literature‑search and screening activities described in the **Methodology sketch** must be fully documented:
- The inclusion criteria for peer‑reviewed experimental studies (authentic vs. AI‑generated facial stimuli) must be recorded in a machine‑readable `inclusion_criteria.yaml`.
- Search queries to OpenAlex, Semantic Scholar, and arXiv (the two Boolean strings listed in the idea) must be saved alongside the raw CSV export in `data/search_results/`.
- Abstract screening decisions by the two independent reviewers must be logged in a `screening_log.csv` that includes reviewer IDs, inclusion/exclusion flags, and justification texts.
- A PRISMA flow diagram generated in the reporting stage must be derived programmatically from these logs and committed to `figures/PRISMA_flow.pdf`.

These artifacts constitute the single source of truth for the systematic‑review component and are required for any downstream validation.

### VII. Statistical Reporting and Reproducibility (project‑specific)

The meta‑analytic calculations outlined in the **Methodology sketch** must adhere to the following:
- Effect‑size conversion must be performed with the `esc` R package (or its Python equivalent) and the exact version used must be recorded in `requirements.txt`/`pyproject.toml`.
- The primary random‑effects meta‑analysis must be executed with the `metafor` R package; the script `code/meta_analysis.R` must explicitly set the package version and seed.
- Moderator analyses for realism and media‑literacy must be coded as mixed‑effects meta‑regressions in the same script, with all predictor variables clearly labelled.
- Robustness checks (leave‑one‑out sensitivity, funnel‑plot generation, Egger’s test) must be implemented in separate, version‑controlled functions and their outputs archived under `results/robustness/`.
- All statistical results reported in the manuscript (effect sizes, confidence intervals, heterogeneity statistics, moderator coefficients, p‑values) must be programmatically extracted from the R objects and inserted into the R Markdown manuscript via parameterized knitting, guaranteeing no manual transcription.

Compliance with these requirements ensures that any statistical claim is traceable to a specific, versioned analysis script and dataset row.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-757-meta-analysis-of-trust-perception-in-dee/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-757-meta-analysis-of-trust-perception-in-dee.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-06-25.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-757-meta-analysis-of-trust-perception-in-dee | **Field**: psychology | **Ratified**: 2026-06-25
