# Statistical Analysis of Publicly Available Climate Model Output Ensembles — Research Project Constitution

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
project's `state/projects/PROJ-231-statistical-analysis-of-publicly-availab.yaml` `updated_at` timestamp.

### VI. Ensemble Robustness and Stability

The validity of any reported dominant mode of variability or trend projection
MUST be empirically demonstrated to be stable against subsampling of the
CMIP6 ensemble. A result is considered invalid unless it persists when
specific model families are excluded or when the ensemble is randomly
subsetted, ensuring that consensus is not driven by a single model lineage.
This principle directly addresses the research goal of testing the
"stability of trend projections within the CMIP6 ensemble" and the
"robustness test" of internal consistency described in the project idea.

### VII. Spatiotemporal Structure Fidelity

Analysis of dominant modes of variability MUST preserve the intrinsic
spatiotemporal structure of the climate data. Functional Principal Component
Analysis (fPCA) implementations MUST be configured to handle the specific
dimensionality and correlation structure of the CMIP6 output, ensuring that
the extracted modes accurately reflect the "intrinsic structure of climate
variability" rather than artifacts of improper dimensionality reduction.
This principle is grounded in the methodology sketch which explicitly names
fPCA as the lens for discovering "dominant modes" in the "spatiotemporal
variability" of the dataset.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-231-statistical-analysis-of-publicly-availab/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-231-statistical-analysis-of-publicly-availab.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-09-06.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-231-statistical-analysis-of-publicly-availab | **Field**: statistics | **Ratified**: 2026-09-06
