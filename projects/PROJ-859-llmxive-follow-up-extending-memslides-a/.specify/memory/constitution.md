# llmXive follow-up: extending "MemSlides: A Hierarchical Memory Driven Agent Framework for Personaliz" — Research Project Constitution

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
project's `state/projects/PROJ-859-llmxive-follow-up-extending-memslides-a.yaml` `updated_at` timestamp.

### VI. Trace Structural Integrity

The validity of the symbolic rule induction is contingent on the precise
preservation of tool-execution trace structure during the data synthesis
phase. As the core research question investigates how structural properties
(e.g., sequence entropy, tool-repetition frequency) determine compressibility,
any corruption or loss of metadata in the synthetic `5,000 multi-turn revision
sessions` dataset invalidates the feature extraction logic. Therefore, the
generation of the synthetic MemSlides benchmark schema MUST log the exact
tool sequence and argument semantic variance for every session to ensure the
structural metrics computed in `code/` are mathematically derivable from the
raw trace logs.

### VII. Latency-Accuracy Trade-off Validation

Evaluation of the compressed agent MUST strictly isolate the performance
impact of the symbolic rule bank from the underlying LLM's generative
capabilities. Following the methodology, the `Edit Accuracy` (fraction of
edits matching ground-truth) and `Retrieval Latency` (time from instruction
to context-ready) must be measured independently on the `500 held-out revision
requests`. The statistical analysis (multiple linear regression) MUST
explicitly correlate structural metrics with the `Edit Accuracy` difference
between the raw memory and compressed memory agents, ensuring that any
observed fidelity loss is directly attributable to the compression ratio and
not confounded by variations in the base agent's execution.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-859-llmxive-follow-up-extending-memslides-a/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-859-llmxive-follow-up-extending-memslides-a.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-859-llmxive-follow-up-extending-memslides-a | **Field**: linguistics | **Ratified**: 2026-07-13
