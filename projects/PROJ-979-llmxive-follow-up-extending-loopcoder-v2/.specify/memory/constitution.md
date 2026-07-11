# llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali" — Research Project Constitution

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
project's `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml` `updated_at` timestamp.

### VI. Internal State Calibration Validity

The project explicitly tests the correlation between initial hidden state entropy and convergence trajectory. Therefore, any metric derived from the model's internal confidence (semantic entropy) MUST be mathematically decoupled from the ground-truth evaluation metric (correctness on HumanEval/MBPP) to prevent circular validation. The methodology for extracting the "uncertainty proxy" via a single forward pass ($k=1$) and the subsequent "trajectory tracking" via iterative passes ($k=1, 2, 3$) MUST be strictly separated in the codebase to ensure the correlation analysis reflects a genuine disconnect or alignment rather than data leakage.

### VII. Dynamic Compute Budget Verification

Given the research goal of replacing static loop counts with dynamic routing, every experiment MUST report both the final accuracy (pass@1) and the computational cost (FLOPs or loop count) for each strategy. The "Router Simulation" artifact, if generated, MUST demonstrate that the FLOPs savings derived from the entropy-based logistic regression model do not come at the expense of a statistically significant drop in accuracy compared to the static $k=2$ baseline, as defined by the paired t-test protocol in the methodology.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-979-llmxive-follow-up-extending-loopcoder-v2 | **Field**: computer science | **Ratified**: 2026-07-11
