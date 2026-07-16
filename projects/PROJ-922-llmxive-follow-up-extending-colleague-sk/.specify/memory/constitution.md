# llmXive follow-up: extending "COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Di" — Research Project Constitution

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
project's `state/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk.yaml` `updated_at` timestamp.

### VI. Deterministic Evaluation of Agent Behavior

Every evaluation metric MUST be derived from a deterministic Python scoring script
that compares model outputs against explicit, pre-defined rule sets rather than
subjective judgment. Specifically:
1. **Heuristic Adherence** MUST be calculated via binary matching against capability
   track rules defined in the input profiles.
2. **Style Consistency** MUST be quantified via keyword and structure frequency analysis
   against behavior track definitions.
3. **Hallucination Rate** MUST be determined by fact-checking against independent
   source traces and ground-truth task context using string matching or simple entailment,
   never against the model's own generated text.
This principle is grounded in the "Methodology sketch" and "Expected results" sections,
which mandate the use of rule-based scoring scripts to ensure reproducibility and
objectivity in measuring hallucination and style drift.

### VII. Resource-Constrained Model Validation

All inference experiments MUST be conducted using quantized small language models
(e.g., Llama-3-8B-Q4, Phi-3-mini) on CPU-only backends (e.g., `llama.cpp` or
`transformers` with `torch_dtype=torch.float32` and no GPU) to validate that
structural prompt separation compensates for limited model capacity.
No results derived from GPU-accelerated or full-parameter models are valid for
the primary hypothesis testing described in this project. This requirement is
explicitly derived from the "Motivation" section's goal of deploying reliable
agents on standard hardware and the "Methodology sketch" which specifies the
CPU-only inference backend.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-16.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-922-llmxive-follow-up-extending-colleague-sk | **Field**: computer science | **Ratified**: 2026-07-16
