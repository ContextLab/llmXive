# Evaluating the Impact of Code Generation Models on Code Documentation Completeness — Research Project Constitution

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
project's `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` `updated_at` timestamp.

### VI. AST-Grounded Completeness Evaluation

Completeness metrics for documentation MUST be derived strictly from the
structural comparison between generated docstrings and the Abstract Syntax
Tree (AST) extracted signatures of the target public methods. As defined in
the methodology, the `python ast` module serves as the ground truth for
parameter existence; any claim of "parameter omission" in the results MUST
be traceable to a specific mismatch between the parsed AST parameters and
the parsed docstring parameters. This principle prohibits reliance on
semantic similarity scores (e.g., from `sentence-transformers/all-MiniLM-L6-v2`)
as the sole indicator of completeness; semantic similarity is auxiliary,
while AST matching is the primary validator for the "70–80% coverage" hypothesis.

### VII. Deterministic Generation Constraints

To ensure the "6-hour job time limit" and statistical validity of the
Wilcoxon signed-rank test, the generation pipeline MUST enforce a hard
limit of 1,000 methods per repository and a fixed temperature of 0.2.
The model configuration (`Salesforce/codegen-350M-mono` with 4-bit
quantization) MUST remain constant across all 20 PyPI leaderboard
repositories. Any deviation in the quantization scheme or temperature
parameter invalidates the comparative analysis between human and LLM
documentation, requiring a full re-run of the specific repository batch
to maintain the integrity of the paired statistical test.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-318-evaluating-the-impact-of-code-generation/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-08.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-318-evaluating-the-impact-of-code-generation | **Field**: computer science | **Ratified**: 2026-08-08
