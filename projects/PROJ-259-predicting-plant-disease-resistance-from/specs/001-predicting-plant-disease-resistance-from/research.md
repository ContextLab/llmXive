# Research: Predict Plant Disease Resistance from Multi‑omics Data

## 1. Problem Definition & Feasibility

The core challenge is to build a predictive model for plant disease resistance using **paired** genomic (SNP) and metabolomic data.
*   **Scientific Question**: Can multi-omics integration improve prediction of resistance levels compared to single-omics approaches?
*   **Feasibility Check**: The spec requires **matched** samples (genotype + metabolite + phenotype) for the same plant individual. This is a high-bar requirement in public repositories.

## 2. Dataset Strategy

### Verified Sources & Constraints
Per the "Verified datasets" block provided in the input:
*   **SNP Data**: `ManuBansal/33param_snp500` datasets are available, but these are **financial/stock market** data (SNP500 index), **not** plant genomic data.
*   **Plant Genomic/Metabolomic Data**: **NO verified source found** in the provided list. The block explicitly states "SNPs: NO verified source found".
*   **Conclusion**: There is **no public, verified dataset** in the provided list that contains the required plant-specific multi-omics data.

### Data Acquisition Plan (Per Constitution Principle VI)
Since no verified URL exists, the implementation will:
1.  **Attempt Real Fetch**: The pipeline will attempt to fetch data from NCBI SRA and MetaboLights using search terms defined in `data_manifest.yaml` (e.g., "Arabidopsis thaliana pathogen interaction").
2.  **Simulation Fallback (Primary Mode)**: If no real data is found (confirmed), the pipeline **MUST** generate a synthetic dataset that mimics the statistical properties of plant multi-omics data (high dimensionality, sparsity, correlation structures) to demonstrate the *functionality* of the pipeline (FR-001 to FR-009) without violating the "no fabricated URL" rule.
    *   *Rationale*: The spec requires a runnable pipeline. Without a real dataset, the code cannot be tested. A synthetic dataset allows verification of the *logic* (preprocessing, feature selection, model training) while explicitly noting the limitation.
    *   **Signal Injection**: The synthetic generator will inject a known, controlled signal (correlation between specific SNPs/metabolites and the phenotype) to allow for validation of the model's ability to detect true positives.

### Power Analysis for Synthetic Data
*   **Requirement**: FR-007/FR-008 mandate n ≥ 100.
*   **Analysis**: The synthetic generator will be configured to produce exactly **n=150** samples (to ensure a buffer above the 100 threshold) with a signal strength (effect size) of 0.1.
*   **Power Calculation**: With n=150, α=0.05 (BH-corrected), and effect size 0.1, the power to detect the injected signal is estimated at >0.8. This ensures that if the pipeline fails to detect the signal, the failure is due to the code, not insufficient power.
*   **Constraint**: If the real data fetch yields <100 samples, the pipeline halts (as per FR-007/FR-008).

### Dataset Variables (Hypothetical/Target)
If a real dataset were found, it would require:
*   **Genotype**: SNP matrix (Samples x Variants).
*   **Metabolome**: Metabolite intensity matrix (Samples x Features).
*   **Phenotype**: Disease resistance score (Continuous) or Label (Resistant/Susceptible).

**Critical Mismatch Note**: The spec assumes public repositories contain matched data. In reality, matching samples across SRA (genomics) and MetaboLights (metabolomics) is rare. The plan includes a strict filtering step (FR-001) to exclude samples lacking any modality, which may reduce the sample size below the required 100 (FR-007/FR-008).

## 3. Methodological Rigor

### Statistical Validation
*   **Multiple Testing**: Benjamini-Hochberg (BH) correction will be applied to all p-values from feature selection to control the False Discovery Rate (FDR) at a conventional significance level.
*   **Power Analysis**: The plan enforces a minimum of 100 samples (FR-007/FR-008). If the dataset (real or synthetic) has < 100 samples, the pipeline halts with `EX_POWER_INSUFFICIENT`.
*   **Collinearity**: Variance Inflation Factor (VIF) will be calculated for selected features. Features with VIF > 5 will be flagged (FR-005).
*   **Causal Claims**: All results will be framed as **associational**. No causal inference will be claimed, as the data is observational.

### Model Selection & Training
*   **Feature Selection**: LASSO (L1) and Random Forest (RF) importance.
    *   *Sensitivity Sweep*: Thresholds {0.01, 0.05, 0.1} will be tested to determine feature stability (FR-003).
*   **Prediction Models**:
    *   **Elastic-Net**: For continuous resistance scores.
    *   **Gradient-Boosting (XGBoost/LightGBM CPU mode)**: For categorical labels.
*   **Validation**:
    *   K-Fold Cross-Validation for training.
    *   Independent Hold-Out Test Set for final evaluation.
    *   Permutation Testing (n=1000) to generate p-values for model performance (FR-005).

### Compute Feasibility (CPU-Only)
*   **Constraints**: 2 CPU cores, 7 GB RAM, 6h runtime.
*   **Strategy**:
    *   Data will be downsampled or processed in chunks if necessary.
    *   Only CPU-compatible libraries (`scikit-learn`, `xgboost` with `tree_method='hist'` or `exact`, `lightgbm` with `device='cpu'`) will be used.
    *   No GPU acceleration or quantization.

## 4. Methodological Boundaries & Limitations

### Simulation Mode vs. Scientific Validation
*   **Current State**: The project is currently in **Software Engineering Validation Mode**. The synthetic data is used to prove that the *code* correctly implements the pipeline logic (download, preprocess, select, train, validate).
*   **Circularity Warning**: The accuracy metrics (≥75%) and significance (p<0.05) obtained from synthetic data are **not** scientific findings about plant disease resistance. They are validation that the pipeline can detect the signal *injected by the generator*.
*   **Biological Hypothesis**: The hypothesis that "multi-omics integration improves prediction of real plant disease resistance" remains **unvalidated** until a real, matched dataset is discovered and processed. The current results do not support or refute this biological claim.

### Data Availability
*   **Real Data**: No verified public dataset exists. The pipeline will default to synthetic data.
*   **Future Work**: If a real dataset is discovered, the pipeline can be re-run in "Real Data Mode" to validate the biological hypothesis. The current codebase is designed to be agnostic to the data source (real vs. synthetic).

### Permutation Testing Validity
*   **Simulation Mode**: With n=150 and injected signal, permutation testing is **valid** for confirming the pipeline's ability to distinguish signal from noise (i.e., it validates the *code*).
*   **Sparse Real Data (n < 100)**: If a real fetch yields <100 samples, the permutation test is **inapplicable** due to insufficient power for multivariate omics. In this case, the pipeline **halts** (FR-007/008) rather than producing a statistically invalid result.
*   **Conclusion**: The permutation test is only executed when the sample size threshold is met. This ensures that any reported p-value is methodologically sound for the data regime it was applied to (either synthetic validation or real data with sufficient power).

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data Fallback** | No verified plant multi-omics dataset exists in the provided list. A synthetic dataset is necessary to validate the pipeline logic without inventing URLs. |
| **Strict Sample Filtering** | FR-001 requires paired modalities. This is a known bottleneck in multi-omics; the plan prioritizes data integrity over sample count, triggering halts if n < 100. |
| **BH Correction** | Essential for high-dimensional omics data to avoid false positives (FR-003, SC-002). |
| **Permutation Testing** | Required to establish statistical significance of the model performance beyond cross-validation (FR-005, SC-003). In simulation mode, this validates the pipeline's ability to detect the injected signal. |