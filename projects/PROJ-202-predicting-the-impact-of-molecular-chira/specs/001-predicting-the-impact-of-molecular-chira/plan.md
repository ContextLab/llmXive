# Implementation Plan: Predicting the Impact of Molecular Chirality on Flavor Perception

**Branch**: `001-predict-chirality-flavor` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-molecular-chira/spec.md`

## Summary

This plan implements a CPU‑tractable computational pipeline to investigate the **associational correlation** between molecular chirality (enantiomers) and flavor perception. The system downloads a **curated subset of 5 enantiomeric pairs** and **2 olfactory receptor AlphaFold models** (filtered by pLDDT ≥ 70), performs molecular docking using AutoDock Vina, refines the top‑scoring complexes with short 100 ps OpenMM MD simulations (feasibility check), validates docking scores with SMINA and PLANTS on the **top 5 pairs**, and statistically correlates computational metrics with manually curated sensory differences. All steps are designed to run on a GitHub Actions free‑tier runner (standard CPU, standard RAM) within the 6‑hour SC‑001 limit.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `rdkit`, `autodock-vina`, `openmm`, `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `biopython`, `tqdm`  
- **Compute Target**: Linux (GitHub Actions free tier) – **CPU‑only**, no CUDA.  
- **Randomness Control**: All scripts set `numpy.random.seed(42)` and `random.seed(42)`.  
- **Scope**:  
  - **Ligands**: 5 enantiomeric pairs (10 ligands).  
  - **Receptors**: 2 AlphaFold models (pLDDT ≥ 70 in binding pocket).  
  - **Docking Jobs**: 5 pairs × 2 enantiomers × 2 receptors = 20 Vina jobs.  
  - **Robustness Scoring**: SMINA + PLANTS on the **top 5 enantiomeric pairs** (20 jobs).  
 - **MD Jobs**: 5 pairs × 2 enantiomers × 2 receptors = 20 complexes, but only the **top 10 complexes** (based on Vina score) are simulated for **100 ps** each ([deferred] total).

## Constitution Check

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **COMPLIANT** | Fixed random seeds, `requirements.txt` pins all versions, data fetched from canonical URLs, end‑to‑end pipeline runnable on fresh runner. |
| **II. Verified Accuracy** | **COMPLIANT** | All external URLs are from the verified datasets block; manual sensory ratings are sourced from peer‑reviewed literature citations. |
| **III. Data Hygiene** | **COMPLIANT** | Raw files stored under `data/raw/` with SHA‑256 checksums; every transformation writes a new file under `data/processed/`. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures and statistics are generated directly from CSVs in `data/processed/` via Jupyter notebooks; no hand‑typed numbers. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes recorded in `state/projects/...yaml`; any change updates the timestamp. |
| **VI. Computational Chemistry Methodology** | **PARTIAL** | Docking follows Principle VI exactly. MD length is reduced to **100 ps** (see Spec Deviation FR‑004). This deviation is documented and flagged as partial compliance. |
| **VII. Statistical Rigor and Reporting** | **PARTIAL** | A bootstrap procedure with a sufficiently large number of iterations is performed (satisfying the execution requirement). However, with N = 5 the interpretability is limited; thus Principle VII is marked partial. |

## Spec Deviation Annotations

| Spec Requirement | Deviation | Rationale |
|------------------|-----------|-----------|
| **FR‑001 (20 pairs)** | **Reduced to 5 pairs** | To meet the 4‑hour US‑1 docking limit on 2 CPU cores. |
| **FR‑004 (1 ns MD)** | **Deferred** – MD reduced to 100 ps for feasibility on free‑tier CI. Full 1 ns will be revisited when GPU resources are available. |
| **FR‑008 (pLDDT ≥ 70)** | **Compliant** | Receptors filtered accordingly. |
| **FR‑009 (Robustness scoring)** | **Implemented on top 5 pairs** (20 jobs) as required; broader dataset scoring would be redundant. |
| **FR‑010 (Experimental Kd cross‑reference)** | **Implemented via manual BindingDB lookup**; if no data are found, the pipeline logs and proceeds without error. |
| **FR‑007 (Sensitivity analysis)** | **Compliant** – sweep of {0.4, 0.5, 0.6} kcal/mol with per‑threshold CSV output. |
| **Principle VI (10 ns MD)** | **Partial** – see FR‑004 deviation. |
| **Principle VII (Bootstrap)** | **Partial** – bootstrap executed, but low N limits inferential strength. |

## Phase Breakdown & FR/SC Mapping

| Phase | Tasks | FR(s) Addressed | Estimated Wall‑Clock Time (CPU‑only) |
|-------|-------|------------------|--------------------------------------|
| **0. Data Acquisition** | `download.py` fetches SMILES, AlphaFold PDBs; manual sensory CSV prepared. | FR‑001, FR‑008 | 5 min |
| **1. Structure Preparation** | `prepare.py` generates 3D RDKit conformers, prepares receptors (Modeller + AMBER ff14SB). | FR‑001, FR‑002 | 10 min |
| **2. Docking** | `dock.py` runs AutoDock Vina for all 20 ligand‑receptor combos; outputs `docking_results.csv`. | FR‑001, FR‑002, FR‑003, FR‑008 | 60 min ([deferred]/job) |
| **3. Robustness Scoring** | `dock_robust.py` runs SMINA and PLANTS on the **top 5 enantiomeric pairs** (20 jobs). | FR‑009 | 60 min ([deferred]/job) |
| **4. MD Refinement (Feasibility)** | `md_sim.py` runs 100 ps OpenMM simulations on the top 10 complexes (based on Vina score). | FR‑004 (deferred), FR‑005 (stability metric) | 30 min ([deferred]/complex) |
| **5. Experimental Cross‑Reference** | `cross_ref.py` looks up BindingDB for any available Kd values; writes `experimental_comparison.csv`. | FR‑010 | 5 min |
| **6. Statistical Analysis** | `analyze.py` performs Shapiro‑Wilk, paired t‑test/Wilcoxon, Benjamini‑Hochberg FDR, Spearman correlation (or point‑biserial), 10k‑iteration bootstrap, and sensitivity sweep. | FR‑005, FR‑006, FR‑007, FR‑009 (validation), FR‑010 (cross‑ref) | 15 min |
| **7. Reporting** | Jupyter notebook generates figures & tables; `paper/` pulls directly from CSVs. | SC‑001, SC‑003, SC‑004 | 5 min |
| **Total** | **≈ 2.75 h** (165 min) – well below the 6‑hour SC‑001 ceiling with a 1.5× safety buffer. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **MD Feasibility (FR‑004)** | Required by spec; full 1 ns exceeds free‑tier limits. | Full 1 ns would break SC‑001. |
| **Robustness Scoring (FR‑009)** | Must validate with at least 3 of the top 5 pairs using SMINA/PLANTS. | Running on entire dataset would waste compute; focusing on top 5 satisfies the spec. |
| **Experimental Cross‑Reference (FR‑010)** | Provides independent validation; BindingDB is the only publicly accessible source. | Ignoring experimental data would leave FR‑010 unmet. |
| **Statistical Power (SC‑001)** | Small N is forced by compute limits; analysis framed as exploratory. | Larger N would exceed runtime budget. |
| **Bootstrap (Principle VII)** | Constitution mandates 10k bootstrap; we execute it despite low N. | Skipping bootstrap would violate the constitution. |

## Total Runtime Budget (SC‑001 Validation)

| Phase | Estimated Time (5 pairs × 2 receptors) | Constraint |
|-------|---------------------------------------|------------|
| **Data Download** | 5 min | < 1 h |
| **Structure Prep** | 10 min | < 1 h |
| **Docking (20 jobs)** | 60 min ([deferred]/job) | < 4 h (US‑1) |
| **Robustness (20 jobs)** | 60 min ([deferred]/job) | < 4 h (US‑1) |
| **MD (10 ps × 10 complexes)** | 30 min ([deferred]/complex) | < 1 h (US‑2) |
| **Cross‑Reference** | 5 min | — |
| **Statistical Analysis & Bootstrap** | 15 min | < 1 h |
| **Reporting** | 5 min | — |
| **Total** | **≈ 2.75 h** (165 min) | **< 6 h (SC‑001)** |

*All estimates assume a standard multi-core CPU configuration without GPU acceleration and include a 1.5× safety buffer.*

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Dataset reduction to 5 pairs / 2 receptors** | Guarantees completion within SC‑001 while preserving a minimal sample for exploratory analysis. |
| **MD duration reduction to 100 ps (deferred 1 ns)** | Enables a feasibility check on free‑tier hardware; full 1 ns will be pursued when resources allow. |
| **Robustness scoring limited to top 5 pairs** | Satisfies FR‑009 without unnecessary compute; avoids circular bias by focusing on the highest‑confidence predictions. |
| **Manual sensory rating curation** | FlavorDB lacks enantiomer granularity; literature provides the necessary differential ratings. |
| **Bootstrap despite low N** | Meets constitutional requirement; results are reported as exploratory with appropriate caveats. |
| **Cross‑reference via BindingDB manual lookup** | Provides an independent experimental anchor; fallback to “no data” logging preserves pipeline robustness. |