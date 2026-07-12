# Research: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## 1. Problem Statement & Hypotheses

**Research Question**: How does the visual complexity of video meeting backgrounds affect cognitive load during remote work, and does this relationship persist when controlling for task difficulty and participant familiarity?

**Primary Hypothesis (H1)**: Higher visual complexity (measured by entropy, color variance, and object count) is positively associated with higher cognitive load (NASA-TLX scores and slower reaction times).

**Secondary Hypothesis (H2)**: The relationship between visual complexity and cognitive load is moderated by task difficulty (i.e., the effect is stronger for difficult tasks).

**Null Hypothesis (H0)**: There is no significant association between visual complexity metrics and cognitive load outcomes.

## 2. Dataset Strategy

This study relies on two distinct data sources: (1) a set of visual stimuli (background images/clips) and (2) human participant responses.

### 2.1 Visual Stimuli (Predictor Variables)
The study requires a diverse set of meeting background images.
*   **Source**: As per the "Verified datasets" block, **NO verified source** was found for a pre-existing "Visual Complexity" or "Meeting Background" dataset.
*   **Strategy**: The system will **synthesize/generate** the stimuli dataset using public domain image repositories (e.g., Unsplash via API, or curated public domain sets) to ensure we have control over the complexity range. The generated images will be stored in `data/stimuli/`.
*   **Variables**:
    *   `image_entropy`: Calculated via `numpy.histogram` (FR-001).
    *   `color_variance`: Calculated via `cv2.meanStdDev` (FR-001).
    *   `object_count`: Detected via YOLOv8n (FR-001).
*   **Validation**: A pilot study (US-0) with n=20 humans will rate these images on a 1-10 scale. The automated metrics will be validated against these human scores (FR-006, SC-001).

### 2.2 Participant Data (Outcome Variables)
*   **Source**: Data collected via the custom Streamlit application (`code/study/app.py`).
*   **Participants**: Target N=100 participants (See Power Analysis below).
*   **Variables**:
    *   `nasa_tlx`: Subjective cognitive load (0-100 scale).
    *   `reaction_time`: Mean ms from post-task RT task.
    *   `task_difficulty`: Self-reported difficulty of the meeting content (1-7 scale).
    *   `baseline_rt`: Reaction time on neutral stimulus.
*   **Dataset Limitation Note**: No external dataset provides NASA-TLX or Reaction Time data for this specific study. The "Verified datasets" block confirms **NO verified source** for NASA-TLX or FWER datasets. Therefore, the system must generate this data via the experimental protocol, not by downloading a pre-existing CSV.

### 2.3 Statistical Validation Data
*   **Null Simulation**: Synthetic data will be generated in `code/utils/synthetic_data.py` where the true effect size is 0. This is used *only* to validate the pipeline's ability to control FWER (FR-007, SC-004). This is **not** a research result; it is a code correctness check. Primary hypothesis testing uses **only** real human data.

## 3. Methodology

### 3.1 Metric Extraction (FR-001)
1.  **Entropy**: Computed as $H = -\sum p(x) \log p(x)$ on the grayscale histogram.
2.  **Color Variance**: Standard deviation of RGB channels averaged.
3.  **Object Count**: YOLOv8n (CPU mode) inference on 1080p frames.
    *   *Constraint*: Must run in <30s for 10 images (NFR-001). YOLOv8n is selected as the smallest viable model.

### 3.2 Experimental Design (US-2, FR-002, FR-002b, FR-002c)
1.  **Stimuli Presentation**: **Balanced Block Randomization**.
    *   *Rationale*: A Latin Square design is infeasible for 50 stimuli (requires 50 distinct sequences). Instead, stimuli are divided into multiple blocks of 10. Each participant views multiple blocks (a set number of stimuli) in a randomized order. This ensures coverage of the complexity range while maintaining feasibility.
2.  **Baseline**: Participants complete a low-complexity RT task first.
3.  **Trials**: Participants view clips, then complete NASA-TLX and a RT task.
4.  **Data Integrity**: Missing data is flagged for exclusion, not imputed (US-2, SC-003).

### 3.3 Statistical Analysis (US-3, FR-003, FR-004, FR-005)
1.  **Primary Model**: Linear Mixed-Effects Model (LMM).
    *   Fixed Effects: Visual Complexity (Entropy, Variance, Object Count), Task Difficulty, Interaction.
    *   Random Effects: Random intercept for `participant_id`.
    *   Formula: `TLX ~ Complexity + Difficulty + (1|participant_id)`
2.  **Multivariate Strategy & Collinearity**:
    *   **Univariate Approach**: To avoid multicollinearity (high correlation between entropy and variance), the primary analysis runs **separate models** for each metric (Entropy, Variance, Object Count).
    *   **PCA Fallback**: If VIF > 5 is detected in any model, the system automatically falls back to a PCA-based "Global Complexity" index for that predictor, reporting the result as "Global Complexity" rather than individual metrics. This pre-registers the consequence of collinearity to ensure interpretability.
3.  **Multiple Comparison Correction**: Benjamini-Hochberg procedure applied to p-values of multiple predictors (FR-004).
4.  **Sensitivity Analysis**: Sweep $\alpha$ over a range of small values. Calculate SD of effect sizes (FR-005b).
5.  **Null Simulation**: Generate synthetic data (effect=0), run model, calculate observed FWER. Compare to nominal $\alpha=0.05$ (FR-007).

## 4. Power Analysis

*   **Design**: Repeated measures (10 trials per participant).
*   **Target Power**: 0.80.
*   **Effect Size**: Cohen's d = 0.5 (medium).
*   **Intra-class Correlation (ICC)**: Assumed 0.3.
*   **Calculation**: Using `statsmodels.stats.power` with ICC adjustment, N=100 participants with 10 trials each yields >0.80 power. The previous assumption of N=50-100 is refined to **N=100** to ensure adequate power for the repeated measures design.

## 5. Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (limited CPU, constrained RAM).
*   **GPU**: **None**. YOLOv8n will run in CPU mode (`device='cpu'`).
*   **Memory**: Data subset to <7GB. Images processed in batches.
*   **Runtime**:
 * Metric extraction: [deferred]/image (CPU) -> 10 images in [deferred].
    *   LMM: <1s for N=100.
    *   Total pipeline: <1 hour.
*   **Libraries**: `ultralytics` (CPU wheel), `statsmodels`, `scikit-learn`. No `torch` CUDA, no `bitsandbytes`.

## 6. Dataset Variable Fit & Mismatch Resolution

*   **Mismatch Identified**: The study requires "meeting background images" and "human-rated complexity". No external dataset contains *both* the specific images and the human ratings for this context.
*   **Resolution**:
    1.  **Stimuli**: Generate/curate a set of public domain images (Unsplash/Pixabay) and store in `data/stimuli/`.
    2.  **Human Ratings**: Conduct a *local* pilot study (US-0) using the system's own interface to generate the ground truth. This is not a "download" but a "data generation" step required by the spec.
    3.  **Main Data**: Collect NASA-TLX/RT via the system's own experiment.
*   **Conclusion**: No external dataset is needed for the *outcome* variables. The "Verified datasets" block correctly lists no source for these. The plan relies on **system-generated** data for both stimuli and responses, validated by the pilot protocol.

## 7. Statistical Rigor & Limitations

*   **Multiple Comparisons**: Addressed via Benjamini-Hochberg (FR-004).
*   **Power**: Refined to N=100 with 10 trials/participant to account for ICC.
*   **Causal Claims**: The study is observational (participants self-select complexity via their background). Claims will be framed as **associational** (Assumption).
*   **Measurement Validity**: NASA-TLX is a standard, validated instrument. Pilot correlation (r > 0.5) validates the automated metrics against human perception (SC-001).
    *   *Validation Logic*: The pilot validates that automated metrics correlate with *human perception*. The main study tests if *perceived complexity* (validated by metrics) predicts *cognitive load*. If pilot correlation fails, metrics are discarded, preventing circular validation.
*   **Collinearity**: VIF check (FR-003) triggers fallback to univariate or PCA models to ensure interpretable coefficients.
*   **Stimulus Validity & Ecological Fallacy**:
    *   *Limitation*: The plan uses static images from public repositories. Real meeting backgrounds are dynamic, often contain people, and have specific lighting conditions. Static images may not elicit the same cognitive load as a dynamic, real-world meeting background.
    *   *Mitigation*: Stimuli will be selected specifically from "Zoom/Teams background" public sets to improve ecological validity.
    *   *Scope*: Results are explicitly limited to "static visual complexity". Future work must address motion.

## 8. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **YOLOv8n over ResNet** | NFR-001 requires <30s for 10 images on CPU. YOLOv8n is the only model fast enough for object counting without GPU. |
| **Synthetic Null Data** | Required by FR-007 to validate the statistical pipeline's FWER control. Not a research result. |
| **No External NASA-TLX Dataset** | No verified source exists. Data must be collected via the experiment (US-2). |
| **Balanced Block Randomization** | Required by US-2 to control for order effects (fatigue/practice) while being feasible for 50 stimuli. |
| **Pilot Study (n=20)** | Required by US-0 to validate automated metrics before the main study. |
| **Univariate Models** | Required to avoid multicollinearity between entropy, variance, and object count. |
