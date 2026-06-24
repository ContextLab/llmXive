# Evaluating the Sensitivity of Common Statistical Tests to Dataset Size — Research Project Constitution

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
project's `state/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta.yaml` `updated_at` timestamp.

### VI. Simulation Fidelity (Domain‑Specific)

All simulated datasets must be generated exactly as described in the
Methodology sketch: normal distributions for t‑test/ANOVA, categorical
distributions for chi‑squared, effect sizes d = 0.2, 0.5, 0.8, and a
sample‑size grid from n = 5 to n = 500 in steps of 5. Each condition must
receive at least 10,000 independent simulation iterations, and the random
seed used for each batch MUST be recorded in `data/simulation_metadata.json`.
These constraints ensure that the empirical error‑rate curves are
statistically stable and comparable across tests.

### VII. Benchmark Validation (Domain‑Specific)

Findings must be corroborated on at least two publicly available small‑sample
datasets (e.g., datasets from the UCI Machine Learning Repository or OpenML)
where ground truth is known or can be approximated. The same analysis
pipeline used for simulations must be applied without modification, and the
resulting error‑rate measurements MUST be reported alongside the simulated
curves. This external validation anchors the simulation results to real‑world
data and satisfies the project’s goal of providing actionable guidance for
resource‑constrained studies.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-341-evaluating-the-sensitivity-of-common-sta | **Field**: statistics | **Ratified**: 2026-06-24
