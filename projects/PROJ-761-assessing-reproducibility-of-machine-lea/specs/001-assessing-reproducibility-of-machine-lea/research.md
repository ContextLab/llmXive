# Research: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

## 1. Problem Statement & Scope
The project aims to quantify the reproducibility of machine-learned reaction yield models reported in scientific literature. The core challenge is the "black box" nature of many published results where code, data splits, or hyperparameters are missing or ambiguous. This study re-implements these models in a controlled environment to measure the deviation between reported and reproduced metrics. The statistical approach uses **Equivalence Testing (TOST)** to determine if deviations fall within a scientifically acceptable tolerance, rather than simply testing for zero difference.

## 2. Dataset Strategy
The success of this project hinges on the availability of datasets that contain the specific variables required by the target papers: **reactant SMILES**, **product SMILES**, **measured yield**, and any **covariates** (temperature, solvent, catalyst loading) mentioned in the methods.

### Verified Datasets & Fallback Strategy
Based on the project's verified dataset list, the following sources are available. However, **none of the currently verified datasets (MAESTRO, MUST, etc.) explicitly contain the specific chemical reaction yield data (SMILES + Yield + Covariates) required for all target papers** as confirmed by the "Partial Fit" or "Not Applicable" status.

| Dataset Name | Verified URL | Status for Project | Strategy |
| :--- | :--- | :--- | :--- |
| MAESTRO | https://huggingface.co/datasets/lucainiao/MAESTRO_2004_SYNTH/resolve/main/MAESTRO_2004_SYNTH.zip | **Partial Fit**: Contains reaction data, but covariate availability (temperature/solvent) must be verified per paper. | **Primary Candidate**: Use if covariates match. If covariates are missing, attempt to extract data from the paper's supplementary materials. |
| MUST (parquet) | https://huggingface.co/datasets/Mustafaege/qwen3.5-toolcalling-v2/resolve/main/data/test-00000-of-00001.parquet | **Not Applicable**: This dataset is for tool-calling, not reaction yield. | Ignore. |
| USPTO-Extract (v1.0) | **NO VERIFIED SOURCE** | **Critical Gap**: The spec assumes availability of "USPTO-Extract v1.0", but no verified URL exists. | **Manifest Dependency**: The plan relies on the `data/manifest.yaml` to provide **direct URLs** to the specific data files (CSV/Parquet) used in each paper, or scripts to generate them from supplementary materials. If no direct URL is provided, the paper is flagged as "Data Unavailable". |
| Generic CSV/Parquet | Various (e.g., nateraw/dummy-csv) | **Not Applicable**: Synthetic or unrelated data. | Ignore. |

**Decision**: The implementation will attempt to load the dataset specified in the `data/manifest.yaml` for each paper. If the manifest does not provide a direct URL to the specific data used in the paper, the system will flag the paper as "Data Unavailable". If the dataset (e.g., MAESTRO) lacks required covariates, the system will **exclude** the paper from the quantitative reproducibility score calculation and record it as a "Data Gap" failure mode. This prevents false negatives in the reproducibility metric due to data incompleteness.

## 3. Methodological Approach

### 3.1 Re-implementation Strategy
For each paper in the manifest:
1.  **Code Retrieval**: Clone the repository or re-implement the model from the description (≤200 LOC limit).
2.  **Environment**: Run inside the pinned Docker container (Python 3.11, PyTorch 2.2 CPU).
3.  **Data Splitting**: Use the exact split indices provided. If missing, use a random split with the reported seed (default 42).
4.  **Training**: Train the model using reported hyperparameters. If the model exceeds 1M parameters or requires unavailable covariates, **exclude** it from the quantitative analysis and log as a failure mode.
5.  **Evaluation**: Compute MAE, R², Spearman ρ on the test set.

### 3.2 Statistical Analysis
-   **Equivalence Testing (TOST)**: Compare reported vs. reproduced metrics against a pre-defined tolerance margin (delta). The null hypothesis is "non-equivalence". Apply Bonferroni correction for 3 metrics.
-   **Fixed-Effects Meta-Analysis (FEMA)**: Aggregate deviations using inverse-variance weighting. The variance for each paper is estimated from the **maximum standard deviation** observed in the seed sweep (FR-010).
-   **Bland-Altman**: Visualize agreement and bias.
-   **Normality Check**: Perform Shapiro-Wilk test; if violated, use non-parametric bootstrap for equivalence testing.

### 3.3 Sensitivity Analysis
-   Sweep seeds {42, 123, 999} to estimate metric variance (standard deviation) due to stochasticity. This `metric_std` is used as the weight in the meta-analysis.

## 4. Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Missing Dataset URL** | High | If no direct URL is in the manifest, flag as "Data Unavailable" and exclude from quantitative analysis. |
| **Missing Covariates** | High | If temperature/solvent data is missing and cannot be retrieved from supplementary materials, exclude from quantitative analysis. |
| **Model Too Large** | Medium | Exclude from quantitative analysis; log as "Model Substitution" failure mode. |
| **Non-reproducible Code** | High | Re-implement from text description; if impossible, flag as "Code Unreproducible". |
| **CPU Runtime Exceeds 6h** | High | Limit model complexity and dataset size; use sampling if necessary. |

## 5. Addressing Reviewer Feedback (Marie Curie / Linus Pauling)
The reviewers (simulated) raised concerns about the lack of **experimental replicates** and **precise conditions** (temperature, solvent) in the original studies.
-   **Response**: This project *assesses* the reproducibility of the *reported* metrics. It does not generate new experimental data. Therefore, the "number of replicates" is a property of the original paper, not this study.
-   **Action**: The plan will explicitly extract the "number of replicates" (if reported) from the original paper's metadata. If not reported, this will be recorded as a "Missing Metadata" flag in the `ReproResult`.
-   **Covariates**: The plan will verify the presence of temperature/solvent in the dataset. If missing and not retrievable from supplementary materials, it will be flagged as a "Data Gap" contributing to potential irreproducibility, and the paper will be excluded from the quantitative score to avoid category errors.

## 6. Conclusion
The research strategy focuses on a rigorous, automated audit of reported metrics. By strictly controlling the environment, explicitly handling data gaps, and using appropriate statistical methods (TOST, FEMA with inverse-variance weighting), the project will provide a quantitative assessment of reproducibility in this domain, directly addressing the need for transparency highlighted by the reviewers.