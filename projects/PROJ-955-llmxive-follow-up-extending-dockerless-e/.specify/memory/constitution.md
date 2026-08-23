# llmXive follow-up: extending "Dockerless: Environment-Free Program Verifier for Coding Agents" — Research Project Constitution

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
project's `state/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e.yaml` `updated_at` timestamp.

### VI. Static-Dynamic Alignment Verification

Every claim regarding the "semantic gap" between static structural features
and dynamic execution ground truth MUST be validated against the specific
SWE-Gym or Multi-SWE-RL test execution logs provided in the `data/` folder.
Static approximations (e.g., control flow graphs generated via `pycg` or
`clang-query`) MUST be explicitly mapped to the dynamic test results (pass/fail)
for the exact same code patch to ensure the correlation analysis is not
contaminated by dataset drift or mismatched versions.

### VII. Failure-Mode Categorization Rigor

When analyzing false positives or false negatives in the static model, every
identified error case MUST be explicitly categorized by its specific code
pattern (e.g., "dynamic dispatch," "external API call," "concurrency race")
as defined in the methodology. A claim that static analysis fails for a
specific behavior is only valid if the `data/` contains at least one
demonstrable instance of that behavior where the static feature vector
diverged from the dynamic ground truth.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-23.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-955-llmxive-follow-up-extending-dockerless-e | **Field**: computer science | **Ratified**: 2026-08-23
