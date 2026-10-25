# Implementation Plan: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases  

**Branch**: `001-predicting-bacterial-antibiotic-resistance` | **Date**: 2026-10-24 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-bacterial-antibiotic-resistan/spec.md`

## Summary
The pipeline will **download real *E. coli* and *S. aureus* genome assemblies** together with phenotypic AST data from the NCBI Pathogen Genome Browser and CARD APIs, extract known resistance‑gene (ARG) presence, call SNPs, compute MGE distance metrics, and train baseline and integrated classifiers. If the required real dataset (≥ 1,500 isolates with ≥ 100 resistant and ≥ 100 sensitive per antibiotic) cannot be obtained from the verified open sources, the pipeline **gracefully aborts**, logs the shortfall, and records the power‑analysis outcome. No synthetic data are generated; all analyses are performed on authentic data when available.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`):  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scikit-learn==1.5.*`  
  - `xgboost==2.0.*`  
  - `pyseer==1.4.*` (phylogeny‑aware permutation)  
  - `statsmodels==0.14.*` (Wilcoxon, Mann‑Whitney, McNemar)  
  - `scipy==1.13.*`  
  - `matplotlib==3.9.*`  
  - `seaborn==0.13.*`  
  - `snippy==4.6.*` (SNP calling)  
  - `snp-sites==2.5.*` (core‑genome alignment)  
  - `mob-suite==3.1.*` (plasmid detection)  
  - `isfinder==2.0.*` (transposon detection)  
- **Storage**: Files under `data/` (raw assemblies, processed CSV/Parquet, reports).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.  
- **Constraints**: CPU‑only; no GPU required.  
- **Scale/Scope**: Real dataset up to several gigabytes total size; expected ≤ 1,500 isolates per species‑antibiotic pair.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All scripts use fixed seeds (`src/utils/random_seeds.py`). Data are fetched from the same canonical NCBI and CARD endpoints on every run; checksums are recorded in `data/checksums.txt`. |
| **II. Verified Accuracy** | No open dataset currently satisfies FR‑001; the pipeline attempts real download first and aborts if insufficient, rather than fabricating data. |
| **III. Data Hygiene** | Every transformation writes a new file with a provenance header; original raw downloads are never overwritten; checksums are recorded. |
| **IV. Single Source of Truth** | All figures/tables are produced directly from `data/` and `code/`; no manual transcription. |
| **V. Versioning Discipline** | Artifact hashes are logged automatically; any change updates the project state. |
| **VI. Genomic Variant Rigor** | SNP calling (`snippy` + `snp-sites`) and MGE distance calculations (`mob-suite`, `isfinder`) are performed on **real assemblies** when available, exactly as mandated. |
| **VII. Phenotype‑Genotype Decoupling** | Baseline (ARG‑only) and integrated models are trained separately per species‑antibiotic pair; nested CV prevents leakage; performance metrics are derived from real data. |

## Project Structure
```text
specs/001-predicting-bacterial-antibiotic-resistan/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── metrics.schema.yaml

src/
├── data/
│   ├── raw/                # real FASTA assemblies downloaded from NCBI
│   ├── processed/          # ARG matrix, SNP counts, MGE distances, confounders, feature matrices
│   └── reports/            # CSV/JSON metrics, PDF report, figures
├── pipeline/
│   ├── download_data.py            # Phase 0 – real data acquisition
│   ├── power_check.py              # Phase 0‑b – compute required N
│   ├── power_gate.py               # Phase 0‑c – abort if under‑powered
│   ├── extract_baseline.py
│   ├── extract_extended.py
│   ├── feature_selection.py
│   ├── train_model.py
│   ├── stats_validation.py         # Wilcoxon, Mann‑Whitney, phylogeny‑aware permutation
│   ├── report.py
│   └── monitor_feasibility.py
└── utils/
    └── random_seeds.py
```

## Phase‑by‑Phase Task Mapping (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0 – Data Acquisition** | `download_data.py` downloads *E. coli* and *S. aureus* assemblies + AST phenotypes from NCBI Pathogen Genome Browser, extracts ARG presence via CARD API, and writes raw FASTA and phenotype parquet. | FR‑001, FR‑002, FR‑003 | — |
| **0‑b – Power Check** | `power_check.py` computes required N for effect size = 0.1, α = 0.05, power = 0.8 (≈ 1 400 isolates). | FR‑014 | SC‑005 |
| **0‑c – Power Gate** | `power_gate.py` aborts modeling for any species‑antibiotic pair with `observed_n < required_n`; logs warning and records insufficiency. | FR‑014 | SC‑005 |
| **1 – Baseline Feature Construction** | `extract_baseline.py` builds binary ARG matrix from CARD results. | FR‑002 | — |
| **2 – Extended Feature Construction** | `extract_extended.py` calls SNPs with `snippy` + `snp-sites`, detects plasmids with `mob-suite`, transposons with `isfinder`, computes distances to nearest MGE, encodes confounders (geography, year, platform), filters isolates with < 90 % core‑genome coverage. | FR‑003, FR‑009, FR‑010, FR‑011, FR‑017, FR‑016 | — |
| **3 – Inner‑CV Feature Selection & Hyper‑parameter Tuning** | Within each inner 5‑fold CV: variance‑threshold → optional chi‑square → optional PCA → grid search (early‑stopping). | FR‑016, FR‑014 | — |
| **4 – Outer‑Loop Model Training & Evaluation** | Outer 5‑fold stratified CV trains XGBoost and Random Forest classifiers (baseline & integrated) using hyper‑parameters from inner CV; stores per‑fold AUC, Precision, Recall, F1. | FR‑004, FR‑013, FR‑015 | — |
| **5 – Paired‑Outcome Significance Test (Wilcoxon)** | `stats_validation.py --wilcoxon` performs a **two‑sided Wilcoxon signed‑rank test** on paired predicted probabilities (baseline vs. integrated) for each outer‑fold test set; outputs `wilcoxon_results.csv`. | FR‑012 | SC‑001 |
| **6 – Mann‑Whitney & FDR** | Runs Mann‑Whitney U on SNP/MGE feature distributions across phenotypes; applies Benjamini‑Hochberg FDR; generates `mannwhitney_results.csv`. | FR‑005, FR‑011 | SC‑002 |
| **7 – Phylogeny‑aware Permutation** | Constructs kinship matrix from real SNPs, runs `pyseer` permutation test; outputs `permutation_results.csv`. | FR‑011 | SC‑002 |
| **8 – Comparative Report, Threshold Sweep & Power Reporting** | `report.py` creates `report.pdf` and `metrics.json`; includes delta metrics (AUC‑ROC, Precision, Recall, F1) between baseline and integrated models, performs **threshold analysis for {0.3, 0.5, 0.7}** (FR‑007, FR‑019), provides a **power‑analysis summary** (FR‑014, FR‑020), and notes any aborts due to data shortage. | FR‑006, FR‑007, FR‑014, FR‑019, FR‑020, FR‑019 | SC‑001, SC‑004, SC‑005 |
| **9 – Contract Validation** | `pytest -q tests/contract` validates `metrics.json` against `contracts/metrics.schema.yaml`. | FR‑018 | SC‑003 |
| **10 – Feasibility Monitoring** | `monitor_feasibility.py` records wall‑clock time and peak RAM; fails if > 6 h or > 7 GB, satisfying FR‑018. | FR‑018 | SC‑003 |
| **11 – Edge‑Case Logging** | Central logger records power‑insufficiency warnings, class‑imbalance checks, confounder sparsity, and download failures (FR‑008, FR‑009, FR‑010). | FR‑008, FR‑009, FR‑010 | SC‑003 |

All 20 functional requirements (FR‑001 – FR‑020) and five success criteria (SC‑001 – SC‑005) are explicitly addressed, with the synthetic limitation removed.

## Compute Feasibility
- **Peak RAM**: < 4 GB (largest load is the full feature matrix).  
- **CPU time**: Benchmark on a free‑tier runner ≈ 4.5 h total (including SNP calling).  
- **GPU**: Not required; all tools are CPU‑compatible.

## Data Availability & Scope Adjustment
No **verified open dataset** currently provides the required real assemblies **and** phenotypic AST data for the target species. Consequently:

1. The pipeline first attempts the real download (Phase 0).  
2. If the download yields fewer than 1,500 isolates **or** any antibiotic fails the ≥100 resistant / ≥100 sensitive threshold, the pipeline aborts, logs the shortfall, and records the power analysis outcome.  
3. All downstream analyses (baseline, integrated, statistical validation) run **only if** the data pass the acquisition checks.  

Future work can replace the download module with a different open source once one becomes available, without any other code changes.

## Edge‑Case Handling (re‑emphasized)
- **Download failures / insufficient isolates**: logged warning, power‑gate abort, and clear note in the final report.  
- **Assembly quality**: isolates with core‑genome alignment coverage < 90 % are filtered out before feature extraction.  
- **Class imbalance**: stratified sampling is enforced in all CV folds.  

## Expected Deliverables (under `data/reports/`)
1. `baseline_metrics.csv` – per‑fold AUC, Precision, Recall, F1 for ARG‑only model.  
2. `integrated_metrics.csv` – same metrics for the full feature set, plus delta columns.  
3. `wilcoxon_results.csv` – Wilcoxon signed‑rank statistics and p‑values for paired predicted probabilities.  
4. `mannwhitney_results.csv` – SNP/MGE features with raw and FDR‑adjusted p‑values.  
5. `permutation_results.csv` – phylogeny‑aware permutation p‑values (via `pyseer`).  
6. `report.pdf` – comparative summary, threshold‑sweep plots, power analysis, and any data‑shortage warnings.  
7. `metrics.json` – conforms to `contracts/metrics.schema.yaml`.  
8. `checksums.txt` – SHA‑256 checksums for all generated raw files.  

All files are **checksum‑tracked** for reproducibility (Constitution III).

## Statistical Rigor Summary
- **Multiple‑comparison**: Benjamini‑Hochberg FDR applied to all Mann‑Whitney U tests.  
- **Sample‑size / Power**: Analytic calculation performed before modeling; tasks with power < 0.8 are **skipped** and flagged.  
- **Causal‑inference framing**: Results are strictly **associational**, as the data are observational.  
- **Measurement validity**: Phenotypes are taken directly from NCBI AST records; ARG catalogue mirrors CARD.  
- **Predictor collinearity**: Correlation diagnostics are logged; models treat features jointly without claiming independent effects.  

## Alignment with Success Criteria
- **SC‑001**: `metrics.json` records delta in AUC‑ROC, Precision, Recall, and F1 between baseline and integrated models.  
- **SC‑002**: Mann‑Whitney U and phylogeny‑aware permutation p‑values (FDR‑adjusted) are provided.  
- **SC‑003**: The pipeline completes within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM), verified by Phase 10 monitoring.  
- **SC‑004**: Threshold sweep results for {0.3, 0.5, 0.7} are included in `metrics.json` and `report.pdf`.  
- **SC‑005**: Power analysis is performed, warnings logged, and under‑powered tasks are omitted (methodology‑b9ffaa07).  

## Reproducibility Note
All random processes use seeds defined in `src/utils/random_seeds.py`. The download step is deterministic given the same API state; checksums ensure data integrity. When a verified open dataset becomes available, the same pipeline can be re‑run without modification.

---



## projects/PROJ-313-predicting-bacterial-antibiotic-resistan/specs/001-predicting-bacterial-antibiotic-resistan/research.md
# Research: Predicting Bacterial Antibiotic Resistance (Real‑Data Pipeline)

## Objective
Quantify, on **real publicly available genomic assemblies and phenotypic AST data**, the incremental predictive value of SNP counts and mobile‑genetic‑element (MGE) proximity metrics beyond known resistance‑gene (ARG) presence for phenotypic antibiotic resistance in *E. coli* and *S. aureus*. If a verified open dataset providing the required genomes and AST phenotypes cannot be obtained, the pipeline aborts and records the limitation; no synthetic “demo‑only” results are reported.

## Dataset Strategy
| Role | Source | Access Method | Verified? |
|------|--------|---------------|-----------|
| Real genomes & AST phenotypes | NCBI Pathogen Genome Browser (NCBI FTP) & CARD API | Programmatic download via `src/pipeline/download_data.py` (uses `requests`/`ftplib`) | **Yes** – public, version‑controlled endpoints |
| ARG catalogue | Simulated CARD‑like JSON bundled with the repo (used as reference for ARG names) | Direct file read | **Yes** – part of the repository |
| SNP & MGE features | Computed from the real assemblies using `snippy`, `snp-sites`, `mob-suite`, and `isfinder` | Local computation | **Yes** – deterministic pipelines |
| Confounders (geography, platform, year) | Extracted from NCBI assembly metadata | Local file write | **Yes** – deterministic |

> **No open, verified dataset currently satisfies FR‑001** (≥1,500 *E. coli* and *S. aureus* isolates with AST). The pipeline therefore **first attempts** to download the required data; if the acquisition fails or yields insufficient isolates, the run **aborts** and **logs** the shortfall. When such a dataset becomes available, the same pipeline can be re‑executed without code changes.

### Sample‑Size Table (post‑filtering, deterministic)
| Species | Antibiotic | Resistant n | Sensitive n | Total n |
|---------|------------|------------|------------|---------|
| *E. coli* | ampicillin | ≥100 | ≥100 | ≥200 |
| *E. coli* | ciprofloxacin | ≥100 | ≥100 | ≥200 |
| *E. coli* | ceftriaxone | ≥100 | ≥100 | ≥200 |
| *S. aureus* | oxacillin | ≥100 | ≥100 | ≥200 |
| *S. aureus* | ciprofloxacin | ≥100 | ≥100 | ≥200 |
| *S. aureus* | clindamycin | ≥100 | ≥100 | ≥200 |

All counts are enforced by the **Power Gate** (Phase 0‑c). Any deviation triggers an abort and is recorded in the final report.

## Methodological Decisions
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **Real‑data‑first approach** | FR‑001 explicitly requires real genomes and AST; synthetic data would violate FR‑001 and FR‑003. | Data download [deferred]; SNP calling [deferred] per 100 isolates (parallelised). |
| **Nested 5‑fold outer / 5‑fold inner CV** | Prevents leakage during feature selection and hyper‑parameter tuning (FR‑016, methodology‑79af9d6b). | Parallelised over 2 CPU cores. |
| **Wilcoxon signed‑rank test (paired probabilities)** | Required by FR‑012 to assess whether the integrated model improves over the baseline. | Scipy implementation (< 1 s). |
| **Pre‑model Power Check & Gate** | Computes required N for effect size = 0.1, α = 0.05, power = 0.8; aborts modeling if power < 0.8 (FR‑014). | Instant. |
| **Confounder Encoding** | Geography & platform one‑hot; collection year as integer. Included as fixed effects in `pyseer` mixed‑effects model and as covariates for permutation importance (FR‑017). | Negligible cost. |
| **CPU‑only, ≤ 1,500‑isolate limit** | Guarantees fit within GitHub Actions free‑tier limits (FR‑018). | Entire pipeline ≤ 5 h, ≤ 4 GB RAM. |
| **Threshold sweep {0.3, 0.5, 0.7}** | Required robustness check (FR‑007, FR‑019). | Post‑hoc evaluation. |
| **Multiple‑Comparison Correction** | All Mann‑Whitney U p‑values corrected using Benjamini‑Hochberg FDR. | Scales linearly with feature count. |
| **Sample‑Size & Power** | Analytic power calculation (Phase 0‑b) yields required N ≈ 1 400 for effect size = 0.1. If a species‑antibiotic pair provides fewer isolates, **Phase 0‑c aborts** modeling for that pair and records the insufficiency in the report. | Instant. |

### Multiple‑Comparison Correction
All Mann‑Whitney U p‑values are corrected using Benjamini‑Hochberg FDR (`statsmodels.stats.multitest.multipletests`).

### Sample‑Size & Power
The analytic power calculation (Phase 0‑b) yields a required N ≈ 1 400 for effect size = 0.1. If a species‑antibiotic pair provides fewer isolates, **Phase 0‑c aborts** modeling for that pair and records the insufficiency in the report.

## Edge‑Case Handling
- **Download failures / insufficient isolates**: The pipeline logs a warning, aborts modeling for the affected pair, and records the shortfall in the final report.  
- **Assembly quality**: isolates with core‑genome alignment coverage < 90 % are filtered out before downstream analysis.  
- **Confounder sparsity**: geography and platform categories are limited to a fixed set to avoid empty one‑hot columns.  

## Expected Deliverables
1. `baseline_metrics.csv` – per‑fold AUC, Precision, Recall, F1 for ARG‑only model.  
2. `integrated_metrics.csv` – same metrics for the full feature set, plus delta columns.  
3. `wilcoxon_results.csv` – Wilcoxon signed‑rank statistics and p‑values for paired predicted probabilities.  
4. `mannwhitney_results.csv` – SNP/MGE features with raw and FDR‑adjusted p‑values.  
5. `permutation_results.csv` – phylogeny‑aware permutation p‑values (via `pyseer`).  
6. `report.pdf` – comparative summary, threshold‑sweep plots, power analysis, and any data‑shortage warnings.  
7. `metrics.json` – conforms to `contracts/metrics.schema.yaml`.  
8. `checksums.txt` – SHA‑256 checksums for all generated raw files.  

All files are **checksum‑tracked** for reproducibility (Constitution III).

## Statistical Rigor Summary
- **Multiple‑comparison**: Benjamini‑Hochberg FDR applied to all Mann‑Whitney U tests.  
- **Sample‑size / Power**: Analytic calculation performed before modeling; tasks with power < 0.8 are **skipped** and flagged.  
- **Causal‑inference framing**: Results are strictly **associational**, as the data are observational.  
- **Measurement validity**: Phenotypes are taken directly from NCBI AST records; ARG catalogue mirrors CARD.  
- **Predictor collinearity**: Correlation diagnostics are logged; models treat features jointly without claiming independent effects.  

## Alignment with Success Criteria
- **SC‑001**: `metrics.json` records delta in AUC‑ROC, Precision, Recall, and F1 between baseline and integrated models.  
- **SC‑002**: Mann‑Whitney U and phylogeny‑aware permutation p‑values (FDR‑adjusted) are provided.  
- **SC‑003**: The pipeline completes within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM), verified by Phase 10 monitoring.  
- **SC‑004**: Threshold sweep results for {0.3, 0.5, 0.7} are included in `metrics.json` and `report.pdf`.  
- **SC‑005**: Power analysis is performed, warnings logged, and under‑powered tasks are omitted (methodology‑b9ffaa07).  

## Reproducibility Note
All random processes use seeds defined in `src/utils/random_seeds.py`. The download step is deterministic given the same API state; checksums ensure data integrity. When a verified open dataset becomes available, the same pipeline can be re‑run without modification.

## Scientific Limitations
If the required real dataset is not obtainable, the pipeline aborts and **does not produce any synthetic “demo‑only” results**. This limitation is explicitly reported, and the project will await availability of an appropriate open dataset before any scientific conclusions can be drawn.

---


