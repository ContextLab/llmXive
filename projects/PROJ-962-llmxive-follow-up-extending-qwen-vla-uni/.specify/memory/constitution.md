# llmXive follow-up: extending "Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Envir" — Research Project Constitution

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
project's `state/projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni.yaml` `updated_at` timestamp.

### VI. Simulation-Based Validation (Domain Specific)

Since the project explicitly targets CPU-only execution and avoids the
original DiT backbone for inference, all trajectory evaluations MUST be
conducted within a deterministic physics simulator (e.g., PyBullet) rather
than on physical hardware or via visual inspection. The methodology requires
that task success rates and kinematic feasibility metrics (collision counts)
be measured strictly within this simulated environment to ensure the
"CPU-only" constraint is met and to allow for rapid, repeatable statistical
comparison against baselines. This principle is grounded in the "Simulation
& Evaluation" and "Methodology sketch" sections which mandate the use of a
CPU-only physics simulator for all 100 test prompts per task type.

### VII. Distillation Fidelity Thresholds (Domain Specific)

The project's primary research question hinges on identifying a complexity
threshold where non-neural approximations (Decision Trees, Gaussian Mixtures)
capture a specific fidelity percentage (>60%) of the original VLA's
trajectory generation. Consequently, the evaluation protocol MUST explicitly
report the fidelity gap between the distilled non-neural models and the
original VLA (or its proxy) for both simple manipulation tasks and
high-horizon/fine-grained tasks. Claims regarding the "fundamental trade-off"
between representation complexity and fidelity are invalid unless supported by
quantitative data showing where the non-neural models fail significantly. This
principle is grounded in the "Expected results" section which defines the
success criteria as identifying a specific complexity threshold where
non-neural approximations capture >60% of trajectory fidelity.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-02.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-962-llmxive-follow-up-extending-qwen-vla-uni | **Field**: computer science | **Ratified**: 2026-08-02
