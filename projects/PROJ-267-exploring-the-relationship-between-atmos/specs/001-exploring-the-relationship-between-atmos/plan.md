# Implementation Plan: Atmospheric River Gravity Correlation

**Branch**: `001-atmospheric-river-gravity` | **Date**: 2026-06-28 | **Spec**: `specs/001-exploring-the-relationship-between-atmos/spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-relationship-between-atmos/spec.md`

## Summary

This feature implements statistical correlation analysis between Atmospheric River (AR) intensity metrics (from NOAA CPC Atmospheric River Catalog) and regional gravity anomalies (from GRACE-FO Level-2 mascon solutions) over the West Coast North America region (35°N-50°N, 120°W-125°W). The technical approach uses Pearson correlation with bootstrap resampling (1000 iterations, seed=42), multiple-comparison correction (Bonferroni or FDR), and control region validation to distinguish signal from noise. All findings are framed as associational per FR-007.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml  
**Storage**: Local files under `data/` (CSV, PNG outputs); no database required  
**Testing**: pytest with contract validation against `contracts/` schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete analysis within 6 hours on 2 CPU cores, 7 GB RAM (SC-004)  
**Constraints**: No GPU/CUDA; CPU-tractable methods only; monthly temporal resolution  
**Scale/Scope**: Single regional time-series analysis (maximum available GRACE-FO data from the mission launch date to present)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Reference |
|-----------|--------|--------------------------|
| I. Reproducibility | PASS | Random seeds pinned (seed=42); external datasets fetched from canonical sources; `requirements.txt` pins all dependencies |
| II. Verified Accuracy | PENDING VERIFICATION | Reference-Validator Agent must verify dataset URLs before Phase 0 begins; research.md currently shows NO VERIFIED SOURCE URL status |
| III. Data Hygiene | PASS | Checksums recorded in `state/`; raw data preserved; derivations written to new files; PII scan enforced |
| IV. Single Source of Truth | PASS | All figures/statistics trace to one row in `data/` and one block in `code/` |
| V. Versioning Discipline | PASS | Content hashes for all artifacts; `updated_at` timestamp in `state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` updated on changes |
| VI. Satellite and Atmospheric Data Integrity | PASS | Data downloaded from NOAA CPC and CSR/JPL GRACE-FO official repositories; preprocessing steps version-controlled with logged parameters |
| VII. Statistical Validation Rigor | KNOWN SPEC CONTRADICTION | Spec contains internal contradiction (cites 'Pearson > 0.5' while stating thresholds MUST NOT be pre-specified). Implementation follows power-justified approach (bootstrap CIs, no pre-specified effect size threshold). Flagged for kickback to spec author. |

**Known Spec Contradiction (Principle VII)**: The spec text states "Pearson correlation coefficient > 0.5" as an example while simultaneously stating "thresholds MUST NOT be pre-specified as success criteria before analysis." This creates circular validation risk. Plan documents this contradiction and implements the power-justified approach instead (bootstrap CIs, no pre-specified effect size).

## Project Structure

### Documentation (this feature)

```text
specs/001-atmospheric-river-gravity/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-267-exploring-the-relationship-between-atmos/
├── data/
│   ├── raw/
│   │   └── grace-fo/
│   │   └── noaa-ar/
│   └── processed/
│       └── merged_monthly.csv
├── code/
│   ├── requirements.txt
│   ├── 01_data_ingestion.py
│   ├── 02_preprocessing.py
│   ├── 03_correlation_analysis.py
│   ├── 04_visualization.py
│   └── 05_sensitivity_report.py
├── tests/
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_pipeline.py
├── state/
│   └── projects/PROJ-267-exploring-the-relationship-between-atmos.yaml
└── docs/
    └── methodology.md
```

**Structure Decision**: Single computational research pipeline with modular Python scripts. This structure supports reproducibility (Principle I), data hygiene (Principle III), and single source of truth (Principle IV) by keeping raw data separate from processed data and version-controlling all transformation scripts.

## Phase Mapping to FR/SC Coverage

| Phase | FR Coverage | SC Coverage | Description |
|-------|-------------|-------------|-------------|
| Phase 0: Data Ingestion | FR-001, FR-002 | SC-001 | Download GRACE-FO mascon and NOAA AR catalog data; verify ≥90% completeness; ingest Gravity Anomaly and AR Event entities |
| Phase 1: Preprocessing | FR-003 | SC-001 | Apply degree-1 correction, C20 replacement, Gaussian smoothing at an appropriate spatial scale; monthly aggregation; transform to Gravity Anomaly entity |
| Phase 2: Correlation Analysis | FR-004, FR-005, FR-008 | SC-002 | Compute Pearson correlations across multiple lags; apply multiple-comparison correction; validate against control regions; apply autocorrelation correction (pre-whitening, effective sample size, Newey-West SE); compare signal to GRACE-FO noise floor (≥3σ threshold); generate Correlation Result entities with region_type field |
| Phase 3: Sensitivity Analysis | FR-006, FR-009 | SC-003 | Sweep thresholds across a range of candidate values; document temporal aggregation bias; report confounder sensitivity |
| Phase 4: Visualization & Reporting | FR-007 | SC-004 | Generate plots; ensure no causal language; complete within 6h runtime |

## FR/SC Traceability Matrix

| ID | Description | Plan Phase | Implementation Artifact |
|----|-------------|------------|------------------------|
| FR-001 | Ingest GRACE-FO Level-2 mascon (≥90% completeness) | Phase 0 | `01_data_ingestion.py`; Gravity Anomaly entity |
| FR-002 | Ingest NOAA AR catalog; aggregate to monthly | Phase 0 | `01_data_ingestion.py`; AR Event entity |
| FR-003 | GRACE-FO preprocessing (degree-1, C20, 300km smoothing) | Phase 1 | `02_preprocessing.py`; Gravity Anomaly entity |
| FR-004 | Pearson correlation across lags 0-3; bootstrap 95% CI; signal vs noise floor (≥3σ) | Phase 2 | `03_correlation_analysis.py`; Correlation Result entity |
| FR-005 | Multiple-comparison correction (Bonferroni/FDR) | Phase 2 | `03_correlation_analysis.py`; Correlation Result entity |
| FR-006 | Sensitivity analysis (thresholds 0.4, 0.5, 0.6) | Phase 3 | `05_sensitivity_report.py` |
| FR-007 | No causal language in outputs | Phase 4 | Output validation checks |
| FR-008 | Control region validation | Phase 2 | `03_correlation_analysis.py`; Correlation Result entity with region_type field |
| FR-009 | Temporal aggregation bias documentation | Phase 3 | `05_sensitivity_report.py` |
| SC-001 | ≥90% data completeness | Phase 0 | Completeness check in `01_data_ingestion.py` |
| SC-002 | p < 0.05 after correction | Phase 2 | Significance flagging in `03_correlation_analysis.py` |
| SC-003 | Threshold set {0.4, 0.5, 0.6} coverage | Phase 3 | Sensitivity sweep in `05_sensitivity_report.py` |
| SC-004 | Runtime ≤6h on 2 CPU, 7 GB RAM | All phases | CPU-tractable methods; sampled data if needed |

## Computational Feasibility

| Resource | Constraint | Mitigation Strategy |
|----------|------------|---------------------|
| CPU | 2 cores | Use vectorized numpy operations; avoid parallelization overhead |
| RAM | 7 GB | Subset data to study region; process in chunks if needed |
| Disk | 14 GB | Store only processed CSV; delete raw downloads after checksum |
| Runtime | 6 hours | Bootstrap A sufficient number of iterations is feasible on CPU; correlation is O(n); autocorrelation correction adds minimal overhead |
| GPU | Not available | Use scipy/statsmodels CPU-only methods; no deep learning |

## Data Model References

All phases reference entity definitions from `data-model.md`:
- **AR Event**: Ingested in Phase 0, aggregated to monthly in Phase 1
- **Gravity Anomaly**: Ingested in Phase 0, preprocessed in Phase 1
- **Correlation Result**: Generated in Phase 2, includes region_type field for target/control distinction

## Autocorrelation Correction (Methodology Update)

Per scientific soundness concern, Phase 2 implements autocorrelation correction:
1. **Pre-whitening**: Fit AR(1) model to time series, use residuals for correlation
2. **Effective sample size**: n_eff = n × (1-ρ)/(1+ρ) where ρ is lag-1 autocorrelation
3. **Robust standard errors**: Newey-West adjustment for p-value computation

This addresses temporal autocorrelation in monthly time series data that would otherwise inflate Type I error rates.