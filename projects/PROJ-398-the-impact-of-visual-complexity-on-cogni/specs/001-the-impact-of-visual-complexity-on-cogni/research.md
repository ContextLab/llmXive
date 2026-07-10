# Research: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## 1. Problem Statement & Hypotheses

**Research Question**: How does the visual complexity of video meeting backgrounds affect cognitive load during remote work, and does this relationship persist when controlling for task difficulty and participant familiarity?

**Hypotheses**:
- **H1**: Higher visual complexity (measured by entropy, variance, and object count) is positively associated with higher cognitive load (NASA-TLX scores and slower reaction times).
- **H2**: The relationship between visual complexity and cognitive load remains significant after controlling for task difficulty and participant ID.
- **H3**: Automated visual complexity metrics correlate significantly (r > 0.5) with human-perceived complexity ratings.

## 2. Dataset Strategy

### 2.1 Verified Sources & Data Validity

Per the project constraints, we must cite **ONLY** the verified datasets listed below.

| Dataset Name | Verified URL | Status | Usage Plan |
| :--- | :--- | :--- | :--- |
| **Real Meeting Backgrounds** | NO verified source found | **MISSING** | **Critical Gap**: No verified public dataset of real meeting backgrounds exists. **Scientific Analysis is BLOCKED** until real data is collected. The plan relies on **synthetic generation** *only* for pipeline validation (code logic, performance). |
| **Synthetic Stimuli** | N/A (Procedural) | **VALIDATED FOR PIPELINE** | Generated via `Pillow`/`numpy` for testing code logic, metric extraction speed (NFR-001), and power analysis. **NOT VALID FOR SCIENTIFIC CLAIMS**. |
| **NASA-TLX Norms** | NO verified source found | **MISSING** | The NASA-TLX scale is a standard instrument. We will use the standard scoring algorithm (Hart & Staveland, 1988) as described in the literature, but raw data must be collected via the pilot/main study. |

**Dataset Strategy Rationale**:
Since the "Verified datasets" block explicitly states "NO verified source found" for the visual stimuli, the implementation cannot cite a URL. To satisfy FR-001 and US-1, the `code/experiments/stimuli_loader.py` will include a **synthetic generation module**. This module will procedurally generate 50 background images with controlled complexity levels (low, medium, high) using `Pillow` and `numpy`. This ensures the pipeline is runnable on CI without external dependencies, satisfying the "Compute Feasibility" constraint. The generated images will be stored in `data/stimuli/` and checksummed (Constitution Principle III).

**Construct Validity Warning**: Synthetic backgrounds (procedurally generated noise/patterns) lack the semantic complexity of real meeting environments. Therefore, any correlation derived from synthetic data is a **pipeline validation metric**, not a scientific finding. The scientific hypothesis (H1-H3) can only be tested with real meeting backgrounds and real human ratings.

**Critical Distinction**:
- **Pipeline Validation (Synthetic)**: We will generate synthetic NASA-TLX scores *only* to verify that the LMM code runs and calculates diagnostics (VIF, FWER) correctly. These scores are **randomly generated** based on known parameters for the purpose of **code logic verification**. They are **NOT** used to test H1-H3.
- **Scientific Validation (Real)**: To test H1-H3, we **MUST** collect real human ratings (Pilot n=20) and real cognitive load data (Main Study). Synthetic cognitive load data is **prohibited** for hypothesis testing.

## 3. Methodology

### 3.1 Pilot Study (Metric Validation)
1.  **Stimulus Generation**: Generate 50 synthetic background images with varying complexity (for code testing).
2.  **Human Rating**: **REQUIREMENT**: Collect ratings from 20 real human participants (US-0) for a set of images (synthetic or real). **Simulated human ratings are NOT accepted for validation.**
3.  **Correlation**: Compute Pearson's r between real human ratings and automated metrics.
4.  **Validation Gate**: Proceed to main analysis only if r > 0.5 AND data source is flagged as `real`.

### 3.2 Automated Metric Extraction
- **Algorithm**:
  - **Entropy**: Shannon entropy of the grayscale image histogram.
  - **Color Variance**: Standard deviation of RGB channel values.
  - **Object Count**: Inference using `ultralytics` YOLOv8n (CPU mode) on 1080p frames.
- **Constraints**: Must process 10 images in <30s on 2 CPU cores (NFR-001). YOLOv8n is selected for its balance of speed and accuracy on CPU.

### 3.3 Statistical Analysis
- **Model**: Linear Mixed-Effects Model (LMM).
  - **Fixed Effects**: Visual Complexity, Task Difficulty.
  - **Random Effects**: (1 | Participant ID).
  - **Outcome**: NASA-TLX Score, Reaction Time.
- **Diagnostics**:
  - **Multicollinearity**: Calculate Variance Inflation Factors (VIF). If VIF > 5, flag instability or apply PCA (FR-003).
  - **Multiple Comparisons**: Apply Benjamini-Hochberg correction for >1 test (FR-004).
  - **Sensitivity Analysis**: Sweep alpha thresholds {0.01, 0.05, 0.1} and report SD of effect sizes (FR-005).
  - **Null Simulation**: Generate synthetic data with effect size = 0 to verify FWER control (FR-007). **This is a logic check to ensure the code correctly reports non-significance when the true effect is zero. It is NOT a hypothesis test.**

## 4. Statistical Rigor & Limitations

- **Power Analysis**: The spec assumes n=50-100 participants for power ≥ 0.80 (Assumption). The pilot (n=20) is for validation only. The main study power is dependent on real recruitment, which is outside the scope of the *computational* pipeline but the analysis code will include a power calculation function.
- **Causal Claims**: As an observational study (even with controlled stimuli), claims are associational. The plan explicitly avoids causal language.
- **Collinearity**: Entropy and Object Count may be correlated. VIF checks are mandatory.
- **Measurement Validity**: NASA-TLX is a validated instrument. Synthetic stimuli are a limitation; real meeting backgrounds would be ideal but are not available in verified sources.
- **Data Validity**: **Findings derived solely from synthetic stimuli are invalid for scientific claims.** The plan explicitly separates "Pipeline Validation Results" from "Scientific Results". **No fabricated cognitive load data will be used to test H1-H3.**
- **Methodological Separation**: The plan strictly separates **Code Logic Verification** (testing if the LMM runs on synthetic data) from **Hypothesis Testing** (testing if complexity causes load with real data). Synthetic data cannot validate the method's ability to detect real-world effects; it only validates the code's execution.

## 5. Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Libraries**: `ultralytics` (CPU wheel), `statsmodels`, `scikit-learn`.
- **Optimization**:
  - Images resized to 640x640 for YOLO inference (standard input size) to reduce RAM/CPU load, while maintaining complexity metrics.
  - Batch processing of images.
  - No GPU acceleration; all models run in default floating-point precision.
- **Runtime**: Estimated < 2 hours for full pipeline (generation + extraction + analysis) on 100 synthetic trials.

## 6. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Stimuli** | No verified dataset URL exists. Synthetic generation ensures reproducibility and CI feasibility for *pipeline testing*. |
| **Real Human Ratings** | Synthetic ratings create circular validation. Real human ratings (n=20) are mandatory for metric validation (US-0). |
| **YOLOv8n** | Smallest YOLO model, optimized for CPU inference. Meets NFR-001 (speed/RAM). |
| **LMM over OLS** | Required to handle repeated measures (Participant ID) and avoid inflated Type I errors. |
| **Benjamini-Hochberg** | Standard for controlling FDR in multiple hypothesis testing (FR-004). |
| **Data Validity Gate** | Prevents publication of scientific claims based on synthetic data. |
| **Null Simulation** | Used strictly to verify FWER control logic, not to generate scientific findings. |
| **No Synthetic Hypothesis Testing** | Synthetic cognitive load data cannot test H1-H3. Only real human data is used for hypothesis testing. |