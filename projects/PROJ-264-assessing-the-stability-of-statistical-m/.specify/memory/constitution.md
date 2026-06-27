# Assessing the Stability of Statistical Model Performance Across Data Subsets — Research Project Constitution

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
project's `state/projects/PROJ-264-assessing-the-stability-of-statistical-m.yaml` `updated_at` timestamp.

### VI. Statistical Power Adequacy

Every model-dataset pair MUST undergo a minimum of 100 resampling evaluations
to distinguish algorithmic performance differences from sampling noise. This
threshold is grounded in the Methodology sketch's repeated k-fold cross-validation
protocol (10 folds × 10 repetitions) and the Research Question's focus on
quantifying performance variance. Variance estimates are only valid when the
number of evaluations exceeds the noise floor identified in Expected Results.

### VII. Dataset Diversity Requirements

Dataset selection MUST span the full range of sample sizes (100 to 100,000)
and feature dimensions specified in the Methodology sketch to enable
correlation analysis between performance variance and dataset properties.
The 15 binary classification datasets from the UCI Machine Learning Repository
MUST be selected to cover this spectrum; any dataset falling outside these
bounds requires justification in `technical-design/` or exclusion from the
analysis.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-264-assessing-the-stability-of-statistical-m/code/`
  pins every Python dependency (pandas, numpy, scikit-learn).
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- All 15 UCI Machine Learning Repository datasets MUST be cached under `data/`
  with their checksums recorded; the project MUST NOT fetch datasets dynamically
  during execution.
- The 100 resampling iterations per model-dataset pair MUST complete within
  6-hour runner limits using CPU execution only.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-264-assessing-the-stability-of-statistical-m.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-06-27.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-264-assessing-the-stability-of-statistical-m | **Field**: statistics | **Ratified**: 2026-06-27
