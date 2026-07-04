# Predicting Material Stability using Machine Learning and DFT Calculations — Research Project Constitution

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
project's `state/projects/PROJ-116-predicting-material-stability-using-mach.yaml` `updated_at` timestamp.

### VI. Numerical-Stability and Convex-Hull Precision

Given the project's focus on distinguishing metastable phases within 0.05 eV/atom of the convex hull, all energy calculations and model predictions MUST maintain sufficient floating-point precision to avoid rounding errors that could misclassify stability. The `code/` MUST explicitly document the use of `pymatgen`'s `PhaseDiagram` class for independent convex hull construction and MUST verify that the distance-to-hull calculations are not dominated by numerical noise. This principle is grounded in the "Methodology sketch" which specifies stratification by distance to the convex hull and the "Expected results" which target a specific recall improvement for phases near this boundary.

### VII. Local-Feature Grounding and Artifact Traceability

Any claim regarding the superiority of local coordination features over bulk descriptors MUST be supported by explicit feature-importance analysis derived from the trained Gradient Boosting Regressor. The project MUST not rely on aggregate performance metrics alone; the `code/` MUST generate and store specific plots (e.g., SHAP values or permutation importance) that isolate the contribution of Voronoi tessellation statistics and bond-length distributions. This requirement is grounded in the "Methodology sketch" step 5 ("Analyze feature importance") and the "Research question" which explicitly asks to what extent local features capture instability mechanisms that bulk descriptors fail to predict.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-116-predicting-material-stability-using-mach/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-116-predicting-material-stability-using-mach.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-04.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-116-predicting-material-stability-using-mach | **Field**: chemistry | **Ratified**: 2026-07-04
