# Implementation Plan: Predicting Gene Expression from Chromatin Accessibility

**Branch**: `211-predicting-gene-expression` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-predicting-gene-expression-from-chromati/spec.md`

## Summary

This project implements a reproducible pipeline to predict gene expression levels from chromatin accessibility profiles across human cell lines (GM, K562, HMEC, IMR90, HepG2) using ENCODE data. The technical approach involves downloading paired RNA-seq and DNase/ATAC-seq data, aggregating accessibility signals into 200 fixed-width bins within ±50kb of Transcription Start Sites (TSS), and training Elastic Net regression models using Leave-One-Out Cross-Validation (LOOCV) due to small sample sizes (N=3-5). The pipeline strictly adheres to CPU-only constraints, ensuring all operations fit within 7GB RAM and 6 hours runtime, while addressing reproducibility and biological interpretability requirements.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `pybedtools`, `requests`, `numpy`, `statsmodels`, `scipy`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/models`); no external database  
**Testing**: `pytest` (unit, integration, and contract tests)  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7GB RAM)  
**Project Type**: Data science pipeline / Research tool  
**Performance Goals**: <7GB RAM peak, <6h total runtime, LOOCV per cell line  
**Constraints**: CPU-only execution; no GPU; strict memory limits; reproducible random seeds ()  
**Scale/Scope**: 5 cell lines (subject to N>=4 gate); ~20k genes per line; **200 binned features per gene**; ~4000 total binned features (200 bins * 20 genes sampled) for CI; real data uses streaming.

> Note: The feature space is reduced from ~1M raw peaks to **200 bins per gene window** to ensure P (features) is manageable relative to N (samples). The "10k total features" figure in prior drafts was ambiguous; the correct metric is **200 features per gene model**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan includes explicit random seed pinning (42) in all stochastic steps (CV splits, data sampling). All external data sources are canonical (ENCODE) with checksum verification.
- **II. Verified Accuracy**: All citations (ENCODE, Elastic Net, Bonferroni, CV methodology) are verified against primary sources via the **Reference-Validator Agent**. No speculative values will be introduced.
- **III. Data Hygiene**: Raw data will be downloaded once, checksummed, and stored in `data/raw`. Derived files (`data/processed`) will carry derivation logs. No in-place modifications. **Data Hygiene Gate**: Pipeline fails if `data/raw` is missing or checksums mismatch.
- **IV. Single Source of Truth**: All figures and statistics will be generated programmatically from `data/processed` artifacts. No hand-typed numbers.
- **V. Versioning Discipline**: All artifacts will be tracked with content hashes. The `state/projects/PROJ-211-predicting-gene-expression-from-chromati.yaml` file will be updated upon any data or code change, specifically the `artifact_hashes` map.
- **VI. Computational Resource Efficiency**: Elastic Net is chosen for CPU efficiency. Data is processed via streaming and gene-by-gene aggregation to stay under 7GB RAM. **Serial execution** on 2 CPUs is used; parallelization is disabled to avoid resource contention. Runtime per cell line capped at a fixed upper bound..
- **VII. Biological Interpretability**: Feature importance analysis is mandatory for every model. TSS proximity mapping (±50kb, ±10kb) will be explicitly reported. **Circularity Check**: Promoter regions (TSS ± 2kb) are excluded from predictors to avoid tautology.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-gene-expression-from-chromati/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-211-predicting-gene-expression-from-chromati/
├── code/
│   ├── download_encode.py       # FR-001: Data ingestion
│   ├── preprocess.py            # FR-002 to FR-006, FR-016: Cleaning, binning, imputation, CV calculation
│   ├── train.py                 # FR-007, FR-010, FR-011: Modeling & LOOCV
│   ├── analyze.py               # FR-008, FR-009, FR-010: Feature importance & TSS mapping
│   ├── generate_synthetic.py    # T005: Synthetic data for CI
│   └── utils.py                 # Logging, checksumming, constants
├── data/
│   ├── raw/                     # Downloaded ENCODE files (checksummed)
│   ├── processed/               # Cleaned, binned, imputed matrices
│   └── models/                  # Serialized Elastic Net models
├── tests/
│   ├── unit/                    # Unit tests for utils, preprocessing
│   ├── integration/             # End-to-end pipeline tests with synthetic data
│   ├── contract/                # Schema validation tests (pytest against contracts/)
│   └── data_hygiene/            # Checksum verification tests
├── requirements.txt             # Pinned dependencies
└── README.md                    # Project overview
```

**Structure Decision**: Single-project structure chosen to minimize overhead and simplify data flow. All data and code reside in a single repository, enabling easy reproducibility on CI. The `code/` directory is split by functional responsibility (download, preprocess, train, analyze) to align with user stories and functional requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The current structure is minimal and directly maps to the spec. | N/A |

## Addressing Unresolved Panel Concerns

The following concerns from the previous iteration have been resolved in this plan:

1.  **Task Ordering & Dependencies (T010/T011)**: The plan now explicitly sequences data download (`download_encode.py`) as a prerequisite. The fallback logic is conditional: if `data/raw/` is empty, the pipeline runs `generate_synthetic.py` *only* for CI validation. The production run strictly requires real ENCODE data. The `Data Hygiene Gate` ensures this rule is enforced.
2.  **Missing Artifacts & Staged Acceptance (T013, T014, T016)**: Each preprocessing step (`preprocess.py`) now has a dedicated function that writes an intermediate file with a checksum. The plan mandates that `filtered_expression.csv`, `imputed_expression.csv`, `housekeeping_genes.csv`, `cell_type_specific_genes.csv`, and `housekeeping_matrix.csv` are all generated and checksummed. The `train.py` script will fail if any required input file is missing.
3.  **Documentation Duplication (T060-T065 vs T048-T059)**: The plan consolidates all "Limitations" and "Causation vs Correlation" documentation into a single `paper/limitations.md` file. The `train.py` and `analyze.py` scripts will output structured JSON logs that feed into this single document.
4.  **Synthetic Data Generation (T011)**: A dedicated `code/generate_synthetic.py` script is defined. It generates `synthetic_counts.csv` and `synthetic_peaks.bed` with realistic distributions to validate the pipeline *before* real data ingestion.
5.  **Elastic Net Implementation (T021)**: The `train.py` script will be implemented in full, including:
    -   **LOOCV** (Leave-One-Out Cross-Validation) instead of 5-fold, due to N=3-5 samples.
    -   Elastic Net with `alpha=0.5` and `l1_ratio` tuned via LOOCV.
    -   Per-cell-line model saving (`elastic_net_{cell_line}.pkl`).
    -   Output of `cv_scores.json` with Pearson R² and p-values (Bonferroni corrected for m=5 cell lines).
    -   **Promoter Exclusion**: TSS ± 2kb excluded from features to avoid circularity.
6.  **Runtime & Parallelization**: The plan removes the parallelization strategy. Models are trained **serially** on the 2-CPU runner. To meet the 6-hour limit, a **Sample Size Gate** skips cell lines with N < 4, reducing the total lines to 3-4, ensuring total runtime < 6h.
7.  **Feature Binning & Dimensionality**: The plan explicitly defines **200 fixed-width bins** per gene window (±50kb) as the feature space. This reduces P from ~100k to ~200 per gene model, making the regression tractable. The "10k total features" claim was corrected to "200 features per gene model".
8. **Statistical Validity**: The plan acknowledges that with N=3-5, the model is underdetermined. R² is reported with large confidence intervals (via bootstrapping if N>=4) or as descriptive statistics. Bonferroni correction is applied to m=5 (cell lines), not [deferred] genes.

## Execution Workflow

1.  **Phase 1 (Setup)**: Initialize `requirements.txt`, project structure, and `contracts/`. Run `pytest tests/contract/` to verify schema definitions.
2.  **Phase 2 (Foundational)**: Implement `generate_synthetic.py`, `utils.py`, and unit tests. Run CI with synthetic data. Verify `synthetic_counts.csv` and `synthetic_peaks.bed` are generated and checksummed.
3.  **Phase 3 (US1 - MVP)**:
    -   **T010**: Implement `download_encode.py`. Download real ENCODE data. Generate `data/raw/encode_counts.csv` and `data/raw/encode_peaks.bed`. Record checksums in `state/`.
    -   **T013**: Implement filtering in `preprocess.py`. Generate `data/processed/filtered_expression.csv` (genes with zero expression removed).
    -   **T014**: Implement imputation in `preprocess.py`. Generate `data/processed/imputed_expression.csv` (median imputation).
    -   **T016/T016b/T016c**: Implement CV calculation and gene categorization. Generate `housekeeping_genes.csv`, `cell_type_specific_genes.csv`, and `housekeeping_matrix.csv`.
    -   **Data Hygiene Gate**: Verify all raw and processed files match checksums. Fail if mismatch.
4.  **Phase 4 (US2 - Modeling)**:
    -   **Sample Size Gate**: Skip cell lines with N < 4.
    -   **T021**: Implement `train.py`.
        -   Aggregate peaks into **200 bins** per gene window (±50kb, excluding TSS ± 2kb).
        -   Train Elastic Net per gene using **LOOCV**.
        -   Calculate R², Pearson R, and p-values.
        -   Apply **Bonferroni correction** (m=5 cell lines).
        -   Save models (`elastic_net_{cell_line}.pkl`) and `cv_scores.json`.
5.  **Phase 5 (US3 - Analysis)**:
    -   **T008/T009/T010**: Implement `analyze.py`.
        -   Extract bin importance (coefficients).
        -   Map bins to TSS distance.
        -   **SC-003 Verification**: Calculate percentage of top-100 bins within ±10kb. Save to `sc003_verification.json`.
        -   **FR-009**: Calculate R² for housekeeping genes subset. Save to `housekeeping_r2.csv`.
        -   **FR-010**: Calculate performance gap (ΔR²) between housekeeping and cell-type-specific genes. Save to `performance_gap.csv`.
        -   **SC-006**: External Validation: Train on 4 lines, test on 1 held-out line. Save results to `external_validation.json`.
6.  **Phase 6 (Research)**: Generate `paper/limitations.md`, `paper/results.md`, and final report. Update `state/` file with artifact hashes.

## Tasks & Deliverables Checklist

- [ ] **T010**: `data/raw/encode_counts.csv`, `data/raw/encode_peaks.bed`, `state/...yaml` checksums.
- [ ] **T011**: `data/raw/synthetic_counts.csv`, `data/raw/synthetic_peaks.bed` (CI only).
- [ ] **T013**: `data/processed/filtered_expression.csv`.
- [ ] **T014**: `data/processed/imputed_expression.csv`.
- [ ] **T016**: `data/processed/housekeeping_genes.csv`.
- [ ] **T016b**: `data/processed/cell_type_specific_genes.csv`.
- [ ] **T016c**: `data/processed/housekeeping_matrix.csv`.
- [ ] **T021**: `data/models/elastic_net_{cell_line}.pkl`, `data/processed/cv_scores.json`.
