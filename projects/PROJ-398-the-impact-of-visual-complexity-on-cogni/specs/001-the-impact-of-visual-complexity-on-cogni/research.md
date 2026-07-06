# Research: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## Research Question

How does the visual complexity of video meeting backgrounds affect cognitive load during remote work, and does this relationship persist when controlling for task difficulty and participant familiarity with the meeting content?

## Dataset Strategy

The project relies on a **synthetic dataset generation** approach. As no verified public dataset exists that combines specific video meeting background frames with paired NASA-TLX and reaction-time cognitive load scores (see "Verified datasets" block below), the study will generate a high-fidelity synthetic dataset. This approach allows for precise control over the independent variable (visual complexity) and the dependent variables (cognitive load), enabling the validation of the analysis pipeline before potential application to real human data.

**Verified Datasets Reference**:
- **CPU-compatible**: NO verified source found.
- *Action*: The project will synthesize background frames using procedurally generated or publicly available stock images (stored in `data/raw/stimuli`) and simulate participant responses using statistical models calibrated to known psychometric distributions.

**Variable Fit Confirmation**:
- **Predictors**: Visual Complexity (Entropy, Color Variance, Object Count).
  - *Source*: Computed via `01_extract_metrics.py` on `data/raw/stimuli`.
- **Outcomes**: NASA-TLX Score, Reaction Time (Mean), Accuracy (%).
  - *Source*: Simulated in `02_generate_synthetic_data.py` based on complexity metrics + noise.
- **Covariates**: Task Difficulty (Simulated), Participant ID.
  - *Source*: Simulated.
- **Fit**: The synthetic generation allows exact mapping of the required variables. No missing variables exist in the synthetic design.

## Methodology

### 1. Visual Complexity Metric Extraction (FR-001)
- **Image Entropy**: Calculated using Shannon entropy on the grayscale histogram of the background frame.
- **Color Variance**: Calculated as the variance of the RGB channels across the image.
- **Object Detection Count**: Performed using **YOLOv8n** (nano model) in CPU mode.
  - *Rationale*: YOLOv8n is the smallest variant in the YOLOv8 family, optimized for speed and capable of running on CPU. Larger models (v8m/l/x) are excluded to meet the 7GB RAM / 2 CPU core constraint.
  - *Handling Zero Objects*: If no objects are detected, the count is recorded as 0. The pipeline must not crash.

### 2. Participant Simulation & Counterbalancing (FR-002)
- **Design**: Within-subjects design. Each "participant" views a subset of stimuli.
- **Counterbalancing**: A **Latin Square** design will be used to assign stimuli to participants, ensuring that each stimulus appears in each position (order) an equal number of times across the sample. This controls for order effects and fatigue.
- **Response Generation**:
  - **NASA-TLX**: Generated as a function of visual complexity + task difficulty + random noise.
  - **Reaction Time**: Generated as a function of complexity (inverse efficiency) + noise.
  - **Missing Data**: Simulated missingness (e.g., 5% of trials) will be flagged for exclusion, not imputed, per US-2.

### 3. Statistical Analysis (FR-003, FR-004, FR-005)
- **Model**: Linear Mixed-Effects Model (LMM) using `statsmodels`.
  - **Formula**: `TLX ~ Complexity + Task_Difficulty + (1 | Participant_ID)`
  - **Fixed Effects**: Complexity (Entropy/Var/Count), Task Difficulty.
  - **Random Effects**: Intercept for Participant_ID.
- **Multicollinearity Check (FR-003)**:
  - Calculate **Variance Inflation Factors (VIF)** for all predictors.
  - *Threshold*: If VIF > 5, the plan will either combine predictors via PCA or flag the instability in the report.
- **Multiple Comparisons (FR-004)**:
  - Apply **Benjamini-Hochberg (BH)** correction to p-values if multiple hypotheses are tested (e.g., testing Entropy, Variance, and Count separately).
  - Report adjusted p-values.
- **Sensitivity Analysis (FR-005)**:
  - Sweep significance threshold $\alpha$ over {0.01, 0.05, 0.1}.
  - Report the variation in the count of significant predictors to assess robustness.

## Statistical Rigor & Assumptions

- **Causal Claims**: None. The study is observational (even with synthetic data, the "participants" are simulated). Claims will be framed as **associational**.
- **Power Analysis**: The sample size (N=100) is assumed sufficient for detecting medium effect sizes (Cohen's d > 0.5). Exact power calculations are deferred to the analysis script but will be documented.
- **Measurement Validity**: NASA-TLX is a validated instrument. In this synthetic study, the "validity" is established by the known ground-truth relationship injected during data generation.
- **Collinearity**: Entropy, Variance, and Object Count may be correlated. VIF will be used to detect this. If high collinearity exists, independent effects will not be claimed; instead, the composite effect will be reported.
- **Multiple Comparison Correction**: Mandatory for >1 test. BH correction is chosen over Bonferroni for better power in exploratory analyses.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Inference**: YOLOv8n on CPU.
  - *Estimate*: ~0.5s per 1080p frame. 50 frames = 25s. Well within limits.
- **Memory**: `opencv` and `ultralytics` CPU wheels fit within 2GB RAM.
- **Disk**: 50 images + synthetic CSVs < 100MB.
- **Runtime**: Total pipeline < 1 hour.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data** | No verified dataset exists with the specific combination of background frames and cognitive load metrics. Synthetic data allows controlled validation of the pipeline and statistical methods. |
| **YOLOv8n (CPU)** | Larger models require GPU or excessive RAM. YOLOv8n is the only variant that meets the "CPU-only, <2GB RAM" constraint while providing object counts. |
| **Latin Square Design** | Essential to control for order effects in a within-subjects design without requiring an impractically large number of participants. |
| **LMM over OLS** | Accounts for the non-independence of observations (multiple trials per participant) via random intercepts. |
| **Benjamini-Hochberg** | More powerful than Bonferroni for multiple comparisons while controlling the False Discovery Rate (FDR). |

## References & Verified Sources

- **Verified Datasets**:
  - CPU-compatible: NO verified source found. (Project uses synthetic data generation).
- **Methodology Citations**:
  - NASA-TLX: (Standard instrument, no URL required for the tool itself, but validation logic is in `code/`).
  - YOLOv8: Ultralytics documentation (CPU inference mode).
  - LMM: `statsmodels` documentation.

*Note: No external dataset URLs are cited as none exist in the verified block. The study relies on internal generation.*
