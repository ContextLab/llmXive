# llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M" — Research Project Constitution

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
project's `state/projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c.yaml` `updated_at` timestamp.

### VI. Input Modality Isolation

The evaluation of state retention MUST strictly control for input dimensionality by isolating the visual encoding variable. As the project hypothesis posits that memory failure stems from high-dimensional visual input overwhelming the context, all experiments comparing the baseline MLLM protocol (raw images) against the proposed text-only agent MUST utilize the identical "3D Maze" environment instances generated from the RNG-Bench codebase, differing only in the renderer output (ASCII grids and JSON event logs vs. raw visual frames). This principle is grounded in the "Methodology sketch" which mandates converting raw visual grid frames into deterministic ASCII representations to ensure the "Memory Gap" metric measures state retention rather than visual processing capacity.

### VII. Resource-Constrained Execution Validation

All inference loops MUST be validated against strict computational constraints (2-core CPU, 7GB RAM, 6-hour execution window) using a quantized 3B parameter text-only model (e.g., Qwen2-3B or Llama-3-8B-Instruct at 4-bit). The project MUST log CPU usage and peak RAM consumption during the agent loop to prove that the proposed architectural pattern (text-only with explicit symbolic state) remains feasible on free-tier runners without requiring massive GPU resources or context expansion, as explicitly required by the "Methodology sketch" and "Motivation" sections.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-13.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-875-llmxive-follow-up-extending-beyond-the-c | **Field**: computer science | **Ratified**: 2026-07-13
