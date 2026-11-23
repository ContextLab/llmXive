# Research: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

## Scientific Background

Hydrothermal vents host unique microbial communities adapted to extreme gradients of temperature, pH, and chemical composition. Ocean acidification (OA) driven by increased atmospheric CO2 is lowering ocean pH, but localized acidification near vents can be exacerbated by vent fluid chemistry. Understanding how microbial community composition shifts in response to pH gradients is critical for using these communities as bioindicators of OA. However, 16S rRNA sequencing data is compositional and sparse, requiring rigorous normalization (rarefaction) and statistical methods (PERMANOVA, LME) to avoid spurious correlations.

## Dataset Strategy

The project requires three data types: 16S rRNA sequencing data (FASTQ or OTU/ASV tables), pH sensor logs, and temperature sensor logs.

### Verified Datasets

Based on the `# Verified datasets` block provided:

| Dataset Type | Source | URL | Status | Notes |
|--------------|--------|-----|--------|-------|
| **OTU Table** | bio-ontology-research-group | ` | **Available** | Contains OTU taxonomy. Must be validated for vent-specific samples and environmental metadata. |
| **OTU Table** | otuzucbit | ` | **Available** | Parquet format. Requires schema inspection for vent/pH metadata. |
| **OTU Table** | kali-ai | ` | **Available** | JSON format. |
| **Audio Spoofing** | LanceaKing | ` | **Mismatch** | Audio spoofing dataset (ASVspoof), not microbial. **Excluded.** |
| **Audio Spoofing** | DynamicSuperbPrivate | ` | **Mismatch** | Audio spoofing dataset. **Excluded.** |

**Critical Gap Analysis**:
- The spec requires **16S rRNA sequencing data** *concurrent* with **pH and temperature logs** from **submarine hydrothermal vents**.
- The verified OTU datasets (bio-ontology-research-group, otuzucbit, kali-ai) are general OTU repositories or specific paper artifacts. They **do not explicitly state** in their URLs or metadata descriptions that they contain *simultaneous* pH and temperature sensor logs from hydrothermal vents.
- The ASV datasets listed (LanceaKing, DynamicSuperbPrivate) are audio spoofing datasets and are irrelevant. **These are excluded.**
- **Action Plan**:
 1. **Primary Strategy**: Attempt to load the `bio-ontology-research-group` OTU table. Inspect metadata columns for `pH`, `temperature`, `location`, and `timestamp`.
 2. **Fallback Strategy**: If the verified OTU tables lack the required concurrent environmental data, the project will **generate a realistic synthetic dataset** that adheres to the biological constraints (pH 1.0–10.0, vent-like community composition) to demonstrate the pipeline's functionality.
 3. **Scientific Limitation**: **Crucially**, synthetic data is used **only for Pipeline Validation** (testing code logic, schema compliance, and statistical flow). It **cannot** validate the scientific claim that "microbial shifts are indicators of ocean acidification." The research question regarding *real* ocean acidification remains unanswerable with the current verified resources. The plan explicitly states this distinction to avoid conflating code correctness with scientific discovery.

**Decision**: The pipeline will be designed to accept *any* CSV/TSV/Parquet input. The `research.md` will document the attempt to use `bio-ontology-research-group` and the subsequent fallback to synthetic data generation if environmental metadata is missing.

## Methodological Rigor

### Statistical Framework

1. **Alpha Diversity (FR-002, US-2)**:
 - **Method**: Shannon and Simpson indices calculated on rarefied data.
 - **Rarefaction**: Depth set to `[deferred]` (defaulting to [deferred] reads for testing, configurable). Sensitivity analysis (SC-003) will sweep depths {5k, 10k, [deferred]}.
 - **Collinearity**: Temperature is included as a covariate. Variance Inflation Factor (VIF) will be calculated (SC-004). If VIF > 5, temperature is flagged as a confounder.
 - **Model**: Linear Mixed-Effects (LME) with `pH` as fixed effect and `site` as random effect. If < 2 sites, fallback to OLS linear regression.
 - **Robustness**: To address compositional artifacts, the analysis will also explore **log-ratio transforms (e.g., CLR)** if the LME assumptions (Gaussian residuals) are violated. Alternatively, a **Generalized Linear Mixed Model (GLMM)** with a Gamma distribution (for positive continuous diversity indices) or Negative Binomial (for counts) will be considered.
 - **Caveat**: Explicitly state that this is an **associational** analysis (FR-003.1).

2. **Beta Diversity & Clustering (FR-004, US-3)**:
 - **Distance**: Bray-Curtis dissimilarity.
 - **Dispersion Check**: `betadisper` (test for homogeneity of multivariate dispersions) *before* PERMANOVA.
 - **Decision Rule**:
 - If `betadisper` is **not significant** (p >= 0.05): Proceed with PERMANOVA.
 - If `betadisper` is **significant** (p < 0.05): The PERMANOVA result is flagged as **confounded by heteroscedasticity**. The primary interpretation will rely on the **PERMDISP** (dispersion test) result or a **distance-based linear model (distLM)** that accounts for dispersion, rather than the PERMANOVA F-statistic. **Subsampling is NOT used to fix dispersion.**
 - **Variance Partitioning**: To isolate pH effects, a **distance-based Redundancy Analysis (dbRDA)** will be performed with pH as the primary variable and temperature as a covariate. This quantifies the unique variance explained by pH after controlling for temperature, addressing the "indicator" claim.
 - **Unbalanced Data**: If sample counts per pH group differ by >2x, rarefaction/subsampling is applied to balance groups *only if* it does not introduce bias, but the primary concern remains dispersion.

3. **Ordination (FR-005)**:
 - **Method**: PCoA first. If stress > 0.2, switch to NMDS.
 - **Visualization**: Points colored by pH level.

### Multiple Comparison & Power

- **Multiple Comparisons**: If multiple diversity metrics or pH thresholds are tested, Bonferroni or Benjamini-Hochberg correction will be applied.
- **Power Analysis**: The plan acknowledges that with < 10 samples per group (Edge Case), statistical power is low.
 - **Multivariate Alternative**: For low-sample scenarios where PERMANOVA is underpowered, the plan will use a **Mantel test** (with caution) or **distance-based redundancy analysis (dbRDA)** with reduced permutations to test for community structure differences. **Spearman correlation is NOT used for multivariate data.**

### Dataset-Variable Fit

- **Requirement**: The dataset *must* contain `pH`, `temperature`, and `16S` counts.
- **Risk**: The verified OTU datasets may lack `pH` and `temperature`.
- **Mitigation**: If the verified data lacks these variables, the project **cannot** answer the specific research question using that data. The plan explicitly states this gap. The implementation will generate synthetic data that *does* contain these variables to validate the *pipeline logic*, but the results will be labeled as "Synthetic Validation" rather than "Empirical Discovery".

## Compute Feasibility

- **CPU-First**: The pipeline uses `scipy`, `statsmodels`, and `pandas`. These are CPU-tractable.
- **Memory**: 16S count tables are typically sparse matrices. We will use `scipy.sparse` to handle large datasets within 7 GB RAM.
- **Disk**: Raw FASTQ files are large. The pipeline will stream them or process in chunks. If the full dataset exceeds 14 GB, we will subsample (first N reads) or use streaming.
- **No GPU Required**: No deep learning models (e.g., transformers) are planned. All methods are classical statistics.

## Data Availability & Ethics

- **Source**: Only verified URLs from the `# Verified datasets` block will be used. If they do not fit, synthetic data is generated.
- **No Gated Data**: No ADNI, HCP, or clinical data requiring credentials is used.
- **Reproducibility**: All random seeds are pinned. Synthetic data generation is deterministic.