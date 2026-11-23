# Research: Predict Plant Disease Resistance from Multi‑omics Data

## 1. Dataset Strategy

The project requires paired genomic (SNP), metabolomic, and phenotypic data from the **same samples**. The strategy prioritizes **verified open sources** (NCBI SRA, MetaboLights) and **halts** if no suitable real dataset is found. Synthetic data is **NOT** used for scientific validation.

### Verified Datasets & Availability

| Dataset Name | Type | Verified URL / Source | Suitability Analysis |
|:--- |:--- |:--- |:--- |
| **NCBI SRA (Plant Pathogen)** | Genomic (Raw Reads) | ` | **Primary Source**: Must search for studies with "SNP" AND "Metabolomics" AND "Phenotype" for same plant species. |
| **MetaboLights** | Metabolomic | `https://www.ebi.ac.uk/metabolights/` | **Primary Source**: Must cross-reference with SRA studies for matched samples. |
| **Metabolomics Workbench** | Metabolomic | ` | **Primary Source**: Alternative for metabolomic data. |
| **33param_snp500** | SNP (CSV) | `https://huggingface.co/datasets/ManuBansal/33param_snp500` | **INSUFFICIENT**: Lacks metabolomic profiles and plant disease resistance phenotypes. **NOT** used for scientific runs or CI fallback. |

### Decision: Real Data Only for Science
**Rationale**: The research question is "Can plant disease resistance be predicted using publicly available... data?" Generating synthetic data to mimic correlations creates a tautology (validating the generator, not the biology).
**Plan**:
1. **Search**: Query NCBI SRA and MetaboLights for studies containing all three modalities (SNP, Metabolite, Phenotype) for the same samples.
2. **Verification**: If a study is found, verify sample overlap. If overlap < 100, the pipeline halts with `EX_DATA_INTEGRITY`.
3. **Fallback**: If **NO** real multi-omics dataset is found, the pipeline **HALTS** with `EX_DATA_INTEGRITY` and reports "No real multi-omics dataset found. Scientific analysis cannot proceed."
4. **CI Mode**: Synthetic data generation is available ONLY via `--ci-mode` flag. This is for testing code execution (T042, T046, T048) and **NOT** for generating scientific results. **SC-001 (≥75% accuracy) is not applicable to CI mode.**

## 2. Statistical Methodology

### Feature Selection (FR-003)
* **Method**: LASSO Regression (continuous) and Random Forest (categorical).
* **Thresholds**: Sensitivity sweep over p-values {, 0.05, 0.1}.
* **Correction**: **Permutation-based FDR** or **Li & Ji effective tests** to account for Linkage Disequilibrium (LD) and metabolite co-regulation. Standard BH is insufficient for correlated data.
* **Output**: Top-ranked SNPs/Metabolites by effect size, capped by significance.
* **Robustness**: Selection frequency calculated across the three thresholds. **Report** variance; **do not halt** (T047 resolved).

### Model Training (FR-004)
* **Algorithms**: Elastic-Net (continuous) or Gradient Boosting Classifier (categorical).
* **Validation**: **Nested Cross-Validation** (K-fold outer, K-fold inner).
 * *Inner Loop*: Feature selection and hyperparameter tuning.
 * *Outer Loop*: Performance estimation.
* **Baseline**: Null model (random labels).

### Significance & Diagnostics (FR-005, Constitution Fact)
* **Permutation Testing**: n=1000 permutations on the **outer** hold-out set (or nested permutation scheme).
 * **Formula**: `p = (count(permutation_score >= observed_score) + 1) / (n_permutations + 1)`. (T018 fixed).
 * **Strategy**: **Block Permutation** (permuting blocks of correlated SNPs) or **Residual Permutation** to preserve correlation structure.
 * **Reproducibility**: Run permutation test twice with fixed seed; assert p-values match within tolerance (T048).
* **Collinearity**: Variance Inflation Factor (VIF) calculated for all selected features.
 * **Flag Threshold**: **VIF > 5** (per FR-005). (Corrected from 33).
* **Power Analysis**: System halts with `EX_POWER_INSUFFICIENT` if n < 100.

### Data Splitting (FR-009)
* **Strategy**: `sklearn.model_selection.StratifiedShuffleSplit` with `test_size=0.2`, `n_splits=1`.
* **Rationale**: Ensures the 80/20 split maintains the same class distribution (resistant/susceptible) in both training and hold-out sets, preventing bias in performance estimation.

## 3. Compute Feasibility (CPU-First)

* **Environment**: GitHub Actions Free Tier (standard CPU, sufficient RAM).
* **Strategy**:
 * **Data Streaming**: Use `datasets.load_dataset(..., streaming=True)` for large CSVs to avoid OOM.
 * **No GPU**: All models (`scikit-learn`) run on CPU.
 * **Time Limit**: Pipeline optimized to complete in < 6 hours.
 * **CI Mode**: Synthetic data generation is lightweight and fast.

## 4. Resolved Concerns

* **T018 (Statistical Formula)**: Formula corrected to `p = (count + 1) / (n + 1)`. Random seed fixed in config.
* **T047 (Robustness Check)**: Removed "halt if variance > [deferred]". Variance is now a reported metric only.
* **T042 (Data Manifest)**: `code/download.py` halts if real data missing. Synthetic data is CI-only.
* **T046 (Resource Monitor)**: `code/utils/resources.py` implemented.
* **T048 (Permutation Reproducibility)**: Plan includes task to run permutation test twice with fixed seed and assert match.
* **Scientific Soundness (Circular Validation)**: Addressed via Nested Cross-Validation and Block Permutation.
* **Scientific Soundness (Dependence)**: Addressed via Block Permutation/Residual Permutation strategy.
