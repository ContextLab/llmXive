# llmXive follow-up: extending "MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level " — Research Project Constitution

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
project's `state/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag.yaml` `updated_at` timestamp.

### VI. Deterministic Topology vs. Neural Baseline Parity

Every comparison between the "GraphCompass" pipeline (graph-based) and the BERTopic baseline (neural) MUST be conducted under strictly controlled computational constraints to isolate the trade-off between computational efficiency and retrieval precision. Specifically, the BERTopic baseline MUST be executed in CPU-only mode to ensure the latency and precision metrics are directly comparable to the graph-based approach, as the core hypothesis relies on validating lightweight, deterministic methods against heavy neural models in resource-constrained environments. All correlation analyses (e.g., Spearman rank correlation between topological features and retrieval precision) MUST be computed on the exact same held-out test set used for the retrieval simulation to prevent data leakage between the model construction and evaluation phases.

### VII. Explicit Graph Metric to Retrieval Precision Correlation

The project MUST explicitly quantify and report the statistical relationship between specific topological features (cluster modularity, node centrality distributions, average path length) and downstream retrieval performance (Recall@5, Recall@10). Claims regarding the predictive power of graph structure MUST be supported by a statistically significant correlation coefficient (targeting r > 0.6) or a paired t-test result that validates the hypothesis that graph topology serves as a reliable proxy for semantic coherence. Vague assertions that graph methods are "effective" are insufficient; the constitution requires the specific numerical correlation between the extracted features (e.g., modularity scores) and the ground-truth retrieval precision to be the primary metric of success.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-911-llmxive-follow-up-extending-mcompassrag/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-14.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-911-llmxive-follow-up-extending-mcompassrag | **Field**: linguistics | **Ratified**: 2026-07-14
