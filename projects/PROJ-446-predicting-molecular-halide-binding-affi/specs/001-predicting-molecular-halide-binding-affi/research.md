# Research: Predicting Molecular Halide Binding Affinities

## Executive Summary

This research investigates the ability of machine learning models (Random Forest, Gradient Boosting) to predict halide binding affinities based on molecular descriptors. The study relies on experimental data from NIST and PubChem, with a robust fallback to physics-constrained simulated data if real-world data is insufficient. The analysis is strictly associational, employing host-molecule stratified cross-validation to prevent leakage and bootstrap confidence intervals to assess performance differences across halide ions.

**Critical Fallback**: If real data is insufficient (<50 hosts with ≥3 halides), the system switches to **Single-Halide Prediction Mode** (FR-011). In this mode, the comparative analysis (US-4) is **ABORTED** as the `halide_identity` variable has no variance. All results are flagged as "Simulated Data Mode" and do not answer the primary research question of halide selectivity.

## Dataset Strategy

### Verified Datasets

The following datasets have been verified for reachability and format. They are the ONLY sources used for data ingestion.

| Source | Description | Verified URL | Status |
|:--- |:--- |:--- |:--- |
| **NIST (Parquet)** | Cybersecurity embeddings (Not directly usable for chemistry, but verified source for NIST structure). | ` | Verified (Format OK, Content Mismatch) |
| **WebBook (CSV)** | Book dataset (Not direct binding constants, but verified WebBook proxy). | ` | Verified (Format OK, Content Mismatch) |
| **PubChem (Parquet)** | Canonicalized PubChem molecules (a large-scale dataset). | ` | Verified (Format OK, Missing Binding Data) |
| **SMILES/Descriptors** | ChEMBL-2025 with RDKit descriptors. | ` | **Primary Candidate** (Has SMILES + Descriptors) |

**Critical Note on Data Availability**:
The "Verified datasets" block does **not** contain a direct dataset of *experimental halide binding constants* (log K) paired with host SMILES and halide identity. The available datasets (NIST, PubChem, ChEMBL) provide molecular structures and general properties but lack the specific `binding_constant` and `halide_identity` columns required for the primary research question.

**Consequence**:
Per **FR-011**, the system **MUST** trigger the simulated data fallback. The pipeline will:
1. Attempt to scrape NIST/PubChem for specific binding constants (as per FR-001).
2. If no records are found (expected), log the warning: `"WARNING: Insufficient data (<50 hosts). Comparative analysis aborted. Switching to single-halide prediction mode with simulated data."`
3. Generate a simulated dataset using the formula: `log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)`. **Note**: This formula generates data for a **single halide** (the most abundant one found or a default). It does **not** include a term for `halide_identity` because the fallback is single-halide mode.
4. Proceed with the analysis in "Simulated Data Mode", explicitly flagging all results as non-comparative and associational.

**Dataset-Variable Fit**:
- **Required**: Host SMILES, Halide Identity, Binding Constant, Solvent.
- **Available (Real)**: Host SMILES, General Descriptors. (Missing: Binding Constant, Halide Identity).
- **Available (Simulated)**: Host SMILES, Generated Descriptors, Generated Binding Constant (physics-constrained, single-halide).
- **Fit**: The real data **fails** the variable fit. The simulated data **passes** the variable fit for a single-halide model but **fails** the "comparative selectivity" requirement. The plan explicitly accounts for this failure mode by aborting the comparative analysis.

## Methodology

### 1. Data Ingestion & Preprocessing
- **Source**: NIST/PubChem scraping (FR-001) -> Fallback to Simulation (FR-011).
- **Filtering**: Retain only hosts with ≥3 halide measurements (if real data exists) OR generate synthetic hosts with 1 halide (if simulated).
- **Solvent**: Filter for acetonitrile, chloroform, DCM.
- **Validation**: Check for valid SMILES; exclude invalid records.

### 2. Feature Engineering
- **Tools**: `rdkit` (Python).
- **Descriptors**:
 - **ECFP4 Fingerprints**: Binary vectors for structural substructures.
 - **RDKit Descriptors**: Molecular weight, LogP, TPSA, **Gasteiger Charge Sum** (for `charge_density`), **Molecular Volume** (for `cavity_volume`).
- **Standardization**: Z-score normalization for continuous descriptors.

### 3. Model Training
- **Algorithms**: Random Forest (`sklearn.ensemble.RandomForestRegressor`), Gradient Boosting (`sklearn.ensemble.GradientBoostingRegressor`).
- **Validation**: **GroupKFold** (5 folds) grouping by `host_id` to prevent data leakage (FR-004, Constitution VII).
- **Hyperparameters**: Default scikit-learn values (FR-005) to ensure reproducibility and fit within CPU budget.
- **Compute**: CPU-only. No CUDA.
- **Fallback Path**: If `data_mode == 'Simulated'`, train on the single available halide. Do not attempt to split by halide.

### 4. Statistical Analysis
- **Metric**: R² and RMSE per halide ion.
- **Comparison**: **Bootstrap Confidence Intervals** (10,000 resamples) for pairwise differences in mean R²/RMSE (FR-009).
 - *Condition*: Only computed if `data_mode == 'Real'` AND `halide_count >= 2`.
 - *Fallback*: If `data_mode == 'Simulated'` OR `halide_count < 2`, **skip** pairwise comparison. Report `comparative_analysis_aborted: true`.
- **Stability**: Coefficient of Variation (CV) of feature importance across bootstrap resamples (FR-006).
- **Physical Plausibility**: Check sign of top feature coefficient against Coulombic attraction (FR-013).

### 5. Reporting
- **Disclaimer**: All findings are **associational** (FR-008).
- **Underpowered Check**: If N < 10 per halide, report CI width as "wide" and avoid significance claims (FR-012).
- **Simulated Data Warning**: Explicitly state that if simulated data was used, the results do not reflect real-world halide selectivity.

## Decision Rationale: Compute & Data

### Compute Feasibility
- **Method**: Random Forest and Gradient Boosting on <1000 samples.
- **Feasibility**: These methods are CPU-tractable and fit within 7 GB RAM / 6 hours.
- **GPU Escape Hatch**: Not required. No deep learning models are planned.

### Data Strategy Rationale
- **Real Data**: Unavailable in verified sources. Scraping NIST/PubChem is the required first step (FR-001), but the plan anticipates failure.
- **Simulated Data**: Required to satisfy FR-011 and allow the pipeline to demonstrate its full logic (training, analysis, reporting) even when the primary research question cannot be answered with real data.
- **Risk**: The results will be based on simulated data. The plan explicitly flags this in the output to prevent scientific misconduct. **Note**: The simulation formula `log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)` is a synthetic proxy for pipeline validation only. It does not validate the model against real-world physics or experimental noise.

## Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No real data found** | High (Primary question unanswerable) | Trigger FR-011 simulation; flag all outputs as "Simulated Data Mode"; abort comparative analysis. |
| **Data Leakage** | High (Invalid R²) | Enforce `GroupKFold` by `host_id`; verify split in tests. |
| **Small Sample Size** | Medium (Wide CIs) | Use Bootstrap CI instead of parametric tests; report "wide" CI if N < 10. |
| **Collinearity** | Medium (Unstable features) | Report CV; flag features with CV ≥ 0.3 as unstable. |
| **Single-Halide Mode** | High (Comparative analysis impossible) | Explicitly set `comparative_analysis_aborted: true` and report "N/A" for halide differences. |
