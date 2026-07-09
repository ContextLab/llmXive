# Implementation Plan: Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

**Branch**: `001-assessing-filtering-impact` | **Date**: 2026-06-29 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-assessing-the-impact-of-data-filtering-o/spec.md`

## Summary
This feature implements a computational pipeline to assess how Signal-to-Noise Ratio (SNR) and morphology score thresholds impact gravitational lens detection rates and purity. The system processes the **Strong Lens Finding Challenge (SLFC)** dataset (the only verified source with the required schema), applies a systematic grid of thresholds, validates detections against the dataset's known ground truth (lens vs. non-lens labels), and performs statistical analysis (Cumulative Link Models, Benjamini-Yekutieli) to quantify trends. The implementation strictly adheres to CPU-only constraints (GitHub Actions free tier) and ensures all Functional Requirements (FRs) and Success Criteria (SCs) are explicitly mapped to implementation phases.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `matplotlib`, `astropy`, `scikit-learn`, `pyyaml`, `statsmodels`  
**Storage**: Local filesystem (CSV/Parquet) within `data/` and `code/`  
**Testing**: `pytest` (unit tests for filtering logic, integration tests for full pipeline)  
**Target Platform**: Ubuntu-latest (GitHub Actions Runner: 2 CPU, 7GB RAM, No GPU)  
**Project Type**: Data Analysis CLI / Script Suite  
**Performance Goals**: Runtime ≤ 6 hours; Memory ≤ 6GB (peak); Disk ≤ 12GB  
**Constraints**: No GPU/CUDA; Chunked data loading; Deterministic random seeds; No causal claims.  
**Scale/Scope**: Grid size: 16 (SNR) × 7 (Morph) = 112 threshold combinations. Dataset: SLFC (a medium-to-large scale dataset).

> **Note on Dataset Feasibility**: The spec references a 12GB DES Year 3 Gold catalog. The verified datasets block does **not** contain a direct link to the DES Year 3 Gold catalog with pre-computed `morphology_score`. The implementation will use the **Strong Lens Finding Challenge (SLFC)** dataset as the *validated proxy* for the DES context. SLFC contains real image cutouts with known labels (lens/non-lens) and features (SNR, morphology) or allows their extraction. This ensures that "purity" and "detection rates" are calculated against real, independent ground truth, not fabricated data.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` used; Data checksums recorded. |
| **II. Verified Accuracy** | PASS | All dataset URLs in `research.md` are from the "Verified datasets" block (SLFC). The Reference-Validator Agent checks the SLFC citation and the methodology for the proxy. |
| **III. Data Hygiene** | PASS | Raw data immutable; derivations in new files; checksums in `state.yaml`. |
| **IV. Single Source of Truth** | PASS | All metrics trace to specific CSV rows in `data/processed/`; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes updated on artifact changes; `state.yaml` is explicitly updated by the `Advancement-Evaluator` agent with `updated_at` timestamps. |
| **VI. Simulation-Based Validation** | PASS | Purity metrics validated against the *real* ground truth labels in the SLFC dataset (lens vs. non-lens). |
| **VII. Threshold Grid Completeness** | PASS | Grid explicitly iterates SNR across a low-signal range and Morph across a moderate-to-high range. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-filtering-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-285-assessing-the-impact-of-data-filtering-o/
├── code/
│   ├── __init__.py
│   ├── config.py           # Path constants, grid definitions, seed
│   ├── data_loader.py      # Chunked loading, SLFC ingestion
│   ├── filter_engine.py    # Threshold grid application, counting logic
│   ├── validation.py       # Label matching, purity calculation
│   ├── stats_analysis.py   # CLM, BY correction, sensitivity
│   ├── visualization.py    # Plot generation
│   └── main.py             # Orchestration script
├── data/
│   ├── raw/
│   │   ├── slfc_dataset.parquet      # Verified SLFC source
│   │   └── injection_ground_truth.csv # Explicit ground truth artifact
│   └── processed/
│       ├── detection_matrix.csv      # FR-002 output
│       ├── purity_metrics.csv        # FR-003 output
│       ├── sensitivity_sweep.csv     # FR-006 output
│       ├── injection_recovery_report.json # FR-008 output
│       └── memory_profile.csv        # SC-005 output
├── tests/
│   ├── test_filter_engine.py
│   ├── test_validation.py
│   └── test_stats_analysis.py
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is selected to minimize overhead and ensure all scripts run in a single environment. This aligns with the CLI nature of the analysis and the constraints of the GitHub Actions runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Chunked Loading** | Spec FR-001 requires handling a dataset that *could* be large. | Loading full dataset into RAM would exceed 7GB limit on CI runners. |
| **SLFC Proxy** | Verified datasets do not contain the full DES Year 3 Gold catalog with required schema. SLFC is the only verified source with real labels and features. | Relying solely on synthetic data would invalidate the purity metric (circular). |
| **FDR Correction (BY)** | FR-005 requires controlling family-wise error across 112+ *dependent* tests. | Standard Benjamini-Hochberg assumes independence; Benjamini-Yekutieli is robust to dependency. |
| **Separate Sensitivity Artifact** | Addressing Unresolved Concern: T020/T004 dependency. | Merging sweep logic into main purity calculation obscures the specific "variation report" required by SC-002. |
| **Memory Measurement** | SC-005 requires active measurement, not just implementation. | Implementing chunked loading does not prove the memory footprint is within limits without logging. |
| **Cumulative Link Models (CLM)** | Logistic Regression violates independence assumption for nested data. | CLM correctly models the cumulative nature of detection thresholds. |

## Implementation Phases

### Phase 0: Data Ingestion & Validation (T004, T005a, T005b)
- **T004**: Load SLFC dataset. Extract/Verify columns `SNR`, `morphology_score`, `RA`, `Dec`, `is_lens`. **Save injection positions to `data/raw/injection_ground_truth.csv`** to serve as explicit input for T021.
- **T005a**: Implement chunked loading to process the dataset without exceeding RAM.
- **T005b**: **Measure and Log Memory**: Actively track peak RAM usage during loading and filtering. Output to `data/processed/memory_profile.csv` to satisfy SC-005. This task explicitly focuses on the measurement/verification of the footprint.

### Phase 1: Threshold Grid & Purity (T010, T011)
- **T010**: Iterate through the defined grid (SNR 5-20, Morph 0.3-0.9).
- **T011**: For each grid point, calculate detection counts (passing threshold) and Purity (TP/(TP+FP)) using the *real* SLFC labels (lens vs. non-lens). Output `detection_matrix.csv`.

### Phase 2: Statistical Analysis (T020, T021)
- **T020**: **Sensitivity Analysis**: Sweep SNR cutoff (Base ± 0.5, ± 1.0). Calculate `fp_variation` (change in FP rate) for each step. Output `sensitivity_sweep.csv` (SC-002). This task is separated from the main purity calculation to ensure the specific variation report is generated.
- **T021**: **Recovery Validation**: Calculate the recovery rate of true lenses at the base threshold. **Generate `injection_recovery_report.json`** with a pass/fail status for the ≥95% threshold (FR-008). This explicitly mandates the generation of the report artifact.

### Phase 3: Visualization & Reporting (T030)
- **T030**: Generate plots (Purity vs. Threshold, Recovery vs. Threshold). Apply Benjamini-Yekutieli correction to p-values from Bootstrap tests on Recovery Rates. Use Cumulative Link Models (CLM) for trend analysis.
