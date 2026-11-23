# Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations — Research Project Constitution

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
project's `state/projects/PROJ-119-statistical-modeling-of-temporal-depende.yaml` `updated_at` timestamp.

### VI. Time-Series Stationarity and Regime Integrity

The Regime-Switching VAR (RS-VAR) methodology applied to cryptocurrency price returns MUST explicitly validate that the identified volatility regimes correspond to statistically distinct, non-overlapping temporal partitions before estimating regime-specific serial correlation. This principle is grounded in the project's core inquiry regarding "time-varying structure of serial correlation" and "cross-asset dependence" across market regimes; without rigorous confirmation that the inferred regimes represent genuine structural breaks rather than artifacts of rolling window noise, the resulting correlation coefficients cannot be validly interpreted as regime-dependent dynamics.

### VII. Non-Stationary Data Handling and Derivative Consistency

All statistical summaries of "serial correlation" and "cross-asset correlation coefficients" MUST be computed on stationary transformations of the primary price signal (e.g., log-returns) rather than raw price levels, ensuring that the empirical estimates of dependence structures are not confounded by stochastic trends. This requirement is explicitly grounded in the project's validation of the research question, which identifies the "time-varying structure of serial correlation" as the target phenomenon; since raw cryptocurrency prices are inherently non-stationary, computing correlations directly on price levels would violate the statistical assumptions required to answer the research question regarding the evolution of dependence structures.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-119-statistical-modeling-of-temporal-depende/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-119-statistical-modeling-of-temporal-depende.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-10-06.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-119-statistical-modeling-of-temporal-depende | **Field**: statistics | **Ratified**: 2026-10-06
