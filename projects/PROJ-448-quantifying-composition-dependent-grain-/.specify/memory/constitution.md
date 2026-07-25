# Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys — Research Project Constitution

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
project's `state/projects/PROJ-448-quantifying-composition-dependent-grain-.yaml` `updated_at` timestamp.

### VI. Computational Thermodynamics Consistency

Segregation energy calculations derived from Quantum ESPRESSO simulations on BCC grain boundary supercells MUST utilize thermodynamic parameters consistent with the TCFE9 CALPHAD database for Fe-based systems. All McLean isotherm model inputs (temperature-dependent parameters) MUST be explicitly documented in `code/` to ensure alignment with the 500-900K extraction range specified in the methodology.

*Grounding: This principle is mandated by the "Methodology sketch" which requires extracting equilibrium phase compositions from TCFE9 and computing segregation energies using DFT on pre-built supercell models, followed by McLean isotherm calculations. Consistency between the DFT inputs and the CALPHAD thermodynamic database is essential for the validity of the composition-segregation relationships.*

### VII. Multicomponent Interaction Validation

Empirical composition-segregation functions fitted via linear regression MUST include interaction terms for multicomponent effects (e.g., Cr-Mo, Cr-V) and be validated against k-fold cross-validation (k=5) across the Fe-Cr-Mo, Fe-Cr-V, and Fe-Mo-V ternary systems. Statistical significance thresholds (p<0.05) MUST be applied uniformly when assessing the emergence of cooperative segregation effects.

*Grounding: This principle directly addresses the "Methodology sketch" requirement to "Fit empirical composition-segregation functions using linear regression with interaction terms for multicomponent effects" and "Perform cross-validation across alloy systems (k-fold, k=5)". It also enforces the "Expected results" criterion that statistical significance at p<0.05 across 5+ alloy systems constitutes publishable evidence, specifically targeting the non-linear relationships and threshold concentrations mentioned.*

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-448-quantifying-composition-dependent-grain-/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-448-quantifying-composition-dependent-grain-.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-25.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-448-quantifying-composition-dependent-grain- | **Field**: materials science | **Ratified**: 2026-07-25
