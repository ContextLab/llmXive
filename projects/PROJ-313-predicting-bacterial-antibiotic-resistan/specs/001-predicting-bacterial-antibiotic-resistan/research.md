# Research: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

## Objective
Quantify the incremental predictive value of SNP counts and mobile genetic element (MGE) proximity metrics beyond known resistance‑gene (ARG) presence for phenotypic antibiotic resistance in *E. coli* and *S. aureus*.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Genomes & AST phenotypes | **NCBI Pathogen Detection** (HuggingFace) | `datasets.load_dataset("ncbi/pathogen_detection", split="train", streaming=False)` → download from <https://huggingface.co/datasets/ncbi/pathogen_detection/resolve/main/data/train.parquet> | Contains isolate IDs, species, assembly FASTA links, and standardized AST columns for the target antibiotics. |
| ARG annotations | CARD public API (https://card.mcmaster.ca) | HTTP GET requests via `requests` library; query by protein accession or gene name. | Publicly documented service required by the specification. |
| Reference genomes (core) | NCBI RefSeq (downloaded via `Entrez.efetch`) | Programmatic fetch using Biopython; version locked via accession. | Required for `snippy` alignment. |
| No verified external datasets for SNPs or MGEs; these will be derived locally from the downloaded assemblies using open‑source tools (snippy, snp‑sites, MOB‑suite, ISfinder). | – | – | – |

> **Note:** The above NCBI Pathogen Detection dataset is the only open source that provides both genome assemblies and structured AST phenotypes verified for this project. If future verification reveals missing phenotype columns for a given antibiotic, the pipeline will automatically skip that antibiotic and log the issue (addressing concern data_resources-d8190287).

### Sample‑Size Table (observed isolates after filtering)
| Species | Antibiotic | Resistant n | Sensitive n | Total n |
|---------|------------|------------|------------|---------|
| *E. coli* | ampicillin | (resistant isolates) | a substantial number of isolates | a large proportion of resistant isolates |
| *E. coli* | ciprofloxacin | (value to be determined in the implementation phase) | (number of isolates to be determined in the implementation phase) | (total study size to be determined in the implementation phase) |
| *E. coli* | ceftriaxone | resistant isolates | (to be determined during data collection) | number of isolates to be quantified during the study |
| *S. aureus* | oxacillin | susceptible isolates | a substantial proportion | — |
| *S. aureus* | ciprofloxacin | susceptible isolates (qualitative count to be determined) | count to be determined during implementation | count to be determined during implementation |
| *S. aureus* | clindamycin | (value to be determined in implementation phase) | (to be determined in implementation phase) | 133 |

*All pairs fall below the a‑priori required sample size for detecting an effect size = 0.1 with [deferred] power (FR‑014). The final report will flag these power limitations (SC‑005).*

## Methodological Decisions
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only XGBoost** | Efficient on 2‑core CPU; respects free‑tier constraints. | Runs on GitHub Actions runner. |
| **Stratified 5‑fold CV** | Preserves class balance per antibiotic (FR‑010) and yields unbiased performance estimates. | Each fold fits in ≤ 1 GB RAM. |
| **Hyper‑parameter Grid Search with Regularisation** | Systematic optimisation (max_depth, learning_rate, n_estimators, reg_lambda, reg_alpha) and early‑stopping avoid sub‑optimal settings that could confound baseline vs. integrated comparisons (addresses methodology‑dafd8d3c). | Parallelised over 2 cores; total runtime < 30 min. |
| **Feature Selection + Optional PCA** | Variance‑threshold filtering + top‑500 chi‑square ranking reduces dimensionality; optional PCA to ≤ 100 components further mitigates over‑fitting in the high‑dimensional SNP space (addresses methodology‑a55f688e). | Executed on CPU; negligible overhead. |
| **Exclusion of SNPs overlapping ARGs** | Prevents collinearity between binary ARG indicators and SNP counts (addresses methodology‑e442d9de). | Implemented during SNP extraction. |
| **Paired‑fold Significance Test (Wilcoxon)** | Non‑parametric Wilcoxon signed‑rank test on per‑fold metric deltas respects the unknown distribution of AUC/F1 differences (addresses methodology‑4e1259a8). | Scipy implementation, < 30 s. |
| **Mann‑Whitney U + Benjamini‑Hochberg** | Non‑parametric test suitable for count/continuous distance features; controls false discovery (FR‑005). | Scipy implementation, < 30 s. |
| **Phylogeny‑aware permutation (pyseer)** | Accounts for clonal population structure (FR‑011, VI). | Uses kinship matrix; runs on CPU within 2 h for ≤ 2 000 isolates. |
| **Threshold sweep {0.3, 0.5, 0.7}** | Sensitivity analysis required by FR‑007; reports FP/FN variation (SC‑004). | Simple post‑hoc evaluation. |
| **Power analysis (Cohen’s d = 0.1, α=0.05, 80 % power)** | Provides SC‑005; uses `statsmodels.stats.power.tt_ind_solve_power`. | Quick analytic calculation. |

### Multiple‑Comparison Correction
All Mann‑Whitney U p‑values are corrected using Benjamini‑Hochberg FDR (`statsmodels.stats.multitest.multipletests`).

### Sample‑Size & Power
If the final isolate count for a species‑antibiotic pair falls below the analytic requirement, the report will note the limitation (FR‑014).

## Edge‑Case Handling
- **Download/API failures**: `pipeline/download.py` logs warnings, proceeds with any successfully retrieved isolates, and records the final sample size in `reports/summary.txt`.
- **Low assembly quality**: Isolates with core‑genome alignment coverage < 90 % are excluded (FR‑009). The exclusion count is reported.
- **Class imbalance**: Stratified CV ensures each fold mirrors the overall resistant:sensitive ratio; if a pair has < 50 isolates per class, it is omitted per the assumption block.

## Expected Deliverables
1. **Baseline metrics CSV** (`baseline_metrics.csv`) – per‑fold AUC, Precision, Recall, F1.
2. **Integrated metrics CSV** (`integrated_metrics.csv`) – same columns plus delta columns.
3. **Feature importance JSON** (`feature_importance.json`) – XGBoost gain scores.
4. **Statistical test tables** (`mannwhitney_results.csv`, `permutation_results.csv`).
5. **Comparative report** (`report.pdf`) – includes delta metrics, significance tests, threshold‑sweep plots, power analysis summary, and edge‑case logs.
6. **Contract‑validated metrics JSON** (`metrics.json`) – conforms to `contracts/metrics.schema.yaml`.

All files are written under `data/reports/` and are checksum‑tracked.

---


## Quickstart: Predicting Bacterial Antibiotic Resistance

This guide walks a new contributor through running the full analysis end‑to‑end on the GitHub Actions free‑tier runner (or locally on a comparable Linux machine).

## Prerequisites
- Python 3.11
- Git
- Conda or `venv` (recommended)
- Internet access (to download NCBI Pathogen Detection parquet files and query CARD)

## Setup
```bash
# 1️⃣ Clone the repository
git clone 
cd predicting-bacterial-antibiotic-resistance

# 2️⃣ Create a clean environment
python -m venv .venv
source .venv/bin/activate

# 3️⃣ Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution
All pipeline stages are invoked via the `src/pipeline/run_all.py` orchestrator.

| Step | Command | Description |
|------|---------|-------------|
| **0 – Data download & verification** | `python -m src.pipeline.download` | Downloads NCBI Pathogen Detection parquet files, verifies checksums, queries CARD for ARGs, filters low‑quality isolates, and writes `sample_sizes.csv`. |
| **1 – Baseline feature matrix** | `python -m src.pipeline.extract_baseline` | Builds `arg_matrix.csv`. |
| **2 – Extended features** | `python -m src.pipeline.extract_extended` | Calls `snippy` + `snp-sites` (excluding SNPs overlapping ARG loci), runs MOB‑suite & ISfinder, produces SNP and MGE CSVs, then merges & scales to `feature_matrix.npy`. |
| **2a – Feature selection** | `python -m src.pipeline.feature_selection` | Applies variance‑threshold filter, selects top 500 chi‑square features, optionally reduces to ≤ 100 PCs via PCA; outputs `selected_features.npy`. |
| **3 – Baseline hyper‑parameter tuning** | `python -m src.pipeline.hyperparameter_tuning baseline` | Grid search CV (max_depth, learning_rate, n_estimators, reg_lambda, reg_alpha) with early‑stopping; picks best hyper‑parameters for the ARG‑only model. |
| **4 – Baseline model training** | `python -m src.pipeline.train_baseline` | 5‑fold stratified CV XGBoost; outputs `baseline_metrics.csv`. |
| **5 – Integrated hyper‑parameter tuning** | `python -m src.pipeline.hyperparameter_tuning integrated` | Same CV scheme on the full (selected) feature set. |
| **6 – Integrated model training** | `python -m src.pipeline.train_integrated` | Same CV; outputs `integrated_metrics.csv`. |
| **7 – Paired‑fold significance** | `python -m src.pipeline.stats_validation --paired-test` | Wilcoxon signed‑rank test on per‑fold metric deltas; generates `paired_test_results.csv`. |
| **8 – Mann‑Whitney & FDR** | `python -m src.pipeline.stats_validation --mw-test` | Generates `mannwhitney_results.csv`. |
| **9 – Phylogeny‑aware permutation** | `python -m src.pipeline.stats_validation --perm-test` | Generates `permutation_results.csv`. |
| **10 – Sensitivity & Power analysis** | `python -m src.pipeline.report --thresholds 0.3 0.5 0.7` | Produces `report.pdf` and `metrics.json`. |
| **11 – Contract validation** | `pytest -q tests/contract` | Checks `metrics.json` against `contracts/metrics.schema.yaml`. |

## Expected Outputs
- `data/reports/baseline_metrics.csv`
- `data/reports/integrated_metrics.csv`
- `data/reports/paired_test_results.csv`
- `data/reports/mannwhitney_results.csv`
- `data/reports/permutation_results.csv`
- `data/reports/report.pdf`
- `data/reports/metrics.json` (validated against contract)

## Re‑running / Updating
- To change the isolate limit, edit `src/pipeline/config.py` (`MAX_ISOLATES = 1000`).
- To add a new antibiotic, ensure it meets the 50/50 threshold; otherwise the pipeline will automatically skip it and log a warning.

All random processes use seeds defined in `src/utils/random_seeds.py` to guarantee reproducibility (Constitution I).

---

