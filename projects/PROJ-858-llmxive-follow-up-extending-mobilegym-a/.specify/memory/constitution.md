# llmXive follow-up: extending "MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mo" — Research Project Constitution

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
project's `state/projects/PROJ-858-llmxive-follow-up-extending-mobilegym-a.yaml` `updated_at` timestamp.

### VI. Dynamic Curriculum Traceability

The State-Guided Curriculum scheduler's selection logic MUST be explicitly logged for every batch, recording the specific "State Coverage Vector" metrics (e.g., `app_settings.dark_mode`, `message_list.unread_count` transitions) that triggered the selection of task parameters. This ensures the dynamic prioritization strategy (targeting the 30-70% success rate "sweet spot") can be audited to confirm it is driven by actual state-space coverage rather than stochastic noise. This requirement is grounded in the methodology's reliance on real-time agent state-space coverage to accelerate convergence.

### VII. Sim-to-Real Transfer Variance Control

Evaluation of Sim-to-Real transfer robustness MUST explicitly report the variance of success rates across complex, high state-dependency apps, not just mean performance. The experimental agent's superiority is contingent on demonstrating lower variance compared to the static baseline, confirming that targeted state exploration yields more generalizable policies. This principle is derived from the expected results which mandate lower performance variance as the primary evidence of robustness.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-858-llmxive-follow-up-extending-mobilegym-a/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- The training execution MUST adhere to the 6-hour wall-clock time cap on the 64-core CPU runner to ensure consistency with the GHA limits defined in the methodology.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-858-llmxive-follow-up-extending-mobilegym-a.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.
- The MobileGym-Bench task definitions (256 test + 160 train tasks) and the MobileGym source code MUST be versioned and checksummed immediately upon acquisition to ensure the "State Coverage Vector" instrumentation operates on the exact baseline specified.

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
**1.0.0** — ratified 2026-07-12.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-858-llmxive-follow-up-extending-mobilegym-a | **Field**: computer science | **Ratified**: 2026-07-12
