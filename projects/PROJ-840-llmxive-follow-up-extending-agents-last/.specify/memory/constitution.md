# llmXive follow-up: extending "Agents' Last Exam" — Research Project Constitution

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
project's `state/projects/PROJ-840-llmxive-follow-up-extending-agents-last.yaml` `updated_at` timestamp.

### VI. Execution Trace Granularity and Diagnostic Classification

Every failure in the Agents' Last Exam (ALE) tasks executed under this project MUST be annotated and classified as either a "State Persistence Error" or a "Reasoning Deficit" based on the execution logs. This classification is derived from the project's specific methodology of parsing agent execution logs to determine if an action contradicted the current environment state (e.g., editing a deleted file) or represented a logical planning failure. This principle mandates that the `code/` directory contains the specific rule-based heuristics and small LLM prompts used to perform this annotation, ensuring that the distinction between memory management failures and reasoning gaps is explicitly captured in the project data.

### VII. Resource-Constrained Context Checkpointing Validation

Any intervention implemented to improve pass rates MUST utilize a lightweight, CPU-based "Context-Checkpointing" mechanism that injects compressed summaries of the file system state and variable values into the agent's context window at fixed intervals (N=1 to 5 steps). This principle is grounded in the project's hypothesis that state persistence is the primary failure mode and that resource-efficient algorithmic solutions, rather than model scaling, are the appropriate remedy. Consequently, all experimental runs MUST be capped to fit within the 6-hour GitHub Actions job limit and executed on a fixed, small open-weight model (e.g., 7B parameters) capable of running within 7GB RAM, ensuring the results directly validate the efficacy of lightweight interventions on constrained hardware.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-840-llmxive-follow-up-extending-agents-last.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-840-llmxive-follow-up-extending-agents-last | **Field**: computer science | **Ratified**: 2026-07-12
