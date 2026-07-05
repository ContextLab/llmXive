# Research: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Overview

This document details the research strategy, dataset selection, methodological rationale, and risk mitigation for implementing the feature specification. It addresses the core question: *Can processing parameters (rolling speed, temperature, reduction ratio) predict crystallographic texture coefficients across alloy families?*

**Decoupling Note**: This research plan explicitly separates **Pipeline Validation** (synthetic data) from **Scientific Discovery** (real data). Synthetic data is used solely to verify code logic and data flow; it cannot validate the physical hypothesis of "how parameters influence texture."

## Dataset Strategy

| Dataset Source | Verified URL | Status | Usage |
|----------------|--------------|--------|-------|
| Materials Project | NO verified source found | ❌ Unavailable | Fallback to synthetic |
| Open Materials Database (OMDB) | https://huggingface.co/datasets/colabfit/JARVIS_OMDB/resolve/main/co/co_0.parquet | ⚠️ Partial | May contain composition but lacks paired rolling/texture data; will be checked for required fields. |
| NIST Materials Data Repository | NO verified source found | ❌ Unavailable | Fallback to synthetic |
| Synthetic Generator (FR-011) | N/A (internal) | ✅ Required | Primary data source if real data insufficient; validates pipeline logic only. **Must generate raw ODF files.** |

**Rationale**: The spec explicitly states that public datasets likely lack paired rolling-process and texture data. The verified dataset block confirms no direct source for ODF/rolling pairs. OMDB contains compositional data but not the required processing-texture pairs. Therefore, the synthetic generator (FR-011) is the primary data source, with real data checked as a fallback. Synthetic data is strictly for pipeline validation (code logic, data flow), not scientific hypothesis testing.

## Methodology

### 1. Data Ingestion & Validation (FR-001)
- Attempt to load real data from OMDB (if fields match: rolling_speed, temperature, reduction_ratio, ODF/pole-figure).
- If < 50 paired samples per alloy family, trigger synthetic generator.
- **Synthetic Requirement**: The generator MUST produce raw diffraction/ODF files (e.g., synthetic .txt or .xml pole figures) to satisfy Constitution Principle VI and FR-003.
- Validate ≥ 50 samples/family; abort if total < 50/family.

### 2. Preprocessing (FR-002)
- **Unit Standardization**: Convert all units to SI (°C, m/s, %).
- **Imputation**: Median imputation for missing numeric values.
- **Outlier Removal**: 3σ threshold; log removed samples.
- **Feature Engineering**: 
  - **Forced Confounders**: Alloy composition and prior history are **always included** as inputs, regardless of VIF, to control for confounding.
  - **Derived Features**: Derive strain rate and Zener-Hollomon parameter (Z) for **logging and physics context only**.
  - **Collinearity Check**: Compute VIF for all features. 
    - **Rule**: If a derived feature (e.g., Z) has VIF ≥ 5, it is **excluded from the model training** to prevent multicollinearity artifacts in feature importance. 
    - **Exception**: Known confounders (composition, history) are **not removed** even if VIF ≥ 5, as they are mandatory for causal adjustment (though causal claims are limited).
  - **Final Input Set**: Rolling speed, temperature, reduction ratio, composition, prior history. (Z is excluded from model training).

### 3. Texture Descriptor Computation (FR-003)
- Use `pymtex` to compute ODF peak intensities (MRD) for {100}, {110}, {111} planes from raw pole-figure/ODF files.
- **Fallback**: If `pymtex` is unavailable, use spherical-harmonic approximation with equivalence criterion (±5% MRD on reference).
- For synthetic data, verify computed descriptors match generator values within ±5% MRD.

### 4. Model Training (FR-004)
- **Algorithm**: Multi-output `RandomForestRegressor` (scikit-learn) for all three texture coefficients jointly.
- **Tuning**: Grid search over `n_estimators` (50–200), `max_depth` (5–20) via 5-fold CV.
- **Constraint**: ≤ 30 min wall-clock time on 2 CPU cores.
- **Seeds**: Fixed random seed for reproducibility (Constitution Principle I).

### 5. Evaluation & Reporting (FR-005, FR-009, FR-010)
- **Metrics**: R², MAE, RMSE per texture coefficient; reported per alloy family.
- **Importance**: Permutation importance ranking; visualize as `importance_plot.png`. **Interpretation**: Scores reflect "predictive contribution" only, not "physical influence" (causal claims require real data and causal design).
- **Sensitivity Analysis**: Sweep R² thresholds (e.g., 0.4–0.6) to assess impact; for synthetic data, test stability across ≥5 random seeds (variance metric).
- **Edge Cases**: 
  - Out-of-range predictions: Flag and log warning; still produce prediction.
  - Missing texture data: Skip sample; log omission.
  - >20% missing data: Abort training with error.

### 6. Synthetic Data Generator (FR-011)
- **Inputs**: Rolling speed, temperature, reduction ratio, alloy composition, prior history.
- **Outputs**: Texture coefficients (with Gaussian noise σ=0.05 MRD), **synthetic ODF/pole-figure files** (raw data), and derived features.
- **Physical Relationships**: Simulate known physics (e.g., higher reduction → stronger texture; temperature dependence).
- **Power Analysis**: Calculate minimum detectable effect size for N=50/family; log warning if |r| > 0.3 (underpowered).

## Causal Inference Strategy & Statistical Rigor

- **Causal Claims**: None made for synthetic data. For real data, the model is purely **associational**. To claim "influence" or "drivers," a causal design (e.g., instrumental variables, propensity scoring) would be required, which is outside the current scope due to data limitations. Feature importance is strictly interpreted as "predictive contribution."
- **Multiple Comparisons**: Not applicable (single model, three outputs); however, per-family metrics are reported separately.
- **Power Analysis for Real Data**: 
  - If real data is found, a formal power analysis will calculate the Minimum Detectable Effect Size (MDES) for the given N.
  - If N < 50, the study is flagged as underpowered for small effects (|r| < 0.3). Success criteria (SC-001) for real data will be interpreted as "associational strength" rather than "scientific proof."
- **Measurement Validity**: `pymtex` is community-standard; synthetic data validated against generator ground truth.
- **Collinearity**: VIF check ensures no spurious feature importance for derived features. Zener-Hollomon is excluded from training to avoid perfect multicollinearity.

## Success Criteria Validation

- **SC-001 (Synthetic)**: R² ≥ 0.50 is a **Pipeline Sanity Check** only. It verifies the model can learn the generator's function. It does **not** validate the physical hypothesis.
- **SC-001 (Real)**: If real data is available, validation requires comparison against a **Physics-Based Baseline** (e.g., Taylor model) or a **Null Model** that preserves variance structure. If no physics baseline exists, validation is limited to "associational strength" (R²) and "stability," with explicit acknowledgment that causal claims cannot be made.
- **SC-002**: At least one processing variable attains a permutation-importance score ≥ 0.10 for every AlloyFamily (interpreted as predictive contribution).
- **SC-003**: End-to-end pipeline execution completes within 6 hours, using ≤ 2 CPU cores and ≤ 6 GB RAM on the GitHub Actions runner.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| No real data available | Synthetic generator (FR-011) ensures pipeline execution; clearly labeled as non-scientific. |
| `pymtex` dependency failure | Fallback to spherical-harmonic approximation; equivalence criterion enforced. |
| CI resource exhaustion | Sample data to ≤ 7GB RAM; limit CV folds; monitor runtime. |
| Model underperforms (R² < 0.5) | Sensitivity analysis; report stability; no scientific claims made for synthetic data. |
| Missing critical features | Power analysis warns; synthetic generator includes confounding variables. |
| Multicollinearity in derived features | Exclude Zener-Hollomon from training; force inclusion of confounders. |

## Conclusion

This research plan prioritizes pipeline reproducibility and data hygiene over scientific hypothesis validation (which requires real paired data and causal design). Synthetic data enables full end-to-end testing under CI constraints. All methodological choices are justified by the spec and constitution, with explicit acknowledgment of limitations regarding causal inference and statistical power.