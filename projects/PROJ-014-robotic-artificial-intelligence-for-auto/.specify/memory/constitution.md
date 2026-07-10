# Robotic Artificial Intelligence Algorithms for Autonomous Vehicle Navigation — Research Project Constitution

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
project's `state/projects/PROJ-014-robotic-artificial-intelligence-for-auto.yaml` `updated_at` timestamp.

### VI. Sensory Fidelity Ablation Protocol

All experiments MUST systematically ablate input modalities (raw pixels, depth maps, occupancy grids) to isolate the non-linear influence of sensory representation fidelity on learning dynamics. This principle is grounded in the research question's explicit focus on the relationship between "input information density" and "sample efficiency," requiring that every reported efficiency metric be accompanied by the specific sensor fidelity level used to derive it, ensuring the study addresses the trade-off between computational cost and learning capability rather than mere hardware benchmarking.

### VII. Generalization vs. Sample Efficiency Trade-off Verification

Evaluation metrics MUST explicitly quantify both sample efficiency (training steps to convergence) and generalization limits (performance in novel scenarios) to validate the "sweet spot" hypothesis. This requirement is directly derived from the research question's prediction of "generalization limits" and the verification check noting that null results (where abstractions destroy generalization) are as scientifically significant as positive results, necessitating a dual-metric reporting standard that prevents the conflation of training speed with policy robustness.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-014-robotic-artificial-intelligence-for-auto/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-014-robotic-artificial-intelligence-for-auto.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-014-robotic-artificial-intelligence-for-auto | **Field**: robotics | **Ratified**: 2026-07-10
