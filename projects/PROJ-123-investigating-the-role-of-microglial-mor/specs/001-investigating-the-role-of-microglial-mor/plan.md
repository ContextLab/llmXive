# Implementation Plan: Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to ingest confocal microscopy images, extract quantitative microglial morphological metrics (branch points, total length, soma area, Sholl intersections), and perform multivariate regression analysis to predict cognitive status. The core innovation is the explicit modeling of interaction effects between "Pathology Status" (Normal vs. Early AD) and "Brain Region" (Hippocampus vs. Prefrontal Cortex) to distinguish normal aging from early Alzheimer's pathology. The implementation strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and statistical rigor (PCA for collinearity, VIF checks, sensitivity analysis).

**Critical Status Note**: As no verified public datasets exist for the specific matched biological variables required, this plan proceeds with **synthetic data generation** for *pipeline logic validation* only. The core biological hypothesis (interaction effects in real neurodegeneration) remains untested until verified real data is acquired. This is a known blocking dependency for the final research conclusion.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `opencv-python-headless`, `scikit-image`, `pyyaml`  
**Storage**: Local filesystem (`data/`), CSV/Parquet intermediates  
**Testing**: `pytest` (contract tests, unit tests for extraction logic, null-hypothesis validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM)  
**Project Type**: Computational Research Pipeline (CLI)  
**Performance Goals**: Runtime < 6 hours; Memory < 7GB; Extraction error < 10% vs manual ground truth (applies to synthetic validation phase only)  
**Constraints**: NO GPU; NO deep learning models for segmentation (uses classical image processing); All datasets must be CPU-loadable; Strict adherence to verified dataset URLs only (currently none available).  
**Scale/Scope**: Processing of a subset of public microscopy images for validation

The research question is: [Research Question]. The method is: [Method]. References: [References].; Scalable to full dataset if memory permits via chunking.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS (Logic) / BLOCKED (Data)** | All random seeds pinned. `requirements.txt` pins versions. Pipeline *designed* to fetch from canonical sources, but currently relies on synthetic data due to lack of verified URLs. |
| **II. Verified Accuracy** | **PASS (Logic) / BLOCKED (Data)** | Citations restricted to the "Verified datasets" block (currently empty of URLs). No fabricated URLs. Code logic validated against synthetic ground truth. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed. Transformations produce new files. No in-place modification. PII scan enabled. |
| **IV. Single Source of Truth** | **PASS** | All stats trace to `data/` CSVs. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in state YAML. Content hashes for code/data. |
| **VI. Neuro-Image Quantification Rigor** | **PASS** | Pipeline implements *algorithmic logic* of Fiji's Simple Neurite Tracer (skeletonization) and Microglial Morphometry plugins using `scikit-image`. Region-specific bias documented. |
| **VII. Distinct Pathological State Modeling** | **PASS** | Regression model explicitly includes `PathologyStatus * BrainRegion` interaction terms. VIF checks enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-123-investigating-the-role-of-microglial-mor/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py              # Paths, seeds, constants
│   ├── data_ingestion.py      # FR-001, FR-002, FR-008
│   ├── morphometry.py         # FR-003, FR-006 (Sholl), FR-011 (PCA)
│   ├── analysis.py            # FR-004, FR-005, FR-009, FR-010
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # Downloaded images (checksummed)
│   ├── processed/             # Extracted metrics CSVs
│   └── intermediates/         # Merged datasets, PCA outputs
├── tests/
│   ├── unit/
│   │   ├── test_morphometry.py
│   │   └── test_analysis.py
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_pipeline.py
└── reports/
    └── final_report.md        # Output with causality_warning
```

**Structure Decision**: Single-project CLI structure selected. This minimizes overhead for a research pipeline, allowing direct script execution in a single virtual environment. Tests are separated into unit, contract, and integration to ensure both logic correctness and schema compliance.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **PCA before Regression** | Morphological features (branch points, length) are definitionally collinear. | Direct regression would yield inflated VIF > 5.0, violating FR-004 and FR-011, making coefficients uninterpretable. *Mitigation*: Loadings will be mapped back to original features for biological interpretation. |
| **Dynamic Pathology Thresholding** | Public datasets often lack explicit "Early AD" labels. | Hard-coding a fixed threshold would fail on heterogeneous datasets; dynamic calculation (p of control) ensures robustness (FR-010). *Mitigation*: Threshold calculated on a strictly separated training set to prevent leakage. |
| **Sensitivity Analysis Loop** | Sholl radius choice is arbitrary. | Single-run analysis risks artifact-driven conclusions; sweeping multiple micron-scale ranges validates robustness (FR-006, SC-003). |

## Blocking Dependencies

1.  **Verified Matched Dataset**: No verified URL exists for a dataset containing *both* high-res microglial images (Hippocampus/PFC) AND matched cognitive scores (MWM) AND pathology markers for the same subjects.
    *   *Impact*: The core hypothesis (interaction effect in real biology) cannot be tested.
    *   *Current Plan*: Proceed with synthetic data to validate code logic (extraction, regression, interaction detection).
    *   *Next Step*: Await discovery of a verified dataset or acquisition of local data.
2. **Ground Truth for Extraction**: No verified manual annotations exist for the target dataset to validate the [deferred] error rate.
    *   *Impact*: Extraction accuracy cannot be measured against real biology.
    *   *Current Plan*: Validate against synthetic ground truth (known branch counts) to ensure the pipeline logic is correct.