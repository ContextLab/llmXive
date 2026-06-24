# Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation — Research Project Constitution

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
project's `state/projects/PROJ-520-neural-correlates-of-visuospatial-attent.yaml` `updated_at` timestamp.

### VI. EEG Data Processing Standards (domain‑specific)

All EEG preprocessing and feature‑extraction steps MUST follow the pipeline
described in the idea’s *Methodology sketch*:  
- Use MNE‑Python to band‑pass filter 1–40 Hz, remove line noise, and apply ICA for artifact rejection.  
- Segment data into 2‑second epochs centred on attention‑shift events as marked by participant responses or landmark interactions.  
- Compute time‑frequency representations with Morlet wavelets over the 8–30 Hz range.  
- Extract mean power for the alpha (8–12 Hz) band from parietal electrodes (P3, Pz, P4) and the beta (13–30 Hz) band from frontal electrodes (F3, Fz, F4).  

These steps MUST be implemented in reproducible scripts under `code/`, and any deviation MUST be documented and version‑controlled.

### VII. Statistical Validation and Performance Benchmarks (domain‑specific)

Model evaluation MUST adhere to the statistical procedures outlined in the idea’s *Methodology sketch*:  
- Train a linear discriminant analysis classifier and report accuracy, precision, and recall using 5‑fold cross‑validation.  
- Classification accuracy must meet or exceed the project‑specified benchmark of 65 % to be considered a successful detection of attentional shift signatures.  
- Perform 1,000‑iteration permutation testing; results are only accepted as statistically significant if the empirical p‑value ≤ 0.05.  

All statistical scripts and result files MUST be stored under `code/` and `data/` respectively, with hashes recorded for versioning.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-520-neural-correlates-of-visuospatial-attent.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-520-neural-correlates-of-visuospatial-attent | **Field**: neuroscience | **Ratified**: 2026-06-24
