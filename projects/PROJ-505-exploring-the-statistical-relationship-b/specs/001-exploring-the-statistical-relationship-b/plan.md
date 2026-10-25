# Implementation Plan: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `001-solar-wind-composition-geomagnetic` | **Date**: 2026-10-24 | **Spec**: `specs/001-solar-wind-composition-geomagnetic/spec.md`  
**Input**: Feature specification from `/specs/001-solar-wind-composition-geomagnetic/spec.md`

## Summary
The pipeline must (1) download open‑source bulk solar‑wind parameters (ACE) and geomagnetic indices (NOAA), (2) **optionally** generate a deterministic synthetic composition dataset **solely for workflow validation** (real composition is unavailable in open repositories), (3) align all series to an hourly grid using median aggregation (allowing `null` for composition when the 2‑hour cadence yields gaps), (4) compute physics‑based coupling functions, (5) fit a baseline multivariate linear regression, (6) **if** real composition data become available **and** Principle VI is formally amended, then fit the full model, compute incremental ΔR², perform 5‑fold cross‑validation, validate coefficients with a 24‑hour block permutation test, apply Benjamini‑Hochberg FDR correction, and compute VIF. All steps run on the GitHub Actions free‑tier CPU box; no GPU is required.

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
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic RNG seeds, all scripts version‑controlled. |
| II. Verified Accuracy | PASS | Only the two open datasets (ACE bulk CSV, NOAA Parquet) are cited; their URLs appear in the verified list. |
| III. Data Hygiene | PASS | Raw files are stored unchanged under `data/raw/`; SHA‑256 checksums recorded in `data/raw/checksums.yaml`. |
| IV. Single Source of Truth | PASS | Every figure/table is generated directly from the JSON artifacts produced by the pipeline. |
| V. Versioning Discipline | PASS | Artifact filenames include content hashes; the runtime records hashes in the project state file. |
| VI. Composition Data Integrity | **BLOCKED – amendment required** | No open ACE SWICS or WIND composition source exists. The pipeline can use a **synthetic** composition dataset **only for workflow validation**. **If Principle VI is not formally amended, the pipeline aborts before any composition‑dependent analysis** (full model, ΔR², permutation, sensitivity). |
| VII. Statistical Validation and Model Transparency | PASS (conditional) | All required models, cross‑validation, ΔR², permutation tests, FDR, and VIF are implemented and will be executed **only if** real composition data are present **and** Principle VI is amended. |

**Action**: The project lead must approve an amendment to Principle VI permitting synthetic composition **solely for workflow validation**. Until that amendment is recorded, steps that depend on composition (full model, ΔR², permutation, sensitivity) are **skipped**, and the final report will note the limitation.

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
│  │   ├─ generate_synthetic_composition.py   # FR‑001 (synthetic fallback, validation only)
│  │   ├─ download_bulk.py                    # FR‑001 (real bulk) & FR‑002 (geomagnetic)
│  │   └─ align.py                            # FR‑003
│  ├─ analysis/
│  │   ├─ coupling_functions.py              # FR‑004
│  │   ├─ regression.py                      # FR‑004, FR‑005, FR‑006, FR‑011 (conditional)
│  │   ├─ cross_validation.py                # FR‑007
│  │   ├─ permutation_test.py                # FR‑008 (conditional)
│  │   └─ sensitivity.py                     # FR‑009, FR‑010 (conditional)
│  ├─ utils/
│  │   ├─ io.py                              # robust CSV/Parquet I/O, fallback loader
│  │   └─ checksum.py                        # SHA‑256 verification
│  └─ main.py                                # Orchestrates the full pipeline, checks Principle VI
├─ data/
│  ├─ raw/
│  │   ├─ ace_bulk.csv                        # FR‑001 (real bulk)
│  │   ├─ noaa_geomagnetic.parquet            # FR‑002 (real indices)
│  │   └─ synthetic_composition.parquet       # FR‑001 (synthetic, validation only)
│  │   └─ checksums.yaml                      # hashes of the three raw files
│  ├─ processed/
│  │   ├─ aligned_hourly.parquet
│  │   └─ with_coupling.parquet
│  └─ artifacts/
│      ├─ alignment_report.json
│      ├─ baseline_model.json
│      ├─ full_model.json               # generated only if Principle VI amended
│      ├─ delta_r2.json                 # generated only if Principle VI amended
│      ├─ cv_metrics.json
│      ├─ permutation_results.json     # generated only if Principle VI amended
│      ├─ sensitivity.json             # generated only if Principle VI amended
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
| **1 Synthetic Composition Generation (validation only)** | `python -m code.ingestion.generate_synthetic_composition --seed 42 --output data/raw/synthetic_composition.parquet` | FR‑001 (synthetic fallback) |
| **2 Real Bulk & Geomagnetic Download** | `python -m code.ingestion.download_bulk --start 2000-01-01 --end 2020-12-31 --ace-out data/raw/ace_bulk.csv --noaa-out data/raw/noaa_geomagnetic.parquet` | FR‑001 (bulk) & **FR‑002** (geomagnetic) |
| **3 Checksum Creation** | `python -m code.utils.checksum --dir data/raw --output data/raw/checksums.yaml` | **Data Hygiene** (Principle III) |
| **4 Alignment** | `python -m code.ingestion.align --ace data/raw/ace_bulk.csv --noaa data/raw/noaa_geomagnetic.parquet --comp data/raw/synthetic_composition.parquet --output data/processed/aligned_hourly.parquet --report data/artifacts/alignment_report.json --max_offset 30 --gap_threshold 6` | FR‑003 (hourly median, ≤30 min offset, flag >6 h gaps) |
| **5 Coupling Function Computation** | `python -m code.analysis.coupling_functions --input data/processed/aligned_hourly.parquet --output data/processed/with_coupling.parquet` | FR‑004 |
| **6 Baseline Regression** | `python -m code.analysis.regression --mode baseline --input data/processed/with_coupling.parquet --output data/artifacts/baseline_model.json` | FR‑004, FR‑011 |
| **7 Full Regression (conditional)** | `python -m code.analysis.regression --mode full --input data/processed/with_coupling.parquet --output data/artifacts/full_model.json` | FR‑005, FR‑006, FR‑011 (executed **only if** Principle VI amendment approved) |
| **8 ΔR² Computation (conditional)** | `python -m code.analysis.regression --compute-delta --baseline data/artifacts/baseline_model.json --full data/artifacts/full_model.json --output data/artifacts/delta_r2.json` | FR‑006 |
| **9 5‑Fold Cross‑Validation** | `python -m code.analysis.cross_validation --input data/processed/with_coupling.parquet --output data/artifacts/cv_metrics.json` | FR‑007 |
| **10 Block Permutation Test (conditional)** | `python -m code.analysis.permutation_test --iterations 1000 --block-size 24 --input data/processed/with_coupling.parquet --output data/artifacts/permutation_results.json` | FR‑008 |
| **11 Sensitivity & FDR (conditional)** | `python -m code.analysis.sensitivity --thresholds 0.01 0.05 0.10 --fdr bh --input data/artifacts/permutation_results.json --output data/artifacts/sensitivity.json` | FR‑009, FR‑010 |
| **12 Reporting** | `python -m code.main` (orchestrates all previous steps, aggregates JSON, produces PNG/PDF figures) | SC‑001 – SC‑004 (validation‑focused) |
| **13 Verification** | `pytest tests/` | Non‑functional validation (ensures all artifacts exist and pass schema). |

All tasks are deterministic, produce real files, and are validated against `contracts/dataset.schema.yaml`.

## Data Availability & Limitations
* **Open bulk & geomagnetic sources** (verified):  
  - ACE bulk CSV: `  
  - NOAA Dst/Kp Parquet: `  
* **Composition ratios**: No verified open source; a deterministic synthetic dataset is generated locally for workflow validation (see FR‑001 synthetic fallback). When an open composition source becomes available, step 1 will be replaced with a real download script, and the synthetic files will be removed.  

## Compute Feasibility
* **Memory**: Full 20‑year hourly dataset ≈ 175 k rows × ~20 columns → < 30 MB in memory.  
* **CPU**: All linear‑model operations, VIF, and 1 000 block permutations finish well within the 6 h CI limit on 2 CPU cores.  
* **Disk**: All parquet/JSON artifacts < 200 MB total.  
* **GPU**: Not required.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open composition data | Cannot answer the scientific hypothesis | Synthetic workflow validates the full analysis pipeline; amendment to Principle VI permits this temporary approach. |
| 2‑hour composition cadence → many hourly `null`s | Reduced effective sample size, possible power loss | Alignment script records missing‑value statistics; cross‑validation uses all available rows; power analysis (research.md) acknowledges the effective N only for synthetic validation. |
| Block permutation runtime > 6 h | CI timeout | Early‑stop rule (SE < 0.001) and 1 000‑iteration minimum keep runtime [deferred]. |
| `pyarrow` missing | Parquet I/O failure | `code.utils.io` falls back to `fastparquet`. |
| Multicollinearity inflates SEs | Misleading significance | VIF computed for every predictor; any VIF ≥ 5 flagged; significance interpreted cautiously. |

## Amendment Dependency
* **If Principle VI amendment is approved**: replace step 1 with a real composition download; final report may claim statistical significance per SC‑001.  
* **If amendment is denied or pending**: pipeline runs with synthetic composition only for validation; final report includes a mandatory disclaimer that no real composition measurements were used and that no scientific claim about the Sun‑Earth system is made.

--- 