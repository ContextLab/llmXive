# llmXive follow-up: extending "https://arxiv.org/abs/2607.07508" — Research Project Constitution

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
project's `state/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv.yaml` `updated_at` timestamp.

### VI. Asynchronous Staleness Sensitivity Analysis

All experimental regimes MUST explicitly vary the gradient staleness parameter (low, fixed high, adaptive) to map the divergence threshold for the specific sub-1B parameter model being tested. Convergence stability MUST be quantified by the variance of the reward signal and the norm of gradient updates, with divergence strictly defined as a sustained drop in reward below the baseline threshold on the GSM8K test split. This principle is grounded in the project's core research question regarding the modulation of critical staleness thresholds by parameter count and the methodology's requirement to simulate variable CPU latency via artificial sleep intervals.

### VII. Resource-Constrained Execution Validity

Every training run MUST be constrained to a maximum of 6 hours on a 2-CPU, 7GB RAM runner environment. The implementation MUST utilize quantized models (e.g., via `bitsandbytes` for CPU execution) and limit batch sizes/steps to ensure memory footprint compliance. Statistical validation (two-sample t-test) comparing convergence stability across regimes is mandatory to confirm that observed effects are not artifacts of resource exhaustion. This principle is grounded in the methodology's explicit runtime constraints and the motivation to enable robust, decentralized agentic workflows without GPU dependency.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-21.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-1032-llmxive-follow-up-extending-https-arxiv | **Field**: other | **Ratified**: 2026-08-21
