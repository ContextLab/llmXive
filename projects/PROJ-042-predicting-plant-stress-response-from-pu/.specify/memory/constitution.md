# Predicting Plant Stress Response from Publicly Available Transcriptomic Data — Research Project Constitution

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
project's `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` `updated_at` timestamp.

### VI. Cross-Dataset Generalization Validation

Models trained on one set of public GEO datasets (drought, salinity, heat, or cold)
MUST be evaluated on held-out independent datasets to quantify generalization gaps.
Within-dataset performance (80/20 split) is insufficient for claiming stress-specific
signatures; only cross-dataset classification accuracy and confusion matrix analysis
can validate the research question regarding separable transcriptional signatures.
This principle is grounded in the methodology sketch's explicit requirement to split
data into "within-dataset" and "cross-dataset" partitions to measure generalization.

### VII. Transcriptomic Data Harmonization and Feature Consistency

All RNA-seq count matrices from NCBI GEO MUST undergo gene identifier harmonization
using biopython to ensure a consistent feature space across datasets. Only genes
present in all integrated datasets are retained for modeling, and low-expression
genes (<1 CPM across >80% of samples) MUST be filtered prior to TPM normalization.
This ensures that observed stress signatures reflect biological signal rather than
technical artifacts or dataset-specific noise, as specified in the methodology sketch's
preprocessing and harmonization steps.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-042-predicting-plant-stress-response-from-pu/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-08.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-042-predicting-plant-stress-response-from-pu | **Field**: biology | **Ratified**: 2026-07-08
