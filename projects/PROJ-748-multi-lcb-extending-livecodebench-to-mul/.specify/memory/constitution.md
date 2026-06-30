# Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages — Research Project Constitution

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
project's `state/projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul.yaml` `updated_at` timestamp.

### VI. Cross-Language Statistical Rigor

Statistical comparisons of model performance across the 12 supported languages (including C++, Java, and Python) MUST utilize paired t-tests or Wilcoxon signed-rank tests with Bonferroni correction applied to the full set of 288 comparisons (24 models × 12 languages). Single-temperature evaluations are insufficient; the project MUST execute tasks at multiple temperatures (0.2, 0.6, 1.0) to quantify language-specific sensitivity, and results MUST explicitly distinguish between general code-generation capability and Python-specific optimization.

### VII. Contamination Control via Temporal Filtering

To ensure a contamination-free evaluation subset, every task in the Multi-LCB dataset MUST be cross-referenced against the training cutoff dates of the target models (e.g., Qwen, GPT-OSS, CodeLlama). Any task with a release date subsequent to a model's training cutoff MUST be excluded from the analysis of that specific model, ensuring that performance metrics reflect true generalization rather than data memorization.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- All code executions MUST utilize the Docker-based sandbox environment described in the methodology to ensure standardized STDIN/STDOUT handling across all 12 languages.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.
- The Multi-LCB dataset (12 languages, 1,055 tasks each) MUST be fetched from the Hugging Face repository using a pinned commit hash or Zenodo snapshot to ensure version stability.

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

**Project ID**: PROJ-748-multi-lcb-extending-livecodebench-to-mul | **Field**: computer science | **Ratified**: 2026-06-30
