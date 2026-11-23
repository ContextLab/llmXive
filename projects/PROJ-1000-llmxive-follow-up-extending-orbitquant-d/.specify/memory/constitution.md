# llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T" — Research Project Constitution

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
project's `state/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d.yaml` `updated_at` timestamp.

### VI. Dynamic Rotation Basis Validation

The dynamic router's selection of pre-optimized rotation matrices MUST be
empirically validated against the specific variance regimes of the
intermediate activation distributions observed in the FLUX.1-dev and Wan 2.1
models. As the methodology relies on a one-time offline clustering of
activation histograms to generate the $K=16$ matrices, the project MUST
document the specific activation layers and dataset subsets used for this
clustering in `data/`. The correlation between prompt semantic entropy and
activation variance, which drives the router's decision logic, MUST be
statistically verified (paired t-test, p < 0.05) on the 200 curated prompts
before any performance claims regarding the dynamic selection mechanism are
accepted.

### VII. W2A4 Regime Overhead Accounting

Any claim of "negligible runtime overhead" for the dynamic selection
mechanism MUST be measured strictly against the static OrbitQuant baseline
under identical W2A4 quantization constraints. The project MUST report the
wall-clock inference time difference for the dynamic forward pass (including
router execution) separately from the quantization/dequantization overhead.
If the overhead exceeds the 2% threshold defined in the expected results,
the project MUST either re-evaluate the router's complexity or explicitly
document the trade-off between quantization error reduction (targeting
15–20% improvement for high-entropy prompts) and inference latency in the
final analysis.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-09-19.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-1000-llmxive-follow-up-extending-orbitquant-d | **Field**: computer science | **Ratified**: 2026-09-19
