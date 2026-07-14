# Predicting Adsorption Isotherm Parameters from Molecular Features — Research Project Constitution

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
project's `state/projects/PROJ-245-predicting-adsorption-isotherm-parameter.yaml` `updated_at` timestamp.

### VI. Physicochemical Descriptor Integrity

Every molecular descriptor (e.g., polarizability, van der Waals volume) and adsorbent property (e.g., pore volume, accessible surface area) used as a model feature MUST be calculated using the exact algorithms and libraries (specifically RDKit and crystallographic parsers) defined in the `code/` directory. No hand-calculated or externally sourced descriptor values are permitted without explicit provenance tracking, ensuring that the "dominant physical drivers" identified in the feature importance analysis are derived strictly from the project's own computational pipeline rather than inconsistent external sources.

### VII. Physicochemical Plausibility Validation

Model predictions for Henry's constants, Freundlich exponents, and Langmuir capacities MUST be validated against established physicochemical principles (e.g., alignment of feature importance with known gas-surface interaction theories) and tested on independent literature datasets (such as Kr adsorption on carbon nanotubes) to ensure the model captures generalizable physics rather than dataset-specific artifacts. A model achieving high statistical metrics (R² ≥ 0.7) but failing this plausibility check is considered invalid for the purpose of computational screening.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- The data pipeline must strictly separate training and test sets by adsorbent material to prevent data leakage, as specified in the methodology.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-245-predicting-adsorption-isotherm-parameter.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.
- All data transformations (filtering for type I isotherms, unit normalization) must be recorded as distinct steps in the `code/` pipeline.

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
**1.0.0** — ratified 2026-07-14.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-245-predicting-adsorption-isotherm-parameter | **Field**: chemistry | **Ratified**: 2026-07-14
