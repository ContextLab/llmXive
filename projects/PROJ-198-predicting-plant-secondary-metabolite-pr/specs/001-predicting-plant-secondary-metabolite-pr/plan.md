# Implementation Plan: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Branch**: `001-predict-plant-metabolite-profiles` | **Date**: 2026-07-03 | **Spec**: `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`
**Input**: Feature specification from `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`

## Summary

This feature implements a computational pipeline to quantify the extent to which biosynthetic gene cluster (BGC) diversity explains variation in quantitative secondary metabolite profiles across plant species. The approach involves downloading genomic assemblies and metabolite tables, predicting BGCs using antiSMASH, aligning the data, and training regression models (Random Forest, Elastic Net, Gradient Boosting, PGLS) with phylogenetic stratification and permutation baselines. The analysis focuses on *quantitative* prediction (abundance vs. copy number) to avoid tautological results from qualitative presence/absence matching.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`, `pymc3` (for PGLS via `statsmodels` custom covariance), `tqdm`, `pydantic`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM)  
**Project Type**: Computational Biology Pipeline / CLI  
**Performance Goals**: Complete data alignment and model training for N=5 (test) and N≥20 (full) within 6 hours on CPU-only infrastructure.  
**Constraints**: No GPU; antiSMASH must run via command-line wrapper. Data subsets to fit 7GB RAM. Genome assemblies > 500MB are skipped to ensure feasibility.  
**Scale/Scope**: Initial dataset a moderate number of matched species; features hundreds of BGC types; targets a broad panel of metabolites. Dimensionality reduction (PCA) applied before multivariate modeling.

> **Note on Compute Feasibility**: The spec mentions "antiSMASH 7.0". Running full antiSMASH on a GitHub Actions runner (limited vCPU, 7GB RAM) for multiple species may exceed the 6-hour limit or 7GB RAM. The plan explicitly commits to a single tool (antiSMASH) for consistency. If antiSMASH fails for a species (timeout or OOM), that species is excluded from the final analysis rather than switching tools, preventing confounding. A strict genome size filter (>500MB skip) is implemented to ensure the pipeline completes within 6 hours.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned dependencies (`requirements.txt`), random seeds in all modeling steps, and explicit data fetching from canonical sources (NCBI, PMDB) in `code/`.
- **II. Verified Accuracy**: All citations in `research.md` and `plan.md` will be validated against the "Verified datasets" block by the Reference-Validator Agent at artifact write, advancement, and transition gates. No URLs will be invented.
- **III. Data Hygiene**: Raw data downloaded to `data/raw` will be checksummed. Intermediate files (aligned matrices) will be written to `data/processed` with derivation logs. No in-place modification. Runtime schema enforcement via Pydantic models ensures data integrity.
- **IV. Single Source of Truth**: All model metrics (R², p-values) in the final report will be generated programmatically from `code/` and stored in `data/processed/metrics.json`.
- **V. Versioning**: Content hashes for all data artifacts will be recorded in the project state file: `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml`.
- **VI. Genotype-Phenotype Gap**: The plan explicitly includes FR-006 (Phylogenetic Permutation) and FR-010 (PGLS) to quantify the gap.
- **VII. Computational Baseline**: The plan includes a baseline permutation test (FR-006) to validate against overfitting.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-plant-secondary-metabolite-profiles/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── feature_matrix.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration and constants
├── data/
│   ├── __init__.py
│   ├── download.py      # FR-001, FR-003 (NCBI, PMDB)
│   ├── preprocess.py    # FR-002, FR-003, FR-009 (antiSMASH wrapper, InChIKey, Pfam fallback)
│   └── align.py         # FR-004 (Matrix alignment, Pydantic validation)
├── modeling/
│   ├── __init__.py
│   ├── train.py         # FR-005, FR-010 (RF, Elastic Net, Gradient Boosting, PGLS)
│   ├── eval.py          # FR-006, FR-007 (LOO CV, Permutation, Sensitivity)
│   └── phylo.py         # PGLS specific logic (statsmodels + dendropy)
├── utils/
│   ├── __init__.py
│   └── logging.py
├── cli/
│   └── main.py          # Entry point
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision**: Single `code/` directory with modular sub-packages for data, modeling, and utilities. This structure supports the linear pipeline flow (Download -> Process -> Align -> Model -> Evaluate) while keeping logic separated for testing. Pydantic models will be used to enforce `contracts/` schemas at runtime.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Phylogenetic Permutation Baseline** | Required by FR-006 and Constitution Principle VII to distinguish signal from phylogenetic artifacts. | Standard random permutation ignores evolutionary relatedness, leading to inflated Type I error rates in cross-species data. |
| **PGLS Model** | Required by FR-010 to account for non-independence of species data. | Standard OLS assumes independence; using OLS would violate statistical assumptions for comparative biology. |
| **antiSMASH Integration** | Required by FR-002 for accurate BGC prediction. | Simple k-mer frequency or gene-count proxies lack the specificity to map to metabolite classes (MIBiG/Pfam ontology). |
| **Dimensionality Reduction (PCA)** | Required due to N < 50 vs. high-feature count to prevent overfitting. | Direct multivariate regression with N < 50 and >100 features is statistically unstable. |
| **Leave-One-Out (LOO) CV** | Required due to small sample size (N < 20) where 5-fold CV yields test sets < 4. | 5-fold CV R² estimates are unstable with N < 20; LOO provides a more robust estimate for small N. |

## Methodological Rigor & Success Criteria

- **FR-005 (Gradient Boosting)**: Implemented via `scikit-learn`'s `GradientBoostingRegressor` (CPU-optimized).
- **FR-007 (Sensitivity Analysis)**: Explicitly sweeps thresholds across a range of values and records R² variation. SC-002 (variation ≤ 0.05) is validated in `modeling/eval.py`.
- **FR-009 (Ontology Mapping)**: Uses MIBiG for bacterial-like clusters; falls back to Pfam HMMs for plant-specific clusters (e.g., Terpene Synthases) to reduce 'unknown' rate.
- **Quantitative Prediction**: The model predicts *log-transformed abundance* (continuous) from *BGC copy number* (continuous), not presence/absence, to avoid tautology.
- **Null Model**: Phylogenetic permutation that shuffles both predictors and targets simultaneously or uses phylogenetic eigenvector regression to account for co-evolution.

## Compute Feasibility

- **Constraint**: 2 CPU, 7 GB RAM, 6 hours.
- **Mitigation**:
    1.  **Genome Size Filter**: Skip species with genome > 500MB to prevent antiSMASH timeout.
    2.  **Single Tool Commit**: Use antiSMASH only. If it fails, exclude species (do not switch tools).
    3.  **Dimensionality Reduction**: Apply PCA to BGC features before PGLS to reduce model complexity.
    4.  **LOO CV**: Use LOO instead of 5-fold CV to maximize data usage with small N.
    5.  **Library Pins**: Use `scikit-learn`, `statsmodels`, `dendropy` (CPU only). Avoid GPU-specific torch versions.