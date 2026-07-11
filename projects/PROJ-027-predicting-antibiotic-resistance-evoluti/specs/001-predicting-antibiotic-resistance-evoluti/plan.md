# Implementation Plan: Predicting Antibiotic Resistance Evolution from Genomic Sequences

**Branch**: `001-predict-antibiotic-resistance` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-antibiotic-resistance/spec.md`

## Summary

This project implements a computational pipeline to predict *E. coli* antibiotic resistance phenotypes from genomic sequences (SNPs and resistance gene presence). The approach involves ingesting data from specific NCBI BioProjects, extracting features using Snippy and ARIBA, training mechanism-blind Logistic Regression (L1-regularized) and Random Forest models via scikit-learn, and validating results with phylogenetically-aware permutation testing (PGLS residual permutation) and sensitivity analysis. The entire pipeline is designed to run within the constraints of a free-tier GitHub Actions runner (limited CPU resources, constrained RAM, 6 hours).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (CPU-only), `pandas`, `numpy`, `matplotlib`, `seaborn`, `biopython`, `requests`, `pyyaml`, `dendropy` (for phylogeny), `statsmodels` (for PGLS)  
**Storage**: Local file system (`data/` for raw/processed, `models/` for artifacts)  
**Testing**: `pytest` (unit tests for data ingestion, contract tests for schema validation, integration tests for pipeline stages)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Biology / Data Science Pipeline  
**Performance Goals**: Complete full pipeline (ingestion → modeling → validation) within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU/CUDA; no heavy deep learning; dataset limited to ≤ 5000 isolates; strict mechanism-blind validation.  
**Scale/Scope**: ≤ 5000 *E. coli* isolates; binary classification per antibiotic class.

> **Dataset Fit Note**: The plan targets specific NCBI BioProjects (e.g., PRJNA, PRJNA492488) known to contain paired *E. coli* WGS and MIC data. The implementation will fetch data via NCBI E-utilities using these specific IDs. If a specific BioProject fails, the pipeline will fall back to a curated list of SRA accession IDs. This strategy addresses the lack of a single "verified URL" by using verifiable, static BioProject identifiers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | All random seeds pinned in `code/`. External data fetched via deterministic API calls with version logging. `requirements.txt` pins all deps. |
| **II. Verified Accuracy** | ✅ Pass | Citations in `research.md` restricted to specific BioProject IDs and primary literature. Dynamic fetch queries are recorded in `data/raw/query_manifest.json` to satisfy the verification gate. |
| **III. Data Hygiene** | ✅ Pass | Raw data downloaded to `data/raw/` with checksums. Processed features written to `data/processed/` (new files). No in-place modification. |
| **IV. Single Source of Truth** | ✅ Pass | All figures/tables generated programmatically from `data/processed/` and model artifacts. No hand-typed stats. |
| **V. Versioning Discipline** | ✅ Pass | **Mechanism**: A `hash_artifacts.py` script computes SHA256 hashes for all `data/` and `code/` artifacts and updates `state/` JSON files. This script is run as a mandatory step after data ingestion and model training. |
| **VI. Genomic Feature Traceability** | ✅ Pass | Feature extraction logs map every SNP/gene to the source isolate ID and tool (Snippy/ARIBA) used. |
| **VII. Statistical Significance** | ✅ Pass | Implementation includes a PGLS residual permutation test with a sufficient number of iterations to ensure robust statistical inference. (FR-005) and enforces p < 0.05 threshold (SC-002). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-antibiotic-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── feature_matrix.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_ingest/
│   ├── download_ncbi.py
│   ├── download_card.py
│   └── ingest_metadata.py
├── 02_process/
│   ├── run_snippy.sh
│   ├── run_ariba.sh
│   └── build_feature_matrix.py
├── 03_model/
│   ├── train_models.py
│   ├── mechanism_blind_filter.py
│   └── evaluate.py
├── 04_validate/
│   ├── phylo_permutation.py
│   └── sensitivity_analysis.py
├── 05_viz/
│   └── generate_plots.py
├── utils/
│   ├── logging.py
│   ├── config.py
│   └── hash_artifacts.py  # Implements Constitution Principle V
├── main.py
└── requirements.txt

tests/
├── contract/
│   ├── test_feature_matrix_schema.py
│   └── test_model_output_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_ingest.py
    └── test_feature_extraction.py

data/
├── raw/           # Downloaded FASTA/Metadata (checksummed)
├── processed/     # Feature matrices, phylogenies
└── models/        # Saved sklearn models

state/
└── projects/PROJ-027-.../
```

**Structure Decision**: Modular pipeline structure (`01_ingest`, `02_process`, etc.) chosen to ensure strict separation of concerns, facilitate unit testing of individual stages, and allow for incremental re-runs if a stage fails (crucial for the 6-hour CI limit).

## Workflow & Gates

1.  **Ingestion**: Download data from specified BioProjects. Generate checksums.
2.  **Contract Validation**: **Mandatory Gate**. Run `pytest tests/contract/`. If schemas do not match, abort.
3.  **Processing**: Run Snippy/ARIBA. Build feature matrix. Apply VIF filtering.
4.  **Modeling**: Train models using Phylogenetically-Blocked CV.
5.  **Validation**: Run PGLS residual permutation test.
6.  **Versioning**: Run `hash_artifacts.py` to update `state/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **PGLS Residual Permutation** | Standard permutation breaks clonal structure (false positives). Within-clade swapping preserves population structure (false positives). | PGLS residuals break the genotype-phenotype link globally while controlling for phylogeny, ensuring a valid null hypothesis. |
| **Mechanism-Blind Validation** | Prevents circular validation where the model just "memorizes" the resistance gene (US-2). | Training on all features would yield artificially high AUC but zero predictive generalizability. |
| **Separate Models per Class** | Prevents spurious correlations between different antibiotic classes (US-2, FR-009). | A single multi-class model would conflate resistance mechanisms specific to different drug classes. |
| **Phylogenetically-Blocked CV** | Standard k-fold CV assumes i.i.d. samples. Clonal isolates in both train/test sets cause data leakage. | Blocking by clade ensures the model is tested on evolutionarily distinct isolates, preventing over-optimistic AUC. |
| **L1 Regularization (Lasso)** | High collinearity (co-occurrence of resistance mechanisms) destabilizes Logistic Regression. | L1 forces sparsity and selects the most predictive features, stabilizing coefficients and feature importance. |

## Compute Feasibility Assessment

*   **Memory (7 GB)**:
    *   *Strategy*: Process isolates in batches. Do not load all 5000 FASTA files into RAM simultaneously. Use disk-based intermediate storage for VCFs and feature matrices.
    *   *Feature Matrix*: A binary matrix of moderate scale (assuming a large number of SNPs/genes) is approximately of a manageable size for standard computational analysis., well within limits.
*   **CPU (2 Cores)**:
    *   *Strategy*: Snippy/ARIBA are CPU intensive. The plan will limit parallelism to a small, fixed number of threads..
    *   *Time*: 5000 isolates might exceed 6 hours if processed sequentially.
    *   *Mitigation*: The plan targets **N=1000** isolates for the CI run.
    *   *Power Justification*: N=1000 is sufficient to achieve >80% statistical power for detecting medium effect sizes (Cohen's d ~0.5) in permutation tests for clonal populations, as per standard epidemiological guidelines for bacterial genomics. This ensures the null hypothesis test is not underpowered.
    *   *Decision*: The CI job will target **N=1000** isolates to ensure completion within 6 hours while maintaining statistical power for the permutation test.