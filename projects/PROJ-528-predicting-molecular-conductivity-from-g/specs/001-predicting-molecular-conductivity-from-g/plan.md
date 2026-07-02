# Implementation Plan: Predicting Molecular Conductivity from Graph-Based Features

**Branch**: `001-predict-molecular-conductivity` | **Date**: 2026-06-24 | **Spec**: `spec.md`

## Summary

This project implements a predictive modeling pipeline to investigate whether graph-based topological descriptors (e.g., conjugation length, aromaticity indices) correlate with molecular electronic properties. The approach involves parsing SMILES strings, computing multiple RDKit-based descriptors, filtering for valid target variables, and training Random Forest and Gradient Boosting regressors. 

**Critical Scope Adjustment**: Per verified dataset constraints, if direct conductivity (charge carrier mobility) data is unavailable, the target variable will be the HOMO-LUMO gap. In this case, the research question is reframed to "Predicting Electronic Delocalization Potential (HOMO-LUMO Gap) from Graph Features." All claims will be framed as predicting electronic structure, not charge transport, to avoid construct validity failure.

The plan strictly adheres to CPU-only constraints, implements scaffold splitting to prevent data leakage, and includes rigorous statistical controls (VIF, Benjamini-Hochberg) and sensitivity analyses for outliers as mandated by the specification.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: 
- Intermediate files: CSV/Parquet (`data/processed/descriptors.csv`, etc.) for efficiency.
- Final contract outputs: JSON (`data/processed/model_results.json`, etc.) as defined in `contracts/`.
**Testing**: `pytest` with unit tests for descriptor computation and integration tests for the full pipeline  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM)  
**Project Type**: Data Science / Computational Chemistry Pipeline  
**Performance Goals**: Complete full analysis (data load -> model eval -> plots) within 6 hours on 2-core CPU.  
**Constraints**: No GPU/CUDA; no quantum mechanical calculations (DFT) unless available in verified dataset (fallback to topological proxies); strict memory limits (<7 GB).  
**Scale/Scope**: Target dataset size up to 5,000 molecules; ~20 features per molecule.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `constitution.md`*

1.  **Reproducibility (I)**: The plan mandates pinned `requirements.txt`, fixed random seeds in all training/splitting steps, and checksums for all raw data artifacts.
2.  **Verified Accuracy (II)**: All dataset URLs are restricted to the "Verified datasets" block in the input. The HuggingFace URLs listed have been verified by the Reference-Validator Agent (as per input block status) and meet the title-token-overlap threshold (≥ 0.7).
3.  **Data Hygiene (III)**: The pipeline separates `data/raw` (immutable, checksummed) from `data/processed` (derived). No in-place modifications.
4.  **Single Source of Truth (IV)**: All output metrics (R², MAE, feature importance) are generated strictly by scripts in `code/` and logged to JSON/CSV, never hand-typed.
5.  **Versioning Discipline (V)**: Artifacts will carry content hashes; the plan includes steps to update the project state file upon completion.
6.  **Graph Descriptor Transparency (VI)**: Descriptors are computed via `rdkit` (version pinned). The code includes unit tests verifying specific SMILES inputs against expected descriptor values.
7.  **Dataset Provenance and Integrity (VII)**: The plan explicitly selects sources from the verified list (HuggingFace). While the constitution prefers Materials Project/PubChem, the "Verified datasets" input block for this project stage authorizes these HuggingFace sources as the primary data provenance.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-conductivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 0 output (generated/validated)
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── descriptors.py       # RDKit descriptor computation logic
├── data_loader.py       # Dataset fetching and cleaning
├── model_training.py    # Scaffold split, RF, GB training, CV, Retraining loops
├── analysis.py          # VIF, feature importance, sensitivity analysis, BH correction
├── plotting.py          # Correlation plots with CI
└── main.py              # Orchestrator
tests/
├── test_descriptors.py  # Unit tests for RDKit logic
├── test_scaffold_split.py
└── test_analysis.py
data/
├── raw/                 # Downloaded parquet/zip files
└── processed/           # Cleaned CSVs with descriptors, JSON results
```

**Structure Decision**: Single `code/` directory structure selected. This minimizes complexity for a data pipeline and aligns with the CPU-only, script-based execution model. No separate frontend/backend is required.

## Implementation Phases

### Phase 0: Contract Generation & Validation
- Generate/validate `contracts/*.schema.yaml` files.
- Ensure schemas are valid YAML and match the data model.

### Phase 1: Data Ingestion & Validation
- Download verified datasets from HuggingFace.
- **Target Variable Check**: Verify presence of conductivity or HOMO-LUMO gap.
  - If neither exists: **HALT** with error "No verified dataset found with required target variable."
  - If only HOMO-LUMO gap exists: **LOG WARNING** and reframe target to "Electronic Delocalization Potential."
- Validate SMILES strings (RDKit).
- Log missing conductivity values and exclude them (FR-012).

### Phase 2: Descriptor Computation & Fallback
- Compute graph-based descriptors (FR-001, FR-008).
- **Quantum Fallback Check**:
  - If quantum-derived descriptors (e.g., HOMO-LUMO gap) are missing from the dataset:
    - **LOG WARNING**: "Quantum descriptors missing; falling back to topological proxies."
    - Use topological conjugation length as proxy.
  - If both quantum and topological proxies fail for a molecule: **EXCLUDE** molecule.

### Phase 3: Preprocessing & Distribution Check
- Check target variable distribution.
  - If log-normal or >3 orders of magnitude: Apply log-transformation.
  - Else: Use raw values and log distributional properties.
- **Correlation Pre-check**: Compute correlation between topological descriptors and target.
  - If correlation is weak (e.g., |r| < 0.3): Log warning "Topological proxy hypothesis unsupported by weak correlation."

### Phase 4: Model Training & VIF Filtering (FR-013)
- **Iterative VIF Loop**:
  1. Calculate VIF for all predictors.
  2. If any feature has VIF > 10:
     - Exclude feature.
     - **RETRAIN** model on reduced feature set.
     - Repeat until all VIF ≤ 10.
  3. Final model trained on reduced set.
- Train Random Forest and Gradient Boosting (FR-003).
- Apply scaffold splitting (FR-002).

### Phase 5: Sensitivity Analysis (FR-007)
- **Retrain Loop**: For each outlier threshold in {2.5σ, 3.0σ, 3.5σ}:
  - Filter data.
  - Retrain models.
  - Record R² scores.
- **Statistical Test**: Perform ANOVA or Kruskal-Wallis on R² scores across thresholds to determine if variance is significant.

### Phase 6: Analysis & Reporting (FR-006, FR-014)
- Compute feature importance (FR-005).
- Calculate feature-conductivity correlations.
- **Benjamini-Hochberg Correction**: Apply FDR correction to p-values (FR-006).
- Generate plots with 95% CI (FR-005).
- Write final results to JSON (model_output_schema.yaml).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Scaffold Splitting | Required by FR-002 to prevent data leakage from structurally similar molecules. | Random splitting would lead to over-optimistic R² scores due to molecular similarity in train/test sets. |
| VIF Filtering & Retraining | Required by FR-013 to ensure statistical independence of features. | Including collinear features would inflate importance scores and violate SC-007/SC-008. |
| Sensitivity Analysis (Retraining) | Required by FR-007 to test robustness against outliers. | A single threshold or post-hoc analysis would not measure how model performance *varies* across cutoffs. |
| Benjamini-Hochberg | Required by FR-006 for multiple comparison correction. | Standard p-values would result in inflated Type I errors when testing multiple feature-conductivity correlations. |
| Target Variable Reframing | Required by data constraints (no verified conductivity). | Using HOMO-LUMO gap as a proxy for conductivity without distinction would be scientifically invalid (construct validity). |