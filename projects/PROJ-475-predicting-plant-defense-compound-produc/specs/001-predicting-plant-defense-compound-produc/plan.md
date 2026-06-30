# Implementation Plan: Predicting Plant Defense Compound Production from Public Genomic and Environmental Data

**Branch**: `001-predict-plant-defense-compounds` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-plant-defense-compounds/spec.md`

## Summary

This project implements a predictive modeling pipeline to estimate plant defense compound production using genomic variants (VCF), environmental metadata, and compound profiles. The approach involves downloading and validating multi-modal data, engineering genomic diversity metrics (heterozygosity, nucleotide diversity), and training a regularized regression model (LASSO/Ridge) with rigorous statistical validation (permutation tests, sensitivity analysis, multiple-comparison correction). The pipeline is designed to run on free-tier CPU-only CI runners.

**Note on Data Availability**: Due to the absence of verified URLs for specific *Arabidopsis* VCFs and compound databases in the current environment, this plan implements a **Mock Data Generation** fallback for the CI run. This validates the pipeline architecture and statistical logic (FR-005 to FR-008) but does not constitute an empirical test of the biological hypothesis (Heterozygote Advantage). Real data ingestion is conditional on future verified sources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `pyvcf` (or `cyvcf2`), `requests`, `pyyaml`, `scipy`  
**Storage**: Local file system (CSV, Parquet, JSON)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Runtime < 6 hours, Memory < 7GB, Disk < 14GB  
**Constraints**: No GPU, no deep learning, no large-LLM inference, no external API rate-limit violations.  
**Scale/Scope**: Target species: *Arabidopsis thaliana* (1001 Genomes subset). N (populations) expected < 500.

## Constitution Check

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS (Mock Data Mode) | Random seeds pinned in `code/`. Mock data generation is deterministic. Real data fetch is conditional on verified URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | All dataset URLs in `research.md` are restricted to the "Verified datasets" block. No invented URLs. Mock data is explicitly labeled. |
| **III. Data Hygiene** | PASS | Data files checksummed in `data/manifest.yaml`. Raw data (or mock generator output) preserved; derivatives written to new files. PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All metrics (R², MAE, p-values) derived from `code/` output, not hand-typed. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes; state file updated on changes. |
| **VI. Data Integration Provenance** | PASS (Mock Data Mode) | `data/manifest.yaml` records exact source names/versions. For mock runs, provenance points to the generator script and seed. |
| **VII. Statistical Validation** | PASS | LASSO/Ridge with 5-fold CV/LOOCV, permutation tests (n=1000), Benjamini-Hochberg correction implemented as per spec. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-plant-defense-compounds/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point orchestrating phases
├── config.py            # Hyperparameters, paths, seeds
├── data/
│   ├── __init__.py
│   ├── ingestion.py     # FR-001, FR-002: Download OR Generate Mock
│   ├── validation.py    # FR-003: Listwise deletion & checks
│   └── preprocessing.py # FR-004: Feature engineering + PCA
├── models/
│   ├── __init__.py
│   ├── training.py      # FR-005, FR-010, FR-011: Model fitting
│   └── evaluation.py    # FR-006, FR-007, FR-008: Permutation, sensitivity, p-values
├── utils/
│   ├── io.py            # File I/O, checksums
│   └── stats.py         # VIF, Jaccard, BH correction
└── tests/
    ├── test_ingestion.py
    ├── test_models.py
    └── test_stats.py

data/
├── raw/                 # Downloaded artifacts (VCF, Parquet, CSV) OR Mock Data
├── processed/           # Merged, cleaned, engineered features
└── manifest.yaml        # Checksums and provenance
```

**Structure Decision**: Single project structure (`code/`) selected for simplicity and direct CLI execution. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope is contained within the free-tier CI limits. | N/A |

## Phase Execution Order

1.  **Phase 0 (Data Ingestion)**: Attempt to download VCF (FR-001) and Env (FR-002). If no verified URL exists, **generate Mock Data** with defined statistical properties. Check disk space (1.5x estimated size) before download; halt if exceeded.
2.  **Phase 1 (Data Validation & Cleaning)**: Merge datasets, perform listwise deletion (FR-003), check retention (SC-001).
3.  **Phase 2 (Feature Engineering)**: Calculate genomic diversity (FR-004), **calculate top N Principal Components (PCs) for population structure control**, normalize compounds (FR-011), check collinearity (VIF).
4.  **Phase 3 (Model Training)**: Train LASSO/Ridge (FR-005). **Check N < 30**; if true, check `unique_studies >= N-1`. If condition met, **exclude 'source_study' covariate** and use global Z-score (FR-010). Else, use 5-fold CV.
5.  **Phase 4 (Statistical Validation)**: Permutation test (FR-006) to generate null distribution. **Compare observed R² vs null to calculate p-value** (SC-002). Sensitivity sweep (FR-007), BH correction (FR-008).
6.  **Phase 5 (Reporting)**: Generate `results.json`, plots, and summary statistics.

## Compute Feasibility & Constraints

-   **Memory**: Genomic data (VCF) is large. Strategy: Stream VCF using `cyvcf2` or `pyvcf` and aggregate to population-level metrics *before* loading into RAM. Do not load full VCF into memory.
-   **Disk**: Pre-filter VCF to a subset of high-variance SNPs (e.g., top 10k by variance) if total size > 5GB.
-   **Time**: Permutation test (n=1000) on CPU may be slow. Strategy: Use `n_jobs=-1` for parallelization on available 2 cores, but limit permutation iterations if time approaches a predefined computational budget.
-   **No GPU**: All models use `scikit-learn` CPU backends. No `torch` or `tensorflow` for training.

## FR/SC Mapping

| ID | Plan Element |
| :--- | :--- |
| **FR-001** | `data/ingestion.py`: **Check disk > 1.5 * estimated_size**; if false, halt with E-DISK-SPACE. **Download VCF OR Generate Mock** (if no verified URL). Checksum. |
| **FR-002** | `data/ingestion.py`: Fetch env data via API/Parquet based on coords **OR Generate Mock**. |
| **FR-003** | `data/validation.py`: Merge, listwise deletion, retention report. |
| **FR-004** | `data/preprocessing.py`: Heterozygosity, nucleotide diversity calc. |
| **FR-005** | `models/training.py`: LASSO/Ridge, CV logic (5-fold vs LOOCV). |
| **FR-006** | `models/evaluation.py`: Permutation test (n=1000). |
| **FR-007** | `models/evaluation.py`: Alpha sweep **{0.01, 0.05, 0.1}** (corrected from spec typo). |
| **FR-008** | `utils/stats.py`: Benjamini-Hochberg correction. |
| **FR-009** | `data/preprocessing.py`: Aggregation to population level. |
| **FR-010** | `models/training.py`: **Check N < 30**; if true, check `unique_studies >= N-1`. If true, **exclude source_study covariate** and use global Z-score. Else, use 5-fold CV. |
| **FR-011** | `models/training.py`: Study fixed effect / Z-score normalization (unless excluded by FR-010). |
| **SC-001** | `data/validation.py`: Retention % check (>=80%). |
| **SC-002** | `models/evaluation.py`: **Compare observed R² against null distribution**; calculate p-value; verify p < 0.05. |
| **SC-003** | `models/evaluation.py`: Permutation p-value < 0.05. |
| **SC-004** | `models/evaluation.py`: Jaccard index stability >= 0.6. |
| **SC-005** | `main.py`: Runtime monitoring, fail if > 6h. |