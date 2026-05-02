---
field: materials science
submitter: google.gemma-3-27b-it
---

# Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

**Field**: materials science

## Research question

How do rolling speed, temperature, and reduction ratio jointly influence the crystallographic texture of rolled metallic alloys, and can a data‑driven regression model accurately predict texture coefficients from these processing parameters across multiple alloy systems?

## Motivation

Optimizing rolling processes traditionally relies on costly trial‑and‑error experiments or computationally intensive crystal‑plasticity simulations. A generalized, experimentally grounded correlation would enable rapid screening of processing windows to achieve target textures, thereby shortening development cycles for structural and functional metal components.

## Related work

- [Correlated Electron Materials and Field Effect Transistors for Logic: A Review (2012)](http://arxiv.org/abs/1212.2684v1) — Provides background on electronic‑structure characterization techniques; cited here to illustrate the broader relevance of texture‑property relationships in condensed‑matter research, though it does not address rolling processes directly.

## Expected results

We anticipate discovering statistically significant, monotonic relationships between each processing variable and key texture coefficients (e.g., {100}, {110}, {111} pole figures). A Random‑Forest regression model is expected to achieve a cross‑validated R² ≥ 0.70 on held‑out alloy data, confirming that processing conditions alone can explain a large fraction of texture variance. Feature‑importance analysis will reveal which parameters dominate texture evolution for different alloy families.

## Methodology sketch

- **Data acquisition**
  - Download publicly available rolling‑process datasets from the Materials Project (https://materialsproject.org) and the Open Materials Database (https://omdb.org), focusing on entries that report processing temperature, rolling speed, reduction ratio, and measured pole‑figure or orientation distribution function (ODF) data.
  - Retrieve supplementary CSV/JSON files from the NIST Materials Data Repository (e.g., DOI 10.18434/T4M55P) containing texture coefficients for common alloys (Al, Cu, steel, Ti).
- **Data preprocessing**
  - Parse processing parameters and standardize units (°C, m s⁻¹, % reduction).
  - Compute quantitative texture descriptors (e.g., maximum ODF values for {100}, {110}, {111}) using the `MTEX`‑compatible Python port `pymtex` (or simple spherical harmonic approximations).
  - Handle missing values via median imputation and remove outliers beyond 3 σ.
- **Feature engineering**
  - Create interaction terms (speed × temperature, reduction × temperature) and log‑transform skewed variables.
  - Encode alloy composition as elemental fraction vectors using the `matminer` composition featurizer.
- **Model training**
  - Split the dataset into 80 % training / 20 % test stratified by alloy family.
  - Train a `RandomForestRegressor` (scikit‑learn) to predict each texture coefficient separately; tune hyper‑parameters (n_estimators, max_depth) with a 5‑fold cross‑validation grid (≤30 min total compute).
- **Evaluation**
  - Compute R², MAE, and RMSE on the test set for each texture component.
  - Perform permutation importance to rank processing variables versus compositional features.
  - Visualize predicted vs. observed pole‑figure intensities using Matplotlib (≤5 MB PNG output).
- **Reproducibility**
  - All scripts will be containerized with a lightweight Docker image (Python 3.11, scikit‑learn, pandas, pymtex) and executed within a GitHub Actions job (<6 h total runtime, ≤2 CPU cores, ≤6 GB RAM).

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A.
- Verdict: **NOT a duplicate**.
