# Implementation Plan: Investigating Network Centrality in ASD Resting-State fMRI

**Branch**: `001-investigate-asd-centrality` | **Date**: 2025-01-10 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-impact-of-network-cent/spec.md`

## Summary

This project implements a reproducible neuroimaging analysis pipeline to investigate network centrality differences (degree, betweenness, eigenvector) in Autism Spectrum Disorder (ASD) versus neurotypical controls using resting-state fMRI data. The approach involves downloading **pre-processed ABIDE derivatives** (fMRIPrep output) from OpenNeuro, parcellating via the Schaefer atlas, computing graph metrics with NetworkX, performing FDR-corrected group comparisons, training a logistic regression classifier, and generating brain surface visualizations. All analysis is constrained to run on GitHub Actions free-tier (CPU, 7GB RAM, no GPU).

**Critical Constraint Resolution**: The spec requires fMRIPrep preprocessing (FR-002). To satisfy this within CI limits (2 CPU, 7GB RAM, 6h), the plan **does not run fMRIPrep in CI**. Instead, it downloads pre-processed derivatives (NIfTI + BIDS sidecars) from OpenNeuro (ABIDE Preprocessed initiative). These derivatives are the direct output of fMRIPrep, satisfying the spec's requirement for fMRIPrep-processed data while ensuring CI feasibility. The pipeline validates on a **subset** of participants (e.g., 20) to fit CI constraints, with the full analysis intended for local execution or larger compute resources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `pyyaml`, `tqdm`, `bids-validator`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/derived`)  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational neuroscience analysis pipeline  
**Performance Goals**: Complete analysis on a subset (e.g., 20 participants) within 6 hours on 2 CPU cores, <7GB RAM peak. Full analysis (N=100+) requires local execution.  
**Constraints**: 
- No GPU usage.
- **No raw fMRI preprocessing in CI**: Input data must be pre-processed derivatives (fMRIPrep output) from OpenNeuro.
- Strict memory limits require chunked processing or subsampling for heavy operations.
- **No Synthetic Data**: The pipeline fails gracefully if real data is unavailable; synthetic data is strictly prohibited.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATES: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned in `code/analysis.py`. Dependencies pinned in `requirements.txt`. Data fetched from canonical OpenNeuro/ABIDE Preprocessed sources. | ✅ PASS |
| **II. Verified Accuracy** | All dataset citations in `research.md` restricted to the provided "Verified datasets" block (OpenNeuro ds0002800). No fabricated URLs. | ✅ PASS |
| **III. Data Hygiene** | Raw data (pre-processed derivatives) stored in `data/raw` with checksums recorded in state file. Derived files (time-series, matrices) saved with explicit provenance. No in-place modification. | ✅ PASS |
| **IV. Single Source of Truth** | Figures and stats in paper generation scripts will read directly from `data/derived` JSON/CSV outputs. No hand-typed numbers. | ✅ PASS |
| **V. Versioning Discipline** | Content hashes for all artifacts tracked in `state/projects/PROJ-460-...yaml`. | ✅ PASS |
| **VI. Neuroimaging Data Integrity** | **External fMRIPrep**: Pre-processed derivatives (output of fMRIPrep) are downloaded from OpenNeuro. Provenance (fMRIPrep version, parameters) is extracted from BIDS sidecars and recorded in `data/derived/preprocessing_log.yaml`. Raw scans are preserved unchanged in `data/raw`. | ✅ PASS (via External Derivatives) |
| **VII. Statistical Rigor** | FDR correction (q < 0.05) mandated for all node-wise tests. Effect sizes and CIs reported. Collinearity diagnostics included (FR-010). | ✅ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-impact-of-network-centrality/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── participant.schema.yaml
│   ├── centrality_output.schema.yaml
│   ├── classification_results.schema.yaml
│   ├── preprocessing_log.schema.yaml
│   ├── centrality_completeness_report.schema.yaml
│   ├── collinearity_diagnostics.schema.yaml
│   └── sensitivity_analysis.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-460-investigating-the-impact-of-network-cent/
├── data/
│   ├── raw/               # Downloaded ABIDE Preprocessed derivatives (NIfTI, CSV)
│   ├── processed/         # Extracted time-series (ROIs)
│   └── derived/           # Centrality metrics, adjacency matrices, results, logs
├── code/
│   ├── __init__.py
│   ├── download.py        # OpenNeuro/ABIDE Preprocessed data acquisition
│   ├── preprocess.py      # Time-series extraction from pre-processed NIfTI
│   ├── graph_analysis.py  # Centrality computation (NetworkX)
│   ├── statistics.py      # T-tests, FDR, sensitivity analysis
│   ├── classification.py  # Logistic regression, CV
│   ├── viz.py             # Nilearn surface plots
│   └── main.py            # Orchestration script
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/          # Schema validation tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular code separation. Data is strictly separated into `raw`, `processed`, and `derived` to satisfy Constitution Principle III and VI. **Subset Processing**: For CI feasibility, the pipeline processes a subset of participants while maintaining the full ROI structure. This is explicitly logged in `PreprocessingLog`.

## Complexity Tracking

No violations identified. The pipeline is linear and modular, fitting within the single-project scope.
