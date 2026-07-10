# Statistical Properties of Integer Partitions Into Distinct Prime Summands — Research Project Constitution

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
project's `state/projects/PROJ-799-statistical-properties-of-integer-partit.yaml` `updated_at` timestamp.

### VI. Finite-Regime Error Term Precision

Every computational result comparing $p_{\mathcal{P}}(n)$ to Meinardus' theorem MUST explicitly report the residual error term for the finite $n$ range investigated. The methodology for computing exact partition values MUST be documented to ensure the non-linear combinatorial aggregation of distinct primes is handled without approximation until the final comparison with the asymptotic limit.

*Justification: This principle is grounded in the "Research-question validation" section of the idea body, which defines the core inquiry as investigating the "specific nature of the deviation between a theoretical asymptotic limit (Meinardus' theorem) and the actual behavior... in the finite regime" and the "error term and its relationship to prime density."*

### VII. Density-Dependent Correlation Rigor

When analyzing the relationship between predictor variables (prime density $\pi(n)$, $1/\ln(n)$) and the partition function residuals, the project MUST avoid assuming a linear or direct summary relationship. Statistical analysis MUST account for the complex, non-linear combinatorial nature of the partition function to distinguish between systematic density-dependent corrections and random noise.

*Justification: This principle is grounded in the "Circularity check" and "Triviality check" sections of the idea body, which highlight that the partition function involves a "complex, non-linear combinatorial aggregation" that is not a "simple linear or direct summary of the density function," and that outcomes must distinguish between a "systematic, density-dependent correction term" and "random noise."*

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-799-statistical-properties-of-integer-partit/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-799-statistical-properties-of-integer-partit.yaml` `artifact_hashes` map.
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

**Project ID**: PROJ-799-statistical-properties-of-integer-partit | **Field**: mathematics | **Ratified**: 2026-07-09
