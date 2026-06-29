# Implementation Plan: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Branch**: `001-predict-plant-defense` | **Date**: 2026-06-24 | **Spec**: `specs/001-predicting-plant-defense/spec.md`
**Input**: Feature specification from `specs/001-predicting-plant-defense/spec.md`

## Summary

This feature implements a computational pipeline to predict plant defense compound (terpenoid, alkaloid, phenylpropanoid) abundance from gene expression profiles. The pipeline downloads paired transcriptomic data from GEO and metabolomics data from Metabolomics Workbench, performs species-specific normalization and batch correction, selects defense-pathway genes via KEGG mapping, trains Ridge Regression models with 5-fold cross-validation, and conducts permutation testing with Bonferroni correction. All analysis runs on CPU-only GitHub Actions free-tier runners (2 CPU, ~7 GB RAM, ≤4 hours). Species-specific models are primary; cross-species modeling is secondary with documented biological batch assumptions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, scipy, requests, pyyaml, biopython, pykegg (or kggpy), pycombat (combat implementation)  
**Storage**: Local files under `data/`, `logs/`, `outputs/`  
**Testing**: pytest with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational-biology-pipeline  
**Performance Goals**: Complete E2E pipeline within 4 hours CPU time on 2-core, ~7 GB RAM  
**Constraints**: No GPU/CUDA; CPU-only libraries with pre-built wheels; dataset subset to fit 7 GB RAM; no in-place data modification  
**Scale/Scope**: A substantial number of samples (after pairing), numerous defense pathway genes, multiple metabolites

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; external datasets fetched by accession ID; `requirements.txt` pins all dependencies |
| **II. Verified Accuracy** | PASS | All citations validated by Reference-Validator; GEO/Metabolomics Workbench accessions documented with checksums |
| **III. Data Hygiene** | PASS | SHA-256 checksums recorded in `state/`; raw data preserved; derivations produce new files; PII scan enforced |
| **IV. Single Source of Truth** | PASS | All figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed numbers |
| **V. Versioning Discipline** | Content hash | Artifacts carry content hashes; `updated_at` timestamps updated on change |
| **VI. Dataset Version Traceability** | PASS | `data/sources.yaml` documents accession, download date, preprocessing version |
| **VII. Statistical Validation Discipline** | PASS | 5-fold CV (mean ± SD); permutation test ≥1000 iterations; p-value <0.05 required for claims |

**GATE STATUS**: PASS — All 7 principles addressed in design and implementation plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-defense/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── expression-matrix.schema.yaml
│   ├── metabolite-matrix.schema.yaml
│   └── model-artifact.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-503-predicting-plant-defense-compound-produc/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download/
│   │   ├── __init__.py
│   │   ├── geo_downloader.py      # FR-001: GEO expression download
│   │   └── metabolomics_downloader.py  # FR-002: Metabolomics Workbench download
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── normalize.py           # FR-003: TPM/FPKM normalization, log-transform
│   │   ├── feature_selection.py   # FR-004: KEGG pathway filtering
│   │   └── batch_correction.py    # FR-010: z-score, ComBat
│   ├── modeling/
│   │   ├── __init__.py
│   │   ├── ridge_regression.py    # FR-005: Model training, CV
│   │   └── permutation_test.py    # FR-006, FR-007: Permutation + Bonferroni
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── pairing_validator.py   # FR-009: Sample-level pairing check
│   │   └── checksum_validator.py  # SC-004: SHA-256 verification
│   ├── logging/
│   │   ├── __init__.py
│   │   └── runtime_logger.py      # FR-008: Runtime/resource logging
│   └── main.py                    # E2E pipeline orchestration
├── data/
│   ├── raw/
│   │   ├── geo/                   # Raw GEO downloads
│   │   └── metabolomics/          # Raw Metabolomics Workbench downloads
│   ├── processed/
│   │   ├── expression_matrix.csv  # Normalized, filtered
│   │   ├── metabolite_matrix.csv  # Log-transformed, paired
│   │   └── feature_set.csv        # Defense pathway genes only
│   └── sources.yaml               # VI: Dataset version traceability
├── logs/
│   ├── data_pairing.json          # Edge case: unmatched samples
│   └── feature_filtering.csv      # Edge case: zero-variance genes
├── outputs/
│   ├── model_artifact.pkl         # FR-005: Serialized model
│   ├── cv_metrics.csv             # FR-005: RMSE, Pearson r per metabolite
│   └── permutation_results.csv    # FR-006, FR-007: p-values, corrected
├── tests/
│   ├── contract/
│   │   ├── test_expression_schema.py
│   │   ├── test_metabolite_schema.py
│   │   └── test_model_artifact_schema.py
│   ├── unit/
│   └── integration/
└── docs/
    └── edge_cases.md              # Edge case documentation
```

**Structure Decision**: Single project structure under `code/` with modular subpackages. This minimizes overhead for CI and keeps the pipeline cohesive for reproducibility (Constitution I).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Species-specific z-score + ComBat (FR-010) | Arabidopsis and Solanum have different expression baselines; cross-species modeling requires batch correction | Direct pooling without correction would introduce systematic bias between species |
| Permutation test + Bonferroni (FR-006, FR-007) | Multiple metabolites tested; family-wise error control required for statistical validity | Uncorrected p-values would inflate Type I error across metabolite tests |
| Sample-level pairing validation (FR-009) | Expression and metabolite data must come from the same biological sample, not just same condition | Condition-level pairing risks mixing biological replicates with different genotypes/treatments |

## FR/SC Coverage Map

| Requirement | Plan Phase | Implementation Artifact | Notes |
|-------------|------------|------------------------|-------|
| FR-001: GEO download | Phase 1 (Data Acquisition) | `code/download/geo_downloader.py` | Specific GEO series IDs documented in data/sources.yaml |
| FR-002: Metabolomics download | Phase 1 (Data Acquisition) | `code/download/metabolomics_downloader.py` | Specific MW experiment IDs documented in data/sources.yaml |
| FR-003: Normalize + variance filter | Phase 2 (Preprocessing) | `code/preprocessing/normalize.py` | TPM/FPKM, log2(x+1), variance <1e-10 filter |
| FR-004: KEGG pathway selection | Phase 2 (Preprocessing) | `code/preprocessing/feature_selection.py` | terpenoid, alkaloid, phenylpropanoid pathways |
| FR-005: Ridge Regression + CV | Phase 3 (Modeling) | `code/modeling/ridge_regression.py` | 5-fold CV, RMSE and Pearson r per metabolite |
| FR-006: Permutation test | Phase 3 (Modeling) | `code/modeling/permutation_test.py` | 1000 iterations, two-sided p-value |
| FR-007: Bonferroni correction | Phase 3 (Modeling) | `code/modeling/permutation_test.py` (post-processing) | Applied across all metabolites tested |
| FR-008: Runtime logging + abort | Phase 4 (Orchestration) | `code/logging/runtime_logger.py` | Abort if >4 hours CPU time |
| FR-009: Pairing validation | Phase 1 (Data Acquisition) | `code/validation/pairing_validator.py` | Halt if <95% samples paired (E-PAIRING) |
| FR-010: Species z-score + ComBat | Phase 2 (Preprocessing) | `code/preprocessing/batch_correction.py` | **Note**: Species differences are biological, not technical; species-specific models are primary |
| SC-001: Pearson r ≥ 0.5 | Phase 3 (Evaluation) | `outputs/cv_metrics.csv` | Target for best performing metabolite; report achieved correlation |
| SC-002: Permutation p ≤ 0.05 | Phase 3 (Evaluation) | `outputs/permutation_results.csv` | Bonferroni-corrected for best performing metabolite |
| SC-003: ≤4 hours runtime | Phase 4 (Orchestration) | `code/logging/runtime_logger.py` (abort logic) | GitHub Actions free-tier constraint |
| SC-004: SHA-256 ≥ 99% match | Phase 1 (Data Acquisition) | `code/validation/checksum_validator.py` | All raw files in data/raw/ |
| SC-005: ≥95% sample pairing | Phase 1 (Data Acquisition) | `code/validation/pairing_validator.py` (E-PAIRING error) | sample_id must appear in both ExpressionMatrix and MetaboliteMatrix |
| SC-006: ≥75% pathway genes retained | Phase 2 (Preprocessing) | `logs/feature_filtering.csv` (retention count) | terpenoid (ko00900), alkaloid (ko00901), phenylpropanoid (ko00940) |

## Compute Feasibility

- **CPU-only**: All libraries (`scikit-learn`, `scipy`, `pandas`) have CPU wheels; no CUDA/bitsandbytes dependencies
- **Memory**: 500 samples × 2000 genes × 8 bytes = 8 MB for expression matrix; total including metadata, metabolite matrix, and ComBat overhead ≈ 2-4 GB (not <2 GB as previously estimated)
- **Disk**: Raw downloads ~500 MB; processed files ~50 MB; total < 14 GB limit
- **Runtime**: 5-fold CV on 2000 genes × 500 samples ≈ 5-10 minutes; 1000 permutations ≈ 30-60 minutes; total < 2 hours with margin
- **Fallback strategy**: If dataset size exceeds limits, implement streaming/chunked processing or sample to 300 samples

## Computational Task Ordering

1. **Phase 1**: Download GEO + Metabolomics data (FR-001, FR-002) → Validate checksums (SC-004) → Validate pairing (FR-009)
2. **Phase 2**: Normalize expression (FR-003) → Select features (FR-004) → Species-specific batch correction (FR-010)
3. **Phase 3a**: Train species-specific Ridge models (Arabidopsis only, Solanum only)
4. **Phase 3b**: Train cross-species Ridge model (with ComBat correction)
5. **Phase 3c**: Compare species-specific vs cross-species performance; document generalizability
6. **Phase 3d**: Permutation test (FR-006) → Bonferroni correction (FR-007)
7. **Phase 4**: Log runtime (FR-008) → Generate outputs (SC-001, SC-002, SC-003, SC-005, SC-006)

## Constitution Check (Post-Design)

*Re-check after Phase 1 design to verify dataset availability.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Reproducibility** | PASS | Seeds pinned; accession IDs documented; requirements pinned |
| **II. Verified Accuracy** | PASS | GEO/MW accessions validated; checksums recorded |
| **III. Data Hygiene** | PASS | SHA-256 hashes; raw data preserved |
| **IV. Single Source of Truth** | PASS | All outputs trace to data/ and code/ |
| **V. Versioning Discipline** | Content hash | Artifacts carry content hashes |
| **VI. Dataset Version Traceability** | PASS | data/sources.yaml documents all accessions |
| **VII. Statistical Validation Discipline** | PASS | 5-fold CV; 1000 permutation iterations; Bonferroni correction |

**GATE STATUS**: PASS — All principles addressed; dataset feasibility confirmed in research.md.