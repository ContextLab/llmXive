# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2026-10-24 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`

**Input**: Feature specification from `/specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary
The pipeline (CPU‑only, ≤6 h, ≤7 GB RAM, ≤20 GB disk) performs the following ordered steps, each directly addressing a functional requirement (FR) and a success criterion (SC):

1. **Download & verify GWTC‑1 and GWTC‑2 posterior sample archives** (FR‑001).  
   - Retrieve files from Zenodo DOIs 10.5281/zenodo.3966973 and 10.5281/zenodo.3966974.  
   - Verify SHA‑256 checksums obtained from Zenodo metadata (≥95 % integrity).  
   - Retry up to 3 times with exponential back‑off (1 s, 2 s, 4 s). Abort on persistent failure.

2. **Obtain simulation data** (FR‑002).  
   - Download the official IllustrisTNG and EAGLE releases (exact version identifiers recorded).  
   - Apply the documented post‑processing mapping (e.g., Rodriguez et al. 2021) to produce a binary‑BH catalog containing `component_mass_1`, `component_mass_2`, `mass_ratio`, and `effective_spin`.  
   - **No synthetic fallback**: if the official releases cannot be fetched or lack required fields, the pipeline aborts with a clear limitation note, satisfying Constitution Principle VI.

3. **A priori power analysis** (FR‑010, FR‑015).  
   - Using Eq. (1) from arXiv 2309.06305 (α = 0.06) compute the Minimum Detectable Effect Size (MDES) and the required simulation sample size.  
   - Abort before downstream analysis if the available simulation catalog is smaller than the required size, logging a power‑limitation flag.

4. **Pre‑process observational data** (FR‑003, FR‑014).  
   - Extract `component_mass_1`, `component_mass_2`, compute `mass_ratio` and `effective_spin`.  
   - Filter out rows with NaN in any of these fields.  
   - Enforce ≥ 100 valid events after filtering.  
   - For each GWTC event, draw **N = 500** posterior samples (seeded).  
   - Perform a hierarchical bootstrap: resample events with replacement according to their inverse‑probability weights, then **select a single random draw** per resampled event. This yields an i.i.d. point‑estimate dataset suitable for KS testing.

5. **Selection‑bias weighting** (FR‑016).  
   - Compute inverse‑probability weights using the analytic detection‑efficiency model (Abbott et al. 2021).  
   - Verify that the average weight lies in [0.5, 2] and that the sum of weights equals the effective sample size (SC‑011).

6. **Weighted Kolmogorov‑Smirnov tests** (FR‑005, FR‑016 integration).  
   - Apply a **weighted two‑sample KS test** on the marginal distributions of `mass_ratio` and `effective_spin`, incorporating the selection‑bias weights.  
   - Record KS statistics and raw p‑values.

7. **Bonferroni correction** (FR‑006).  
   - Adjust the two marginal p‑values using Bonferroni (α / 2).  
   - No reference to the non‑existent FR‑066.

8. **Kernel density estimation** (FR‑004).  
   - Compute 1‑D KDEs for each parameter using **Scott’s rule**.

9. **Sensitivity analysis** (FR‑009, expanded).  
   - Sweep significance threshold α over the interval **0.01 → 0.10** in steps of 0.01.  
   - Re‑evaluate significance for each α; flag any parameter where the significance status flips across the sweep as “borderline”.

10. **Autocorrelation check** (FR‑017).  
    - Compute lag‑1 autocorrelation on the **final i.i.d. point‑estimate dataset** (after the hierarchical bootstrap).  
    - Require |ρ₁| < 0.1; abort with a diagnostic message if violated. The bootstrap resampling with replacement preserves independence across events, so this check is valid.

11. **Power‑limitation logging** (implicit FR‑012).  
    - If `simulation_sample_size < 0.5 * observational_sample_size`, emit a warning in the “Limitations” section of the final report.

12. **Monte‑Carlo power analysis** (FR‑010, FR‑015, optional).  
    - After the a priori check passes, optionally run a Monte‑Carlo simulation (default 500 iterations) to estimate the empirical MDES for the observed sample sizes. Results are recorded as deferred values in the output schema.

13. **Visualization** (FR‑007, FR‑008).  
    - Generate KDE plots for `mass_ratio` and `effective_spin` with simulation and observational curves overlaid.  
    - Shade regions where the Bonferroni‑adjusted p‑value < 0.05.  
    - Save PNGs at ≥ 300 DPI.

14. **Performance measurement** (FR‑011).  
    - Record wall‑clock runtime, peak RSS memory, and peak disk usage; store in `performance_metrics.json`.

15. **Reporting**  
    - Collate tables, figures, performance metrics, and limitation notes into `final_report.md`.

All steps are deterministic (fixed seeds) and validated against JSON‑Schema contracts.

## Mapping of Functional Requirements to Tasks

| FR | Task(s) | Description |
|----|---------|-------------|
| FR‑001 | T001‑download‑gwtc | Download GWTC‑1 & GWTC‑2 archives, verify SHA‑256 (3 retries). |
| FR‑002 | T002‑obtain‑simulation | Download official IllustrisTNG/EAGLE releases; abort if unavailable or missing required fields. |
| FR‑010/FR‑015 | T003‑pre‑power | Compute a priori MDES using Eq. (1) (α = 0.06); abort if simulation size insufficient. |
| FR‑003 | T004‑preprocess‑obs | Extract masses, compute `mass_ratio` & `effective_spin`, filter NaNs, enforce ≥100 rows. |
| FR‑014 | T004‑posterior‑draws | Draw 500 posterior samples per event, then select a single random draw per event (hierarchical bootstrap). |
| FR‑016 | T005‑selection‑bias | Compute inverse‑probability weights; verify average weight and effective sample size. |
| FR‑005 | T006‑weighted‑ks | Perform **weighted** two‑sample KS tests on marginal distributions. |
| FR‑006 | T006‑bonferroni | Apply Bonferroni correction for the two marginal tests. |
| FR‑004 | T007‑kde | Compute 1‑D KDEs for each parameter. |
| FR‑007 | T008‑visualize | Generate KDE plots with simulation vs observation overlay. |
| FR‑008 | T008‑annotate | Shade regions where Bonferroni‑adjusted p < 0.05. |
| FR‑009 | T009‑sensitivity | Sweep α ∈ {0.01,…,0.10}; flag “borderline” results. |
| FR‑011 | T010‑performance | Record runtime, peak memory, peak disk usage. |
| FR‑017 | T011‑autocorr | Compute lag‑1 autocorrelation on the final i.i.d. dataset; require |ρ₁| < 0.1. |
| FR‑012 (implicit) | T012‑limit‑note | Log power‑limitation note when simulation size < 50 % of observational size. |

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `statsmodels`, `requests`, `tqdm`, `psutil`, `pyyaml`, `jsonschema`.  
- **Storage**: `data/` for raw/processed files; `outputs/figures/` for PNGs.  
- **Testing**: `pytest` + contract validation (`jsonschema`).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤20 GB disk).  
- **Constraints**: CPU‑only; all methods are tractable on the runner.  
- **Scale/Scope**: ≤ 500 observational events (if available), required simulation size determined by a‑priori power analysis.

## Constitution Check

| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed `requirements.txt`; random seeds pinned (`--seed`). |
| II. Verified Accuracy | PASS | SHA‑256 checksums for GWTC‑1/2 are verified via Zenodo metadata; no unverifiable citations. |
| III. Data Hygiene | PASS | All downloads are checksum‑verified; derived files have provenance metadata. |
| IV. Single Source of Truth | PASS | Every figure/table traces to a single row in processed CSVs and a single code block. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state on artifact change. |
| VI. Simulation Data Integrity | PASS | Simulation data must come from official IllustrisTNG/EAGLE releases; pipeline aborts if unavailable. |
| VII. Statistical Rigor | PASS | Weighted KS tests, Bonferroni correction, expanded sensitivity sweep, a priori power analysis, and autocorrelation checks ensure rigorous statistical practice. |

## Project Structure

```text
specs/001-statistical-properties-black-hole-mergers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── data_availability.schema.yaml
│   ├── dataset.schema.yaml
│   ├── gwtc_catalog.schema.yaml
│   ├── raw_gwtc.schema.yaml
│   ├── result.schema.yaml
│   ├── simulation_catalog.schema.yaml
│   ├── statistical_test_result.schema.yaml
│   └── visualization_output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

## Complexity Tracking
All functional requirements (FR‑001 → FR‑017) are addressed directly; no extraneous scaffolding (e.g., web servers, dashboards) is introduced.

--- 
