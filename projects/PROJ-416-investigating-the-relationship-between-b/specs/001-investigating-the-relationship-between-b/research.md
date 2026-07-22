# Research: Investigate Brain Network Dynamics and VR Therapy Response

## Dataset Strategy

The project relies on open, directly-downloadable neuroimaging datasets. Per the "Verified datasets" block, the following sources are identified:

| Dataset | Verified URL / ID | Relevance to Study |
| :--- | :--- | :--- |
| **OpenNeuro ds001971** | `https://openneuro.org/datasets/ds001971` (Primary Candidate) | **Primary Candidate**. Contains resting-state fMRI data and clinical anxiety scores (GAD-7/HAM-A) for pre/post treatment. **Verification**: Must confirm presence of paired pre/post scores in metadata. If missing, pipeline halts (FR-011). |
| **OpenNeuro ds000232** | `https://openneuro.org/datasets/ds000232` (Fallback) | **Fallback**. Known to contain rs-fMRI and anxiety data. Used if ds001971 lacks required variables. |
| **GAD-7** | NO verified source found. | **Instrument Only**. The dataset must contain GAD-7 scores. The URL for GAD-7 itself is not needed, but the *dataset* must include these scores. |
| **HAM-A** | `https://huggingface.co/datasets/hamazi/nva-danganneko/resolve/main/cham221.zip` (Note: Likely unrelated to clinical HAM-A) | **Caution**. The provided HAM-A URL appears to be a game-related dataset (Azur Lane). **Action**: The pipeline will NOT use this URL for clinical HAM-A scores. It will rely on the OpenNeuro dataset's internal metadata for clinical scores. If OpenNeuro lacks HAM-A, the pipeline halts. |
| **AND** | `https://huggingface.co/datasets/Manusagents/...` | **Irrelevant**. Cybersecurity signals. Not used. |
| **ASSOCIATIONAL** | NO verified source found. | **Concept Only**. Not a dataset. |

**Decision**: The project will attempt to use the **OpenNeuro ds001971** dataset as the primary source.
- **Validation**: Before any download, the `DataValidator` service will inspect the dataset metadata (or a small sample) to confirm the existence of `pre_treatment_score`, `post_treatment_score`, and `anxiety_instrument` fields.
- **Fallback**: If the verified OpenNeuro dataset lacks clinical scores, the project will attempt to use **ds000232**. If no dataset with paired pre/post clinical scores is found, the project **cannot proceed** with the current research question. The pipeline will halt with a fatal error: "Missing required variable: pre/post anxiety scores in verified dataset."
- **Search Protocol**: If both primary and fallback datasets fail, the pipeline will log "No Open Longitudinal Dataset Found" and halt, acknowledging the high risk of dataset mismatch for longitudinal clinical trial data with rs-fMRI.

### Dataset Search Protocol
Given the high risk of dataset mismatch (longitudinal clinical trial with rs-fMRI is rare in open repositories), the following protocol is implemented:
1.  **Primary**: Verify ds001971 for pre/post clinical scores.
2.  **Fallback**: Verify ds000232 for pre/post clinical scores.
3.  **Halt**: If neither dataset contains the required variables, halt with "No Open Longitudinal Dataset Found".

## Statistical Methodology

### ANCOVA Model
The primary analysis models the post-treatment anxiety score ($Y_{post}$) as a function of:
1.  **Baseline Severity**: Pre-treatment score ($Y_{pre}$).
2.  **Network Metrics**: Modularity ($Q$), Global Efficiency ($E_{glob}$), Local Efficiency ($E_{loc}$).
3.  **Confounders**: Age, medication status (if available).

$$Y_{post} = \beta_0 + \beta_1 Y_{pre} + \beta_2 M + \beta_3 E_{glob} + \beta_4 E_{loc} + \gamma C + \epsilon$$

**Note on Outcome Definition**: The outcome is $Y_{post}$ (ANCOVA design) to avoid regression to the mean artifacts associated with modeling change scores ($\Delta = Y_{post} - Y_{pre}$) while controlling for $Y_{pre}$. The 'Treatment Response' entity is defined as the change score for reporting purposes, but the regression uses $Y_{post}$.

### Collinearity Handling
- **VIF Check**: Calculate Variance Inflation Factor (VIF) for all predictors.
- **Threshold**: If VIF > 5 for any predictor:
  1.  **Ridge Regression**: Apply Ridge regression with $\lambda=1.0$. This is the primary fallback to stabilize coefficients in the presence of collinearity.
  2.  **Fallback**: If Ridge fails to converge or $R^2 < 0.05$, switch to separate univariate models for each network metric.
  3.  **Dimensionality Reduction**: If multicollinearity persists (VIF > 5 even after Ridge), apply PCA to the network metrics and use the first principal component as a predictor.
- **Rationale**: Network metrics (e.g., global efficiency and modularity) are often definitionally related. Independent effects cannot be claimed without addressing collinearity. The analysis will report the association of *sets* of metrics or PCA components rather than claiming independent effects of individual metrics if collinearity is high. Ridge regression is used to stabilize coefficients, but if it fails, univariate models are used as a last resort.

### Multiple Comparison Correction
- **Method**: Bonferroni or Benjamini-Hochberg (FDR).
- **Application**: Applied to the p-values of the network metric coefficients ($\beta_2, \beta_3, \beta_4$) when testing >1 metric.
- **Reporting**: Both uncorrected and corrected p-values are reported.

### Power Analysis
- **Tool**: `statsmodels.stats.power.FTestPower` (equivalent to G*Power).
- **Parameters**: $\alpha=0.05$, $f^2=0.15$ (medium effect), Power $\ge 0.8$.
- **Outcome**: Minimum $N$ required is calculated.
  - If $N < 5$: Halt analysis (insufficient data).
  - If $5 \le N < N_{min}$: Flag limitation in report as 'Exploratory'. Results will be reported as effect size estimates with wide confidence intervals, not definitive hypothesis tests.
  - **Critical Note**: With N=20 and 5+ predictors, the study is underpowered to detect f²=0.15 effects. The study is explicitly framed as exploratory.

### Sensitivity Analysis
- **Motion Thresholds**: Sweep $\{2.0, 3.0\}$ mm.
- **P-value Thresholds**: Sweep $\{0.01, 0.05, 0.1\}$.
- **Output**: Variation in outcome rates (significant associations found) across these thresholds. Output artifact: `reports/sensitivity_analysis.md`.

## Computational Feasibility

- **Hardware**: CPU-only (2 cores, 7GB RAM).
- **Streaming**: `datasets.load_dataset(..., streaming=True)` used to avoid loading full datasets into RAM. This strategy is for real, large datasets, not test shards.
- **Subset**: Analysis restricted to a subset of valid subjects meeting the 6-hour window.
- **Disk**: Streaming strategy ensures raw data is processed and deleted/archived to stay within 14GB limit. The selected subset of subjects is estimated to fit within the limit (approx. -4GB for processed data).
- **No GPU**: No deep learning models. All statistics are classical.

## Causal Framing
- **Observational Check**: The pipeline checks `metadata.study_design` for "randomized" or `metadata.randomized` for boolean true.
- **Framing**: If not randomized, all findings are framed as **ASSOCIATIONAL**. No causal claims (e.g., "VR therapy causes changes") are made.
- **Exploratory Framing**: If N < required power, findings are framed as **Exploratory** with effect size estimates and wide CIs, not hypothesis tests.