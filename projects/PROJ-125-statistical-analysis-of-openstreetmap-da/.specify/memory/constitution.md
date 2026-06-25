# Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects — Research Project Constitution

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
project's `state/projects/PROJ-125-statistical-analysis-of-openstreetmap-da.yaml` `updated_at` timestamp.

### VI. Spatial Resolution Integrity

All spatial joins between OpenStreetMap vector features and satellite thermal
rasters MUST document the reprojection and aggregation method used to resolve
the vector-raster mismatch at the target 30m resolution. This ensures the
statistical relationship is not an artifact of misaligned coordinate systems.

### VII. Proxy Validity Boundaries

Any claim that OpenStreetMap features serve as a proxy for thermal monitoring
MUST include a sensitivity analysis quantifying the variance explained by
known missing factors (e.g., material albedo) to avoid overclaiming proxy
utility.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-125-statistical-analysis-of-openstreetmap-da/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- OpenStreetMap vector data and satellite thermal imagery (MODIS/Landsat)
  MUST be retrieved from their canonical repositories for each run, with
  fetch timestamps recorded in `data/` metadata.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-125-statistical-analysis-of-openstreetmap-da.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-125-statistical-analysis-of-openstreetmap-da | **Field**: statistics | **Ratified**: 2026-06-25
