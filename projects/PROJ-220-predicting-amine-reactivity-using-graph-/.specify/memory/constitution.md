# Predicting Amine Reactivity Using Graph Neural Networks and Public Databases — Research Project Constitution

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
project's `state/projects/PROJ-220-predicting-amine-reactivity-using-graph-.yaml` `updated_at` timestamp.

### VI. Heterophily-Aware Graph Construction

Graph representations MUST explicitly model the distinct electronic environments of reactants and transition states to address the heterophily inherent in SN2 reaction graphs. Node features MUST include atom type, hybridization, and partial charges (calculated via Gasteiger methods), and edge features MUST encode bond order. If standard aggregation mechanisms fail to converge on diverse amine scaffolds, the architecture MUST switch to a heterophily-aware variant (e.g., specific GraphSAGE or GAT modifications) as defined in the methodology sketch. This principle is grounded in the "Methodology sketch" requirement to construct heterogeneous graphs and the "Literature gap analysis" identifying the struggle of standard GNNs with heterophilous graphs in reaction contexts.

### VII. Mechanistic Interpretability and Validation

Model performance MUST be evaluated not only by predictive metrics (MAE, R²) but also by the alignment of learned feature importance with established chemical intuition. The project MUST employ SHAP (SHapley Additive exPlanations) or attention-weight analysis to rank atomic features and subgraphs by their contribution to predicted rates. Success is defined by the identification of specific subgraph motifs (e.g., steric bulk at the alpha-carbon) that correlate with experimental rates (|r| > 0.6) and align with known determinants like pKa. This principle is grounded in the "Expected results" section requiring correlation with known chemical intuition and the "Methodology sketch" detailing the interpretability analysis and statistical testing against baselines.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-220-predicting-amine-reactivity-using-graph-/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-220-predicting-amine-reactivity-using-graph-.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-08-16.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-220-predicting-amine-reactivity-using-graph- | **Field**: chemistry | **Ratified**: 2026-08-16
