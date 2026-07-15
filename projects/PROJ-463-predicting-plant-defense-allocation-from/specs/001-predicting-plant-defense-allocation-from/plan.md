# Implementation Plan: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

**Branch**: `001-plant-defense-allocation` | **Date**: 2026-06-16 | **Spec**: `specs/001-plant-defense-allocation/spec.md`
**Input**: Feature specification from `/specs/001-plant-defense-allocation/spec.md`

## Summary

This feature implements a computational pipeline to predict plant defense allocation (chemical vs. physical) using tissue-specific transcriptomic responses to herbivory. The system downloads and preprocesses public RNA-seq data (FASTQ), performs differential expression analysis (DESeq), constructs herbivore-response vectors, and trains regularized models (Elastic Net, Random Forest) to predict a derived Defense Allocation Index.

**Current Status**: **Structural Prototype**. Due to the absence of verified plant herbivory RNA-seq datasets in the provided "Verified datasets" block, the current implementation uses **synthetic data** to validate the code structure, schema compliance, and statistical logic (LOSO, PGLS, Power Analysis). The scientific hypothesis *cannot* be validated until verified real data is provided.

The plan strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and statistical rigor (power analysis, phylogenetic null models, FWER correction) while remaining computationally feasible on CPU-only free-tier CI.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `biopython`, `rpy2` (for DESeq2/ComBat-seq via R), `requests`, `tqdm`, `pyyaml`, `seaborn`, `matplotlib`, `ete3` (for phylogeny), `pydantic` (for schema validation).  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/traits`); JSON/CSV/Parquet formats.  
**Testing**: `pytest` (unit), `pytest-benchmark` (optional), schema validation via `jsonschema`.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM).  
**Project Type**: Data analysis pipeline / Research tool.  
**Performance Goals**: Complete full pipeline on a sampled subset (≤15 species) within 6 hours; RAM usage < 6GB.  
**Constraints**: No GPU; no large-LLM inference; strict memory limits.  
**Scale/Scope**: Analysis of plant species with paired chewing/piercing-sucking RNA-seq data and defense traits.

**Execution Mode**:
- **Default**: `--mode synthetic`. Generates synthetic TPM matrices and trait data with known ground truth for structural validation.
- **Real Data**: `--mode real`. Attempts to fetch from NCBI/TRY. **Will fail** if datasets are not in the verified list, raising `human_input_needed`.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action/Notes |
|-----------|-------------------|--------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, `requirements.txt` with exact versions, and re-runnable scripts. |
| **II. Verified Accuracy** | **PASS (Structural Only)** | The *process* for verifying URLs is implemented. Current execution uses synthetic data due to lack of verified plant datasets. Real data validation is blocked until verified sources are provided. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksums for raw data (`data/raw`), immutable transformation steps, and no PII. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` and `code/`. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be generated for artifacts; state file updated on changes. |
| **VI. Transcriptomic Data Provenance** | **PASS (Simulated)** | Plan logs accession IDs, genome versions, and tool versions. For synthetic data, a "Synthetic Manifest" records generation parameters and seed. |
| **VII. Defense Trait Data Integrity** | **PASS** | Plan mandates storing raw traits with citations and documenting normalization steps for the Defense Allocation Index. |

## Project Structure

### Documentation (this feature)

```text
specs/001-plant-defense-allocation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # NCBI/TRY data acquisition
│   ├── preprocess.py        # fastp, HISAT2, featureCounts wrappers
│   ├── batch_correction.py  # ComBat-seq logic (uses fixed 50-gene list)
│   ├── traits.py            # Defense trait compilation (with fallback)
│   └── synthetic_generator.py # Synthetic data generation for prototype
├── analysis/
│   ├── de_analysis.py       # DESeq2 execution
│   ├── feature_engineering.py # Herbivore-response vectors, pathway agg (excludes trait genes)
│   ├── modeling.py          # Elastic Net, RF, LOSO CV, PGLS
│   └── validation.py        # Power analysis, Phylo null, Permutation tests
├── utils/
│   ├── logger.py
│   ├── config.py            # Paths, seeds, thresholds
│   └── provenance.py        # Checksums, manifest generation
├── cli/
│   └── run_pipeline.py      # Entry point (--mode synthetic|real)
└── tests/
    ├── unit/
    ├── integration/
    └── contract/            # Schema validation tests

data/
├── raw/                     # Unmodified FASTQ, trait dumps (or synthetic raw)
├── processed/               # TPM matrices, DE results
├── traits/                  # Compiled defense indices
└── manifests/               # Provenance logs (including synthetic manifest)
```

**Structure Decision**: Selected **Option 1 (Single project)** with modular separation of data, analysis, and utils. This minimizes overhead for a research pipeline and simplifies dependency management on CI.

## Complexity Tracking

No violations detected. The plan adheres to the constraint of CPU-only execution by explicitly sampling data and using lightweight statistical models.

## Implementation Phases

### Phase 0: Data Acquisition & Verification (FR-001, FR-011)

1.  **Source Verification**: Check if required plant herbivory RNA-seq datasets and TRY trait data exist in the "Verified datasets" block.
    -   *If Missing*: Log `human_input_needed`, switch to `--mode synthetic` (default), and generate synthetic data with known ground truth for structural validation.
    -   *If Present*: Download FASTQ files and trait data.
2.  **Fallback Lookup (FR-011)**: For each target species, attempt to fetch traits from TRY. If missing, query Phenoscape/GBIF.
    -   *Halt Condition*: If >30% of target species lack data from *all* sources, halt and raise `human_input_needed`.
3.  **Quality Control**: Verify ≥2 biological replicates per condition. Exclude studies lacking tissue metadata.

### Phase 1: Preprocessing & Batch Correction (FR-002, FR-003)

1.  **Pipeline Execution**: Run `fastp` (trimming), `HISAT2` (alignment), `featureCounts` (quantification) to produce TPM matrices.
2.  **Batch Correction (FR-003)**:
    -   Apply `ComBat-seq`.
    -   **Fixed Gene List**: Use the specific 50 housekeeping genes defined in FR-003 (ACT2, ACT7, GAPDH, UBQ10, EF1a, TUB6, TUB1, PP2A, SAND, CYP79D16, CYP79D15, CYP79D17, CYP83A1, CYP83B1, CYP96A1, CYP96A2, CYP96A3, CYP71A1-32) for GeNorm M-value selection.
    -   **Metric**: Calculate Coefficient of Variation (CV) reduction for these 50 genes. Target: ≥20% reduction.
    -   **Flag**: If residual variance >15%, flag for manual review.

### Phase 2: Feature Engineering & Defense Index (FR-004, FR-005, FR-006, FR-012)

1.  **Differential Expression (FR-004)**: Run DESeq2 (FDR < 0.05, |log₂FC| > 1) for each species-tissue pair.
2.  **Herbivore-Response Vector (FR-005)**:
    -   Select a subset of common DE genes (ranked by aggregate -log10(p-value)).
    -   **Leakage Prevention**: Exclude genes directly involved in the synthesis of the measured defense traits (e.g., CYPD16 for glucosinolates) from the predictor set.
3.  **Pathway Aggregation (FR-012)**:
    -   Map DE genes to KEGG/GO pathways.
    -   **Robustness Check**: Filter pathways to those with ≥3 mapped genes in *all* target species.
    -   Reduce features to ≤50 pathway-level scores.
4.  **Defense Allocation Index (FR-006)**:
    -   Compile traits: Chemical = [Glucosinolates, Alkaloids, Phenolics]; Physical = [Trichome Density, Leaf Tensile Strength].
    -   Calculate DAI = (mean standardized chemical) / (mean standardized physical).

### Phase 3: Modeling & Statistical Validation (FR-007, FR-008, FR-009, FR-010, FR-016, FR-017)

1.  **Power Analysis (FR-016)**:
    -   **Gate**: Execute *before* model training.
    -   Calculate required N for target R² (0.1, 0.2, 0.3) with α=0.05, β=0.2.
    -   **Halt**: If available N < 15, halt and report "Insufficient statistical power".
2.  **Model Training**:
    -   Train Elastic Net and Random Forest using **Leave-One-Species-Out (LOSO)** CV.
    -   Feature selection and training occur strictly within the training fold.
3.  **Phylogenetic Validation (FR-007, FR-017)**:
    -   **PGLS**: Fit Phylogenetic Generalized Least Squares model.
    -   **Null Model**: Generate null distribution of R² by permuting *outcome* (DAI) labels while preserving phylogenetic structure of predictors (or using phylogenetic permutation of residuals).
    -   **Threshold**: Observed R² must exceed the upper tail of the null distribution.
4.  **Significance Testing (FR-008, FR-010)**:
    -   Permutation test (N=10,000) for Spearman correlation.
    -   Apply Holm-Bonferroni correction for multiple hypotheses.
5.  **Sensitivity Analysis (FR-009)**:
    -   Vary DE gene count (e.g., low, moderate, high) and report R² variation.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Dataset Mismatch** | High ([deferred] with current list) | Critical | Use synthetic data for structural validation; flag `human_input_needed` for real data. |
| **RAM Overflow** | Medium | High | Sample to multiple species; stream data processing. |
| **Power Failure** | High (if N<15) | Critical | Explicit power analysis gate; halt if N < 15. |
| **Phylogeny Missing** | Medium | Medium | Generate synthetic tree if real tree unavailable; document limitation. |
| **Circular Validation** | High | Critical | Exclude trait-synthesis genes from predictors; use residual permutation for null model. |

## Decision Rationale

The decision to use synthetic data is driven by the **fatal dataset mismatch** in the "Verified datasets" block. The spec requires plant herbivory RNA-seq and TRY traits, but the provided list contains only human, disease, or non-biological datasets. Implementing a pipeline that attempts to fetch from these URLs would fail immediately. Using synthetic data allows the **statistical rigor** (LOSO, PGLS, Power Analysis) and **code structure** to be validated, ensuring the system works correctly when the correct datasets are eventually provided.

**Note**: The current phase is **Prototype Validation**. The project cannot reach `research_complete` without verified real data.