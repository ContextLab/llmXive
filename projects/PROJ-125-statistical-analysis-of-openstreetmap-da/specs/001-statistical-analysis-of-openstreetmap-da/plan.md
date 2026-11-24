# Implementation Plan: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Branch**: `PROJ-125-statistical-analysis-of-openstreetmap-da` | **Date**: 2026-10-21 | **Spec**: `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`
**Input**: Feature specification from `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`

## Summary

The pipeline first verifies that a programmatically downloadable, cloud‑screened Landsat LST product is available (Phase 0). Only after this **data‑availability check** passes will any ingestion, preprocessing, or modeling steps run. If the LST asset is missing, the pipeline aborts with a clear `DATA_GAP` error, satisfying SC‑002. All subsequent phases are **conditionally gated** on successful completion of Phase 0.

The pipeline then ingests verified OpenStreetMap (Geofabrik US PBF) vectors for up to ten configured cities, aligns them with the LST raster on a deterministic 30 m grid, computes exploratory spatial statistics, applies a memory governor, fits spatial regression models (OLS, SAR, GWR) when resources allow, performs spatial 5‑fold cross‑validation, applies permutation‑FDR correction with spatially‑constrained permutations, and conducts sensitivity analyses (GWR bandwidth sweep or OLS coefficient‑stability sweep). Results are written to CSV/JSON artifacts and visualized in a final report.

**Memory‑governor**: `psutil` monitors peak RSS. If usage exceeds **5 GB**, the pipeline degrades to OLS‑only mode (`model_type: OLS_DEGRADED`), logs a bias warning, and continues (FR‑005). If usage exceeds **6 GB**, the run aborts with exit code 99 (SC‑005). The governor runs before model fitting (Phase 5).

**Key revisions**:
- Explicit LST data‑availability gating (Phase 0) and ordering.
- Provisional handling of the Unexplained Variance Gap (FR‑010) – the metric is optional and not required by any contract.
- Spatially‑constrained permutation scheme for FDR correction (FR‑008).
- Heuristic nature of the effective sample size formula `N_eff = N/(1+Moran’s I)` is now documented as a descriptive approximation (not a power analysis).

## Implementation Phases & FR/SC Coverage

| Phase | Tasks | FR IDs | SC IDs | Contract |
|-------|-------|--------|--------|----------|
| **0. Data‑availability & Spec Amendment Check** | Verify presence of LST GeoTIFFs that satisfy FR‑002; if absent, abort with `DATA_GAP`. Also verify that the literature ceiling citation for FR‑010 is a verified reference; if not, flag the metric as provisional. | FR-002, FR-010 | SC-001, SC-002 | — |
| **1. Configuration & scaffolding** | `config.py` (seeds, `CITY_LIST` ≤ 10, `MAX_MEMORY_GB=6`, `DEGRADE_GB=5`, `MAX_SAMPLES=500_000`, tuned `MAX_BLOCKS`), `requirements.txt` pins. | FR-012 | SC-001 | — |
| **2. Data ingestion** | Download city boundaries and OSM vectors from **verified Geofabrik US PBF**. LST ingestion performed by `ingest_lst.py` under the contract defined in Phase 0. Checksums + fetch timestamps recorded in `data/raw/manifest.json`. | FR-001, FR-002, FR-012 | SC-001, SC-002 | `contracts/dataset.schema.yaml` |
| **3. Preprocessing & alignment** | Deterministic UTM CRS selection (EPSG:3857 fallback), 30 m resampling (nearest‑neighbor for categorical rasters, bilinear for continuous), rasterize vectors (mean aggregation), mask LST gaps; log all methods (Principle VI) in `data/processed/alignment_log.json`. | FR-003, FR-011 | SC-001, SC-002 | `contracts/dataset.schema.yaml` |
| **4. Exploratory statistics** | Pearson correlation matrix; Moran’s I per variable (999 permutations) → `data/results/exploratory.csv`. | FR-004 | SC-001 | — |
| **5. Memory governor & sampling** | psutil peak‑RSS monitor; if peak > 5 GB → set `memory_status: DEGRADED`, fit OLS only, log `model_type: OLS_DEGRADED`. If peak > 6 GB → abort with exit 99. Spatial block sampling reduces cells to **N < 500 k**; `MAX_BLOCKS` tuned to keep RSS ≤ 6 GB. | FR-005 (Memory rule) | SC-005 | `contracts/metrics.schema.yaml` |
| **6. Model fitting** | OLS with spatially clustered SE; SAR (spatial lag, `spreg`); GWR (`mgwr`, AICc bandwidth). In degraded mode only OLS is fitted, Moran’s I is still reported, and a bias warning is emitted. | FR-005, FR-007 | SC-001, SC-005 | `contracts/model_output.schema.yaml` |
| **7. Spatial cross‑validation** | 5‑fold spatial block CV (k‑means on coordinates); compute RMSE, MAE, R² per model → `data/results/metrics.csv`. | FR-006, FR-007 | SC-001 | `contracts/model_output.schema.yaml` |
| **8. Multiple‑comparison correction** | Permutation‑FDR (α = 0.05) **using spatially constrained permutations within the CV blocks**; add column `correction_method = "permutation-FDR"`. | FR-008 | SC-003 | `contracts/metrics.schema.yaml` |
| **9. Sensitivity & proxy validity** | GWR bandwidth sweep 50–500 m (step 25) **or** OLS coefficient‑stability sweep over block sizes in degraded mode; generate R²‑vs‑bandwidth (or block‑size) plot; **provisionally** compute Unexplained Variance Gap = 0.68 − Observed_R² (flagged as provisional; a negative gap signals the literature ceiling may be invalid). | FR-009, FR-010 (provisional) | SC-004 | `contracts/model_output.schema.yaml` |
| **10. Reporting & export** | Assemble `metrics.csv`, model JSON, plots, markdown report referencing all artifacts; include caveats about the provisional gap metric and the N_eff heuristic. | FR-004–FR-010 | SC-001, SC-003, SC-004 | `contracts/output.schema.yaml` |
| **11. Quality assurance** | Run `ruff` + `black` on `code/`; store lint report at `data/results/qa/lint_report.txt`. Execute pytest unit tests (`tests/unit/`) and contract tests (`tests/contract/`); store logs at `data/results/qa/test_report.txt`. | FR-005 | SC-001, SC-005 | all contracts |

## Statistical Rigor

- **Multiple comparisons**: permutation‑FDR with **spatially constrained permutations** (Phase 8).  
- **Power / sample size**: report raw `N` and heuristic `N_eff = N/(1+Moran’s I)` **as a descriptive lower‑bound only**; **do not** use it for formal power claims.  
- **Causal framing**: observational, associational design — all results labelled descriptive; degraded‑mode results additionally labelled `descriptive‑only`.  
- **Measurement validity**: LST provenance and cloud‑screening method recorded in `data/raw/manifest.json`; OSM feature definitions recorded per layer.  
- **Collinearity**: correlation matrix and VIF diagnostics reported; coefficients are not interpreted as independent effects when high collinearity is present.

## Compute Feasibility & Strategy (Decision/Rationale)

- **CPU‑first**: all libraries (`statsmodels`, `spreg`, `mgwr`, `esda`) are NumPy‑based and run comfortably on the GitHub Actions free‑tier runner. No GPU escape hatch is required.  
- **Memory governor**: tuned `MAX_BLOCKS` (≈ 250) keeps peak RSS ≤ 5 GB for typical US city extents; fallback to OLS_DEGRADED above 5 GB; hard abort above 6 GB (SC‑005).  
- **Sampling**: spatial block sampling using `MAX_BLOCKS` ensures real data (not synthetic) is used while respecting the 500 k cell limit.  
- **Runtime budget**: per‑city end‑to‑end run expected < 4 h; full 10‑city batch < 6 h.

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds, deterministic downloads, manifest timestamps. |
| II. Verified Accuracy | FLAGGED | FR‑010 ceiling citation and LST source need verified references (see Phase 0). |
| III. Data Hygiene | PASS | Checksums recorded; all transformations write new files. |
| IV. Single Source of Truth | PASS | All numbers trace to rows in `metrics.csv` and JSON model outputs. |
| V. Versioning Discipline | PASS | Artifact hashes updated on each change. |
| VI. Spatial Resolution Integrity | PASS | Reprojection/aggregation methods logged per layer. |
| VII. Proxy Validity Boundaries | PASS | Sensitivity analyses quantify stability; missing‑factor limitations documented. |

## Scope Clarifications

- Phases 1‑10 are **conditionally executed** only after Phase 0 confirms LST availability and a verified R² ceiling. This resolves the previous ordering inconsistency.  
- The Unexplained Variance Gap is reported **provisionally**; a negative gap indicates that the literature ceiling may be invalid, not that the model “exceeds literature”.  

--- 
