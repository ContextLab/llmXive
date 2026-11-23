# Predicting Material Degradation Under Cyclic Loading from Public Datasets — Research Project Constitution

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
project's `state/projects/PROJ-378-predicting-material-degradation-under-cy.yaml` `updated_at` timestamp.

### VI. Numerical Stability and Imputation Rigor

Given the reliance on iterative imputation (`scikit-learn IterativeImputer`)
to handle missing values in sparse fatigue datasets, every imputation run
MUST record the exact convergence tolerance and maximum iteration count
(`max_iter=10`) used in the execution log. Feature normalization and
imputation parameters MUST be frozen in a configuration file prior to model
training to prevent data leakage between the training and validation folds
during the `k=5` cross-validation process. This principle is grounded in
the Methodology sketch's explicit requirement to "handle missing values using
iterative imputation" and "perform feature normalization" before training
regression models.

### VII. Uncertainty Quantification Mandate

All degradation predictions (remaining useful life, stiffness loss) MUST be
accompanied by prediction intervals generated via Quantile Regression Forests,
not just point estimates. The project MUST explicitly report the coverage
probability of these intervals against the test set to validate the
uncertainty estimates. This requirement is grounded in the Methodology sketch's
directive to "Generate uncertainty estimates using quantile regression forests
to provide prediction intervals alongside point estimates" and the Expected
results section's focus on identifying predictors where "composition and
loading alone" may be insufficient, necessitating rigorous uncertainty bounds
to distinguish signal from noise.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-378-predicting-material-degradation-under-cy/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-378-predicting-material-degradation-under-cy.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-04.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-378-predicting-material-degradation-under-cy | **Field**: materials science | **Ratified**: 2026-08-04
