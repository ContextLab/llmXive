# Evaluating the Explainability of LLM-Based Bug Fixes — Research Project Constitution

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
project's `state/projects/PROJ-130-evaluating-the-explainability-of-llm-bas.yaml` `updated_at` timestamp.

### VI. Explainability Artifact Transparency

All explainability outputs—attention visualizations, saliency maps, and generated natural‑language rationales—MUST be saved under a dedicated `explanations/` directory using a standardized naming scheme (`<bug-id>_attention.png`, `<bug-id>_saliency.npy`, `<bug-id>_rationale.txt`). Each file MUST be accompanied by a JSON metadata record that includes the model revision, random seed, prompt text, and processing parameters. This ensures that every explainability artifact can be independently inspected and reproduced, as required by the methodology sketch.

### VII. Benchmark Dataset Integrity

The Defects4J v2.0 benchmark MUST serve as the sole source of buggy programs and test suites for this project. The original dataset archive MUST be stored unchanged under `data/defects4j/`; any derived subsets or filtered views MUST be version‑controlled and traceable to the original rows. Model weights for CodeLlama‑7B‑Instruct must be retrieved from the official HuggingFace repository (`codellama/CodeLlama-7b-Instruct-hf`) and the exact revision identifier used MUST be recorded in `code/model_revision.txt`. These constraints ground the project’s reproducibility in the concrete data and model assets described in the idea body.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/`
  pins every Python dependency, including specific versions of `transformers`, `datasets`, `captum`, `scikit-learn`, and `pytest`.
- The project must fetch the Defects4J v2.0 dataset from its canonical repository and store it under `data/defects4j/` without modification; the original archive must be retained.
- Model weights for CodeLlama‑7B‑Instruct must be retrieved from the official HuggingFace repository (`codellama/CodeLlama-7b-Instruct-hf`) and the exact revision identifier used must be recorded in `code/model_revision.txt`.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention, and must accept a `--bug-id` argument to process any specific bug from the Defects4J set.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-130-evaluating-the-explainability-of-llm-bas.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-06-24.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-130-evaluating-the-explainability-of-llm-bas | **Field**: computer science | **Ratified**: 2026-06-24
