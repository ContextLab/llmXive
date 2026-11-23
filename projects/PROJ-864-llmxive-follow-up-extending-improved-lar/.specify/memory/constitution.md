# llmXive follow-up: extending "Improved Large Language Diffusion Models" — Research Project Constitution

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
project's `state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` `updated_at` timestamp.

### VI. Overfitting Trajectory Isolation

To validate the hypothesis that bidirectional diffusion models exhibit superior resistance to overfitting on limited data, the project MUST strictly isolate the "overfitting-as-a-feature" signal from architectural confounders. This requires:
1.  **Identical Architectural Constraints**: The 100M-parameter autoregressive and bidirectional masked diffusion models MUST share identical embedding dimensions and attention heads, ensuring that performance divergence is attributable solely to the diffusion mechanism and not capacity differences.
2.  **Controlled Data Regime**: The "Micro-Corpus" MUST be strictly limited to 10 million tokens, with a held-out test set of 1M tokens, to force the overfitting regime where the hypothesis is testable.
3.  **Independent Benchmarking**: Final validation MUST utilize an independent benchmark suite (e.g., BigBench or HumanEval subsets) that is explicitly excluded from the training corpus and Micro-Corpus construction to ensure metrics reflect generalization rather than training data memorization.

### VII. CPU-Feasibility Constraint

Given the goal of democratizing access to efficient language model training on standard CPU clusters, every training iteration MUST be executed within a 7GB RAM and 6-hour wall-clock time budget. The project MUST log and verify CPU RAM usage and wall-clock time per epoch to confirm that the bidirectional diffusion model's training protocol remains viable under these strict resource constraints, utilizing CPU-optimized loops (e.g., `torch.compile` on CPU) where applicable.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-07.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-864-llmxive-follow-up-extending-improved-lar | **Field**: linguistics | **Ratified**: 2026-08-07
