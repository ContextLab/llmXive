# Research: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Summary of Research

This research phase identifies the specific datasets, tools, and methodological strategies required to implement the plan within the constraints of a CPU‑only GitHub Actions runner. It addresses feasibility of antiSMASH execution, availability of matched genomic/metabolomic data, and statistical challenges posed by small sample sizes. All design decisions respect the observational nature of the study and the success criteria defined in the specification.

## Dataset Strategy

The study requires a matched set of plant species with both high‑quality genome assemblies and quantitative metabolite abundance profiles. No pre‑matched open dataset exists, so we will construct one by intersecting separate public sources.

| Dataset | Role | Source / URL (Verified) | Feasibility & Notes |
| :--- | :--- | :--- | :--- |
| **Genomic Assemblies** | Source of BGC features | **NO verified source found** for a pre‑matched plant genome/metabolome dataset. | Genomes will be fetched programmatically from **NCBI RefSeq** using Biopython. A curated species list (e.g., 1000 Plants initiative) will drive the download. Genomes > 500 MB are skipped to respect runtime limits. |
| **Metabolite Profiles** | Source of targets | **NO verified source found** for a pre‑matched plant genome/metabolome dataset. | Quantitative tables will be retrieved from **MetaboLights** (via API) or **PMDB** where available. Only studies providing numeric abundance tables are retained. |
| **BGC Prediction Tool** | Feature extraction | **NO verified source found** for a pre‑trained model. | **antiSMASH 7.0** (command‑line) is the de‑facto standard. It will be run inside a Docker container on the CI runner; if a species exceeds the genome‑size filter or antiSMASH times out, the species is excluded. |
| **Phylogenetic Tree** | Stratification / PGLS | **NO verified source found** for a pre‑built plant tree. | We will generate a tree by downloading the **1KP (1000 Plants) phylogeny** from the Open Tree of Life repository and pruning it to the species present in our final aligned matrix using `dendropy`. No external URL is cited because no verified source is available; the step is documented and reproducible. |

**Data Alignment Strategy**

1. **Species List** – Defined in `config/species_list.yaml`.  
2. **Download** –  
   * Genomes: `ncbi-genome-download` (FASTA + GFF).  
   * Metabolites: MetaboLights API (CSV/TSV).  
3. **Processing** –  
   * Run antiSMASH on each FASTA; parse JSON to extract BGC type counts and presence.  
   * Map BGC types to MIBiG ontology; fallback to Pfam HMMs for plant‑specific clusters; unmapped → “unknown”.  
   * Harmonize metabolite identifiers to InChIKey, add pseudo‑count = 1, apply log‑transformation.  
4. **Alignment** – Inner join on species name; rows missing either modality are **excluded** (log warning). **Species with zero predicted BGCs are retained** (count = 0, presence = 0) as biologically meaningful data points.  
5. **Output** – `data/processed/aligned_matrix.csv` (features + targets) and `data/processed/phylo_tree.nwk` (pruned tree).  

## Methodological Rigor

### Statistical Approach
- **Models**: Random Forest, Elastic Net, Gradient Boosting (scikit‑learn, CPU‑only) and **Phylogenetic Generalized Least Squares (PGLS)** (statsmodels with custom phylogenetic covariance).  
- **Validation**:  
  * **Leave‑One‑Out (LOO) CV** for N < 20; **5‑Fold CV** (recorded as `"5Fold"` in `model_output.schema.yaml`) when N ≥ 20; both are reported as `cv_method`.  
  * **Bootstrap** (1000 resamples) to obtain confidence intervals for R².  
  * **Phylogenetic Permutation Baseline** – **only metabolite labels are shuffled** while preserving the predictor matrix and phylogenetic tree; repeated until convergence; p‑value computed as proportion of permuted R² ≥ observed R² (addresses Concern methodology‑c739be52).  
- **Metrics**: R², Pearson r, permutation‑derived p‑value.  
- **Multiple Comparisons** – Bonferroni/FDR correction applied when testing multiple metabolite classes.  
- **Power** – With N < 20 the analysis is exploratory; no formal power analysis is feasible. Results are framed as hypothesis‑generating and interpreted with caution (addresses Concern methodology‑f2827a91).  
- **Confounder Limitation** – Environmental metadata, tissue type, developmental stage, and batch are not available for the public datasets; their omission is a limitation that may introduce omitted‑variable bias (addresses Concern methodology‑1deeed41).  
- **Collinearity** – VIF scores calculated; high VIF features are reported but retained due to biological relevance.  
- **Dimensionality Reduction** – PCA applied to BGC feature matrix when feature count > N/2; PGLS operates on PCA‑reduced components (addresses Concern methodology‑f2827a91).  

### Success Criteria Alignment
- **SC‑001** – Null hypothesis (R² = 0) tested via permutation baseline; significance threshold p < 0.05.  
- **SC‑002** – Sensitivity sweep must produce **max |ΔR²| ≤ 0.05**. The pipeline now **fails with a non‑zero exit code** if this bound is exceeded, enforcing the mandatory criterion (addresses Concern methodology‑9d101ccd).  
- **SC‑003** – Overall runtime ≤ 6 h on the free‑tier runner (enforced by runtime monitoring).  
- **SC‑004** – Alignment success rate computed as `#species with both modalities / #species in input list`; required ≥ [deferred]% for N ≥ 5.  

## Compute Feasibility Analysis

- **antiSMASH Runtime** – Approx. 5 min per ≤ 500 MB genome on 2 CPU cores; with ≤ 20 species total runtime ≤ 1.5 h.  
- **Memory** – antiSMASH processes each genome sequentially; peak RAM ≈ several GB.  
- **Overall** – Data download (< 1 GB), preprocessing, PCA, modeling, and permutation baseline comfortably fit within the 7 GB RAM / 6 h limit.  

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| Use NCBI RefSeq for genomes | Reliable, programmatic access, no authentication required. |
| Skip genomes > 500 MB | Guarantees antiSMASH completes within CI time budget. |
| LOO CV for N < 20 | Provides stable performance estimates with limited samples. |
| 5‑Fold CV for N ≥ 20 | Recorded as `"5Fold"` to satisfy schema; aligns with FR‑005 when sample size permits. |
| Phylogenetic permutation after model training | Baseline must compare against a trained model; ordering corrected. |
| PCA before PGLS | Reduces dimensionality to avoid over‑fitting; enforced as a hard dependency. |
| Log‑transform + pseudo‑count for metabolites | Standard practice to handle zeros and skewed distributions. |
| Inner join alignment | Ensures paired analysis; partial rows excluded per spec. Zero‑BGC rows are **retained** as valid data points (see Edge Cases). |
| No fallback for data sources | Aligns with the “FAIL LOUDLY” requirement; any download failure aborts with a clear error message. |
| Schema validation after each major stage | Guarantees conformity to contracts and satisfies Constitution Principle III. |

## Single Source of Truth (SSoT)

All final statistics, performance tables, and feature‑importance rankings are written to **`data/processed/model_metrics.json`**. This file serves as the definitive source for downstream reporting, figure generation, and manuscript preparation, satisfying Constitution Principle IV.
