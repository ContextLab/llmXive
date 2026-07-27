# Research: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## 1. Scientific Context

The primary hypothesis is that individual differences in resting-state brain network topology (specifically Clustering Coefficient and Characteristic Path Length) predict the strength of neural entrainment to rhythmic stimuli. This is an observational study correlating structural graph metrics with functional entrainment metrics.

**Key Constraints**:
- **Data Source**: HCP S release (resting-state fMRI).
- **Entrainment Data**: External CSV (user-provided or simulated for validation only).
- **Sample Size**: N >= 30 required for hypothesis testing. N < 30 triggers "Data Insufficient" halt.
- **Compute**: CPU-only (2 cores, 7GB RAM) on GitHub Actions.

## 2. Dataset Strategy

The project requires two distinct data sources:
1.  **Resting-State Connectivity**: To compute topology metrics (Clustering Coefficient, Path Length).
2.  **Entrainment Metrics**: To serve as the dependent variable (Phase-Locking Values).

### Verified Datasets

Based on the provided verified list, the following datasets are available:

| Dataset Name | Description | Verified URL | Fit for Purpose |
| :--- | :--- | :--- | :--- |
| **HCP (train.csv)** | HCP data in CSV format. | `https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv` | **Partial**. A CSV file is more manageable than raw images, but we must verify it contains the required connectivity matrices or time series. |
| **HCP-flat** | HCP flat data. | `https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | **Partial**. Parquet format is efficient. Must verify column content (subject_id, connectivity matrix). |

**Critical Gap Analysis**:
The spec requires **HCP S1200 resting-state fMRI connectivity matrices** (200x200) and **rhythmic entrainment metrics** for the *same* subjects.
- The verified HCP URLs (`ramandeepsaha/hcp`, `jonxuxu/HCP-flat`) are generic HCP datasets. They likely contain demographic or basic imaging data, but **do not** guarantee the presence of pre-computed 200x200 connectivity matrices or the specific "rhythmic entrainment" behavioral metrics required by the spec.
- The spec explicitly states: "It is assumed that real-world HCP fMRI connectivity and rhythmic entrainment metrics for the same subjects may not exist in public repositories."
- **Plan**: The implementation will attempt to load the verified HCP datasets. If they lack the required connectivity matrices or if no matching entrainment CSV exists (or N < 30 after join), the system will halt with "Data Insufficient" as per FR-003.
- **No Synthetic Data for Hypothesis**: The pipeline will NOT generate synthetic entrainment data to replace missing real data. It will only generate synthetic data in `validation_mode` to verify code logic (FR-009).

### Data Acquisition Strategy

1.  **Step 1: Download HCP Subset**. Use `datasets.load_dataset` or direct download to fetch the `ramandeepsaha/hcp` or `jonxuxu/HCP-flat` dataset.
2.  **Step 2: Validate Columns**. Check for `subject_id` and a column representing connectivity (e.g., flattened matrix or pre-computed metrics). If missing, the pipeline will attempt the **Local Preprocessing Fallback** (download raw data and parcellate) or halt.
3.  **Step 3: Ingest Entrainment CSV**. The user must provide `data/raw/entrainment_metrics.csv`. If missing, the pipeline halts with "Data Insufficient".
4.  **Step 4: Join & Count**. Perform an inner join on `subject_id`. If N < 30, halt with "Data Insufficient".
5.  **Step 5: Multi-Atlas Acquisition**. If the primary HCP source only provides Schaefer data, attempt to download AAL and Power 264 connectivity matrices from the same or verified alternative sources. If unavailable, halt the sensitivity analysis with a specific error.

### Data Matching

The pipeline explicitly checks if the `subject_id`s in the HCP data match those in the entrainment CSV. If no match is found (N < 30), the system halts with "Data Insufficient". The plan acknowledges that without a matched dataset, the hypothesis is untestable, and no synthetic data will be generated to replace the missing real data.

## 3. Methodological Rigor

### Statistical Analysis Plan

1.  **Univariate Analysis**:
    - Compute Spearman correlation ($r$) between Clustering Coefficient and Entrainment.
    - Compute Spearman correlation ($r$) between Characteristic Path Length and Entrainment.
    - Null Hypothesis ($H_0$): $r = 0$.

2.  **Multiple Linear Regression (MLR)**:
    - **Gate**: ONLY executed if both univariate correlations are significant ($p < 0.05$).
    - Model: $Entrainment = \beta_0 + \beta_1(Clustering) + \beta_2(PathLength) + \epsilon$.
    - **Collinearity Check**: Calculate Variance Inflation Factor (VIF). If $VIF > 5$, flag `collinearity_warning`, **suppress MLR coefficients**, and report only univariate results.
    - **Correction**: Apply Holm-Bonferroni correction to the p-values of the two predictors. If the MLR stage is reached, the correction is applied to the **entire family of tests** (2 univariate + 2 MLR) to control the family-wise error rate.

3.  **Robustness Check (Sensitivity Analysis)**:
    - Repeat analysis using AAL and Power 264 atlases.
    - Generate a comparative bar chart showing $|r_{Schaefer} - r_{Alternative}|$.

### Power & Sample Size Justification

**Formal Power Analysis**:
The study enforces a minimum sample size of N=30 for hypothesis testing. A formal power calculation (two-tailed, alpha=0.05) was performed to determine the detectable effect size at this threshold:
- **Alpha ($\alpha$)**: 0.05 (two-tailed).
- **Sample Size (N)**: 30.
- **Test**: Spearman Rank Correlation (approximated by Pearson for power estimation).
- **Power (1 - $\beta$) to detect r=0.3**: **[deferred]**.
- **Power (1 - $\beta$) to detect r=0.45**: **[deferred]**.
- **Power (1 - $\beta$) to detect r=0.5**: **[deferred]**.

**Interpretation & Limitations**:
- **Underpowered for Small/Moderate Effects**: With N=30, the study has **limited power ([deferred])** to detect moderate correlations ($r=0.3$). Consequently, a non-significant result ($p > 0.05$) **cannot** be interpreted as evidence of no effect; it may simply reflect insufficient statistical power.
- **Exploratory Framing**: All results will be explicitly framed as **exploratory**. The "Power Warning: N < 30 (Exploratory)" flag (triggered if N < 30, but also noted as a limitation for N=30) will be included in the final report.
- **Decision Rule**: The N=30 threshold is a pragmatic minimum to ensure the correlation estimate is not entirely dominated by noise, but it is not a guarantee of high power. The study is designed to detect **large** effects ($r \ge 0.45$) with reasonable confidence (80% power) and to flag smaller effects as inconclusive.
- **No Justification for N < 30**: The system will **halt** with "Data Insufficient" if N < 30, as the power to detect any meaningful effect becomes negligible (<30%), rendering the hypothesis test statistically invalid.

### Causal Inference

- The study is **observational**. Claims will be framed as **associational** (correlation), not causal. No randomization of network topology exists.

## 4. Compute Feasibility

- **CPU-First**: The analysis involves:
    - Loading a subset of HCP data (parquet/CSV).
    - Computing graph metrics on 200x200 matrices (trivial for NetworkX).
    - Running Spearman correlations and MLR (trivial for `scipy`/`statsmodels`).
- **Memory**: 7GB RAM is sufficient for N=50 subjects with 200x200 matrices (approx 50 * [deferred] floats = 16MB).
- **Disk**: Adequate storage capacity is allocated for raw and processed data.
- **GPU**: Not required. The method does not involve deep learning or large matrix factorizations that require CUDA.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use Verified HCP URLs** | The spec requires real data. The verified list provides the only available sources. If they don't contain the specific metrics, the system halts (compliance with FR-003). |
| **No Synthetic Data for Hypothesis** | The spec explicitly forbids using synthetic data to replace missing real data for the primary hypothesis. This prevents fabrication. |
| **Validation Mode** | A separate mode is needed to test the code logic (recovering $r=0.5$) without contaminating the empirical results. |
| **Holm-Bonferroni** | Standard correction for multiple comparisons (2 predictors) in exploratory neuroscience. Applied to the full family of tests if MLR is reached. |
| **VIF Threshold (5)** | Standard threshold for detecting multicollinearity in regression. If exceeded, MLR coefficients are suppressed as per FR-004. |
| **Local Preprocessing Fallback** | Ensures FR-001 is satisfied even if pre-computed matrices are missing. |
| **Strict Halt for Data Mismatch** | Ensures the study is not run on mismatched data, which would invalidate the hypothesis. |
| **Power Threshold N=30** | Chosen as a pragmatic minimum to avoid completely underpowered tests, with explicit acknowledgment that it only provides **[deferred] power** for moderate effects ($r=0.3$) and **[deferred] power** for large effects ($r \ge 0.45$). |