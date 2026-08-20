# Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems — Research Project Constitution

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
project's `state/projects/PROJ-212-exploring-the-impact-of-network-structur.yaml` `updated_at` timestamp.

### VI. Numerical Stability in Dynamical Integration

All Kuramoto oscillator simulations MUST utilize the RK45 integration method
with explicitly documented step-size tolerances to ensure the stability of
the synchronization order parameter $r(t)$ over the required duration (t > 100).
Random initial phases and coupling strengths MUST be seeded consistently to
prevent integration drift artifacts from being misidentified as topological
effects.

*Grounding*: This principle is derived from the "Methodology sketch" which
specifies integrating the Kuramoto model "via RK45 method" and measuring
"synchronization order parameter r(t) over time" to determine robustness
thresholds. The requirement for numerical stability is intrinsic to the
validity of the regression analysis between topological metrics and
synchronization thresholds described in "Expected results".

### VII. Statistical Rigor in Topological Correlation

Correlations between topological metrics (degree distribution, clustering
coefficient, average path length) and synchronization robustness MUST be
validated using linear and polynomial regression with a minimum R² > 0.6
and 95% confidence intervals. Feature significance MUST be confirmed via
ANOVA with a p-value threshold < 0.05, and all models MUST undergo
10-fold cross-validation on the dataset splits to prevent overfitting to
specific network instances.

*Grounding*: This principle is explicitly grounded in the "Expected results"
section which mandates "Statistical significance will be confirmed via
regression analysis (R² > 0.6)... with confidence intervals computed at 95%
level" and the "Methodology sketch" which lists "Perform linear and polynomial
regression", "Apply ANOVA... with p-value threshold < 0.05", and "Validate
results via 10-fold cross-validation".

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-212-exploring-the-impact-of-network-structur/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-212-exploring-the-impact-of-network-structur.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-20.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-212-exploring-the-impact-of-network-structur | **Field**: physics | **Ratified**: 2026-08-20
