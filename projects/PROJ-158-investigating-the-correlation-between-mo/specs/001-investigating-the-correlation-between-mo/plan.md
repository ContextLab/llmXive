# Implementation Plan: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

**Branch**: `001-molecular-structure-dssc-performance` | **Date**: 2026-06-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-molecular-structure-dssc-performance/spec.md`

## Summary

This feature implements a computational pipeline to investigate the **efficacy of different model architectures** (Graph Convolutional Network vs. Random Forest) in capturing the correlation between molecular structure and Dye-Sensitized Solar Cell (DSSC) performance (Power Conversion Efficiency, PCE). The approach involves ingesting the **Nazeer et al. DSSC dataset** (experimental PCE values), standardizing molecular structures using RDKit, and training a GCN alongside a Random Forest baseline. The models will be evaluated using scaffold-aware k-fold cross-validation on CPU-only hardware. The study **does not claim to discover the existence** of a structure-performance correlation (which is assumed), but rather compares how well different architectures model this relationship. Finally, interpretability analysis will extract **model-attributed** substructures, explicitly framed as associational features rather than causal drivers.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `pandas`, `pyyaml`, `requests`
**Storage**: Local files (`data/raw/`, `data/processed/`), JSON/CSV/Parquet artifacts.
**Testing**: `pytest` (unit tests for ingestion, integration tests for training loop).
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).
**Project Type**: Computational Research / Data Science Pipeline.
**Performance Goals**: Complete training and evaluation within 6 hours on CPU; MAE/R² metrics computed per fold.
**Constraints**: No GPU usage; memory usage < 7GB; strict scaffold-aware splitting to prevent leakage.
**Scale/Scope**: Dataset size < 1GB (estimated); ~A fixed number of epochs per fold; 5 folds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale / Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan mandates pinned seeds, canonical Zenodo dataset URL, and `requirements.txt`. |
| **II. Verified Accuracy** | **Pass** | Dataset URL restricted to the verified Zenodo source (Nazeer et al.). No invented URLs. |
| **III. Data Hygiene** | **Pass** | Raw data preserved; transformations create new files; checksums required in `state.yaml`. |
| **IV. Single Source of Truth** | **Pass** | All metrics derived from `code/` execution; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes; state file updated on change. |
| **VI. Scaffold-Aware Validation** | **Pass** | Plan explicitly implements Bemis-Murcko scaffold splitting and non-parametric statistical tests. |
| **VII. Chemical Descriptor Integrity** | **Pass** | RDKit standardization (tautomer, salt removal) is a required step before graph construction. |

## Project Structure

### Documentation (this feature)

```text
specs/001-molecular-structure-dssc-performance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dssc_dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.py          # Downloads and checksums raw data from Zenodo
│   ├── preprocess.py        # RDKit standardization & graph feature extraction
│   └── split.py             # Scaffold-aware splitting logic
├── models/
│   ├── gcn.py               # GCN architecture (CPU optimized)
│   ├── rf_baseline.py       # Random Forest baseline
│   └── train.py             # Training loop with cross-validation
├── analysis/
│   ├── interpret.py         # Integrated gradients / motif extraction
│   └── stats.py             # Wilcoxon signed-rank tests, effect sizes
├── utils/
│   ├── logger.py
│   └── config.py            # Seed pinning, paths
└── main.py                  # Orchestration script
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `models`, `analysis`) to ensure isolation of concerns and easy reproducibility.

## Phase Breakdown (Mapping to FR/SC)

### Phase 0: Data Acquisition & Integrity (FR-001, FR-009, SC-001)
- **Action**: Download DSSC dataset from **Nazeer et al. Zenodo repository** (Verified Source).
- **Action**: Verify checksums and PCE unit consistency (FR-009).
- **Action**: Log any missing/invalid PCE entries.
- **Output**: `data/raw/dssc_dataset.csv` (or parquet).

### Phase 1: Pre-processing & Graph Construction (FR-002, FR-007, SC-004)
- **Action**: Standardize SMILES (salt removal, tautomer canonicalization) via RDKit.
- **Action**: Compute atom/bond features (atomic number, hybridization, aromaticity).
- **Action**: Handle invalid SMILES (log to `failed_molecules.log`).
- **Output**: `data/processed/graph_data.pt` (PyTorch Geometric format).

### Phase 2: Model Training & Evaluation (FR-003, FR-004, FR-005, SC-002, SC-003)
- **Action**: Implement Bemis-Murcko scaffold extraction.
- **Action**: Perform 5-fold scaffold-aware split.
- **Action**: Train GCN (≤2 layers, hidden=128) and RF (Morgan fingerprints) on CPU.
- **Action**: Compute MAE, RMSE, R² per fold.
- **Action**: Execute **Wilcoxon signed-rank test** (non-parametric) to compare fold-wise MAE distributions, calculating effect size (Cliff's Delta).
- **Action**: Write the **entire aggregated metrics object** (containing `gcnn_results`, `random_forest_results`, and `motifs`) to `results/metrics.json` as defined in the schema.
- **Output**: `results/metrics.json`, `results/model_artifacts/`.

### Phase 3: Interpretability & Motif Extraction (FR-006, FR-008, SC-005)
- **Action**: Apply Integrated Gradients to GCN predictions.
- **Action**: Identify top recurring subgraphs (motifs) in high-PCE predictions.
- **Action**: **Validation Step**: Perform a statistical enrichment test of identified motifs against a null distribution of random subgraphs to distinguish model bias from signal.
- **Action**: Verify motifs are non-isomorphic.
- **Action**: **Limitation Statement**: Explicitly label motifs as "model-attributed features associated with high PCE" and not "causal drivers" due to uncontrolled confounding variables.
- **Output**: Motifs included in `results/metrics.json` (under `motifs` key).

## Compute Feasibility Statement
The plan explicitly restricts the GCN to ≤2 layers and hidden size 128, and mandates CPU-only execution. The dataset is expected to be <1GB. The total runtime is estimated to be well [deferred] on a 2-core CPU runner, avoiding GPU dependencies (no CUDA, no mixed precision). Memory usage is controlled by processing folds sequentially and avoiding large batch sizes if necessary.

## Statistical Methodology Note
Given the small number of folds (N=5), the plan adopts a **non-parametric Wilcoxon signed-rank test** instead of a paired t-test to ensure methodological rigor and avoid violations of normality assumptions. This addresses the low statistical power inherent in 5-fold cross-validation comparisons.