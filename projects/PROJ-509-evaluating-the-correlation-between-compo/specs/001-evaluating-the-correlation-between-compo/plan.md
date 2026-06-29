# Implementation Plan: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Branch**: `001-evaluating-compositional-correlation` | **Date**: 2026-06-24 | **Spec**: `specs/001-evaluating-the-correlation-between-compo/spec.md`

## Summary

This project implements a CPU-tractable pipeline to evaluate the correlation between compositional descriptors (mean/variance of electronegativity, atomic radius, valence electrons, melting point, ionization energy) and predicted formation energy in inorganic materials. The approach involves downloading the MP-2020.12.1 dataset from a verified Zenodo source, filtering for inorganic compounds, computing descriptors using `pymatgen`/`matminer`, training Random Forest and Gradient Boosting regressors via `scikit-learn`, and performing feature importance analysis with Partial Dependence Plots. The pipeline includes a rigorous multicollinearity check (VIF) and a null model baseline to ensure scientific validity.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pymatgen` (elemental properties), `scikit-learn` (models), `pandas` (data), `numpy` (numerics), `matplotlib` (plots), `pyyaml` (contracts).  
**Storage**: Local CSV/Parquet files in `data/` (raw and derived), JSON artifacts in `data/evaluation/`.  
**Testing**: `pytest` with contract validation against `contracts/`.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7 GB RAM, no GPU).  
**Project Type**: Data science CLI / research pipeline.  
**Performance Goals**: Total runtime ≤ 6 hours; Memory ≤ 4 GB during processing.  
**Constraints**: No GPU; no heavy deep learning; dataset size capped at [deferred] rows if >60,000 detected to ensure feasibility.
**Scale/Scope**: Processing up to 150k+ inorganic entries (automatically sampled to a reduced size if memory constraints are approached).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan includes pinned `random_state` and explicit dataset versioning (Zenodo DOI). |
| **II. Verified Accuracy** | **Pass** | Dataset source is the canonical MP-2020 Zenodo mirror (DOI: 10.5281/zenodo.4053859) which is verified and accessible. |
| **III. Data Hygiene** | **Pass** | Plan mandates checksumming of raw data and versioned derived files. |
| **IV. Single Source of Truth** | **Pass** | All metrics derived from `data/evaluation/model_metrics.json` (sole SSoT). |
| **V. Versioning Discipline** | **Pass** | Content hashes will be recorded in `state/`. |
| **VI. Deterministic Feature Engineering** | **Pass** | Descriptors computed via pure functions from a versioned elemental table. |
| **VII. Statistical Evaluation Rigor** | **Pass** | Plan includes Chemical Family stratified split, VIF analysis, permutation importance, and PDPs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-correlation-between-compo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-509-evaluating-the-correlation-between-compo/
├── data/
│   ├── raw/                 # Downloaded MP-2020.12.1 (parquet/csv)
│   ├── elemental_properties/ # Versioned elemental reference table
│   ├── processed/           # Computed descriptors (CSV)
│   └── evaluation/          # Model metrics, PDP data
├── code/
│   ├── __init__.py
│   ├── ingest.py            # FR-001: Download & Filter
│   ├── descriptors.py       # FR-002: Compute features
│   ├── train.py             # FR-003: Train RF & GB
│   ├── evaluate.py          # FR-004: Metrics & Split check
│   ├── importance.py        # FR-005: Permutation & Ranking
│   └── plots.py             # FR-006: PDP generation
├── tests/
│   ├── contract/            # Schema validation tests
│   └── unit/                # Descriptor logic tests
├── contracts/               # Implementation artifacts for validation
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
├── requirements.txt         # Pinned dependencies
└── README.md
```

**Structure Decision**: Single project structure with clear separation of `data/` (raw vs. processed) and `code/` (modular pipeline steps) to ensure reproducibility and easy testing on CI.

## Memory & Sampling Protocol

To guarantee feasibility on the GitHub Actions free-tier (7 GB RAM, 6h runtime):
1. **Threshold**: If the filtered dataset exceeds **[deferred] rows**, a **stratified sample** (by **Chemical Family**) is taken to exactly **[deferred] rows**.
2. **Stratification**: Sampling is stratified by the most abundant element in the compound (Chemical Family) to preserve compositional diversity.
3. **Trigger**: This check occurs in `ingest.py` immediately after filtering.
4. **Logging**: The sampling action and the resulting row count are logged to `data/logs/sampling.log`.

## Complexity Tracking

No violations found. The project adheres to the CPU-only constraint by selecting `scikit-learn` models and limiting data size via stratified sampling. The stratification method has been updated to 'Chemical Family' to ensure scientific validity, overriding the legacy spec assumption of 'crystal system' stratification.
