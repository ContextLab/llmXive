# llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models un" — Research Project Constitution

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
project's `state/projects/PROJ-910-llmxive-follow-up-extending-code2lora-hy.yaml` `updated_at` timestamp.

### VI. Static-Analysis Fidelity (Domain-Specific)

The AST-derived feature vectors (including cyclomatic complexity, depth of
inheritance tree, import graph degree centrality, and token-type histograms)
generated in the `data/` pipeline MUST be deterministic and verifiable against
the source code commits in the RepoPeftBench dataset. Any deviation in the
`ast` module parsing logic or feature calculation between runs invalidates
the `code/` reproducibility claim, as the core hypothesis relies on the
substitution of neural embeddings with these specific syntactic metrics.

### VII. Performance-Latency Trade-off Validation (Domain-Specific)

All reported results MUST include paired measurements of exact-match accuracy
and adapter generation latency. The project explicitly validates the trade-off
between the baseline neural encoder (0.6B parameters) and the proposed
AST-based linear projection; therefore, omitting latency metrics or failing
to perform the required paired t-test against the Code2LoRA-Evo baseline
renders the results incomplete per the project's defined research question.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-910-llmxive-follow-up-extending-code2lora-hy/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-910-llmxive-follow-up-extending-code2lora-hy.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-10.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-910-llmxive-follow-up-extending-code2lora-hy | **Field**: computer science | **Ratified**: 2026-07-10
