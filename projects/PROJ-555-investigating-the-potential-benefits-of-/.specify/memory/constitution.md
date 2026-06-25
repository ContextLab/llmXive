# Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas — Research Project Constitution

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
project's `state/projects/PROJ-555-investigating-the-potential-benefits-of-.yaml` `updated_at` timestamp.

### VI. Ecotourism Revenue Transparency

All ecotourism‑related financial data (visitor numbers, revenue totals, reinvestment rates) referenced in the methodology MUST be sourced from publicly available conservation‑organization or tourism‑authority reports, stored as CSV/JSON files under `data/ecotourism/`, and accompanied by a metadata file that records the source name, retrieval date, and any preprocessing steps. Any analysis that uses these financial variables MUST cite the corresponding metadata entry, ensuring that revenue‑based conclusions are traceable to the original reports.

### VII. Satellite Data Integrity

Raw Landsat Level‑2 surface reflectance scenes downloaded via the USGS EarthExplorer API MUST be saved unmodified in `data/raw/landsat/`. Each scene MUST have its checksum recorded in `state/projects/PROJ-555-investigating-the-potential-benefits-of-.yaml` and be referenced by acquisition date and scene identifier in all downstream processing scripts. NDVI calculations MUST be performed on these archived raw files using a documented preprocessing pipeline, guaranteeing that any change in satellite data handling is auditable.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-555-investigating-the-potential-benefits-of-/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- All Landsat data are fetched programmatically from the USGS EarthExplorer API; the exact query parameters and API version are recorded in `code/data_acquisition.py`.
- Raw satellite files are stored under `data/raw/landsat/` and checksummed as described in Principle VII.
- Ecotourism financial datasets are stored under `data/ecotourism/` with accompanying metadata as required by Principle VI.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-555-investigating-the-potential-benefits-of-.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-555-investigating-the-potential-benefits-of- | **Field**: environmental science | **Ratified**: 2026-06-25
