# Implementation Plan: Predicting Gene Essentiality from Protein Interaction Network Topology

**Branch**: `001-gene-regulation` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
This plan implements a computational biology pipeline to test the hypothesis that network topology (centrality metrics) in Protein-Protein Interaction (PPI) networks predicts gene essentiality. The system downloads PPI data from STRING and essentiality labels from DEG for multiple model organisms, computes centrality metrics (degree, betweenness, eigenvector), calculates Spearman correlations, and performs comparative statistical analysis (Phylogenetic Meta-Analysis) across species. The implementation prioritizes CPU-feasibility on GitHub Actions runners, rigorous data validation, and robust sensitivity analysis against network confidence thresholds.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `pandas`, `scipy`, `statsmodels`, `requests`, `biopython`, `pymer4` (for phylogenetic meta-analysis), `openpyxl`  
**Storage**: Local filesystem (`data/` for raw/processed data, `code/` for scripts)  
**Testing**: `pytest` with contract validation against `contracts/*.schema.yaml` files (specifically `tests/contract/test_centrality_schema.py`, `tests/contract/test_correlation_schema.py`, `tests/contract/test_pgls_schema.py`).  
**Target Platform**: Linux (GitHub Actions Runner: CPU, ~7 GB RAM)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete analysis for 5-8 organisms within 6 hours; centrality calculation < 30 mins/organism.  
**Constraints**: No local GPU; strict memory limits (modest RAM capacity); data must be streamed or sampled to fit disk.  
**Scale/Scope**: -model organisms; networks up to large-scale node counts; A substantial number of edges per organism.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds in `config.py`, and automated data fetching from canonical sources (STRING/DEG) on every run. |
| **II. Verified Accuracy** | **PASS** | The `Reference-Validator` agent is explicitly integrated into the pipeline. It runs at three gates: (1) on artifact write (citations), (2) before advancement, and (3) at the `research_review` transition. The plan includes a script to invoke this agent, ensuring Principle II is enforced, not just intended. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data files (`data/`) and immutable derivation of processed datasets. |
| **IV. Single Source of Truth** | **PASS** | A `traceability.py` script is mandated to generate a manifest linking every statistic in the paper to exactly one row in `data/` and one code block in `code/`. This enforces the "one row, one block" requirement of Principle IV programmatically. |
| **V. Versioning Discipline** | **PASS** | Content hashes for data/code will be recorded in `state/` YAML; artifacts invalidated on change. |
| **VI. Cross-Species Consistency** | **PASS** | Pipeline enforces identical preprocessing, centrality computation (NetworkX), and mapping (BioMart) for all organisms. |
| **VII. Threshold Sensitivity** | **PASS** | Plan explicitly schedules sensitivity analysis across thresholds [,, 900] with logging of edge set changes. |

## Project Structure

### Documentation (this feature)
```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── organism_profile.schema.yaml
    ├── centrality_result.schema.yaml
    └── correlation_result.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-452-predicting-gene-essentiality-from-protei/
├── code/
│   ├── __init__.py
│   ├── config.py              # Random seeds, thresholds, organism IDs
│   ├── data/
│   │   ├── download_string.py # Fetch PPI from STRING (v)
│   │   ├── download_deg.py    # Fetch Essentiality from DEG
│   │   ├── download_depmap.py # Fetch independent validation data
│   │   └── map_genes.py       # Ensembl BioMart mapping
│   ├── analysis/
│   │   ├── centrality.py      # NetworkX metrics (GCC only)
│   │   ├── correlation.py     # Spearman & Mann-Whitney U
│   │   ├── phylo_meta.py      # Phylogenetic Meta-Analysis (Fisher's Z)
│   │   ├── sensitivity.py     # Threshold loop
│   │   └── null_model.py      # Degree-preserving random graphs
│   └── utils/
│       ├── graph_utils.py     # Random graph generation, sparsity checks
│       ├── logging.py
│       └── traceability.py    # SSOT manifest generator
├── data/
│   ├── raw/                   # Downloaded CSV/TSV (checksummed)
│   ├── processed/             # Mapped, cleaned data
│   └── results/               # Correlation tables, PGLS outputs
├── tests/
│   ├── contract/              # Schema validation tests (mapped to specific contracts)
│   ├── integration/           # End-to-end pipeline tests
│   └── unit/                  # Logic tests (e.g., centrality calculation)
└── requirements.txt
```

**Structure Decision**: Single-project structure chosen to simplify data flow and dependency management for a research pipeline. Modular separation of `data/`, `analysis/`, and `utils/` ensures maintainability and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Phylogenetic Meta-Analysis** | Required for cross-species comparison (FR-006) to account for phylogenetic non-independence. | Simple t-tests or ANOVA would violate statistical assumptions by ignoring evolutionary history, leading to inflated Type I errors. |
| **Sensitivity Analysis Loop** | Required by SC-002 and FR-007 to validate robustness against network construction parameters. | A single-threshold run would fail to demonstrate the stability of findings, risking publication of artifacts. |
| **Gene Mapping (BioMart)** | Required by FR-003 to resolve identifier mismatches between STRING and DEG. | Hardcoded mappings are unscalable and error-prone across multiple organisms and genome versions. |
| **Traceability Script** | Required by Constitution Principle IV to enforce "one row, one block" traceability. | Manual tracking is error-prone and non-reproducible; a script ensures the SSoT requirement is met programmatically. |