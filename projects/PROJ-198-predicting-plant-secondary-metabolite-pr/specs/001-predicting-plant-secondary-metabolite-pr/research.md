# Research: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Summary
This research document identifies concrete open data sources, tools, and statistical strategies that satisfy the feature specification while operating within the CPU‑only GitHub Actions environment. Because no fully‑matched open dataset exists, we will construct a matched matrix by intersecting separate public repositories and augment the genomic feature set with additional functional annotations.

## Dataset Strategy

| Dataset | Role | Feasibility & Notes |
|--------|------|---------------------|
| **Genomic Assemblies** | Provide BGC features | Open FTP site at NCBI RefSeq for plants; genomes larger than 500 MB are automatically skipped to keep runtime within limits. |
| **Metabolite Profiles** | Provide quantitative targets | Open plant metabolite collection **KNApSAcK** (http://www.knapsackfamily.com/knapsack_jsp/information.jsp). Provides InChIKey‑linked abundance tables across many species; heterogeneous experimental conditions are noted as a limitation. |
| **Phylogenetic Tree** | Enable phylogenetic stratification & PGLS | Obtained programmatically via the Open Tree of Life API (small Newick file < 5 MB). |
| **Ecological & Trait Covariates** | Control non‑phylogenetic confounds | Retrieved from the **TRY Plant Trait Database** (https://www.try-db.org/). Includes habitat, tissue type, and growth form where available. |
| **BGC Prediction Tool** | Extract BGC presence/count | antiSMASH 7.0 Docker image `antismash/antismash:7.0`. Runs on CPU; each genome processed sequentially. |
| **MIBiG Ontology** | Map BGC types to metabolite classes | MIBiG 3.0 JSON file, publicly hosted on the MIBiG website. |

**Data Alignment Workflow**
1. **Species List** – Defined in `config/species_list.yaml`.  
2. **Genome Download** – `code/data/download.py` uses a Biopython‑based FTP client to fetch FASTA + GFF files.  
3. **Metabolite Download** – `code/data/download.py` retrieves the KNApSAcK CSV, parses InChIKeys, and stores under `data/raw/metabolites/`.  
4. **Covariate Download** – `code/data/download.py` pulls trait data from TRY and writes `data/raw/covariates.tsv`.  
5. **antiSMASH Execution** – Dockerized antiSMASH runs on each genome; JSON output parsed by `code/data/antismash.py`.  
6. **Ontology Mapping** – BGC types matched to MIBiG 3.0; unmatched → `'unknown'`.  
7. **Metabolite Harmonization** – InChIKey standardization, pseudo‑count = 1, log‑transform (`log(x+1)`). Output: `data/processed/metabolite_harmonized.csv`.  
8. **Alignment** – Inner join on species name; rows missing either modality are logged (warning) and excluded. Species with zero BGCs are retained (count = 0). Output: `data/processed/aligned_matrix.csv`.  

## Statistical Approach (Methodological Rigor)

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Primary Model** | Phylogenetic Generalized Least Squares (PGLS) | Pre‑registered primary analysis per methodology‑3d60dfa9; accounts for shared ancestry (FR‑010). |
| **Exploratory Models** | Random Forest, Elastic Net, Gradient Boosting (scikit‑learn) | Provide complementary non‑linear and regularized perspectives; treated as exploratory with Bonferroni correction across the three models. |
| **Cross‑Validation** | Leave‑One‑Out (LOO) when N < 20; 5‑Fold CV when N ≥ 20 (recorded as `cv_method`). | Maximises data usage for small N; aligns with SC‑004. |
| **Bootstrap** | 1000 resamples to obtain 95 % CI for R². | Provides uncertainty estimates given limited sample size. |
| **Permutation Baseline** | Phylogenetic label‑permutation (shuffle metabolite values, keep BGC matrix & tree). 1000 permutations; p‑value = proportion ≥ observed R². | Satisfies SC‑001 and Constitution Principle VII. |
| **Multiple Comparisons** | Bonferroni correction across the three exploratory models; FDR correction across metabolite classes. | Controls family‑wise error. |
| **Collinearity** | Compute VIF for each BGC feature; report but retain biologically relevant predictors. | Acknowledges multicollinearity (FR‑009). |
| **Dimensionality Reduction** | Apply PCA to BGC matrix if `#features > N/2`; retain components explaining ≥ 90 % variance before PGLS. | Prevents over‑fitting with limited samples. |
| **Covariate Inclusion** | Add ecological niche, tissue type, and growth habit from TRY as additional regressors. | Addresses non‑phylogenetic confounds (methodology‑e127a4aa). |
| **Power Analysis** | Simulation‑based power estimation (see plan.md). Report required N≈35 for [deferred] power to detect R² = 0.15; acknowledge exploratory nature. | Addresses methodology‑a0abd40a. |
| **Construct Validity** | Supplement BGC count with PFAM domain diversity and antiSMASH confidence scores; explicitly frame results as associative. | Addresses methodology‑ff795ba0. |
| **Sensitivity Sweep** | Vary antiSMASH confidence threshold (0.3, 0.5, 0.7). Abort pipeline if max |ΔR²| > 0.05 (SC‑002). | Guarantees robustness. |
| **Non‑phylogenetic Confounds** | Include covariates; perform sensitivity checks with/without them. | Mitigates hidden confounding. |
| **Metrics** | R², Pearson r, permutation p‑value, feature importance (RF), coefficient magnitudes (Elastic Net). | Directly addresses SC‑001 & FR‑006. |
| **Power Reporting** | Effect sizes with bootstrap CIs; discuss limited N. | Transparent limitation. |

## Success Criteria Alignment
- **SC‑001** – Permutation baseline p‑value < 0.05 required for claim of predictive signal.  
- **SC‑002** – Sensitivity sweep enforced via exit‑code; max |ΔR²| ≤ 0.05.  
- **SC‑003** – CI timer monitors total runtime; failure if > 6 h.  
- **SC‑004** – Alignment success rate computed over full input list; must meet deferred threshold for N ≥ 5 (asserted in `align.py`).  

## Compute Feasibility
- antiSMASH 7.0 Docker image runs on CPU; each genome ≤ 5 min for assemblies ≤ 500 MB.  
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
| Add `.flake8` and `.env.example` generation | Meets verification requirements (T002). |
| Restrict outputs to project‑owned directories | Avoids writing to platform‑owned `state/` (T005). |
| Robust retry and timeout handling for download & antiSMASH | Addresses failures in T006, T007, T010. |
| Explicit covariate download from TRY | Mitigates non‑phylogenetic confounds (T009). |
| Config loading guard & alignment stats JSON | Fixes configuration load error and ensures `alignment_stats.json` (T018). |

## Single Source of Truth (SSoT)
All final statistics, performance tables, and feature‑importance rankings are written to **`data/processed/model_metrics.json`**. This file is the definitive artifact for downstream reporting and figure generation.

---

