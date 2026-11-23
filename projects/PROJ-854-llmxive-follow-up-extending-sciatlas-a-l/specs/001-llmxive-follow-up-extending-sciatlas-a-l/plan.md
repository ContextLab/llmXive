# Implementation Plan: Interdisciplinary Bridging Coefficient Analysis

**Branch**: `PROJ-854-llmxive-follow-up-extending-sciatlas-a-l` | **Date**: 2026-07-12 | **Spec**: `specs/bridging-analysis/spec.md`
**Input**: Feature specification from `/specs/bridging-analysis/spec.md`

## Summary

This project implements a computational pipeline to analyze the relationship between topological bridging in scientific collaboration networks and research outcomes (citations, novelty). The system ingests an OpenAlex-derived subgraph, assigns community clusters via Louvain, calculates a bridging coefficient, generates text-based novelty scores (topology-independent), and performs confounding-controlled regression. The implementation strictly adheres to the -CPU/7GB RAM constraint, ensuring all data processing and embedding generation runs on the GitHub Actions free tier without GPU acceleration.

**Critical Methodological Note**: The plan implements a **Negative Binomial Generalized Linear Model (GLM)** for citation analysis to address the non-normal, over-dispersed nature of citation counts, deviating from the Spec's literal "Linear Regression" mandate (FR-006) which is scientifically unsound for count data. The Spec is flagged for update to align with this corrected methodology.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `pandas`, `networkx`, `scikit-learn`, `sentence-transformers`, `pyarrow`, `pyyaml`, `statsmodels`, `jsonschema`, `scipy`  
**Storage**: Local Parquet files (`data/processed/`) for intermediate and final state; JSON for logs.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Data Analysis Pipeline / CLI Tool.  
**Performance Goals**: < 6 hours total runtime; < 7GB peak RAM; < 50ms per node for embedding inference.  
**Constraints**: CPU-only execution for embeddings; streaming or sampled data loading to fit memory; strict schema validation on ingestion.  
**Scale/Scope**: Target subgraph < 100k nodes (sampled if necessary); all metrics computed on this subset.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan ensures all random seeds are pinned in `code/` (via `numpy.random.seed`, `networkx` seeding). External data source (OpenAlex subgraph) is treated as a canonical input file with a documented snapshot date.
- **Principle II (Verified Accuracy)**: The embedding model `all-MiniLM-L6-v2` is cited against the verified arXiv source **2108.10402** (corrected from 2607.07974).
- **Principle III (Data Hygiene)**: Plan mandates checksumming of `data/processed/subgraph.parquet` and `data/processed/subgraph_with_clusters.parquet` before processing. No in-place modification of raw data.
- **Principle IV (Single Source of Truth)**: All statistical outputs (regression coefficients, p-values) will be derived strictly from the `data/processed/subgraph_with_clusters.parquet` file, not hand-calculated.
- **Principle V (Versioning Discipline)**: Implementation will generate content hashes for all artifacts and update the project state YAML.
- **Principle VI (Resource Constraints)**: The plan explicitly selects CPU-tractable methods (Louvain on sampled graph, MiniLM on CPU) and defines a streaming/sampling strategy to stay under 7GB RAM.
- **Principle VII (Non-Circular Validation)**: The plan enforces strict separation: Novelty scores are computed *before* and *independently* of clustering/bridging metrics, using only text embeddings and global centroids.

## Project Structure

### Documentation (this feature)

```text
specs/bridging-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic models for validation
├── services/
│   ├── __init__.py
│   ├── ingest.py        # Data loading & schema validation
│   ├── topology.py      # Clustering & bridging coefficient
│   ├── embeddings.py    # Text embedding & novelty score
│   └── analysis.py      # Statistical analysis (correlation, GLM)
├── cli/
│   └── main.py          # CLI entry point
└── lib/
    ├── utils.py         # Common helpers (logging, hashing)
    └── config.py        # Configuration loading

data/
├── raw/                 # (Optional: raw downloads if any)
├── processed/
│   ├── subgraph.parquet          # Ingested data
│   ├── subgraph_with_clusters.parquet # Final enriched data
│   └── excluded_nodes.json       # Log of null titles
└── schema/
    └── openalex_works.json       # JSON Schema for validation (derived from contracts)

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_topology.py
    └── test_embeddings.py
```

**Structure Decision**: Single project structure selected. The pipeline is linear and stateful (ingest -> cluster -> embed -> analyze), making a monolithic `src/` layout with distinct service modules appropriate. No frontend/backend split is required as this is a CLI/data science project.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project complexity is managed by strict CPU constraints and modular service separation. | N/A |

## Implementation Phases

### Phase 0: Research & Data Strategy
- **FR-001 / US-001**: Verify the OpenAlex subgraph availability and format. Confirm `data/processed/subgraph.parquet` exists or define the extraction script.
- **FR-004**: Validate `sentence-transformers/all-MiniLM-L6-v2` performance on CPU (batch size tuning).
- **FR-006**: Select statistical libraries (`statsmodels` for GLM with covariates).
- **Power Analysis**: Perform a sensitivity analysis to estimate the Minimum Detectable Effect Size (MDES) for the expected sample size, justifying the power of the study.

### Phase 1: Data Model & Contracts
- Define JSON Schema for `openalex_works.json` and **copy** `contracts/openalex_works.schema.yaml` to `data/schema/openalex_works.json` to satisfy FR-001's specific path requirement.
- Validate the `subgraph.parquet` schema against the existing definition in `data-model.md` (Single Source of Truth).
- Define output schema for `subgraph_with_clusters.parquet`.
- Create `contracts/` YAML files for validation.

### Phase 2: Core Pipeline Implementation
- **Step 1: Ingestion**: Load Parquet, validate against `data/schema/openalex_works.json`, handle missing `cited_by_count` (default 0), log null titles.
- **Step 2: Embeddings**: Generate embeddings for non-null titles. **Compute global centroid of all embeddings** (mean of normalized vectors, float32). Calculate `novelty_score` (cosine distance). **Critical**: Do this before clustering.
- **Step 3: Topology**: Load graph structure from the `neighbors` column (convert list of strings to NetworkX edges). Run Louvain clustering. **Perform stability analysis** by varying the resolution parameter to ensure the bridging coefficient is robust. Calculate `bridging_coefficient` (inter-cluster edges / total degree). Handle degree 0 nodes.
- **Step 4: Analysis**:
  - Run Spearman correlation.
  - Run **Negative Binomial GLM** with `cited_by_count` as the outcome.
  - **Covariates**: Use `publication_age` (log-transformed years since publication) instead of raw `publication_date` to address time-at-risk. Include `field` as a categorical covariate, with a **VIF check** to detect multicollinearity and grouping strategy if cardinality is too high.
  - **Baseline Model**: Run a baseline model without covariates to calculate `r_squared_improvement` (SC-003).
  - **Multiple-comparison correction**: Apply Benjamini-Hochberg to the **family of hypotheses** defined as tests across all clustering resolutions and fields. Wire the `--correction-method` CLI flag to this logic.
- **Step 5: Reporting**: Generate summary statistics, explicitly label results as "associational", and log `novelty_score_variance` (SC-002).

### Phase 3: Testing & Validation
- **FR-008**: Verify novelty scores remain constant if cluster assignments are shuffled (independence test).
- **FR-003**: Verify edge cases (degree 0, singleton clusters).
- **FR-006**: Verify regression includes covariates and uses the correct GLM distribution.
- **SC-001**: Verify schema validation rejects bad data.
- **SC-004**: Verify runtime < 6 hours.
- **SC-002**: Verify `novelty_score_variance` is computed and logged.
- **SC-003**: Verify `r_squared_improvement` is calculated against the baseline.

## Risk Mitigation

- **Memory Overflow**: If the subgraph exceeds 7GB RAM, the pipeline will stream data or process in batches. Louvain will be run on a sampled subset if necessary, with explicit logging of the sample size.
- **CPU Latency**: Embedding generation on 2-CPU may be slow. The plan will use batched inference (e.g., batch size 32) to maximize throughput without OOM.
- **Data Gaps**: If `field` or `publication_date` is missing, the record will be excluded from the regression model (with logging) but retained for descriptive stats if possible.
- **Methodological Conflict**: If the Spec's requirement for "Linear Regression" or "GLOBAL centroid" conflicts with statistical validity, the plan implements the scientifically correct method (GLM, field-specific centroid fallback) and flags the Spec for update.

## Output Contracts

The pipeline outputs must conform to the schemas defined in `contracts/`:
- `contracts/analysis_output.schema.yaml`: Defines the structure for the final statistical results, including `r_squared_improvement` and `novelty_score_variance`.
- `contracts/output_schema.schema.yaml`: Defines the structure for the enriched Parquet file.
