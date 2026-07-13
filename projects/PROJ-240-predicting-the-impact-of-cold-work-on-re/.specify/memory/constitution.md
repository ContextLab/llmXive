# Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys — Research Project Constitution

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
project's `state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml` `updated_at` timestamp.

### VI. Computational Kinetic Stability

Given the project's reliance on a Random Forest Regressor to predict time-to-peak softening from limited experimental data (<5,000 rows), all model training pipelines MUST enforce CPU-only execution and strict memory bounds to ensure the 6-hour runtime constraint is met. Feature engineering steps involving interaction terms between cold work percentage and solute elements (Mg, Si, Cu, Mn) MUST be deterministic and documented in `code/` to prevent variance in the derived non-linear relationship from differing across execution environments.

### VII. Experimental Data Fidelity

As the project addresses a gap where no unified dataset exists for aluminum alloys under varying cold work, the `data/` directory MUST strictly segregate raw experimental measurements of time-to-peak softening from derived features. The validation protocol MUST utilize a held-out test set of experimental data points that were explicitly excluded from training and feature selection to ensure the reported R² > 0.6 and MAE metrics reflect genuine predictive capability on unseen material compositions rather than overfitting to the specific alloy series (e.g., 5xxx vs. 6xxx) present in the training fold.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-13.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-240-predicting-the-impact-of-cold-work-on-re | **Field**: materials science | **Ratified**: 2026-07-13
