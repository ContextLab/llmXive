# Research: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## Overview

This research phase defines the data sources, acquisition strategy, and statistical methodology for investigating the relationship between visual complexity and cognitive load. The study utilizes **real human data** collected via a pilot study for the outcome variables (NASA-TLX, reaction time), while using **real image stimuli** for the predictor variable (visual complexity).

## Dataset Strategy

### 1. Visual Stimuli (Predictor Variable)
*   **Source**: No verified public dataset of "meeting backgrounds with ground-truth complexity" was found in the verified datasets list.
*   **Strategy**: The project will utilize a curated set of diverse background images (e.g., plain, cluttered, nature, abstract) stored in `data/stimuli/`.
    *   **Acquisition**: These will be sourced from open-license image repositories (e.g., Unsplash, Pexels) via a script, ensuring no PII is present.
    *   **Processing**: Each image will be processed by the `extract_metrics.py` script to generate:
        *   **Image Entropy**: Shannon entropy of the grayscale image.
        *   **Color Variance**: Variance of the HSV saturation channel.
        *   **Object Count**: Number of detected objects using YOLOv8n (CPU mode).
*   **Validation**: Per SC-001, a pilot study (n=20) will be conducted to collect **human-rated complexity scores**. The automated metrics will be validated against these real human ratings to ensure construct validity, avoiding circular logic.

### 2. Participant Data (Outcome Variables)
*   **Source**: No verified public dataset of human NASA-TLX scores linked to specific video backgrounds exists in the verified list.
*   **Strategy**: **Real data collection via Pilot Study**.
    *   **Mechanism**: Recruit N=20 participants via a web-based survey platform (e.g., Prolific, Qualtrics) or local recruitment.
    *   **Procedure**:
        *   Participants view a subset of the stimuli in a counterbalanced order (Latin Square design).
        *   After each clip, participants complete the **NASA-TLX** questionnaire.
        *   Participants complete a **reaction-time task** (e.g., N-back or simple detection) post-clip.
    *   **Data Integrity**: Data is collected in raw form, timestamped, and stored in `data/measurements/`. No synthetic generation is used for the primary outcome variables.
    *   **Baseline Measurement**: Per SC-003, each participant will complete a baseline condition (low-complexity stimulus) to establish a reference reaction time.

## Methodology & Statistical Plan

### 1. Metric Extraction (FR-001)
*   **Algorithm**:
    *   Entropy: `scipy.stats.entropy` on flattened grayscale histogram.
    *   Variance: `numpy.var` on HSV saturation channel.
    *   Objects: `ultralytics.YOLO('yolov8n.pt')` running on CPU.
*   **Handling Edge Cases**:
    *   Zero object count: Handled gracefully (returns 0).
    *   Skewed distribution: Log-transformation applied if Shapiro-Wilk test indicates non-normality (sensitivity check).

### 2. Experimental Design (FR-002)
*   **Counterbalancing**: A Latin Square design is used to assign stimuli to participants, ensuring order effects are controlled.
*   **Baseline Condition**: Each participant completes a baseline trial with a low-complexity stimulus. Reaction times are calculated as the difference from this baseline (SC-003).
*   **Missing Data**: Records with missing values are flagged and excluded from the final model (as per SC-003), not imputed.

### 3. Statistical Analysis (FR-003, FR-004, FR-005)
*   **Model**: Linear Mixed-Effects Model (LMM) using `statsmodels`.
    *   **Fixed Effects**: Visual Complexity (Entropy), Task Difficulty (self-reported), Stimulus ID.
    *   **Random Effects**: Participant ID (intercept).
    *   **Equation**: $TLX_{ij} = \beta_0 + \beta_1(Complexity_{ij}) + \beta_2(Difficulty_{ij}) + u_i + \epsilon_{ij}$
*   **Collinearity Check**: Variance Inflation Factor (VIF) calculated for predictors. If VIF > 5, PCA is applied to combine predictors (SC-003).
*   **Multiple Comparison Correction**: Benjamini-Hochberg procedure applied to p-values of fixed effects (FR-004).
*   **Sensitivity Analysis**: The significance threshold ($\alpha$) is swept over {0.01, 0.05, 0.1} to test the stability of the effect (FR-005, SC-005).
*   **FWER Calculation**: Per SC-004, the observed Family-Wise Error Rate will be estimated via permutation testing (shuffling labels) to verify it against the nominal alpha level.
*   **Power Consideration**: The sample size (N=20) is a pilot study. A power analysis will be conducted post-hoc to inform future full-scale studies.

## Dataset Variable Fit & Risks

*   **Risk**: Small sample size (N=20) may limit statistical power.
    *   **Mitigation**: The study is explicitly framed as a pilot. Results are preliminary.
*   **Risk**: YOLOv8n on CPU may be slow.
    *   **Mitigation**: The plan limits the stimulus set to 50 images. Inference is batched. If runtime exceeds limits, image resolution is downsampled to 640x640 (standard for YOLO) before inference.

## References

*   **NASA-TLX**: Hart, S. G., & Staveland, L. E. (1988). Development of NASA-TLX (Task Load Index). *Human Mental Workload*. (Standard reference for the metric).
*   **YOLOv8**: Ultralytics. (2023). YOLOv8 Documentation. (Standard reference for object detection).
*   **Statistical Methods**: Bates, D., et al. (2015). Fitting Linear Mixed-Effects Models Using lme4. *Journal of Statistical Software*.
