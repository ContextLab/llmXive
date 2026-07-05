# Research: Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

## Overview
This research investigates the feasibility of predicting Glass Forming Ability (GFA) in metallic alloys using machine learning on thermodynamic descriptors. The study focuses on Random Forest and Gradient Boosting classifiers, with rigorous validation across chemical families and methodological diagnostics.

## Dataset Strategy

| Dataset | Source URL | Format | Variables Needed | Fit Verification |
|---------|------------|--------|------------------|------------------|
| GFA-DB (Zenodo) | ` (Hypothetical Real Example) | CSV | Composition, GFA label (or Rc) | **MISMATCH RISK**: Verify binary GFA label or continuous Rc. If missing, apply threshold (Rc < 100 K/s) or fallback to Synthetic. |
| Materials Project | ` Name or service not known)"))] (API) | JSON | Elemental composition | **MISMATCH RISK**: Requires mapping to GFA labels from GFA-DB. If GFA-DB lacks labels, cannot proceed without fallback. |

> **Critical Note**: If the verified URL is inaccessible or schema is incompatible, the pipeline falls back to a **Synthetic Dataset** generated via Inoue's rules. This synthetic data is for **development and code validation only** and is explicitly excluded from final scientific conclusions.

### Power Analysis
- **Minimum Sample Size (N)**: 150 samples required to detect an AUC of 0.70 with 80% power at alpha=0.05 (two-tailed).
- **Decision**: If the verified dataset yields N < 150, the cross-system validation is statistically underpowered. Results will be reported as **'Exploratory'** rather than confirmatory.
- **Family Split**: Requires N >= 20 samples per chemical family (Fe, Zr, etc.) for a valid cross-system split. If N < 20 in any family, the system falls back to a Stratified Random Split and reports the limitation.

### Construct Definition
- **Glass-Forming**: Defined as alloys with a critical cooling rate (Rc) < 100 K/s.
- **Binary Label**: If the source provides continuous Rc, the pipeline applies this threshold. If only binary labels exist, they are used as-is.
- **Fallback**: If neither Rc nor binary labels exist, the pipeline generates a Synthetic Fallback dataset.

## Model Strategy

- **Algorithms**: Random Forest (RF) and Gradient Boosting (GB) via `scikit-learn`.
- **Rationale**: CPU-tractable, robust to collinearity, interpretable feature importance.
- **Validation**:
 - **Primary**: 5-fold stratified CV + cross-system split (Fe-based vs Zr-based).
 - **Grouping Logic**: Samples are grouped by the primary transition metal (highest atomic fraction).
 - **Fallback**: If distinct families are insufficient (N < 20), use Stratified Random Split.
- **Metrics**: Accuracy, AUC-ROC, F1-score (for class imbalance).
- **Permutation Test**: 100 permutations of labels to ensure model performance is not due to chance or family identity alone. Requirement: Model AUC must be significantly better than permuted baseline (p < 0.05).
- **Constraints**: No GPU, ≤7 GB RAM, chunked processing if needed.

## Methodological Rigor

- **Collinearity**: Variance Inflation Factor (VIF) computed; VIF > 5 flagged. If VIF > 10, apply PCA to reduce dimensionality.
- **Threshold Sensitivity**: Sweep {0.4, 0.5, 0.6}; report FPR variation. Flag if data is synthetic.
- **Causal Framing**: All conclusions explicitly labeled "associational". If data is synthetic, append "Data Provenance: Synthetic/Unverified".
- **Power/Sample Size**: Acknowledge limitation; report as 'Exploratory' if N < 150.
- **Multiple Comparisons**: Not applicable (single primary hypothesis per model); family-wise error correction deferred if multiple tests added.

## Assumptions & Risks

| Assumption | Risk | Mitigation |
|------------|------|------------|
| Zenodo GFA-DB accessible and compatible | Dataset unavailable or schema mismatch | Flag as blocking gap; fallback to Synthetic for code validation only. |
| Elemental property tables static | Version drift | Use fixed snapshot; record version in metadata. |
| Binary GFA label exists (or Rc) | Continuous GFA requires thresholding | Apply Rc < 100 K/s threshold; if missing, fallback to Synthetic. |
| Class balance sufficient | Imbalance reduces F1 | Stratified sampling; report F1 alongside accuracy. |
| Distinct chemical families exist | Homogeneous dataset | Fallback to Stratified Random Split; report limitation. |

## Computational Feasibility

- **RAM**: ≤7 GB via chunked processing (chunksize=1000, dynamic adjustment).
- **Runtime**: ≤6h via efficient `scikit-learn` implementation.
- **No GPU**: Confirmed; `scikit-learn` CPU-only.
- **Libraries**: `pandas`, `numpy`, `scikit-learn`, `pyyaml`, `requests` (all CPU-wheel compatible).

## Conclusion

This research plan is contingent on obtaining a verified dataset with composition and GFA labels. Once data is secured, the pipeline will compute descriptors, train models, and perform cross-system validation with rigorous diagnostics. All findings will be framed as associational. If the dataset is insufficient (N < 150 or N < 20 per family), results will be reported as 'Exploratory' or 'Not Applicable' respectively.