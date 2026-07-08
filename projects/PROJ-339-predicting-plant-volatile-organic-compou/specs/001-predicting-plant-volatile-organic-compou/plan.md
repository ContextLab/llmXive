# Implementation Plan: Predicting Plant VOC Emission Profiles from Genomic and Environmental Data

**Branch**: `001-predict-voc-profiles` | **Date**: 2026-06-29 | **Spec**: `specs/001-predict-voc-profiles/spec.md`
**Input**: Feature specification from `/specs/001-predict-voc-profiles/spec.md`

## Summary

This project implements a CPU-tractable pipeline to predict *Arabidopsis thaliana* Volatile Organic Compound (VOC) emission profiles using paired RNA-seq and environmental data. **Scope Note**: Due to the absence of verified paired *Arabidopsis* RNA-seq/VOC datasets in public repositories (NCBI GEO, Metabolomics Workbench), this project currently functions as a **Methodological Simulation & Pipeline Validation** study. The primary objective is to validate the data ingestion, normalization, modeling, and interpretation logic on a synthetic dataset that mimics the expected schema. Real biological discovery is deferred until verified paired data is acquired. The approach ingests public genomic data (or generates synthetic equivalents), normalizes counts to TPM, handles missing values via imputation, and merges with VOC targets based on exact sample pairing. A Random Forest Regressor (scikit-learn) will be trained with nested 5-fold cross-validation to predict VOC levels, followed by permutation feature importance and SHAP analysis to identify biological drivers (in the synthetic context). All findings will be framed as associational, with strict adherence to multiple-comparison corrections and biological pathway validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `shap`, `requests`, `biopython` (for potential ID mapping), `pyyaml`  
**Storage**: Local CSV/Parquet files under `data/` (no external DB)  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM, 14GB Disk, No GPU)  
**Project Type**: Data Science Pipeline / Research Script (Methodological Simulation)  
**Performance Goals**: Complete full pipeline (ingest -> train -> eval -> report) within 6 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU usage; no deep learning training; dataset size limited to a small-scale cohort to ensure cross-validation stability and CPU feasibility; strict adherence to "no unpaired samples" rule.  
**Scale/Scope**: Single species (*Arabidopsis thaliana*), single study type (stress response), ~-100 samples.

> **Critical Note on Dataset Availability**: The spec assumes the existence of paired RNA-seq and VOC data for *Arabidopsis thaliana* in public repositories. The verified dataset list provided for this project **does not contain a verified source** for *Arabidopsis thaliana* paired RNA-seq/VOC data. The plan explicitly addresses this gap in `research.md` by defining a fallback strategy (synthetic/mock data generation for pipeline validation) while acknowledging the limitation for real-world biological insight. The project is scoped as a **Methodological Simulation** pending real data acquisition.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`. Data acquisition scripts target specific URLs (or mock generators if URLs fail). `requirements.txt` pins versions. Synthetic data generator is versioned and checksummed. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` and `paper/` will be validated against the "Verified datasets" block. No fabricated URLs. Real data queries logged. |
| **III. Data Hygiene** | PASS | Raw data (or mock data) checksummed. Transformations produce new files. No in-place modification. PII scan passed (no PII expected in plant data). |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` and `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes computed by `code/utils/hashing.py`. The `state/projects/...yaml` file is updated automatically upon artifact changes to reflect content hashes. |
| **VI. Biological Pathway Consistency** | PASS | Feature importance results cross-referenced with known terpene synthase families (descriptive statistic only, acknowledging synthetic nature). |
| **VII. Interpretable Modeling** | PASS | SHAP and permutation importance calculated and visualized with explicit p-value derivation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-voc-profiles/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── 01_ingest.py         # Data ingestion, normalization, imputation
├── 02_merge.py          # Sample pairing logic
├── 03_train.py          # Random Forest training, CV, metrics
├── 04_interpret.py      # SHAP, permutation importance, biological overlap
├── 05_report.py         # JSON report generation with disclaimers
├── generators/
│   └── synthetic_data.py # Canonical source for mock data (checksummed)
├── utils/
│   ├── imputation.py    # KNN/Median strategies
│   ├── validation.py    # Replicate checks, data type validation
│   └── hashing.py       # Content hashing for versioning
└── main.py              # Orchestration script

tests/
├── test_ingest.py
├── test_merge.py
└── test_model.py

data/
├── raw/                 # Downloaded/mock raw files
└── processed/           # Merged, normalized CSVs
```

**Structure Decision**: Single project structure (`code/`) selected for simplicity and ease of CI/CD on GitHub Actions. No frontend/backend split required for this research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is limited to a single pipeline on CPU. | N/A |

## Phase Breakdown & FR/SC Coverage

### Phase 0: Data Strategy & Validation
- **FR-001, FR-011, FR-012**: Query NCBI GEO and Metabolomics Workbench using specific accession search strings for *Arabidopsis* paired RNA-seq/VOC data. Log results. If no paired data is found (as currently verified), generate a synthetic dataset using `code/generators/synthetic_data.py` (canonical source, checksummed). Implement replicate check (≥3) and continuous metadata validation (including CO2).
- **SC-004**: Stability of feature importance will be measured during CV.
- **Constitution**: Verify canonical source for synthetic data and checksumming mechanism.

### Phase 1: Data Ingestion & Preprocessing
- **FR-001, FR-002, FR-003**: Implement ingestion (mock or real), TPM normalization, imputation (median/KNN), and strict sample pairing. Exclude unpaired samples.
- **FR-011 (Code: `code/01_ingest.py`)**: Filter conditions with <3 replicates.
- **FR-012 (Code: `code/02_merge.py`)**: Exclude samples with missing continuous environmental metadata (temperature, light intensity, **CO2 level**).
- **SC-001**: Prepare data for R² baseline comparison.
- **Dimensionality**: Aggregate gene expression into pathway-level features (e.g., TPS families) to reduce dimensionality for N=60.

### Phase 2: Model Training & Evaluation
- **FR-004, FR-005**: Train Random Forest Regressor (scikit-learn) with **Nested k-Fold Cross-Validation

The specific value to remove/generalize: 'k'

Rewritten passage:
Nested k-Fold Cross-Validation** (inner loop for tuning, outer for evaluation) on CPU. Report R² and RMSE.
- **FR-009**: Add associational disclaimer to outputs.
- **SC-001, SC-002**: Measure R² against mean-predictor baseline and RMSE against observed variability.
- **Statistical Rigor**: Fit imputation parameters only on training folds to prevent leakage.

### Phase 3: Interpretation & Reporting
- **FR-006, FR-007, FR-008, FR-010**: Calculate permutation importance (using null distribution generation), SHAP values, and overlap with terpene synthase families. Apply Benjamini-Hochberg correction on derived p-values.
- **SC-003, SC-004, SC-005**: Report overlap proportion, stability across folds, and **FDR value** (per `contracts/output.schema.yaml`).
- **Output**: Generate JSON report with disclaimers and corrected significance flags.

## Compute Feasibility Plan

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Data Size**: Capped at ~ samples to ensure <1 hour runtime and <4GB RAM usage.
- **Method**: Random Forest (CPU-optimized in scikit-learn). No GPU, no quantization.
- **Fallback**: If real data is unavailable (highly likely given the verified list), the pipeline will run on a synthetic dataset generated to match the schema, ensuring the code logic is validated.