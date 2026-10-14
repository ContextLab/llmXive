# llmXive follow-up: extending "From Activation to Causality: Discovery of Causal Visual Representatio" — Research Project Constitution

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

Review records are bound to the content of the artifact they reviewed; a
record goes stale when that artifact changes. The platform does this
bookkeeping. `state/projects/PROJ-956-llmxive-follow-up-extending-from-activat.yaml` belongs to the platform:
project code, tests and tasks MUST NOT read it, write it, or create a
`state/` directory inside the project.

### VI. Validation Independence

The temporal stability metrics used to evaluate the causal-classification
hypothesis (trial-to-trial variance of peak BOLD response and AR(1)
autocorrelation coefficients) MUST be computed directly from the raw
pre-processed fMRI time-series, not from any quantity derived from the
counterfactual generation process that produced the "True Causal" vs.
"False Positive" voxel labels. As stated in the methodology's Validation
Independence Check, the stability metrics and the classification labels
MUST remain independent measurement sources, since the project's central
claim is that raw time-series properties provide a non-generative
validation signal for causal claims.

### VII. Statistical Comparability

Group comparisons between "True Causal" (Group A) and "False Positive"
(Group B) voxels MUST control for confounds explicitly identified in the
methodology: (a) temporal metrics MUST be normalized by each voxel's
overall mean activation strength to control for amplitude differences
unrelated to stability, and (b) voxels MUST be matched for concept type
(e.g., faces, hands) before applying the paired Wilcoxon signed-rank test
(or t-test where normality holds). Effect sizes (Cohen's d) MUST be
reported alongside p-values for both the variance and autocorrelation
metrics.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-956-llmxive-follow-up-extending-from-activat/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- The pre-processed fMRI time-series data (NSD dataset) and the associated
  voxel classification labels from the original BrainCause repository MUST
  be fetched from the same canonical source on every run, and their
  checksums recorded under `data/` per Principle III.

## Data Hygiene

- When the analysis needs checksums of its own data (to verify a download
  or detect a changed input), it writes them to a manifest under `data/`
  (for example `data/checksums.sha256`). It never records hashes under
  `state/`, which is the platform's.
- Raw data is preserved unchanged; derivations are written to new
  filenames. This applies in particular to the raw BOLD time-series: all
  extracted per-voxel metrics (trial-to-trial variance, AR(1) coefficients,
  normalization factors) MUST be written to derived files rather than
  modifying the raw time-series.
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
**1.0.0** — ratified 2026-10-14.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-956-llmxive-follow-up-extending-from-activat | **Field**: computer science | **Ratified**: 2026-10-14
