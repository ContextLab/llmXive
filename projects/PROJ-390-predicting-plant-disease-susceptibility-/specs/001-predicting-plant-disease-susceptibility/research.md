# Research: Predicting Plant Disease Susceptibility from Publicly Available Genomic and Environmental Data

## Executive Summary

This research plan outlines the methodology for predicting plant disease susceptibility by fusing genomic sequencing data with environmental metadata. The core challenge is the integration of heterogeneous data sources (raw FASTQ from NCBI SRA and gridded climate data from ERA5-Land) and the rigorous statistical validation of predictive models on a CPU-constrained environment. The plan prioritizes data integrity, reproducibility, and statistical significance over model complexity.

**Critical Feasibility Note**: This research is contingent on the existence of real, open data with linked genomic, environmental, and independent phenotypic disease labels. If such data cannot be identified, the project will halt at the **Feasibility Gate** and reframe its output as a "Pipeline Validation" report only, with no scientific claims regarding disease prediction.

## Dataset Strategy

### Verified Datasets

The implementation **MUST** use only the datasets listed below. If a dataset required by the spec (e.g., specific crop SRA data with disease labels) is not in this list, the implementation must either:
1. Use a verified open substitute that supports the same question.
2. Explicitly state that no open source exists and reframe the question.
3. **NOT** fabricate a URL.

**Verified datasets** (Cite ONLY these URLs):
- **AUC-ROC**: NO verified source found. (Metric derived from model output).
- **MICE (parquet)**:
 - `
 - `
 - `
- **SRA (parquet)**:
 - `https://huggingface.co/datasets/sradc/chunked-wikipedia20200301en-bookcorpusopen/resolve/main/data/train-00000-of-00053-fce5f0af789cac4c.parquet` (Note: This appears to be text data, not genomic. **CRITICAL GAP IDENTIFIED**).
 - `https://huggingface.co/datasets/sradc/chunked-shuffled-wikipedia20200301en-bookcorpusopen/resolve/main/data/train-00000-of-00053-550defad11191c81.parquet` (Text data).
 - ` (Image data).

### Dataset Fit Analysis & Gap Resolution

**Critical Finding**: The "Verified datasets" block provided for this project contains **NO** actual genomic (SRA) or environmental (ERA5) data. The SRA-listed URLs point to text corpora (Wikipedia/BookCorpus) and images (ImageNet). The MICE URLs point to protein/gene expression data unrelated to plant disease susceptibility in the field.

**Resolution Strategy**:
1. **Genomic Data**: The spec requires NCBI SRA data for crops (Wheat, Rice, etc.). Since no verified SRA URL exists in the provided list, the implementation **MUST** programmatically fetch data from the NCBI SRA using E-utilities (as per FR-001) or use a well-known open genomic repository (e.g., ENA) if accessible without credentials. The plan will **NOT** use the provided "SRA (parquet)" URLs as they are invalid for this purpose.
 * *Action*: The ingestion script will target specific, publicly accessible SRA run IDs for the target crops. If a specific run ID is not available in a public list, the system will log "No verified open dataset found for [Crop]-[Disease]" and skip that species, or use a synthetic proxy for testing the pipeline flow (clearly flagged as synthetic).
2. **Environmental Data**: ERA-Land is a public reanalysis product. The plan will use the `cdsapi` (if available) or direct `curl` to the Copernicus Climate Data Store (if public download is enabled) or NOAA APIs. If no open API key is available, the system will log the limitation.
3. **Fallback**: If no real open data can be fetched for the specific crop-disease combination, the system will generate a **small, synthetic dataset** that mimics the schema (SNP frequencies, temperature, disease label) **ONLY** to validate the pipeline logic. This synthetic data will be explicitly labeled `SYNTHETIC` and **excluded from any scientific claims regarding disease prediction**.

**Decision/Rationale**:
* **CPU-First**: All data processing (alignment, imputation, RF/SVM) will run on the CPU. No GPU models are planned.
* **Data Streaming**: If real SRA data is fetched, it will be streamed in chunks to avoid RAM overflow.
* **No Fabrication**: The plan explicitly avoids using the provided "SRA (parquet)" URLs as they do not contain genomic data. The implementation will attempt to fetch from NCBI directly or use synthetic data for pipeline validation only.

## Feasibility Gate

Before any modeling begins, the system must pass the **Feasibility Gate**:
1. **Search**: Query NCBI BioProject/BioSample for studies linking crop species (Wheat, Rice, Maize, Tomato, Soybean) with disease phenotypes and geographic metadata.
2. **Verify**: Confirm that at least one study provides:
 * Raw genomic reads (SRA).
 * Explicit disease status labels (Susceptible/Resistant).
 * Independent phenotypic source (e.g., Field Trial ID, not derived from the SRA metadata itself).
 * Location/Date data for environmental matching.
3. **Gate Result**:
 * **PASS**: Proceed to Phase 1.
 * **FAIL**: Halt project. Output `feasibility_report.md` stating "No verified open dataset found; project reframed as Pipeline Validation."

## Statistical Rigor & Methodology

### Model Training (FR-005)
* **Algorithms**: Random Forest (RF) and Support Vector Machine (SVM).
* **Split**: 70/15/15 stratified by species and disease status.
* **Hyperparameter Tuning**: Grid search limited to ≤50 combinations to ensure CPU feasibility.
* **Collinearity Handling (FR-009)**:
 * **LD Pruning**: SNPs with $r^2 > 0.8$ will be pruned.
 * **PCA**: If features exceed a substantial fraction of the sample size, PCA will reduce dimensionality to a correspondingly smaller set of components.
 * **Reporting**: The plan will report the number of features before and after pruning. If PCA is used, feature importance will be reported for original features *before* PCA, and PCA components will be reported as 'latent factors' without direct biological interpretation.

### Statistical Validation (FR-007, FR-008)
* **Permutation Test**: 1000 permutations, seed=42.
 * **Null Hypothesis**: Model performance is no better than random.
 * **Significance**: $p < 0.05$ (SC-002).
 * **Constraint**: Permutation tests are **only** performed on real data. Synthetic data is excluded.
* **Sensitivity Analysis**: Threshold sweep over a representative range of values.
 * **Metric**: Variation in False Positive Rate (FPR) and False Negative Rate (FNR).
* **Multiple Comparisons**: If multiple models or thresholds are tested, Bonferroni correction will be applied to the final reported p-values.

### Power & Sample Size
* **Limitation**: The free-tier runner (limited RAM) limits the dataset size to a moderate number of samples for complex alignment + modeling.
* **Acknowledgement**: The plan explicitly states that power is limited. With a sample size of approximately one thousand across five species, the per-species test set comprises roughly thirty samples. This is **underpowered** for detecting small effect sizes (AUC > 0.55) with high confidence.
* **Mitigation**:
 * Success criteria (SC-001) are redefined to report AUC with **95% Confidence Intervals (bootstrapped)** rather than a fixed threshold.
 * The project is framed as a "Feasibility Study" rather than a definitive diagnostic tool.
 * If the lower bound of the 95% CI is > 0.5, the result is considered "promising but requires larger validation."

## Computational Feasibility

* **Environment**: GitHub Actions Free Tier (multi-core CPU, 7 GB RAM, 14 GB disk).
* **Strategy**:
 1. **Sampling**: Limit SRA downloads to a small subset (e.g., a few samples per species) for the initial run.
 2. **Alignment**: Use `minimap2` with preset parameters optimized for speed (`-ax sr` for short reads).
 3. **Imputation**: Use **k-NN** (sklearn.impute.KNNImputer) which is CPU-tractable for <10k features and <1k samples.
 4. **No GPU**: No transformer models or deep learning. All ML is classical (RF, SVM).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No open SRA data with disease labels** | High (Fatal) | **Feasibility Gate** halts project. Reframe as "Pipeline Validation". Synthetic data used ONLY for schema testing. |
| **NCBI Rate Limits** | Medium | Exponential backoff (maximum limited number of retries). |
| **ERA5 Data Unavailable** | Medium | Fall back to NOAA; if both fail, exclude sample (log action). |
| **RAM Overflow** | High | Stream data; process one sample at a time. |
| **p >> n (Overfitting)** | High | LD pruning + PCA to reduce features to a substantially smaller subset. |
| **Label Independence Violation** | High | **Label Validation Protocol** excludes ambiguous samples. |

## References

* **NCBI SRA**: Programmatic access via E-utilities (no URL in verified block; standard API).
* **ERA5-Land**: Copernicus Climate Data Store (public API).
* **Scikit-learn**: Documentation for RF, SVM, and permutation tests.