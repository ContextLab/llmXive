# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## 1. Problem Statement & Hypothesis

**Research Question**: Does increasing the visual salience (luminance contrast/brightness) of a target object in a morally ambiguous scenario increase the blame attributed to the agent associated with that object?

**Hypothesis**: Higher visual salience of the causal agent/object will lead to higher blame ratings (1-7 Likert scale) compared to lower salience variants, controlling for semantic content.

## 2. Dataset Strategy

### Source Selection
The project relies on open visual datasets containing social or conflict scenarios.
*   **Primary Candidate**: Visual Genome (VG) or similar dataset with moral/social tags.
    *   **Status**: **VERIFIED SOURCE REQUIRED**.
    *   **Action**: Phase 0.1 will search for a verified URL in the `# Verified datasets` block. If found, it will be used. If not, the project **halts** and generates a "Data Gap Report".
    *   **Fallback**: None. The plan rejects the use of random public domain images or synthetic geometric scenes as they lack the required semantic content (moral ambiguity) to answer the research question.

**Verified Datasets Used for Analysis**:
*   **None**. The plan does not use external pre-computed statistics (like 'ANOVA (json)') for validation as they introduce category errors. Validation relies entirely on synthetic data with known ground truth.

### Data Suitability & Mismatch
*   **Visual Genome**: Contains images but **no verified URL** in the provided block. The plan cannot rely on a direct API call to VG in the CI environment without a verified source.
*   **Gap**: The spec requires "morally ambiguous images." The available verified datasets (if any) do not contain images.
*   **Resolution**: The implementation will use a **verified subset** of an open dataset if found. If not, the project halts. No simulated or placeholder images will be used for the main analysis.

## 3. Methodology

### Phase 0.1: Dataset Verification & Ingestion
*   **Input**: List of potential dataset sources.
*   **Process**:
    1.  Check `# Verified datasets` block for a URL matching the criteria (images with social/conflict tags).
    2.  If found, download and checksum the dataset.
    3.  If not found, generate "Data Gap Report" and halt.
*   **Output**: `data/raw/verified_dataset_info.json`.

### Phase 0.5: Human Coding Pilot (FR-008)
*   **Input**: Subset of raw images (N=10).
*   **Process**:
    1.  Deploy a local annotation tool (e.g., Label Studio or CSV-based).
    2.  Recruit N=2 independent annotators (real humans).
    3.  Calculate Cohen's kappa.
    4.  If kappa < 0.8, exclude scenarios or re-code.
*   **Output**: `data/processed/human_coding_results.csv`.

### Phase 1: Data Preparation & Salience Manipulation (FR-001)
*   **Input**: Raw images (subset).
*   **Process**:
    1.  **Metadata Filtering**: Filter for 'social' or 'conflict' tags (simulated for prototype, real for full study).
    2.  **Manipulation**: Use `Pillow` to adjust `brightness` and `contrast` parameters.
        *   Low: Original.
        *   Medium: +[deferred] contrast/brightness in target region.
        *   High: +[deferred] contrast/brightness in target region.
    3.  **Validation**: Calculate pixel-wise difference and verify semantic preservation (SSIM).
*   **Output**: 3 variants per scenario (Low, Medium, High).

### Phase 2: Survey Deployment Pilot (FR-002, FR-003)
*   **Design**: Within-subject, randomized order.
*   **Process**:
    1.  Deploy a functional survey interface (e.g., local server or sandbox) to N=10 real participants.
    2.  Collect blame ratings and metadata.
    3.  **Data Cleaning (FR-007)**: Implement logic to detect "straight-lining" (identical ratings across all items).
*   **Output**: `data/survey/pilot_responses.csv` with real human data.

### Phase 3: Statistical Analysis & Pipeline Validation (FR-004, FR-005, FR-006)
*   **Model**: **Linear Mixed-Effects Model (LMM)**.
    *   **Rationale**: A standard repeated-measures ANOVA treats 'Scenario' as a fixed effect or ignores its variability. Given the design (20 scenarios x 3 levels), the effect of salience may vary significantly by scenario. An LMM with random intercepts for `Scenario` and `Participant` properly accounts for this nested structure, preventing biased estimates and inflated Type I errors.
    *   **Formula**: `Rating ~ Salience + (1 | Participant) + (1 | Scenario)`
    *   **Fixed Effect**: Salience (3 levels: Low, Medium, High).
    *   **Random Effects**: Random intercepts for `Participant` and `Scenario`.
    *   **Dependent Variable**: Blame Rating (1-7).
*   **Assumptions**:
    *   **Sphericity**: Not required for LMM, but residuals will be checked for normality and homoscedasticity.
    *   **Multiple Comparisons**: Bonferroni correction for pairwise contrasts (Low vs Med, Med vs High, Low vs High).
*   **Effect Size**: Calculate partial eta-squared ($\eta_p^2$) or marginal R-squared and 95% Confidence Intervals.
*   **Validation Strategy**:
    *   **Pipeline Validation (Synthetic Data)**:
        *   **Positive Control**: Generate synthetic data with an **injected effect** (e.g., d=0.5). The pipeline must **correctly reject** the null hypothesis, proving sensitivity.
        *   **Null Control**: Generate synthetic data with **no effect** (Rating = Base + Noise). The pipeline must **fail to reject** the null hypothesis, proving specificity and Type I error control.
        *   **Scope**: This phase validates the **analysis pipeline's ability to detect effects** and control error rates. It does **not** validate the scientific hypothesis (that salience affects blame) which requires real empirical data.
*   **Output**: `data/analysis/results.json` and a console report.

## 4. Statistical Rigor & Feasibility

*   **Multiple Comparison Correction**: Bonferroni correction will be applied to the 3 pairwise contrasts (FR-005).
*   **Power Analysis**: The plan acknowledges the limitation of the sample size (pilot). The analysis will report the achieved power or note the limitation if the sample size is small.
*   **Causal Inference**: The design is experimental (within-subject manipulation), allowing causal claims *within the constraints of the simulation*.
*   **Collinearity**: Not applicable (Salience levels are mutually exclusive experimental conditions).
*   **Compute Feasibility**:
    *   **Memory**: Image processing for ~60 images is negligible (<100 MB).
    *   **CPU**: LMM on 150 rows is fast.
    *   **Time**: Total runtime < 5 minutes.
    *   **No GPU**: All operations (Pillow, statsmodels) are CPU-native.

## 5. Risks & Mitigations

*   **Risk**: No verified image dataset URL.
    *   **Mitigation**: Halt project. Do not proceed with unverified data.
*   **Risk**: "Human coding" cannot be performed in CI.
    *   **Mitigation**: Phase 0.5 explicitly includes a real human coding pilot task.
*   **Risk**: Real survey data collection is external.
    *   **Mitigation**: Phase 2.5 explicitly includes a real survey deployment pilot task.
*   **Risk**: Pipeline validation is circular.
    *   **Mitigation**: Use **Positive Control** (injected effect) and **Null Control** (no effect) synthetic datasets to validate sensitivity and specificity. Explicitly state that this validates the *pipeline*, not the *hypothesis*.