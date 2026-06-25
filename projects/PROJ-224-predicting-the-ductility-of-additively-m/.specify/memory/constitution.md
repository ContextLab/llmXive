# Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys — Research Project Constitution

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
project's `state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml` `updated_at` timestamp.

### VI. Modeling Transparency

All statistical and machine‑learning models employed in this project MUST be
fully documented in the repository, including:

- the precise model type (e.g., linear mixed‑effects model, gradient‑boosting regressor),
- every hyper‑parameter and its value,
- the random seed used for any stochastic training,
- the exact training/validation split strategy,
- the version of the software library that implements the model.

These requirements stem from the methodology sketch, which specifies fitting a
linear mixed‑effects model and training a gradient‑boosting regressor with
cross‑validation. Providing this detail guarantees that reviewers can
reproduce reported coefficients, confidence intervals, and performance metrics.

### VII. External Data Provenance

Each external dataset acquired for this project (Materials Project API, the
“Hadditive manufacturing superalloy” collection on HuggingFace Datasets, and
supplementary tables from the related‑work papers) MUST be:

- recorded with its source name and version (e.g., Materials Project release X.Y, HuggingFace dataset version tag),
- downloaded via a scripted process that logs the retrieval timestamp,
- stored under `data/external/` alongside a checksum file,
- accompanied by a concise README that cites the original publication or dataset description.

This principle directly reflects the data acquisition plan outlined in the
idea body and ensures that the exact composition of the dataset can be
re‑created on future runs.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-224-predicting-the-ductility-of-additively-m/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-224-predicting-the-ductility-of-additively-m | **Field**: materials science | **Ratified**: 2026-06-25
