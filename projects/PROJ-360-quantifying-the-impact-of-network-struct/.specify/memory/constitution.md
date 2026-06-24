# Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids — Research Project Constitution

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
project's `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` `updated_at` timestamp.

### VI. Numerical Stability and Determinism

All computational analyses (network‑metric calculation, correlation
coefficients, linear‑regression training, and cross‑validation) MUST be
performed with deterministic algorithms and explicit numerical tolerances.
Random seeds for any stochastic component (e.g., train‑test splits in the
5‑fold cross‑validation described in the *Methodology sketch*) MUST be fixed
and recorded in the executing script. Library versions that affect
floating‑point behavior (e.g., NumPy, SciPy, scikit‑learn) MUST be pinned in
`requirements.txt`. If a numerical‑library version changes, the full
analysis pipeline must be re‑run and the resulting correlation coefficients
and model‑performance metrics must remain within 1 % of the previously
recorded values.

### VII. Materials Project Data Provenance

The primary dataset – CIF files and associated thermal‑conductivity values
sourced from Materials Project – MUST be captured as an immutable snapshot at
the start of the project. The snapshot identifier (e.g., release tag or
download timestamp) MUST be recorded in a `data/metadata.yaml` file. All
downstream scripts MUST retrieve the data exclusively from this snapshot
directory; any update to the upstream Materials Project dataset requires a
new snapshot and a full recomputation of all network metrics and model
evaluations. This guarantees that every reported result can be traced back to
the exact version of the Materials Project data used in the *Methodology
sketch*.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-360-quantifying-the-impact-of-network-struct/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-360-quantifying-the-impact-of-network-struct | **Field**: physics | **Ratified**: 2026-06-24
