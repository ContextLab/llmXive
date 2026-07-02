# Implementation Plan: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `feature-001-geomagnetic-correlation` | **Date**: 2026-06-24 | **Spec**: `specs/feature-001-geomagnetic-correlation/spec.md`
**Input**: Feature specification from `/specs/feature-001-geomagnetic-correlation/spec.md`

## Summary

The pipeline quantifies associational relationships between ACE solar‑wind composition (proton density, temperature, helium abundance) and NOAA geomagnetic indices (Kp, Dst). It downloads multi‑year data, validates required variables, aligns to a 1‑hour UTC grid with strict gap handling, computes lagged Pearson and Spearman correlations, adjusts raw p‑values using an effective sample size (Neff) that accounts for autocorrelation, applies a **global** Bonferroni correction derived from the **full 1998‑2020 series**, and generates visual artefacts and a validation report for the held‑out 2018‑2020 period.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `requests`, `tqdm`, `pyyaml`  
- **Storage**: `data/raw/`, `data/processed/`, `artifacts/`  
- **Testing**: `pytest` (see detailed task list)  
- **Target Platform**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, ≤6 h) – CPU‑only.  
- **Constraints**: No GPU, no large‑LLM inference, all libraries CPU‑compatible.  

## Project Structure

```
code/
├── __init__.py          # logging config, random seed
├── data/
│   ├── fetch.py         # FR‑001, FR‑006 – download & variable existence check
│   ├── align.py         # FR‑002 – resample, linear interpolation ≤6 h, logging
│   └── validate.py      # abort on missing variables, logs exact missing name (SC‑002)
├── analysis/
│   ├── neff.py          # FR‑010 – compute lag‑specific Neff using Pyper & Peterman
│   ├── correlation.py   # FR‑003 – lagged Pearson/Spearman
│   └── significance.py  # FR‑004 – global Bonferroni correction (single artifact)
├── viz/
│   ├── plots.py         # FR‑008 – time‑series overlay & heatmaps (PNG ≤5 MB)
│   └── report.py        # FR‑009 – Markdown validation report
├── main.py              # CLI orchestration
└── requirements.txt     # pinned versions
tests/
├── unit/
│   ├── test_fetch.py
│   ├── test_align.py
│   ├── test_neff.py
│   ├── test_significance.py
│   └── test_validation_abort.py
├── integration/
│   └── test_pipeline.py
└── conftest.py
data/
├── raw/
└── processed/
    └── synced.csv
artifacts/
├── plots/
├── reports/
└── thresholds/
    └── global_threshold.json   # stores Neff and Bonferroni α_adj
```

## Phases & Explicit Plan Elements

| Phase | Description | FR / SC addressed | Output / Contract |
|------|-------------|-------------------|-------------------|
| **Phase 0** | Scaffold repository, create directory layout, pin `requirements.txt`. | – | – |
| **Phase 1** | **Variable Validation** – `fetch.py` checks that ACE files contain **exact** columns `N_p`, `T_p`, `He2+_ratio`. If any are missing, the pipeline aborts with error `Missing required variable: <name>` and logs the name (fulfills FR‑006, SC‑002). | FR‑006, SC‑002 | No output; abort on failure. |
| **Phase 2** | **Alignment** – `align.py` resamples both ACE and NOAA series to a 1‑hour UTC grid, fills gaps ≤ 6 h by linear interpolation, logs each interpolated interval, and **excludes** any gap > 6 h from downstream correlation (still visualised). The resulting CSV (`synced.csv`) contains **no NaNs** (SC‑004). | FR‑001, FR‑002, SC‑004 | `data/processed/synced.csv` (conforms to `contracts/dataset.schema.yaml`). |
| **Phase 3** | **Global Statistical Thresholding** – `neff.py` computes lag‑specific effective sample sizes for each composition‑index pair on the **full 1998‑2020 series** (no splitting). `significance.py` then applies a Bonferroni correction for the multiple tests, storing `α_adj` and all Neff values in `artifacts/thresholds/global_threshold.json`. This artifact is the **single source** for significance testing in both training and validation (addresses FR‑010, SC‑003). | FR‑010, FR‑004, SC‑003 | `artifacts/thresholds/global_threshold.json` (validated against a new `contracts/threshold.schema.yaml`). |
| **Phase 4** | **Correlation Computation** – `correlation.py` uses the global Neff values and the Bonferroni α_adj from Phase 3 to compute Pearson r, Spearman ρ, raw p‑values (adjusted for Neff), and Bonferroni‑corrected p‑values for each of the 30 lagged pairs. Results are written to `artifacts/correlations.csv` and must conform to `contracts/analysis_schema.schema.yaml`. | FR‑003, FR‑004 | `artifacts/correlations.csv`. |
| **Phase 5** | **Visualization & Reporting** – `plots.py` creates PNG heatmaps and time‑series overlays (≤ 5 MB each) and validates them against `contracts/visual_artifact.schema.yaml`. `report.py` generates `artifacts/reports/validation_report.md` adhering to `contracts/output.schema.yaml`, summarising any pair with |r| > 0.5 **and** Bonferroni‑corrected p < 0.05. | FR‑008, FR‑009 | PNG artefacts, `validation_report.md`. |
| **Phase 6** | **Performance Contracts** – Benchmark scripts (`benchmarks/performance.py`) record runtime and peak RAM for Phases 2–5; results are compared against SC‑001 (≤ 6 h, ≤ 7 GB) and SC‑004 (≤ 30 min, ≤ 4 GB). Failures raise a CI error. | SC‑001, SC‑004 | Log file `artifacts/performance.log`. |

## Task List (Deterministic Function Names)

| Task ID | Description | Produces |
|--------|-------------|----------|
| T001 | `scripts/create_scaffold.py` – creates repo directories. | directories |
| T002 | `scripts/init_requirements.py` – writes `code/requirements.txt`. | file |
| T003 | `scripts/configure_linting.py` – creates `pyproject.toml`, `.ruff.toml`, `.black`. | files |
| T004 | `code/data/fetch.py` – download ACE, verify variables, abort on missing. | raw files, abort message |
| T005 | `code/data/align.py` – resample, interpolate, log gaps. | `synced.csv` |
| T006 | `code/analysis/neff.py` – compute lag‑specific Neff on full series. | JSON artifact |
| T007 | `code/analysis/significance.py` – global Bonferroni, write `global_threshold.json`. | JSON artifact |
| T008 | `code/analysis/correlation.py` – compute correlations using global thresholds. | `correlations.csv` |
| T009 | `code/viz/plots.py` – generate PNG heatmaps & overlays (size ≤5 MB). | PNG files |
| T010 | `code/viz/report.py` – generate `validation_report.md`. | Markdown report |
| T011 | `scripts/run_performance.py` – benchmark Phases 2‑5, write log. | `performance.log` |
| T012‑T030 | Unit & integration tests (e.g., `test_fetch_abort_on_missing.py`, `test_align_interpolation.py`, `test_neff_formula.py`, `test_bonferroni_divisor.py`, `test_pipeline_full_run.py`, `test_viz_png_size_limit.py`, `test_report_threshold_detection.py`). | pytest modules |

All tests are named explicitly as above to satisfy deterministic execution.

## Constitution Check

| Principle | Status | Note |
| :--- | :--- | :--- |
| I. Reproducibility | PASS | Version‑pinned `requirements.txt`; random seeds fixed in `code/__init__.py`. |
| II. Verified Accuracy | **FAIL** | NOAA Kp/Dst dataset URL is missing from the verified block; pipeline aborts until a verified source is supplied. |
| III. Data Hygiene | PASS | Raw data checksummed; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | All figures and statistics generated from code; no hand‑typed numbers. |
| V. Versioning Discipline | PASS | Artifacts hashed; `state/` updated on change. |
| VI. Temporal Alignment | PASS | All series aligned to 1‑hour UTC grid; lag consistency enforced. |
| VII. Statistical Rigor | PASS | Global Neff & Bonferroni computed once; applied to both training and validation. |

## Risks & Mitigations (re‑iterated)

- **Missing NOAA source** – pipeline aborts; flagged as critical.  
- **Interpolation bias** – interpolated points are excluded from correlation; only visualised.  
- **Non‑stationarity** – median of rolling‑window lag‑1 autocorrelations used for Neff; documented in research.md.  
- **Dependent tests** – Bonferroni justified as per community practice; noted in research.md.  
