# Implementation Plan: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Branch**: `001-neural-oscillations-tDCS-biomarker` | **Date**: 2026-06-24 | **Spec**: `specs/001-neural-oscillations-tDCS-biomarker/spec.md`
**Input**: Feature specification from `/specs/001-neural-oscillations-tDCS-biomarker/spec.md`

## Summary

This feature implements a computational pipeline to evaluate whether resting-state and task-related EEG oscillatory features can predict individual motor performance improvement after anodal tDCS. The system ingests public EEG data, processes it using MNE-Python (band-pass 1–45 Hz, common average reference), extracts spectral power (delta–gamma) and connectivity (PLV, wPLI) features, and fits a Ridge Regression model with 5-fold cross-validation.

**Critical Data Constraint**: No verified public dataset currently exists that contains *paired* EEG recordings and tDCS motor performance scores for the same subjects. Consequently, the "Primary Mode" (real hypothesis testing) is **skipped** for this iteration.

Instead, the system implements a **Positive Control Mode**: it generates synthetic tDCS response variables with a **known, injected signal** correlated to specific EEG features (e.g., C3-C4 beta power). This allows the pipeline to validate its ability to *detect* a known biomarker signal, distinguishing between "pipeline validation" (code runs) and "scientific validation" (model detects signal). If no signal is detected in Positive Control, the pipeline is flagged as broken.

The pipeline includes rigorous validation via permutation testing, FDR correction, and sensitivity analysis (FR-007), all constrained to run on CPU-only GitHub Actions runners (≤7 GB RAM, ≤6 h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: MNE-Python (EEG processing), scikit-learn (modeling), numpy, pandas, scipy, statsmodels (statistics), pyyaml (contracts).  
**Storage**: Local file system (raw data in `data/raw`, processed in `data/processed`, models in `models/`). No external database.  
**Testing**: `pytest` (unit tests for preprocessing, integration tests for pipeline modes).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Data Science Pipeline / Research Tool.  
**Performance Goals**: Runtime ≤ 6 hours; Peak RAM ≤ 7 GB; Disk ≤ 14 GB.  
**Constraints**: No GPU/CUDA; no large-LLM inference; strict separation of Positive Control logic; synthetic targets must have a known injected signal for validation.  
**Scale/Scope**: Single cohort analysis (approx. –100 subjects from PhysioNet); ~10–20 EEG channels; ~5–10 spectral/connectivity features per subject.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical URLs only. |
| **II. Verified Accuracy** | PASS | All dataset URLs in `research.md` are restricted to the "# Verified datasets" block provided in the prompt. No fabricated citations. |
| **III. Data Hygiene** | PASS | Raw data checksummed on ingestion (SHA-256); no in-place modifications; derived files written with new names; PII scan passed (public anonymized data). |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/processed` and `code/`; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Artifact hashes tracked in `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml` via SHA-256; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Neurophysiological Data Integrity** | PASS | Pipeline enforces 1–45 Hz filter, common average reference, and bad-channel logging via MNE-Python. |
| **VII. Biomarker Validation and Generalization** | DEFERRED | Constitution requires evaluation on an independent public dataset. No second verified paired dataset exists. This phase is deferred until a second dataset is identified. Current validation is limited to Positive Control (synthetic). |

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-oscillations-tDCS-biomarker/
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
code/
├── 01_ingest_preprocess.py      # Data download, checksum, mode detection (Primary/Fallback/Positive Control), filtering
├── 02_feature_extraction.py     # Spectral power, connectivity (PLV, wPLI) - ROI specific
├── 03_modeling.py               # Ridge regression, CV, synthetic target generation (Positive Control)
├── 04_validation.py             # Permutation test, FDR, sensitivity analysis
├── 05_report.py                 # Report generation
├── utils/
│   ├── config.py                # Paths, seeds, thresholds
│   └── io_helpers.py            # CSV/Parquet loaders
└── tests/
    ├── test_preprocess.py
    ├── test_positive_control.py
    └── test_validation.py

data/
├── raw/                         # Downloaded datasets (checksummed)
├── processed/                   # Aligned epochs, feature matrices
└── synthetic/                   # Positive Control synthetic targets

models/
└── ridge_model.pkl              # Serialized model (Positive Control only)

requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure all data flows through a linear pipeline suitable for CI/CD. Modular scripts allow independent testing of preprocessing, feature extraction, and modeling steps.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Positive Control Mode** | Required because no paired real data exists. A simple "fail on missing data" would prevent any validation. | A simple "fail" would leave the pipeline untested. Positive Control validates the *sensitivity* of the biomarker detection. |
| **Permutation Testing** | Required by SC-002/US-3 for robust statistical inference. | Standard parametric p-values are insufficient for small sample sizes and non-normal distributions common in EEG. |
| **FDR Correction** | Required by FR-006 to control family-wise error across multiple frequency bands. | Bonferroni correction is too conservative for correlated EEG features; FDR balances sensitivity and specificity. |

## Implementation Phases

### Phase 0: Data Ingestion & Checksum Verification (FR-001, SC-001)
**Task 0.1**: Download PhysioNet EEG Motor Movement/Imagery dataset.
**Task 0.2**: Compute SHA-256 checksums for all raw files and log to `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml`.
**Task 0.3**: Verify data integrity against checksums. If mismatch, halt.
**Task 0.4**: Check for paired tDCS data. **Result**: No paired data found. Switch to **Positive Control Mode**.
**Task 0.5**: Generate synthetic tDCS response with **known injected signal** (e.g., [deferred] correlation with C3-C4 beta power) and random noise. Verify correlation is low before training.

### Phase 1: Preprocessing & Feature Extraction (FR-003, FR-004, FR-005)
**Task 1.1**: Band-pass filter (1–45 Hz) and re-reference (Common Average).
**Task 1.2**: Extract spectral power (Delta, Theta, Alpha, Beta, Gamma) via Welch's method.
**Task 1.3**: Extract connectivity (PLV, wPLI) for **ROI pairs** (C3-C4, C3-Cz, C4-Cz) and Global Mean.
**Task 1.4**: Assemble feature matrix.

### Phase 2: Modeling (FR-005)
**Task 2.1**: Fit Ridge Regression with 5-fold CV.
**Task 2.2**: In Positive Control Mode, verify model detects the injected signal (R² > 0, p < 0.05).
**Task 2.3**: Flag outputs as `structural_validation_only` if signal is not detected (pipeline broken).

### Phase 3: Validation & Sensitivity (FR-006, FR-007, SC-004)
**Task 3.1**: Run a sufficient number of permutations to establish the null distribution.
**Task 3.2**: Apply FDR correction.
**Task 3.3**: Perform sensitivity analysis: sweep p ∈ {0.01, 0.05, 0.1} and R² ∈ {0.2, 0.3, 0.4}.
**Task 3.4**: Calculate `stability_variance`. Success defined as `stability_variance ≤ 0.05`.

### Phase 4: Reporting (SC-002, SC-003)
**Task 4.1**: Generate report with R², p-values, and sensitivity table.
**Task 4.2**: Log runtime and RAM usage to verify NFR-001 (≤6h, ≤7GB).