# Implementation Plan: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

**Branch**: `001-predicting-bacterial-antibiotic-resistance` | **Date**: 2026-10-24 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-predicting-bacterial-antibiotic-resistan/spec.md`

## Summary
The pipeline **first attempts** to download a subset of *E. coli* and *S. aureus* genome assemblies together with phenotypic AST data from the **NCBI Pathogen Genome Browser** and ARG annotations from the **CARD API** (fulfilling FR‑001 and FR‑002). If any download or API step fails, the pipeline **gracefully aborts** the primary scientific analysis, logs the shortfall, and records the limitation in the final report. A deterministic synthetic dataset is then generated **only for pipeline sanity‑checking and documentation purposes**; results derived from synthetic data are clearly labelled “demo‑only” and are **not** used to answer the core research question about real bacterial resistance (addressing methodology‑5dcb84cf and scientific_soundness‑89bc3505).

All downstream analyses (baseline ARG‑only model, integrated SNP + MGE model, statistical validation) are executed **exclusively on real data** when the download succeeds. The synthetic fallback preserves the workflow structure but does not contribute to the primary claim, satisfying Constitution Principle II while avoiding construct‑validity violations.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`):
  - `pandas==2.2.*`
  - `numpy==1.26.*`
  - `scikit-learn==1.5.*`
  - `xgboost==2.0.*`
  - `datasets==2.19.*` (used only for the deterministic synthetic fallback)
  - `pyseer==1.4.*` (phylogeny‑aware permutation)
  - `pysam==0.22.*` (SNP counting on real alignments)
  - `statsmodels==0.14.*`
  - `scipy==1.13.*`
  - `matplotlib==3.9.*`
  - `seaborn==0.13.*`
- **Storage**: Files under `data/` (raw, processed, reports).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.  
- **Constraints**: CPU‑only; no GPU. All tools (`snippy`, `snp-sites`, MOB‑suite, ISfinder) are invoked only when real assemblies are present.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All scripts are deterministic (fixed seeds in `src/utils/random_seeds.py`). Real data download is reproducible via NCBI Entrez utilities and CARD API; synthetic fallback is deterministic and checksum‑verified. |
| **II. Verified Accuracy** | Real data are fetched from the canonical NCBI and CARD endpoints, which are open, programmatically accessible resources. Synthetic fallback is explicitly marked as a demo and does **not** replace the required real dataset. |
| **III. Data Hygiene** | Every transformation writes a new file with a provenance header; checksums are recorded in `data/checksums.txt`. |
| **IV. Single Source of Truth** | All figures/tables are generated directly from `data/` and `code/`; no manual transcription. |
| **V. Versioning Discipline** | Artifact hashes are recorded automatically by the platform. |
| **VI. Genomic Variant Rigor** | When real data are available, SNPs are called with `snippy` followed by `snp-sites`; ARG‑MGE distances are computed using MOB‑suite and ISfinder as prescribed. Synthetic fallback only creates placeholder numeric features for pipeline testing, never for primary analysis. |
| **VII. Phenotype‑Genotype Decoupling** | Baseline ARG‑only model is run as a negative control; integrated model is evaluated separately per species/antibiotic. All metrics derived from nested 5‑fold outer / 5‑fold inner CV to prevent leakage. |

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
│   ├── raw/                # real FASTA assemblies (if download succeeds) or synthetic placeholders (demo only)
│   ├── processed/          # ARG matrix, SNP counts, MGE distances, feature matrices
│   └── reports/            # CSV/JSON metrics, PDF report, figures
├── pipeline/
│   ├── download_real.py               # Phase 0‑a (real data)
│   ├── generate_synthetic.py           # Phase 0‑a (synthetic demo)
│   ├── power_check.py                 # Phase 0‑b
│   ├── power_gate.py                  # Phase 0‑c (abort under‑powered tasks)
│   ├── extract_baseline.py
│   ├── extract_extended.py
│   ├── feature_selection.py
│   ├── train_model.py
│   ├── stats_validation.py            # Wilcoxon, Mann‑Whitney, phylogeny‑aware permutation
│   └── report.py
└── utils/
    └── random_seeds.py
```

## Phase‑by‑Phase Task Mapping (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0‑a – Data Acquisition** | `download_real.py` attempts to fetch *E. coli* and *S. aureus* FASTA assemblies and AST phenotypes from NCBI Pathogen Browser and CARD. If any step fails, the script logs the error, **aborts** downstream modeling, and triggers `generate_synthetic.py` for a demo run. | FR‑001, FR‑002, FR‑008, FR‑009, FR‑014 | SC‑003, SC‑005 |
| **0‑b – Power Check** | `power_check.py` computes required N (≈ 1 400 for effect size = 0.1, α = 0.05, 80 % power). | FR‑014 | SC‑005 |
| **0‑c – Power Gate** | `power_gate.py` **aborts** modeling for any species‑antibiotic pair where `observed_n < required_n`; logs a clear warning and records insufficiency in the final report (addresses methodology‑b9ffaa07). | FR‑014 | SC‑005 |
| **1 – Baseline Feature Construction** | `extract_baseline.py` builds binary ARG presence matrix (`arg_matrix.csv`). | FR‑002 | — |
| **2 – Extended Feature Construction** | `extract_extended.py` (a) aligns reads with `snippy` and calls SNPs with `snp-sites` (real data only); (b) computes genomic distance from each ARG to the nearest transposon (via ISfinder) or plasmid (via MOB‑suite); (c) adds confounder columns (geography, collection date, sequencing platform) encoded as one‑hot or ordinal; (d) filters isolates with < 90 % core‑genome coverage. When synthetic fallback is active, placeholder numeric features are generated but flagged as demo‑only. | FR‑003, FR‑009, FR‑010, FR‑011, FR‑017, FR‑016 | — |
| **3 – Inner‑CV Feature Selection & Hyper‑parameter Tuning** | Inside each **5‑fold inner CV** fold: variance‑threshold filtering → optional chi‑square ranking → optional PCA → grid search with early‑stopping. All steps occur within the inner fold to prevent leakage (addresses FR‑016, methodology‑79af9d6b). | FR‑003, FR‑014, FR‑016 | — |
| **4 – Outer‑Loop Model Training & Evaluation** | Outer **5‑fold stratified** CV trains XGBoost and Random Forest classifiers (baseline & integrated) using hyper‑parameters from inner CV. Stores per‑fold metrics. | FR‑004, FR‑013, FR‑015 | — |
| **5 – Paired‑Outcome Significance Test** | `stats_validation.py --wilcoxon` computes a **two‑sided Wilcoxon signed‑rank test** on paired predicted probabilities (baseline vs. integrated) for each outer fold, producing `paired_test_results.csv` (addresses FR‑012, methodology‑fbbf7991, plan_consistency‑8e9b53e6). | FR‑012 | SC‑001 |
| **6 – Permutation‑Importance & Mann‑Whitney U** | For each retained SNP/MGE feature, runs Mann‑Whitney U on outer‑fold held‑out sets, applies Benjamini‑Hochberg FDR, generates `mannwhitney_results.csv`. | FR‑005, FR‑011 | SC‑002 |
| **7 – Phylogeny‑aware Permutation** | Constructs a kinship matrix from real SNPs, runs `pyseer` permutation test, outputs `permutation_results.csv`. | FR‑011 | SC‑002 |
| **8 – Comparative Report & Threshold Sweep** | `report.py` creates `report.pdf` and populates `metrics.json` with overall deltas, **threshold analysis for {0.3, 0.5, 0.7}** (FR‑007, FR‑019, methodology‑b9ffaa07), and power‑analysis warnings (FR‑014, FR‑020). | FR‑006, FR‑007, FR‑014, FR‑020 | SC‑001, SC‑004, SC‑005 |
| **9 – Contract Validation** | `pytest -q tests/contract` validates `metrics.json` against `contracts/metrics.schema.yaml`. This step **verifies FR‑018 (computational feasibility) and SC‑003** (methodology‑d64b1e24, spec_coverage‑cdcd01f3). | FR‑018 | SC‑003 |
| **10 – Feasibility Monitoring** | `pipeline/monitor_feasibility.py` records wall‑clock time and peak RAM for each phase; if limits (≤ 6 h, ≤ 7 GB) are exceeded, the run fails and the violation is logged (explicitly covers FR‑018 and SC‑003). | FR‑018 | SC‑003 |
| **11 – Edge‑Case Logging** | Logs any download/API failures, low‑coverage isolates, class‑imbalance warnings, and power insufficiencies (FR‑008, FR‑009, FR‑010). | FR‑008, FR‑009, FR‑010 | SC‑003 |

All functional requirements (FR‑001 – FR‑018) and success criteria (SC‑001 – SC‑005) are explicitly addressed, with statistical rigor (multiple‑comparison correction, power analysis, Wilcoxon test) and strict adherence to the compute budget.

## Compute Feasibility
- **Dataset size**: Real download ≤ 500 MB; synthetic demo ≤ 200 MB.  
- **Peak RAM**: < 3 GB (during inner‑CV feature selection).  
- **CPU time**: Benchmark on a free‑tier runner ≈ 3.5 h total.  
- **GPU**: Not required; all libraries are CPU‑compatible.

## Data Availability & Scope Adjustment
The **NCBI Pathogen Genome Browser** and **CARD API** are open, programmatically accessible endpoints that provide genome assemblies, AST phenotypes, and ARG annotations. They satisfy FR‑001. The pipeline **first attempts** to download this real data; if any download or API call fails, the scientific analysis is **aborted** and the limitation is recorded. A deterministic synthetic dataset is generated solely to demonstrate that the workflow runs end‑to‑end; results derived from it are labelled “demo‑only” and do **not** constitute evidence for the research hypothesis. Future work should replace the synthetic fallback with an open, fully‑featured dataset when one becomes available.

## Edge‑Case Handling (re‑emphasized)
- **Real data download failures**: the pipeline automatically switches to the synthetic demo, logs the reason, and **does not** proceed with modeling on synthetic data for the primary claim (FR‑008).  
- **Low assembly quality**: a small subset of synthetic assemblies is intentionally corrupted to test the < 90 % coverage filter (FR‑009).  
- **Class imbalance**: synthetic phenotypes are forced to a balanced split; any seed that violates this triggers regeneration.  

## Expected Deliverables (under `data/reports/`)
1. `baseline_metrics.csv`  
2. `integrated_metrics.csv`  
3. `paired_test_results.csv` (Wilcoxon)  
4. `mannwhitney_results.csv`  
5. `permutation_results.csv`  
6. `report.pdf` – includes a clear “Demo‑only” flag if synthetic data were used.  
7. `metrics.json` – conforms to `contracts/metrics.schema.yaml` (includes `overall_metrics`, `per_fold_metrics`, `threshold_analysis`, `power_analysis`).  
8. `checksums.txt` – SHA‑256 checksums for all generated raw files.  

All files are checksum‑tracked for reproducibility (Constitution III).

## Quick Reference for Developers
Run the full workflow with `python -m src.pipeline.run_all`.  
To adjust isolate count or random seed, edit `src/pipeline/config.py` (`MAX_ISOLATES`, `RANDOM_SEED`).  
To add a new antibiotic, ensure the synthetic phenotype generator creates a balanced split; otherwise the pipeline will skip it and log a warning.  

All random processes use seeds defined in `src/utils/random_seeds.py` to guarantee reproducibility (Constitution I).

---

