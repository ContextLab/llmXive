# Implementation Plan: Predicting Gene Essentiality from Protein Interaction Network Topology

**Branch**: `001-gene-regulation` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-gene-essentiality-from-protei/spec.md`
**Input**: Feature specification from `/specs/001-predicting-gene-essentiality-from-protei/spec.md`

## Summary

This project implements a computational pipeline to test the hypothesis that network topology (centrality metrics) in Protein-Protein Interaction (PPI) networks predicts gene essentiality across multiple model organisms. The system fetches PPI data from the STRING API and essentiality labels from the DEG database, maps identifiers via Ensembl BioMart, computes centrality metrics (degree, betweenness, eigenvector) using NetworkX, and calculates Spearman correlations. It further performs Phylogenetic Generalized Least Squares (PGLS) with Fisher's z-transformation to compare correlation strengths across species, accounting for phylogenetic non-independence. Sensitivity analysis on network confidence thresholds and null hypothesis testing (via label permutation and graph rewiring) are included. All analyses are constrained to run on CPU-only GitHub Actions runners (2 cores, 7GB RAM) with explicit network sampling for large graphs to ensure runtime compliance.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `networkx` (graph analysis), `pandas` (data manipulation), `scipy` (statistics), `statsmodels` (PGLS), `requests` (data fetching), `pyyaml` (config), `numpy` (numerical ops), `biopython` (phylogeny), `dendropy` (tree handling).
**Storage**: Local file system (`data/` for raw/processed data, `results/` for outputs). No external database.
**Testing**: `pytest` with contract tests against YAML schemas.
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: Computational research pipeline / CLI.
**Performance Goals**: Complete pipeline for 5-8 organisms within 6 hours. Centrality calculation < 30 mins per organism (max 25k nodes) via sampling if necessary.
**Constraints**: CPU-only (no GPU); RAM < 7GB; disk < 14GB; no external API keys required (public datasets).
**Scale/Scope**: A set of model organisms; networks up to a large scale (sampled if larger); ~k essentiality labels.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; all datasets fetched from official API endpoints in `research.md`; `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | PASS | **Gate**: The `Reference-Validator` agent runs on `research.md` citations before pipeline execution. If any citation is unreachable or mismatched, the build fails. Only official API endpoints (STRING, DEG, OpenTree) are cited. |
| **III. Data Hygiene** | PASS | Raw data downloaded to `data/raw/` with checksums; derivations saved to `data/processed/` with new filenames. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All statistics in `results/` derived strictly from `data/` via `code/`. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | **Step**: A `hash_checker.py` script runs after each pipeline stage, computing SHA256 hashes for `data/` and `results/` and updating `state/projects/PROJ-452-...yaml` `artifact_hashes` and `updated_at`. |
| **VI. Cross-Species Comparative Consistency** | PASS | Identical pipeline (preprocessing, centrality, mapping) enforced via a single `code/analysis.py` script looped over organisms. |
| **VII. Threshold Sensitivity Transparency** | PASS | Sensitivity analysis (multiple runs) in a single pass; results recorded per threshold in `results/sensitivity/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-gene-essentiality-from-protei/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py # Load config (thresholds, organism IDs)
├── data_loader.py # Fetch STRING/DEG via API, map IDs via Ensembl
├── network_analysis.py # Centrality computation, sampling, random graph generation
├── statistics.py # Correlation, PGLS (Fisher z), BH correction, label permutation
├── main.py # Orchestration: download -> map -> analyze -> hash -> test -> save
├── hash_checker.py # Computes hashes and updates state YAML
└── utils.py # Logging, checksumming

data/
├── raw/ # Downloaded parquet/csv files (from API)
├── processed/ # Mapped IDs, computed centralities
└── phylogeny/ # Newick tree file (from OpenTree)

results/
├── correlations.json # Per-organism, per-threshold results (includes mapping_coverage_percent)
├── pgls_results.json # Comparative statistics
├── sensitivity_report.md
└── null_distribution/ # Randomized graph results

tests/
├── unit/
│ ├── test_network_analysis.py
│ └── test_statistics.py
├── contract/
│ ├── test_schemas.py # Validates against:
│ │ # - contracts/correlation_result.schema.yaml
│ │ # - contracts/pgls_result.schema.yaml
│ │ # - contracts/sensitivity_report.schema.yaml
│ └── test_mapping.py
└── integration/
 └── test_pipeline.py
```

**Structure Decision**: Single `code/` directory with modular scripts. This minimizes overhead for a research pipeline and ensures a single point of execution (`main.py`) for reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **PGLS Implementation** | Required by FR-006 to account for phylogenetic non-independence. | Simple t-test or ANOVA would violate statistical assumptions for cross-species data (non-independence). |
| **Sensitivity Analysis Loop** | Required by FR-007 and Constitution Principle VII. | Running a single threshold would fail to address network construction robustness. |
| **Label Permutation** | Required by SC-001 to test association validity (shuffling labels). | Graph rewiring alone is tautological for degree centrality and insufficient for testing label association. |
| **Network Sampling** | Required to meet 30-min CPU limit for large networks (>5k nodes). | Full exact centrality on dense graphs >25k nodes exceeds 6-hour CI limit. |

## Computational Feasibility & Methodology Details

### 1. Data Fetching & Mapping (FR-001, FR-002, FR-003)
- **STRING**: Data fetched via `requests` to ` (or similar public endpoint).
- **DEG**: Data fetched via `requests` to ` Name or service not known)"))] or equivalent public download.
- **Mapping**: Ensembl BioMart API used to map gene symbols/IDs between STRING and DEG.
 - **Fallback**: If API fails, strict string matching is attempted.
 - **Metric**: `mapping_coverage_percent` calculated as `(mapped_genes / total_essential_genes) * 100` and logged.

### 2. Centrality Computation (FR-004)
- **Algorithm**: NetworkX.
- **Optimization**: For networks with > 5,000 nodes, `betweenness_centrality` uses `k`-sampling (approximate) to ensure completion within 30 mins. Exact calculation used only for smaller networks.
- **Edge Case**: Disconnected networks result in 0 centrality; logged as warning.

### 3. Correlation & Null Testing (FR-005, SC-001, FR-010)
- **Primary Test**: Spearman correlation between centrality and essentiality.
- **Null Model A (Label Permutation)**: Essentiality labels shuffled [deferred] times to generate empirical p-value for SC-001. This tests if the observed correlation is greater than random assignment of essentiality.
- **Null Model B (Graph Rewiring)**: Degree-preserving random graphs generated to test if correlation is an artifact of degree distribution (FR-010). *Note: This is not used for the primary label association test to avoid tautology for degree centrality.*

### 4. Comparative Analysis (FR-006, FR-008)
- **Method**: PGLS using `statsmodels` with Fisher's z-transformation on correlation coefficients.
- **Tree**: Sourced from OpenTree of Life.
- **Fallback**: If tree missing, linear model with warning.

### 5. Versioning & Testing
- **Hashing**: `hash_checker.py` runs post-analysis to update `state/` YAML.
- **Contract Tests**: `main.py` explicitly calls `pytest tests/contract/`. If any schema validation fails, the build terminates immediately.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| API Rate Limiting | High (No data) | Implement exponential backoff in `data_loader.py`. |
| Large Network | Critical (Timeout) | Network sampling (k-sampling) for betweenness centrality. |
| No Phylogenetic Tree | Medium (No PGLS) | Fallback to linear model; log warning. |
| Mapping Failure | High (Low Power) | Log `mapping_coverage_percent`; skip organism if < 10%. |