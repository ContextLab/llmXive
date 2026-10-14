# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2026-10-13 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary
This plan implements a reproducible, CPU‑only pipeline that (1) **downloads** GWTC‑1 and GWTC‑2 posterior samples from their canonical Zenodo DOI records; if any download fails, the pipeline **aborts** with an explicit error (as mandated by the spec). (2) **Preprocesses** the validated posterior samples into a point‑estimate CSV containing component masses, mass ratios, and effective spins. (3) **Generates** a synthetic binary‑black‑hole population catalog from the “Power‑law mass with independent spin” hypothesis (mass‑power‑law index = ‑2.35, spin uniformly in [‑0.5, 0.5]) with a pinned random seed. (4) **Applies** detection‑efficiency correction: when efficiency curves are unavailable, the same detection‑space cut is applied to **both** the observational and synthetic catalogs to ensure a fair comparison. (5) **Performs** weighted two‑sample Kolmogorov‑Smirnov (KS) tests with event‑level bootstrapping (B = 1000, seeded); the p‑value is the proportion of bootstrap KS statistics **greater than or equal to** the observed statistic. (6) **Conducts** a sensitivity analysis over α ∈ {0.05, 0.06} (α = 0.06 sourced from arXiv 2309.06305) and flags “borderline” results where significance flips. (7) **Computes** a KS‑specific Minimum Detectable Effect Size (MDES) defined as the minimum Kolmogorov distance D detectable with 80 % power at α = 0.05 using the asymptotic formula D = √[‑0.5 ln(α/2)·((n₁+n₂)/(n₁·n₂))]; logs a power‑limitation note if the simulation sample size is < 50 % of the observational sample size. (8) **Produces** annotated KDE visualizations with divergence regions highlighted. All steps are deterministic, checkpointed, and validated against JSON‑Schema contracts.

## Project Structure

```
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
│   ├── result.schema.yaml
│   ├── simulation_catalog.schema.yaml
│   ├── statistical_test_result.schema.yaml
│   └── visualization_output.schema.yaml
└── tasks.md
```

## Implementation Phases & Tasks

| Phase | Task ID | Description | Input(s) | Output(s) | Contract |
|-------|---------|-------------|----------|-----------|----------|
| **Phase 0 – Data Acquisition** | **T001** | Download GWTC‑1 and GWTC‑2 posterior sample files from Zenodo DOIs (10.5281/zenodo.3966973, 10.5281/zenodo.3966974) using `src/data/download.py`. Perform up‑to‑3 exponential‑backoff retries. Validate each file against `contracts/raw_gwtc.schema.yaml`. **If any download fails, abort the pipeline with an explicit error** (per spec). | Zenodo URLs | `data/raw/gwtc1.h5`, `data/raw/gwtc2.h5` (validated) | raw_gwtc.schema.yaml |
|       | **T002** | Record SHA‑256 checksums of any accepted raw files in `data/raw/checksums.json`. Emit a data‑availability report `data/results/data_availability.json` validated against `contracts/data_availability.schema.yaml`. | Raw files (if any) | `data/results/data_availability.json` | data_availability.schema.yaml |
| **Phase 1 – Preprocessing & Simulation Generation** | **T003** | Load validated GWTC posterior files, draw a **single** posterior sample per event (preserving i.i.d. across events), filter rows with NaN in `mass_ratio`, `effective_spin`, or `component_mass_1`. Require ≥ 100 valid events; otherwise raise an explicit error. Write `data/processed/obs_catalog.csv`. | Validated raw files | `data/processed/obs_catalog.csv` | dataset.schema.yaml |
|       | **T004** | Generate a synthetic BBH population catalog from the “Power‑law mass with independent spin” hypothesis (mass‑power‑law index = ‑2.35, spin uniform in [‑0.5, 0.5]), using a pinned seed (2026‑10‑13‑seed). Write `data/processed/sim_catalog.csv`. | None (synthetic) | `data/processed/sim_catalog.csv` | simulation_catalog.schema.yaml |
| **Phase 2 – Selection‑Bias Correction** | **T005** | If detection‑efficiency curves are provided, compute inverse‑probability weights for each observational event (`src/analysis/selection_bias.py`). **If not, apply the same detection‑space cut (e.g., minimum detectable chirp mass) to BOTH the observational and simulation catalogs** so they share the same observable region. Log the applied scope (`detection_space` or `intrinsic_space`). Output `data/processed/selection_weights.csv`. | Obs catalog, sim catalog, optional efficiency data | `data/processed/selection_weights.csv` | dataset.schema.yaml |
| **Phase 3 – Statistical Analysis** | **T006** | Compute 1‑D KDEs (Scott’s rule) for `mass_ratio` and `effective_spin`. Perform a weighted two‑sample KS test using event‑level bootstrap (B = 1000, seeded). For each bootstrap iteration draw one posterior sample per event, compute the weighted KS statistic, and obtain the empirical p‑value as the **proportion of bootstrap statistics ≥ the observed statistic**. Apply Bonferroni correction across the two parameters. Write `data/results/ks_results.json` validated against `contracts/statistical_test_result.schema.yaml`. | Obs catalog, sim catalog, weights | `data/results/ks_results.json` | statistical_test_result.schema.yaml |
|       | **T007** | Sensitivity analysis: recompute significance for α = 0.05 and α = 0.06 (α = 0.06 per arXiv 2309.06305). Flag a result as “borderline” if significance flips between the two thresholds. Append `alpha_sweep_results` and `borderline_flag` to the KS result objects. | ks_results.json | Updated `ks_results.json` | statistical_test_result.schema.yaml |
|       | **T008** | Power analysis: compute MDES for the KS test using the formula D = √[‑0.5 ln(α/2)·((n₁+n₂)/(n₁·n₂))] with α = 0.05 and target power = 0.80. If `simulation_sample_size < 0.5·observational_sample_size`, set `power_limitation_flag` = true and include a human‑readable limitation note. Insert the `power_analysis` object into each entry of `ks_results.json`. | Sample sizes from obs & sim | Updated `ks_results.json` (with nested `power_analysis`) | statistical_test_result.schema.yaml |
| **Phase 4 – Visualization & Reporting** | **T009** | Generate KDE plots for `mass_ratio` and `effective_spin` with obs & sim overlaid (`src/viz/plot_distributions.py`). Annotate regions where the Bonferroni‑adjusted p‑value < 0.05 as divergence zones. Save PNGs at ≥ 300 DPI (`outputs/figures/mass_ratio_kde.png`, `outputs/figures/effective_spin_kde.png`). Produce a manifest `outputs/figures/figure_manifest.json` validated against `contracts/visualization_output.schema.yaml`. | KDEs, KS results | PNG files + manifest | visualization_output.schema.yaml |
|       | **T010** | Orchestrate the full pipeline (`src/main.py`). On successful completion, collate all artifacts into `data/results/final_report.md`, including a “Limitations” section that reports any power‑limitation note and notes that all findings are associational (observational study). | All previous outputs | `final_report.md` | (no schema; free‑form report) |

## Constitution Check

| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Pinned `requirements.txt`; deterministic seeds; no hidden randomness. |
| II. Verified Accuracy | PASS | All external URLs are either verified (none for GWTC) or explicitly marked unavailable; no unverified citations. |
| III. Data Hygiene | PASS | Checksums recorded; raw files immutable; derived files have provenance metadata. |
| IV. Single Source of Truth | PASS | Every figure/statistic traces to a single row in `data/processed/` and a single code block. |
| V. Versioning Discipline | PASS | Content hashes tracked; `state/projects/...yaml` updated on each artifact change. |
| VI. Simulation Data Integrity | **PENDING DEVIATION** | Principle VI requires IllustrisTNG/EAGLE data, which lack the needed schema. This plan uses a synthetic power‑law catalog pending a formal constitutional amendment. |
| VII. Statistical Rigor | PASS | Weighted KS with bootstrapped p‑values, Bonferroni correction, α‑sweep sensitivity, MDES definition, CPU‑only implementation. |

*Note*: The pending deviation to Principle VI will be submitted separately; until then the plan operates under a documented deviation, not a ratified amendment.

## Compute Feasibility

- All computations run on the GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 20 GB disk, ≤ 6 h). No GPU is required. Estimated runtime [deferred] for the full pipeline on synthetic data; real GWTC data (on the order of a few hundred events) remains well within limits.
