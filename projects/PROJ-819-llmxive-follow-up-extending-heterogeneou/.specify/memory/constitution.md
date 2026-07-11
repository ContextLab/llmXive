# llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration" — Research Project Constitution

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
project's `state/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou.yaml` `updated_at` timestamp.

### VI. Semantic Cache Validity

For any cached inference result retrieved via the Semantic Cache module, the
project MUST explicitly record the cosine similarity score of the retrieved
prompt embedding against the query embedding. A cached result is only
considered valid for the "Accuracy Evaluation" if the recorded similarity
score meets the empirically determined threshold (e.g., >0.95) established
during the "Threshold Tuning" phase. This principle ensures that the
efficiency gains of the cache do not come from unverified or low-similarity
retrievals that could compromise scientific reasoning fidelity, directly
addressing the core research question regarding the trade-off between hit-rate
and accuracy.

### VII. Resource-Constrained Execution Fidelity

All performance metrics (wall-clock time, model invocations, token usage)
MUST be measured exclusively within an execution environment simulating
resource-constrained conditions (specifically, a standard multi-core CPU
environment with memory limits approximating 7GB RAM, as defined in the
Methodology sketch). This ensures that the reported efficiency gains are
valid for the intended deployment targets (edge devices, CPU-only clusters)
and not artifacts of unconstrained hardware resources.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/`
  pins every Python dependency, including the specific embedding model
  (`all-MiniLM-L6-v2`) and the EywaOrchestra framework dependencies.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention, specifically including the cache implementation and
  the paired t-test statistical analysis scripts.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou.yaml` `artifact_hashes` map.
- Raw data (the Eywa benchmark subset) is preserved unchanged; derivations
  (the 500 distinct but overlapping sub-task queries) are written to new
  filenames with documented generation logic.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status. Additionally, the accuracy
evaluation results MUST be verified against the ground-truth scientific
outcomes provided in the Eywa benchmark, ensuring independence from the
cache mechanism.

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

**Project ID**: PROJ-819-llmxive-follow-up-extending-heterogeneou | **Field**: other | **Ratified**: 2026-07-11
