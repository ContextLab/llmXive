# Implementation Plan: Predicting Plant Secondary Metabolite Profiles from Publicly Available Genomic Data

**Branch**: `001-predict-plant-metabolite-profiles` | **Date**: 2026-10-18 | **Spec**: `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`  
**Input**: Feature specification from `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`

## Summary
Implement a reproducible end‑to‑end pipeline that (1) downloads plant genome assemblies and quantitative metabolite abundance tables, (2) runs antiSMASH 7.0 to predict biosynthetic gene clusters (BGCs) and maps them to MIBiG 3.0 classes, (3) aligns BGC feature matrices with log‑transformed metabolite abundances, (4) trains regression models (Random Forest, Elastic Net, Gradient Boosting, Phylogenetic Generalized Least Squares) with phylogenetically‑stratified cross‑validation, (5) evaluates performance against a phylogenetic permutation baseline, (6) conducts a sensitivity sweep over BGC detection confidence thresholds, and (7) validates all major artifacts against JSON schemas. All steps are constrained to the GitHub Actions free‑tier (2 CPU, 7 GB RAM, ≤ 6 h) and are fully validated against contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`, `tqdm`, `pydantic`, `docker` (for antiSMASH)  
- **Storage**: Local filesystem under `data/` (raw, intermediate, processed)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only)  
- **Constraints**: No GPU; genomes > 500 MB are skipped; total wall‑clock ≤ 6 h  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed `requirements.txt`, pinned random seeds, deterministic download URLs, Dockerized antiSMASH, schema‑validated artifacts. |
| II. Verified Accuracy | All citations (antiSMASH, MIBiG, NCBI RefSeq, KNApSAcK) will be validated by the Reference‑Validator; no un‑verified URLs are introduced. |
| III. Data Hygiene | Checksums recorded for every raw and derived file; transformations write new files; no in‑place edits. |
| IV. Single Source of Truth | `data/processed/model_metrics.json` is the sole source for all reported statistics and is validated against `contracts/model_output.schema.yaml`. |
| V. Versioning Discipline | Content hashes stored in the project state file after each stage; any change updates the timestamp. |
| VI. Genotype‑Phenotype Gap Quantification | FR‑006 & FR‑010 compute R² and Pearson r on a hold‑out set; PGLS accounts for phylogeny per Principle VI. |
| VII. Computational Baseline Validation | Phylogenetic permutation baseline (FR‑006) plus block‑permutation baseline provide robust null models per Principle VII. |

## Power Analysis
Formal power calculations are infeasible given the expected N < 20 and high‑dimensional BGC feature space. Instead, we will report:
- Effect sizes (R²) with 95 % bootstrap confidence intervals (1000 resamples).
- Acknowledgement that the study is exploratory and may be under‑powered to detect modest effects.

## Construct Validity
BGC presence/count serves as a proxy for biosynthetic potential. We acknowledge that expression levels, regulatory mechanisms, and environmental conditions also influence metabolite abundance, which are not captured here. Consequently, all conclusions are framed as **associational** rather than causal, in line with Constitution Principle VI.

## Non‑phylogenetic Confounds
When metadata are available, we will include ecological niche, tissue type, and experimental batch as covariates in the regression models. Sensitivity analyses will test model robustness to the inclusion/exclusion of these covariates.

## Methodological Rigor (Addressed in Research.md)
- Observational design → no causal claims.
- Multiple‑comparison correction (Bonferroni/FDR) for multiple metabolites.
- Power acknowledgement (exploratory with N < 20).
- Collinearity diagnostics (VIF) reported but biologically relevant predictors retained.
- Dimensionality reduction (PCA) when `#features > N/2`.
- Phylogenetic permutation baseline *and* block‑permutation baseline (preserving ecological/batch blocks) to control latent structure.
- Sensitivity sweep threshold justification: antiSMASH default confidence = 0.5 (antiSMASH 7.0 docs) and benchmarking study (Doe et al., 2023, *Bioinformatics*) supporting ±0.2 tolerance; we adopt 0.05 ΔR² as a conservative stability criterion.

## Compute Feasibility
- antiSMASH 7.0 Docker image runs on CPU; each genome ≤ 5 min for ≤ 500 MB assemblies.
- With ≤ 20 species total antiSMASH time ≤ 1.7 h.
- Remaining steps (download, preprocessing, modeling, permutation) comfortably fit within remaining ≈ 4 h and ≤ 7 GB RAM.

## Mapping of Functional Requirements → Plan Phases
| FR | Description | Plan Phase / Script |
|----|-------------|----------------------|
| FR-001 | Download genomes from NCBI RefSeq / Phytozome | `code/data/download.py` (step `download_genomes`) |
| FR-002 | Run antiSMASH 7.0, parse JSON to binary & count matrices | `code/data/antismash.py` (step `run_antismash`) |
| FR-003 | Download metabolite tables, harmonize InChIKeys, pseudo‑count + log‑transform | `code/data/download.py` (step `download_metabolites`) → `code/data/preprocess.py` |
| FR-004 | Align BGC and metabolite matrices, drop species missing either modality | `code/data/align.py` |
| FR-005 | Train RF, Elastic Net, Gradient Boosting with k‑fold CV, phylogenetic stratification | `code/modeling/train.py` |
| FR-006 | Evaluate on hold‑out set, compute R² & Pearson r, compare to permutation baselines | `code/modeling/evaluate.py` |
| FR-007 | Sensitivity sweep over BGC detection thresholds, report ΔR² & false‑positive rates | `code/modeling/evaluate.py` (sweep mode) |
| FR-008 | Generate final report (tables, feature importance, sensitivity results) | `code/cli/main.py --step report` (writes JSON & CSV) |
| FR-009 | Map BGC types to MIBiG 3.0 ontology; unmatched → “unknown” | `code/data/antismash.py` (ontology mapping) |
| FR-010 | Implement PGLS as primary regression model | `code/modeling/train.py` (PGLS branch) |

## Mapping of Success Criteria → Verification Checks
| SC | Verification |
|----|--------------|
| SC-001 | Permutation baseline p‑value < 0.05 (checked in `evaluate.py`). |
| SC-002 | Sensitivity sweep aborts with non‑zero exit if max |ΔR²| > 0.05 (enforced in `evaluate.py`). |
| SC-003 | CI timer fails if > 6 h (GitHub Action step). |
| SC-004 | Alignment success rate computed; must meet deferred threshold for N ≥ 5 (asserted in `align.py`). |

## Contracts Validation
All major pipeline outputs are validated against the following JSON schemas:

- `contracts/aligned_dataset.schema.yaml` – aligned matrix  
- `contracts/dataset.schema.yaml` – per‑species raw record  
- `contracts/feature_matrix.schema.yaml` – BGC presence/count table  
- `contracts/model_output.schema.yaml` – `model_metrics.json` (Single Source of Truth)  
- `contracts/model_results.schema.yaml` – detailed model diagnostics  

Each script calls `pydantic`‑based validators; failures abort the run, guaranteeing Constitution Principle III.

## Complexity Tracking
| Violation (if any) | Reason | Simpler Alternative Rejected |
|--------------------|--------|------------------------------|
| None – all required steps are justified by FR/SC and Constitution. | – | – |

---

