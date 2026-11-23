# Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection — Research Project Constitution

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
project's `state/projects/PROJ-372-assessing-the-sensitivity-of-regression-.yaml` `updated_at` timestamp.

### VI. Empirical Validation of Theoretical Assumptions

Coefficient stability metrics MUST be explicitly correlated with quantified violations of OLS assumptions (specifically heteroscedasticity and outliers) rather than treated as independent of data quality. As defined in the methodology, datasets MUST be tagged by violation severity using the Breusch-Pagan test for heteroscedasticity and Cook's distance for outliers, and the empirical standard deviation of coefficients across subsets MUST be analyzed as a function of these severity metrics alongside the condition number. This principle ensures that the project does not merely observe instability but explicitly maps it to the specific theoretical breaches identified in the research question.

### VII. Non-Circular Derivation of Stability Metrics

The validation target (empirical variance of coefficients across subsets) MUST be strictly independent of the predictor variables (collinearity condition number and violation severity metrics) derived from the full dataset. Per the methodology sketch, the project MUST verify that the calculation of empirical variance across the 200 random observation subsets does not inadvertently reuse the full-dataset properties in a way that creates circular reasoning, ensuring that the observed interaction effects genuinely reflect subset selection sensitivity rather than artifact of the measurement process.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-372-assessing-the-sensitivity-of-regression-/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-372-assessing-the-sensitivity-of-regression-.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-15.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-372-assessing-the-sensitivity-of-regression- | **Field**: statistics | **Ratified**: 2026-08-15
