# Implementation Plan: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `001-solar-wind-composition-geomagnetic` | **Date**: 2026-10-20 | **Spec**: `specs/001-solar-wind-composition-geomagnetic/spec.md`  
**Input**: Feature specification from `/specs/001-solar-wind-composition-geomagnetic/spec.md`

## Summary
The pipeline must (1) obtain bulk solar‑wind parameters and geomagnetic indices from open sources, (2) generate a deterministic synthetic composition dataset that respects the 2‑hour cadence of ACE SWICS/WIND instruments, (3) align all series to an hourly grid (allowing missing composition values and flagging gaps > 6 h), (4) compute physics‑based coupling functions, (5) fit baseline and full multivariate linear regressions, (6) quantify incremental explanatory power (ΔR²) with 5‑fold time‑series cross‑validation, (7) validate composition coefficients with a 24‑h block permutation test, (8) apply Benjamini‑Hochberg FDR correction, (9) compute VIF for multicollinearity, and (10) produce a consolidated, schema‑validated report. All steps run on the GitHub Actions free‑tier CPU box; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==2.0.*`  
  - `scikit-learn==1.5.*`  
  - `statsmodels==0.14.*`  
  - `scipy==1.14.*`  
  - `pyarrow==15.0.*` (fallback `fastparquet==2024.1.*`)  
  - `tqdm==4.66.*`  
  - `pyyaml==6.0.*`  
- **Storage**: Local CSV/Parquet under `data/` (`raw/`, `processed/`, `artifacts/`).  
- **Testing**: `pytest==8.3.*` (unit & integration).  
- **Target Platform**: GitHub Actions free‑tier (2 CPU, 7 GB RAM, 14 GB disk).  
- **Compute Limits**: ≤ 6 h runtime, ≤ 6 GB RAM, ≤ 200 MB total disk usage.  

## Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic RNG seed, all scripts version‑controlled. |
| II. Verified Accuracy | PASS | No new citations; only verified URLs are used. |
| III. Data Hygiene | PASS | Raw synthetic files are checksummed; every transformation writes a new file. |
| IV. Single Source of Truth | PASS | All figures/tables are generated directly from artifact files. |
| V. Versioning Discipline | PASS | Artifacts referenced by content hash (handled by runtime). |
| VI. Composition Data Integrity | **PENDING AMENDMENT** | Current composition data are synthetic (generated locally). An amendment is required to either (a) allow synthetic data solely for workflow validation, **or** (b) provide an open real composition dataset. Until approved, downstream claims of scientific significance are suppressed. |
| VII. Statistical Validation and Model Transparency | PASS | Full regression, CV, ΔR², permutation test, FDR, VIF are implemented and output reproducible artifacts. Claims of significance are gated behind the Principle VI amendment. |

**Action**: Project lead must approve a scope amendment for Principle VI. Until approval, the pipeline proceeds with synthetic composition only and the final report contains a mandatory disclaimer.

## Project Structure
```text
specs/001-solar-wind-composition-geomagnetic/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── dataset.schema.yaml
└── tasks.md   # generated later

projects/PROJ-505-exploring-the-statistical-relationship-b/
├─ code/
│  ├─ __init__.py
│  ├─ ingestion/
│  │   ├─ generate_synthetic_composition.py   # FR‑001 (synthetic fallback)
│  │   ├─ download_bulk.py                    # FR‑001 (real bulk & indices)
│  │   └─ align.py                            # FR‑003
│  ├─ analysis/
│  │   ├─ coupling_functions.py              # FR‑004
│  │   ├─ regression.py                      # FR‑004, FR‑005, FR‑006, FR‑011
│  │   ├─ cross_validation.py                # FR‑007
│  │   ├─ permutation_test.py                # FR‑008
│  │   └─ sensitivity.py                     # FR‑009, FR‑010
│  ├─ utils/
│  │   ├─ io.py                              # robust CSV/Parquet I/O, fallback loader
│  │   └─ checksum.py                        # SHA‑256 verification
│  └─ main.py                                # Orchestrates the full pipeline
├─ data/
│  ├─ raw/
│  │   ├─ synthetic_composition.parquet      # FR‑001 (synthetic)
│  │   └─ bulk_and_geomagnetic.parquet       # FR‑001 (real bulk + Dst/Kp)
│  ├─ processed/
│  │   ├─ aligned_hourly.parquet
│  │   └─ with_coupling.parquet
│  └─ artifacts/
│      ├─ alignment_report.json
│      ├─ baseline_model.json
│      ├─ full_model.json
│      ├─ delta_r2.json
│      ├─ cv_metrics.json
│      ├─ permutation_results.json
│      ├─ sensitivity.json
│      └─ final_report.json
├─ tests/
│  ├─ unit/
│  │   ├─ test_ingestion.py
│  │   ├─ test_coupling.py
│  │   └─ test_io.py
│  └─ integration/
│      └─ test_full_pipeline.py
├─ requirements.txt
└─ README.md
```

## Phase & Task Breakdown (covers every FR & SC)

| Phase | Script / Command | FR / SC addressed |
|-------|------------------|-------------------|
| **0 Amendment Check** | Manual review of Principle VI amendment status | VI |
| **1 Synthetic Composition Generation** | `python -m code.ingestion.generate_synthetic_composition --seed 42 --output data/raw/synthetic_composition.parquet` | FR‑001 (synthetic fallback) |
| **2 Real Bulk & Geomagnetic Download** | `python -m code.ingestion.download_bulk --start 2000-01-01 --end 2020-12-31 --output data/raw/bulk_and_geomagnetic.parquet` | FR‑001 (bulk & indices) |
| **3 Alignment** | `python -m code.ingestion.align --bulk data/raw/bulk_and_geomagnetic.parquet --composition data/raw/synthetic_composition.parquet --output data/processed/aligned_hourly.parquet --report data/artifacts/alignment_report.json --max_offset 30 --gap_threshold 6` | FR‑003 (hourly median, ≤30 min offset, flag >6 h gaps) |
| **4 Coupling Function Computation** | `python -m code.analysis.coupling_functions --input data/processed/aligned_hourly.parquet --output data/processed/with_coupling.parquet` | FR‑004 |
| **5 Baseline Regression** | `python -m code.analysis.regression --mode baseline --input data/processed/with_coupling.parquet --output data/artifacts/baseline_model.json` | FR‑004, FR‑011 |
| **6 Full Regression** | `python -m code.analysis.regression --mode full --input data/processed/with_coupling.parquet --output data/artifacts/full_model.json` | FR‑005, FR‑006, FR‑011 |
| **7 ΔR² Computation** | `python -m code.analysis.regression --compute-delta --baseline data/artifacts/baseline_model.json --full data/artifacts/full_model.json --output data/artifacts/delta_r2.json` | FR‑006 |
| **8 5‑Fold Cross‑Validation** | `python -m code.analysis.cross_validation --input data/processed/with_coupling.parquet --output data/artifacts/cv_metrics.json` | FR‑007 |
| **9 Block Permutation Test** | `python -m code.analysis.permutation_test --iterations 1000 --block-size 24 --input data/processed/with_coupling.parquet --output data/artifacts/permutation_results.json` | FR‑008 |
| **10 Sensitivity & FDR** | `python -m code.analysis.sensitivity --thresholds 0.01 0.05 0.10 --fdr bh --input data/artifacts/permutation_results.json --output data/artifacts/sensitivity.json` | FR‑009, FR‑010 |
| **11 Reporting** | `python -m code.main` (orchestrates all previous steps, aggregates JSON, produces PNG/PDF figures) | SC‑001 – SC‑004 |
| **12 Verification** | `pytest tests/` | Non‑functional validation (not mapped to a specific FR/SC). |

All tasks are deterministic, produce real files, and are validated against `contracts/dataset.schema.yaml`.

## Data Availability & Limitations
* **Open bulk & geomagnetic sources**:  
  - **ACE (CSV)**: `https://huggingface.co/datasets/ACERobotics/ACE-Data-0/resolve/main/Room-scale/date_to_take_mapping_20261006.csv` (provides hourly solar‑wind bulk parameters).  
  - **NOAA (Parquet)**: `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet` (contains hourly Dst and Kp after preprocessing).  
* **Composition ratios**: No verified open source; synthetic dataset generated locally (see FR‑001 synthetic fallback).  
* When a verified composition source becomes available, replace step 1 with a real download script; the rest of the pipeline remains unchanged.

## Compute Feasibility
* **Memory**: Full 20‑year hourly dataset ≈ 175 k rows × ~20 columns → < 30 MB in memory.  
* **CPU**: Linear regression, VIF, and 1 000 block permutations complete well within the 6 h CI limit on 2 CPU cores.  
* **Disk**: All parquet/JSON artifacts < 200 MB total.  
* **GPU**: Not required.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open composition data | Scientific hypothesis cannot be answered | Use synthetic data for workflow validation; request Principle VI amendment; swap in real data when available. |
| 2‑hour composition cadence → many missing hourly values | Alignment step may produce many `null` entries, potentially reducing statistical power | Alignment script records missing‑value statistics; cross‑validation and permutation tests operate on the available data; power analysis (see research.md) acknowledges reduced effective sample size. |
| Block permutation runtime > 6 h | CI timeout | Minimum 1 000 iterations; early stop when SE < 0.001 (per FR‑008). |
| `pyarrow` missing | Parquet I/O failure | `code.utils.io` falls back to `fastparquet`. |
| Multicollinearity inflates SEs | Misleading significance | VIF computed for all predictors; any VIF ≥ 5 flagged and reported; significance interpreted cautiously. |

## Amendment Dependency
* **If Principle VI amendment is approved**: replace step 1 with a real composition download; final report may claim statistical significance per SC‑001.  
* **If amendment is denied or pending**: pipeline runs with synthetic composition only; final report includes a disclaimer that no real composition measurements were used and no scientific claim about the Sun‑Earth system is made.  

---
