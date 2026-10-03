# Implementation Plan: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

**Branch**: `001-assess-uncertainty-quantification` | **Date**: 2026-06-22 | **Spec**: `specs/001-assess-uncertainty-quantification/spec.md`
**Input**: Feature specification from `/specs/001-assessing-uncertainty-quantification/spec.md`

## Summary

This project implements a comparative assessment of three lightweight Uncertainty Quantification (UQ) techniques—Deep Ensembles, Monte-Carlo (MC) Dropout, and Sparse Gaussian Processes (GP)—for predicting material properties (formation energy, bulk modulus, band gap) using the OQMD dataset. The plan ensures strict adherence to the project constitution, specifically the CPU runtime budget, reproducibility via pinned seeds, and data hygiene via checksums. The implementation will download the verified OQMD subset, engineer compositional and structural features, train a constrained baseline neural network (≤10k parameters) with a heteroscedastic output head, apply the three UQ methods, and evaluate them using Expected Calibration Error (ECE), interval scores, and a downstream screening case study against a Point Estimate baseline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `gpytorch` (for Sparse GP), `pandas`, `numpy`, `scikit-learn`, `datasets` (Hugging Face), `pyyaml`, `pytest`, `scipy`  
**Storage**: Local file system (`data/raw`, `data/processed`, `results/`) for intermediate CSVs/Parquets and model checkpoints.  
**Testing**: `pytest` with `conftest.py` for fixtures; integration tests for pipeline timeout enforcement.  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPU cores, several GB RAM).  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Total pipeline runtime ≤ 5 hours; Deep Ensemble training ≤ 30 mins; UQ evaluation ≤ 20 mins per property.  
**Constraints**: 
- A baseline neural network with a limited parameter count will be employed..
- No GPU usage (CPU-only implementation).
- Hard timeout enforcement (5 hours).
- Sparse GP must use PCA reduction to ≤20 components.
- Data must be streamed or sampled if full dataset exceeds RAM.
**Scale/Scope**: A stratified sample of inorganic compounds from OQMD; UQ methods; random seeds for robustness.

> **Spec Deviation Note**: FR-001 mandates downloading from 'https://huggingface.co/datasets/OQMD/OQMD-Subset'. This URL has no verified source. The plan substitutes it with the verified source `materials-toolkits/oqmd` (Hugging Face) which contains the necessary crystallographic data. This deviation is necessary to satisfy data hygiene and availability constraints.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts will use `seed=42` (and 43, 44 for robustness). `requirements.txt` will pin versions. Data downloaded from canonical Hugging Face URLs. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will only use the verified URLs provided in the metadata block. No fabricated dataset links. |
| **III. Data Hygiene** | **PASS** | `data/raw` files will be checksummed immediately after download. `validation_report.json` will log exclusions. |
| **IV. Single Source of Truth** | **PASS** | All metrics (ECE, Interval Score) will be computed by code and written to CSVs. No hand-typed numbers in `plan.md`. |
| **V. Versioning Discipline** | **PENDING** | Status will update to PASS only after `data/checksums.json` contains real hashes and `results/robustness_report.json` is generated. |
| **VI. Lightweight UQ Execution** | **PASS** | NN constrained to ≤10k params. Sparse GP limited to a moderate number of inducing points + PCA. Total runtime capped with explicit timeout logic. |
| **VII. Calibration-Driven Eval** | **PASS** | Evaluation module will output reliability diagrams (PNG), ECE, and Interval Scores for deferred intervals. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-uncertainty-quantification/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (SSoT)
│   ├── dataset.schema.yaml           # SSoT for MaterialSample
│   ├── uq_prediction.schema.yaml     # SSoT for UQPrediction
│   └── calibration_metric.schema.yaml # SSoT for CalibrationMetric
├── contracts/legacy/    # Legacy drafts (to be deleted by Implementer)
│   ├── dataset_schema.schema.yaml
│   ├── material_sample.schema.yaml
│   ├── metric.schema.yaml
│   └── prediction.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.py          # Downloads OQMD, checksums, retries
│   ├── preprocess.py        # Feature engineering, stratified split, exclusion logging
│   └── validation.py        # Generates validation_report.json
├── models/
│   ├── baseline_nn.py       # A neural network with a heteroscedastic head and a configurable number of hidden layers., ≤10k params
│   ├── deep_ensemble.py     # x NN training
│   ├── mc_dropout.py        # MC Dropout inference wrapper
│   └── sparse_gp.py         # PCA + Sparse GP with GPyTorch
├── eval/
│   ├── calibration.py       # ECE, Interval Score, Sharpness
│   ├── screening.py         # Downstream case study logic (Bootstrap CI)
│   └── plots.py             # Reliability diagrams
├── main.py                  # Pipeline orchestrator, timeout enforcement
└── utils/
    └── logging.py           # Structured logging

tests/
├── unit/                    # Model architecture checks, feature sanity
├── integration/             # Pipeline timeout, data flow
└── contract/                # Schema validation against contracts/

data/
├── raw/                     # Downloaded parquet/csv (checksummed)
├── processed/               # Train/Val/Test splits, feature matrices
└── checksums.json           # SHA-256 hashes

results/
├── models/                  # Saved checkpoints (NN, GP)
├── uq_predictions.csv       # Final predictions with bounds
├── calibration_report.csv   # ECE/Score metrics
├── reliability_diagrams/    # PNG files
└── robustness_report.json   # CV of ECE across seeds
```

**Structure Decision**: Selected a modular `code/` structure separating data, models, and evaluation to facilitate independent testing of the three UQ methods and strict adherence to the 5-hour runtime budget. The `main.py` orchestrator enforces the global timeout and seed management.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sparse GP with PCA** | Required by FR-005 to fit within 7GB RAM and 5h runtime on CPU. | Full GP is O(N³) and intractable for N>10k; standard GP without PCA would exceed memory. |
| **Three UQ Methods** | Required by spec to compare Deep Ensembles, MC-Dropout, and Sparse GP. | Using only one method would fail the comparative research question (US-2). |
| **Downstream Screening** | Required by US-3 to demonstrate practical utility. | Abstract metrics alone do not validate the "Motivation" of the project. |
| **Heteroscedastic NN** | Required to compute Aleatoric uncertainty (mean of variances). | Standard point-estimate NN cannot output variance, making FR-008 impossible. |
| **Bootstrap CI** | Required to compare disjoint samples (UQ vs. Point Estimate). | McNemar's test requires paired data, which is not available here. |