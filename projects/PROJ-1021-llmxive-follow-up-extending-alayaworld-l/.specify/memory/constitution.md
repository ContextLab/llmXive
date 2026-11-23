# llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation" — Research Project Constitution

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
project's `state/projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l.yaml` `updated_at` timestamp.

### VI. Deterministic Symbolic Grounding

The project's core innovation relies on a lightweight, rule-based symbolic engine (implemented in pure Python/C) to track object states (e.g., HP, inventory) deterministically based on user action inputs. To ensure the validity of the "Semantic Drift Score," the symbolic engine's state trajectory MUST be generated without stochastic elements and must serve as the immutable ground truth against which visual detections are compared. Any deviation in the symbolic logic execution path invalidates the drift measurement.

### VII. Edge-Device Inference Constraints

As the methodology explicitly targets deployment on resource-constrained edge devices (2-core CPU, 7GB RAM) to avoid massive GPU fine-tuning, all generated code and benchmarks MUST strictly adhere to these hardware limits. Inference speeds, memory usage, and wall-clock times MUST be measured and reported specifically against this 2-core/7GB constraint; results derived from GPU-accelerated environments or systems exceeding these resources are non-compliant with the project's primary motivation.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-20.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-1021-llmxive-follow-up-extending-alayaworld-l | **Field**: computer science | **Ratified**: 2026-08-20
