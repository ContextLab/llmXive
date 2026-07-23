# Research: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## Scientific Background

Neural entrainment to rhythmic stimuli is a fundamental mechanism for temporal prediction in the brain. While the temporal dynamics of entrainment are well-studied, the role of **resting-state network topology** (the structural organization of functional connectivity) in modulating this process remains unclear. This project hypothesizes that specific topological properties—specifically **Clustering Coefficient** (local segregation) and **Characteristic Path Length** (global integration)—predict the strength of neural entrainment.

## Data Availability

### Primary Data Source
The primary intended source for connectivity data is the **Human Connectome Project (HCP) S1200 Release**. 
*   **Source**: `https://www.humanconnectome.org/study/hcp-young-adult/data-releases`
*   **Status**: **Restricted Access**. Requires Data Use Agreement (DUA) and credentials.
*   **Implication**: The CI runner cannot authenticate. Therefore, the pipeline must implement a **Simulated Data Fallback** (FR-009) as the default execution path for CI runs.
*   **Note**: No public dataset exists containing **matched** HCP fMRI connectivity and rhythmic entrainment metrics for the same subjects. The "Verified Datasets" table from previous iterations has been removed as it contained unusable links; the correct source is the official HCP release, which is restricted.

### Simulation Strategy
Given the unavailability of matched real data in the CI environment, the project employs a dual-mode simulation strategy:
1.  **Scientific Analysis Mode (Null Hypothesis)**: Generates synthetic data where `entrainment` is **uncorrelated** with topology (r=0). This tests the pipeline's ability to correctly fail to reject the null hypothesis (Type I error control). This is the **default** mode for scientific inquiry.
2.  **Validation Mode (Unit Test)**: Generates synthetic data with a **target r=0.5**. This is strictly a unit test to verify that the pipeline *can* detect a signal when one exists. This mode is **not** used for scientific hypothesis testing and is explicitly labeled as "Unit Test" in all outputs.

## Methodological Rigor

### Statistical Approach
1.  **Graph Metrics**:
    *   **Clustering Coefficient (CC)**: Measures local efficiency.
    *   **Characteristic Path Length (CPL)**: Measures global integration.
    *   *Collinearity Handling*: CC and CPL are often inversely related (mathematically coupled in small-world networks). We will calculate the **Variance Inflation Factor (VIF)**. 
        *   **If VIF > 5**: We will perform **Orthogonalization** (e.g., regress CC on CPL, use residuals as the predictor) to estimate unique effects. We will **report** standardized betas and p-values for the orthogonalized model and the joint R-squared. We will **not** suppress p-values, as this would render the hypothesis untestable.
        *   **If VIF <= 5**: Report standard MLR coefficients and p-values.
    *   *Interpretation*: Even with orthogonalization, the interpretation is limited to "unique variance explained" rather than independent biological signals, acknowledging the inherent coupling of these metrics.
2.  **Primary Analysis**:
    *   **Model**: Multiple Linear Regression (MLR): `Entrainment ~ CC + CPL`.
    *   **Correction**: **Holm-Bonferroni** correction applied to the p-values of the two predictors (FR-002, US-2).
    *   **Null Hypothesis**: $H_0: r = 0$ (no association).
    *   **Effect Size**: Report Pearson/Spearman correlation coefficient (r) and R-squared for all models.
3.  **Robustness**:
    *   Re-run analysis with **AAL** and **Power 264** parcellations.
    *   Generate a **comparative bar chart** showing the absolute difference in effect sizes (FR-010).

### Power & Sample Size
*   **Target N**: 50 (simulated).
*   **Power Analysis**: For N=50 with two predictors, the power to detect a moderate effect (f² = 0.15, r ≈ 0.38) at α=0.05 is approximately 0.70. Power to detect small effects (f² = 0.02, r ≈ 0.14) is < 0.20.
*   **Limitation**: N=50 is exploratory. The plan explicitly flags "Power Warning: N < 30" if the simulated N drops below 30. Results should be interpreted as preliminary.
*   **Effect Size**: For Validation Mode, target correlation $r \ge 0.5$ to ensure the pipeline detects the signal. For Scientific Mode, we test against $r=0$.

### Causal Inference Assumptions
*   **Observational Design**: The study is correlational. No randomization of network topology exists. Claims will be strictly framed as **associational**.
*   **Measurement Validity**: Simulated metrics are validated against the known generation parameters. The simulation does not claim to prove the biological hypothesis but to validate the analytical pipeline.

## Computational Feasibility

*   **Environment**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
*   **Strategy**:
    *   **CPU-First**: All operations (NetworkX graph construction, MLR, plotting) are lightweight and run efficiently on CPU.
    *   **Memory**: N=50 subjects with 200x200 matrices = ~200 MB total data. Well within 7GB RAM.
    *   **Time**: Graph metric calculation for 50 nodes is trivial (<1 min). MLR is instantaneous. Total runtime < 10 mins.
*   **GPU Escape Hatch**: Not required. No transformer models or heavy deep learning are used.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Missing Real Data** | **Simulated Data Fallback** (FR-009) is the default path. Distinguished between Null (Scientific) and r=0.5 (Validation) modes. |
| **Collinearity (VIF > 5)** | **Orthogonalization** implemented. Individual p-values are reported for the orthogonalized model, not suppressed. |
| **Zero Variance** | `graph_metrics.py` detects zero variance and flags the metric as "Non-informative" (Edge Case). |
| **Subject ID Mismatch** | Inner join performed; if N < 30, trigger simulation fallback (FR-003). |
| **Invalid Input Data** | System halts with "Invalid Entrainment Data" if CSV structure is invalid (FR-008, SC-005). |
| **Power Limitation** | Explicitly flag "Power Warning" in output and report effect sizes with confidence intervals. |