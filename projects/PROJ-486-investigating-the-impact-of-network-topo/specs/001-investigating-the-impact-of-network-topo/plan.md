# Implementation Plan: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Branch**: `001-network-topology-entrainment` | **Date**: 2023-10-27 | **Spec**: `specs/001-investigating-the-impact-of-network-topo/spec.md`

## Summary

This feature implements a computational pipeline to investigate the statistical association between resting-state brain network topology (Clustering Coefficient, Characteristic Path Length) and neural entrainment strength. 

**Critical Methodological Clarification**: Due to the unavailability of real-world matched datasets (HCP fMRI + rhythmic entrainment metrics), the system defaults to a **Simulated Data Fallback** (FR-009) with a known ground-truth correlation (r=0.5). 
- **Purpose of Simulation**: This simulation is strictly for **Software Validation** (verifying the pipeline runs without error and correctly detects an injected signal). It is **NOT** used to validate the biological hypothesis. 
- **Scientific Claim**: The primary scientific claim regarding the "impact of network topology" remains dependent on real data, which is currently unavailable. Therefore, this study is framed as a **Pipeline Validation & Power Analysis**. Success is defined by the pipeline's ability to correctly process data, apply statistical corrections, and identify power limitations if real data were to be collected.

The implementation includes robust preprocessing, graph metric calculation using NetworkX, Multiple Linear Regression (MLR) with a deterministic fallback to Univariate analysis if collinearity is high, Holm-Bonferroni correction, and sensitivity analysis across multiple parcellation schemes (Schaefer, AAL, Power).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `networkx`, `scikit-learn`, `matplotlib`, `seaborn`  
**Storage**: Local CSV/Parquet files. All output formats strictly adhere to the schemas defined in `contracts/` (specifically `output.schema.yaml`, `dataset.schema.yaml`, `correlation_results.schema.yaml`, `sensitivity.schema.yaml`, `topology_metrics.schema.yaml`).  
**Testing**: `pytest` (unit tests for metrics, integration tests for pipeline).  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 cores, 7GB RAM, CPU-only).  
**Project Type**: Data Analysis Pipeline / Scientific Simulation.  
**Performance Goals**: Complete analysis of N=50 subjects with 200x200 matrices within 6 hours.  
**Constraints**: No GPU; no deep learning training; strict memory management (streaming/chunking if needed); deterministic random seeds.  
**Scale/Scope**: N=50 subjects (simulated or subset); 3 parcellation schemes; 2 topology metrics.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds (numpy, python) will be pinned in `code/analysis.py`. External data sources (simulated) are deterministic.
- **II. Verified Accuracy**: Citations for HCP and methodology will be validated by the **Reference-Validator Agent** against the `# Verified datasets` list. The agent will enforce the `CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7) before any review points are awarded. No invented URLs.
- **III. Data Hygiene**: All generated data files will be checksummed. No in-place modification of raw inputs.
- **IV. Single Source of Truth**: All figures and statistics in the report will be generated directly from the `data/` CSV outputs, not hand-typed.
- **V. Versioning Discipline**: A Python script (`code/state_manager.py`) will compute SHA-256 hashes of all generated artifacts (CSVs, PNGs) and write them to `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml` under the `artifact_hashes` map. This automation ensures compliance with the Constitution.
- **VI. Statistical Rigor**: The plan explicitly includes Holm-Bonferroni correction (FR-004, SC-003) and a deterministic VIF-based decision tree for collinearity handling.
- **VII. Multimodal Data Alignment**: The pipeline performs an inner join on `subject_id` and explicitly handles missing matches by triggering the simulation fallback (FR-003, FR-009).

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-entrainment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    ├── correlation_results.schema.yaml
    ├── sensitivity.schema.yaml
    └── topology_metrics.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration (seeds, thresholds, paths)
├── data_loader.py       # Data ingestion and validation (FR-007, FR-008)
├── graph_metrics.py     # NetworkX topology calculation (FR-002)
├── stats_engine.py      # MLR, VIF, Holm-Bonferroni, Univariate fallback (FR-004)
├── simulation.py        # Synthetic data generation (FR-009)
├── viz.py               # Scatter plots, bar charts (FR-005, FR-010)
├── state_manager.py     # Hashing and state update (Constitution Principle V)
└── main.py              # Orchestrator
tests/
├── test_graph_metrics.py
├── test_stats_engine.py
├── test_simulation.py
└── test_integration.py
```

**Structure Decision**: Single `code/` directory with modular functions is selected to minimize overhead and simplify testing on the free-tier runner. No separate backend/frontend is required as this is a batch processing pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The complexity is inherent to the scientific method (simulation + sensitivity analysis + robust collinearity handling). | A single-atlas, single-metric approach would fail SC-002 (Robustness) and SC-003 (Multiple Comparisons). A simple MLR without VIF fallback would fail SC-003 if predictors are collinear. |