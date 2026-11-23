# Phase Transitions in Amorphous Solids Under Shear Stress — Research Project Constitution

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
project's `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml` `updated_at` timestamp.

### VI. Simulation Trajectory Integrity

All molecular dynamics trajectory data used for analysis MUST be preserved in
its raw, unmodified form under `data/raw/`. Any preprocessing step that
computes derived metrics (such as the non-affine displacement D²_min or local
strain tensors) MUST write to a distinct file under `data/processed/`.
This ensures that the statistical comparison between brittle and ductile
regimes, which relies on the Kolmogorov-Smirnov test of D²_min distributions,
remains auditable against the original particle coordinates from sources like
`amorphous-silicon-shear-trajectories` or metallic glass simulation archives.

### VII. Numerical Determinism in Yielding Prediction

To ensure the phase diagram correlating strain rate, temperature, and D²_min
thresholds is reproducible, all clustering operations (k-means with k=3) and
yielding point identification algorithms MUST use fixed random seeds and
deterministic tie-breaking rules. The identification of stress drop events
and the subsequent calculation of p-values (targeting p < 0.05) MUST yield
identical results when the `code/` is executed on a fresh environment,
preventing stochastic variance from obscuring the precursory structural
signatures of the brittle-to-ductile transition.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-09-03.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-080-phase-transitions-in-amorphous-solids-un | **Field**: materials science | **Ratified**: 2026-09-03
