# llmXive follow-up: extending "Function-Aware Fill-in-the-Middle as Mid-Training for Coding Agent Fou" — Research Project Constitution

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
project's `state/projects/PROJ-1074-llmxive-follow-up-extending-function-awa.yaml` `updated_at` timestamp.

### VI. Structural Generalization Validation

The project's core hypothesis—that the "function-call" inductive bias is structural rather than syntactic—MUST be validated by isolating the training signal from code-specific syntax. As defined in the Methodology sketch, any mid-training corpus derived from logical or mathematical sources (e.g., GSM8K, LogiQA) MUST be formatted strictly as pseudo-code function blocks (`def step_N(): return derived_fact`) to ensure the FIM mechanism targets dependency resolution logic rather than programming language syntax. Performance gains on non-code benchmarks (LogiQA, BFCL) MUST be statistically significant (via paired t-test or Wilcoxon signed-rank test) compared to both a standard causal language modeling control and a no-mid-training baseline to confirm transferability.

### VII. Synthetic Data Leakage Prevention

To ensure the validity of the "structural bias" claim, the project MUST enforce strict separation between training and evaluation artifacts. As specified in the Methodology sketch, the synthetic "logical function" training data derived from GSM8K or logical reasoning chains MUST NOT contain direct encodings of answers to the evaluation benchmarks (LogiQA, BFCL). The Reference-Validator Agent MUST verify that the "logical function" format used in the 500k training examples does not inadvertently leak test-set information, ensuring that performance improvements stem from the learned reasoning mechanism rather than data memorization.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-1074-llmxive-follow-up-extending-function-awa/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-1074-llmxive-follow-up-extending-function-awa.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-19.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-1074-llmxive-follow-up-extending-function-awa | **Field**: computer science | **Ratified**: 2026-08-19
