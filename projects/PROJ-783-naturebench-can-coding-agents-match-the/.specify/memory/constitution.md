# NatureBench: Can Coding Agents Match the Published SOTA of Nature-Family Papers? — Research Project Constitution

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
project's `state/projects/PROJ-783-naturebench-can-coding-agents-match-the.yaml` `updated_at` timestamp.

### VI. Abstraction Distance Quantification

Every task's "abstraction distance" score MUST be derived from the explicit
expert rubric evaluating the frequency of standard library functions versus
novel algorithmic derivation, as defined in the methodology sketch. No
task may be assigned a distance score without a recorded expert rating
(1–5 scale) linked to the specific NatureBench task ID.

### VII. Independent Validation Protocol

All agent success metrics MUST be calculated by comparing final numerical
outputs against the *published numerical results* from the target Nature-family
papers. Validation MUST NOT rely on the agent's internal confidence scores,
intermediate code correctness, or the textual method description alone.
Error categorization MUST strictly isolate "Wrong Method Choice" failures
for the primary correlation analysis against the abstraction distance metric.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-783-naturebench-can-coding-agents-match-the/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- Agent execution runs MUST enforce the strict 4-hour wall-clock timeout
  per task to align with the original study's budget, ensuring all runs
  fit within the 6-hour GitHub Actions limits (7GB RAM, 2 CPU).

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-783-naturebench-can-coding-agents-match-the.yaml` `artifact_hashes` map.
- Raw data (NatureBench 90 tasks and ground-truth SOTA values) is preserved
  unchanged; derivations (e.g., error logs, parsed results) are written to
  new filenames.
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
**1.0.0** — ratified 2026-06-30.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-783-naturebench-can-coding-agents-match-the | **Field**: linguistics | **Ratified**: 2026-06-30
