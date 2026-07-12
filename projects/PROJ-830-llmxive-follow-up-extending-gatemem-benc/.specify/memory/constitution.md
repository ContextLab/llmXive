# llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo" — Research Project Constitution

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
project's `state/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc.yaml` `updated_at` timestamp.

### VI. Governance-Utility Trade-off Validation

Every evaluation of the proposed gatekeeper architecture MUST explicitly report
the three core metrics defined in the GateMem benchmark: Utility (task success
rate), Access Control (rate of unauthorized data exposure), and Forgetting
(rate of successful data deletion). Claims regarding the resolution of the
trade-off between leakage and utility are only valid if supported by paired
statistical tests (t-tests or Wilcoxon signed-rank) comparing the gatekeeper
method against the specified Retrieval-only and Long-Context baselines using
the same LLM backbone and retrieval index.

*Justification: Derived from the "Expected results" and "Methodology sketch"
sections, which mandate the use of GateMem's specific metrics and statistical
analysis to prove that governance can be decoupled from primary reasoning while
maintaining task utility within a narrow margin.*

### VII. Computational Efficiency and Resource Profiling

Performance claims regarding the "CPU-tractable" nature of the governance layer
MUST be substantiated by direct measurements of wall-clock inference time and
peak CPU/RAM usage. These metrics MUST be recorded for both the proposed
gatekeeper pipeline (utilizing the frozen DistilBERT model and regex logic) and
the baseline agents to quantify the computational overhead reduction.

*Justification: Derived from the "Motivation" section, which highlights the need
for a practical alternative in resource-constrained settings, and the
"Methodology sketch" section, which explicitly lists "Cost Profiling" as a
required experimental step to measure inference time and resource usage.*

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-12.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-830-llmxive-follow-up-extending-gatemem-benc | **Field**: computer science | **Ratified**: 2026-07-12
