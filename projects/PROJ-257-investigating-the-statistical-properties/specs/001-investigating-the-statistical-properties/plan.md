# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2026-10-20 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`

**Input**: Feature specification from `/specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary
The pipeline (CPU‑only, ≤6 h, ≤7 GB RAM, ≤20 GB disk) performs:

1. **Download & verification** of GWTC‑1 and GWTC‑2 posterior samples (FR‑001).  
2. **Derivation or synthetic generation** of a binary‑black‑hole population catalog (FR‑002, fallback to synthetic power‑law spin distribution).  
3. **Pre‑processing** of observational posteriors into a point‑estimate CSV (FR‑003, FR‑014).  
4. **Selection‑bias weighting** using inverse‑probability weights (FR‑016).  
5. **Kernel density estimation** for `mass_ratio` and `effective_spin` (FR‑004).  
6. **Kolmogorov‑Smirnov (KS) tests** on marginal distributions (FR‑005) with Bonferroni correction (FR‑006).  
7. **Joint 2‑D Energy‑distance test** (additional robustness, not required but useful).  
8. **Sensitivity analysis** over α ∈ {0.05, 0.06} (FR‑009, verified α = 0.06 from arXiv 2309.06305).  
9. **Monte‑Carlo power analysis** and Minimum Detectable Effect Size (MDES) estimation (FR‑010, FR‑015).  
10. **Power‑limitation flagging** when simulation sample size < 50 % of observational size (FR‑012).  
11. **Visualization** of KDEs with divergence shading (FR‑007, FR‑008).  
12. **Performance measurement** (runtime, memory, disk) (FR‑011).  
13. **Orchestration & reporting** into a final markdown report (includes limitations section for power and i.i.d. concerns).

All steps are deterministic (fixed random seeds) and validated against JSON‑Schema contracts.

### Mapping of Functional Requirements (FR) to Tasks
| FR | Task(s) | Description |
|----|---------|-------------|
| FR‑001 | T001‑download‑gwtc | Download GWTC‑1 & GWTC‑2 posterior samples, verify SHA‑256 checksums (3 retries). |
| FR‑002 | T004‑obtain‑simulation | Attempt download of official IllustrisTNG/EAGLE releases; if unavailable, generate synthetic catalog using a power‑law spin distribution (fallback). |
| FR‑003 | T003‑preprocess‑obs | Extract `component_mass_1`, `component_mass_2`, compute `mass_ratio` and `effective_spin`; filter NaNs; require ≥100 valid events. |
| FR‑004 | T006‑kde | Compute 1‑D KDEs with Scott’s rule for each parameter. |
| FR‑005 | T006‑ks | Perform two‑sample KS tests on hierarchical‑bootstrap samples. |
| FR‑006 | T006‑bonferroni | Apply Bonferroni correction for the two marginal tests. |
| FR‑007 | T009‑visualize | Produce KDE plots with divergence regions shaded, PNG ≥300 DPI. |
| FR‑008 | T009‑annotate | Annotate regions where Bonferroni‑adjusted p < 0.05. |
| FR‑009 | T007‑sensitivity | Sweep α ∈ {0.05, 0.06}; flag “borderline” when significance flips. |
| FR‑010 | T008‑power‑mc | Monte‑Carlo power analysis; compute MDES (empirical). |
| FR‑011 | T011‑performance | Record runtime, peak memory, peak disk usage. |
| FR‑014 | T003‑posterior‑draws | Draw 500 posterior samples per event, then select a single random draw per event (hierarchical bootstrap). |
| FR‑015 | T008‑mdes‑analytic | Compute analytic MDES using Eq. (1) from arXiv 2309.06305 (α = 0.06). |
| FR‑016 | T005‑selection‑bias | Compute inverse‑probability weights from downloaded detection‑efficiency curves; fallback to analytic model. |
| FR‑017 | T017‑autocorr | Compute lag‑1 autocorrelation for each parameter; require |ρ₁| < 0.1. |
| FR‑012 (implicit) | T012‑limit‑note | Log power‑limitation note when simulation size < 50 % of observational size. |

### Handling of Unverified Observational Datasets
The verified dataset block reports **no verified source** for GWTC‑1 and GWTC‑2 (DOIs 10.5281/zenodo.3966973/3966974). Consequently:

- **T001** will attempt download using the DOI URLs, but the pipeline will treat the lack of a verified checksum as a *fatal data‑availability gap*.  
- If the download fails or checksum cannot be verified, the pipeline aborts with a clear error recorded in `data/results/data_availability.json`.  
- This limitation is explicitly documented in the “Limitations” section of the final report (SC‑009).  

### Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `tqdm`, `huggingface_hub`, `psutil`, `pyyaml`, `jsonschema`.  
- **Storage**: `data/` for raw/processed files; `outputs/figures/` for PNGs.  
- **Testing**: `pytest` + contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤20 GB disk).  
- **Constraints**: CPU‑only; all methods are tractable on the runner.  
- **Scale/Scope**: ≤ 500 observational events (if available), ≥ 100 synthetic events.

## Constitution Check

| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed `requirements.txt`; random seeds pinned (`--seed`). |
| II. Verified Accuracy | PARTIAL | Simulation fallback uses a documented hypothesis; GWTC URLs lack verified checksum → documented as limitation. |
| III. Data Hygiene | PASS | All downloads checksum‑verified (when possible); derived files have provenance metadata. |
| IV. Single Source of Truth | PASS | Every figure/table traces to a single row in processed CSVs and a single code block. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state on artifact change. |
| VI. Simulation Data Integrity | PASS | When official releases are unavailable, synthetic catalog is generated per fallback requirement. |
| VII. Statistical Rigor | PASS | Hierarchical bootstrap respects i.i.d. assumption; KS tests, Bonferroni, sensitivity, power analysis, autocorrelation checks included. |

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
│   ├── simulation_catalog.schema.yaml
│   ├── statistical_test_result.schema.yaml
│   └── visualization_output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

src/
├── data/
│   ├── download_gwtc.py          # T001
│   ├── record_availability.py    # T002
│   ├── download_simulation.py    # T004
│   ├── generate_synthetic.py     # fallback for T004
│   ├── preprocess_obs.py         # T003
│   ├── selection_bias.py         # T005
│   └── compute_weights.py
├── analysis/
│   ├── kde_ks.py                 # T006
│   ├── joint_test.py             # optional 2‑D test
│   ├── sensitivity.py            # T007
│   ├── power_analysis_mc.py      # T008
│   └── performance_metrics.py    # T011
├── viz/
│   └── plot_distributions.py     # T009
└── main.py                       # orchestrator (T010)

tests/
└── contract/                     # schema validation tests
```

## Complexity Tracking
All functional requirements (FR‑001 → FR‑017) are addressed directly by the tasks above. No extraneous scaffolding (e.g., API servers, dashboards) is introduced because the scientific question does not require them.

---
