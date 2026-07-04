# Research: The Impact of Visual Crowding on Facial Emotion Recognition Accuracy

## Overview

This research document details the datasets, methods, and statistical strategies required to implement the feature specification. It addresses the core research question: *To what extent does increasing visual crowding density degrade the perceptual accuracy of facial emotion recognition, and does this degradation vary across specific emotion categories?*

## Dataset Strategy

### Verified Datasets

| Dataset Name | Verified URL | Usage | Notes |
|--------------|--------------|-------|-------|
| RAVDESS (Speech/Audio-Visual) | https://huggingface.co/datasets/viks66/ravdess_speech/resolve/main/ravdess.zip | Stimulus Source | Contains multiple emotion categories (neutral, happiness, sadness, anger, fear, disgust, surprise, contempt) with actor metadata. **Note**: This dataset contains video files. The pipeline will extract frames to generate multiple unique flanker instances per actor/emotion, addressing the limitation of single static images. |

**Dataset Fit Verification**:
- **Required Variables**: Target face image, emotion label (8 categories), actor ID, gender, age.
- **RAVDESS Availability**: The RAVDESS dataset explicitly contains all 8 required emotion categories.
- **Missing Variable Check**: The dataset does *not* contain pre-computed crowding metrics or human judgment data. These are generated/computed by the pipeline (US-1, US-2) and collected via the experimental interface (US-4).
- **Image Limitation Mitigation**: RAVDESS provides video files, not static images. The pipeline (`code/utils/frame_extractor.py`) will extract distinct frames from the video streams to ensure sufficient unique face instances for the crowding manipulation without repetition, satisfying the need for diverse flankers.
- **Conclusion**: The dataset is a perfect fit for the *stimulus generation* phase once frame extraction is implemented.

### Data Processing Strategy

1.  **Download & Cache**: `code/utils/download.py` will fetch the RAVDESS zip from the verified URL. Checksums will be computed and stored in `state/`.
2.  **Frame Extraction**: `code/utils/frame_extractor.py` will extract 3-5 distinct frames per video file per actor/emotion to create a pool of unique flankers.
3.  **Stimulus Generation**: `code/utils/stimulus_gen.py` will create crowding stimuli by placing flanker images at specified eccentricities (2°, 4°, 6°) and counts (1, 3, 5).
    - **Edge Case Handling**: Overlap detection will be implemented; overlapping stimuli will be excluded and logged.
4.  **Clutter Metrics**: `code/utils/clutter_metrics.py` will compute local contrast variance and spatial frequency energy for the flanker region of each stimulus.
5.  **Human Data Collection**: A **Pilot Study** (n≥5 participants) will be conducted first to validate the GLMM random effects structure and convergence behavior. If the pilot validates the model, the full study (target n=30-50) will proceed. A synthetic data generator is retained *only* for unit testing the code logic, not for scientific validation.

## Statistical Methodology

### Model Specification

- **Model Type**: Generalized Linear Mixed Model (GLMM) with binomial link function.
- **Outcome Variable**: Recognition Accuracy (Binary: Correct/Incorrect).
- **Fixed Effects**:
    - **Primary**: `ClutterMetric` (Continuous: Spatial Frequency Energy).
    - **Categorical**: `EmotionCategory` (8 levels).
    - **Interaction**: `ClutterMetric * EmotionCategory`.
    - **Note on FlankerCount**: `FlankerCount` is the experimental manipulation that *determines* `ClutterMetric`. To avoid severe multicollinearity (circularity), `FlankerCount` will **NOT** be entered as a simultaneous fixed effect with the continuous metric in the primary model. It will be used descriptively or in a secondary model to confirm the discrete manipulation effect.
- **Random Effects**:
    - `(1 | ParticipantID)`: To account for individual differences in baseline accuracy.
    - `(1 | StimulusID)`: To account for stimulus-specific variability.

### Statistical Rigor & Assumptions

1.  **Multiple Comparison Correction**:
    - **Requirement**: FR-005 mandates correction for >1 hypothesis test.
    - **Method**: Benjamini-Hochberg False Discovery Rate (FDR) correction at α ≤ 0.05 will be applied to p-values of interaction terms and main effects.
    - **Implementation**: `statsmodels.stats.multitest.multipletests` with method `'fdr_bh'`.

2.  **Sample Size & Power**:
    - **Target**: Power ≥ 0.8 to detect a medium-to-large interaction effect (f² ≥ 0.15) at α ≤ 0.05.
    - **Justification**: Based on prior visual crowding literature (e.g., Pelli & Tillman,; similar effect sizes in facial emotion studies), a medium effect size is a conservative estimate for the interaction between clutter and emotion.
    - **Calculation**: Using G*Power guidelines for mixed models, targeting an interaction effect requires approximately **30-50 participants** with **~100 trials per participant** (balanced across conditions) to achieve sufficient power. The pilot (n=5) will be used to refine this estimate.
    - **Limitation**: If the final sample is insufficient, the report will explicitly state the limitation and interpret results as exploratory.

3.  **Causal Inference & Framing**:
    - **Design**: Experimental (manipulated variables: flanker count, eccentricity).
    - **Framing**:
        - For the **discrete manipulation** (Flanker Count): Findings can support causal claims about the effect of the *manipulation* on accuracy (e.g., "Increasing flanker count *causes* a reduction in accuracy").
        - For the **continuous metric** (Clutter Metric): Findings will be framed as **associational** (e.g., "Higher spatial frequency energy is *associated* with lower accuracy") to avoid over-generalizing the mechanism beyond the specific experimental conditions. This distinction ensures scientific rigor while acknowledging the experimental design.

4.  **Measurement Validity**:
    - **Instruments**: Visual clutter metrics (local contrast variance, spatial frequency energy) are cited in vision literature as valid proxies for crowding intensity.
    - **Action**: The `research.md` and final report will cite relevant vision science literature supporting these metrics.

5.  **Predictor Collinearity**:
    - **Risk**: `FlankerCount` and `ClutterMetric` are definitionally related. `Local Contrast Variance` and `Spatial Frequency Energy` are also highly correlated.
    - **Mitigation**:
        - **Primary Strategy**: The primary GLMM will use only the **continuous `ClutterMetric`** (Spatial Frequency Energy) as the predictor. `FlankerCount` will be excluded from this specific model to avoid collinearity.
        - **Secondary Strategy**: If both clutter metrics are tested, Variance Inflation Factors (VIF) will be computed. If VIF > 5, the metric with the lower theoretical relevance will be dropped.
        - **Reporting**: If collinearity is detected, independent effects will not be claimed; instead, the relationship will be reported descriptively.

### Convergence & Fallback Strategy

- **Primary**: Fit GLMM using `statsmodels` or `pymer4` (Python wrapper for lme4).
- **Pilot Validation**: Before the full study, a pilot (n=5) will be run to verify that the random effects structure converges. If the pilot fails to converge, the random effects will be simplified (e.g., removing `(1 | StimulusID)`).
- **Fallback**: If convergence fails in the full study, the pipeline will:
    1. Log the diagnostic warning.
    2. Simplify the model to Fixed Effects only.
    3. Report the fallback status in the final output.
- **Constraint**: This fallback ensures the pipeline completes even if the mixed model fails, satisfying SC-003.

## Human Data Collection Protocol

- **Viewing Distance**: Participants will be instructed to maintain a fixed viewing distance of **60 cm** from the screen.
- **Screen Calibration**: The stimulus generation script will calculate pixel positions based on a standard screen resolution (e.g., 1920x1080) and the fixed distance to ensure 2°, 4°, 6° eccentricity is physically accurate.
- **Procedure**: A simple web-based or local app interface will present stimuli for a brief duration, followed by an 8-alternative forced choice (8AFC) response.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (limited CPU, limited RAM, no GPU).
- **Strategy**:
    - **Data Sampling**: If the RAVDESS dataset + generated stimuli exceed memory, the pipeline will process in chunks or sample a representative subset for the GLMM fitting.
    - **Library Selection**: Use `statsmodels` (CPU-optimized) instead of heavy deep learning libraries. `opencv-python-headless` for image processing. `pyav` for video frame extraction.
    - **Runtime**: The pipeline is designed to complete within 6 hours. Stimulus generation is parallelizable; GLMM fitting on a large-scale dataset is CPU-tractable.

## References

- **RAVDESS**: Livingstone & Wong (2018). "The Ryerson Audio-Visual Database of Emotional Speech and Song." *Scientific Data*. (Verified via HuggingFace).
- **Crowding Theory**: Pelli & Tillman (2008). "The uncrowded window of object recognition." *Nature Neuroscience*.
- **GLMM Methods**: Bates et al. (2015). "Fitting Linear Mixed-Effects Models Using lme4." *Journal of Statistical Software*.
- **Power Analysis**: Cohen (1988). *Statistical Power Analysis for the Behavioral Sciences*.