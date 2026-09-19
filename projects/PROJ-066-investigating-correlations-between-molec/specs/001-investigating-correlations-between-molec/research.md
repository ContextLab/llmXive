# Research: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

## 1. Research Question & Hypothesis

**Primary Question**: Can fundamental 2D molecular descriptors (specifically logP and TPSA) accurately predict experimental drug-likeness scores (oral bioavailability, apparent permeability, clearance)?

**Hypothesis**: There is a strong positive correlation (Pearson r ≥ 0.6) between calculated logP/TPSA and oral bioavailability. Random Forest models will rank these descriptors within the top 3 feature importances.

**Primary Endpoint**: Oral Bioavailability. This is the primary hypothesis test. Correlations for Papp and Clearance are secondary and will be adjusted for multiple comparisons (Bonferroni correction) to control the Family-Wise Error Rate.

## 2. Dataset Strategy

### 2.1 Source Selection
The project requires a dataset containing raw SMILES strings and experimental values for bioavailability, permeability, or clearance. We will use the canonical ChEMBL 33 release to ensure reproducibility and adherence to the "Data Hygiene" principle.

**Selected Dataset**: ChEMBL Release 33 (EMBL-EBI)
* **Source Type**: SQLite Database (Direct Download)
* **Verified URL**: `
* **Verification Step**: The `download.py` script will first perform a `HEAD` request (or `curl -I`) to verify the file exists at the canonical path. If the file is missing or returns 404, the pipeline halts with a clear error: "Canonical ChEMBL 33 source unavailable."
* **Coverage Check**: The database contains `molecule_dictionary`, `assay_dictionary`, and `bioactivity_data` tables. We will join these to extract molecules with `standard_type` matching our targets.

**Exclusion of Third-Party Sources**: We explicitly reject pre-curated or "cleaned" third-party datasets (e.g., user-uploaded Hugging Face repos) for this study. The provenance of their cleaning logic is opaque, and their descriptors may not align with the project's specific RDKit sanitization pipeline (FR-002).

### 2.2 Data Access & Feasibility
* **Access Method**: The SQLite file (several gigabytes) will be downloaded to `data/raw/`. It will be opened with `sqlite3` or `pandas.read_sql` in chunks/streaming mode to avoid loading the entire database into RAM.
* **Feasibility**: The file size fits within the available RAM limit when accessed via streaming queries.
* **Variable Fit**:
 * *Predictors*: We will calculate logP, TPSA, MW, etc., **freshly** from the raw SMILES string in the database. We will **not** use any pre-calculated columns if they exist, to ensure ground truth consistency.
 * *Outcomes*: We will extract `standard_value` where `standard_type` matches our targets.
 * **Target Variable Mapping**: To prevent 0-row results due to strict string matching, we will map synonyms to our target types:
 * **Bioavailability**: `standard_type` IN ('Bioavailability', 'Fraction absorbed', '%F', 'F%')
 * **Permeability**: `standard_type` IN ('Apparent permeability', 'Papp', 'Permeability')
 * **Clearance**: `standard_type` IN ('Clearance', 'CL', 'Intrinsic clearance')
 * **Data Independence Check**: We will verify that the `standard_value` is an experimental measurement and not a derived value based on the predictors (e.g., ensuring no circular derivation from logP).

### 2.3 Data Preprocessing Strategy
1. **Sanitization**: For every extracted SMILES, we will run RDKit `SanitizeMol` (FR-002) to remove salts, fix valences, and validate structure. Invalid molecules are logged and excluded.
2. **Filtering**: Remove rows with `NaN` in target columns.
3. **Deduplication**: Group by canonical SMILES.
 * If assay dates differ: Keep the most recent.
 * If dates match: Average the experimental values.
4. **Pre-Sampling Validation**: Before sampling, we query the count of valid rows for each target type.
 * If a target has < 1,000 rows, that target is **excluded** from analysis with a warning: "Insufficient data for [Target] (N < 1000)."
 * This prevents the pipeline from crashing during stratification due to sparse targets.
5. **Sampling**: Apply stratified random sampling to cap the dataset at [deferred] molecules (FR-008).
 * **Stratification Logic**: Since targets are continuous, we bin the `standard_value` into a small, fixed number of quantile bins determined by the unique value count.
 * If `n_unique` < 2 (all values identical), stratification is skipped for that target (treated as a single class).
 * This robust logic prevents crashes on low-cardinality targets.

## 3. Methodology

### 3.1 Descriptor Calculation
* **Tools**: `rdkit.Chem.Descriptors`
* **Descriptors**: TPSA, logP (MolLogP), Molecular Weight (MW), Number of Rotatable Bonds, H-Bond Donors, H-Bond Acceptors, Ring Count.
* **Ground Truth**: All descriptors are calculated **freshly** from the raw SMILES string using the project's specific RDKit version. No pre-calculated values are used. This ensures construct validity and independence from any dataset-specific preprocessing artifacts.

### 3.2 Model Training
* **Split**: 80/20 Train/Test, stratified by the binned target variable. Seed = 42.
* **Models**:
 1. **Linear Regression**: Baseline for linear correlation.
 2. **Random Forest Regressor**: `n_estimators=100`, `max_depth=10` (to prevent overfitting and manage memory).
* **Hardware**: CPU-only (parallel execution enabled, capped to 2 cores via environment variable).

### 3.3 Evaluation Metrics
* **RMSE**: Root Mean Squared Error.
* **Pearson Correlation (r)**: Coefficient of correlation between predicted and experimental values.
* **Feature Importance**: Ranked list from Random Forest.
* **Multiple Comparisons**: Since we test multiple targets, we will apply Bonferroni correction to the p-values of the correlation tests. The primary conclusion is drawn from the Bioavailability result.

### 3.4 Statistical Rigor & Limitations
* **Power Analysis**: The sample size is sufficient for regression. The pre-sampling check ensures we only proceed if N > 1000 per target.
* **Collinearity**: logP and MW are often correlated. The plan acknowledges this; the Random Forest will handle non-linear interactions, but the Linear Regression coefficients will be interpreted with caution.
* **Causal Claims**: The study is observational. Claims will be framed as "predictive associations," not causal mechanisms.

## 4. Compute Feasibility & Escape Hatch

* **CPU Strategy**: All steps (descriptors, LR, RF) are CPU-tractable. The 15k sample size ensures < 1GB RAM usage during training.
* **GPU Escape Hatch**: Not required for this specific methodology. If the user later requests deep learning (e.g., GNNs), the plan would shift to a Kaggle GPU offload. For this spec, the CPU path is the primary and sufficient path.

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Dataset**: ChEMBL 33 (Official) | Canonical source, ensures reproducibility and data hygiene. |
| **Target Mapping**: Synonym list | Prevents 0-row results due to naming variations in ChEMBL. |
| **Sampling**: Pre-validation + min(10, n_unique) bins | Prevents crashes on sparse targets and ensures robust stratification. |
| **Descriptors**: Fresh calculation | Ensures ground truth independence and construct validity. |
| **Proxy Strategy**: None | Strictly restricts analysis to specified targets; no pIC50 substitution. |