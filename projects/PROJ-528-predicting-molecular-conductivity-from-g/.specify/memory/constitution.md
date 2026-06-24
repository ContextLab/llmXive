# Predicting Molecular Conductivity from Graph-Based Features — Research Project Constitution

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
project's `state/projects/PROJ-528-predicting-molecular-conductivity-from-g.yaml` `updated_at` timestamp.

### VI. Graph Descriptor Transparency

All graph-based molecular descriptors employed (degree distribution, average path length, ring counts, conjugation length, aromaticity indices) MUST be generated using the RDKit library version recorded in `requirements.txt`. The code that computes each descriptor MUST be committed under `code/` with accompanying unit tests that verify correct values for given SMILES inputs. Any modification to descriptor definitions MUST create a new versioned file and update the corresponding checksum in the project state.

### VII. Dataset Provenance and Integrity

The primary dataset of SMILES strings and experimental conductivity measurements MUST be sourced exclusively from the Materials Project and/or PubChem. Raw download files MUST be stored unchanged in `data/raw/` with checksums recorded. All preprocessing steps (e.g., filtering, log‑transformation) MUST be performed by scripts that output new files under `data/processed/`, preserving the original raw files. Metadata accompanying each dataset file MUST record the source name, access date, and any selection criteria used, ensuring full traceability of the data used for model training and evaluation.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-528-predicting-molecular-conductivity-from-g/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-528-predicting-molecular-conductivity-from-g.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-06-24.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-528-predicting-molecular-conductivity-from-g | **Field**: chemistry | **Ratified**: 2026-06-24
