# Quantifying the Impact of Spatial Correlations on Perovskite Solar Cell Efficiency — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re‑running the project's `code/` against the project's `data/` on a fresh GitHub Actions runner. Random seeds MUST be pinned in `code/`. External datasets MUST be fetched from the same canonical source on every run.

### II. Verified Accuracy (inherits parent Principle II)

Every external citation in `idea/`, `technical-design/`, `implementation-plan/`, or `paper/` MUST be verified by the Reference-Validator Agent against the primary source before contributing review points. Title-token-overlap with the cited source MUST be ≥ `CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7).

### III. Data Hygiene

Datasets MUST be checksummed and the checksum recorded under `data/`. No data may be modified in place; every transformation MUST produce a new file with a documented derivation. Personally identifying information MUST NOT appear in committed data.

### IV. Single Source of Truth (inherits parent Principle I)

Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand‑typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research‑stage artifact change updates this project's `state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml` `updated_at` timestamp.

### VI. Spatial Characterization Consistency

All elemental composition maps (Pb, I, MA) acquired from the NREL Perovskite Database and the Materials Project **must** be stored in their raw EDS format under `data/raw/`. Pre‑processing steps—including calibration with `hyperSpy`, alignment to a common pixel grid, and masking of defective regions—**must** be performed by scripts in `code/preprocess/` that log the exact parameters used. Any derived concentration maps **must** be saved as new files with provenance metadata linking them to the original raw files and the specific version of the preprocessing script.

### VII. Statistical Modeling Transparency

Statistical analyses linking correlation‑length metrics to device performance **must** be executed by code in `code/modeling/` that explicitly records: (a) the regression method (e.g., linear regression, GAM), (b) the computed Pearson r, p‑value, and confidence intervals, and (c) the cross‑validation strategy (leave‑one‑out). All model hyperparameters and random seeds **must** be versioned. Results reported in the manuscript **must** reference the exact CSV output files produced by these scripts, ensuring a one‑to‑one mapping between reported numbers and reproducible code.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-204-quantifying-the-impact-of-spatial-correl/code/` pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end‑to‑end without manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's `state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted` transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-06-24.

Amendments follow the parent llmXive constitution's amendment procedure (open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's `current_stage`. The principal agent for this project is **flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The parser at `src/llmxive/config.py` is the single source these numbers flow from.

**Project ID**: PROJ-204-quantifying-the-impact-of-spatial-correl | **Field**: physics | **Ratified**: 2026-06-24
