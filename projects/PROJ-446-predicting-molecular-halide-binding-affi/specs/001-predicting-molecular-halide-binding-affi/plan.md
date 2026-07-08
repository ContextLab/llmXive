# Implementation Plan: Predicting Molecular Halide Binding Affinities with Machine Learning

**Branch**: `001-predicting-halide-binding-affinities` | **Date**: 2024-01-15 | **Spec**: `specs/001-predicting-halide-binding-affinities/spec.md`

## Summary

This feature implements a machine learning pipeline to predict molecular halide binding affinities using experimental data from NIST and PubChem. The approach involves data ingestion with strict solvent filtering (acetonitrile, chloroform, DCM), molecular descriptor generation (ECFP, RDKit), and training of Random Forest and Gradient Boosting models. 

**Critical Scope Limitation**: No verified dataset currently exists in the provided resource list that contains the required variables (host SMILES, halide identity, binding constant, solvent). The pipeline will attempt to scrape NIST/PubChem, but given the high probability of failure, it is designed to trigger the **Simulated Data Fallback (FR-011)** immediately. In this mode, the pipeline generates synthetic data based on a hardcoded physics formula. **Crucially, in Simulated Data Mode, the comparative analysis (US-4) is explicitly aborted and flagged as unanswerable.** All outputs in this mode are marked "Simulated Data Mode" and are strictly for pipeline validation, not scientific discovery.

All analysis is framed as **associational** (not causal). The "Physical Plausibility Check" in simulated mode is a trivial confirmation of the generation formula, not a validation of chemical learning.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn>=1.4.0`, `rdkit`, `pandas`, `numpy`, `requests`, `beautifulsoup4`, `pyyaml`  
**Storage**: Local CSV/Parquet files in `data/`  
**Testing**: `pytest`  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, 7 GB RAM, CPU-only)  
**Project Type**: Computational Chemistry / Data Science Pipeline  
**Performance Goals**: Complete training and analysis within 6 hours; peak RAM < 7 GB  
**Constraints**: 
- No GPU/CUDA (Constitution Principle I: Reproducibility)
- No deep learning from scratch
- Strict solvent filtering
- Host-identity splitting
- **Causal Limitation**: No causal claims; all findings are associational.

**Scale/Scope**: Target ≥50 host molecules with ≥3 halide measurements each; fallback to simulated data if <50. **If simulated data is used, comparative analysis is aborted.**

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`; external datasets fetched from canonical HuggingFace URLs (or simulated); `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | **Blocking Gate**: The Reference-Validator Agent validates all citations (NIST, PubChem, literature) against primary sources. **If validation fails, the build fails.** DOI checks are enforced. |
| **III. Data Hygiene** | **Compliant** | Raw data checksummed in `state.yaml`; transformations produce new files; no in-place modification; PII scan enforced. |
| **IV. Single Source of Truth** | **Compliant** | **Traceability Mechanism**: Every figure, statistic, or interpretation in the paper includes a `run_id` and `data_row_id` that trace back to exactly one row in `data/` and one block in `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Content hashes updated in `state.yaml` on every artifact change; `updated_at` timestamps maintained. |
| **VI. Halide-Specific Evaluation** | **Compliant** | Model performance evaluated separately for F⁻, Cl⁻, Br⁻, I⁻; per-halide R²/RMSE reported; aggregate scores insufficient. **Abort if N < 10 per halide.** |
| **VII. Molecular Split Validation** | **Compliant** | Data splits performed by host molecule identity (not measurement); strategy documented and verified before training. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-halide-binding-affinities/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-446-predicting-molecular-halide-binding-affi/
├── code/
│   ├── requirements.txt
│   ├── 01_data_ingestion.py       # FR-001, FR-010, FR-011
│   ├── 02_feature_engineering.py  # FR-002, FR-003
│   ├── 03_model_training.py       # FR-004, FR-005
│   ├── 04_feature_analysis.py     # FR-006, FR-007, FR-013
│   ├── 05_statistical_reporting.py# FR-008, FR-009, FR-012
│   └── utils/
│       ├── config.py              # Random seeds, paths
│       └── validators.py          # Schema validation
├── data/
│   ├── raw/                       # Downloaded raw data (checksummed)
│   ├── processed/                 # Cleaned CSVs, descriptors
│   └── simulated/                 # Fallback simulated data (if triggered)
├── docs/
│   └── paper/                     # Final report, figures
└── state/
    └── projects/PROJ-446-...yaml  # Artifacts, hashes, stage
```

**Structure Decision**: Single-project structure selected to maintain tight coupling between data pipeline, modeling, and reporting. `code/` contains sequential scripts for reproducibility; `data/` separates raw and processed to enforce hygiene; `state/` tracks artifact hashes per Constitution Principle V.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Simulated Data Fallback (FR-011)** | NIST/PubChem may lack sufficient halide-specific records (≥50 hosts, ≥3 halides each). **No verified dataset exists.** | Directly aborting the project would fail the research goal; simulation with physics constraints (charge density, cavity volume) provides a fallback for **pipeline validation only**. **Comparative analysis (US-4) is explicitly aborted in this mode.** |
| **Host-Identity Splitting (FR-004)** | Prevents data leakage where same host appears in train and test. | Random measurement splitting would inflate performance metrics by leaking host-specific structural info. |
| **Bootstrap CIs (FR-009)** | Small sample size (N=5 folds) invalidates parametric tests; Wilcoxon unsuitable. **Measurement-level bootstrap used; abort if N < 10 per halide.** | Standard t-tests or Wilcoxon would produce unreliable p-values; bootstrap provides robust CI estimation for performance differences (if powered). |
| **Causal Limitations** | Observational data cannot support causal claims. | Attempting causal inference without randomization would violate scientific rigor and Constitution Principle I. |
