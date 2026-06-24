# Memory Palace Pedagogy: VR-Enhanced Spatial Learning for Abstract Concepts — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re‑running the
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
`code/`. Derived numbers MUST NOT be hand‑typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The
Advancement-Evaluator Agent invalidates stale review records when the
hashed artifact changes. Every research‑stage artifact change updates this
project's `state/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati.yaml` `updated_at` timestamp.

### VI. Statistical Rigor

All statistical analyses described in the methodology sketch—specifically
the linear mixed‑effects model, confidence‑interval reporting, and the
10 000‑shuffle permutation test—MUST be implemented exactly as specified,
with the same model formula, random‑effects structure, and significance
threshold (p < 0.05). Effect sizes, 95 % confidence intervals, and likelihood‑ratio
test statistics for the interaction term must be exported to a machine‑readable
CSV in `results/` and referenced by any figure or table that presents the
findings. Any deviation from this analysis plan requires explicit justification
in a commit message and must be approved by the Advancement‑Evaluator Agent.

### VII. Human Data Privacy

The project uses the *Pupil Labs Reading* dataset from OpenNeuro, which contains
physiological recordings of human participants. All raw data files must remain
unchanged and must not contain any personally identifying information. Any
derived data (e.g., the computed Cognitive‑Load Index) must be stored under
`data/derived/` with a clear provenance record and must be screened by the
Repository‑Hygiene Agent for potential re‑identification risk before any
commit is accepted. No new participant‑level identifiers may be added at any
stage of the pipeline.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/code/`
  pins every Python dependency.
- The Code‑Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end‑to‑end without
  manual intervention.
- The *Pupil Labs Reading* dataset must be downloaded programmatically from the
  OpenNeuro repository using the same dataset identifier each time, and the
  download script must record the dataset version hash in `data/metadata.yaml`.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository‑Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement‑Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-06-24.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement‑Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review‑point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-557-memory-palace-pedagogy-vr-enhanced-spati | **Field**: psychology | **Ratified**: 2026-06-24
