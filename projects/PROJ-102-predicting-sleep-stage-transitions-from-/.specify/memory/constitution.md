# Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning — Research Project Constitution

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
project's `state/projects/PROJ-102-predicting-sleep-stage-transitions-from-.yaml` `updated_at` timestamp.

### VI. EEG Signal Integrity and Preprocessing Fidelity

Given the project's reliance on single-channel scalp EEG (Fpz-Cz) from the Sleep-EDF database to detect subtle spectral shifts (e.g., alpha-to-theta) and temporal entropy changes, all preprocessing steps (bandpass filtering 0.5–45 Hz, 50/60 Hz notch removal) MUST be implemented as immutable pipeline stages in `code/`. The raw signal must never be modified in place; any artifact removal or normalization must generate a new file with a documented derivation hash. This ensures that the specific "transition windows" (60-second segments centered on stage changes) remain mathematically traceable to the original PhysioNet source, preventing signal distortion that could obscure the distinct dynamics of NREM versus REM transitions.

### VII. Computational Constraints and Model Parsimony

In alignment with the project's explicit resource constraints (CPU-only execution within a 6-hour GitHub Actions window, <100k parameters, 7GB RAM limit), the model architecture (1D-CNN or LSTM) MUST be strictly validated against these bounds before training begins. The `code/` must include automated checks that fail the build if the parameter count exceeds the limit or if memory usage predictions exceed the available RAM. This principle ensures that the "lightweight" methodology required for wearable device applicability is not compromised by model complexity, and that all reported transition prediction accuracies are derived from models that can realistically run on the target hardware.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-102-predicting-sleep-stage-transitions-from-/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-102-predicting-sleep-stage-transitions-from-.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-12.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-102-predicting-sleep-stage-transitions-from- | **Field**: neuroscience | **Ratified**: 2026-07-12
