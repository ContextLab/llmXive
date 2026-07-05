# Research: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

## Executive Summary

This research phase investigates the feasibility of aggregating ≥100 solder alloy compositions with Vickers hardness measurements from open sources to train and evaluate regression models. The primary challenge is the scarcity of high-quality, standardized hardness data for specific solder families in public repositories. The plan prioritizes CPU-tractable methods and rigorous statistical diagnostics (VIF, SHAP) to ensure findings are robust and associational.

## Dataset Strategy

### Verified Literature Corpus

The spec requires aggregation from Materials Project, NIST, OpenAlloy, and literature. The following verified sources were checked against the project's constraints:

| Source | Status | Notes |
| :--- | :--- | :--- |
| **Materials Project** | **Not Verified in Block** | The "Verified datasets" block provided no URL for Materials Project. Literature scraping is required. |
| **NIST** | **Verified (Non-Target)** | URLs provided (`nisten/opus-doctor-patient...`) are for medical conversations, not materials science. **No verified NIST materials source found.** |
| **OpenAlloy** | **No Verified Source** | Spec notes "NO verified source found". |
| **Literature** | **Primary Strategy** | The 'Verified Literature Corpus' consists of specific, cited papers (e.g., the Mg-Gd alloy paper, standard Sn-Ag-Cu reviews) that will be scraped. |

**Critical Gap & Mitigation**:
The "Verified datasets" block contains **zero** materials science datasets relevant to solder hardness. The provided URLs are for medical conversations, skin disease, and unrelated ML benchmarks.
*   **Action**: The `code/ingestion` module implements a 'Literature Aggregator' that parses PDFs from the 'Verified Literature Corpus' into a structured CSV.
*   **Fallback**: If <50 unique compositions are found after scraping, the system emits the `N < 50` warning and proceeds with reduced power, as per FR-001.
*   **No URL Fabrication**: No URLs are cited for solder data in this plan. The pipeline will rely on the 'Verified Literature Corpus' only.

### Dataset Variables & Fit

| Variable | Required? | Source Strategy |
| :--- | :--- | :--- |
| **Elemental Composition** | Yes (All elements) | Extracted from literature tables. Must sum to [deferred] (or ≥95%). |
| **Vickers Hardness (HV)** | Yes | Extracted from literature tables. Must be room-temperature. |
| **Elemental Properties** | Yes (Derived) | Lookup tables (atomic mass, radius, electronegativity) from standard periodic table data (hardcoded in code). |
| **Microstructure/History** | No | Excluded per Assumption. If present in source, flagged as missing/confounding. |

**Variable Fit Check**:
The spec assumes datasets contain "all required variables." Since no verified dataset URL exists, the plan assumes the *literature* contains these variables. If a paper reports hardness but not full composition, that record is dropped.

## Statistical Methodology

### Model Strategy
1.  **Baseline**: Linear Regression (OLS) with R² and RMSE.
2.  **Primary**: XGBoost Regressor (CPU-optimized, `tree_method='hist'` or `exact` for small N).
3.  **Validation**: 5-Fold Cross-Validation (stratified by alloy family if possible, otherwise random).
4.  **Comparison**: **Bootstrap Model Comparison** (1000 resamples of the test set) to compare R² distributions.

### Statistical Rigor & Assumptions
*   **Multiple Comparisons**: Not applicable for a single primary comparison (XGBoost vs. Linear). However, if multiple metrics (R², RMSE, MAE) are tested, a Bonferroni correction will be applied.
*   **Sample Size/Power**:
    *   Target: N ≥ 100.
    *   Limitation: If N < 100, the plan explicitly states that the power to detect small effect sizes is low. The Bootstrap Model Comparison is used to mitigate the low power of a t-test on 5 folds.
    *   Mitigation: 1000 Bootstrap resamples on the held-out test set to generate robust 95% CIs (FR-005) and compare model distributions.
*   **Causal Inference**:
    *   **Strictly Associational**: As per FR-007 and Assumption, the study frames results as "Composition is associated with Hardness." No causal claims (e.g., "Adding X causes Y increase") are made.
    *   **No Randomization**: The dataset is observational. Confounding variables (thermal history, microstructure) are acknowledged as limitations.
*   **Measurement Validity**:
    *   Vickers hardness is assumed valid if reported in peer-reviewed literature.
    *   Standardization: All HV values converted to a single unit (HV). Different load forces are noted as a potential source of variance.
*   **Collinearity**:
    *   **Issue**: Elemental properties (mass, radius, electronegativity) are often correlated.
    *   **Method**: Variance Inflation Factor (VIF) calculated for all predictors.
    *   **Threshold**: VIF ≥ 5 flags high collinearity. If detected, feature importance is interpreted descriptively (joint effect) rather than as independent contributions.

### Theoretical Justification for Descriptors

The descriptors (weighted mean atomic mass, electronegativity variance, atomic radius variance, etc.) are not treated as independent physical mechanisms but as **alternative encodings** of the composition vector.
*   **Hume-Rothery Rules**: These rules suggest that atomic size difference and electronegativity differences drive phase stability and hardness.
*   **Miedema Models**: These models use electronegativity and electron density to predict formation enthalpies.
*   **Justification**: The specific descriptors (variance, weighted mean) are chosen as proxies for these known physical mechanisms (lattice distortion, phase stability) in solder alloys.
*   **Interpretation**: SHAP values are interpreted as "contribution to the non-linear mapping" rather than "independent causal effect". The model selection (XGBoost vs Linear) tests the *non-linearity* of the composition-hardness map, not the independent contribution of 'mass' vs 'radius'.

## Computational Feasibility

*   **Hardware**: GitHub Actions Free Tier (limited CPU, 7GB RAM).
*   **Constraints**:
    *   No GPU. XGBoost must run in CPU mode.
    *   Memory: Dataset is small (<1MB raw, <10MB processed). No memory issues expected.
    *   Time: Training XGBoost on N=100 with 5-fold CV takes seconds. Total pipeline < 1 hour.
*   **Libraries**: `scikit-learn`, `xgboost` (CPU wheels only), `shap` (CPU mode), `pdfplumber` (for literature scraping).

## Decision Rationale

1.  **Why XGBoost?** It handles non-linear relationships common in materials science and provides built-in feature importance. It is CPU-tractable for small N.
2.  **Why CLR Transform?** Compositional data (sums to 1) violates assumptions of standard regression (spurious correlation). CLR maps data to Euclidean space, satisfying FR-014.
3.  **Why Bootstrap?** With N < 100, asymptotic normality assumptions for CIs are weak. Bootstrap (1000 resamples) provides empirical CIs without distributional assumptions.
4.  **Why Literature Aggregator?** No verified open API exists. The 'Verified Literature Corpus' ensures reproducibility and traceability.
