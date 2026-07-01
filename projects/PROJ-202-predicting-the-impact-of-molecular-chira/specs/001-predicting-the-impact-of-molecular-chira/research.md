# Research: Predicting the Impact of Molecular Chirality on Flavor Perception

## Executive Summary

This research plan outlines a CPU‑tractable computational workflow to investigate the **associational correlation** between molecular chirality (enantiomers) and flavor perception. By docking enantiomeric pairs of aroma molecules into olfactory receptor models and correlating binding affinity differences with manually curated sensory differences, we aim to establish a baseline for stereoselective binding. All conclusions are framed as **observational and exploratory** due to limited sample size and model uncertainty.

## Dataset Strategy

The project relies exclusively on **verified datasets** (no invented sources). Where a verified URL does not provide the required granularity, we supplement with **manual curation** from peer‑reviewed literature.

| Data Type | Description | Source URL | Usage |
|-----------|-------------|------------|-------|
| **SMILES (Ligands)** | Aroma molecule SMILES strings (curated subset) | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Source for a set of enantiomeric pairs (selected for known distinct sensory profiles). |
| **AlphaFold Receptor Models** | Predicted structures of olfactory receptors | `https://huggingface.co/datasets/nferruz/dataset_alphafold/resolve/main/natural_alphafold.tar.gz` | Filtered by pLDDT ≥ 70 in the binding pocket (FR‑008). |
| **Manual Sensory Ratings** | Enantiomer‑specific intensity/pleasantness values extracted from primary literature (e.g., R‑Carvone vs L‑Carvone). | `data/manual_enantiomer_ratings.csv` (curated locally) | Provides the `sensory_rating_R` and `sensory_rating_L` columns needed for correlation. |
| **Experimental Binding Constants** | Reported Kd or Ki values for odorant‑receptor pairs (when available). | Manual lookup in **BindingDB** (`https://www.bindingdb.org/`) – not a verified URL, so we treat it as an optional fallback. | Used for FR‑010 cross‑reference; if none are found, the step logs “No experimental data”. |

**FlavorDB Note**: No verified API or enantiomer‑specific dataset is available. Consequently, we do **not** rely on FlavorDB for quantitative sensory differences; instead, we use the manually curated CSV. If a given pair lacks literature‑derived ratings, it is **excluded** from the correlation analysis but retained in docking and MD outputs.

## Methodology & Statistical Rigor

### 1. Data Selection & Preparation (US‑1)
- **Ligand Curation**: From the SMILES dataset we select 5 enantiomeric pairs with documented distinct sensory profiles (e.g., (R)-Carvone vs (S)-Carvone). The IDs and SMILES are recorded in `data/processed/enantiomer_pairs.csv`.
- **Receptor Filtering**: AlphaFold models are parsed; any model with pLDDT < 70 in the binding pocket is discarded (FR‑008). Two high‑confidence receptors are retained.
- **3D Conformer Generation**: RDKit creates three low‑energy conformers per enantiomer; the lowest‑energy conformer is used for docking.

### 2. Molecular Docking (US‑1)
- **Tool**: AutoDock Vina (CPU binary, no GPU flags).  
- **Grid Definition**: Centered on the binding pocket residues identified from the AlphaFold model.  
- **Execution**: 20 ligand‑receptor jobs (5 pairs × 2 enantiomers × 2 receptors).  
- **Outputs**: `data/processed/docking_results.csv` containing Vina scores, RMSD, and timestamps. Pairs with ΔAffinity > 0.5 kcal/mol are flagged (FR‑003).

### 3. Robustness Scoring (FR‑009)
- **Scope**: The **top 5 enantiomeric pairs** (based on Vina affinity) are rescored with **SMINA** and **PLANTS** (CPU‑only). This yields 20 additional scoring jobs (5 pairs × 2 enantiomers × 2 receptors).  
- **Goal**: Demonstrate agreement across three scoring functions for the most promising complexes, satisfying FR‑009 without biasing the entire dataset.

### 4. MD Refinement (US‑2, FR‑004 Deferred)
- **Selection**: The 10 best complexes (5 pairs × 2 enantiomers) from the Vina results are simulated for **100 ps** each using OpenMM (TIP3P water, AMBER ff14SB).  
- **Rationale**: 100 ps is a **feasibility probe**; it provides local stability metrics (average RMSD, interaction fingerprints) while respecting the 1‑hour US‑2 limit. Full 1 ns MD is **deferred** pending GPU resources (see Spec Deviation).  
- **Outputs**: `data/processed/md_summary.csv` with average RMSD, H‑bond counts, and hydrophobic contacts.

### 5. Experimental Cross‑Reference (FR‑010)
- **Procedure**: `cross_ref.py` queries BindingDB for any reported Kd/Ki values matching our ligand‑receptor pairs. Results are stored in `data/processed/experimental_comparison.csv`. If no match is found, the script logs the absence and continues; the pipeline does not fail.

### 6. Statistical Analysis (US‑3)
- **Normality**: Shapiro‑Wilk test on ΔAffinity values.  
- **Paired Test**: If p > 0.05 → paired t‑test; else → paired Wilcoxon signed‑rank test (FR‑005).  
- **Multiple Comparisons**: Benjamini‑Hochberg FDR correction applied when >5 receptor‑ligand pairs are tested (FR‑006).  
- **Correlation**:  
  - When both `sensory_rating_R` and `sensory_rating_L` are present → Spearman’s ρ between ΔAffinity and ΔRating.  
  - If only a binary `distinct_profile_flag` is available → point‑biserial correlation.  
- **Bootstrap**: 10,000 resampling iterations produce 95 % confidence intervals for effect sizes (Constitution Principle VII).  
- **Sensitivity Sweep (FR‑007)**: Thresholds {0.4, 0.5, 0.6} kcal/mol are evaluated; for each threshold the number of significant ΔAffinity pairs (adjusted p < 0.05) is recorded in `statistical_analysis.csv`.  
- **Output Schema**: Conforms to `contracts/statistical_analysis.schema.yaml`.

### 7. Causal Inference & Limitations
- **Observational Design**: No randomization of molecules or receptors; all claims are **associational**.  
- **Statistical Power**: N = 5 pairs yields low power; non‑significant results are reported as inconclusive rather than evidence of no effect.  
- **Model Uncertainty**: AlphaFold pLDDT values, even when ≥ 70, can introduce errors larger than the 0.5 kcal/mol signal; this is explicitly discussed.  
- **MD Shortness**: 100 ps provides only a local stability check; it is not a rigorous conformational validation.  
- **Experimental Ground Truth**: BindingDB coverage for odorant‑receptor pairs is sparse; absence of data is logged and does not invalidate the pipeline.

## Compute Feasibility & Constraints

- **Hardware**: GitHub Actions free tier (2 CPU cores, 7 GB RAM).  
- **Memory**: Peak usage < 4 GB during MD; well within the 7 GB limit.  
- **Runtime**: Detailed budget (see `plan.md`) totals **≈ 2.75 h**, comfortably below the 6‑hour SC‑001 ceiling.  
- **No GPU**: All tools forced to CPU mode (`--cpu`, `device='CPU'`).  

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Dataset reduction** | Guarantees runtime compliance while preserving a minimal exploratory sample. |
| **MD feasibility reduction** | Enables MD on free‑tier CI; full 1 ns is deferred for future GPU runs. |
| **Robustness scoring on top 5** | Meets FR‑009 without excessive compute; avoids post‑hoc bias. |
| **Manual sensory curation** | Compensates for the lack of enantiomer‑specific FlavorDB data. |
| **Bootstrap despite low N** | Satisfies constitutional requirement; results are labeled exploratory. |
| **BindingDB fallback** | Provides an optional experimental anchor; pipeline remains robust if no data are found. |