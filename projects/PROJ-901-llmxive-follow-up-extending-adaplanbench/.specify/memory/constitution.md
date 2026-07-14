# llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age" — Research Project Constitution

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
project's `state/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench.yaml` `updated_at` timestamp.

### VI. Dual-Track Architecture Integrity

The separation between the deterministic constraint-tracking module and the
natural language generation model (e.g., Phi-3-mini) MUST be maintained as
distinct code paths. The rule-based conflict resolution logic MUST be
validated independently of the generative model's output to ensure that
constraint adherence metrics (>85%) reflect the explicit memory module's
efficacy rather than stochastic model behavior. This principle is grounded
in the "Methodology sketch" which defines a dual-track agent where a
small SLM handles generation while a deterministic key-value store logs
constraints, and the "Expected results" which attribute performance gains
specifically to the explicit memory module mitigating failure modes.

### VII. Resource-Constrained Execution Validation

All experimental runs MUST explicitly log CPU usage and memory footprint to
verify adherence to the GitHub Actions free-tier limits (2 CPU, 7GB RAM).
Performance claims regarding the scalability of the dual-track approach
MUST be corroborated by these resource logs to ensure the architecture
remains viable in constrained deployment environments. This principle is
grounded in the "Methodology sketch" section which mandates "Resource
Monitoring" to verify limits, and the "Motivation" which emphasizes the
need for a "scalable, deployment-ready solution for constrained environments."

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-14.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-901-llmxive-follow-up-extending-adaplanbench | **Field**: linguistics | **Ratified**: 2026-07-14
