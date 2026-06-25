# The Role of Network Module Dynamics in Predicting Individual Differences in Working Memory Capacity — Research Project Constitution

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
project's `state/projects/PROJ-383-the-role-of-network-module-dynamics-in-p.yaml` `updated_at` timestamp.

### VI. Neuroimaging Data Integrity (domain‑specific)

All raw resting‑state fMRI scans used to compute module‑flexibility metrics MUST be stored in their original DICOM/NIfTI format under `data/raw_fmri/`. Preprocessing (slice‑time correction, motion correction, spatial normalization, temporal filtering) MUST be performed using a version‑controlled pipeline (e.g., fmriprep) whose configuration file is committed to `code/`. The exact version of the preprocessing software and all its parameters MUST be recorded in the project's `state/...yaml` metadata. Any deviation from the standard pipeline MUST be justified in a `code/preprocessing/README.md` and reproduced on a fresh runner.

### VII. Behavioral Measure Consistency (domain‑specific)

Working‑memory capacity scores derived from the 2‑back task MUST be computed from the raw response logs using the published scoring algorithm, with the algorithm version and any parameter choices documented in `code/behavioral_scoring/`. The raw logs must be retained unchanged under `data/raw_behavior/`, and any exclusion criteria (e.g., trials with reaction time outliers) MUST be listed in a separate file linked in the scoring script. All derived score files must be checksum‑verified and traceable back to the original logs.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-383-the-role-of-network-module-dynamics-in-p/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-383-the-role-of-network-module-dynamics-in-p.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-383-the-role-of-network-module-dynamics-in-p | **Field**: neuroscience | **Ratified**: 2026-06-25
