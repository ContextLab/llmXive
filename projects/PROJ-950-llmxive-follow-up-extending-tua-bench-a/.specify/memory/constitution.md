# llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents" — Research Project Constitution

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
project's `state/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a.yaml` `updated_at` timestamp.

### VI. Deterministic Execution-Only Evaluation

Evaluation of agent performance MUST rely exclusively on the deterministic
execution success of terminal commands as defined by the TUA-Bench protocol.
Success metrics MUST NOT incorporate subjective interpretation of agent
reasoning, intermediate log outputs, or semantic similarity of generated
command chains. This principle is grounded in the Methodology sketch's
requirement to "Use TUA-Bench's deterministic execution-based scoring" and
the Expected results section's focus on "execution success" as the primary
metric independent of the retrieval mechanism's internal logic.

### VII. Procedural Memory Bank Integrity

The "Procedural Memory Bank" used for retrieval augmentation MUST consist
solely of verified, human-written command sequences curated for the specific
scientific workflow tasks in scope. The integrity of this memory bank MUST be
preserved; no automated generation or model-fine-tuned sequences are permitted
in the base memory bank to ensure the validity of the "retrieval-augmented"
intervention. This principle is grounded in the Methodology sketch's
instruction to "Compile a 'Procedural Memory Bank' containing 50 verified,
human-written command sequences" and the Motivation's goal to test
"explicit, deterministic scaffolding" rather than model retraining.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-09-30.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-950-llmxive-follow-up-extending-tua-bench-a | **Field**: computer science | **Ratified**: 2026-09-30
