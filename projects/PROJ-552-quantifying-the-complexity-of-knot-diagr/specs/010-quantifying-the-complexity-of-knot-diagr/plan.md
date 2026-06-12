# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `/specs/001-knot-complexity-analysis/spec.md`

## Summary

This feature implements computational analysis of knot diagram complexity by downloading prime knot data from Knot Atlas, validating data consistency for core invariants (crossing number, braid index), fitting regression models to assess relationships with hyperbolic volume, and documenting all transformations for reproducibility. Phase 1 focuses on validated crossing number ≤10 data with full data availability through crossing number ≤13 (total prime knots with crossing number 1-13: the established count per OEIS A002863).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, matplotlib, seaborn, requests, pyyaml, jsonschema, arxiv  
**Storage**: Local files under `data/` directory (parquet/CSV formats), no database  
**Testing**: pytest with contract tests for schema validation  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete pipeline execution within standard CI job budget (within acceptable duration)  
**Constraints**: Data download must handle API failures with exponential backoff; all transformations must be reproducible with pinned random seeds  
**Scale/Scope**: Dataset contains a comprehensive set of prime knots with crossing number ≤13 (source: OEIS A002863, https://oeis.org/A002863)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Traceability Annotation |
|-----------|-------------------|------------------------|
| I. Reproducibility | COMPLIANT | Random seeds pinned in `code/src/analysis.py` and `code/src/reproducibility.py`; external datasets fetched from canonical source on every run via `code/src/download.py`; `requirements.txt` at `code/` pins all dependencies |
| II. Verified Accuracy | COMPLIANT | Reference-Validator Agent verifies all external citations before implementation; title-token-overlap ≥0.7 required before review points awarded; verification logs stored in `docs/reproducibility/validation_reports/` |
| III. Data Hygiene | COMPLIANT | All files under `data/` checksummed (SHA-256) via `code/src/reproducibility.py`; no in-place modifications; every transformation produces new file with documented derivation; Implementation: `code/src/reproducibility.py` writes checksums to `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml artifact_hashes` map |
| IV. Single Source of Truth | COMPLIANT | Every figure/statistic traces back to exactly one row in `data/` and one block in `code/` via `code/src/reproducibility.py` derivation tracking; derived numbers not hand-typed; traceability enforced via JSON schema validation in `contracts/` |
| V. Versioning Discipline | COMPLIANT | Every artifact carries content hash via `code/src/reproducibility.py`; Advancement-Evaluator Agent invalidates stale review records when hashed artifact changes; `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml updated_at` timestamp updated on artifact change |
| VI. Mathematical Invariant Consistency | COMPLIANT | All computed knot invariants verified against established definitions from primary mathematical literature; discrepancies documented with derivation notes in `data/`; validation against KnotInfo for hyperbolic volume per FR-013 |
| VII. Statistical Significance Thresholds | COMPLIANT | All statistical claims include explicit significance thresholds (p-values, confidence intervals) and effect size measures; both Pearson and Spearman reported where distribution assumptions uncertain per FR-006; p-values explicitly marked as 'not applicable for census data' in all outputs |

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── knot_record.schema.yaml
│   ├── regression_model.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/                  # Downloaded Knot Atlas data (unchanged)
│   ├── processed/            # Cleaned/derived datasets
│   └── plots/                # Exploratory analysis figures (PNG)
├── src/
│   ├── download.py           # Knot Atlas data download with retry logic
│   ├── clean.py              # Data parsing and cleaning
│   ├── invariants.py         # Invariant computation (Phase 2+)
│   ├── analysis.py           # Regression and statistical tests
│   └── reproducibility.py    # Checksums, logs, derivation notes, state YAML updates
├── tests/
│   ├── contract/             # Schema validation tests
│   ├── integration/          # Pipeline integration tests
│   └── unit/                 # Unit tests for individual functions
├── docs/
│   └── reproducibility/      # Checksums, logs, derivation notes, validation reports
├── requirements.txt          # Pinned Python dependencies
└── README.md                 # Project overview and execution instructions
```

**Structure Decision**: Single project structure with clear separation between data download, cleaning, analysis, and reproducibility modules. This aligns with Constitution Principle I (Reproducibility) by keeping all code under `code/` and all data under `data/`.

## Complexity Tracking

No complexity violations identified. Single-project structure is appropriate for this computational research pipeline.

**Dataset Verification**: OEIS A002863 (https://oeis.org/A002863) has been verified by the Reference-Validator Agent against primary source before implementation. Title-token-overlap ≥0.7 confirmed. Dataset contains all known prime knots with crossing number ≤13 (complete set)..

## Transformation Pipeline

### Step 1: Data Download
- **Input**: Knot Atlas web API
- **Output**: `data/raw/knot_atlas_raw.parquet`
- **Transformation**: Web scraping with exponential backoff retry logic
- **Validation**: Checksum recorded, null percentage computed

### Step 1.5: Validation Status Assignment
- **Input**: `data/raw/knot_atlas_raw.parquet`
- **Output**: `data/processed/knot_records_clean.parquet` with `validation_status` field populated
- **Transformation**: Assign `validation_status` based on crossing number range:
  - `validated` for crossing number ≤10 (SC-001 primary scope)
  - `exploratory` for crossing number 11-13 (SC-001 secondary scope)
- **Validation**: Map to SC-001 validation scope; document in `docs/reproducibility/validation_scope.md` with explicit linkage to crossing number ranges and completeness criteria
- **Documentation**: `validation_status` field connects directly to SC-001 validation scope documentation; all analysis using `exploratory` data must be flagged in final reports per FR-001
- **Data Filtering Enforcement**: Analysis scripts MUST accept `--validated-only` flag that strictly enforces `crossing_number <= 10` filter before any statistical computation. When `--validated-only` is set, any record with `validation_status = 'exploratory'` is silently excluded from all statistical analysis. This prevents cross-contamination between validated and exploratory data.

### Step 2: Data Cleaning
- **Input**: `data/raw/knot_atlas_raw.parquet`
- **Output**: `data/processed/knot_records_clean.parquet`
- **Transformation**: Parse, clean, flag quality issues, apply tie-breaking rules
- **Validation**: Format validation, duplicate detection, null percentage <1% (crossing number, hyperbolic volume); braid index threshold <5% for tabulated values with algorithmic computation fallback documented

### Step 3: Invariant Computation (Phase 2+)
- **Input**: `data/processed/knot_records_clean.parquet`
- **Output**: `data/processed/invariants_computed.parquet`
- **Transformation**: Compute arc index, Seifert circle count, bridge number from available representations
- **Validation**: Algorithm validation against KnotInfo with ≥90% match threshold; Seifert circle computation per math/0303273 (https://arxiv.org/abs/math/0303273); bridge number via Schubert's bridge decomposition (2-bridge knot, https://en.wikipedia.org/wiki/2-bridge_knot)

### Step 4: Regression Analysis
- **Input**: `data/processed/invariants_computed.parquet` (or clean dataset for Phase 1)
- **Output**: `data/processed/regression_results.json`
- **Transformation**: Fit linear, polynomial, logarithmic models; compute goodness-of-fit metrics
- **Validation**: VIF assessment, residual analysis for outlier families; census_data_flag set to true in all outputs with explicit p-value disclaimers

### Step 5: Reproducibility Documentation
- **Input**: All data files and transformation outputs
- **Output**: `docs/reproducibility/` directory with checksums, logs, derivation notes
- **Transformation**: Generate SHA-256 checksums, timestamped logs, derivation notes
- **Validation**: Independent reproducibility check