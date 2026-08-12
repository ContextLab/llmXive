# llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report" — Research Project Constitution

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
project's `state/projects/PROJ-891-llmxive-follow-up-extending-kwai-keye-vl.yaml` `updated_at` timestamp.

### VI. Geometric Stress-Testing Integrity

To validate the "native-resolution" claim of the Kwai Keye-VL-2.0 architecture,
every evaluation run MUST include both the original square-cropped control set
and the synthetically generated extreme-aspect-ratio variants (ratios 1:10, 10:1,
1:20, 20:1) derived from the ActivityNet Captions dataset. The methodology
sketch explicitly defines these geometric perturbations as the independent
variable; therefore, any deviation from these specific aspect ratios or the
preservation of original temporal ground-truth annotations during data
construction invalidates the statistical comparison of mean Intersection-over-Union
(mIoU) scores. This principle ensures the experiment directly addresses the
research question regarding spatial token dispersion under extreme geometries.

### VII. Resource-Constrained Inference Fidelity

Given the project's explicit constraint to evaluate the 3B active parameter
quantized (INT4) model on a CPU-only environment with a 7GB RAM limit, all
performance metrics (latency, memory footprint) and accuracy results MUST be
generated using the specified `llama.cpp` or `Optimum-Intel` inference stack
with CPU offloading enabled. The constitution mandates that no GPU-accelerated
inference or alternative memory management strategies be used for the primary
results, as the "silent performance failures" and latency characteristics under
these specific hardware constraints are central to the motivation of assessing
real-world applicability for mobile-shot or surveillance video analysis.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-891-llmxive-follow-up-extending-kwai-keye-vl/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-891-llmxive-follow-up-extending-kwai-keye-vl.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-12.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-891-llmxive-follow-up-extending-kwai-keye-vl | **Field**: computer science | **Ratified**: 2026-08-12
