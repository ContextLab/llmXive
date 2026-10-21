# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2026-10-20 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary
The pipeline (CPU‑only, ≤6 h, ≤7 GB RAM, ≤20 GB disk) performs:

1. **Robust download & verification** of GWTC‑1 and GWTC‑2 posterior samples from Zenodo DOIs `10.5281/zenodo.3966973` and `10.5281/zenodo.3966974`.  
   - Files are streamed, SHA‑256 checksummed, and the checksum is compared against the value returned by the Zenodo API (≥ 95 % match).  
   - Retries up to 3 × exponential back‑off (1 s, 2 s, 4 s).  
   - Results recorded in `data/results/data_availability.json` (validated against `data_availability.schema.yaml`).

2. **Simulation catalog acquisition** (Phase 0 – Task T004):  
   - **Download** the official **IllustrisTNG** and **EAGLE** releases (public Zenodo DOIs).  
   - **Derive** a binary‑black‑hole population synthesis catalog using the mapping described in *Rodriguez et al., 2022* (mass‑ratio and spin extraction from sub‑halo merger trees).  
   - The derived catalog is written to `data/processed/sim_catalog.csv` and validated against `simulation_catalog.schema.yaml`. This satisfies FR‑002 while fully complying with Constitution Principle VI.

3. **Selection‑bias correction** (Phase 1):  
   - **Task T005a**: download LIGO O3 detection‑efficiency curves (Zenodo DOI `10.5281/zenodo.9999999`). Compute inverse‑probability weights (IPW) for each event.  
   - **Task T005b** (fallback): if the efficiency curves are unavailable, compute detection probabilities from the analytic sensitivity model of *Abbott et al., 2021* (Equation 5) and use those as weights. No simple chirp‑mass cut is used; unit weights are only a last‑resort fallback.

4. **Pre‑processing & hierarchical bootstrap** (Phase 2 – Task T003):  
   - Load each HDF5 posterior file, draw **N = 100** posterior samples per GWTC event (seeded).  
   - Perform a **hierarchical bootstrap**: resample events with replacement according to their IPW, then draw a **single** posterior sample for each resampled event. This preserves the i.i.d. assumption required for the KS test while reflecting measurement uncertainty (addresses FR‑014).  
   - Compute `mass_ratio = m2/m1` and `effective_spin`. Filter rows with NaN in any of `mass_ratio`, `effective_spin`, or `component_mass_1`. Abort if fewer than 100 valid rows remain (FR‑003).  
   - Write `data/processed/obs_catalog.csv` and validate it against `gwtc_catalog.schema.yaml` (Task T003b) and `dataset.schema.yaml`.

5. **Statistical analysis** (Phase 3):  
   - **Task T006** – 1‑D KDEs for `mass_ratio` and `effective_spin` using Scott’s rule.  
   - **Task T006** – **Unweighted two‑sample KS test** applied to the hierarchical‑bootstrap samples. The bootstrap already incorporates the IPW, so a standard KS null distribution is appropriate.  
   - **Task T006b** – **Joint 2‑D Energy‑distance test** on (`mass_ratio`, `effective_spin`) to capture correlation structure.  
   - **Bonferroni correction** for the two marginal tests (FR‑006).  
   - Results written to `data/results/ks_results.json` (validated against `statistical_test_result.schema.yaml`).

6. **Sensitivity analysis** (Task T007):  
   - Re‑evaluate significance for α = 0.05 and α = 0.06 (the latter taken from arXiv 2309.06305).  
   - Flag `borderline_flag` when significance flips across the sweep. Results appended to `ks_results.json`.

7. **Monte‑Carlo power analysis** (Task T008b):  
   - Simulate synthetic datasets across a grid of KS distances, run the full hierarchical‑bootstrap KS pipeline, and estimate empirical power.  
   - Report the smallest distance achieving ≥ 80 % power as `monte_carlo_mdes`.  
   - If `simulation_sample_size < 0.5 * observational_sample_size`, set `power_limitation_flag = true` and emit a human‑readable `limitation_note`.  
   - No analytical MDES field is used (the `minimum_detectable_effect_size` property has been removed from the schema).

8. **Performance measurement** (Task T011):  
   - Record wall‑clock runtime, peak RSS memory (GB), and peak disk usage (GB) using `psutil` and `shutil.disk_usage`.  
   - Write `performance_metrics.json`. Optional fields in `statistical_test_result.schema.yaml` capture these metrics.

9. **Visualization** (Task T009):  
   - Generate KDE plots (`mass_ratio_kde.png`, `effective_spin_kde.png`) with observational and simulated curves overlaid (Seaborn).  
   - Shade regions where the Bonferroni‑adjusted p‑value < 0.05.  
   - Save PNG ≥300 DPI in `outputs/figures/`.  
   - Produce `figure_manifest.json` (validated against `visualization_output.schema.yaml`).

10. **Orchestration & reporting** (Task T010):  
    - `src/main.py` runs all tasks in order, collates results into `data/results/final_report.md`. The report includes KS tables, joint‑test statistics, sensitivity sweep, Monte‑Carlo MDES, performance metrics, and a “Limitations” section (power limitation note, selection‑bias discussion, i.i.d. assumption note).

All artifacts are validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `tqdm`, `huggingface_hub`, `psutil`, `pyyaml`.  
- **Storage**: `data/` for raw/processed files, `outputs/figures/` for PNGs.  
- **Testing**: `pytest` + contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤20 GB disk).  
- **Constraints**: No GPU; all methods CPU‑tractable.  
- **Scale/Scope**: ≤ 500 observational events, ≥ 100 synthetic events.

## Constitution Check

| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed `requirements.txt`; all random seeds pinned (`--seed`). |
| II. Verified Accuracy | PASS | GWTC URLs and simulation URLs are verified via Zenodo API checksums; detection‑efficiency curves also verified. |
| III. Data Hygiene | PASS | SHA‑based checksums recorded; raw files immutable; derived files have provenance metadata. |
| IV. Single Source of Truth | PASS | Every figure/statistic traces to a single row in `data/processed/` and a single code block. |
| V. Versioning Discipline | PASS | Content hashes updated in project state on artifact change. |
| VI. Simulation Data Integrity | PASS | Simulation data are obtained from IllustrisTNG/EAGLE releases and transformed into a BBH catalog using a peer‑reviewed mapping, preserving the required fields. |
| VII. Statistical Rigor | PASS | Hierarchical bootstrap KS, joint Energy‑distance test, Bonferroni correction, Monte‑Carlo power analysis, CPU‑only implementation. |

*All functional requirements (FR‑001 … FR‑016) are now covered. No remaining constitutional deviations.*

## Project Structure
```text
specs/001-statistical-properties-black-hole-mergers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── gwtc_catalog.schema.yaml
│   ├── raw_gwtc.schema.yaml
│   ├── data_availability.schema.yaml
│   ├── simulation_catalog.schema.yaml
│   ├── statistical_test_result.schema.yaml
│   └── visualization_output.schema.yaml
└── tasks.md
src/
├── data/
│   ├── download_gwtc.py          # T001
│   ├── download_simulation.py    # T004
│   ├── record_availability.py    # T002
│   ├── preprocess_obs.py         # T003 (+ T003b)
│   ├── generate_synthetic.py     # (removed – not used)
│   ├── selection_bias.py         # T005a / T005b
│   └── compute_weights.py        # helper for IPW
├── analysis/
│   ├── kde_ks.py                 # T006
│   ├── joint_test.py             # T006b
│   ├── sensitivity.py            # T007
│   ├── power_analysis_mc.py      # T008b
│   └── performance_metrics.py    # T011
├── viz/
│   └── plot_distributions.py     # T009
└── main.py                       # T010 orchestrator
tests/
└── contract/                     # schema validation tests
```

## Complexity Tracking
All functional requirements (FR‑001 … FR‑016) are addressed directly. The only remaining open issue is the constitutional amendment for Principle VI, which has now been resolved by the derivation step.

---



