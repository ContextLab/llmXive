# Evaluating the Effectiveness of Differential Privacy in Federated Learning — Research Project Constitution

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
project's `state/projects/PROJ-044-evaluating-the-effectiveness-of-differen.yaml` `updated_at` timestamp.

### VI. Heterogeneity-Aware Evaluation

The project MUST explicitly isolate and report performance metrics for
"minority clients" (defined by low label frequency in Dirichlet-partitioned
datasets) separately from "majority clients" and the global average.
This principle is grounded in the research question's focus on how
heterogeneity modulates the privacy-utility trade-off and the methodology's
requirement to use Dirichlet concentration parameters (α ∈ {0.1, 0.5, 1.0})
to define imbalanced distributions. All evaluation scripts MUST compute
client-level accuracy on held-out local test data to detect disproportionate
degradation in under-represented groups, as specified in the expected results.

### VII. Statistical Rigor for Privacy-Utility Curves

Every claim regarding the "critical heterogeneity threshold" or disproportionate
degradation of privacy budgets (ε < 0.5) MUST be supported by paired t-tests
(p < 0.05) comparing DP vs. non-DP baselines and majority vs. minority client
accuracies. This principle is grounded in the methodology's explicit
requirement to run 5 independent seeds per configuration and perform statistical
analysis on the convergence speed and accuracy metrics across varying ε and α
values. Visualizations MUST overlay minority-client degradation curves against
global accuracy to substantiate statistical findings.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-044-evaluating-the-effectiveness-of-differen.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-11.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-044-evaluating-the-effectiveness-of-differen | **Field**: computer science | **Ratified**: 2026-07-11
