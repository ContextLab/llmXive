# Implementation Plan: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Branch**: `001-neural-oscillations-tDCS-biomarker` | **Date**: 2026-06-24 | **Spec**: `specs/001-neural-oscillations-tDCS-biomarker/spec.md`
**Input**: Feature specification from `/specs/001-neural-oscillations-tDCS-biomarker/spec.md`

## Summary

This feature implements a rigorous, CPU‑tractable pipeline to test the hypothesis: *“Can resting‑state and task‑related EEG oscillatory features predict an individual’s motor performance improvement after a single session of anodal tDCS?”*  

**CRITICAL DATA CONSTRAINT**: The specification mandates a **Single‑Source Paired Dataset** (FR‑001, FR‑011, FR‑015). After exhaustive search of the verified public repositories (OpenNeuro, PhysioNet, Kaggle), **no dataset containing both raw EEG and paired tDCS motor scores for the same subjects was found**.  
Consequently, the pipeline will run exclusively in **Data Insufficient Mode** for the current execution. It will generate a `verified_source_manifest.json` indicating the absence of paired data and terminate the statistical modeling stage. **No synthetic data are created.**

**Why this distinction matters**: The hypothesis remains scientifically valid, but without a paired dataset the core predictive analysis cannot be performed. The plan separates the *contingent* statistical workflow (Primary Mode) from the *always‑executed* data‑verification workflow. **Primary Mode is currently a theoretical construct** that will only be executable if a new, verified single-source dataset is discovered in the future.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `pyyaml`, `jsonschema` (for runtime contract validation), `statsmodels` (for power analysis).  
- **Storage**: Local file system (`data/`, `output/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner, 2 CPU, ≤7 GB RAM, ≤6 h)  
- **Constraints**: No GPU, no large‑scale deep learning, all steps CPU‑friendly. Runtime contract validation uses `jsonschema` to enforce data integrity per Constitution Principle III.

## Phase Overview

| Phase | Description | Key Files |
|-------|-------------|-----------|
| **0 – Pre‑registration** | Generate `pre-registration.json` containing analysis plan hash, timestamp, and parameters (R² target, power, α, **predictor count**). | `code/reports/preregister.py` |
| **1 – Power Analysis (Gate)** | Compute minimum sample size required to detect **R² = 0.1** with **80 % power**, **α = 0.05**, assuming **21 predictors** (15 spectral power features from motor‑cortex channels × 5 bands + Multiple connectivity metrics from C3‑C4, C3‑Cz, C4‑Cz). If `N_actual < N_min`, set mode flag to **Underpowered**, skip inference, and record `min_n_required`. | `code/modeling/power_analysis.py` |
| **2 – Source Verification** | Search OpenNeuro, PhysioNet, Kaggle with query “EEG AND tDCS AND motor”. Produce `verified_source_manifest.json`. If a paired dataset is found → **Primary Mode**; else → **Data Insufficient Mode**. | `code/ingestion/verify_source.py` |
| **3 – Data Alignment Check** | Confirm subject IDs overlap between EEG and tDCS within the single source (FR‑011). If mismatch → switch to **Data Insufficient Mode**. | `code/ingestion/manifest.py` |
| **4 – Preprocessing** *(Primary Mode only)* | Band‑pass filter 1–45 Hz, common‑average reference, automated bad‑channel rejection (z‑score threshold). Output epochs in `data/processed/`. | `code/preprocessing/filter.py`, `code/preprocessing/epoch.py` |
| **5 – Feature Extraction** *(Primary Mode only)* | Compute spectral power (Welch) for delta–gamma bands per channel and connectivity (PLV, wPLI) for C3‑C4, C3‑Cz, C4‑Cz. Save feature matrix `data/processed/features.csv`. | `code/features/spectral.py`, `code/features/connectivity.py` |
| **6 – Dimensionality Reduction & Feature Selection** *(Primary Mode only, Mandatory Gate)* | **Decision Rule**: <br>• If `N ≥ 30` → apply **PCA** retaining enough components to explain ≥ [deferred] % variance **and** enforce `p_reduced ≤ 0.5 × N`. <br>• If `N < 30` → apply **LASSO** (L1) to enforce sparsity while also respecting `p_reduced ≤ 0.5 × N`. <br>If the constraint cannot be satisfied, the pipeline flags **Underpowered** and halts modeling (additional safety gate). This step is critical to prevent the 'p >> n' problem and ensure model stability. | `code/modeling/feature_selection.py` |
| **7 – Normality Check** *(Primary Mode only)* | Shapiro‑Wilk on tDCS response (FR‑009). If non‑normal (p < 0.05) → switch to **Rank‑Ridge** regression. | `code/modeling/normality.py` |
| **8 – Modeling** *(Primary Mode only, provided power sufficient)* | Nested CV: outer k‑fold, inner k‑fold for ridge α. Use **Ridge** if normal, **Rank‑Ridge** otherwise. Input is the **reduced feature set** from Phase 6. Output coefficients, adjusted R². | `code/modeling/ridge.py` |
| **9 – Validation** *(Primary Mode only, conditional on N)* | • **Permutation Testing**: 1000 permutations **only if N ≥ 30**; otherwise skip and log “Permutation testing skipped (N < 30): Insufficient permutations for reliable p-value estimation” (addresses scientific_soundness‑9e79653c). <br>• **Kolmogorov‑Smirnov** test on permutation p‑values (FR‑019) – performed only when permutation testing runs. <br>• **FDR (Benjamini‑Hochberg)** on feature p‑values (FR‑014). <br>• **Sensitivity Analysis**: sweep p‑thresholds {0.01, 0.05, 0.1} and R² thresholds (configurable). **Note**: This is an 'Internal Consistency Check' (variance of significance across thresholds), not a validation of predictive power. True predictive power requires the independent dataset (Phase 10). Record stability variance. | `code/modeling/validation.py` |
| **10 – Independent Dataset Check** *(Primary Mode only)* | Attempt to load a second public dataset with paired EEG + tDCS (e.g., Kaggle EEG Motor Imagery). <br>• **If found**: Repeat phases 4‑9 on that dataset and report comparative metrics (FR‑020, Principle VII). <br>• **If not found**: Log “Skipped: No independent dataset found” (satisfying Principle VII) and **continue** with primary results. The final report will clearly flag the missing generalization check as "Generalizability: Unverified" rather than halting the entire analysis. | `code/modeling/independent_check.py` |
| **11 – Reporting** | Assemble `results.json` (or `output.json`), `pre-registration.json`, `verified_source_manifest.json`, and logs. | `code/reports/assemble.py` |

## Constitution Check

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed random seeds, `requirements.txt`, checksum‑verified data, end‑to‑end CI run. |
| **II. Verified Accuracy** | Citations limited to verified dataset URLs; no invented sources. |
| **III. Data Hygiene** | Raw data immutable, checksums stored, derived files in separate directories. Runtime validation via `jsonschema`. |
| **IV. Single Source of Truth** | Every statistic traced to a single row in `data/processed/` and corresponding code module. |
| **V. Versioning Discipline** | Content hashes for all artifacts, timestamps managed by CI. |
| **VI. Neurophysiological Data Integrity** | MNE pipeline (1–45 Hz, CAR, automated bad‑channel rejection). |
| **VII. Biomarker Validation** | Independent dataset step (Phase 10) with explicit skip logging and "Unverified" flag if unavailable. |

## Project Structure

```text
specs/001-neural-oscillations-tDCS-biomarker/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── eeg-features.schema.yaml
    ├── feature.schema.yaml
    ├── model_output.schema.yaml
    ├── output.schema.yaml
    └── tdc-response.schema.yaml
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Dual‑Mode Logic (Theoretical)** | Spec requires a fallback when no paired data exists (US‑1, FR‑001). The logic is retained as a contingency but is not exercised in the current run. | A single linear pipeline would either crash on missing data or produce invalid results. |
| **Rank‑Ridge Fallback** | Non‑normal response distributions invalidate ordinary least‑squares (FR‑009). | Standard Ridge assumes normality; without transformation p‑values become unreliable. |
| **Power‑Analysis Gate** | Guarantees sufficient sample size before inference (FR‑007, FR‑008). | Proceeding with underpowered data yields false negatives and violates scientific rigor. |
| **Feature‑Selection Decision Rule** | Prevents p ≫ n problems given high‑dimensional EEG features (Methodology‑01e580f5). | Ignoring dimensionality would lead to over‑fitting despite regularization. |
| **Permutation‑Testing Conditionality** | Small N makes permutation‑based p‑values unstable; skipping when N < 30 preserves statistical validity (scientific_soundness‑9e79653c). | Running permutation tests with insufficient permutations would produce misleading significance. |
| **Sensitivity Analysis Reframing** | Addresses the tautology concern (scientific_soundness‑2b7bb1bd) by labeling it as internal consistency, not predictive validation. | A sensitivity sweep on the same data cannot prove external validity. |

## Testing Strategy

- **Unit Tests** for each module (ingestion, preprocessing, feature extraction, modeling).  
- **Integration Tests** for full pipeline in both **Primary** and **Data Insufficient** modes (including underpowered gate).  
- **Contract Validation** using `jsonschema` against all `contracts/*.schema.yaml` to enforce data integrity (Constitution Principle III).  
- **Runtime Checks** ensuring ≤ 7 GB RAM and ≤ 6 h total runtime on GitHub Actions free tier.

## Runtime Feasibility

All steps are bounded to ≤ 7 GB RAM by batch processing (epoch loading in chunks, PCA on scaled matrices) and ≤ 6 h total runtime on the GitHub Actions free tier. No GPU or CUDA dependencies.