# Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors — Research Project Constitution

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
project's `state/projects/PROJ-233-predicting-the-diffusion-coefficient-of-.yaml` `updated_at` timestamp.

### VI. Numerical Stability and Non-Linear Interaction Validation

Given the project's explicit reliance on capturing non-linear interactions between compositional and microstructural descriptors (e.g., atomic radius mismatch $\times$ dislocation density) to explain diffusion variance, all model training and evaluation MUST prioritize numerical stability and robustness against overfitting. Specifically, the XGBoost and Random Forest models trained in `code/` MUST undergo rigorous hyperparameter optimization via Bayesian optimization within defined compute budgets to ensure that identified interaction terms are not artifacts of model instability. Furthermore, the project MUST report confidence intervals for feature importance rankings derived from bootstrapping (1,000 iterations) to validate that the non-linear interactions claimed to drive >70% of the variance are statistically stable across data perturbations.

### VII. Independent Validation and Descriptor Provenance

To prevent circular validation, the project MUST enforce a strict separation between input descriptors and validation targets. Input features derived from compositional data (via Materials Project API) and microstructural proxies (derived from processing parameters or literature correlations) MUST NOT share any experimental measurement source with the target variable (experimental hydrogen diffusion coefficients $D$). The validation target MUST be sourced exclusively from independent permeation experiments or distinct datasets (e.g., NIST Standard Reference Database entries) to ensure that the model's predictive power is not inflated by data leakage. Any imputation of missing microstructural values (via k-Nearest Neighbors) MUST be documented as a derivation step that does not introduce bias from the target variable.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-233-predicting-the-diffusion-coefficient-of-/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-233-predicting-the-diffusion-coefficient-of-.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-09-25.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-233-predicting-the-diffusion-coefficient-of- | **Field**: materials science | **Ratified**: 2026-09-25
