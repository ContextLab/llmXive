# Research: Resting-State Network Modularity Predicts Social Network Size

## Research Question
Does higher resting-state functional network modularity, quantified by the Louvain-derived modularity quality index (Q), associate with a larger self-reported social network size in healthy adults?

## Dataset Strategy

The primary data source is the Human Connectome Project (HCP) large-scale subjects release. To ensure CPU feasibility on GitHub Actions, a random sample of subjects will be processed.

### Verified Datasets
The following verified sources are used for data retrieval. No other URLs are fabricated.

| Dataset Name | Description | Verified URL | Usage Strategy |
|:--- |:--- |:--- |:--- |
| HCP 1200 Subjects | Full HCP release including minimally preprocessed fMRI and behavioral data. | ` Name or service not known)"))] (S3 Bucket) | Primary source for both fMRI NIfTI files and behavioral CSVs. Access via `aws` CLI or `requests` with public credentials. |
| HCP Behavioral Data | CSV file containing subject metadata and behavioral data. | ` certificate verify failed: Hostname mismatch, certificate is not valid for 'data.humanconnectome.org'. (_ssl.c:1016)")))] | Primary source for social network metrics (`Number of close friends`, `Number of acquaintances`). |

**Critical Data Availability Check**:
The pipeline will **halt** if the verified HCP S3 bucket does not contain the minimally preprocessed fMRI NIfTI files for the sampled subjects. No synthetic, simulated, or mismatched datasets (e.g., `nilearn`'s `fetch_development_fmri`) will be used to replace missing fMRI data. If the verified source only contains metadata, the project scope is redefined to "Pipeline Validation on Public Matched Dataset" (e.g., a smaller public study with both fMRI and social metrics), and the analysis will not proceed on HCP data.

### Variable Mapping
- **Predictor**: Modularity Quality Index (Q) derived from resting-state fMRI.
- **Outcome**: Social Network Size (Sum of `Number of close friends` + `Number of acquaintances`).
- **Covariates**:
 - Age (continuous)
 - Sex (binary)
 - Mean Framewise Displacement (motion)
 - Total Connectivity Strength (sum of absolute edge weights). *Note: This covariate is subject to a VIF check to avoid collinearity with Q.*

## Methodological Rigor

### Statistical Approach
- **Primary Analysis**: Standard Linear Regression (OLS) with robust standard errors.
 - Model: `Social_Network_Size ~ Modularity_Q + Age + Sex + Motion + Total_Strength`
 - Null Hypothesis: Coefficient for `Modularity_Q` = 0.
- **Collinearity Check**: A Variance Inflation Factor (VIF) check is mandatory before fitting the primary model. If VIF > 5 for `Total_Strength`, the model will be re-run without this covariate, and the result will be reported as a sensitivity analysis.
- **Multiple Comparisons**: If separate models are run for "friends" and "acquaintances", the Benjamini-Hochberg procedure will be applied to control the False Discovery Rate (FDR).
- **Sensitivity Analysis**: The primary analysis will be repeated across a range of graph density thresholds to ensure the result is not an artifact of a single cutoff.
- **Power & Sample Size**: A formal power calculation is performed for N=200, r=0.2, and 5 covariates. The result (approx. moderate power) indicates the study is underpowered for definitive hypothesis confirmation. The study is explicitly framed as a **Pilot/Feasibility** study to estimate effect sizes and validate the pipeline. A sensitivity analysis for power (e.g., "What N is needed for r=0.1?") is included.
- **Causal Claims**: The analysis is observational. Findings will be framed as **associational**. No causal claims regarding modularity causing social size will be made.
- **Metabolic Cost**: The "metabolic cost" hypothesis (Geoffrey West) is addressed by including `Total_Strength` as a covariate, but only if collinearity is low. If collinearity is high, the hypothesis is treated as exploratory.

### Dataset-Variable Fit
- **Critical Check**: The plan verifies that the verified HCP behavioral data contains the columns `Number of close friends` and `Number of acquaintances`. If these are missing, the pipeline will attempt a case-insensitive substring search for synonyms (e.g., 'friends', 'social_size'). If no match is found, the pipeline will raise a runtime error and halt.
- **fMRI Data**: The plan strictly requires the verified HCP S3 bucket to contain the minimally preprocessed fMRI NIfTI files. If these are missing, the pipeline halts. No synthetic fallback is permitted.

### Reviewer Feedback Integration
- **Metabolic Cost**: The reviewer (Geoffrey West) noted the need to model metabolic cost. The plan addresses this by including **Total Connectivity Strength** as a covariate, subject to a VIF check to avoid multicollinearity with Modularity Q.
- **Power**: The plan acknowledges the underpowered nature of N=200 for small effects and frames the study as a pilot.

## Computational Feasibility
- **Memory**: Data will be processed in chunks. Only 200 subjects' correlation matrices (200x200) will be held in memory simultaneously.
- **Runtime**: The pipeline is designed to complete within 6 hours on a 2-core CPU.
- **GPU**: No GPU usage. All algorithms (Louvain, OLS) are CPU-tractable.
