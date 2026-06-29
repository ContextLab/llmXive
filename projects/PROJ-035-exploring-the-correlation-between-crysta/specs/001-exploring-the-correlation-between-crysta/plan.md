# Implementation Plan: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Branch**: `001-crystal-thermal-correlation` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-crystal-thermal-correlation/spec.md`

## Summary

This feature implements a computational materials science pipeline to investigate the associational relationship between crystallographic distortion metrics (octahedral tilting, bond-length variance, tolerance factor) and thermal conductivity in perovskite structures (ABX₃). The pipeline ingests data from the Materials Project API, computes structural descriptors using pymatgen, performs statistical correlation analysis with False Discovery Rate (FDR) correction, and fits a multiple linear regression model with collinearity diagnostics. All analysis is constrained to CPU-only execution compatible with GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/processed CSVs, `data/metadata.yaml` for provenance)  
**Testing**: `pytest` (contract tests against schema, unit tests for descriptor math)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete analysis within 6 hours on 2 CPU cores, <7 GB RAM  
**Constraints**: CPU-only (no CUDA/GPU), deterministic seeds, no causal language in reports  
**Scale/Scope**: Single dataset batch (Materials Project query subset), <10k entries expected  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Plan Compliance Action |
|------------------------|------------------------|
| **I. Reproducibility** | All random states pinned (`random_state=42`); `requirements.txt` pins exact versions; CI runs from scratch. |
| **II. Verified Accuracy** | Dataset sources (Materials Project API) to be verified against primary docs before `research_accepted`; citation validation agent runs on report. |
| **III. Data Hygiene** | Raw data checksummed in `state/...yaml`; derived data written to new filenames; no in-place modification. |
| **IV. Single Source of Truth** | Report statistics trace to `data/analysis_results.csv`; figures generated from `code/` scripts, not hand-typed. |
| **V. Versioning Discipline** | Content hashes recorded for `data/` artifacts; `updated_at` timestamps updated on artifact change. |
| **VI. Computational Determinism** | Double-precision arithmetic enforced; `random_state` set for all CV splits and regressions; statistical significance (p-values) reported. |
| **VII. Dataset Provenance** | API query date and endpoint version recorded in `data/metadata.yaml`; thermal conductivity source tag (MP/NIST) recorded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-crystal-thermal-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── analysis_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-035-exploring-the-correlation-between-crysta/
├── code/
│   ├── __init__.py
│   ├── ingestion.py           # Fetches from API, validates ABX3
│   ├── descriptors.py         # Computes tilting, bond variance, tolerance
│   ├── analysis.py            # Correlation, Regression, VIF, FDR
│   ├── reporting.py           # Plots, Sensitivity Analysis, Text Gen
│   └── utils.py               # Seed pinning, checksum helpers
├── data/
│   ├── raw/                   # Raw API dumps (checksummed)
│   ├── processed/             # Cleaned CSVs
│   └── metadata.yaml          # Provenance records
├── tests/
│   ├── contract/              # Schema validation tests
│   └── unit/                  # Descriptor math tests
├── requirements.txt           # Pinned dependencies
└── README.md                  # Entry point
```

**Structure Decision**: Single project structure selected for simplicity and reproducibility. All code resides in `code/` to ensure the `Reproducibility` (Principle I) and `Single Source of Truth` (Principle IV) requirements are met via a unified entry point.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Project adheres to standard computational pipeline patterns. | N/A |

## FR/SC Coverage Map

| Requirement | Plan Phase/Step | Location |
|-------------|-----------------|----------|
| **FR-001** (Fetch MP API, filter ABX3) | Phase 1: Ingestion | `code/ingestion.py` |
| **FR-002** (Remove missing values) | Phase 1: Ingestion | `code/ingestion.py` |
| **FR-003** (Compute descriptors) | Phase 2: Descriptors | `code/descriptors.py` |
| **FR-004** (Benjamini-Hochberg FDR) | Phase 3: Analysis | `code/analysis.py` |
| **FR-005** (VIF > 5 flag) | Phase 3: Analysis | `code/analysis.py` |
| **FR-006** (Associational framing) | Phase 4: Reporting | `code/reporting.py` |
| **FR-007** (P-value sweep 0.01/0.05/0.1) | Phase 4: Reporting | `code/reporting.py` |
| **FR-008** (CPU-only) | Global Constraint | `requirements.txt` / CI config |
| **FR-009** (Scatter plots w/ CI) | Phase 4: Reporting | `code/reporting.py` |
| **FR-010** (Power justification) | Phase 3: Analysis | `code/analysis.py` |
| **SC-001** (Data retention rate) | Phase 1: Ingestion | Logs/Metadata |
| **SC-002** (Correlation significance) | Phase 3: Analysis | FDR-corrected p-values |
| **SC-003** (Model R²) | Phase 3: Analysis | Cross-validated R² |
| **SC-004** (Sensitivity coverage) | Phase 4: Reporting | P-value sweep results |
