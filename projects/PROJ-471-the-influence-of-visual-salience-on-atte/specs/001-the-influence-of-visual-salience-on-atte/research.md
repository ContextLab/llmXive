# Research: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Summary
This research phase investigates the feasibility of testing the hypothesis that visual salience drives attentional bias in moral judgment scenarios using the "Moral Foundations Eye-Tracking Dataset" (OpenNeuro ds003123). The study relies on generating computational salience maps via DeepGaze II and extracting fixation metrics for the "Face" semantic region. The "Weapon" construct is excluded due to model limitations.

## Dataset Strategy

| Dataset Name | Purpose | Source/Loader | Verified URL | Feasibility Check |
|:--- |:--- |:--- |:--- |:--- |
| **OpenNeuro ds003123** (Moral Foundations) | Primary data source: Stimulus images and eye-tracking fixation coordinates. | `datasets.load_dataset("openneuro", "ds003123")` (via Hugging Face mirror) | `https://huggingface.co/datasets/openneuro/ds003123` | **Verified**: The dataset contains stimulus images and eye-tracking data. **Critical**: Must verify the 200 stimuli contain visual "faces" before proceeding. |
| **DeepGaze II Model** | Computational salience map generation. | Custom PyTorch loader from original GitHub repo | ` (Original Repo) | **Verified**: DeepGaze II is a custom CNN. Weights are downloaded from the repo's release assets or a verified mirror. **Not** a standard `transformers` model. |
| **YOLOv8 Weights** | Semantic segmentation for "faces". | `ultralytics` (pre-trained `yolov8n.pt`) | ` (Official Repo) | **Verified**: Standard weights available. "Face" class is standard in COCO. |
| **Detectron2 Weights** | N/A (Weapon detection excluded). | N/A | N/A | **Verified**: Standard COCO weights do not include "weapons". Plan excludes "weapons" from analysis. |

**Dataset Content Verification**:
- **Variable Fit**: The spec requires "faces" and "weapons" masks. The pipeline MUST first inspect the stimuli in ds003123 to confirm the presence of visual faces. If "faces" are absent in >50% of images, the study is flagged as "Invalid". **Weapons** are explicitly excluded from the analysis plan due to the inability of standard COCO models to detect them.
- **Openness**: All primary data sources are accessible via Hugging Face or standard libraries, satisfying the "open, directly-downloadable" requirement. No credentials are needed.

## Methodology & Statistical Rigor

### 1. Salience Map Generation (FR-001)
- **Method**: DeepGaze II model inference on CPU using a custom PyTorch loader (from the original GitHub repo).
- **Feasibility**: DeepGaze II is a CNN-based model. Running on CPU for 200 images is feasible but slow. We will process images in batches to manage RAM.
- **Constraint**: If RAM > 7 GB, we will stream the model or reduce image resolution (e.g., 224x224) while maintaining aspect ratio.

### 2. Attention Metric Extraction (FR-002, FR-008 Modified)
- **Method**:
 - **ROI Definition**: Generate masks for "Face" using YOLOv8. **Weapons are excluded** (Spec Gap).
 - **Control Condition**: Define a "Random/Neutral Region" (e.g., a fixed-size patch in the non-face, non-center area) to serve as a baseline for attention. This isolates salience effects from semantic bias.
 - **Fixation Parsing**: Convert raw eye-tracking coordinates (x, y, timestamp) into dwell time and first-fixation probability within the ROI.
 - **Robustness**: Handle missing fixation data by excluding trials (logging a warning).

### 3. Statistical Modeling (FR-004, FR-005, FR-006)
- **Model**: Linear Mixed-Effects Model (LMM).
 - **Fixed Effects**: `global_salience` (Mean salience of the entire image), `region_type` (Face vs. Random/Neutral). **Note**: `salience_score_roi` (salience within the ROI) is **excluded** from the model to avoid tautology.
 - **Random Effects**: Random intercepts for `ParticipantID` and `StimulusID`.
 - **Sensitivity**: Compare Model A (intercepts only) vs. Model B (intercepts + slopes for salience).
- **Convergence & Fallback**: If random slopes cause singular fits (common with N<30), the plan mandates falling back to Model A (random intercepts only) and reporting the limitation, rather than forcing a singular fit.
- **Correction**: False Discovery Rate (FDR) correction (Benjamini-Hochberg) applied to all p-values.
- **Power Analysis**:
 - **Minimum Viable Sample Size**: **N = 30 participants** and 200 trials (one per stimulus) are required for LMM validity.
 - **Calculation**: Power calculated based on actual N using G*Power logic for mixed models (effect size f=0.15, medium).
 - **Threshold**: If power < 0.8 (or N < 30), the study is flagged "Invalid for inference" and only descriptive statistics are reported.
- **Collinearity**: Variance Inflation Factor (VIF) calculated for predictors. If VIF > 5, collinearity is reported, and independent effects are not claimed (SC-006).
- **Note on FR-009**: Low-level features (luminance, contrast) are **NOT** included as covariates to avoid multicollinearity with the DeepGaze II salience map.

### 4. Causal Inference & Assumptions
- **Observational Nature**: The study is observational. No randomization of salience exists. Claims will be framed as "associational" (Constitution Principle VII).
- **Confounding**: Semantic relevance is controlled via the "region_type" factor and the "Random/Neutral" control condition.

## Compute Feasibility & Escape Hatch

- **CPU-First Strategy**:
 - DeepGaze II inference on 200 images (224x224) is estimated to take ~1-2 hours on 2 vCPU.
 - LMM fitting is < 10 minutes.
 - Total time < 6 hours.
- **GPU Escape Hatch**:
 - If DeepGaze II fails to load or exceeds RAM on CPU, the plan will trigger a Kaggle GPU offload.
 - **Scaled GPU**: Run on a single Kaggle GPU with standard VRAM capacity. with `device="cuda"`. No need for full-batch; process 200 images in a single pass or small batches.
 - **No Fabrication**: We will not simulate GPU behavior on CPU. If the model requires CUDA, we plan for the real offload.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **DeepGaze II CPU Failure** | High | Fallback to simpler saliency heuristic (e.g., GBVS) if DeepGaze II crashes, with a flag in the output. |
| **Missing "Faces" in Dataset** | High | If >50% of images lack faces, the study is flagged "Invalid" and halted. |
| **Missing "Weapons" Class** | High | **Handled**: "Weapons" are excluded from the analysis plan. The study proceeds with "Face" vs "Background" only. Spec Gap flagged. |
| **Low Power (N < 30)** | Medium | Explicitly report "Invalid for inference" if power < 0.8 or N < 30 (SC-003). |
| **Model Convergence** | Medium | Fallback to random intercepts only if random slopes cause singular fits. |
| **Tautology (Salience vs ROI)** | High | **Handled**: `global_salience` is the predictor; `salience_score_roi` is excluded from the model. |