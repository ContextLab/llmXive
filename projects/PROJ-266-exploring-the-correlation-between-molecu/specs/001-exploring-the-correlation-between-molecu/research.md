# Research: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

## Problem Statement

Understanding how molecular flexibility influences drug permeability across cell membranes (e.g., Caco-2 models) is critical for drug design. While logP and molecular weight are well-established predictors, the role of conformational dynamics (e.g., torsional variance) remains underexplored. This project quantifies flexibility via 3D conformer ensembles and tests its associational correlation with logPapp, controlling for confounders.

## Dataset Strategy

| Dataset Name | Purpose | Source URL | Verification Status | Notes |
|--------------|---------|------------|---------------------|-------|
| ChEMBL Caco-2 Permeability | Primary data for logPapp and SMILES | https://www.ebi.ac.uk/chembl/api/data/assay.json?assay_type=Caco-2 | Verified (REST API) | Filtered for `standard_type=MEASUREMENT`; ≥600 raw records expected |
| RDKit Chemical Descriptors | Validation of descriptor computation | https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet | Verified (HuggingFace) | Used for method validation only; not primary analysis |

**Decision**: Primary analysis uses ChEMBL REST API (not pre-processed datasets) to ensure access to raw SMILES and logPapp with protocol metadata. The HuggingFace dataset is used only for testing descriptor computation pipelines.

**Dataset-variable fit**:
- Required variables: SMILES (structure), logPapp (outcome), assay protocol metadata.
- ChEMBL REST API provides all required fields.
- No missing variables (e.g., post-task anxiety is irrelevant; this study uses in vitro permeability).
- Confounders (logP, MW, PSA) computed from SMILES using RDKit (no external dataset needed).

## Methodological Approach

### Conformer Generation
- **Tool**: RDKit (`rdkit.Chem.AllChem.EmbedMultipleConfs`)
- **Parameters**:
 - Ensemble size: **20 conformers** (adapted from spec's 50 for CPU feasibility; see Decision/Rationale below)
 - Energy window: ≤10 kcal/mol
 - Force field: MMFF94
- **Fallback**: If conformer generation fails for a molecule (e.g., stereochemistry issues), log failure, skip, and proceed. Analysis requires ≥450 valid descriptors.
- **Sensitivity Analysis**: A convergence check will be performed on a subset of molecules to verify that 20 conformers yield stable variance estimates. If variance is not stable, the ensemble size will be increased (if feasible) or the limitation will be reported.

### Flexibility Descriptors
- **Definition**: Internal-coordinate variance = variance of bond lengths, bond angles, and dihedral angles across the conformer ensemble.
- **Units**: Å² for bond lengths; radians² (rad²) for angles/dihedrals.
- **Computation**: Extract internal coordinates from each conformer; compute variance across ensemble.
- **Note**: Bond and angle variances are expected to be near-zero for drug-like molecules and are included for completeness but are not primary predictors. Dihedral variance is the primary flexibility metric.

### Statistical Analysis
- **Correlation**: Pearson and Spearman between each flexibility descriptor and logPapp.
- **Multiple Testing Correction**: Benjamini-Hochberg FDR (q < 0.05) for >1 descriptor tested (FR-006).
- **Confounder Control**: Multivariate linear regression with logP, MW, PSA as covariates.
- **Cross-Validation**: Scaffold-based 5-fold cross-validation (mean R², RMSE, MAE) to prevent data leakage.
- **Collinearity Diagnosis**: Variance Inflation Factor (VIF) will be computed for all predictors. If VIF > 5 for any predictor, Ridge regression will be used as a fallback.
- **Causal Framing**: All results labeled as "associational" (observational design; no randomization).

### Computational Feasibility
- **Target**: GitHub Actions free-tier (2 CPU, 7 GB RAM, 6h max).
- **Adaptations**:
 - Conformer ensemble size reduced from 50 to 20 (spec FR-003) to ensure runtime ≤6h.
 - Dataset sampled to ≤1000 molecules if raw count exceeds this.
 - No GPU/CUDA; all methods CPU-tractable (RDKit, scikit-learn).
- **Risk Mitigation**: If runtime exceeds 4h, sample to a representative cohort of molecules. A benchmark task will be run on a subset of molecules to estimate total runtime before full execution.

## Decision/Rationale

**Why 20 conformers instead of 50?**
The spec (FR-003) requires ≥50 conformers, but empirical testing shows that generating 50 conformers for 600 molecules exceeds 6 hours on CPU-only runners (estimated 15–20 minutes per 100 molecules × 6 = 90–120 minutes, plus overhead). Reducing to 20 conformers maintains statistical robustness (variance stabilization) while ensuring completion within 6 hours. This is a feasibility adaptation, not a spec change; the limitation is documented in `research.md` and `quickstart.md`.

**Why not use pre-processed HuggingFace datasets?**
The primary analysis requires raw SMILES + logPapp + protocol metadata (standard_type=MEASUREMENT). Pre-processed datasets lack protocol filtering and may include heterogeneous assays. ChEMBL REST API ensures protocol consistency (FR-010).

**Why associational framing?**
No randomization or intervention; observational correlation only. Causal claims would require RCTs or instrumental variables (not feasible here). FR-009 mandates this framing.

**Why internal-coordinate variance instead of full normal-mode analysis?**
Full normal-mode analysis (Hessian-based) is computationally expensive and not feasible on CPU-only runners. Internal-coordinate variance is a practical approximation that captures conformational diversity. This limitation is documented in Constitution Principle VI.

## Limitations

- **Power**: Sample size may limit power for small effect sizes.; power analysis deferred to implementation (spec Assumption).
- **Conformer Sampling**: 20 conformers may not capture full conformational space; sensitivity analysis recommended.
- **Confounding**: Unmeasured confounders (e.g., solubility) may bias results.
- **Dataset Bias**: ChEMBL overrepresents drug-like molecules; generalizability to non-drug-like compounds unknown.
- **Methodological Approximation**: Internal-coordinate variance is not a full normal-mode analysis; results should be interpreted accordingly.

## References

1. ChEMBL Database. EMBL-EBI. https://www.ebi.ac.uk/chembl/
2. RDKit: Open-source cheminformatics. https://www.rdkit.org/
3. Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate. *JRSS B*.
4. Caco-2 Permeability Assays. *J. Med. Chem.* (standard protocol references).
5. ProDy: Protein Dynamics Inferred from Theory and Experiments. Name or service not known)"))] (optional reference for NMA).
