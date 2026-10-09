# Research: Pipeline Validation for Gut Microbiome & Cognitive Function Analysis

## Problem Statement
The goal is to validate a complete analysis pipeline that could later be applied to UK Biobank microbiome and cognition data. Because the UK Biobank dataset is access‑gated and may not be available on the CI runner, we **first attempt** to download the real data using provided credentials. If the download fails, the pipeline **automatically falls back** to a deterministic synthetic data generator that reproduces the required schema (field IDs 20400, 20002, antibiotic flag, confounders, etc.). This dual‑strategy ensures that (1) the pipeline is fully functional on CI and (2) the scientific hypothesis will be tested on the **real UKB cohort** when credentials are supplied.

## Dataset Strategy

| Variable | UKB Field | Synthetic Generation Method |
|----------|-----------|------------------------------|
| participant_id | – | UUID (deterministic via seed) |
| age | 21022 | Truncated Normal (μ=65, σ=8, [40,85]) |
| sex | 31 | Binary 0/1 ([deferred] each) |
| bmi | 21001 | Truncated Normal (μ=27, σ=5, [15,45]) |
| diet_quality | 1338 | Beta‑scaled 0‑100 |
| physical_activity | 900 | Log‑Normal MET‑min/week |
| medication_use | 6153 | Binary, age‑dependent |
| antibiotic_use | custom | Binary, age‑dependent |
| microbiome_counts | 20400 | Dirichlet‑Multinomial (on the order of hundreds of genera) |
| reaction_time | 20002 | Normal (μ=600 ms, σ=150) |
| numeric_memory | 20002 | Uniform 0‑100, age‑correlated |
| reasoning | 20002 | Uniform 0‑100, age‑correlated |
| validation_reference | – | Cites UKB cognitive instrument validation papers (FR‑009). |

*The synthetic data are generated with a fixed seed, ensuring that every CI run receives identical files.* No external dataset URLs are used because none satisfy the required schema.  

When real UKB credentials are supplied, the **same pipeline** reads the downloaded files (`data/raw/ukb_microbiome.parquet`, `data/raw/ukb_cognitive.parquet`) and proceeds identically, guaranteeing that all downstream steps are validated on authentic observations.

## Methodological Rigor

### Compositional Data Analysis (ILR)
- **Why ILR?** Microbiome relative abundances lie on a simplex; ILR maps them to Euclidean space, yielding orthonormal coordinates and eliminating the sum‑to‑zero constraint that would invalidate ordinary least‑squares regression.  
- **Reference**: Gloor et al., 2017, *Microbiome datasets are compositional* (to be verified by the Reference‑Validator).

### Statistical Modeling
1. **Primary Model** – Multivariate OLS:  
   `CognitiveScore ~ ILR_taxon + Age + Sex + BMI + DietQuality + PhysicalActivity + MedicationUse`.  
2. **Regularized Models** – Lasso & Ridge (scikit‑learn) to assess multicollinearity robustness.  
3. **Multiple‑Testing** – Benjamini‑Hochberg FDR control (α = 0.05).  
4. **Interaction** – `Age_Group * ILR_taxon` term to test age‑dependent effects without stratifying.  
5. **Reduced Models** – Excluding diet & medication to evaluate over‑control bias (FR‑010).  

All models are fit with `statsmodels` OLS and `scikit‑learn` for regularized variants. Diagnostics (VIF, residual plots) are logged but not required for the synthetic validation.

### Causal Claims
- `causality_claim: false` is written into every result file (FR‑008). The study is explicitly observational; no causal inference methods are applied.

### Power & Sample‑Size
- A **simulation‑based power check** runs on a synthetic N=10,000 cohort, injecting a known effect size β = 0.1 and confirming ≥ 80 % detection power. This validates that the pipeline can detect realistic effects when the real UKB sample size (≈10k) is used.

## Decision / Rationale: CPU vs. GPU
All computations are classical statistics and scale linearly with sample size. No deep‑learning or GPU‑only libraries are required. The pipeline therefore runs entirely on the CPU‑first environment of the GitHub Actions runner. No GPU escape hatch is needed.

## Addressing Spec Constraints
- **FR‑001**: Implemented as a *conditional* step—real download is attempted; synthetic fallback guarantees CI execution.  
- **SC‑001‑SC‑006**: Measured on synthetic data for pipeline sanity; real‑world metrics will be collected when the UKB data become available.  
- **Dataset Mismatch**: Explicitly acknowledged; synthetic data is the only feasible, reproducible source for CI execution, but scientific inference will be performed on real data once accessible.  

---

