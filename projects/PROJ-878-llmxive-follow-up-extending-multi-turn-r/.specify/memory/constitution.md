# llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode" — Research Project Constitution

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
project's `state/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r.yaml` `updated_at` timestamp.

### VI. Topological Metric Traceability

Every convergence failure rate and turn-count statistic reported MUST be
explicitly derived from a calculated *maximum nesting depth* or *branching
factor* metric extracted from the specific problem instance's directed
dependency graph. As defined in the methodology sketch, the parser converting
problem instances into dependency graphs must be versioned, and the specific
metric values for each dataset entry MUST be stored in `data/` to allow
independent verification of the correlation between structural complexity
and the observed non-linear degradation in convergence speed.

### VII. Synthetic Graph Construction Integrity

The synthetic logical deduction dataset generated from the GSM8K baseline
MUST strictly adhere to the controlled topological parameters (nesting depth
1–10, branching factor 1–5) specified in the data acquisition plan. The
generation script MUST log the exact random seed and algorithmic parameters
used to construct each dependency graph, ensuring that the "tipping point"
where iterative refinement fails to converge is a result of the defined
structural constraints rather than stochastic variation in the graph
construction process.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-18.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-878-llmxive-follow-up-extending-multi-turn-r | **Field**: linguistics | **Ratified**: 2026-08-18
