# Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets — Research Project Constitution

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
project's `state/projects/PROJ-422-predicting-molecular-permeability-coeffi.yaml` `updated_at` timestamp.

### VI. Graph-Representation Fidelity

Every molecular graph constructed in `code/` MUST be derived strictly from
SMILES strings using the RDKit library as specified in the methodology,
ensuring that atom connectivity and bond orders match the input data exactly.
Any deviation from the standard SMILES-to-graph parsing logic (e.g., manual
edge addition or heuristic simplification not documented in `code/`) is
prohibited, as the project's core hypothesis relies on comparing the
predictive power of the Message Passing Neural Network (MPNN) against standard
descriptors based on the integrity of the topological input.

### VII. Validation Independence and Statistical Rigor

The evaluation of model performance MUST rely exclusively on the
permeability coefficient values provided in the public datasets (NIST or
Zenodo), which serve as independent experimental measurements distinct from
the molecular structure inputs. No circular validation is permitted where
the target variable is inferred from the input descriptors. Furthermore,
comparisons between the Graph Neural Network (GNN) and the Random Forest
baseline MUST include a paired t-test on prediction errors to establish
statistical significance, ensuring that any claimed advantage of the
graph-based representation is not due to random variance.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-422-predicting-molecular-permeability-coeffi.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-26.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-422-predicting-molecular-permeability-coeffi | **Field**: chemistry | **Ratified**: 2026-08-26
