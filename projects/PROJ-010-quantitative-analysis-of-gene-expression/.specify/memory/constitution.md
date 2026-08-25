# Quantitative Analysis of Gene Expression Dynamics during Human Brain Development — Research Project Constitution

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
project's `state/projects/PROJ-010-quantitative-analysis-of-gene-expression.yaml` `updated_at` timestamp.

### VI. Dynamic Network Topology Validation

Every inference of a transcription factor regulatory network MUST be derived
from time-resolved single-cell RNA-seq data using the specified sliding-window
pseudotime approach (Monocle3 or Slingshot for trajectory ordering, SCENIC or
GRNBoost2 for network reconstruction). Claims of "rewiring events" MUST be
supported by quantified edge weight differences and hub stability metrics
between adjacent developmental windows, verified against permutation tests
to ensure significance compared to randomized network structures. This
principle ensures that observed topological changes reflect genuine biological
dynamics rather than batch effects or noise, directly addressing the project's
core goal of mapping stage-specific network rewiring during critical
neurodevelopmental windows.

### VII. Disorder Vulnerability Correlation Rigor

Any correlation between identified network rewiring events and neurological
disorder vulnerability windows MUST be established by mapping known disorder
risk genes (from GWAS catalogs) onto the dynamic networks and testing for
enrichment in rewired hubs using hypergeometric tests. Claims of correlation
MUST be validated against an independent dataset (e.g., bulk RNA-seq time
courses from different cohorts) to ensure results are not artifacts of a
single dataset's noise profile. This principle enforces the project's
specific methodology for linking dynamic network topology changes to disorder
susceptibility, ensuring that identified vulnerability windows are robust and
not dataset-specific artifacts.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-010-quantitative-analysis-of-gene-expression/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-010-quantitative-analysis-of-gene-expression.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-25.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-010-quantitative-analysis-of-gene-expression | **Field**: biology | **Ratified**: 2026-08-25
