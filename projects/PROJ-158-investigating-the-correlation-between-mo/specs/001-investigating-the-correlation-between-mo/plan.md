# Implementation Plan: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

**Branch**: `001-molecular-structure-dssc-performance` | **Date**: 2026-06-27 | **Spec**: `specs/001-molecular-structure-dssc-performance/spec.md`

## Summary

This project implements a machine learning pipeline to predict the Power Conversion Efficiency (PCE) of Dye-Sensitized Solar Cells (DSSCs) based on molecular structure. The approach utilizes a Graph Convolutional Network (GCN) with ≤2 layers, trained on CPU, compared against a Random Forest baseline using Morgan fingerprints. The workflow strictly adheres to scaffold-aware cross-validation to prevent data leakage and includes an interpretability phase to identify structural motifs driving high performance. All steps are constrained to run within the GitHub Actions free-tier limits (limited CPU, limited RAM, 6h runtime).

**Key Methodological Updates**:
- Statistical testing updated to **Wilcoxon signed-rank test** (non-parametric) to handle small sample sizes (n=5 folds).
- **Confounding variable control**: Molecular Weight (MW) and atom count will be included as covariates/features to ensure motifs are not size proxies.
- **Dataset provenance**: Explicit validation of PCE values against Nazeer et al. ranges and fallback to DSSC2024 if provenance is weak.
- **Motif validation**: Counterfactual checks added to validate motif predictive power.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `pandas`, `networkx`, `pyyaml`
**Storage**: Local file system (`data/raw`, `data/processed`, `code/outputs`)
**Testing**: `pytest` (unit tests for data ingestion, integration tests for training loop)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Data Science / Computational Chemistry Pipeline
**Performance Goals**: Complete full 5-fold CV and analysis within 6 hours; memory usage < 7GB.
**Constraints**: No GPU; GCN hidden size ≤ 128; max 2 GCN layers; hard timeout wrapper (5h 30m) integrated into training loop.
**Scale/Scope**: Dataset size < 1GB (verified); ~100-500 molecules (typical for DSSC specific datasets).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

### Verified Dataset Sources (Constitution Principle II)
The following datasets are used, mapped to the 'Nazeer et al.' claim:
1. **DSSC-Final-Datasets**: ` (Primary candidate, subject to provenance verification).
2. **DSSC2024**: ` (Secondary candidate, selected if primary lacks scientific metadata).

## Constitution Check

| Principle | Status | Implementation Strategy |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/utils/seeds.py`. External datasets fetched via verified HuggingFace loaders (see Technical Context). `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **PASS** | All dataset citations map to the "Verified datasets" block above. Provenance verification step added to ensure alignment with Nazeer et al. data. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw` with immediate checksum verification (single atomic operation: download + verify). Derivations written to `data/processed`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Metrics stored in `data/outputs/metrics.json`. This file is the SSoT for all reported statistics in `plan.md`, `research.md`, and `paper.md`. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/projects/PROJ-158-investigating-the-correlation-between-mo.yaml` upon completion of each phase. |
| **VI. Scaffold-Aware Validation** | **PASS** | `code/models/split.py` implements `get_scaffold_split` (Bemis-Murcko). Fallback to stratified random split if fold size < 5. Paired statistical tests (Wilcoxon) mandated in `code/eval/stats.py`. |
| **VII. Chemical Descriptor Integrity** | **PASS** | RDKit standardization (tautomer/salt removal) enforced in `code/data/preprocess.py`. MW and atom count computed and stored for confounding control. |

## Project Structure

### Documentation (this feature)

```text
specs/001-molecular-structure-dssc-performance/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output
 ├── dataset.schema.yaml
 ├── model_output.schema.yaml
 └── motif.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│ ├── download.py # Downloads from verified HF URLs + checksum verify
│ ├── preprocess.py # RDKit standardization, graph generation, MW/atom count
│ └── validate.py # Schema and PCE range validation
├── models/
│ ├── gcn.py # 2-layer GCN implementation
│ ├── rf.py # Random Forest baseline
│ ├── split.py # Scaffold-aware k-fold logic (get_scaffold_split)
│ └── train.py # Training loop with integrated timeout wrapper
├── eval/
│ ├── metrics.py # MAE, RMSE, R² calculation
│ └── stats.py # Wilcoxon signed-rank test, permutation test, Cohen's d
├── interpret/
│ ├── motifs.py # GNNExplainer/IG, subgraph extraction, counterfactual check
│ └── viz.py # Substructure visualization helpers
├── utils/
│ ├── seeds.py # Global random seed pinning
│ └── timeout.py # Hard timeout wrapper implementation
└── main.py # Orchestration script

tests/
├── unit/
│ ├── test_preprocess.py
│ └── test_scaffold_split.py # Validates get_scaffold_split logic
└── integration/
 └── test_training_loop.py
```

**Structure Decision**: Single project structure selected to minimize overhead for a CPU-bound, single-dataset analysis. The separation of `data`, `models`, `eval`, and `interpret` ensures modularity for the specific requirements of FR-001 through FR-009.

## Complexity Tracking

No complexity violations detected. The plan adheres strictly to the spec's constraints (CPU-only, 2-layer GCN, 6h limit) and resolves the task granularity concerns by consolidating the download/verify logic and the timeout wrapper integration into coherent, executable units in the code structure.