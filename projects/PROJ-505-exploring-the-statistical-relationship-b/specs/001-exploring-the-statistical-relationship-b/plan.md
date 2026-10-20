# Implementation Plan: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `001-solar-wind-composition-geomagnetic` | **Date**: 2026-10-20 | **Spec**: `specs/001-solar-wind-composition-geomagnetic/spec.md`  
**Input**: Feature specification from `/specs/001-solar-wind-composition-geomagnetic/spec.md`

## Summary
The project must ingest solar‑wind composition data (O/Fe, He/H, C/O) from ACE/WIND and geomagnetic indices (Dst, Kp) from NOAA, align them to an hourly grid, compute coupling functions, fit baseline and full multivariate linear regressions, evaluate incremental R² (ΔR²), perform 5‑fold time‑series cross‑validation, run a 24‑hour block permutation test, apply Benjamini‑Hochberg FDR correction, and report variance‑inflation factors (VIF).

Because **no verified open dataset provides the required composition ratios**, the pipeline **generates a deterministic synthetic dataset** (see `research.md` for full description). This synthetic data is **only for workflow validation**; scientific conclusions about the real Sun‑Earth system require an amendment to Constitution Principle VI (Composition Data Integrity) or the availability of an open real dataset. The plan therefore includes an explicit amendment request and a gating mechanism that prevents any claim of scientific significance until the amendment is approved.

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
- **Storage**: Local CSV/Parquet under `data/` (`raw/`, `processed/`, `artifacts/`)  
- **Testing**: `pytest==8.3.*` (unit & integration)  
- **Target Platform**: GitHub Actions free‑tier (2 CPU, 7 GB RAM, 14 GB disk) – **CPU‑first**; no GPU required.  
- **Compute Limits**: ≤ 6 h runtime, ≤ 6 GB RAM, ≤ 200 MB disk usage.

## Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic RNG seed, all scripts version‑controlled. |
| II. Verified Accuracy | PASS | No new citations; the lack of an open composition source is documented. |
| III. Data Hygiene | PASS | Synthetic raw files are checksummed; every transformation writes a new file. |
| IV. Single Source of Truth | PASS | All figures/tables are generated directly from artifact files. |
| V. Versioning Discipline | PASS | Artifacts are referenced by content hash (handled by runtime). |
| **VI. Composition Data Integrity** | **PENDING AMENDMENT (blocking)** | Current pipeline uses synthetic composition ratios. An amendment is required to either (a) allow synthetic data solely for workflow validation, **or** (b) supply an open real composition dataset. Until the amendment is approved, any downstream phases that would rely on real composition data are **gated** (see “Amendment Dependency” below). |
| VII. Statistical Validation and Model Transparency | PASS | Full regression, CV, ΔR², permutation test, FDR, VIF are implemented and output reproducible artifacts. Claims of statistical significance are suppressed when only synthetic data are used. |

**Action**: Project lead must approve a scope amendment for Principle VI. Until approval, the pipeline proceeds **only with the synthetic dataset** and the final report will contain a disclaimer that no scientific claim about real composition effects is made.

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
│  │   ├─ generate_synthetic_data.py   # FR‑001/002 (synthetic fallback)
│  │   ├─ align.py                     # FR‑003
│  │   └─ download_real.py             # placeholder – will fail if invoked (no open source)
│  ├─ analysis/
│  │   ├─ coupling_functions.py       # FR‑004 (baseline physics)
│  │   ├─ regression.py               # FR‑004, FR‑005, FR‑006, FR‑011
│  │   ├─ cross_validation.py         # FR‑007
│  │   ├─ permutation_test.py         # FR‑008
│  │   └─ sensitivity.py              # FR‑009, FR‑010
│  ├─ utils/
│  │   ├─ io.py                       # robust CSV/Parquet I/O, pyarrow fallback
│  │   └─ checksum.py                 # SHA‑256 verification
│  └─ main.py                         # Orchestrates the full pipeline
├─ data/
│  ├─ raw/            # Synthetic source files (preserved unchanged)
│  ├─ processed/      # Aligned & enriched parquet files
│  └─ artifacts/      # JSON/CSV results, plots
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
| **1 Synthetic Data Generation** | `python -m code.ingestion.generate_synthetic_data --seed 42 --output data/raw/synthetic.parquet` | FR‑001, FR‑002 (synthetic fallback) |
| **2 Alignment** | `python -m code.ingestion.align --input data/raw/synthetic.parquet --output data/processed/aligned_hourly.parquet --report data/artifacts/alignment_report.json --max_offset 30` | FR‑003 |
| **3 Feature Engineering (Coupling Functions)** | `python -m code.analysis.coupling_functions --input data/processed/aligned_hourly.parquet --output data/processed/with_coupling.parquet` | FR‑004 |
| **4 Baseline Regression** | `python -m code.analysis.regression --mode baseline --input data/processed/with_coupling.parquet --output data/artifacts/baseline_model.json` | FR‑004, FR‑011 |
| **5 Full Regression** | `python -m code.analysis.regression --mode full --input data/processed/with_coupling.parquet --output data/artifacts/full_model.json` | FR‑005, FR‑006, FR‑011 |
| **6 ΔR² Computation** | `python -m code.analysis.regression --compute-delta --baseline data/artifacts/baseline_model.json --full data/artifacts/full_model.json --output data/artifacts/delta_r2.json` | FR‑006 |
| **7 Cross‑Validation** | `python -m code.analysis.cross_validation --input data/processed/with_coupling.parquet --output data/artifacts/cv_metrics.json` | FR‑007 |
| **8 Permutation Test** | `python -m code.analysis.permutation_test --iterations 1000 --block-size 24 --input data/processed/with_coupling.parquet --output data/artifacts/permutation_results.json` | FR‑008 |
| **9 Sensitivity & FDR** | `python -m code.analysis.sensitivity --thresholds 0.01 0.05 0.10 --fdr bh --input data/artifacts/permutation_results.json --output data/artifacts/sensitivity.json` | FR‑009, FR‑010 |
| **10 Reporting** | `python -m code.main` (orchestrates all steps, aggregates JSON/CSV, produces plots in `data/artifacts/`) | SC‑001 – SC‑004 |
| **Optional Verification** | `pytest tests/` | (non‑functional testing; not linked to a specific FR/SC) |

All tasks are deterministic, produce real files, and can be validated against the contract schema.

## Data Availability & Limitations
* **No verified open dataset provides ACE SWICS or WIND composition ratios** for 2000‑2020.  
* The pipeline therefore **generates a deterministic synthetic dataset** (see `research.md` for full description).  
* When an open composition dataset becomes available, replace step 1 with `download_real.py`; the remainder of the pipeline is unchanged.

## Compute Feasibility
* **Memory**: ~30 MB for the full 20‑year hourly dataset – well under 7 GB RAM.  
* **CPU**: Linear regression, VIF, and 1 000 block permutations on this size complete comfortably within the 6 h CI limit on 2 CPU cores.  
* **Disk**: All parquet/JSON artifacts < 200 MB total.  
* **GPU**: Not required.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open composition data | Cannot answer scientific hypothesis | Use synthetic data for workflow validation; request constitution amendment; replace with real data when available. |
| Synthetic ratios lack physical realism | Construct‑validity issue | Explicitly label results as synthetic; avoid any real‑world inference. |
| Block permutation runtime > 6 h | CI timeout | Minimum 1 000 iterations; early stop when SE < 0.001 (as required by FR‑008). |
| `pyarrow` missing | Parquet I/O failure | `code.utils.io` falls back to `fastparquet`. |
| Multicollinearity inflates SEs | Misleading significance | Compute VIF; flag VIF ≥ 5 and report descriptive statistics only. |

## Amendment Dependency
* **If the Principle VI amendment is approved**: the pipeline may later be re‑run with real composition data (by swapping `generate_synthetic_data.py` for `download_real.py`). The final report will then include the claim language required by SC‑001 in the spec.
* **If the amendment is denied or pending**: the pipeline proceeds **only with the synthetic dataset**. All downstream phases (2‑10) run unchanged, but the final report will contain a mandatory disclaimer: *“No open composition measurements were used; results are synthetic and do not constitute scientific evidence about the real Sun‑Earth system.”* No claim of statistical significance per SC‑001 will be made.

---



