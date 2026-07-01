# Research: Predicting the Impact of Molecular Chirality on Flavor Perception

## Overview

This research phase defines the dataset strategy, methodological approach, and computational constraints for assessing the associational correlation between stereoselective binding and flavor perception. The study explicitly controls for confounding variables (molecular size, hydrophobicity) and acknowledges statistical power limitations.

## Dataset Strategy

| Dataset | Purpose | Verified URL / Source | Loading Method | Notes |
|---------|---------|----------------------|----------------|-------|
| Curated Chiral Pairs | Ligand structures & Sensory ratings | `data/raw/curated_chiral_pairs.csv` (Manually curated from literature: Carvone, Limonene, etc.) | `pandas.read_csv()` | Contains pairs with known sensory differences. Verified against primary literature. |
| AlphaFold Receptors | Protein structures | ` (Direct PDB download) | `requests` | Extract PDBs; filter by pLDDT ≥70 in **pre-defined** orthosteric pocket. |
| Sensory Ratings | FlavorDB/ChEMBL correlation | Included in `curated_chiral_pairs.csv` | `pandas.read_csv()` | Fallback: If coverage <50%, switch to ChEMBL 33 query (see FR-011). |
| PDB Complexes (validation) | Docking validation | ` | `pandas.read_parquet()` | Used for SMINA/PLANTS validation (FR-009). |

**Dataset Coverage Gap**: FlavorDB sensory ratings are not in the verified dataset list. Per FR-011, if coverage <50%, the system will switch to a curated ChEMBL set. The fallback set is derived from **ChEMBL 33** using a specific query script (`code/01_fallback_chembl.py`) which is versioned and checksummed.

## Methodological Approach

### Phase 0.5: Fallback Data Strategy (FR-011)
- Check coverage of sensory ratings in `curated_chiral_pairs.csv`.
- If <50%, execute `01_fallback_chembl.py` to query ChEMBL 33 for chiral pairs with sensory annotations.
- Output: `data/raw/chembl_chiral_pairs.csv` with checksum.

### Phase 1: Data Download & Preparation (FR-001, FR-008)
- Download SMILES and AlphaFold PDBs.
- **Pocket Definition**: Use a **pre-defined orthosteric pocket** based on homology to OR51E2 (residues within 6.0 Å of a reference ligand), NOT post-docking COM.
- Filter receptors: keep only those with pLDDT ≥70 in the pre-defined pocket.
- Use RDKit to generate 3D conformers for enantiomers (mirror image generation).
- Limit to ≤20 enantiomeric pairs and ≤5 receptors.

### Phase 2: Molecular Docking (FR-002, FR-003, FR-009)
- Use AutoDock Vina in CPU-only mode (no CUDA flags).
- Dock each enantiomer against each receptor.
- Output: CSV with binding affinity (kcal/mol), RMSD, receptor ID, ligand ID.
- **Threshold**: The 0.5 kcal/mol threshold is a **screening heuristic** (acknowledging Vina RMSE ~2.0-2.5 kcal/mol). Primary analysis uses continuous Δaffinity.
- **Validation**: Run SMINA and PLANTS on top 5 pairs (FR-009) using `07_validation_docking.py`.

### Phase 3: MD Refinement & Interaction Fingerprinting (FR-004)
- Select top 10 complexes (by docking score).
- Run **1ns MD** with OpenMM, **implicit solvent (GBSA)**, 2 CPU cores.
- **Justification**: 10ns/TIP3P is infeasible on CI. This step serves as a "stability screen" to filter grossly unstable poses, not to converge free energies.
- Extract interaction fingerprints (H-bonds, hydrophobic contacts) via MDAnalysis.
- Output: Trajectory files + summary CSV of interaction frequencies.

### Phase 4: Statistical Analysis (FR-005, FR-006, FR-007, FR-010)
- **Confounding Control**: Include molecular descriptors (MW, LogP) as covariates in a partial correlation or multiple regression model.
- **Primary Test**: Paired Wilcoxon signed-rank test on enantiomeric docking scores.
- **Correlation**: Spearman correlation between binding differences and sensory ratings, controlling for covariates.
- **Multiple Comparisons**: Apply Benjamini-Hochberg FDR correction for >5 tests.
- **Sensitivity Analysis**: Sweep threshold ∈ {0.4, 0.5, 0.6} kcal/mol; output `sensitivity_analysis.csv` (FR-007).
- **Power Mitigation**: If Wilcoxon is underpowered (n<20), switch to **Bayesian Hierarchical Model** (weakly informative priors) to estimate effect size distribution.
- **Success Metric**: Check if |ρ| > 0.3 and report status.

## Computational Constraints

- **Runtime**: ≤6 hours total (2h Docking + 3h MD + 1h Analysis).
- **Memory**: ≤7 GB RAM peak (especially during MD).
- **CPU**: 2 cores only; no GPU/CUDA.
- **Dataset Size**: ≤20 pairs, ≤5 receptors to ensure feasibility.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: FDR correction applied for >5 tests.
- **Power Justification**: Sample size n≤20 is underpowered for |ρ|>0.3 (Power <0.30). **Mitigation**: Report effect sizes with 95% CIs; use Bayesian fallback if frequentist test fails. Non-significant results are valid outcomes.
- **Causal Framing**: Observational design; correlations framed as **associational**, not causal.
- **Measurement Validity**: Receptors filtered by pLDDT ≥70 in **pre-defined** pocket.
- **Collinearity**: Enantiomers are definitionally related; no claim of independent effects.
- **Scoring Function Noise**: Acknowledge that 0.5 kcal/mol threshold is within Vina's error margin; rely on sensitivity analysis and continuous metrics.

## Risk Mitigation

- **Docking Failure**: Log errors; assign null scores; exclude from mean.
- **Missing Sensory Data**: Exclude pair from correlation; retain docking results.
- **Low pLDDT**: Flag for manual review or exclude based on threshold.
- **Runtime Overrun**: Sample fewer pairs/receptors if needed; log adaptation.
- **MD Instability**: If 1ns GBSA shows high RMSD, flag complex as "unstable" and exclude from correlation.
