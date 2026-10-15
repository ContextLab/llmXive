# Implementation Plan: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `001-solar-wind-composition-geomagnetic` | **Date**: 2026-10-15 | **Spec**: `specs/001-solar-wind-composition-geomagnetic/spec.md`  
**Input**: Feature specification from `/specs/001-solar-wind-composition-geomagnetic/spec.md`

## Summary
The project implements a **pipeline validation** for studying solar‑wind composition and geomagnetic storm intensity. Because no verified open dataset supplies the required ACE SWICS composition ratios or NOAA Dst/Kp indices, the workflow **exclusively uses a synthetic dataset** that matches the required schema. The synthetic data are used **solely to confirm that the end‑to‑end statistical workflow (ingestion, alignment, coupling‑function computation, regression, ΔR², cross‑validation, permutation testing, FDR, VIF) runs correctly and produces verifiable artifacts**. No scientific claim about the real solar‑wind–geomagnetic relationship will be made from the synthetic results.

## Scope Limitation
* No verified open source provides the required composition ratios or geomagnetic indices.  
* The pipeline therefore **directly generates** a synthetic dataset (see `code/ingestion/generate_synthetic_data.py`).  
* Results derived from synthetic data are labeled as *pipeline validation only*; they are not evidence for or against the hypothesis that composition predicts storm intensity.

### Statistical Power & Detectable Effect Size (Synthetic‑Data Context)
* Sample: a multi‑year span of hourly data, yielding a substantial number of rows and comfortably fitting within available memory.  
* Power analysis is retained **only as a reference for the synthetic scenario**; the synthetic effect sizes are drawn from a distribution that may or may not exceed the ΔR² > 0.05 threshold. This allows the pipeline to be exercised under both significant and non‑significant conditions.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `scipy==1.14.*`, `pyarrow==15.0.*` (optional – fallback to `fastparquet`), `tqdm==4.66.*`, `pyyaml==6.0.*`  
- **Storage**: Local CSV/Parquet files under `data/` (`raw/`, `processed/`, `artifacts/`)  
- **Testing**: `pytest==8.3.*` (unit & integration)  
- **Target Platform**: GitHub Actions free‑tier runner (Linux, 2 CPU, 7 GB RAM, 14 GB disk) – **CPU‑first**; no GPU required.  
- **Constraints**: All scripts must run within 6 h, peak RAM < 6 GB.  

## Constitution Check
| Principle | Status | How the Plan Satisfies |
|-----------|--------|------------------------|
| **I. Reproducibility** | PASS | Fixed `requirements.txt`, pinned random seeds, deterministic synthetic generator, and end‑to‑end scripts in `code/`. |
| **II. Verified Accuracy** | PASS (with explicit gap) | No unverified citations are introduced; the lack of real data is documented transparently. |
| **III. Data Hygiene** | PASS | Raw (synthetic) files are checksummed; transformations write new files; no in‑place edits. |
| **IV. Single Source of Truth** | PASS | All figures/tables are produced directly from the artifact files in `data/artifacts/`. |
| **V. Versioning Discipline** | PASS | Artifacts are referenced by content hash in the project state file (handled by the runtime). |
| **VI. Composition Data Integrity** | PASS (synthetic) | Synthetic raw files are stored unchanged; derived ratios are computed only from these raw files; provenance metadata is recorded. |
| **VII. Statistical Validation and Model Transparency** | PASS (pipeline‑validation) | Full regression, 5‑fold CV, ΔR², block permutation, FDR, and VIF are all implemented in `code/analysis/` and output reproducible CSV/JSON artifacts. Any claim of statistical significance is directly supported by these artifacts **within the synthetic context**. |

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
│  │   ├─ generate_synthetic_data.py   # FR‑001/002 synthetic generator (primary source)
│  │   └─ align.py                     # FR‑003 (hourly median, ≤30 min offset)
│  ├─ analysis/
│  │   ├─ coupling_functions.py       # FR‑004 baseline physics
│  │   ├─ regression.py               # FR‑004, FR‑005, FR‑006, FR‑011
│  │   ├─ cross_validation.py         # FR‑007
│  │   ├─ permutation_test.py         # FR‑008
│  │   └─ sensitivity.py              # FR‑009, FR‑010
│  ├─ utils/
│  │   ├─ io.py                      # robust CSV/Parquet I/O, optional `pyarrow` fallback
│  │   └─ checksum.py                # SHA‑256 verification
│  └─ main.py                        # Orchestrates the full pipeline
├─ data/
│  ├─ raw/                           # Synthetic source files (preserved unchanged)
│  ├─ processed/                     # Aligned hourly dataset (parquet)
│  └─ artifacts/                     # CSV/JSON results, plots
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

| Phase | Tasks (script) | FR / SC addressed |
|-------|----------------|-------------------|
| **0 Prep** | `pip install -r requirements.txt` (pinned) | – |
| **1 Synthetic Data Generation** | `code/ingestion/generate_synthetic_data.py --seed 42 --output data/processed/aligned.parquet` | FR‑001, FR‑002 (fallback) |
| **2 Alignment** | `code/ingestion/align.py --input data/processed/aligned.parquet --output data/processed/aligned_hourly.parquet` | FR‑003 |
| **3 Feature Engineering** | `code/analysis/coupling_functions.py --input data/processed/aligned_hourly.parquet --output data/processed/with_coupling.parquet` | FR‑004 (baseline physics) |
| **4 Baseline Regression** | `code/analysis/regression.py --mode baseline --input data/processed/with_coupling.parquet --output data/artifacts/baseline_model.json` | FR‑004, FR‑011 |
| **5 Full Regression** | `code/analysis/regression.py --mode full --input data/processed/with_coupling.parquet --output data/artifacts/full_model.json` | FR‑005, FR‑006, FR‑011 |
| **6 ΔR² Computation** | `code/analysis/regression.py --compute-delta --baseline data/artifacts/baseline_model.json --full data/artifacts/full_model.json --output data/artifacts/delta_r2.json` | FR‑006 |
| **7 Cross‑Validation** | `code/analysis/cross_validation.py --input data/processed/with_coupling.parquet --output data/artifacts/cv_metrics.json` | FR‑007 |
| **8 Permutation Test** | `code/analysis/permutation_test.py --iterations 1000 --block-size 24 --input data/processed/with_coupling.parquet --output data/artifacts/permutation_results.json` | FR‑008 |
| **9 Sensitivity & FDR** | `code/analysis/sensitivity.py --thresholds 0.01 0.05 0.10 --fdr bh --input data/artifacts/permutation_results.json --output data/artifacts/sensitivity.json` | FR‑009, FR‑010 |
| **10 Reporting** | `code/main.py` (orchestration) aggregates all JSON/CSV into final tables & plots in `data/artifacts/` | SC‑001 – SC‑004 |
| **11 Verification** | `pytest tests/` (unit + integration) validates I/O, schema compliance, and that all FR‑related outputs exist and match `contracts/dataset.schema.yaml` | – |

All tasks are deterministic, produce real files, and can be verified by the contract schema.

## Data Availability & Limitations
* No verified open source provides ACE SWICS composition ratios or NOAA Dst/Kp indices.  
* The pipeline **directly generates** a synthetic dataset that matches the required schema (see `contracts/dataset.schema.yaml`).  
* Because the data are synthetic, the project **cannot answer the scientific hypothesis** about composition’s predictive power; it only validates that the statistical workflow runs correctly on a realistic‑looking dataset.

## Compute Feasibility
* **Memory**: 20 years × 24 h ≈ 175 k rows → ≈ 30 MB in `pandas`; well under 7 GB RAM.  
* **CPU**: Linear regression, VIF, and 1 000 block permutations on 175 k rows complete in [deferred] on 2 CPU cores.  
* **Disk**: All parquet/CSV artifacts < 200 MB total.  
* **No GPU** required; all libraries are CPU‑compatible.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing verified data | Cannot answer scientific question | Use synthetic data; clearly label results as pipeline validation. |
| Block permutation runtime | May exceed 6 h if iteration count is increased | Default 1 000 iterations; early stop when SE < 0.001. |
| `pyarrow` unavailable | Parquet I/O failures | `code/utils/io.py` tries `pyarrow`; on ImportError falls back to `fastparquet`. |
| Multicollinearity | Inflated SEs, misleading p‑values | Compute VIF; if VIF ≥ 5, report descriptive effect sizes only. |

---



