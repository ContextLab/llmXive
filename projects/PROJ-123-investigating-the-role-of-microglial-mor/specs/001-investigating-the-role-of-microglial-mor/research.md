# Research: Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline

## 1. Problem Definition & Hypothesis

**Research Question**: Do specific aspects of microglial morphological remodeling in the hippocampus vs. prefrontal cortex predict age-related cognitive decline, and can these patterns distinguish between normal aging and early Alzheimer's pathology?

**Hypothesis**: Microglial morphology (specifically reduced complexity/branching) in the hippocampus will be a stronger predictor of cognitive status in the "Early AD" group compared to the "Normal Aging" group, whereas the prefrontal cortex will show a more linear relationship with age across both groups.

**Key Challenge**: The interaction between `PathologyStatus` and `BrainRegion` must be statistically isolated from main effects to avoid conflating aging with pathology.

**Construct Validity Note**: The study uses 'Cognitive Status Score' (single timepoint) as a proxy for 'cognitive decline' due to the cross-sectional nature of available public datasets. Findings will be framed as "associations with current cognitive state" rather than "decline" unless longitudinal validation is performed later.

## 2. Dataset Strategy

The project relies on matched datasets containing high-resolution confocal microscopy images, cognitive scores, and pathology metadata.

| Variable | Source / Description | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **Microglial Images** | High-res confocal microscopy (Hippocampus/PFC) | **NO verified source found** | *Critical Gap*: No verified URL exists for the specific Allen/AD-Knowledge Portal subset required. |
| **Cognitive Scores** | Morris Water Maze latency / Z-scores | **NO verified source found** | *Critical Gap*: No verified URL exists for the specific matched cognitive dataset. |
| **Pathology Status** | Amyloid-beta load, Tau markers | **NO verified source found** | *Critical Gap*: No verified source. Dynamic thresholding (FR-010) is mandatory. |
| **PC1_Morphology** | Derived via PCA | N/A (Computed) | N/A |
| **BrainRegion** | Metadata tag | N/A (Computed) | N/A |

**Note on Data Availability**: The "Verified datasets" block provided for this project indicates **NO verified source** for the primary biological datasets.
*   **Action**: The implementation will use **synthetic/mock data generators** for the initial pipeline validation (US-1, US-2, US-3) to ensure the code logic (extraction, regression, interaction terms) works correctly.
*   **Future Step**: The `data_ingestion.py` module will be parameterized to accept real data paths once verified URLs are established. The plan explicitly flags this as a **blocking dependency** for real-world results.

*Per the specification, if a dataset the spec needs has NO verified source, we state that explicitly rather than fabricating one.*

## 3. Methodological Approach

### 3.1 Image Preprocessing & Feature Extraction (FR-001, FR-002, FR-003)
*   **Denoising**: Apply Gaussian blur and adaptive thresholding (equivalent to Fiji's "Denoise" and "Auto Threshold") to remove noise.
*   **Segmentation**: Skeletonization of microglial processes using `scikit-image` (algorithmic logic matching Simple Neurite Tracer).
*   **Metrics**:
    *   **Branch Points**: Count of nodes with degree > 2 in the skeleton.
    *   **Total Length**: Sum of pixel distances in the skeleton (scaled by resolution).
    *   **Soma Area**: Area of the central cell body (largest connected component).
    *   **Sholl Intersections**: Count of intersections at radii $r \in \{2, 5, 10, \dots\}$ $\mu m$.
*   **Validation**: Compare automated counts against a manually annotated subset (target <10% error) *in the synthetic validation phase*.

### 3.2 Statistical Modeling (FR-004, FR-011)
*   **Collinearity Handling**: Morphological features (branch points vs. total length) are inherently correlated.
    *   **Method**: Principal Component Analysis (PCA) on the morphological feature matrix.
    *   **Output**: Orthogonal components (PC1, PC2, etc.) used as predictors.
    *   **Check**: Calculate Variance Inflation Factor (VIF). If VIF > 5.0, re-run PCA or drop features.
    *   **Interpretability Protocol**: To address the loss of biological specificity, the plan will:
        1.  Report the loadings of significant PCs to identify which original features (branch points, length) drive the variance.
        2.  Run a secondary Lasso/Ridge regression to see if individual features survive regularization, providing a direct biological link.
*   **Regression Model**:
    $$ \text{CognitiveScore}_i = \beta_0 + \beta_1 \text{PC1}_i + \beta_2 \text{Pathology}_i + \beta_3 \text{Region}_i + \beta_4 (\text{Pathology}_i \times \text{Region}_i) + \epsilon_i $$
    *   **Interaction**: The term $\beta_4 (\text{Pathology} \times \text{Region})$ is the primary test of the hypothesis.
    *   **Causality**: `causality_warning` = `true` (FR-007).
*   **Data Leakage Prevention**: The "control group" for dynamic pathology thresholding (FR-010) will be defined strictly by *external metadata* (e.g., age < 60) or a separate training set, ensuring the threshold is calculated independently of the subjects used in the regression model.

### 3.3 Validation & Sensitivity (FR-005, FR-006)
*   **Cross-Validation**: 5-fold CV to assess generalizability (SC-002).
*   **Sensitivity Analysis**: Sweep Sholl radius steps $\{2\mu m, 5\mu m, 10\mu m\}$ and report variation in interaction p-value (SC-003).
*   **Null Hypothesis Validation**: Synthetic data will include cases with *zero* interaction effects to ensure the pipeline correctly identifies non-significance (avoiding circular validation).

### 3.4 Power Analysis & Limitations
*   **Interaction Effect Power**: Interaction effects typically require substantially larger sample sizes than main effects.
*   **Current Status**: Public datasets likely have small N.
*   **Strategy**: If N is insufficient to detect moderate effects (Power < 0.80), the study will:
    1.  Report observed power and effect sizes with wide confidence intervals.
    2.  Frame results as "exploratory" rather than confirmatory.
    3.  Explicitly state the limitation in the final report.

## 4. Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (2 CPU, ~7GB RAM).
*   **Strategy**:
    *   **No GPU**: All image processing uses `scikit-image` (CPU). No deep learning segmentation (e.g., U-Net) to avoid memory/CUDA issues.
    *   **Data Sampling**: If the full dataset exceeds RAM, the pipeline will process images in batches and stream results to CSV.
    *   **Memory Limit**: Intermediate matrices (PCA) limited to < 2GB.
    *   **Time Limit**: Total runtime target < 4 hours (leaving 2h buffer).

## 5. Decision Log & Rationale

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data for Validation** | No verified URLs exist for the required matched biological datasets. Running the pipeline on real data is currently impossible. Synthetic data allows testing the *logic* (FR-001 to FR-011) without hallucinating data sources. |
| **PCA over Direct Regression** | Branch points and total length are definitionally related (more branches = longer total length). Direct regression violates VIF < 5.0 (FR-004). PCA ensures orthogonal predictors. *Mitigation*: Loadings will be mapped back to original features. |
| **Dynamic Pathology Threshold** | Public datasets often lack explicit "Early AD" labels. Calculating the 75th percentile of the control group (FR-010) provides a consistent, data-driven classification method. *Mitigation*: Strict separation of training/test sets to prevent leakage. |
| **Sholl Sensitivity Sweep** | The choice of 5µm is arbitrary. Sweeping {2, 5, 10}µm ensures the interaction effect is not an artifact of the radius step (SC-003). |
| **Exploratory Framing** | Given likely low sample size for interaction effects, results will be framed as exploratory with reported power, avoiding false claims of confirmation. |