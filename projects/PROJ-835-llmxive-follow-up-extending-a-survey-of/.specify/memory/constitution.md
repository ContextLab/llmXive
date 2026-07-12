# llmXive follow-up: extending "A Survey of Large Audio Language Models: Generalization, Trustworthine" — Research Project Constitution

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
project's `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` `updated_at` timestamp.

### VI. CPU-Only Inference Constraint

All feature extraction and classification tasks MUST execute exclusively on
CPU resources without GPU acceleration, as defined in the "Methodology sketch"
which mandates a "CPU-only environment" and "2-core CPU runner" to validate
the feasibility of edge deployment. The frozen audio encoder (e.g., distilled
Whisper Base or HuBERT Base) and the binary classifier (Logistic Regression)
MUST be verified to run within the 7GB RAM and 6-hour runtime constraints
specified for the project's resource profiling.

### VII. Latent-Space Anomaly Detection Protocol

The project MUST adhere to a strict protocol where safety gating is derived
solely from statistical anomalies in the latent embedding space of pre-trained
audio encoders, as posited in the "Research question" and "Expected results."
The methodology MUST distinguish between benign inputs and cross-modal
jailbreak samples (including inaudible prompts and adversarial noise) by
training a lightweight classifier on fixed-dimensional embeddings rather than
retraining the base model. Evaluation MUST prioritize recall (>85% target)
for malicious inputs using precision, recall, and F1-score metrics on a held-
out test set derived from original benchmark metadata (e.g., LLaMA-Adapter,
AudioBench) to ensure independence from embedding statistics.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-835-llmxive-follow-up-extending-a-survey-of/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-835-llmxive-follow-up-extending-a-survey-of | **Field**: computer science | **Ratified**: 2026-07-12
