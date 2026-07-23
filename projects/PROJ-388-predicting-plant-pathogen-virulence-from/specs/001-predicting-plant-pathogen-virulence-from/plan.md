# Implementation Plan: Predicting Plant Pathogen Virulence from Publicly Available Genomic and Phenotypic Data

**Branch**: `001-predict-plant-pathogen-virulence` | **Date**: 2024-05-22 | **Spec**: `specs/001-predict-plant-pathogen-virulence/spec.md`

## Summary
This project implements a reproducible, CPU-tractable pipeline to predict plant pathogen virulence by correlating genomic features (virulence gene presence/absence, TF binding site counts) with phenotypic disease severity scores. The system targets *Fusarium graminearum*, *Pseudomonas syringae*, and *Xanthomonas* spp. It adheres to strict data hygiene, phylogenetic correction (using Phylogenetic Independent Contrasts for small N), and multiple testing correction (Benjamini-Hochberg) as mandated by the specification and constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `biopython`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `seaborn`, `jupyter`, `requests`, `hmmsearch` (external binary), `ete3` (for phylogeny), `dendropy` (for tree manipulation).  
**Storage**: Local file system (`data/raw`, `data/processed`, `output`).  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions CPU runner: 2 vCPU, 7GB RAM).  
**Project Type**: Computational Biology Pipeline / CLI.  
**Performance Goals**: Pipeline execution ≤ 6 hours; Peak RAM ≤ 7 GB.  
**Constraints**: No GPU usage; strict adherence to open, downloadable data sources; no synthetic data generation.  
**Scale/Scope**: Targeting a cohort of isolates/species aggregates across multiple species.; feature matrix size < 1000 features.

## Constitution Check

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`; `requirements.txt` with exact versions; external datasets fetched via deterministic URLs. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` restricted to real programmatic sources (NCBI E-utilities, PHI-base). The "Verified datasets" block in the spec contains mismatched data (human/NLP) and is explicitly bypassed in favor of these APIs. |
| **III. Data Hygiene** | **Compliant** | Raw data checksummed; derivations written to new files; PII scan pass (biological data is non-PII). |
| **IV. Single Source of Truth** | **Compliant** | Figures/Stats in `quickstart.md`/`paper` derived directly from `code/` output; no hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Artifacts carry content hashes; `state.yaml` updated on artifact change. |
| **VI. Cross-Isolate Integrity** | **Compliant** | Analysis restricted to target taxa; **Benjamini-Hochberg FDR** (per Constitution) used as primary method; Spearman correlation used for small N. |
| **VII. Public Data Provenance** | **Compliant** | Metadata links isolates to source accessions; `hmmsearch` models and PWMs explicitly referenced. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predict-plant-pathogen-virulence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)
```text
src/
├── data/
│   ├── download.py          # NCBI/PHI-base ingestion with retries
│   ├── extract.py           # hmmsearch & PWM counting
│   └── merge.py             # Phenotype-Genome alignment
├── analysis/
│   ├── phylogeny.py         # Tree construction (ML from housekeeping genes)
│   ├── correlation.py       # Phylogenetic Signal-Adjusted Spearman / Lasso
│   └── viz.py               # Heatmap generation
├── utils/
│   ├── config.py            # Seed pinning, paths
│   └── logging.py           # Exponential backoff logger
└── main.py                  # Pipeline orchestrator

tests/
├── unit/
│   ├── test_download.py
│   └── test_extract.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

requirements.txt
```

**Structure Decision**: Single project structure selected. The pipeline is a linear workflow (Download -> Extract -> Merge -> Analyze -> Visualize) best served by a modular monolithic codebase rather than a distributed microservice architecture. This minimizes overhead on the limited CI runner resources.

## Phase Breakdown & FR/SC Mapping

### Phase 0: Data Ingestion & Feature Extraction (FR-001, FR-002, FR-006, FR-009)
- **Objective**: Download genomes and phenotypes; extract features; handle missing data.
- **FR-001**: Implement `download.py` using `biopython` E-utilities for NCBI and direct URL fetch for PHI-base (bypassing the invalid verified URLs in the spec's block).
- **FR-002**: Implement `extract.py` calling `hmmsearch` (via subprocess) for PHI-base/Pfam; count PWMs.
- **FR-006**: Logic to drop rows with missing phenotypes; log exclusion count.
- **FR-009**: Fallback logic: If < 50% isolate linkage, aggregate by **Species Aggregate** (as defined in Key Entities). If N < 10 after aggregation, skip statistical testing and output a "Descriptive Case Study" (no p-values).
- **SC-001**: Success rate calculated as (processed / requested).

### Phase 1: Phylogenetic Tree Construction (FR-003)
- **Objective**: Generate a tree with valid branch lengths for the target isolates.
- **FR-003**: Construct tree via **Maximum Likelihood (ML)** using core **housekeeping genes** (e.g., rpoB, gyrB, 16S) distinct from virulence factors to avoid circularity.
- **Tree Validation**: Ensure the tree is rooted and, if possible, ultrametric. If NCBI Taxonomy is used for topology, branch lengths must be estimated via `ape` or `ete3` (not assumed zero).
- **Output**: `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy`.

### Phase 2: Statistical Analysis (FR-004, FR-005, FR-007, SC-002, SC-004)
- **Objective**: Compute correlations and apply FDR.
- **Method Selection**:
  - If N >= 30: Use **Phylogenetic Generalized Least Squares (PGLS)**.
  - If N < 30: Use **Phylogenetic Signal-Adjusted Spearman Rank Correlation** (primary) or **L1-regularized (Lasso) Regression** (robustness check for high-dimensional data).
- **FR-004**: Compute correlation coefficients. Use **Phylogenetic Independent Contrasts (PIC)** shuffling to generate the null distribution, preserving tree structure.
- **FR-005**: Apply **Benjamini-Hochberg (BH)** FDR correction (per Constitution Principle VI). **Benjamini-Yekutieli (BY)** is used only as a sensitivity analysis.
- **FR-007**: Filter results for visualization (|ρ| ≥ 0.5) but retain all for output.
- **SC-002**: FDR control verified by the permutation test logic (PIC shuffling).
- **SC-004**: Report proportion of significant features with |ρ| ≥ 0.5.
- **Note**: If N < 10 (e.g., species-level fallback), this phase is skipped, and a descriptive summary is generated instead.

### Phase 3: Visualization & Documentation (FR-008, FR-010, SC-003, SC-005)
- **Objective**: Generate heatmap and Jupyter notebook.
- **FR-008**: `seaborn` heatmap for top 10 features.
- **FR-010**: Generate `requirements.txt` with exact versions.
- **SC-003**: Notebook execution test (numerical equivalence).
- **SC-005**: Runtime monitoring (ensure ≤ 6h, ≤ 7GB RAM).

## Compute Feasibility Strategy
- **CPU-First**: All methods (Lasso, Spearman, ML tree construction) are CPU-tractable. No GPU required.
- **Memory Management**:
  - Genomes: Stream or process one isolate at a time during feature extraction.
  - Feature Matrix: Small (N isolates x M genes). M < 5000. Fits easily in 7GB RAM.
  - Phylogeny: Tree size is negligible.
- **Dataset Streaming**: If NCBI download is large, use chunked writing. If PHI-base is large, filter immediately.
- **No Synthetic Data**: Only real, downloaded data will be used.

## Power & Limitation Disclosure
- **Sample Size**: With N < 30, power to detect small effects is low. The plan prioritizes reporting effect sizes and confidence intervals over binary significance.
- **High Dimensionality**: To address p >> n, features are pre-filtered (present in >10% of isolates) and Lasso regression is used for robustness.
- **FDR Conservatism**: Given the high collinearity and small N, the Benjamini-Hochberg method may be conservative. A sensitivity analysis (raw p-values) is included.