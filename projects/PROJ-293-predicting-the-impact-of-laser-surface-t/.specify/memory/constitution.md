# Predicting the Impact of Laser Surface Texturing on Wear Resistance — Research Project Constitution

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
project's `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml` `updated_at` timestamp.

### VI. Numerical Stability in Sparse Regression

Given the project's reliance on aggregating sparse tabular data from disparate
sources (targeting ~300 records across multiple material classes) to train
regression models, all numerical preprocessing MUST explicitly handle
instability risks. Specifically, feature scaling (min-max normalization) and
interaction term construction (e.g., Power × Scanning Speed) MUST be
performed strictly within the training fold during cross-validation to prevent
data leakage, and models MUST be evaluated using 5-fold cross-validation
rather than a single train/test split to ensure robustness against small
sample variance. This principle is grounded in the "Methodology sketch"
section's explicit constraints on hyperparameter optimization and the
"Expected results" section's requirement for a non-linear functional
relationship derived from limited data.

### VII. Cross-Material Generalizability Validation

Because the research question explicitly seeks a functional relationship
applicable across "at least 3 material classes" to enable "virtual
prototyping" beyond single-material case studies, model validation MUST
include a leave-one-material-class-out cross-validation strategy. The
project's primary performance metric (R²) reported in the final paper MUST
be accompanied by the specific performance degradation observed when the
model is trained on one class (e.g., steels) and tested on another (e.g.,
aluminum), ensuring the learned functional form is not an artifact of a
single material's property distribution. This requirement is directly
derived from the "Methodology sketch" section's "Generalizability check"
step and the "Motivation" section's goal of reducing material-specific
trial-and-error.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-293-predicting-the-impact-of-laser-surface-t/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-21.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-293-predicting-the-impact-of-laser-surface-t | **Field**: materials science | **Ratified**: 2026-08-21
