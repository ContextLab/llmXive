# Predicting Molecular Interactions in Polymer Blends Using Machine Learning — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re‑running the
project's `code/` against the project's `data/` on a fresh GitHub Actions
runner. Random seeds MUST be pinned in `code/`. External datasets MUST be
fetched from the same canonical source on every run.

### II. Verified Accuracy (inherits parent Principle II)

Every external citation in `idea/`, `technical-design/`,
`implementation‑plan/`, or `paper/` MUST be verified by the
Reference‑Validator Agent against the primary source before contributing
review points. Title‑token‑overlap with the cited source MUST be ≥
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

Review records are bound to the content of the artifact they reviewed; a
record goes stale when that artifact changes. The platform does this
bookkeeping. `state/projects/PROJ-237-predicting-molecular-interactions-in-pol.yaml` belongs to the platform:
project code, tests and tasks MUST NOT read it, write it, or create a
`state/` directory inside the project.

### VI. Model Interpretability (domain‑specific)

All predictive models **must** include a post‑hoc interpretability analysis
using SHAP values, as stipulated in the *Methodology sketch* (“Use SHAP
values … to rank which molecular structural features contribute most to the
predicted deviation”). The resulting feature‑importance reports MUST be
saved under `results/interpretability/` and cited in the manuscript to
justify any scientific claims about structural drivers of non‑linear HSP
deviations.

### VII. Computational Resource Constraints (domain‑specific)

All data processing, model training, and evaluation pipelines **must** complete
within the 6‑hour GitHub Actions job limit on a 2‑core/7 GB RAM runner,
as required in the *Methodology sketch* (“All data processing and model
training must run within a 6‑hour GitHub Actions job …”). Scripts MUST
enforce batch size ≤ 16, limit graph depth, and abort with a clear error if
resource usage exceeds the allotted limits.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-237-predicting-molecular-interactions-in-pol/code/`
  pins every Python dependency.
- The Code‑Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end‑to‑end without
  manual intervention.

## Data Hygiene

- When the analysis needs checksums of its own data (to verify a download
  or detect a changed input), it writes them to a manifest under `data/`
  (for example `data/checksums.sha256`). It never records hashes under
  `state/`, which is the platform's.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository‑Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference‑Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement‑Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-10-23.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement‑Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review‑point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-237-predicting-molecular-interactions-in-pol
