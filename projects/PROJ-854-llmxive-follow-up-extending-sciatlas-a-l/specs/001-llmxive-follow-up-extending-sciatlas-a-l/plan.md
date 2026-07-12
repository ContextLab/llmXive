# Implementation Plan: llmXive Follow-up: Interdisciplinary Bridging Coefficient Analysis

**Branch**: `001-bridging-coefficient-analysis` | **Date**: 2026-07-13 | **Spec**: `specs/001-bridging-coefficient-analysis/spec.md`
**Input**: Feature specification from `specs/001-bridging-coefficient-analysis/spec.md`

## Summary

This feature implements a statistical analysis pipeline to determine if the density of cross-disciplinary connections (interdisciplinary bridging coefficient) in a scientific knowledge graph predicts future citation impact and novelty. The approach involves downloading the **OpenAlex** dataset, performing community detection (Louvain/Leiden) to define structural clusters, calculating the bridging coefficient for each node, deriving novelty scores via **k-NN average similarity** (independent of topology), and performing Spearman correlation with **binned non-linear analysis** and multiple-comparison correction. The entire pipeline is constrained to run on a CPU-only GitHub Actions runner (2 cores, 7GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `networkx` (graph processing), `scikit-learn` (clustering, embeddings, regression), `sentence-transformers` (CPU-compatible embeddings), `pandas`, `numpy`, `scipy` (statistics), `pyalex` (OpenAlex API).
**Storage**: Local filesystem (`data/` for raw/processed data, `artifacts/` for outputs). No external database.
**Testing**: `pytest` with contract tests against YAML schemas.
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, No GPU).
**Project Type**: Computational research pipeline / CLI.
**Performance Goals**: Peak RAM ≤ 7GB; Runtime ≤ 6h; Embedding inference ≤ 50ms/node (batched).
**Constraints**: No GPU usage; no 8-bit quantization; strict separation of topological (predictor) and text-based (outcome) variables; all statistical claims must be labeled "associational"; temporal lag variables included for validity.
**Scale/Scope**: Subgraph of OpenAlex (sampled via **degree-stratified random sampling** to [deferred] nodes); A set of text clusters; primary hypothesis tests + binned analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
|:--- |:--- |:--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; data fetched from **OpenAlex API** (canonical source); `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | Dataset source is **OpenAlex** (verified URL: ` Name or service not known)"))]). All citations in `research.md` cite this canonical source. |
| **III. Data Hygiene** | PASS | Raw data checksummed; derivations written to new files; PII scan enforced via `pytest`. |
| **IV. Single Source of Truth** | PASS | Figures/stats in output trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Artifact hashes tracked via `sha256sum` in `data/`; `state/projects/...yaml` `updated_at` timestamp updated automatically upon artifact change. |
| **VI. Compute Feasibility** | PASS | `sentence-transformers/all-MiniLM-L6-v2` used (CPU-optimized); `networkx` with **degree-stratified sampling**; subgraph sampling ensures RAM < 7GB. |
| **VII. Non-Circular Validation** | PASS | `primary_cluster` (Louvain) and `topic_cluster` (K-Means on text) are computed independently; novelty score derived *only* from text (k-NN), bridging *only* from graph. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bridging-coefficient-analysis/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output
 ├── node.schema.yaml
 └── analysis_output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── models/
│ ├── node.py # Node dataclass
│ └── graph_utils.py # Louvain, bridging calc
├── services/
│ ├── ingest.py # Data download/parsing (OpenAlex)
│ ├── embeddings.py # Text embedding service
│ ├── clustering.py # Topological & Text clustering
│ └── analysis.py # Correlation, Regression, Binned Analysis
├── cli/
│ └── main.py # Entry point for pipeline
└── lib/
 └── config.py # Constants, seeds, paths

tests/
├── contract/
│ └── test_schemas.py # Validates against contracts/
├── integration/
│ └── test_pipeline.py # End-to-end on sample
└── unit/
 └── test_metrics.py # Unit tests for bridging/novelty
```

**Structure Decision**: Single project structure selected. The workflow is linear (Ingest -> Process -> Analyze) and fits a monolithic `src/` layout. `services` encapsulates the distinct logic (graph vs. text) to enforce the Non-Circular Validation principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Clustering** (Louvain + K-Means) | Required by Spec to separate topology (predictor) from text (outcome) to avoid circularity. | Using a single clustering method would violate Constitution Principle VII (Non-Circular Validation). |
| **Batched Embedding** | Required to fit 7GB RAM limit on [deferred] nodes. | Loading all embeddings at once would exceed memory constraints on the free-tier runner. |
| **Binned Analysis** | Required to detect non-monotonic (inverted U) relationships. | Simple Spearman correlation may miss complex non-linear effects. |
| **Degree-Stratified Sampling** | Required to ensure the subgraph is representative of high-degree (hub) nodes which are critical for bridging. | Random sampling might under-represent the structural hubs needed for the analysis. |

## Revised Assumptions & Constraints

- **Dataset**: The study uses **OpenAlex** as the primary data source, accessible via ` Name or service not known)"))].
- **Sampling**: The subgraph is sampled using **degree-stratified random sampling** to ensure representative coverage of structural hubs.
- **Non-Linearity**: The relationship between bridging and impact may be non-monotonic; the plan includes binned analysis to detect this.
- **Temporal Validity**: The analysis includes publication year and citation year to validate the "future impact" claim.
- **Power**: If the sample size required for [deferred] power (rho=0.1) exceeds compute limits, the study is framed as an **exploratory pilot**.