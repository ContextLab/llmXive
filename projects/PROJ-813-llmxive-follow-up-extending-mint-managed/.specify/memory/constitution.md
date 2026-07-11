# llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs" — Research Project Constitution

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
project's `state/projects/PROJ-813-llmxive-follow-up-extending-mint-managed.yaml` `updated_at` timestamp.

### VI. Simulation Determinism & Topological Fidelity

All discrete-event simulations utilizing the SimPy environment MUST be
configured to produce identical wall-clock time trajectories for identical
input seeds, ensuring that performance gains attributed to the "Topological
Lookahead" policy are not artifacts of simulation randomness. The constructed
"LoRA Topology Graph" (pairwise parameter overlap matrix) MUST be derived
strictly from the synthesized 10,000 adapters' rank and sparsity patterns
without leakage from the access trace, preserving the independence of the
topology generation from the workload dynamics as specified in the
Methodology sketch.

### VII. Statistical Rigor in Latency Evaluation

Comparative analysis between the "Topological Lookahead" policy and the FCFS
baseline MUST employ paired t-tests (or non-parametric equivalents where
normality fails) on the full distribution of latency measurements across the
10^6 request trace. Claims of "at least 15% reduction" in cold-start latency
MUST be supported by the resulting p-values and confidence intervals,
preventing over-interpretation of marginal performance differences in
high-variance system simulations.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-813-llmxive-follow-up-extending-mint-managed/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-813-llmxive-follow-up-extending-mint-managed.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-813-llmxive-follow-up-extending-mint-managed | **Field**: computer science | **Ratified**: 2026-07-11
