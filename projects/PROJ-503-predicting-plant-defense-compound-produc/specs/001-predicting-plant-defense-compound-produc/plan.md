# Implementation Plan: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Branch**: `001-predict-plant-defense` | **Date**: 2026-06-24 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-predict-plant-defense/spec.md`

## Summary

This project implements a computational pipeline to predict plant defense compound production (terpenoids, alkaloids, phenylpropanoids) from gene expression data in *Arabidopsis* and *Solanum* species under herbivore stress. The approach involves downloading paired transcriptomic (GEO) and metabolomic (Metabolomics Workbench) data, filtering for defense‑pathway genes, applying species‑specific normalization and ComBat batch correction, and training a Ridge Regression model with rigorous nested cross‑validation and permutation testing. The pipeline is designed to run within the constraints of a GitHub Actions free‑tier runner (limited CPU resources, constrained RAM, 4 h limit).

**Key Changes from Previous Revision**:
- **Dataset Strategy**: Acknowledged scarcity of paired data; defined fallback to condition-level aggregation if strict pairing fails.
- **Modeling**: Prioritized species-specific models; cross-species model is now exploratory and conditional on n>=50. Added mandatory species-holdout validation.
- **Statistical Rigor**: Enforced nested CV; added PCA/Lasso mitigation for p>>n; reported both Bonferroni and FDR corrected p-values.
- **Traceability**: Explicitly linked all tasks to FRs/SCs and defined concrete file paths and error codes.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `biopython`, `requests`, `pyyaml`, `statsmodels`, `gseapy` (for KEGG pathway mapping), `pyarrow` (for parquet I/O), `pycombat` (for ComBat), `black`, `flake8`, `pip-audit`  
**Storage**: Local filesystem (`projects/PROJ-503-predicting-plant-defense-compound-produc/data/`, `logs/`, `outputs/`)  
**Testing**: `pytest` (unit, integration, contract) with coverage ≥ 80% per module  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Performance Goals**: End‑to‑end runtime ≤ 4 hours; Memory usage ≤ 6 GB; Disk usage ≤ 12 GB  
**Constraints**: No GPU; CPU‑only operations; strict sample‑level pairing (with fallback); abort on time, power, or data‑availability violations.  
**Scale/Scope**: Multiple species, A moderate number of samples (expected after pairing), ~‑ defense metabolites, Several hundred to a few thousand defense‑pathway genes.

## Constitution Check

| Principle | Status | Concrete Verification Step |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts are deterministic (pinned seeds). `requirements.txt` pins exact versions. External data fetched via accession IDs only. |
| **II. Verified Accuracy** | **PASS** | **Phase 1 T020**: Run Reference-Validator Agent on all citations (GEO, Metabolomics Workbench, KEGG) before modeling. Abort if any citation is invalid. |
| **III. Data Hygiene** | **PASS** | `data/raw/` files are checksummed (SHA‑256) upon download (Phase 0 T010); transformations produce new files under `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `outputs/` are the sole source for `paper/`. No hand‑typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes are recorded in `state/` for: raw data files, processed matrices, model artifacts, and metrics. (Phase 4 T045). |
| **VI. Dataset Version Traceability** | **PASS** | `data/sources.yaml` records accession IDs, download dates, and preprocessing script versions. |
| **VII. Statistical Validation Discipline** | **PASS** | Nested k‑fold CV

The specific value to remove/generalize: 'k'

Rewritten passage:
Nested k‑fold cross-validation will be employed to evaluate model performance. The research question remains: How does the proposed method compare to existing baselines in terms of predictive accuracy and generalization? The method involves partitioning the dataset into k mutually exclusive subsets, iteratively training on k−1 folds and validating on the remaining fold, repeated across all folds. (Citation: Author et al., 2023)., 000‑iteration permutation tests, and Bonferroni (plus FDR) correction are enforced. |

## Project Structure (all paths are relative to `projects/PROJ-503-predicting-plant-defense-compound-produc/`)

```
projects/PROJ-503-predicting-plant-defense-compound-produc/
├─ code/
│  ├─ __init__.py
│  ├─ main.py                  # Entry point with runtime monitoring (E-TIMEOUT)
│  ├─ data_download.py         # GEO & Metabolomics Workbench fetchers
│  ├─ preprocessing.py         # Normalization, pairing, filtering
│  ├─ feature_selection.py     # KEGG pathway mapping + PCA
│  ├─ modeling.py              # Ridge, nested CV, permutation, VIF
│  └─ utils.py                 # Logging, error handling (E-PAIRING, E-POWER, E-DATA)
├─ data/
│  ├─ raw/                     # Downloaded raw files (checksummed)
│  ├─ sources.yaml             # Dataset version traceability
│  └─ processed/               # Cleaned, paired, normalized matrices
├─ logs/
│  ├─ data_pairing.json        # Mismatch logs (E-PAIRING)
│  ├─ feature_filtering.csv    # Zero-variance logs
│  ├─ vif_diagnostics.csv      # VIF scores per gene
│  └─ runtime.log              # CPU time tracking (E-TIMEOUT)
├─ outputs/
│  ├─ models/
│  │  ├─ ridge_species_A_model.pkl       # Primary model (Species A)
│  │  ├─ ridge_species_S_model.pkl       # Primary model (Species S)
│  │  └─ ridge_cross_species_model.pkl   # Exploratory (if n>=50)
│  ├─ metrics/
│  │  └─ model_results.json   # SC-001, SC-002 results
│  └─ diagnostics/
│     └─ vif_diagnostics.csv
├─ docs/
│  ├─ quickstart.md
│  ├─ data-model.md
│  ├─ edge_cases.md            # Ortholog fallback logs
│  ├─ quickstart_validation.md
│  ├─ refactoring_log.md
│  ├─ security_report.md
│  └─ assumption_resolution_log.md
├─ tests/
│  ├─ unit/
│  │  ├─ test_data_download.py
│  │  ├─ test_preprocessing.py
│  │  └─ test_modeling.py
│  ├─ integration/
│  │  └─ test_e2e_runtime.py   # Asserts total runtime < 4 h
│  └─ contract/
│     └─ test_schemas.py
├─ contracts/
│  ├─ expression_matrix.schema.yaml
│  ├─ metabolite_matrix.schema.yaml
│  └─ model_output.schema.yaml
└─ requirements.txt
```

## Phase 0 – Project Bootstrap (T001-T010)

| Step | Description | FR/SC | Artifact |
|------|-------------|-------|----------|
| T001 | Create all directories: `code/`, `data/raw/`, `data/processed/`, `data/paired/`, `logs/`, `outputs/models/`, `docs/`, `tests/contract/`, `tests/integration/`, `tests/unit/`. | – | `mkdir -p ...` |
| T002 | Initialise `git` repo and add `.gitignore`. | – | – |
| T003 | Create `.flake8` and `pyproject.toml` with black configuration. | – | Config files |
| T004 | Add `requirements.txt` with exact version pins. | – | `requirements.txt` |
| T005 | Add `state/` directory for content‑hash tracking. | – | – |
| T006 | Add CI workflow skeleton (`.github/workflows/ci.yml`). | – | CI file |
| T007 | Implement runtime timer in `code/main.py` that logs elapsed CPU time and raises `E‑TIMEOUT` if >4h (FR‑008). | FR‑008 | `logs/runtime.log` |
| T008 | Add `pip-audit` security scan step to CI; output to `docs/security_report.md`. | – | `docs/security_report.md` |
| T009 | Run power‑analysis utility (see `code/utils.py`) to confirm n>=28 for r=0.5 at [deferred] power; abort with `E‑POWER` if n<28. | FR‑009 | `logs/power_analysis.log` |
| T010 | Verify checksum coverage >= 99% for all downloaded files; abort with `E‑CHECKSUM` if not met (SC‑004). | SC‑004 | `logs/checksum_report.log` |

## Phase 1 – Data Acquisition & Pairing (T011-T020)

| Step | Description | FR/SC | Artifact |
|------|-------------|-------|----------|
| T011 | Search GEO for herbivore‑stress series in *Arabidopsis* and *Solanum*. | FR‑001 | `data/raw/geo_*.txt` |
| T012 | Search Metabolomics Workbench for targeted metabolomics of defense compounds. | FR‑002 | `data/raw/mw_*.txt` |
| T013 | If no paired dataset is found, abort with `E‑DATA` and log to `logs/data_availability.log`. | – | – |
| T014 | Download raw files, compute SHA‑256 checksums, store in `logs/checksum_report.log`. | SC‑004 | – |
| T015 | Parse sample‑level metadata (biosample_id) from both sources; construct `PairedSampleIndex`. Run power analysis (T009); abort with `E‑POWER` if n<28. | FR‑009 | `data/processed/paired_samples.csv` |
| T016 | Enforce >= 95% pairing rate; if below, abort with `E‑PAIRING` and write detailed JSON to `logs/data_pairing.json`. (Fallback: try condition-level aggregation). | FR‑009, SC‑005 | `logs/data_pairing.json` |
| T017 | Record dataset provenance in `data/sources.yaml` (accession, download date, checksum). | VI | `data/sources.yaml` |
| T018 | Log power‑analysis results (required n=28, available n, achieved power) to `logs/power_analysis.log`. | – | – |
| T019 | Validate that each metabolite has >= 5 quantified samples; drop metabolites failing this threshold and log to `logs/metabolite_filtering.csv`. | – | – |
| T020 | **Run Reference‑Validator Agent** on all citations before proceeding to Phase 2 (Constitution Principle II). | II | – |

## Phase 2 – Pre‑processing & Feature Selection (T021-T030)

| Step | Description | FR/SC | Artifact |
|------|-------------|-------|----------|
| T021 | Normalize expression to TPM/FPKM, log‑transform metabolites (log2). | FR‑003 | `data/processed/expression_matrix.csv`, `metabolite_matrix.csv` |
| T022 | Apply species‑specific z‑score normalization (FR‑010). | FR‑010 | – |
| T023 | Apply ComBat batch correction across species (FR‑010). | FR‑010 | – |
| T024 | Map genes to KEGG defense‑biosynthetic pathways (terpenoid, alkaloid, phenylpropanoid). Only include genes with pathway annotation. | FR‑004 | – |
| T025 | **Mandatory PCA** if features (p) > 2 * samples (n): reduce to a subset of the most significant components

The research question, method, and references remain unchanged as no specific empirical values were asserted beyond the generalization of the component count.. Log components to `logs/pca_summary.csv`. | – | – |
| T026 | Filter out genes with variance < 1e‑10; log removed genes to `logs/feature_filtering.csv`. | FR‑003, SC‑006 | – |
| T027 | Verify that >= 75% of known defense pathway genes are retained; abort with `E‑FEATURE` if not (SC‑006). | SC‑006 | – |
| T028 | Store final feature matrix (`ExpressionMatrix`) and target matrix (`MetaboliteMatrix`) conforming to schemas. | – | `data/processed/expression_matrix.csv`, `metabolite_matrix.csv` |
| T029 | Generate VIF diagnostics for all retained genes; write `outputs/vif_diagnostics.csv` (columns: gene_id, vif_score, threshold_exceeded). | – | `outputs/vif_diagnostics.csv` |
| T030 | Update `data/sources.yaml` with preprocessing version tag. | – | – |

## Phase 3 – Modeling, Evaluation & Reporting (T031-T045)

| Step | Description | FR/SC | Artifact |
|------|-------------|-------|----------|
| T031 | Split data into outer k-fold cross-validation

Research Question: How does the proposed method perform in terms of generalization error?
Method: k-fold cross-validation
References: [Citation verbatim] (maintaining paired samples). | FR‑005 | – |
| T032 | Within each outer fold, perform inner cross-validation to select Ridge alpha (grid search). | FR‑005 | – |
| T033 | Train Ridge regression on training folds; predict on held‑out fold; collect RMSE & Pearson r per metabolite. | FR‑005 | – |
| T034 | After outer CV, compute mean ± SD of RMSE and Pearson r across folds; store in `outputs/metrics/model_results.json`. | SC‑001 | `outputs/metrics/model_results.json` |
| T035 | Perform multiple permutation tests (shuffle metabolite labels) for each metabolite; compute raw p‑values. | FR‑006 | – |
| T036 | Apply Bonferroni correction across all metabolites (FR‑007); store corrected p‑values. Also compute Benjamini-Hochberg FDR for sensitivity analysis. | FR‑007, SC‑002 | – |
| T037 | Flag metabolites with corrected p < 0.05 as significant (`is_significant`). | – | – |
| T038 | Save primary species-specific Ridge models (`ridge_species_A_model.pkl`, `ridge_species_S_model.pkl`). | FR‑010 | `outputs/models/...` |
| T039 | **Conditional**: Create `outputs/models/cross_species_model.pkl` only if paired samples >= 50; otherwise log `E‑SAMPLESIZE`. | FR‑010 | `outputs/models/...` |
| T040 | **Mandatory**: Evaluate species‑holdout generalization (train on A, test on S; train on S, test on A). If holdout fails, discard cross-species model. | – | `outputs/metrics/species_holdout.json` |
| T041 | Serialize model artifacts and evaluation metrics conforming to schemas. | – | – |
| T042 | Log total CPU time; abort with `E‑TIMEOUT` if > 4 h (already enforced in T007). | FR‑008 | `logs/runtime.log` |
| T043 | Generate a concise summary report (`docs/model_summary.md`) linking each metric back to its source data row (Single Source of Truth). | – | – |
| T044 | Run contract validation tests (`tests/contract/test_schemas.py`). | – | – |
| T045 | Archive all content hashes (raw data, processed matrices, models, metrics) in `state/` for reproducibility. | V | – |

## Phase 4 – Documentation, QA & Release (T046-T065)

| Step | Description | Artifact |
|------|-------------|----------|
| T046a | Create `docs/quickstart.md` with end‑to‑end instructions. | `docs/quickstart.md` |
| T046b | Create `docs/data-model.md` describing schemas. | `docs/data-model.md` |
| T046c | Create `contracts/` module specifications. | `contracts/...` |
| T047 | Run quickstart validation on a fresh runner; log success to `docs/quickstart_validation.md`. | `docs/quickstart_validation.md` |
| T048 | Execute linting (`flake8`) and formatting (`black --check`); fix all violations; document changes in `docs/refactoring_log.md`. | `docs/refactoring_log.md` |
| T049 | Perform security audit (`pip-audit`); record findings in `docs/security_report.md`. | `docs/security_report.md` |
| T050 | Profile pipeline with `cProfile`; identify bottlenecks; optimize data loading and model training; verify E2E runtime <4h in `tests/integration/test_e2e_runtime.py`. | `logs/profiling_report.txt` |
| T051 | Ensure unit test coverage >= 80% for each module (`pytest --cov=code`). | – |
| T052 | Parse `spec.md` for any `[deferred]` citation markers; confirm each has a verified URL in `research.md`; create `docs/assumption_resolution_log.md`. | `docs/assumption_resolution_log.md` |
| T053 | Commit all artifacts; tag release with content hash version. | – |

## Mapping of Functional Requirements & Success Criteria

| FR / SC | Covered in Phase | Details |
|---------|------------------|---------|
| FR‑001 | Phase 1 (T011‑T014) | GEO download, checksum, provenance |
| FR‑002 | Phase 1 (T011‑T014) | Metabolomics Workbench download, checksum |
| FR‑003 | Phase 2 (T021‑T023) | Normalization, log‑transform, variance filter |
| FR‑004 | Phase 2 (T024) | KEGG pathway mapping only (no regulatory genes) |
| FR‑005 | Phase 3 (T031‑T034) | Ridge regression with nested CV |
| FR‑006 | Phase 3 (T035‑T036) | Permutation testing |
| FR‑007 | Phase 3 (T036) | Bonferroni correction |
| FR‑008 | Phase 0 (T007) & Phase 3 (T042) | Runtime abort |
| FR‑009 | Phase 1 (T015‑T016) | Pairing rate check, power analysis, abort `E‑PAIRING`/`E‑POWER` |
| FR‑010 | Phase 2 (T022‑T023) & Phase 3 (T038‑T040) | Z‑score + ComBat, species-specific models, holdout validation |
| SC‑001 | Phase 3 (T034) | Mean Pearson r >= 0.5 (outer CV) |
| SC‑002 | Phase 3 (T036) | Bonferroni‑corrected p <= 0.05 |
| SC‑003 | Phase 0 (T007) & Phase 4 (T050) | Total runtime <= 4 h |
| SC‑004 | Phase 0 (T010) | Checksums >= 99% |
| SC‑005 | Phase 1 (T016) | Pairing >= 95% |
| SC‑006 | Phase 2 (T027) | Retain >= 75% defense genes |

## Complexity Tracking & Mitigations

- **High‑dimensionality (p>>n)**: Mandatory PCA (T025) if p > 2n to reduce predictors before Ridge. If PCA is not used, Lasso/Elastic Net will be considered in the inner CV loop.
- **Cross‑species heterogeneity**: Primary models are species-specific. Cross-species model is exploratory and conditional on n>=50. Mandatory species-holdout validation (T040) ensures biological generalizability.
- **Multiple testing**: Bonferroni applied (FR-007); FDR reported for sensitivity. Justified by small metabolite set (<20) with note that FDR can be toggled via config.
- **Runtime**: Permutation tests parallelized over available CPU cores; profiling ensures <= 4 h.
- **Data Scarcity**: Fallback to condition-level aggregation if strict pairing fails (T016). If still insufficient, abort with E-PAIRING.

## Additional Quality Controls

- **VIF Diagnostics** (`outputs/vif_diagnostics.csv`) to flag extreme collinearity.
- **Checksum verification** (`logs/checksum_report.log`) with 99% pass threshold.
- **Feature retention audit** (`logs/feature_retention.log`) confirming >= 75% pathway gene coverage.
- **Assumption resolution log** (`docs/assumption_resolution_log.md`) for deferred citations.

--- End of Plan ---