# llmXive follow-up: extending "EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic E" — Research Project Constitution

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
project's `state/projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra.yaml` `updated_at` timestamp.

### VI. Conflict-Based Retrieval Fidelity

The `EvoMem-Conflict` agent variant MUST retrieve memory patches strictly based on the heuristic-defined "conflict" status (semantic contradiction between prior and new state instructions) as implemented in the CPU-tractable detector. Any deviation from this specific filtering logic, such as retrieving non-conflicting recent patches or using a full-history baseline for the conflict-variant, invalidates the comparison against the `EvoMem-All` baseline. This principle is grounded in the methodology's explicit definition of the research question: comparing the efficacy of isolating "conflict-inducing" patches against retrieving all recent traces.

### VII. Ground-Truth Execution Independence

Evaluation of agent performance MUST rely exclusively on the successful execution of terminal commands (the ground truth) and MUST NOT derive success scores from the content of the retrieved memory traces themselves. This principle is grounded in the methodology's requirement for "Validation Independence," ensuring that the measured reduction in hallucination and improvement in accuracy are objective results of the retrieval strategy, not artifacts of the memory content.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.
- The `Terminal-Bench-Evo` dataset subset MUST be filtered for chains containing 5+ version updates with explicit command/path changes prior to agent execution.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.
- Logs of context window size, inference time, and step-level outcomes for both `EvoMem-All` and `EvoMem-Conflict` variants MUST be preserved as distinct artifacts.

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

**Project ID**: PROJ-850-llmxive-follow-up-extending-evoarena-tra | **Field**: linguistics | **Ratified**: 2026-07-12
