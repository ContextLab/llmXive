# Research: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

## 1. Problem Definition

The goal is to predict the Glass-Forming Ability (GFA) of metallic glasses, quantified by the critical cooling rate ($R_c$). Lower $R_c$ indicates better GFA (easier to form a glass). The project aims to:
1. Ingest experimental data linking composition to $R_c$.
2. Engineer physics-based features (atomic radius, electronegativity, VEC) using Pymatgen.
3. Train regression models to predict $log_{10}(R_c)$.
4. Screen novel ternary alloys and rank them by predicted GFA with uncertainty estimates.

## 2. Dataset Strategy

### 2.1 Primary Dataset
The project relies on the **GFA (csv)** dataset.
- **Source**: ` (Direct file URL).
- **Verification**: This URL is listed in the "Verified datasets" block. The pipeline will verify the file exists and contains the required `log10_Rc` (or `Rc`) and `composition` columns.
- **Schema Check**: The pipeline must verify the presence of a `log10_Rc` column (or `Rc` to be log-transformed) and composition columns (elemental fractions). **Crucially**, if the file is a metadata index (e.g., containing only flags) and lacks these columns, the pipeline fails with an explicit error.
- **Handling**:
 - If the dataset is missing `log10_Rc`, the pipeline fails explicitly (FR-001).
 - Compositions with elements not in Pymatgen are excluded with a warning.

### 2.2 Secondary Data (Novelty Check)
- **Known Alloys List**: The spec mentions a "Known Alloys List" derived from Materials Project and literature.
- **Constraint**: No verified URL for a comprehensive "Known Alloys List" exists in the "Verified datasets" block.
- **Strategy**: The novelty check (FR-013) will:
 1. Attempt to load `data/known_alloys.csv` (a local curated file).
 2. If absent, attempt to query the Materials Project API (if `MP_API_KEY` is set).
 3. If all fail, log a warning and set `novelty_status` to `unverified_external`.
- **Rationale**: This avoids the "default to novel" error and provides a concrete fallback mechanism, satisfying the "querying" requirement as best as possible given resource constraints.

## 3. Feature Engineering Strategy

Features are derived from elemental composition using `pymatgen`:
1. **Atomic Radius**: Weighted mean and variance of atomic radii.
2. **Electronegativity**: Weighted mean and variance.
3. **Valence Electron Count (VEC)**:
 - `VEC_raw`: Sum of `element.valence_electrons` for each element.
 - `VEC_avg`: Weighted mean of valence electrons.
4. **Interaction Features**:
 - Atomic size mismatch (variance of radii).
 - Pairwise size mismatch for unique element pairs in ternary compositions (FR-002b).

**Dataset Variable Fit**: The dataset contains composition (elemental fractions) and target ($R_c$). Pymatgen provides the necessary physical descriptors. No missing variables are anticipated for the primary analysis, provided the dataset contains standard metallic elements.

## 4. Modeling Strategy

### 4.1 Algorithms
- **Random Forest Regressor**: Robust to non-linearities and feature interactions.
- **Gradient Boosting Regressor**: High predictive accuracy, sensitive to hyperparameters.
- **Bootstrapped Ensemble**: 10 independent RF models for uncertainty quantification (FR-003, FR-007).

### 4.2 Validation & Selection
- **LOCO Cross-Validation**: Split by chemical family (e.g., Zr-based, Cu-based) to ensure the model generalizes to unseen chemistries (FR-004).
- **LOCO Clustering Algorithm**:
 - **Rule**: A composition is assigned to the cluster of the element with the **highest atomic fraction**.
 - **Tie-Breaker**: If two elements have the same fraction, the element with the **higher atomic number** is chosen.
 - **Rationale**: This deterministic rule ensures reproducible fold assignment and addresses the ambiguity concern.

### 4.3 Statistical Rigor & Heteroscedasticity
- **Residual Analysis**: Perform Breusch-Pagan test (FR-010).
- **Correction**: If heteroscedasticity is detected ($p < 0.05$):
 - **Attempt**: Bin residuals by feature-space quantiles (sufficient samples per bin).
 - **Fallback**: If bins are too small (common in small datasets), fit a global log-variance model or switch to Huber loss. This ensures robustness without the instability of small-sample binning.
- **Weighing**: Weights are inversely proportional to the estimated local/global variance.

### 4.4 Domain of Applicability (DoA)
- **Method**: Convex hull of training feature space + Mahalanobis distance.
- **Curse of Dimensionality Mitigation**: To address sparsity in high-dimensional spaces, the feature space is reduced to a small set of principal components (retaining [deferred] variance) before calculating Mahalanobis distance and convex hull. This improves the validity of the Gaussian assumption.
- **Penalty**: Candidates outside DoA get a **+1.0** penalty to $log_{10}(R_c)$ before ranking (FR-009).
- **Scientific Note**: While a continuous penalty (proportional to distance) might be scientifically superior, the fixed +1.0 penalty is a strict requirement of FR-009. The plan implements the fixed penalty to satisfy the spec, acknowledging this as a known limitation that may introduce bias. The `risk_score` (Mahalanobis distance) is also output to allow downstream re-analysis without the penalty.

## 5. Screening Strategy

- **Combinatorics**: Generate all unique ternary combinations from the most abundant metallic elements (Al, Ca, Fe, Mg, Ti, Na, K, Zn, Si, Zr, Cu, Ni, Cr, Mn, V, Sn, Pb, Ag, Au, Pd, Pt, Mo, W, Nb, Ta, Hf, Y, La, Ce, Sc).
- **Prediction**: Use the best model to predict $log_{10}(R_c)$.
- **Filtering**:
 - **Relative**: Retain candidates in the bottom 10th percentile of predicted $log_{10}(R_c)$.
 - **Absolute**: Candidates must also satisfy $log_{10}(R_c) < 4.0$ (or the dataset's 10th percentile, whichever is stricter) to ensure physical viability.
- **Ranking**: Sort by ascending $log_{10}(R_c)$ (lowest cooling rate = best GFA).
- **Confidence Intervals**: Derived from the [deferred] and [deferred] percentiles of the 10 bootstrapped predictions.
- **Novelty Check**: Query `data/known_alloys.csv` if present. If not, set `novelty_status` to `unverified_external`.

## 6. Compute Feasibility Analysis

- **Hardware**: GitHub Actions Free Tier (multiple CPU, ample RAM).
- **Memory**:
 - Dataset size: Small (<100MB).
 - Feature matrix: a moderate number of rows × a moderate number of features. Negligible.
 - Combinatorial generation: $\binom{30}{3} \times 3!$ (approx. [deferred] combinations). Storing features for a large-scale dataset is feasible within a compact memory footprint.
 - Model training: Random Forest on <50 features and <1000 samples is instant on CPU.
 - Bootstrapping (10 models): 10x training time, still < 1 minute.
- **Time**: Total pipeline estimated < 1 hour. Well within 6-hour limit.
- **GPU**: Not required. All libraries (`scikit-learn`, `pymatgen`, `pandas`) have CPU wheels.

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset missing `log10_Rc` | Pipeline failure | Explicit check in `download.py`; fail fast with clear error. |
| Pymatgen missing element | Data loss | Log warning, exclude row, continue. |
| No candidates below threshold | Empty output | Output empty CSV with header; log message. |
| Novelty list unavailable | False "novel" claims | Flag as "unverified_external" in `verification_requests.json`. |
| Heteroscedasticity | Biased model | Implement weighted retraining with binning safeguards or global fallback (FR-010). |
| Spec vs. Science Conflict (DoA) | Model bias | Implement +1.0 penalty as per FR-009; document as known limitation; output `risk_score`. |
| Dimensionality in DoA | False flags | Use PCA reduction before Mahalanobis calculation. |
