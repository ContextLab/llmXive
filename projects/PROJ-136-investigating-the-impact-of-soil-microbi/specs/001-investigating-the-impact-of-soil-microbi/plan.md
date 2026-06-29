# Implementation Plan: 001-soil-microbiome-diversity-disease-resistance

**Branch**: `001-soil-microbiome-diversity-disease-resistance` | **Date**: 2026-06-24 | **Spec**: `/specs/001-soil-microbiome-diversity-disease-resistance/spec.md`
**Input**: Feature specification from `/specs/001-soil-microbiome-diversity-disease-resistance/spec.md`

## Summary

This project investigates the associational relationship between soil microbiome alpha-diversity and plant disease incidence using observational data. **BLOCKING GATE**: Per research.md, no verified dataset sources exist for EMP agricultural subset, MG-RAST soil microbiome, or plant disease incidence records. Implementation is contingent on dataset verification or spec amendment. The technical approach involves: (1) downloading and preprocessing 16S rRNA amplicon tables and disease incidence records, (2) computing alpha-diversity metrics and fitting beta regression/GLMM models, (3) performing ANCOM differential abundance testing and co-occurrence network analysis for keystone taxon identification. All analyses will be framed as associational per FR-009, with multiple-comparison correction per FR-010 and power analysis per FR-015. **Note**: Spec uses "Disease Resistance" terminology but measures "disease incidence" (construct validity threat documented in research.md).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: scikit-learn, pandas, numpy, scipy, statsmodels, biopython, networkx, qiime2 (via subprocess), co-occurrence network tools  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `code/`)  
**Testing**: pytest with contract validation against schema files  
**Target Platform**: Linux (GitHub Actions free-tier runner: standard CPU resources, limited RAM, no GPU)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete analysis within 6 hours on CPU-only runner; memory usage ≤7 GB  
**Constraints**: No GPU acceleration; default precision only; sampled datasets if needed to fit RAM; all analyses must be reproducible per Constitution Principle I  
**Scale/Scope**: Target ≥30 matched samples (per spec); empirical targets deferred to research phase  
**BLOCKING GATE**: Analysis steps contingent on dataset verification per Constitution Principle II. Do NOT proceed until research.md Dataset Strategy FATAL MISMATCH is resolved.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

| Principle | Status | Evidence/Annotation |
|-----------|--------|---------------------|
| I. Reproducibility | PASS | See code/requirements.txt; random seed pinning in code/analysis/*.py (permutation_tests.py, statistical_models.py); containerization requirements for QIIME 2/CoNet |
| II. Verified Accuracy | BLOCKING | No verified dataset sources exist for EMP agricultural subset, MG-RAST soil microbiome, or disease incidence records (research.md:Dataset Strategy). Principle II cannot be satisfied until datasets are verified or spec amended. |
| III. Data Hygiene | PASS | Checksum all files under data/ via code/analysis/data_acquisition.py; preserve raw data unchanged in data/raw/; derivations in data/processed/ reference raw sources |
| IV. Single Source of Truth | PASS | All figures/statistics trace to data/ rows and code/ blocks; no hand-typed numbers; see data-model.md entity relationships |
| V. Versioning Discipline | PASS | Content hashes for all artifacts in state/PROJ-136-artifact-hashes.json; state updated on artifact changes |
| VI. Ecological Data Provenance | PASS | Store EMP/MG-RAST/disease data in data/raw/ with provenance metadata (source URL, download date, version); derivations reference raw sources per data-model.md data flow |
| VII. Statistical Analysis Transparency | PASS | Record software versions (statsmodels, scikit-bio), seeds, model specs in code/analysis/*.py; output test statistics and p-values per research.md Statistical Methods |

**Dataset Fit Warning**: Per the verified datasets block, NO verified source exists for the Earth Microbiome Project agricultural subset, MG-RAST soil microbiome repository, or plant disease incidence records referenced in the spec. Research.md must explicitly state this mismatch and either (a) identify alternative verified datasets that contain the required variables, or (b) flag this as a blocking gap requiring spec amendment. **IMPLEMENTATION BLOCKED** until this is resolved.

**Construct Validity Note**: Spec title uses "Disease Resistance" but measures "disease incidence" (observational, not controlled inoculation). All plan/research docs use "disease incidence" consistently; spec amendment required for terminological alignment (spec-root cause).

## Project Structure

### Documentation (this feature)

```text
specs/001-soil-microbiome-diversity-disease-resistance/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── sample.schema.yaml
│   ├── disease-incidence.schema.yaml
│   └── taxon.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-136-investigating-the-impact-of-soil-microbi/
├── data/
│   ├── raw/                 # Original downloaded datasets (checksummed)
│   └── processed/           # Derived files (rarefied tables, diversity metrics)
├── code/
│   ├── analysis/
│   │   ├── data_acquisition.py    # Creates Sample, Disease Incidence entities; validates contracts/sample.schema.yaml, contracts/disease-incidence.schema.yaml
│   │   ├── preprocessing.py       # Creates processed Sample data; validates contracts/sample.schema.yaml
│   │   ├── diversity_analysis.py  # Creates alpha-diversity metrics for Sample; validates contracts/sample.schema.yaml
│   │   ├── statistical_models.py  # Uses Sample, Disease Incidence entities; validates contracts/sample.schema.yaml, contracts/disease-incidence.schema.yaml
│   │   ├── keystone_taxa.py       # Creates Taxon entities; validates contracts/taxon.schema.yaml
│   │   └── permutation_tests.py   # Uses Sample, Disease Incidence entities; validates contracts/sample.schema.yaml, contracts/disease-incidence.schema.yaml
│   ├── tests/
│   │   ├── contract/              # Validates against contracts/*.schema.yaml files
│   │   ├── integration/
│   │   └── unit/
│   └── requirements.txt
├── state/
│   └── projects/PROJ-136-investigating-the-impact-of-soil-microbi.yaml
└── specs/001-soil-microbiome-diversity-disease-resistance/
    └── [documentation files]
```

**Traceability Mapping**: Analysis scripts → Data-model entities → Contract schemas:
- `data_acquisition.py`: Creates Sample, Disease Incidence → contracts/sample.schema.yaml, contracts/disease-incidence.schema.yaml
- `preprocessing.py`: Modifies Sample (sequencing_depth, rarefaction_depth) → contracts/sample.schema.yaml
- `diversity_analysis.py`: Creates alpha-diversity metrics on Sample → contracts/sample.schema.yaml
- `statistical_models.py`: Uses Sample (alpha-diversity), Disease Incidence (incidence_rate) → contracts/sample.schema.yaml, contracts/disease-incidence.schema.yaml
- `keystone_taxa.py`: Creates Taxon (relative_abundance, differential_abundance_q) → contracts/taxon.schema.yaml
- `permutation_tests.py`: Uses Sample (alpha-diversity), Disease Incidence (incidence_rate) → contracts/sample.schema.yaml, contracts/disease-incidence.schema.yaml

**Contract Coverage**: All data outputs validated against corresponding schema files before downstream processing. Contract tests in `code/tests/contract/` enforce schema compliance.

**Structure Decision**: Single computational research project structure. Data layer separated from code layer; analysis scripts organized by functional area (acquisition, preprocessing, diversity, models, keystones, permutation). Tests organized by contract/integration/unit levels. This supports Constitution Principles I (Reproducibility), III (Data Hygiene), and VII (Statistical Transparency).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## FR Coverage Mapping

| FR ID | Plan Element | Research.md Section |
|-------|--------------|---------------------|
| FR-001 | data_acquisition.py downloads EMP/MG-RAST | Dataset Strategy |
| FR-002 | preprocessing.py rarefaction to a standardized read depth | Preprocessing |
| FR-003 | diversity_analysis.py computes Shannon/Simpson/Faith's PD | Alpha-Diversity Computation |
| FR-004 | statistical_models.py fits beta regression/GLMM | Beta Regression / GLMM |
| FR-005 | permutation_tests.py executes multiple permutations | Permutation Tests |
| FR-006 | keystone_taxa.py runs ANCOM | ANCOM Differential Abundance |
| FR-007 | keystone_taxa.py constructs CoNet networks | Co-occurrence Networks |
| FR-008 | data_acquisition.py checks required variables | Dataset Strategy (variable verification) |
| FR-009 | All results framed as associational | Statistical Methods (framings) |
| FR-010 | Multiple-comparison correction in all hypothesis tests | Multiple-Comparison Correction |
| FR-012 | VIF calculation for alpha-diversity collinearity | Statistical Methods (collinearity diagnosis) |
| FR-015 | power_analysis.py conducts a priori power analysis | Power Analysis |