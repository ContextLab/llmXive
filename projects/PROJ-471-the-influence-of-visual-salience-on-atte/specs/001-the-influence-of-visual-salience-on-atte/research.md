# Research: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## 1. Research Question & Hypothesis

**Primary Question**: Does computational visual salience (derived from low-level image features) predict the allocation of visual attention (fixation duration/probability) to morally relevant regions (faces, weapons) in moral judgment scenarios?

**Hypothesis**: Higher visual salience in morally relevant regions (faces, weapons) will be positively associated with increased dwell time and first-fixation probability on those regions. **Note**: Low-level visual features (luminance, contrast) are computed for VIF diagnostics only and are NOT included as covariates in the final model to avoid multicollinearity (SCR-001). The study does not claim to "control for" these features in the final model, as they are conceptually redundant with the salience predictor.

**Null Hypothesis**: Visual salience does not significantly predict attentional allocation to morally relevant regions; attention is driven primarily by top-down moral reasoning or other unmeasured factors.

## 2. Dataset Strategy

The study relies on the **OpenNeuro "Moral Foundations Eye-Tracking Dataset" (ds003123)**.

### Verified Datasets
*Note: Only URLs from the provided verified list are used. If a dataset is not in the list, it is not used.*

| Dataset Name | Purpose | Verified Source URL | Access Method |
|:--- |:--- |:--- |:--- |
| **OpenNeuro (ds003123)** | Raw eye-tracking data & stimulus images | *Not in verified list* | **CRITICAL**: The spec assumes `ds003123` exists. The provided verified list contains `clane9/openneuro-fslr64k` (fMRI data) and `qiuweihao/laion_4_to_3_deepgaze` (salience training). **The specific "Moral Foundations Eye-Tracking Dataset" (ds003123) is NOT in the verified list.** |
| **DeepGaze II Training Data** | Model weights/pre-training (if needed) | ` | `datasets.load_dataset` |
| **YOLOv8 Table Detection** | Model weights (Face detection) | ` | Metadata only |
| **Detectron2 Data** | Model weights (Weapon detection) | ` | Model weights |

**Critical Feasibility Gap**: The spec requires `ds003123` (Moral Foundations Eye-Tracking). This dataset is **not** in the provided "Verified datasets" block.
* **Action**: The plan treats `ds003123` as a **Manual Prerequisite**. The pipeline explicitly checks for the presence of `data/raw/ds003123`. If missing, the pipeline halts with error code `DATA_MISSING_001`. This ensures the 'fresh runner' requirement is met by failing fast rather than running incomplete.
* **Fallback**: If `ds003123` is inaccessible, the study is deemed "Invalid for inference" and the pipeline halts. No open substitute exists for this specific eye-tracking/moral judgment combination.

**Variable Fit Verification**:
* **Predictor**: Image properties (Salience). *Source*: Computed from images in `ds003123`.
* **Outcome**: Eye-tracking fixation (Dwell time, First fixation). *Source*: `ds003123` (sub-01/func/sub-01_task-moral_eys.trc or similar).
* **Covariates**: Low-level features (Luminance, Contrast). *Source*: Computed from images (Diagnostic Only).
* **Region Masks**: Faces, Weapons. *Source*: Generated via YOLOv8/Detectron2 on images in `ds003123`.

## 3. Methodological Rigor

### Statistical Analysis Plan
1. **Model**: Linear Mixed-Effects Model (LMM) or Gamma GLMM.
 * **Fixed Effects**: Salience, Region Type.
 * **Random Effects**: Random intercepts for `ParticipantID` and `StimulusID`.
 * **Formula**: `DwellTime ~ Salience + (1 | ParticipantID) + (1 | StimulusID)`
 * **Distributional Check (T031)**: If residuals are non-normal, switch to Gamma GLMM or log-transform `DwellTime`.
2. **Multiple Comparisons**: False Discovery Rate (FDR) correction (Benjamini-Hochberg) applied to all p-values (FR-006).
3. **Power Analysis (T029c)**: A priori power calculation is performed **before** data ingestion is finalized. Using G*Power parameters (effect size f=0.15, alpha=0.05, power=0.80) based on literature meta-analyses. If the calculated required N exceeds the available dataset size, the pipeline halts with 'Invalid for inference'.
4. **Sensitivity Analysis**: Compare Model A (random intercepts only) vs. Model B (random intercepts + slopes for salience). Report change in effect size and significance (FR-005).
5. **Collinearity**: Variance Inflation Factor (VIF) calculated for all predictors. If VIF > 5, the predictor is flagged. **Low-level features (FR-009) are excluded from the final model to avoid multicollinearity**, but calculated for diagnostics (T030b).

### Robustness & Diagnostics
* **Missing Data**: Trials with missing fixation data are excluded. Excluded IDs logged to `data/interim/excluded_trials.csv`.
* **Model Convergence**: If LMM fails to converge, the model is refitted with simplified random effects. If still failing, the trial is excluded.
* **Salience Fallback**: If DeepGaze II fails on an image, GBVS is run. If GBVS succeeds, the image is marked "Fallback Used" and **excluded from the primary success count (SC-001)** but retained for exploratory analysis.
* **Mask Validation (T020e)**: If YOLOv8/Detectron2 confidence < 0.85, the image is flagged for manual review and excluded from the primary analysis (SC-001).

## 4. Compute Feasibility

* **Environment**: GitHub Actions Free Tier (standard CPU allocation, adequate RAM).
* **Salience Generation**: DeepGaze II is heavy. Strategy:
 * Load model in `float32` (no 8-bit quantization for accuracy).
 * Process images in batches.
 * Use `torch.no_grad()` and stream results to disk immediately to free RAM.
 * **Timeout**: If a batch exceeds a predefined duration threshold, the job is killed.
* **GPU Escape Hatch**: **NOT APPLICABLE**. The plan strictly adheres to CPU-only execution to satisfy Constitution Principle I. No GPU offload mechanism is implemented.

## 5. Decision Rationale

* **Why DeepGaze II?**: State-of-the-art for computational salience; aligns with spec.
* **Why exclude FR-009 covariates from model?**: Salience maps are *derived* from low-level features (luminance, contrast) via a non-linear process. Including both causes high multicollinearity (VIF > 5), inflating variance and invalidating inference. We calculate VIF to prove this, then exclude them from the LMM to preserve statistical validity (SCR-001).
* **Why no GPU offload?**: Constitution Principle I requires reproducibility on a "fresh GitHub Actions runner" (CPU). Introducing GPU offload creates a heterogeneous environment that breaks this principle.
* **Why GLMM fallback?**: Dwell time is typically heavy-tailed. A standard Gaussian LMM violates normality assumptions. T031 checks residuals and switches to Gamma GLMM if needed.
* **Why Manual Dataset?**: The specific dataset is not in the verified list. The plan treats it as a manual prerequisite to ensure reproducibility by failing fast if the data is missing.
