# Research: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

## Summary

This research phase validates the feasibility of the proposed study, identifies available data sources, and outlines the statistical methodology. The core hypothesis is that trait anxiety modulates the relationship between gaze fixation duration on threat stimuli and subsequent recall accuracy in a Rapid Serial Visual Presentation (RSVP) task.

## Dataset Strategy

**Critical Feasibility Note**: The provided "Verified datasets" block indicates **NO verified source** for the RSVP dataset (OpenNeuro ds001435) or the IAPS/NimStim stimulus database. The STAI links provided are unrelated (image captions). **This is a fatal feasibility gap.**

The plan assumes the implementation will attempt to locate a verified substitute or halt if none is found. The methodology is designed to work with *any* open RSVP dataset that contains:
1.  Raw eye-tracking data (x, y coordinates, timestamps).
2.  Stimulus metadata (ID, valence/threat label).
3.  Behavioral recall data (binary accuracy).
4.  Trait anxiety scores (STAI or equivalent).

**Verified Sources Attempted**:
-   **RSVP Data**: No verified URL found. The plan will attempt to download from `openneuro.org` via `wget` if a direct link is discovered, but currently, this is a blocker.
-   **Stimulus Mapping**: No verified URL for IAPS. The plan will rely on metadata embedded in the dataset or a local lookup table if provided by the dataset author.
-   **STAI Data**: No verified source for the specific study's STAI scores.

**Decision**: If no verified source containing all four variables is found, the pipeline will fail at the download stage with a clear error message: "ERROR: No verified dataset found containing required variables (Eye-tracking, Valence, Recall, STAI)."

**Alternative Strategy**: If a verified dataset is found that matches the *design* (RSVP + Eye-tracking + Recall) but lacks STAI, the study must be reframed to exclude the anxiety modulation hypothesis. However, per the spec, the anxiety component is core. Therefore, the study is currently **blocked** pending a verified data source.

**Table of Data Sources**:

| Variable | Source | Status | Verified URL |
|----------|--------|--------|--------------|
| Eye-tracking (Raw) | OpenNeuro ds001435 (Target) | **NO VERIFIED SOURCE** | N/A |
| Stimulus Valence | IAPS/NimStim (Target) | **NO VERIFIED SOURCE** | N/A |
| Recall Accuracy | OpenNeuro ds001435 (Target) | **NO VERIFIED SOURCE** | N/A |
| Trait Anxiety (STAI) | OpenNeuro ds001435 (Target) | **NO VERIFIED SOURCE** | N/A |

*Note: The implementation will strictly adhere to the "Verified datasets" block. If a dataset is not in that block, it will not be used.*

## Statistical Methodology

**Model**: Mixed-Effects Logistic Regression (GLMM).
**Formula**: `recall_accuracy ~ fixation_duration * valence * trait_anxiety + (1 | participant_id) + (1 | stimulus_id)`
**Link Function**: Logit.
**Optimizer**: `bobyqa` (robust for GLMMs).
**Convergence Tolerance**: 1e-6.

**Hypothesis Testing**:
1.  **Main Effect**: Does fixation duration predict recall?
2.  **Interaction**: Does the effect of fixation duration on recall differ by valence?
3.  **Three-Way Interaction**: *Does trait anxiety modulate the relationship between fixation duration and recall probability?* (Primary Question).

**Likelihood-Ratio Test (LRT)**:
-   Compare Full Model (with 3-way interaction) vs. Reduced Model lacking the three-way interaction.
-   Statistic: Chi-squared (df = 1).
-   Significance: p < 0.05.

**Power Analysis**:
-   Method: Monte Carlo simulation with alpha=0.05 and using a target effect size of f² ≥ 0.15, given a minimum sample size sufficient for statistical power.
-   The achieved power will be reported to assess study sensitivity.
-   **Implementation**: A dedicated Phase 2.5 will execute this simulation.

**Multiple Comparisons**:
-   If multiple models are tested (e.g., different random effect structures), a correction (e.g., Bonferroni) will be applied.
-   The primary test is the LRT for the 3-way interaction.

**Causal Inference**:
-   The study is observational (no randomization of anxiety). Claims will be framed as **associational**.
-   "Anxiety modulates the relationship" will be interpreted as a statistical interaction, not a causal mechanism.

**Measurement Validity**:
-   **Fixation Duration**: Validated via I-VT algorithm. **Calibration**: The algorithm uses a velocity threshold. This must be converted to `pixels_per_frame` using the formula: `threshold = (angular_velocity_threshold) * (pixels_per_degree) / (sampling_rate_hz)`. `pixels_per_degree` is derived from screen width and viewing distance. **If these geometric parameters are missing from the dataset metadata, the I-VT algorithm cannot be reliably applied, and the pipeline will halt.**
-   **Valence**: Validated via IAPS/NimStim norms (if available in dataset metadata) or defined using continuous valence scale.
-   **Anxiety**: STAI is a validated self-report measure.

**Collinearity Check**:
-   Predictors (fixation, valence, anxiety) are not definitionally related.
-   However, if "threat" stimuli are inherently longer, collinearity may exist. This will be checked via VIF (Variance Inflation Factor).

## Compute Feasibility

**CPU-First Strategy**:
-   **Data Download**: `wget` (streaming).
-   **Preprocessing**: `pandas` + `numpy` (vectorized operations). I-VT algorithm is computationally light.
-   **Model Fitting**: `statsmodels` (GLMM) or `lme4` (via `rpy2` if necessary, but Python native preferred). `statsmodels` is CPU-only and fits within 7GB RAM for moderate datasets.
-   **Visualization**: `matplotlib` (headless).

**GPU Escape Hatch**:
-   Not required. The statistical model (GLMM) is not a deep learning task and runs efficiently on CPU.
-   If the dataset is extremely large (> 1M trials), streaming will be used to avoid OOM.

**Runtime Estimate**:
-   Download: Several minutes to half an hour (depending on network).
-   Preprocessing: Approximately half an hour to an hour.
-   Model Fitting: Several hours (depending on convergence).
-   Visualization: < 5 mins.
-   **Total**: ~3-4 hours (within 4-hour limit).

## Data Availability & Risks

**Major Risk**: **No verified dataset exists** that contains all required variables (Eye-tracking, Valence, Recall, STAI) in a downloadable format.

**Mitigation**: The pipeline will check for the presence of these variables in any downloaded dataset. If missing, it will exit with a specific error.
