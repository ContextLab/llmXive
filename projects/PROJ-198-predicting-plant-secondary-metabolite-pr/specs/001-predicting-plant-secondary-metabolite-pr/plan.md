# Implementation Plan: Predicting Plant Secondary Metabolite Profiles from Publicly Available Genomic Data

**Branch**: `001-predict-plant-metabolite-profiles` | **Date**: 2026-07-03 | **Spec**: `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`
**Input**: Feature specification from `specs/001-predict-plant-secondary-metabolite-profiles/spec.md`

## Summary

This feature implements a computational pipeline to quantify the extent to which biosynthetic gene cluster (BGC) diversity explains variation in quantitative secondary metabolite profiles across plant species. The approach involves downloading genomic assemblies and metabolite tables, predicting BGCs using antiSMASH, aligning the data, and training regression models (Random Forest, Elastic Net, Gradient Boosting, PGLS) with phylogenetic stratification and permutation baselines. The analysis focuses on *quantitative* prediction (abundance vs. copy number) to avoid tautological results from qualitative presence/absence matching.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`, `tqdm`, `pydantic`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free‑tier runner: 2 CPU, 7 GB RAM)  
**Performance Goals**: Complete data alignment and model training for up to 20 species within 6 h on CPU‑only infrastructure.  
**Constraints**: No GPU; antiSMASH must run via Docker or local CLI. Genomes > 500 MB are skipped to stay within runtime limits.  
**Scale/Scope**: Matched set of plant species (≥ 5 for CI test, ≥ 20 for full analysis); BGC feature matrix of hundreds of types; metabolite panel of dozens of compounds.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

- **I. Reproducibility** – Pinned `requirements.txt`, fixed random seeds, deterministic data fetching.  
- **II. Verified Accuracy** – All citations will be validated against the “Verified datasets” block; no invented URLs.  
- **III. Data Hygiene** – Checksums recorded for every raw and derived artifact; transformations produce new files.  
- **IV. Single Source of Truth** – All final statistics, performance tables, and feature‑importance rankings are written to **`data/processed/model_metrics.json`**, which serves as the definitive SSoT for downstream reporting.  
- **V. Versioning** – Content hashes stored in the project state file.  
- **VI. Genotype‑Phenotype Gap** – FR‑006 and FR‑010 explicitly quantify variance explained (R²) and use PGLS to account for phylogeny.  
- **VII. Computational Baseline** – Phylogenetic permutation baseline (see Methodological Rigor) validates that observed signal exceeds null expectation.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-secondary-metabolite-profiles/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── aligned_dataset.schema.yaml
    ├── feature_matrix.schema.yaml
    ├── model_output.schema.yaml
    └── model_results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py                # Configuration and constants
├── data/
│   ├── __init__.py
│   ├── download.py          # FR‑001, FR‑003 (NCBI, MetaboLights)
│   ├── preprocess.py        # FR‑002, FR‑003, FR‑009 (antiSMASH wrapper, InChIKey mapping)
│   └── align.py             # FR‑004 (matrix alignment, Pydantic validation)
├── modeling/
│   ├── __init__.py
│   ├── train.py             # FR‑005, FR‑010 (RF, Elastic Net, Gradient Boosting, PGLS)
│   ├── eval.py              # FR‑006, FR‑007 (LOO CV, bootstrap, permutation baseline)
│   └── phylo.py             # Phylogenetic utilities for PGLS
├── utils/
│   ├── __init__.py
│   └── logging.py
├── cli/
│   └── main.py              # Entry point
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision** – A single `code/` package with clear sub‑modules mirrors the linear pipeline (download → antiSMASH → alignment → model → evaluate) while keeping concerns isolated for testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Phylogenetic Permutation Baseline | Required by FR‑006 & Constitution Principle VII to rule out phylogenetic artefacts. | Simple random label shuffle would ignore shared evolutionary history. |
| PGLS Model | Required by FR‑010 to account for non‑independence of species. | Ordinary least squares would violate comparative‑biology assumptions. |
| antiSMASH Integration | Required by FR‑002 for accurate BGC prediction. | Heuristic k‑mer counts lack specificity and ontology mapping. |
| Dimensionality Reduction (PCA) | Needed when BGC feature count > N/2 to avoid over‑fitting (see Power Acknowledgement). | Direct high‑dimensional regression would be statistically unstable. |
| Leave‑One‑Out CV | With N < 20, 5‑fold CV yields tiny test folds; LOO maximises data usage. | 5‑fold CV would produce noisy R² estimates. |
| Sensitivity‑Failure Hard Stop | SC‑002 mandates variation ≤ 0.05; pipeline must abort if exceeded. | A warning would allow a non‑compliant result to pass. |

## Methodological Rigor & Success Criteria

- **Observational Design** – The study is purely correlational; no experimental manipulation or instrumental variables are employed. All causal language is avoided; results are interpreted as associations only (see Constitution Principle VI).  
- **Construct Validity** – BGC **counts** are used as a proxy for biosynthetic capacity. We acknowledge that metabolite abundance is also driven by gene expression, environmental conditions, tissue specificity, and experimental batch effects, which are not modeled due to data unavailability (see Concern methodology‑9c4cf52f).  
- **Power Acknowledgement** – With N < 20 the analysis is exploratory; no formal power analysis is feasible. Results are framed as hypothesis‑generating and interpreted with caution (see Concern methodology‑f2827a91).  
- **Confounder Limitation** – Environmental metadata, tissue type, developmental stage, and batch are not available for the public datasets; their omission is a limitation that may introduce omitted‑variable bias (see Concern methodology‑1deeed41).  
- **Models**: Random Forest, Elastic Net, Gradient Boosting (scikit‑learn, CPU‑only) and **Phylogenetic Generalized Least Squares (PGLS)** (statsmodels with custom phylogenetic covariance).  
- **Validation**:  
  * **Leave‑One‑Out (LOO) CV** for N < 20; **5‑Fold CV** (recorded as `"5Fold"` in `model_output.schema.yaml`) when N ≥ 20; both are reported as `cv_method`.  
  * **Bootstrap** (1000 resamples) provides confidence intervals for R².  
  * **Phylogenetic Permutation Baseline** – **only metabolite labels are shuffled** while preserving the predictor matrix and phylogenetic tree; repeated until convergence; p‑value computed as proportion of permuted R² ≥ observed R² (see Concern methodology‑c739be52).  
- **Multiple Comparisons** – Bonferroni/FDR correction applied when testing multiple metabolite classes.  
- **Collinearity** – VIF scores calculated; high VIF features are reported but retained due to biological relevance.  
- **Dimensionality Reduction** – PCA applied to BGC feature matrix when feature count > N/2; PGLS operates on PCA‑reduced components (see Concern methodology‑f2827a91).  

### Success Criteria Alignment
- **SC‑001** – Null hypothesis (R² = 0) tested via permutation baseline; significance threshold p < 0.05.  
- **SC‑002** – Sensitivity sweep must produce **max |ΔR²| ≤ 0.05**. The pipeline now **fails with a non‑zero exit code** if this bound is exceeded, enforcing the mandatory criterion (see Concern methodology‑9d101ccd).  
- **SC‑003** – Overall runtime ≤ 6 h on the free‑tier runner (enforced by runtime monitoring).  
- **SC‑004** – Alignment success rate computed as `#species with both modalities / #species in input list`; required ≥ [deferred]% for N ≥ 5.  

## Compute Feasibility

- **antiSMASH Runtime** – Approx. 5 min per ≤ 500 MB genome on 2 CPU cores; with ≤ 20 species total runtime ≤ 1.5 h.  
- **Memory** – antiSMASH processes each genome sequentially; peak RAM ≈ several GB.  
- **Overall** – Data download (< 1 GB), preprocessing, PCA, modeling, and permutation baseline comfortably fit within the 7 GB RAM / 6 h limit.  

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| Use NCBI RefSeq for genomes | Reliable, programmatic access, no authentication required. |
| Skip genomes > 500 MB | Guarantees antiSMASH completes within CI time budget. |
| LOO CV for N < 20 | Provides stable performance estimates with limited samples. |
| 5‑Fold CV for N ≥ 20 | Recorded as `"5Fold"` to satisfy schema; aligns with FR‑005 when sample size permits. |
| Phylogenetic permutation after model training | Baseline must compare against a trained model; ordering corrected (see Concern methodology‑c739be52). |
| PCA before PGLS | Reduces dimensionality to avoid over‑fitting; enforced as a hard dependency (see Concern methodology‑f2827a91). |
| Log‑transform + pseudo‑count for metabolites | Standard practice to handle zeros and skewed distributions. |
| Inner join alignment | Ensures paired analysis; partial rows excluded per spec. Zero‑BGC rows are **retained** as valid data points (see Edge Cases). |
| No fallback for data sources | Aligns with the “FAIL LOUDLY” requirement; any download failure aborts with a clear error message. |
| Schema validation after each major stage | Guarantees conformity to contracts and satisfies Constitution Principle III. |

## Schema Validation (new)

After each major stage (download, antiSMASH preprocessing, alignment, PCA, model training, evaluation) the generated artifacts are validated against the JSON schemas in `contracts/` using Pydantic models. Validation failures abort the pipeline, guaranteeing conformity to the data model and Constitution Principle III.

## Single Source of Truth (SSoT)

All final statistics, performance tables, and feature‑importance rankings are written to **`data/processed/model_metrics.json`**. This file serves as the definitive source for downstream reporting, figure generation, and manuscript preparation, satisfying Constitution Principle IV.
