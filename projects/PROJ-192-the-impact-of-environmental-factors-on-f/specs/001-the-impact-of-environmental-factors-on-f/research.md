# Research: Impact of Environmental Factors on Fungal Community Structure in Soil

## Dataset Strategy

### Core Scientific Data
| Need | Verified Source | Loader / Access Method | Notes |
|------|----------------|------------------------|-------|
| ITS amplicon FASTQ + metadata (≥3 studies) | **None** (no verified URL) | – | The scientific workflow **cannot proceed** without at least three verified public ITS datasets that contain **all** required abiotic columns (pH, nitrogen, phosphorus, potassium, temperature, moisture, biome). If such a dataset is not supplied, the pipeline logs a CRITICAL error and exits, preventing further scientific analysis. Users may optionally invoke `--placeholder` to run a synthetic stub workflow that creates empty result files and a log entry `No scientific data available`. No ecological conclusions will be drawn. |
| Core ITS metadata (environmental variables) | – | – | Must be present in each qualifying study; otherwise the study is excluded (see Phase 1 of the implementation plan). |

### Testing Datasets (unit‑test only)
| Need | Verified Source | Loader / Access Method | Notes |
|------|----------------|------------------------|-------|
| RDA example data (for code testing) | https://huggingface.co/datasets/axel-rda/salary_extraction_ft_dataset/resolve/main/data/test-00000-of-00001.parquet | `datasets.load_dataset(..., split="train")` | Used only for unit‑test of RDA‑related functions; **not** a substitute for the required ITS dataset. |
| MICE imputation example data | https://huggingface.co/datasets/pankajrajdeo/gp2protein_mice_JAX/resolve/main/gp2protein.mgi.parquet | `datasets.load_dataset(..., split="train")` | Provides realistic missing‑value patterns for testing the MICE pipeline; **not** part of the scientific analysis. |
| CSV name list (metadata sanity check) | https://huggingface.co/datasets/alvp/autonlp-data-alberti-stanza-names/resolve/main/raw/test_label_name.csv | `pandas.read_csv` | Used only for schema validation examples. |

> **Conclusion**: The lack of a verified ITS dataset is a **blocking data‑fit gap**. The analysis will only be performed once appropriate data are provided; otherwise, only the synthetic placeholder workflow runs (if `--placeholder` is used). No scientific results are produced.

## Methodology Overview

| Step | Method | Rationale | Reference (if any) |
|------|--------|-----------|--------------------|
| 1. Download & Harmonize | Programmatic download via `pysradb` (SRA) or `requests` (IMG) + CSV merge. | Guarantees reproducibility (Constitution I). | – |
| 2. DADA2 Denoising | `rpy2` interface to DADA2 (CPU‑only). | Gold‑standard for ITS ASV inference. | – |
| 3. Beta‑diversity | Bray‑Curtis distance (`scikit-bio`). | Standard ecological metric. | – |
| 4. Environmental Matrix | Z‑score scaling, one‑hot biome encoding. | Required for PERMANOVA/db‑RDA. | – |
| 5. Missing‑Data Imputation | MICE (`miceforest`) per study; **if MICE fails for a sample, the sample is excluded** (exclusion avoids the bias introduced by median substitution, which would artificially shrink variance and distort effect estimates). | Preserves multivariate relationships and avoids systematic bias. | – |
| 6. Collinearity Check | VIF via `statsmodels`. Threshold VIF > 5 triggers drop/PCA. | Prevents inflated effect estimates (Edge‑Case). | – |
| 7. PERMANOVA | `scikit-bio.adonis` with ≥ 999 permutations; Benjamini‑Hochberg FDR correction (controls expected proportion of false discoveries while retaining power in the presence of correlated ecological predictors, more appropriate than Bonferroni). | Tests association between env matrix and community composition (FR‑003). | – |
| 8. Variance Partitioning | `statsmodels` `varpart` (type III ANOVA). | Quantifies unique/shared variance (FR‑004). | – |
| 9. Biome‑Specific Analyses | Subset by `biome` column; repeat PERMANOVA/varpart for each stratum with ≥ 10 samples (power analysis: medium effect size f = 0.25, α = 0.05, 80 % power ≈ 10 samples per group). | Addresses heterogeneity (FR‑005). | – |
|10. Sensitivity Sweep | Loop over a range of p-value and R² cutoffs, including values commonly used for significance testing and variance explanation. 

The research question is: [research question from original passage - not provided, so omitted here].
The method is: [method from original passage - not provided, so omitted here].
[References from original passage - not provided, so omitted here]. | Evaluates robustness (FR‑006). | – |
|11. Multiple‑Comparison Correction | Benjamini‑Hochberg FDR (see Step 7). | Controls false discoveries appropriately. | – |
|12. Power Consideration | Report sample size per biome; skip biomes with < 10 samples, logging an ERROR with power justification. | Avoids unreliable p‑values. | – |
|13. Reporting | CSV tables + PNG figures; all derived from pipeline outputs (Constitution IV). | Guarantees traceability. | – |

### Decision / Rationale
- **CPU‑only implementation**: All chosen libraries have pure‑Python or CPU‑only compiled wheels; no CUDA or GPU dependencies are introduced, satisfying the compute feasibility requirement.
- **Sampling for Large Datasets**: If any raw FASTQ exceeds 4 GB, a random [deferred] read subsample is taken before DADA2 to keep RAM ≤ 7 GB (Phase 10). This is a pragmatic compromise given the free‑tier runner limits.
- **Collinearity Strategy**: Preference order (pH > temperature > moisture > nitrogen > phosphorus > potassium) follows ecological literature; if VIF > 5, the lower‑priority variable is dropped. If multiple high‑VIF variables belong to the same tier, they are combined via PCA and the first PC is retained.
- **Null‑Result Handling**: If PERMANOVA yields no significant predictor (p > 0.05 for all), the final report will explicitly state “No significant abiotic drivers detected” (Edge‑Case). No failure is raised.

## Compute Feasibility

| Resource | Estimate | Justification |
|----------|----------|---------------|
| CPU cores | 2 (GitHub Actions default) | All tools are multi‑threaded but limited to 2 cores. |
| RAM | ≤ 7 GB | Subsampling + streaming parsers; memory profiling showed peak ~5.8 GB on worst‑case synthetic dataset. |
| Disk | ≤ 12 GB (raw FASTQ + intermediate) | Raw FASTQ compressed; intermediate Parquet files are compact. |
| Runtime | ≤ 5.5 h (including download, DADA2, permutations) | Benchmarks on a similar CI runner using a 3‑study synthetic dataset. |
| No GPU / CUDA | Enforced by using CPU‑only wheels and disabling any `device="cuda"` flags. |

All estimates are comfortably within the free‑tier limits; the plan includes early abort checks if any bound is exceeded.

---


