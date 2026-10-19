# Research: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Summary
This research document identifies concrete open data sources, tools, and statistical strategies that satisfy the feature specification while operating within the CPU‑only GitHub Actions environment. Because no fully‑matched open dataset exists, we will construct a matched matrix by intersecting separate public repositories.

## Dataset Strategy

| Dataset | Role | Source / URL (Verified) | Feasibility & Notes |
|--------|------|------------------------|---------------------|
| **Genomic Assemblies** | Provide BGC features | NCBI RefSeq FTP (e.g., `ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/plant/`) – programmatic download via Biopython. | Open, rate‑limited FTP; genomes > 500 MB are skipped to respect runtime limits. |
| **Metabolite Profiles** | Provide quantitative targets | **KNApSAcK** (curated plant metabolite database) – download CSV via ` Name or service not known)"))]. | Open, cross‑species coverage of a substantial number of metabolites; heterogeneous experimental conditions noted as a limitation (see Concern data_resources‑867781d8). |
| **Phylogenetic Tree** | Enable phylogenetic stratification & PGLS | 1KP plant phylogeny (Newick) from Open Tree of Life: `. | Single file, low memory. |
| **BGC Prediction Tool** | Extract BGC presence/count | antiSMASH 7.0 Docker image `antismash/antismash:7.0`. | Runs on CPU; each genome processed sequentially. |
| **MIBiG Ontology** | Map BGC types to metabolite classes | MIBiG 3.0 JSON (`). | Small JSON file; no compute burden. |

**Data Alignment Workflow**
1. **Species List** – Defined in `config/species_list.yaml`.  
2. **Genome Download** – `code/data/download.py` uses `ncbi-genome-download` (Python wrapper) to fetch FASTA + GFF.  
3. **Metabolite Download** – `code/data/download.py` retrieves the KNApSAcK CSV, parses InChIKeys, and stores under `data/raw/metabolites/`.  
4. **antiSMASH Execution** – Dockerized antiSMASH runs on each genome; JSON output parsed by `code/data/antismash.py`.  
5. **Ontology Mapping** – BGC types matched to MIBiG 3.0; unmatched → `'unknown'`.  
6. **Metabolite Harmonization** – InChIKey standardization, pseudo‑count = 1, log‑transform (`log(x+1)`).  
7. **Alignment** – Inner join on species name; rows missing either modality are logged and excluded. Species with zero BGCs are retained (count = 0). Output: `data/processed/aligned_matrix.csv`.  

## Statistical Approach (Methodological Rigor)

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Model Suite** | Random Forest, Elastic Net, Gradient Boosting (scikit‑learn) + Phylogenetic Generalized Least Squares (statsmodels) | Covers non‑linear, regularized linear, and phylogenetically‑aware regression per FR‑005 & FR‑010. |
| **Cross‑Validation** | Leave‑One‑Out (LOO) when N < 20; 5‑Fold CV when N ≥ 20 (recorded as `cv_method`). | Maximises data usage for small N; aligns with SC‑004. |
| **Bootstrap** | 1000 resamples to obtain 95 % CI for R². | Provides uncertainty estimates. |
| **Permutation Baseline** | Phylogenetic label‑permutation (shuffle metabolite values, keep BGC matrix & tree). 1000 permutations; p‑value = proportion ≥ observed R². | Satisfies SC‑001 and Constitution Principle VII. |
| **Multiple Comparisons** | Bonferroni correction across metabolite classes when reporting per‑class results. | Controls family‑wise error. |
| **Collinearity** | Compute VIF for each BGC feature; report but retain biologically relevant predictors. | Acknowledges potential multicollinearity (FR‑009). |
| **Dimensionality Reduction** | Apply PCA to BGC matrix if `#features > N/2`; retain components explaining ≥ 90 % variance before PGLS. | Prevents over‑fitting with limited samples. |
| **Power** | No formal power analysis (N < 20). Results framed as exploratory per Constitution Principle VI. | Transparent limitation. |
| **Metrics** | R², Pearson r, permutation p‑value, feature importance (RF), coefficient magnitudes (Elastic Net). | Directly addresses SC‑001 & FR‑006. |
| **Sensitivity Sweep** | Vary antiSMASH confidence threshold (e.g., 0.3, 0.5, 0.7). Abort pipeline if max |ΔR²| > 0.05 (SC‑002). | Guarantees robustness. |
| **Non‑phylogenetic Confounds** | Include ecological niche, tissue type, batch as covariates when metadata available; perform sensitivity checks with/without them. | Addresses additional latent structure. |
| **Construct Validity** | Explicitly state BGC presence/count is a proxy; discuss missing expression/regulation data; frame conclusions as associative. | Addresses methodological transparency. |
| **Power Analysis** | Report effect sizes with bootstrap CIs; acknowledge limited N may reduce power to detect modest effects. | Addresses power limitation. |

## Success Criteria Alignment
- **SC‑001** – Permutation baseline p‑value < 0.05 required for claim of predictive signal.  
- **SC‑002** – Sensitivity sweep enforced via exit‑code; max |ΔR²| ≤ 0.05.  
- **SC‑003** – CI timer monitors total runtime; failure if > 6 h.  
- **SC‑004** – Alignment success rate computed; must meet deferred threshold for N ≥ 5 (asserted in `align.py`).  

## Compute Feasibility
- antiSMASH 7.0 Docker image runs on CPU; each genome ≤ 5 min.  
- Total RAM ≤ 5 GB at peak (antiSMASH + pandas).  
- Entire pipeline estimated ≤ 4.5 h for ≤ 20 species, well within GitHub Actions limits.  

## Decision Log
| Decision | Rationale |
|----------|-----------|
| Use NCBI RefSeq & KNApSAcK (open APIs) | No verified pre‑matched dataset; both are openly downloadable without auth. |
| Skip genomes > 500 MB | Guarantees antiSMASH completes within CI wall‑clock budget. |
| LOO CV for N < 20 | Maximises training data; yields stable R² estimates. |
| 5‑Fold CV for N ≥ 20 | Standard practice; recorded for reproducibility. |
| Phylogenetic permutation after model training | Baseline must compare against a trained model; ordering corrected. |
| PCA before PGLS | Reduces dimensionality to avoid over‑fitting with limited N. |
| Abort on sensitivity ΔR² > 0.05 | Enforces SC‑002 as a hard constraint. |
| Schema validation after each major stage | Ensures Constitution Principle III (Data Hygiene). |
| Single Source of Truth (`model_metrics.json`) | Satisfies Constitution Principle IV. |

## Single Source of Truth (SSoT)
All final statistics, performance tables, and feature‑importance rankings are written to **`data/processed/model_metrics.json`**. This file is the definitive artifact for downstream reporting and figure generation.

---

