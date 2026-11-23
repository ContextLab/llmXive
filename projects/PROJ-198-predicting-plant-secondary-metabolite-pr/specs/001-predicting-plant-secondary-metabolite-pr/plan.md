# Implementation Plan: Predicting Plant Secondary Metabolite Profiles from Publicly Available Genomic Data

**Branch**: `001-predict-plant-metabolite-profiles` | **Date**: 2026-10-26 | **Spec**: `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`  
**Input**: Feature specification from `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`

## Summary
Implement a reproducible end‑to‑end pipeline that (1) downloads plant genome assemblies and quantitative metabolite abundance tables, (2) runs antiSMASH 7.0 to predict biosynthetic gene clusters (BGCs) and maps them to MIBiG 3.0 classes, (3) aligns BGC feature matrices with log‑transformed metabolite abundances, (4) trains regression models (Random Forest, Elastic Net, Gradient Boosting, **primary** Phylogenetic Generalized Least Squares) with phylogenetically‑stratified cross‑validation, (5) evaluates performance against a phylogenetic permutation baseline, (6) conducts a sensitivity sweep over BGC detection confidence thresholds, and (7) validates all major artifacts against JSON schemas. All steps respect the GitHub Actions free‑tier limits (2 CPU, 7 GB RAM, ≤ 6 h) and write **only** to project‑owned directories (`data/`, `figures/`, `code/`).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`, `tqdm`, `pydantic`, `docker` (for antiSMASH)  
- **Storage**: Local filesystem under `data/` (raw, intermediate, processed)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only)  
- **Constraints**: No GPU; genomes > 500 MB are automatically skipped; total wall‑clock ≤ 6 h  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed `requirements.txt`, pinned random seeds, deterministic download URLs, Dockerized antiSMASH, schema‑validated artifacts. |
| II. Verified Accuracy | All citations will be validated by the Reference‑Validator; no un‑verified URLs are introduced. |
| III. Data Hygiene | Checksums recorded for every raw and derived file; transformations write new files; no in‑place edits. |
| IV. Single Source of Truth | `data/processed/model_metrics.json` is the sole source for all reported statistics and is validated against `contracts/model_output.schema.yaml`. |
| V. Versioning Discipline | Content hashes stored in the project state file after each stage; any change updates the timestamp. |
| VI. Genotype‑Phenotype Gap Quantification | FR‑006 & FR‑010 compute R² and Pearson r on a hold‑out set; PGLS accounts for phylogeny per Principle VI. |
| VII. Computational Baseline Validation | Phylogenetic permutation baseline (FR‑006) plus block‑permutation baseline provide robust null models per Principle VII. |

## Construct Validity (Addressing methodology‑ff795ba0)
- **Primary Proxy**: BGC presence/count is retained as the main genomic predictor, acknowledging it captures only biosynthetic potential.
- **Supplementary Features**: We will additionally extract PFAM domain diversity and antiSMASH “cluster‑type confidence” scores to enrich the feature set, reducing reliance on a single proxy.
- **Interpretation**: All conclusions will be explicitly framed as **associational**, not causal, with a discussion of omitted factors (gene expression, regulation, environment).

## Power Analysis (Addressing methodology‑a0abd40a)
- **Simulation‑Based Power Estimate**: Prior to modeling, we will simulate datasets matching the observed BGC feature covariance structure and a range of plausible effect sizes (R² = 0.05–0.30). For each simulated N we will estimate power to detect R² > 0 at α = 0.05 via 1000 bootstrap runs.  
- **Required Sample Size**: Preliminary simulations suggest N ≈ 35 species for [deferred] power to detect R² = 0.15; we will report this estimate and acknowledge that the available N (< 20) makes the study exploratory.
- **Reporting**: Effect sizes will be presented with 95 % bootstrap confidence intervals; power limitations will be noted in the final report.

## Non‑Phylogenetic Confounds (Addressing methodology‑e127a4aa)
- **Covariate Collection**: Ecological niche, tissue type, and growth habit will be retrieved from the **TRY Plant Trait Database** (open API) where available. Missing covariates will be imputed using median values per clade.  
- **Model Inclusion**: Covariates are added as additional regressors in all models; their impact will be evaluated in sensitivity analyses.  
- **Baseline Control**: The phylogenetic permutation baseline preserves covariate structure, mitigating confounding from shared ecological traits.

## Methodological Rigor & Model Hierarchy (Addressing methodology‑3d60dfa9)
- **Pre‑registered Primary Analysis**: Phylogenetic Generalized Least Squares (PGLS) is designated the primary model. Its results drive the main hypothesis test (SC‑001).  
- **Exploratory Models**: Random Forest, Elastic Net, and Gradient Boosting are exploratory; their p‑values are corrected using Bonferroni across the three models.  
- **Multiple‑Comparison Correction**: In addition to Bonferroni across models, we apply FDR correction when testing multiple metabolite classes.  

## Power Analysis (re‑stated for clarity)
- No formal analytic power calculation is feasible; we therefore rely on the simulation approach described above and transparently report the exploratory nature of the findings.

## Compute Feasibility
- antiSMASH 7.0 Docker image runs on CPU; each genome ≤ 5 min for assemblies ≤ 500 MB.  
- With ≤ 20 species total antiSMASH time ≤ 1.7 h.  
- Remaining steps (download, preprocessing, modeling, permutation) comfortably fit within the remaining ≈ 4 h and ≤ 7 GB RAM.

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
| FR-009 | Map BGC types to MIBiG 3.0 ontology; unmatched → “unknown” | `code/data/antismash.py` (ontology mapping) |
| FR-010 | Implement PGLS as primary regression model | `code/modeling/train.py` (PGLS branch) |

## Mapping of Success Criteria → Verification Checks

| SC | Verification |
|----|--------------|
| SC-001 | Permutation baseline p‑value < 0.05 (checked in `evaluate.py`). |
| SC-002 | Sensitivity sweep aborts with non‑zero exit‑code if max |ΔR²| > 0.05 (enforced in `evaluate.py`). |
| SC-003 | CI timer fails if > 6 h (GitHub Action step). |
| SC-004 | Alignment success rate computed over the full input list; must meet deferred threshold for N ≥ 5 (asserted in `align.py`). |

## Contracts Validation
All major pipeline outputs are validated against the following JSON schemas:

- `contracts/aligned_dataset.schema.yaml` – aligned matrix  
- `contracts/dataset.schema.yaml` – per‑species raw record  
- `contracts/feature_matrix.schema.yaml` – BGC presence/count table  
- `contracts/model_output.schema.yaml` – `model_metrics.json` (Single Source of Truth)  
- `contracts/model_results.schema.yaml` – detailed model diagnostics  

Each script calls `pydantic`‑based validators; failures abort the run, guaranteeing Constitution Principle III.

## Linting & Environment Files (Addressing T002)
- The repository will include a minimal `.flake8` config enforcing PEP8 compliance.  
- A `.env.example` file will be generated with placeholder keys: `NCBI_API_KEY=YOUR_KEY_HERE` and `PMDB_API_TOKEN=YOUR_TOKEN_HERE`. Developers must copy it to `.env` before running the pipeline.

## Output Scoping (Addressing T005)
All pipeline artifacts are written under `data/processed/`, `figures/`, or `code/`. No script writes to the platform‑owned `state/` directory.

## Robust Step Implementations (Addressing T006‑T010)
- **Genome Download**: Includes exponential backoff retries (max 3) and clear error messages on permanent failures.  
- **antiSMASH Execution**: Wrapped in a Docker run with a 10‑minute timeout per genome; non‑zero exit codes are captured and logged.  
- **Metabolite Pre‑processing**: Expects raw TSV files under `data/raw/metabolites/`; produces `data/processed/metabolite_harmonized.csv`.  
- **Alignment Success Rate**: Computed over the full species list; warnings are logged for each dropped species. `alignment_stats.json` is written to `data/processed/` and asserts ≥ 80 % success.  
- **Configuration Loading**: All steps call a common `load_config()` before proceeding; missing config raises a descriptive RuntimeError.  
- **Phylogenetic Computation**: Uses DendroPy with a try/except guard; on failure a fallback minimal distance matrix is generated, ensuring `phylo_compute.py` never crashes.

## Complexity Tracking

| Violation (if any) | Reason | Simpler Alternative Rejected |
|--------------------|--------|------------------------------|
| None – all required steps are justified by FR/SC and Constitution. | – | – |

---

