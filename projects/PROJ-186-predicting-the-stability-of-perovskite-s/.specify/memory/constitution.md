# Predicting the Stability of Perovskite Structures Using Machine Learning — Research Project Constitution

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
project's `state/projects/PROJ-186-predicting-the-stability-of-perovskite-s.yaml` `updated_at` timestamp.

### VI. Numerical Stability and Descriptor Rigor

All regression targets (decomposition energy in eV/atom) and descriptors
(Goldschmidt tolerance factor *t*, octahedral factor *μ*, ionic radii,
electronegativity) MUST be calculated using the specific `pymatgen` periodic-table
utilities and thermodynamic definitions outlined in the methodology sketch.
Models MUST be evaluated strictly on the held-out test set defined by the
80/20 stratified split to ensure that performance metrics (RMSE ≤ 0.15 eV/atom)
are not inflated by data leakage or descriptor miscalculation. This principle
is grounded in the "Descriptor calculation" and "Evaluation" sections of the
project idea, which explicitly define the chemical descriptors and the
performance threshold required to validate the hypothesis that data-driven
models can generalize stability relationships.

### VII. Combinatorial Screening Validity

The virtual screening phase MUST strictly adhere to the defined combinatorial
library constraints (A-site: alkali, alkaline-earth, post-transition; B-site:
transition metals, Sn, Ge; X: Cl, Br, I) and the specific stability cutoff
(predicted decomposition energy < -0.1 eV/atom or temperature > 150 °C).
Any candidate flagged for experimental follow-up MUST be traceable to this
specific enumeration and threshold logic. This principle is grounded in the
"Virtual screening" and "Expected results" sections of the idea body, which
mandate the generation of a ranked list of ≥ 200 hypothetical compositions
and the specific criteria for identifying the top 10 candidates.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-186-predicting-the-stability-of-perovskite-s.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-05.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-186-predicting-the-stability-of-perovskite-s | **Field**: materials science | **Ratified**: 2026-07-05
