# llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil" — Research Project Constitution

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
project's `state/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any.yaml` `updated_at` timestamp.

### VI. Temporal Discontinuity Quantification

The project's primary metric, "flow-map divergence," MUST be calculated as the
L2 distance between the predicted intermediate latent state $z_r$ (derived via
flow-map backward simulation) and the high-resolution Euler rollout reference
state. This calculation is strictly required for all 500 curated video clips
to empirically measure instability induced by high-frequency temporal
discontinuities, as the methodology explicitly relies on correlating this
divergence with input statistical properties like optical flow magnitude
variance and inter-frame histogram differences.

### VII. CPU-Tractability and Resource Constraint

All inference and divergence calculation steps MUST execute within the defined
resource limits: the AnyFlow model MUST be loaded in ONNX format for CPU-only
inference with quantization settings ensuring memory usage remains under 7 GB,
and the entire pipeline (inference plus statistical analysis) MUST complete
within the 6-hour GitHub Actions runner limit on 2 cores. This principle is
derived from the methodology's explicit requirement to identify "CPU-tractable
statistical features" and the constraint that the pipeline must run on standard
compute resources without GPU acceleration.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-812-llmxive-follow-up-extending-anyflow-any | **Field**: computer science | **Ratified**: 2026-07-11
