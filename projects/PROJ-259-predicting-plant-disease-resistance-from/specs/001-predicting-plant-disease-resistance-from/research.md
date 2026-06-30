# Research: 001-predict-plant-disease-resistance

## Summary of Scientific Approach

This project investigates whether plant disease resistance can be predicted using publicly available genomic (SNPs) and metabolomic data. The approach involves retrieving paired multi-omics datasets, preprocessing them to align samples, selecting predictive features via regularized regression and tree-based methods, and training interpretable models (Elastic-Net/Gradient-Boosting). Rigorous statistical validation (BH correction, permutation testing) ensures robustness.

## Dataset Strategy

### Verified Datasets

Per the `# Verified datasets` block in the user message, the following sources are available. However, **none** of the verified URLs correspond to the specific multi-omics (SNP + Metabolite + Phenotype) plant data required by the spec.

| Dataset Name | Type | Verified URL | Status |
| :--- | :--- | :--- | :--- |
| AUC (Financial) | Parquet | `https://huggingface.co/datasets/ChanceFocus/flare-finarg-ecc-auc/...` | ❌ Irrelevant (Finance) |
| ROC (Romanian) | Parquet | `https://huggingface.co/datasets/gigant/ro_corpora_parliament_processed/...` | ❌ Irrelevant (NLP) |
| SNP (Financial) | CSV | `https://huggingface.co/datasets/ManuBansal/33param_snp500/...` | ❌ Irrelevant (Financial S&P 500, not genomic) |
| MUST (Tool Calling) | Parquet | `https://huggingface.co/datasets/Mustafaege/...` | ❌ Irrelevant (LLM training) |
| **Plant Multi-omics** | **SNP+Metabo+Pheno** | **NO verified source found** | ⚠️ **Critical Gap** |

### Dataset Fit Assessment

The project specification (FR-001) requires **paired** genomic (SNP), metabolomic, and resistance phenotype data for the same plant samples.
- The verified `SNP` datasets provided (`ManuBansal/33param_snp500`) are financial time-series data (S&P 500), not biological genomic variants.
- No verified URL exists for plant multi-omics data in the provided list.
- The spec assumes such data exists in public repositories (NCBI SRA, MetaboLights).

**Decision**: The pipeline **MUST** be designed to fetch data directly from NCBI SRA (genomic) and MetaboLights/Metabolomics Workbench (metabolomic) using accession numbers provided in `data_manifest.yaml`. Since no single verified dataset URL exists that satisfies the "paired" requirement, the implementation will rely on the `download.py` module to construct a paired dataset by matching samples across repositories based on study accession numbers.

**Risk Mitigation**: If a dataset lacks a verified source in the `# Verified datasets` block, the pipeline will not fabricate a URL. Instead, it will require the user to populate `data_manifest.yaml` with valid NCBI/MetaboLights accession numbers. If no such valid accession numbers are provided, the pipeline will halt with `EX_DATA_INTEGRITY` or `EX_POWER_INSUFFICIENT` (FR-007/008).

## Statistical Methodology

### Feature Selection
- **Method**: LASSO (L1) regression for linear feature selection; Random Forest (RF) importance for non-linear interactions.
- **Correction**: Benjamini-Hochberg (BH) procedure applied to p-values to control False Discovery Rate (FDR) at α = 0.05.
- **Sensitivity Sweep**: Thresholds {0.01, 0.05, 0.1} tested to calculate selection frequency.
- **Output**: Top 50 SNPs and 50 metabolites capped by effect size.

### Model Training
- **Algorithms**: Elastic-Net (continuous phenotype) or Gradient-Boosting Classifier (categorical).
- **Validation**: 5-fold Stratified Cross-Validation.
- **Baseline**: Null model (random labels) for comparison.

### Significance Testing
- **Permutation Test**: n=1000 permutations on the hold-out set to derive model-level p-value.
- **Collinearity**: Variance Inflation Factor (VIF) calculated; features with VIF > 5 flagged.

## Compute Feasibility Analysis

- **Hardware**: GitHub Actions free-tier (2 CPU, ~7 GB RAM).
- **Strategy**:
  - **Data Sampling**: If a dataset exceeds 500 samples, the pipeline will sample to ~500-1000 to ensure RAM < 7 GB, unless the full dataset is required for power (FR-008).
  - **Algorithms**: Elastic-Net and Gradient-Boosting (with `n_estimators` capped at 100) are CPU-tractable.
  - **Preprocessing**: `fastp` and `bcftools` are run via Docker containers with optimized flags for low memory.
  - **Runtime**: Target < 4 hours to allow for CI overhead.

## Assumptions & Constraints

- **Data Availability**: Assumes researchers can identify valid NCBI/MetaboLights accession numbers that contain paired data. If no such data exists, the project cannot proceed.
- **Observational Nature**: All claims are associational; no causal inference.
- **Resource Limits**: No GPU; no deep learning models (e.g., autoencoders) used.

## Research Decisions & Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use NCBI SRA & MetaboLights directly** | No verified single-source dataset exists. Direct retrieval ensures compliance with Constitution Principle VI (Provenance). |
| **CPU-only algorithms** | Required by GitHub Actions free-tier constraints (FR-006). |
| **BH Correction** | Mandatory per spec (FR-003) and Constitution Principle VII (Statistical Rigor) to handle high-dimensional omics data. |
| **Permutation Testing** | Required (FR-005) to validate model performance against chance, ensuring SC-003 is met. |
