# Research: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

## Problem Statement

The field of machine-learned reaction yield prediction lacks a standardized, automated audit of reproducibility. Published papers report performance metrics (MAE, R², Spearman ρ), but independent re-implementations often fail to match these numbers due to unreported seeds, dataset version drift, or missing covariates. This study aims to quantify the gap between reported and reproduced metrics across a curated set of papers, identify the sources of systematic bias, and generate actionable community guidelines.

## Dataset Strategy

The study relies on open, programmatic datasets to ensure execution on the free-tier CI runner. The primary dataset is the **USPTO-Extract** collection, which provides standardized reaction data (SMILES, yields).

### Verified Datasets

The following datasets are verified for availability and format. The plan uses these exact sources with specific version tags:

| Dataset Name | Source/URL | Version | Usage | Verification Status |
|:--- |:--- |:--- |:--- |:--- |
| USPTO Balanced | ` | v1.0 | Primary test set for re-implementation. | Verified (Parquet, accessible). |
| USPTO Full | ` | v1.0 | Alternative source for validation splits if needed. | Verified (Parquet, accessible). |
| USPTO Conditions | `https://huggingface.co/datasets/chembl/uspto_conditions/resolve/main/data/test-00000-of-00001.parquet` | v1.0 | **Specific** source for papers requiring temperature/solvent covariates. | Verified (Parquet, accessible). |

**Note on Covariates**: The spec (FR-003) requires verification of covariates (temperature, solvent, catalyst loading).
- **If a target paper requires covariates not present in the verified USPTO extracts (e.g., USPTO Balanced lacks temperature)**:
 1. The system attempts to locate the specific dataset version referenced in the paper's supplementary materials (if a public URL exists).
 2. If a specific dataset with covariates (e.g., USPTO Conditions) is found, it is used.
 3. **If no dataset with the required covariates is available**: The paper is marked as `unreproducible` and **excluded** from the deviation calculation and meta-analysis. We do **not** attempt to reproduce the model on incomplete data, as this would conflate data mismatch with code reproducibility errors (construct validity failure).
- **If a paper uses the standard SMILES/Yield only**: The standard USPTO Balanced dataset is used.

### Data Access Method

- **Streaming**: To respect system memory constraints, datasets are loaded using `datasets.load_dataset(..., streaming=True)` from Hugging Face.
- **Checksumming**: Upon download, file checksums (SHA-256) are computed and stored in `data/manifest.yaml` to satisfy Constitution Principle VI (Dataset Version Fidelity).
- **No Gated Data**: The plan explicitly excludes datasets requiring registration (e.g., ADNI, proprietary EHR) as they cannot be fetched by the CI runner.

## Statistical Methodology

The statistical analysis is designed to detect systematic bias and quantify variance components.

### 1. Reproducibility Score (FR-009)
For each paper, a score $S \in [0,1]$ is calculated:
$$ S = 1 - \frac{1}{3} \left( \frac{|\Delta \text{MAE}|}{|\text{MAE}_{\text{ref}}| + \epsilon} + \frac{|\Delta R^2|}{|R^2_{\text{ref}}| + \epsilon} + \frac{|\Delta \rho|}{|\rho_{\text{ref}}| + \epsilon} \right) $$
where $\epsilon = 10^{-6}$ and $\Delta$ is the absolute deviation between reproduced and reported values.
*Clarification*: This score measures "Deviation from Claim", not absolute scientific validity. It quantifies how far the reproduction is from the paper's report, not whether the paper's report is correct.

### 2. Paired t-test (FR-006, SC-002)
- **Hypothesis**: $H_0$: Mean difference between reported and reproduced metrics is zero.
- **Correction**: Bonferroni correction applied for multiple comparisons (3 metrics).
- **Outcome**: Flag if corrected $p < 0.05$, indicating systematic bias.
- **Note**: Reported metrics are treated as constants (as per spec), but TOST is added as a secondary robustness check.

### 3. TOST Equivalence Test (Secondary)
- **Purpose**: To assess if the deviation is within a pre-defined tolerance (e.g., 5% relative error), acknowledging uncertainty in reported metrics.
- **Outcome**: Complement to the t-test.

### 4. Bland-Altman Analysis (FR-007)
- **Purpose**: Visualize agreement and detect proportional bias (e.g., larger errors at higher yields).
- **Output**: PNG plots saved to `artifacts/plots/`.

### 5. Linear Mixed-Effects Model (FR-008)
- **Model**: $Y_{ij} = \beta_0 + \beta_1 \text{ModelSubstitution}_i + \beta_2 \text{CovariateMissing}_i + u_j + \epsilon_{ij}$
- **Fixed Effects**: `ModelSubstitution` (binary), `CovariateMissing` (binary). *Note: 'LibraryVersion' and 'SeedChoice' are constant across the run and thus have zero variance; they are excluded from fixed effects to avoid mathematical singularity. 'SeedChoice' is analyzed via Sensitivity Analysis instead.*
- **Random Effects**: $u_j \sim N(0, \sigma^2_{paper})$ (Random intercept for paper).
- **Goal**: Quantify the variance explained by model substitution and data gaps.

### 6. Heterogeneity (I²)
- **Metric**: $I^2 = \frac{Q - df}{Q} \times 100\%$
- **Standardization**: Calculated on **relative error** ($|\Delta|/|Ref|$) to ensure comparability across different metric scales (e.g., MAE vs R²).
- **Usage**: Input for the qualitative failure log.

### 7. Sensitivity Analysis (FR-010)
- **Method**: Re-run training with seeds $\{42, 123, 999\}$.
- **Metric**: Record maximum standard deviation of metrics across seeds (`max_metric_std`).
- **Timeout**: If sweep exceeds a predefined duration threshold, flag `sweep_incomplete` and record single-seed result.

## Decision/Rationale: Compute Feasibility

- **CPU-First**: All models (Random Forest, Gradient Boosting, shallow NN ≤ 3 layers) are selected to run on the 2-core CPU runner.
- **No GPU**: The plan explicitly forbids `device="cuda"`. If a paper's model requires a GPU (e.g., >1M parameters or deep transformers), the plan triggers the "Model Substitution" logic (Assumption in spec) to replace it with a comparable CPU-tractable baseline, logging the deviation.
- **Streaming**: The use of `streaming=True` ensures the full USPTO dataset can be processed without exceeding available memory constraints., avoiding the need for a "toy" subset unless the specific paper's split is small.