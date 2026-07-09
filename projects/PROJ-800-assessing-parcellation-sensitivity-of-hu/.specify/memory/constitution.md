# Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes — Research Project Constitution

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
project's `state/projects/PROJ-800-assessing-parcellation-sensitivity-of-hu.yaml` `updated_at` timestamp.

### VI. Parcellation Resolution Invariance

This project explicitly governs the sensitivity of graph-theoretical metrics to node definition.
Any reported centrality rankings (degree, betweenness) or global topological properties MUST
be accompanied by the specific atlas resolution (e.g., AAL-90, Schaefer-200, Schaefer-400)
used to generate them. Comparisons of hub status across studies or cohorts MUST only be
considered valid if the parcellation schemes are identical or if the project's specific
overlap statistics (Jaccard, Dice) and rank correlation analyses have been computed to
quantify the variance introduced by the resolution shift. This principle is grounded in the
project's core research question regarding the invariance of metrics across resolutions and
the methodology sketch's requirement to map continuous data to three distinct standard atlases
to generate separate adjacency matrices for direct comparison.

### VII. Set-Theoretic Hub Validation

Hub identification in this project MUST be validated through set-theoretic intersection rather
than mathematical derivation from the centrality values themselves. A region's status as a "hub"
is defined strictly as membership in the top 10% of nodes by a specific metric within a specific
scheme. Validation of hub resilience MUST rely on overlap coefficients (Jaccard/Dice) and rank
correlations between these independently thresholded sets. This principle is explicitly grounded
in the "Independence Check" step of the methodology sketch, which mandates that the stability
metric must not be derived from the centrality values but from the set-theoretic intersection
of independent thresholding events.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-800-assessing-parcellation-sensitivity-of-hu.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-09.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-800-assessing-parcellation-sensitivity-of-hu | **Field**: neuroscience | **Ratified**: 2026-07-09
