# Implementation Plan: Predict Plant Disease Resistance from Multi‑omics Data

**Branch**: `001-predict-plant-disease-resistance` | **Date**: 2026-06-25 | **Spec**: `specs/001-predict-plant-disease-resistance/spec.md`
**Input**: Feature specification from `specs/001-predict-plant-disease-resistance/spec.md`

## Summary

This feature implements a reproducible, CPU-tractable pipeline to predict plant disease resistance using paired genomic (SNP) and metabolomic data. The system downloads public datasets from **NCBI SRA** and **MetaboLights**, preprocesses raw reads, aligns modalities, performs LASSO/Random Forest feature selection with Benjamini-Hochberg correction, trains Elastic-Net/Gradient Boosting models with **Nested Cross-Validation**, and validates via **Block Permutation Testing**. The pipeline enforces strict data integrity (sufficient paired samples), resource constraints (≤7GB RAM, ≤6h), and statistical rigor (VIF > 5 flagging, BH-adjusted p < 0.05).

**Critical Data Policy**: This pipeline is designed for **real biological discovery**. It operates in two distinct modes:
1.  **Scientific Mode (Default)**: Attempts to download real multi-omics data. If no real dataset (SNP + Metabolite + Phenotype) is found, the pipeline **HALTS** with `EX_DATA_INTEGRITY`. No synthetic data is used for scientific results.
2.  **CI Mode (`--ci-mode`)**: Explicitly generates synthetic data to verify code logic, file I/O, and pipeline structure. **SC-001 (≥75% accuracy) is NOT applicable to CI Mode.** Synthetic data is never used to validate biological hypotheses.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==1.26.4`, `statsmodels==0.14.2`, `pyyaml==6.0.1`, `datasets` (HuggingFace for metadata only), `pytest`, `biopython`  
**Storage**: Local file system (`data/`, `code/`), HDF5/Parquet for intermediate large tables  
**Testing**: `pytest` with coverage, contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7GB RAM)  
**Project Type**: CLI / Data Science Pipeline  
**Performance Goals**: End-to-end ≤ 6 hours, Peak RAM ≤ 7 GB  
**Constraints**: No GPU available for training; data must be streamed or sampled to fit RAM; strict error codes for data/power insufficiency.  
**Scale/Scope**: Analysis of public multi-omics datasets (target: ≥100 samples, thousands of features).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and re-runnable Docker container. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to verified NCBI SRA/MetaboLights sources. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan requires `data_manifest.yaml` with checksums; raw data preserved; derivations versioned. |
| **IV. Single Source of Truth** | **PASS** | Metrics output to CSV/JSON; paper figures generated programmatically from these files. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; `state/` updated on artifact change. |
| **VI. Multi‑omics Provenance** | **PASS** | Plan explicitly defines `data_manifest.yaml` to record accession numbers (NCBI/MetaboLights), query strings, and retrieval dates. Synthetic data is excluded from scientific runs. |
| **VII. Statistical Validation** | **PASS** | Plan mandates BH correction (with LD-aware permutation), nested cross-validation, VIF calculation (flag > 5 per FR-005), and CI reporting. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-disease-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (populated)
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-259-predicting-plant-disease-resistance-from/
├── code/
│   ├── __init__.py
│   ├── download.py              # Data retrieval from NCBI SRA/MetaboLights & manifest generation
│   ├── preprocess.py            # SNP/Metabolite normalization (fastp/bcftools wrappers)
│   ├── feature_selection.py     # LASSO/RF, BH correction, sensitivity sweep
│   ├── model_training.py        # Elastic-Net/GBM, Nested CV, Permutation test
│   ├── validation.py            # External validation logic
│   ├── utils/
│   │   ├── resources.py         # Memory/CPU monitoring (T046 artifact)
│   │   └── stats.py             # VIF, p-value calculation, Block Permutation
│   └── cli.py                   # Main entry point
├── data/
│   ├── raw/                     # Downloaded raw files (NCBI/MetaboLights)
│   ├── processed/               # Aligned matrices
│   ├── data_manifest.yaml       # Provenance record
│   └── synthetic/               # Synthetic fallbacks ONLY for --ci-mode (not scientific)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                # Schema validation tests
├── docs/
│   └── ...
└── requirements.txt
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) selected to align with CLI pipeline nature and simplify Docker containerization for CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multi-modal alignment** | FR-001 requires strict pairing of SNP, Metabolite, and Phenotype. | Simple single-modality analysis would fail FR-001 and US-1. |
| **Nested Cross-Validation** | Scientific Soundness concern: Feature selection must be nested to avoid circular validation. | Simple CV on selected features inflates performance and invalidates p-values. |
| **Block Permutation** | Scientific Soundness concern: SNPs/Metabolites are correlated (LD/co-regulation). | Independent label shuffling fails to control FDR in correlated data. |
| **VIF Flag > 5** | Spec FR-005 mandates flagging VIF > 5. | VIF > 33 accepts extreme collinearity, destabilizing coefficients. |
| **Halt on Missing Data** | Constitution Principle VI & Data Resources concern: No synthetic data for science. | Generating synthetic data to "fill gaps" invalidates the biological hypothesis. |

## Task Resolution Notes

- **T018 (Permutation Formula)**: Formula corrected to `p = (count + 1) / (n + 1)`. Fixed seed mandatory.
- **T047 (Robustness Check)**: Removed "halt if variance > [deferred]". Variance is now a reported metric only.
- **T042 (Data Manifest)**: `download.py` now halts if real multi-omics data is missing. Synthetic data is CI-only. Explicitly logs "CRITICAL: Real data missing. Generating synthetic data for CI mode only." and calls `generate_synthetic.py`. Generates `data_manifest.yaml` with `source: SIMULATED`.
- **T046 (Resource Monitor)**: `code/utils/resources.py` is implemented and listed in structure. Monitors RAM/CPU and logs to `pipeline_log.txt`.
- **T048 (Permutation Reproducibility)**: Plan includes a specific task to run permutation test twice with fixed seed and assert match.
- **FR-009 (Data Split)**: Explicitly defined as `StratifiedShuffleSplit` (scikit-learn) with [deferred] Training / [deferred] Hold-out ratio.
