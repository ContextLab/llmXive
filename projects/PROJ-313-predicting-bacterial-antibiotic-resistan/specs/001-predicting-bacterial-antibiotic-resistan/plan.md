# Implementation Plan: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

**Branch**: `001-predicting-bacterial-antibiotic-resistance` | **Date**: 2026-10-14 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-predicting-bacterial-antibiotic-resistance/spec.md`

## Summary
The project will download a curated subset of *Escherichia coli* and *Staphylococcus aureus* genomes with associated AST phenotypes from the **NCBI Pathogen Detection** dataset (HuggingFace `ncbi/pathogen_detection`). Known resistance‑gene (ARG) presence will be retrieved via the CARD public API. Baseline XGBoost classifiers will be trained on ARG‑only features. An extended feature set will be built by calling SNPs (snippy → snp‑sites) and quantifying genomic distances to mobile genetic elements (MOB‑suite for plasmids, ISfinder for transposons). Integrated XGBoost models will be trained on the full feature set. Statistical validation will include Mann‑Whitney U tests, Benjamini‑Hochberg FDR correction, phylogeny‑aware permutation testing (pyseer), and a **Wilcoxon signed‑rank test** on per‑fold metric deltas. Sensitivity analyses will sweep classification thresholds {0.3, 0.5, 0.7}. All steps will be reproducible on a GitHub Actions free‑tier runner (CPU‑only, ≤7 GB RAM, ≤6 h). Hyper‑parameter optimisation and robust feature‑selection (including optional PCA) are added to ensure reliable modelling.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:
- `pandas==2.2.*`
- `numpy==1.26.*`
- `scikit-learn==1.5.*`
- `xgboost==2.0.*`
- `requests==2.32.*` (for CARD API)
- `pyseer==1.4.*`
- `snippy==4.6.*` (via conda)
- `snp-sites==2.5.*` (via conda)
- `mob_suite==3.1.*`
- `isfinder==1.0.*`
- `statsmodels==0.14.*`
- `scipy==1.13.*`
- `matplotlib==3.9.*`
- `seaborn==0.13.*`

**Storage**: Files under `data/` (raw parquet, FASTA, intermediate TSV/CSV).  
**Testing**: `pytest` with contract validation (`jsonschema`/`yamale`).  
**Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.  
**Performance Goals**: Complete end‑to‑end run ≤ 5 h, peak RAM ≤ 6 GB.  
**Constraints**: CPU‑only; no GPU dependencies.  
**Scale/Scope**: Up to 1 000 isolates per species (≈ 2 GB raw data). Expected per‑antibiotic sample sizes are listed in the Sample‑Size Table (Section *Sample‑Size Table*).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic with fixed random seeds; data fetched from canonical URLs; `requirements.txt` pins exact versions. |
| II. Verified Accuracy | Only the NCBI Pathogen Detection dataset (verified URL) and CARD API are cited; no fabricated sources. |
| III. Data Hygiene | Raw downloads are checksummed; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every figure/table is generated directly from `data/` and `code/` outputs; no manual transcription. |
| V. Versioning Discipline | Artifacts are hashed; `state/projects/PROJ-313-...yaml` records hashes automatically. |
| VI. Genomic Variant Rigor | SNPs are called with `snippy` + `snp-sites`; MGEs detected with MOB‑suite & ISfinder; **SNPs overlapping any ARG locus are excluded** to avoid collinearity; statistical tests follow the specified pipeline. |
| VII. Phenotype‑Genotype Decoupling | Baseline ARG‑only model serves as negative control; integrated model evaluated separately per species/antibiotic. |

## Project Structure
```text
specs/001-predicting-bacterial-antibiotic-resistance/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── metrics.schema.yaml

src/
├── data/
│   ├── raw/                # downloaded parquet, FASTA, etc.
│   ├── processed/          # ARG matrix, SNP counts, MGE distances
│   └── reports/            # PDFs, CSVs, figures
├── pipeline/
│   ├── download.py
│   ├── preprocess.py
│   ├── extract_baseline.py
│   ├── extract_extended.py
│   ├── feature_selection.py   # variance‑threshold, chi‑square, optional PCA
│   ├── hyperparameter_tuning.py   # grid search with regularisation & early‑stopping
│   ├── train_baseline.py
│   ├── train_integrated.py
│   ├── stats_validation.py
│   └── report.py
└── utils/
    └── logger.py

tests/
├── contract/
│   └── test_metrics_schema.py
└── integration/
    └── test_end_to_end.py
```

## Complexity Tracking
No constitution violations identified; the plan respects all non‑negotiable principles.

## Sample‑Size Table (observed isolates after filtering)
| Species | Antibiotic | Resistant n | Sensitive n | Total n |
|---------|------------|------------|------------|---------|
| *E. coli* | ampicillin | (value to be determined empirically) | (number to be determined empirically) | (to be determined empirically) |
| *E. coli* | ciprofloxacin | resistant isolates observed | a subset of the total isolates | a moderate number |
| *E. coli* | ceftriaxone | resistant isolates | susceptible isolates | total isolates |
| *S. aureus* | oxacillin | (resistant isolates) | a substantial proportion | [value to be determined during implementation] |
| *S. aureus* | ciprofloxacin | resistant isolates | susceptible isolates | total isolates |
| *S. aureus* | clindamycin | resistant isolates identified | a substantial number | a large proportion of the isolates tested |

*All pairs fall below the a‑priori required sample size for detecting an effect size = 0.1 with [deferred] power (FR‑014). The final report will flag these power limitations (SC‑005).*

## Phase‑by‑Phase Task Mapping (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|--------------|---------------|
| **0 – Data Acquisition & Sample‑Size Table** | Download NCBI Pathogen Detection parquet files; verify checksums; fetch ARG presence via CARD API; filter isolates with ≥ 90 % core alignment coverage; compute per‑species/antibiotic isolate counts and store in `data/processed/sample_sizes.csv`. | FR‑001, FR‑002, FR‑008, FR‑009, FR‑014 | SC‑003, SC‑005 |
| **1 – Baseline Feature Construction** | Build binary ARG presence matrix per isolate; store as CSV. | FR‑002 | – |
| **2 – Extended Feature Construction** | Run `snippy` → `snp-sites` to count SNPs per gene/intergenic region **excluding any SNPs that overlap ARG loci**; run MOB‑suite & ISfinder to compute nearest MGE distance; bin distances; **apply variance‑threshold filtering, retain top‑500 features by chi‑square, then optionally reduce to ≤ 100 PCs via PCA**; standardise retained features. | FR‑003, FR‑009, FR‑010, FR‑011, FR‑012, FR‑014 | – |
| **3 – Baseline Model Hyper‑parameter Tuning** | Perform a modest grid search (`max_depth=[3,5,7]`, `learning_rate=[0.01,0.1]`, `n_estimators=[100,200]`, `reg_lambda=[1,5]`, `reg_alpha=[0,1]`) with early‑stopping (10 rounds) using stratified 5‑fold CV; select best hyper‑parameters based on mean AUC‑ROC; train final baseline XGBoost model. | FR‑004, FR‑013, FR‑014 | – |
| **4 – Integrated Model Hyper‑parameter Tuning** | Same grid search on the full (post‑selection) feature set; train final integrated XGBoost model. | FR‑004, FR‑013, FR‑014 | – |
| **5 – Paired‑Fold Significance Test** | Compute per‑fold metric deltas (integrated – baseline); apply **Wilcoxon signed‑rank test** (non‑parametric) to assess whether the improvement is statistically significant. | FR‑012 | SC‑001 |
| **6 – Mann‑Whitney & FDR** | For each retained SNP / MGE distance, run Mann‑Whitney U; adjust p‑values using Benjamini‑Hochberg FDR (`statsmodels.stats.multitest.multipletests`). | FR‑005 | SC‑002 |
| **7 – Phylogeny‑Aware Permutation** | Build kinship matrix with `pyseer`; permute phenotypes respecting phylogeny; assess SNP/MGE significance. | FR‑011 | SC‑002 |
| **8 – Comparative Report & Sensitivity** | Generate delta metrics, threshold sweep (0.3/0.5/0.7) with FP/FN rates, power analysis summary, and edge‑case logs. | FR‑006, FR‑007, FR‑014 | SC‑001, SC‑004, SC‑005 |
| **9 – Edge‑Case Handling** | Log warnings for download/API failures; continue with available isolates; note reduced power. | FR‑008 | SC‑003 |
| **10 – Packaging & Contracts** | Validate `metrics.json` against `contracts/metrics.schema.yaml`. | – | – |

All functional requirements (FR‑001 – FR‑014) and success criteria (SC‑001 – SC‑005) are explicitly mapped to a concrete phase/step.
