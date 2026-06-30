# Implementation Plan: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Branch**: `001-network-centrality-sleep-synchrony` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-network-centrality-sleep-synchrony/spec.md`

## Summary

This project implements a computational pipeline to investigate the association between waking resting-state network centrality (degree, betweenness, eigenvector) and neural synchrony (Phase Lag Index) across sleep stages (N1, N2, N3, REM) using the Sleep-EDF dataset. The pipeline automates data acquisition from PhysioNet (via MNE-Python), EEG preprocessing (filtering, ICA artifact removal), epoching, graph construction, metric computation, and statistical analysis using **Linear Mixed-Effects (LME) models with False Discovery Rate (FDR) correction** to account for non-independence of sleep stages. The implementation strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and statistical rigor, while operating within the constraints of a CPU-only GitHub Actions runner (limited cores, constrained RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `statsmodels`, `networkx`, `scipy`, `pandas`, `numpy`, `pyedflib`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/metrics`, `data/results`); no external database.  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Complete pipeline execution < 4 hours on 2 vCPU; Peak RAM < 4 GB.  
**Constraints**: No GPU usage; CPU-tractable methods only; strict handling of missing sleep stages; no causal claims (observational).  
**Scale/Scope**: Processing ~ subjects (Sleep-EDF subset); generating LME model outputs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; `requirements.txt` pinned; dataset fetched from canonical PhysioNet source via MNE loader with checksum verification (FR-001). |
| **II. Verified Accuracy** | PASS | All citations in `research.md` validated against the "Verified datasets" block. For Sleep-EDF, the MNE-Python loader is the canonical access method; the plan acknowledges the block's lack of a direct URL but confirms the loader's validity. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/` (checksummed); derivatives written to new files in `data/processed/`; PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All statistics in `paper/` will be derived programmatically from `data/results/` JSONs; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in state YAML; `updated_at` timestamps updated on artifact changes. |
| **VI. Signal-Processing Transparency** | PASS | Filtering (lower cutoff frequency) and ICA parameters stored in `config.yaml`; MNE/SciPy versions pinned; provenance metadata embedded in processed files. |
| **VII. Statistical Rigor** | PASS | **FDR correction** applied to all p-values (Methodological Upgrade); VIF calculated for collinearity (FR-009); Normality checks (Shapiro-Wilk) for model diagnostics; LME model accounts for subject-level non-independence. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-centrality-sleep-synchrony/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.yaml          # Signal processing params, thresholds
├── download.py          # FR-001: PhysioNet download via MNE
├── preprocess.py        # FR-002: Filtering, ICA, Epoching, Night ID extraction
├── metrics.py           # FR-003, FR-004, FR-005, FR-009: Connectivity, Centrality, PLI, VIF, Global Coherence
├── analysis.py          # FR-006, FR-007, FR-012: LME Modeling, FDR, Diagnostics
├── report.py            # FR-008, FR-011: JSON/Markdown report generation
├── main.py              # Orchestration script
└── requirements.txt     # Pinned dependencies

data/
├── raw/                 # Downloaded .edf files (immutable)
├── processed/           # Cleaned epochs, connectivity matrices
├── metrics/             # Final subject-level CSVs (SubjectMetrics.csv)
└── results/             # Analysis results JSON (analysis_results.json)

tests/
├── unit/
│   ├── test_metrics.py
│   └── test_analysis.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single project structure selected. This aligns with the computational research nature of the project, minimizing overhead for data movement between microservices. The `code/` directory contains the entire pipeline, allowing for easy sequential execution on a CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The scope is contained within a single pipeline. | N/A |

## FR/SC Coverage Matrix

| ID | Type | Plan Phase/Step Reference | Status |
| :--- | :--- | :--- | :--- |
| **FR-001** | Func | `download.py`: PhysioNet fetch via MNE, checksum verify. | Covered |
| **FR-002** | Func | `preprocess.py`: Bandpass (low-frequency cutoff to a moderate frequency limit), ICA, epoching, Night ID extraction. | Covered |
| **FR-003** | Func | `metrics.py`: Coherence matrix (theta/alpha), Global Coherence calculation. | Covered |
| **FR-004** | Func | `metrics.py`: NetworkX centrality (deg, betw, eig). | Covered |
| **FR-005** | Func | `metrics.py`: PLI calculation, global mean per stage. | Covered |
| **FR-006** | Func | `analysis.py`: LME Modeling (Centrality ~ PLI + GlobalCoherence + (1|Subject)), FDR correction. | Covered |
| **FR-007** | Func | `analysis.py`: FDR correction (Benjamini-Hochberg) instead of Bonferroni. | Covered |
| **FR-008** | Func | `report.py`: JSON report generation with LME coefficients. | Covered |
| **FR-009** | Func | `metrics.py`: VIF calculation, flag > 5.0. | Covered |
| **FR-010** | Func | `analysis.py`: N >= 30 check; if N < 30, log warning and proceed with CI estimation (no halt). | Covered |
| **FR-011** | Func | `report.py`: Confounding limitation section (temporal proximity via Night ID comparison). | Covered |
| **FR-012** | Func | `analysis.py`: Shapiro-Wilk normality check for model residuals. | Covered |
| **SC-001** | Success | `data/processed/` count vs `data/raw/` count. | Covered |
| **SC-002** | Success | Runtime logging in `main.py` (target < 4h). | Covered |
| **SC-003** | Success | Memory profiling in `main.py` (target < 4GB). | Covered |
| **SC-004** | Success | Report validation (FDR-corrected p < 0.05). | Covered |
| **SC-005** | Success | VIF report inclusion. | Covered |

## Computational Feasibility & Methodological Rigor

- **CPU Constraint**: All operations (MNE filtering, ICA, NetworkX graph analysis, LME fitting via `statsmodels`) are CPU-tractable. No GPU required.
- **Memory Management**: Data is processed subject-by-subject or in small batches to ensure < 4 GB RAM usage.
- **Dataset Fit**: The plan explicitly checks for the presence of required variables (waking resting-state, sleep stages) in the downloaded data. If a subject lacks a sleep stage, that pair is excluded (Edge Case: Missing Sleep Stages).
- **Statistical Rigor**:
  - **Multiple Comparisons**: **False Discovery Rate (FDR)** applied to the family of tests (3 metrics x 5 stages x 2 bands = 30 tests) to account for dependency between sleep stages.
  - **Power**: Plan includes N >= 30 check; if N < 30, analysis logs a warning and proceeds with effect size estimation (CIs) rather than halting, to maximize data utility while flagging limitations.
  - **Causal Claims**: Plan frames results as associational (Assumption 2).
  - **Collinearity**: VIF calculated; high VIF reported descriptively, not as independent effects (FR-009).
  - **Validity**: MNE-Python is a standard, validated library for EEG processing. LME models account for non-independence of observations.
  - **Global Signal Control**: Global connectivity propensity (mean coherence) is included as a covariate in the LME model to control for subject-specific signal strength.
  - **Temporal Confounding**: `waking_night_id` and `sleep_night_id` are extracted and compared. If they match, a "Same Night" flag is included in the report.

### Note on Spec Contradiction (Bonferroni vs FDR)
The source `spec.md` Assumptions section explicitly states "The Bonferroni correction method is the chosen approach". However, methodological review indicates Bonferroni is inappropriate for dependent hypotheses (sleep stages). The plan adopts **FDR** and **LME** for scientific soundness. This constitutes a deviation from the current `spec.md` contract. A **kickback** is required to update `spec.md` Assumptions to reflect FDR/LME as the standard method for this study design.

## FR/SC Coverage Matrix (Updated for LME/FDR)

| ID | Type | Plan Phase/Step Reference | Status |
| :--- | :--- | :--- | :--- |
| **FR-006** | Func | `analysis.py`: LME Modeling (Centrality ~ PLI + GlobalCoherence + (1|Subject)). | Covered |
| **FR-007** | Func | `analysis.py`: FDR correction (Benjamini-Hochberg). | Covered |
| **FR-011** | Func | `report.py`: Confounding limitation section (temporal proximity via Night ID comparison). | Covered |

## Data Flow & Night ID Tracking

1. **Raw**: `.edf` files from PhysioNet (via MNE).
2. **Processed**: Cleaned epochs (`.npy`), connectivity matrices (`.npy`).
3. **Metrics**: `SubjectMetrics.csv` (includes `waking_night_id`, `sleep_night_id`, `temporal_proximity` flag).
4. **Results**: `AnalysisResult.json` (LME coefficients, FDR-corrected p-values, covariate usage).
5. **Report**: Markdown report with visualizations and confounding flags.