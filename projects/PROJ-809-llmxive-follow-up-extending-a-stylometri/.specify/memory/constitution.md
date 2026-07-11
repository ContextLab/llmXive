# llmXive follow-up: extending "A Stylometric Application of Large Language Models" — Research Project Constitution

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
project's `state/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri.yaml` `updated_at` timestamp.

### VI. Lightweight Modeling Fidelity

All stylometric experiments MUST utilize character-level n-gram models (order $n=4$ to $6$) implemented via CPU-efficient libraries (e.g., `scikit-learn` `CountVectorizer` or custom hash-maps) as specified in the Methodology. The use of transformer-based models or GPU-accelerated fine-tuning is strictly prohibited for the core "predictive comparison" validation, ensuring the project remains within the defined low-resource constraint. This principle is grounded in the project's explicit goal to test if stylometric signals persist in technical writing without requiring the computational cost of large transformers.

### VII. Domain-Constraint Sensitivity

Evaluation MUST explicitly include synthetic "hybrid" abstracts created by swapping sentences between authors to verify that the "predictive comparison" signal degrades when authorial consistency is broken. This requirement ensures the metric distinguishes between true stylistic habits and mere topical content, directly addressing the risk that rigid scientific abstract syntax might obscure authorial individuality.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-11.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-809-llmxive-follow-up-extending-a-stylometri | **Field**: computer science | **Ratified**: 2026-07-11
