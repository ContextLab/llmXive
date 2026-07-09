# Research: Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

## Dataset Strategy

This project relies on **verified datasets** as defined in the project's `# Verified datasets` block. The original spec references a DES Gold catalog of substantial size. However, the verified datasets block does **not** contain a direct link to the DES Year 3 Gold catalog with pre-computed `morphology_score` and `SNR` columns suitable for immediate analysis.

**Strategy**:
1.  **Primary Data Source**: We will use the **Strong Lens Finding Challenge (SLFC)** dataset as the *validated proxy* for the DES context.
    *   **Source**: `https://huggingface.co/datasets/strong-lens-finding-challenge/` (Verified URL).
    *   **Rationale**: SLFC is the only verified source that contains real image cutouts with known ground truth labels (`is_lens` = True/False) and features (SNR, morphology) or allows their extraction. This ensures that "purity" (TP/(TP+FP)) is calculated against *real* background noise (non-lens contaminants) and *real* lenses, not fabricated data.
    *   **Schema Adaptation**: The SLFC dataset provides the necessary columns. We will extract `SNR`, `morphology_score`, `RA`, `Dec`, and `is_lens` directly. **No synthetic generation of these features is performed.**
2.  **Validation Catalog**: The "independent validation" is the `is_lens` label within the SLFC dataset itself.
    *   **Rationale**: The SLFC dataset is a competition dataset where the ground truth is known. This satisfies Constitution Principle VI (Simulation-Based Validation Grounding) by using a real, independently verified ground truth rather than a synthetic injection.

**Dataset Fit Verification**:
*   **Required Variables**: `SNR`, `morphology_score`, `RA`, `Dec`, `is_lens`.
*   **Verified Source Check**: The SLFC dataset contains these variables.
*   **Constraint**: We cannot use the large DES file directly as it is not in the verified list. We will use the SLFC dataset as the representative sample for DES-like analysis. **No synthetic data generation is used to mimic properties.**

## Statistical Methodology

### 1. Threshold Grid Application
*   **Grid**: SNR ∈ [5, 20] (step 1), Morph ∈ [0.3, 0.9] (step 0.1).
*   **Total Combinations**: 16 × 7 = 112.
*   **Metric**: Detection Count per combination (candidates passing threshold).
*   **Handling Missing Data**: Rows with missing `SNR` or `morphology_score` are excluded from the specific threshold count but do not crash the process (FR-002, US-1).

### 2. Purity Calculation
*   **Method**: Cross-match detected candidates with the `is_lens` label in the SLFC dataset using coordinate tolerance ≤ 1.0 arcsec (FR-003).
*   **Formula**: `Purity = TP / (TP + FP)`.
    *   **TP**: Detected candidates where `is_lens` == True.
    *   **FP**: Detected candidates where `is_lens` == False (real contaminants).
*   **Edge Case**: If `TP + FP = 0`, purity is recorded as `NaN` or `0` (not crash) (US-2).

### 3. Statistical Analysis
*   **Trend Analysis**: **Cumulative Link Models (CLM)** are used to model the probability of detection as a function of the threshold, explicitly accounting for the nested/cumulative nature of the data (a detection at SNR=10 is also detected at SNR=5). This replaces Logistic Regression which assumes independence.
*   **Goodness-of-Fit**: Bootstrap resampling is used to generate confidence intervals for detection rates.
*   **Multiple Comparison Correction**: **Benjamini-Yekutieli (BY)** procedure applied to the p-values of the 112 threshold combinations. BY is robust to arbitrary dependency structures (unlike standard BH), addressing the concern about nested/correlated tests (FR-005).
*   **Causal Framing**: All results are framed as **associational**. No causal claims about lens physics are made (FR-004).

### 4. Sensitivity Analysis
*   **Sweep**: SNR cutoffs at `Base ± 0.5σ`, `Base ± 1.0σ`.
*   **Output**: Variation in False Positive Rate (FPR) for each sweep step (FR-006, SC-002).

## Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (limited CPU, limited RAM, No GPU).
*   **Memory Management**:
    *   Data loaded in **chunks** (e.g., 10k rows at a time) or via **lazy evaluation** to avoid loading the full dataset into RAM.
    *   Intermediate results (detection matrix) are small and fit easily in memory.
*   **Runtime**:
    *   Filtering 10k-50k rows across 112 thresholds is computationally trivial (< 1 hour).
    *   Bootstrap resampling on the lens population is CPU-tractable.
    *   CLM fitting is CPU-tractable for this dataset size.
    *   Total estimated runtime: < 2 hours (well within 6h limit).
*   **No GPU**: All operations use `scipy`, `numpy`, `pandas`, and `statsmodels` which run efficiently on CPU. No CUDA/PyTorch GPU dependencies.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use SLFC Dataset** | Verified datasets do not contain the full DES Year 3 Gold catalog with required schema. SLFC is the only verified source with real labels and features, ensuring scientific validity of the purity metric. |
| **Real Contaminants for FP** | The SLFC dataset includes a "non-lens" class. This provides real False Positives, avoiding the circularity of synthetic contamination. |
| **Chunked Loading** | Required by FR-001 and Constitution Principle III to ensure memory safety on 7GB RAM runners. |
| **Benjamini-Yekutieli Correction** | Required by FR-005 to handle the 112 *dependent* hypothesis tests (nested grid). Standard BH is invalid here. |
| **Associational Framing** | Required by FR-004; observational data cannot support causal claims. |
| **Cumulative Link Models (CLM)** | Required to handle the nested/cumulative nature of the threshold grid data. Logistic Regression assumes independence which is violated here. |

## Power & Sample Size Note
The SLFC dataset size (approximately k to tens of thousands of rows) is used as a proxy. If the number of true lenses in the subset is too low (<30), the purity metric will be reported as "insufficient sample" to avoid statistical invalidity, satisfying the power requirement for the intended effect size.
