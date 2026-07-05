# Predicting Coating Adhesion Strength from Composition and Surface Features — Research Project Constitution

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
project's `state/projects/PROJ-419-predicting-coating-adhesion-strength-fro.yaml` `updated_at` timestamp.

### VI. Computational Numerical Stability and Resource Bounds

All machine learning models (Gradient Boosting, Random Forest) trained in this project MUST be executed within the strict resource constraints defined in the methodology: a single-core CPU environment with a maximum runtime of 4 hours and a memory cap of 7 GB. Model training and evaluation MUST utilize nested 5-fold cross-validation to prevent data leakage, and all random seeds MUST be explicitly fixed to ensure that the reported R², RMSE, and MAE metrics are deterministic. Feature engineering steps, specifically the calculation of elemental one-hot vectors and atomic radius variance, MUST be validated for numerical stability to avoid overflow or underflow errors during the preprocessing of composition data from the Materials Project and Open Materials Database.

### VII. Multi-Modal Data Integration and Feature Attribution Rigor

The project MUST explicitly validate the predictive contribution of compositional descriptors (e.g., crosslinker density, functional group counts) against surface metrics (e.g., RMS roughness, water contact angle) using SHAP values and permutation importance. Any claim regarding the relative importance of a specific descriptor MUST be supported by a statistically significant difference (paired t-test, p < 0.05) between the full-feature model and the respective baseline models (composition-only and surface-only). The dataset assembly process MUST ensure that records are strictly aligned by coating-substrate pair identifiers before merging composition data from the Materials Project, surface topography data from the NIST Surface Metrology Repository, and adhesion strength measurements from open-access studies, preventing the introduction of spurious correlations due to misaligned metadata.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-419-predicting-coating-adhesion-strength-fro/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-419-predicting-coating-adhesion-strength-fro.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-05.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-419-predicting-coating-adhesion-strength-fro | **Field**: materials science | **Ratified**: 2026-07-05
