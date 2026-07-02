# Implementation Plan: Predicting Plant Pathogen Host Range from Publicly Available Genomic and Interaction Data

**Branch**: `001-predicting-plant-pathogen-host-range-fro` | **Date**: 2026-06-24 | **Spec**: `specs/001-predicting-plant-pathogen-host-range-fro/spec.md`
**Input**: Feature specification from `/specs/001-predicting-plant-pathogen-host-range-fro/spec.md`

## Summary

This project implements a computational pipeline to predict plant pathogen host ranges using genomic features (effector counts, Pfam domains, GC content, k-mer frequencies, secondary-metabolism clusters) and public interaction data (PHI-Base, Interactome3D, NCBI BioSample). The core deliverable is an interpretable, regularized logistic-regression model trained on a diverse set of pathogens, validated via k-fold cross-validation and permutation testing, running entirely on CPU-only CI hardware within 5 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (>=1.3.0), `pandas` (>=2.0.0), `numpy` (>=1.24.0), `shap` (>=0.44.0, cpu-only), `biopython` (>=1.81), `requests` (>=2.31.0), `loguru` (>=0.7.0), `pyyaml` (>=6.0.1)  
**Storage**: Local filesystem (`data/`, `results/`, `logs/`); no external database required.  
**Testing**: `pytest` (>=7.4.0) with `pytest-cov` for coverage; contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, 14 GB disk).  
**Project Type**: CLI pipeline (Python scripts + Bash wrappers).  
**Performance Goals**: End-to-end runtime ≤ 5 hours for 50 pathogens; memory ≤ 4 GB; prediction latency ≤ 30s per novel genome.  
**Constraints**: No GPU/CUDA; no deep learning; no proprietary data; strict data provenance (NCBI GenBank, PHI-Base, etc.); missing interactions treated as 'unknown' unless sensitivity analysis is run.  
**Scale/Scope**: A diverse set of pathogens (max 2 GB total genome data), ~ host species, genomic feature categories.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Detail |
|------------------------|-------------------|------------------------|
| **I. Reproducibility** | ✅ Compliant | Random seeds pinned in `code/`; external datasets fetched from canonical sources (NCBI, PHI-Base) on every run; `requirements.txt` pins all dependencies. |
| **II. Verified Accuracy** | ✅ Compliant | All citations in `research.md` and `plan.md` validated against primary sources; title-token overlap ≥ 0.7 enforced by Reference-Validator Agent. URLs for PHI-Base, Interactome3D, NCBI BioSample, and NCBI GenBank are now explicitly listed in `research.md`. |
| **III. Data Hygiene** | ✅ Compliant | All `data/` files checksummed; raw data preserved; transformations produce new files with derivation logs; PII scan passed. |
| **IV. Single Source of Truth** | ✅ Compliant | Every figure/statistic in paper traces to exactly one row in `data/` and one block in `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Compliant | All artifacts carry content hashes; `state/` YAML updated on artifact changes; Advancement-Evaluator invalidates stale reviews. |
| **VI. Biological Data Provenance** | ✅ Compliant | Pathogen genomes from NCBI GenBank with exact accession versions recorded; interaction records from PHI-Base/Interactome3D/NCBI BioSample with source and retrieval date logged. |
| **VII. Interpretability and Biological Relevance** | ✅ Compliant | SHAP values generated for all features; feature importance validated against biological expectations (effectors, secondary metabolism); mechanisms linked to model outputs in manuscript. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-plant-pathogen-host-range-fro/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── dataset.schema.yaml
│   ├── genomic_features.schema.yaml
│   ├── interaction.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-515-predicting-plant-pathogen-host-range-fro/
├── code/
│   ├── __init__.py
│   ├── cli/
│   │   ├── run_pipeline.sh          # Bash wrapper with --data-dir, --mode, --seed args
│   │   └── predict_host_range.sh    # Prediction script with --genome arg
│   ├── download/
│   │   ├── fetch_genomes.py         # NCBI GenBank downloader (FR-001)
│   │   └── fetch_interactions.py    # PHI-Base/Interactome3D/NCBI BioSample merger (FR-002)
│   ├── features/
│   │   ├── extract_genomic_features.py  # EffectorP, Pfam, GC, k-mer, antiSMASH (FR-003)
│   │   └── collinearity_check.py        # VIF analysis (FR-014)
│   ├── model/
│   │   ├── train.py                   # Logistic regression with CV (FR-004, FR-005)
│   │   ├── evaluate.py                # AUPRC, precision, permutation testing (FR-006, FR-007)
│   │   └── predict.py                 # Novel genome prediction (FR-008, US-3)
│   ├── report/
│   │   ├── generate_reports.py        # SHAP, significant features, bias report (FR-007, FR-018)
│   │   └── sensitivity_analysis.py    # FR-016: unknown vs. negative comparison
│   └── utils/
│       ├── logging.py                 # pipeline.log with timestamps (FR-010)
│       └── validation.py              # Data quality checks (FR-013, FR-011)
├── data/
│   ├── raw/                           # Downloaded genomes, interaction tables
│   ├── processed/                     # Feature matrices, interaction matrices
│   └── checksums.json                 # Data hygiene checksums (Constitution III)
├── results/
│   ├── model.pkl                      # Trained model artifact
│   ├── feature_importance.csv         # SHAP values
│   ├── significant_features.tsv       # Permutation-test results
│   ├── prediction.csv                 # Novel pathogen predictions
│   └── bias_awareness_report.json     # Training distribution analysis
├── logs/
│   └── pipeline.log                   # All processing steps (FR-010)
├── tests/
│   ├── contract/                      # Schema validation tests
│   ├── integration/                   # End-to-end pipeline tests
│   └── unit/                          # Feature extraction, model training tests
├── requirements.txt                   # Pinned dependencies (Constitution I)
└── README.md                          # Quickstart guide (quickstart.md)
```

**Structure Decision**: Single-project structure with modular `code/` subdirectories for download, features, model, report, and utils. This aligns with CLI pipeline requirements, ensures reproducibility, and facilitates testing. The `contracts/` directory contains YAML schemas for data and model outputs, validated by contract tests.

### Contract Testing

Contract tests (`tests/contract/`) will validate:
- `dataset.schema.yaml`: Validates input data structure (genomes, interactions, features).
- `genomic_features.schema.yaml`: Validates extracted feature vectors.
- `interaction.schema.yaml`: Validates interaction records (including -1 for unknown).
- `model_output.schema.yaml`: Validates model artifacts and prediction outputs.

## Implementation Phases

### Phase 0: Data Ingestion & Validation
- **T001**: Implement `fetch_genomes.py` to download FASTA files from NCBI GenBank (FR-001).
- **T002**: Implement `fetch_interactions.py` to merge PHI-Base, Interactome3D, and NCBI BioSample (FR-002).
- **T003**: Implement data validation logic to handle missing genomes (warning) and missing interactions (FR-011, FR-013).
- **T004**: Generate `data/processed/interaction_matrix.csv` and `data/processed/genome_manifest.json`.

### Phase 1: Feature Engineering & Preprocessing
- **T005**: Implement `logging.py` to configure loguru with timestamps and error levels (FR-010).
- **T006**: Implement `extract_genomic_features.py` to compute effector counts, Pfam, GC, k-mers, and SM clusters (FR-003).
- **T007**: Implement dimensionality reduction: PCA (k=20) for k-mers and top-50 filtering for Pfam domains (Research Rationale).
- **T008**: Implement `collinearity_check.py` to perform VIF analysis and remove collinear features (FR-014).
- **T009**: Generate `data/processed/feature_matrix.csv`.

### Phase 2: Model Training & Evaluation
- **T010**: Implement `train.py` for L1 logistic regression with inner/outer CV (FR-004, FR-005).
- **T011**: Implement `evaluate.py` for AUPRC, precision, and permutation testing (FR-006, FR-007).
- **T012**: Implement SHAP value generation and feature ranking (FR-007).
- **T013**: Generate `results/model.pkl`, `results/feature_importance.csv`, `results/significant_features.tsv`.

### Phase 3: Reporting & Sensitivity Analysis
- **T014**: Implement `generate_reports.py` to create the Bias-Awareness Report (FR-018).
- **T015**: Implement `sensitivity_analysis.py` to compare 'unknown' vs 'negative' treatments (FR-016).
- **T016**: Generate `results/bias_awareness_report.json` and `results/sensitivity_report.json`.

### Phase 4: CLI & Deployment
- **T017**: Create `run_pipeline.sh` CLI entry point.
  - **Arguments**: `--data-dir` (path to input data), `--mode` (train, predict, sensitivity), `--seed` (random seed).
  - **Outputs**: `results/model.pkl`, `results/feature_importance.csv`, `results/significant_features.tsv`, `logs/pipeline.log`.
  - **Completion Criteria**: Script runs end-to-end on test data and produces all required artifacts.
- **T018**: Create `predict_host_range.sh` for novel pathogen prediction (US-3).
- **T019**: Run end-to-end integration tests on GitHub Actions.

### Phase 5: Validation & Documentation
- **T020**: Verify all outputs against `contracts/` schemas.
- **T021**: Update `README.md` and `quickstart.md`.
- **T022**: Final review and stage advancement.

## Complexity Tracking

> **No violations detected in Constitution Check; table omitted.**
