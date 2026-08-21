# Research: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Problem Statement

Can interpretable machine learning models (symbolic regression, SHAP-analyzed trees) identify structural and compositional "governing factors" that predict **Melting Point** (or **Latent Heat of Fusion** if available) for phase-change materials as effectively as black-box baselines, and do these factors generalize to independent literature data?

## Dataset Strategy

### Primary Dataset: Matbench Melting Points
- **Source**: `matbench` Python package (Open Source).
- **Dataset Name**: "matbench_melting_points".
- **Verified URL**: Not required (package-based access).
- **Target Variable**: `melting_point` (Primary). If `latent_heat` is present, it will be used as the target; otherwise, the research focuses on `melting_point`.
- **Size**: [deferred]+ compounds.
- **Access**: `from matbench import Matbench; dataset = Matbench('melting_points')`.

### Validation Dataset: Literature PCMs
- **Source**: Curated list of 50 known PCMs from NIST Webbook public tables.
- **Verified URL**: N/A (Curated artifact).
- **Strategy**: A CSV file `data/external/literature_pcms_raw.csv` is generated. If external download fails, a hardcoded fallback of 50 PCMs with known Melting Points is created to ensure the file is non-empty and checksummed.
- **Target Variable**: Must match the training target (Melting Point).

### Data Availability Risk
- **Critical**: The "Verified datasets" block contains no materials science datasets.
- **Mitigation**: Use `matbench` (open source) for training. Use a curated CSV for validation. No fabrication of URLs or data.

### Data Preprocessing
- **Imputation**: Missing elemental properties imputed from periodic table averages.
- **Exclusion**: Compounds with undefined crystal structures are excluded.
- **Checksum**: All downloaded data is checksummed and stored in `data/raw`.

## Methodology

### Feature Engineering
1. **Elemental Descriptors**: **Periodic Group**, **Period**, **Atomic Mass**, **Electronegativity**, **Atomic Radius** (mean, max, min, variance).
 - **Note**: Raw `Atomic Number` is excluded as it is a unique ID, not a predictive feature.
2. **Graph Descriptors**: Crystal graph adjacency, symmetry operations, bond density.
3. **Collinearity Check**: Identify and flag definitionally dependent features (e.g., atomic vs. ionic radius).

### Model Training
1. **Baselines**: Random Forest, Gradient Boosting (CPU-optimized).
2. **Interpretable**: PySR (symbolic regression) with a bounded time budget.
3. **Interpretability**: SHAP analysis on tree ensembles.

### Validation
1. **External**: Apply derived rules to a set of literature PCMs (using the same target variable).
2. **Sensitivity**: Sweep feature importance thresholds.
3. **Collinearity**: Adjust interpretation for joint relationships.

## Statistical Rigor

- **Multiple Comparisons**: Apply family-wise error correction if >1 test is run.
- **Power Justification**: Acknowledge power limitations if sample size is small.
- **Causal Claims**: Frame all findings as associational (observational data).
- **Measurement Validity**: Cite validation evidence for instruments (e.g., `pymatgen` graph generation).
- **Collinearity**: Report descriptive relationships for definitionally dependent features.

## Compute Feasibility

- **CPU-First**: All models (RF, GB, PySR) are CPU-tractable.
- **Memory**: Target ≤ 7 GB RAM (streaming if necessary).
- **Time**: Target ≤ 6 hours (PySR time budget: 4 hours).
- **GPU Escape Hatch**: Not required for this methodology.

## Decision/Rationale

- **Why CPU?**: Random Forest, Gradient Boosting, and PySR are CPU-tractable. No GPU needed.
- **Why `matbench`?**: It is the only verified open-source dataset with melting points for >5,000 compounds.
- **Why No Proxy?**: We do NOT use Melting Point as a proxy for Latent Heat. We predict the variable that is actually available.
- **Why External Validation?**: Required by Constitution Principle VII to confirm generalization.

## References

- **Matbench**: ` (Open source library).
- **Matbench Melting Points**: Dataset within `matbench` package.
- **NIST Webbook**: Public tables for validation set curation.
- **PySR**: ` (Standard library).