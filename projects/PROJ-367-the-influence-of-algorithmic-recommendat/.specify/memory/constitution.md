# The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning — Research Project Constitution

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
project's `state/projects/PROJ-367-the-influence-of-algorithmic-recommendat.yaml` `updated_at` timestamp.

### VI. Causal Independence Validation

The project MUST explicitly verify that the predictor variable (recommendation diversity) is not mechanically derived from the outcome variable (enrollment choices). As the research question posits a causal influence of algorithmic input on human behavioral output, the methodology must ensure that the "system's suggestion" and the "user's final action" remain distinct data sources. Any analysis that conflates these or fails to account for user agency (e.g., ignoring recommendations) violates the foundational premise of the study as validated in the phenomenon-vs-method check.

### VII. Behavioral Agency Preservation

The study design MUST separate the predictor (system recommendation logs) from the outcome (actual enrollment choices) to test the specific hypothesis regarding algorithmic influence on learner exploration. The methodology must be robust enough to detect null results, acknowledging that learner agency and intrinsic interests may override algorithmic homogenization. Consequently, the analysis must not assume a positive correlation; the evaluation framework must treat a null result as a significant, publishable finding that challenges assumptions about the power of recommender systems in educational contexts.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-367-the-influence-of-algorithmic-recommendat.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-30.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-367-the-influence-of-algorithmic-recommendat | **Field**: psychology | **Ratified**: 2026-07-30
