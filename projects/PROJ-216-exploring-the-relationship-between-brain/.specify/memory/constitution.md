# Exploring the Relationship Between Brain Network Dynamics and Musical Creativity — Research Project Constitution

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
project's `state/projects/PROJ-216-exploring-the-relationship-between-brain.yaml` `updated_at` timestamp.

### VI. Neuroimaging Data Standardization

All raw fMRI data used in the study (OpenNeuro datasets ds000224 and ds000230) MUST be stored in BIDS format. The preprocessing pipeline (FSL/AFNI commands for motion correction, normalization, and band‑pass filtering) MUST be version‑controlled, logged, and invoked via reproducible scripts in `code/`. Any derived connectivity matrices must retain provenance metadata linking them to the original BIDS‑structured raw files.

### VII. Statistical Reporting Transparency

Every correlation analysis between graph metrics and improvisation scores MUST report the effect size (Cohen's d) and a 95 % confidence interval, and MUST explicitly state the multiple‑comparison correction method (Bonferroni) used. The exact statistical scripts (e.g., `stats/correlation_analysis.py`) must be executable without manual parameter changes to reproduce the reported numbers.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-216-exploring-the-relationship-between-brain/code/`
  pins every Python dependency, including specific versions of `nibabel`, `nilearn`, `networkx`, and other neuroimaging libraries.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end‑to‑end without
  manual intervention.
- External neuroimaging datasets (OpenNeuro ds000224, ds000230) MUST be
  fetched using the same `wget`/`curl` commands recorded in the reproducibility script, and the exact dataset version (snapshot hash) must be recorded in `data/manifest.yaml`.
- Preprocessing scripts that invoke FSL/AFNI tools must specify exact tool versions and command‑line flags to ensure identical outputs across runs.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-216-exploring-the-relationship-between-brain.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-06-24.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-216-exploring-the-relationship-between-brain | **Field**: neuroscience | **Ratified**: 2026-06-24
