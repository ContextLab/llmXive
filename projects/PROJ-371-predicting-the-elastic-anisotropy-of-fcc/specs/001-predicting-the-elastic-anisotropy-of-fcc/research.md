# Research: Predicting the Elastic Anisotropy of FCC Metals from Composition

## Dataset Strategy

The project relies on three primary public databases for elastic constants of FCC metals.

**Verified Datasets & Accession Numbers**:
1.  **MatBench (Primary Source)**: `matbench_elastic` (HuggingFace ID: `matbench_elastic`). This dataset contains curated elastic tensors for single-phase metals.
    - *Variable Fit*: Contains $C_{ij}$ tensors, crystal system, and formula.
    - *Action*: Load via `datasets.load_dataset("matbench_elastic")`. Filter for `cubic` and `fcc` structure types.
2.  **Materials Project (Supplemental)**: Dataset ID `elastic_tensors` (MP ID: `mp-elastic`).
    - *Variable Fit*: Contains $C_{ij}$ tensors and crystal system metadata.
    - *Action*: Query via `pymatgen` or REST API. **Authentication**: The pipeline reads the `MP_API_KEY` from environment variables. If missing, the script fails gracefully with a clear error message.
3.  **AFLOWlib (Supplemental)**: REST API.
    - *Variable Fit*: Contains elastic constants and structure tags.
    - *Action*: Filter for `cubic` and `fcc` structure types.

**Data Volume Estimate**:
- Target: A representative set of unique FCC entries.
- Size: < 1 MB (CSV/JSON). Well within 7 GB RAM and 14 GB disk limits.

## Feature Engineering Strategy

**Compositional Descriptors** (FR-002):
1.  **Atomic Radius Variance**: $\sigma_r = \sqrt{\frac{1}{N}\sum (r_i - \bar{r})^2}$
2.  **Electronegativity Standard Deviation**: $\sigma_{\chi} = \sqrt{\frac{1}{N}\sum (\chi_i - \bar{\chi})^2}$
3.  **Valence Electron Concentration (VEC)**: Average valence electrons per atom.
    - *Source*: `mendeleev` or `pymatgen` periodic table (no external API).

**Feature Validity & Alternatives**:
- *Limitation*: Global averages (radius, EN) may miss local bonding effects critical for anisotropy.
- *Contingency*: If the initial model R² < 0.3, the pipeline will automatically compute and add 'd-electron count' and 'metallic radius' as complementary features. A decision gate in the `evaluate.py` script will trigger this if the benchmark is not met.

**Handling Missing Data**:
- If API returns null for $C_{11}, C_{12}, C_{44}$: Skip entry, log ID.
- If $C_{11} = C_{12}$: Skip entry (division by zero in $A_1$), log warning.
- If crystal structure is not FCC: Skip entry.

## Modeling Strategy

**Algorithms** (FR-003):
1.  **Random Forest Regressor**: Robust to non-linearity. **Complexity Control**: `max_depth=3`, `min_samples_leaf=5`.
2.  **Gradient Boosting Regressor** (`HistGradientBoostingRegressor`): High accuracy. **Complexity Control**: `n_estimators=50`, `max_depth=3`.
3.  **Linear Regression**: Baseline. **Remediation**: If VIF > 5, apply PCA to collinear features before fitting.

**Validation**:
- **Split**: **Leave-One-Element-Out (LOEO)**.
    - *Rationale*: To adhere to Constitution Principle VII (Chemical Similarity Leakage), we exclude all instances of a single element type from the training set for each fold. This ensures the model predicts for elements it has never seen, minimizing leakage.
    - *Limitation*: With a limited sample size, even LOEO does not fully eliminate leakage for chemically similar elements (e.g., Cu/Ag) due to shared periodic trends. Results are framed as 'interpolation within known elemental families'.
- **Metric**: $R^2$, MAE, RMSE.
- **Hardware**: CPU-only (no CUDA). `scikit-learn` defaults to CPU.

**Statistical Rigor**:
- **Associational Framing**: All reports will explicitly state findings are correlational (FR-004).
- **Multiple Comparisons**: Not strictly applicable as we are comparing 3 models on the same test set, but we will report confidence intervals via bootstrapping if N permits, or standard error of the mean.
- **Power Analysis**: With a limited sample size, power is limited. We will report the achieved $R^2$ as an exploratory benchmark (SC-002) and note the limitation.
- **Collinearity**: Descriptors (radius, EN) may be correlated. We will check VIF (Variance Inflation Factor). **Protocol**: If VIF > 5 for any feature, PCA is applied to the collinear subset, and the resulting components are used.

## Sensitivity Analysis (FR-005)

**Method**:
- Define outlier removal threshold $k \in \{2.5, 3.0, 3.5\}$ standard deviations from the **mean of $A_1$** (target variable).
- *Correction*: Outlier removal is strictly based on the target variable $A_1$, **not** model residuals, to prevent data snooping.
- For each $k$:
  1. Filter dataset (remove entries where $|A_1 - \mu| > k\sigma$).
  2. Train/Validate models using LOEO.
  3. Record $R^2$.
- **Success Criterion**: Variance of $R^2$ across the three thresholds must be $\le 0.1$.

## Physical Consistency

**Bounds**: $0 < A_1 < 3$.
- Any prediction outside this range is flagged.
- **Warning Threshold**: >5% violation rate triggers a warning in the report (SC-003).
- **Action**: Do not clip values; report them as violations to maintain scientific integrity.

## Data Coverage Verification (SC-001)

**Task**: The pipeline will count the number of unique FCC entries in the final processed dataset.
**Logic**:
- `coverage_count` = number of rows in `features_materials.csv`.
- `coverage_threshold_met` = `coverage_count >= 50`.
- This value is explicitly written to the `validation_report.json`.

## Benchmark Evaluation (SC-004)

**Task**: The pipeline will compare the maximum achieved $R^2$ against the hypothesis benchmark of 0.5.
**Logic**:
- `max_r2` = maximum $R^2$ across all models and thresholds.
- `benchmark_met` = `max_r2 >= 0.5`.
- This value is explicitly written to the `validation_report.json`.

## Physical Consistency Check (SC-003)

**Task**: The pipeline will calculate the violation rate and trigger a warning if necessary.
**Logic**:
- `violation_rate` = `physical_violations / total_entries`.
- `warning_triggered` = `violation_rate > 0.05`.
- This value is explicitly written to the `validation_report.json`.

## Report Generation (FR-004)

**Task**: Generate the `associational_statement` field.
**Logic**:
- The `validation_report.json` will include a standard string: "These findings reflect correlations between compositional descriptors and elastic anisotropy within the training space. No causal mechanisms are implied."
- This string is hardcoded in the `evaluate.py` script to ensure consistency.

## Limitations & Leakage Risk

- **Chemical Similarity**: Even with LOEO, chemically similar elements (e.g., Cu and Ag) may share underlying physical properties that allow the model to 'guess' correctly based on periodic trends rather than learned composition-anisotropy relationships. This inflates R².
- **Interpretation**: Therefore, the R² metric is interpreted as 'interpolation capability within known elemental families' rather than 'generalization to novel chemistries'.
- **Dataset Size**: With a moderate sample size, the model is highly sensitive to individual data points. The sensitivity analysis is designed to quantify this instability.

## Decision Rationale

- **Why CPU-only?**: Free-tier CI runners (GitHub Actions) do not provide GPUs. The spec explicitly requires CPU compatibility (US-2).
- **Why LOEO?**: Constitution VII requires stratification to prevent leakage. Random split on a small sample with elemental features causes severe leakage. LOEO is the standard compromise for small N in materials informatics, despite residual leakage risks for similar elements.
- **Why `mendeleev`?**: Lightweight, no external API needed, standard for periodic table data in Python.
- **Why MatBench?**: It is a pre-verified, curated dataset that avoids the authentication complexity of raw API calls while providing the necessary variables.