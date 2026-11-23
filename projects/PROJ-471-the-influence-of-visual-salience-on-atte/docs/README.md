# Documentation Index

This directory contains project governance documents, Spec Change Requests (SCRs), and technical guides.

## Spec Change Requests (SCRs)

SCRs are formal documents that modify the project scope to address infeasibilities or contradictions.

- **SCR-001: Weapons Exclusion** (`scr_001_weapons_exclusion.md`)
 - **Reason:** Lack of "Weapons" class in COCO dataset used by YOLOv8.
 - **Impact:** Study scope reduced to "Face" vs "Background" ROIs only.
 - **Status:** Applied (FR-008 removed from `spec.md` and `plan.md`).

- **SCR-002: Low-Level Covariates Exclusion** (`scr_002_lowlevel_covariates_exclusion.md`)
 - **Reason:** High multicollinearity between DeepGaze II features and manual low-level features (luminance, contrast).
 - **Impact:** FR-009 removed; VIF checks performed instead of explicit covariate modeling.
 - **Status:** Applied (FR-009 removed from `spec.md`).

## Technical Guides

- **Salience Generation:** CPU-only DeepGaze II implementation with GBVS fallback.
- **Power Analysis:** Simulation-based power estimation using `simr` (medium effect size d=0.5).
- **Data Integrity:** "Fail loudly" policy for data fetching; no synthetic fallbacks.

## Pipeline Execution Flow

1. **Setup:** Initialize environment and validate dependencies.
2. **Ingestion:** Fetch real data from OpenNeuro/Hugging Face.
3. **Salience:** Generate maps (DeepGaze II -> GBVS fallback -> Exclude).
4. **Processing:** Segment faces (YOLOv8) and parse eye-tracking.
5. **Alignment:** Merge datasets on `TrialID`.
6. **Analysis:** Power gate -> VIF check -> LMM Fit -> Sensitivity Analysis.

## Versioning

Artifacts are versioned using SHA-256 hashes recorded in `state.yaml`.
See `code/utils/versioning.py` for implementation details.
