# llmXive follow-up: extending "Mega-ASR: Towards In-the-wild^2 Speech Recognition via Scaling up Real" — Research Project Constitution

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
project's `state/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow.yaml` `updated_at` timestamp.

### VI. Non-Linear Interaction Characterization

The project MUST explicitly model and report the interaction effects between
compound acoustic distortions (e.g., reverberation combined with low SNR) as
defined in the Methodology sketch. The "semantic collapse threshold" cannot
be derived from additive assumptions; every reported failure point MUST be
validated against the specific 54 compound distortion scenarios and their
atomic components to confirm the existence of a non-linear "critical
interaction vector." This principle ensures the project addresses the
identified literature gap regarding synergistic failure modes rather than
reverting to standard additive noise testing.

### VII. CPU-Tractability and Diagnostic Efficiency

All diagnostic models (including the regression or decision tree predictors
for collapse points) and ground truth generation (using lightweight sentence
embeddings like `all-MiniLM-L6-v2`) MUST be executable on CPU with <7GB RAM
as specified in the Model Selection and Methodology sketch. The project
MUST demonstrate that the proposed "Acoustic Stress Index" provides a
resource-efficient alternative to GPU-intensive full-benchmark testing,
validating the claim that robustness limits can be estimated in minutes
rather than days.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-844-llmxive-follow-up-extending-mega-asr-tow | **Field**: computer science | **Ratified**: 2026-07-12
