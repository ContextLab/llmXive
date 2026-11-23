# Implementation Plan: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

**Branch**: `001-plant-defense-allocation` | **Date**: 2026-06-16 | **Spec**: `specs/001-plant-defense-allocation/spec.md`
**Input**: Feature specification from `/specs/001-plant-defense-allocation/spec.md`

## Summary

This project implements a computational pipeline to predict plant defense allocation strategies (chemical vs. physical) based on tissue-specific transcriptomic responses to chewing versus piercing-sucking herbivores. The approach involves downloading raw RNA-seq data from NCBI GEO/SRA (prioritizing verified accession IDs), preprocessing it (QC, alignment, quantification with median depth downsampling), performing batch correction (only when not confounded with species), deriving herbivore-response vectors (Chewing - Piercing) from differentially expressed genes (excluding biosynthetic pathways of target traits), and training regularized regression models (Elastic Net, Random Forest) with **Clade-Stratified Leave-One-Species-Out (LOSO)** cross-validation. The pipeline includes rigorous statistical validation (bootstrapped LOSO, phylogenetic null models, power analysis based on phylogenetic lambda) and strict data gating mechanisms to ensure feasibility and reproducibility.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets`, `pandas`, `scikit-learn`, `statsmodels`, `biopython`, `pyyaml`, `fastp` (via subprocess), `hisat2` (via subprocess), `featurecounts` (via subprocess), `rpy2` (for DESeq2), `pyphenoscape`, `rgbib`, `requests`, `kaggle-kernels` (for GPU offload)
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/interim/`)
**Testing**: `pytest` (contract tests against YAML schemas), `unittest` for logic
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM) with automatic offload to Kaggle GPU for heavy alignment/quantification if needed (via execution agent auto-detection using `kaggle-kernels` CLI).
**Project Type**: Computational Biology Pipeline / CLI
**Performance Goals**: Complete QC and DE analysis for ≥3 studies within 6 hours on CPU; Model training within 6 hours.
**Constraints**: Must run on moderate RAM resources. (streaming data); No local GPU; Must not fabricate data; Must strictly adhere to the "Verified datasets" list for any pre-processed data references.
**Scale/Scope**: Processing of ≥3 GEO/SRA studies, ~ species (target), generating multiple pathway-level features per species.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins versions; Random seeds set in `code/analysis/` scripts; External datasets fetched programmatically from NCBI (GEO/SRA) or verified HF sources. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `plan.md` will be validated against the provided "Verified datasets" list or primary literature (e.g., arXiv). No fabricated URLs. **Reference-Validator Agent** runs before T014/T025a. **`data/processed/metadata_verification_report.json`** is the SSoT for Principle II validation. The pipeline executes the Reference-Validator Agent against all citations in research.md and plan.md before proceeding to T014. |
| **III. Data Hygiene** | **PASS** | `data/raw/` stores unaltered FASTQ (including `data/raw/synthetic/`); `data/processed/` stores derived files with checksums; No in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | All metrics in the final output trace to `data/processed/` CSV/JSON files; No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded in `state/` YAML; Artifact updates trigger `updated_at` refresh. **`phylogenetic_tree.tre`** is checksummed and versioned in `state/`. |
| **VI. Transcriptomic Data Provenance** | **PASS** | Raw FASTQs archived in `data/raw/` (including synthetic in `data/raw/synthetic/`) with manifest including accession ID, organism, tissue, treatment, replicate count, and reference genome version. |
| **VII. Defense Trait Data Integrity** | **PASS** | Traits stored in `data/defense_traits/` with source citations; Normalization pipeline documented; Index calculation traceable. |

## Project Structure

### Documentation (this feature)

```text
specs/001-plant-defense-allocation/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ ├── output.schema.yaml
│ └── traits.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│ ├── fetch_gse.py # T011: Download metadata & FASTQs
│ ├── verify_metadata.py # T011a: Validate replicates/tissue (Filter & Continue)
│ ├── preprocess.py # T012: fastp, HISAT2, featureCounts
│ ├── batch_correct.py # T013: ComBat-seq (with Batch-Design Check)
│ ├── traits_fetch.py # T025a/b: TRY, Phenoscape, GBIF
│ ├── merge_traits.py # T025c: Merge traits & FR-011 gate
│ └── phylogeny.py # T028a: Open Tree of Life (No star fallback)
├── analysis/
│ ├── de_analysis.py # T014a: DESeq2, response vectors (Common DE selection)
│ ├── pathway_agg.py # T014b: Pathway Aggregation (Exclude biosynthetic)
│ ├── modeling.py # T038: Elastic Net, RF, Clade-Stratified LOSO
│ ├── validation.py # T040: Permutation, PGLS, Power (Phylogenetic lambda)
│ └── reproducibility.py # T040: Jaccard similarity check (No proxy fallback)
├── utils/
│ ├── config.py # Paths, seeds, thresholds
│ └── logging.py
├── cli/
│ └── run_pipeline.py # Orchestrator
tests/
├── contract/
│ └── test_schemas.py # Validates against contracts/
├── integration/
│ └── test_pipeline.py # End-to-end on synthetic/subset
└── unit/
 └── test_utils.py
```

**Structure Decision**: Single-project structure (`src/`) chosen to minimize overhead for a research pipeline. Data flows from `data/raw/` to `data/processed/` via modular scripts in `src/data/` and `src/analysis/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Clade-Stratified LOSO + Phylogenetic Null** | Required by FR-007, FR-017 to handle non-independence and small sample sizes. Standard LOSO is insufficient if test species is phylogenetically close to training set. | Standard K-fold CV would inflate performance metrics due to phylogenetic relatedness; simple correlation ignores evolutionary history. |
| **ComBat-seq with Batch-Design Check** | Required by FR-003 to correct batch effects in count data while preserving biological variance. ComBat-seq fails if batch == species. | Standard ComBat (limma) assumes normality; RNA-seq count data requires negative binomial handling (ComBat-seq). If confounded, random effects in PGLS are used instead. |
| **Pathway Aggregation (Exclude Biosynthetic)** | Required by FR-012 to Reduce a substantial number of DE genes. to ≤50 features to avoid overfitting (small-n, large-p). Biosynthetic pathways of target traits are excluded to prevent tautology. | Using raw gene counts would lead to singular matrices in regression with <15 species. Using biosynthetic pathways would predict traits using their own expression (leakage). |
| **Bootstrapped CI for LOSO** | Required to address the single-point variance issue of LOSO with N < 15. | A single test point provides no variance estimate; bootstrapping provides a confidence interval on the mean performance. |
| **Median Depth Downsampling** | Required to prevent bias against low-expression species when read depth varies. | Arbitrary sampling (first 1M reads) introduces confounding; median depth ensures equal sequencing effort. |

## Tasks (Critical Path)

- **T011**: Download metadata & FASTQs (NCBI GEO/SRA).
- **T011a**: **Validate & Filter**. Check replicates, tissue, paired herbivore types. **Filter and Continue** (log exclusions in `metadata_verification_report.json`). Do NOT halt on missing data. If <3 valid studies found, halt with "Insufficient Data for Comparative Analysis".
- **T014a**: **DE Analysis**. Run DESeq2. Select **Common DE Genes** via Aggregate Significance within training fold (no leakage). Derive response vector as (Chewing log2FC - Piercing log2FC).
- **T014b**: **Pathway Aggregation**. Map DE genes to KEGG/GO. **Exclude biosynthetic pathways** of target traits (Glucosinolates, Alkaloids, Phenolics). Reduce to ≤50 features.
- **T025a**: **Fetch Traits**. Use ` Name or service not known)"))].
- **T025b**: **Fallback Traits**. Use `pyphenoscape` and `rgbif`.
- **T025c**: **Merge & Gate**. Aggregate traits into `final_aggregated_traits.json`. Calculate Defense Allocation Index. **Halt if >30% missing** (FR-011).
- **T026**: **Power Analysis**. Calculate N_eff using phylogenetic lambda. Halt if insufficient power.
- **T028a**: **Fetch Phylogeny**. Use ` Name or service not known)"))]. **Halt if fetch fails** (No star tree).
- **T038**: **Modeling**. Clade-Stratified LOSO. Bootstrapped CI. Permutation test.
- **T040**: **Reproducibility**. Jaccard similarity against verified lists. **No proxy fallback**.
