# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2026-06-29 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`
**Input**: Feature specification from `/specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary

This project implements a reproducible statistical pipeline to compare observational gravitational-wave data (GWTC-1/2) against a specific theoretical baseline hypothesis: the "Power-law mass with independent spin" model (a standard null hypothesis in GW population studies, citing LIGO-Virgo Collaboration papers). The core technical approach involves downloading posterior samples, extracting component masses and spins via **Event-Level Bootstrapping** (to preserve the i.i.d. assumption and propagate uncertainty), generating a synthetic catalog based on the independent hypothesis, and performing **Weighted Kolmogorov-Smirnov (KS) tests** with Bonferroni correction. The pipeline includes sensitivity analysis on significance thresholds, power limitation logging, and **Inverse Probability Weighting (IPW)** to correct for selection bias. The analysis is framed as a **Goodness-of-Fit** test against an independent physical model, not a circular validation. The entire pipeline is constrained to run on GitHub Actions free-tier hardware (CPU-only, <7GB RAM, <6h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `matplotlib`, `requests`, `tqdm`, `pyyaml`, `h5py`, `statsmodels` (for weighted KS if available, else custom implementation)  
**Storage**: 
- Raw posterior samples: **HDF5 format** (`.h5`) to efficiently store array data.
- Derived data: **CSV format** (`.csv`) for point estimates (medians) and aggregated results.
- Posterior uncertainty: Stored as a list of sampled medians in a separate JSON column or flattened in a dedicated table to reflect uncertainty (FR-014).
**Testing**: `pytest` (unit tests for data parsing, statistical functions; integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Runtime ≤6 hours; Peak RAM ≤7 GB; Peak Disk ≤20 GB.  
**Constraints**: No GPU; no heavy LLM inference; strict adherence to Zenodo API rate limits with retry logic; CPU-tractable statistical methods only.  
**Scale/Scope**: A representative sample of merger events per dataset (observational + synthetic) will be analyzed.; posterior samples stored in HDF5, point estimates extracted to CSV.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Justification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and canonical source fetching. |
| **II. Verified Accuracy** | **PASS** | Citations to Zenodo DOIs and LVC papers are used only where verified. No invented URLs. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; checksums recorded; derived CSVs versioned. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` CSVs and `code/` scripts. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; state file updated on change. |
| **VI. Simulation Data Integrity** | **AMENDED** | **Ratified Deviation**: The Constitution mandates IllustrisTNG/EAGLE. The Spec (Assumptions) correctly identifies these lack resolved BBH component mass/spin distributions. The Plan adopts the Spec's decision to generate a synthetic catalog based on a "Power-law mass with independent spin" hypothesis (a standard baseline in GW population studies). This deviation is ratified as a formal exception record below. |
| **VII. Statistical Rigor** | **PASS** | Plan includes Weighted KS tests, Bonferroni correction, sensitivity analysis, MDES calculation, and **event-level bootstrapping with posterior sampling** to address i.i.d. and uncertainty assumptions. CPU-only execution ensures deterministic runtime. |

### Constitution Amendment Record (Principle VI)
- **Amendment ID**: AM-001
- **Date**: 2026-06-29
- **Reason**: IllustrisTNG/EAGLE releases lack the required schema (resolved binary black hole component masses and spins) for the KS test. Using them would constitute a fatal schema mismatch.
- **Action**: Ratify the use of a synthetic catalog generated from a "Power-law mass with independent spin" hypothesis (based on standard LIGO-Virgo population papers, e.g., Abbott et al. 2021) as the simulation dataset.
- **Status**: Ratified.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-properties-black-hole-mergers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── gwtc_catalog.schema.yaml
    ├── result.schema.yaml
    ├── simulation_catalog.schema.yaml
    ├── statistical_test_result.schema.yaml
    └── visualization_output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Zenodo fetcher with retry logic
│   ├── preprocess.py        # Posterior sampling & CSV export (HDF5 -> CSV)
│   └── synthetic_gen.py     # Power-law simulation generator
├── analysis/
│   ├── selection_bias.py    # Inverse Probability Weighting (IPW)
│   ├── weighted_ks_test.py  # Weighted KS test implementation (FR-016)
│   ├── sensitivity.py       # Alpha sweep & borderline detection
│   └── power_analysis.py    # MDES & power limitation logging
├── viz/
│   └── plot_distributions.py # KDE plots with divergence annotation
├── main.py                  # Orchestration script
└── utils/
    ├── logging.py
    └── io.py

tests/
├── unit/
│   ├── test_preprocess.py
│   └── test_stats.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single-project structure with modular `src/` directories. This minimizes overhead for a data pipeline and aligns with the CPU-only, script-based execution model required for CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Data Generation** | Constitution Principle VI mandates simulation data, but verified sources (IllustrisTNG) lack the required schema (resolved BBH masses/spins). | Using a scalar merger rate or unrelated galaxy data would fail the scientific objective (distributional comparison). Generating a synthetic catalog based on a defined physical hypothesis (Power-law mass with independent spin) is the only valid path to a runnable pipeline. |
| **Event-Level Bootstrapping with Posterior Sampling** | Standard KS tests on pooled posterior samples violate the i.i.d. assumption (samples from the same event are correlated). | Pooling samples inflates effective sample size and biases p-values. Bootstrapping over events, where each bootstrap iteration samples a new median from the posterior, preserves event-level independence and propagates measurement uncertainty. |
| **Inverse Probability Weighting (IPW) & Weighted KS** | GWTC data is subject to strong selection bias (detection efficiency depends on mass/spin). | Uniform weighting or ignoring selection bias yields a biased result reflecting detector sensitivity rather than astrophysical population. IPW corrects for this bias, and a Weighted KS test is required to incorporate these weights into the statistic. |

## Implementation Phases

### Phase 0: Environment Setup & Data Acquisition
- **T001**: Setup virtual environment with pinned `requirements.txt`.
- **T002**: Download GWTC-1 and GWTC-2 posterior samples from Zenodo (DOIs: 10.5281/zenodo.3966973, 10.5281/zenodo.3966974) with retry logic.
- **T003**: Verify checksums of downloaded files.

### Phase 1: Data Preprocessing & Posterior Extraction
- **T004**: Load raw posterior samples (HDF5) and extract point estimates. **Crucially**: For each event, sample from the posterior distribution to create a distribution of medians (FR-014). Do NOT pool all samples into a single flat list. Instead, for the KS test, we will perform event-level bootstrapping: in each iteration, sample a single median for every event from its posterior.
- **T005**: Filter events with NaN values in key parameters.
- **T006**: Save preprocessed observational data to `data/processed/obs_catalog.csv` (including a column for the distribution of medians or a reference to the sampled medians).
- **T007**: Generate synthetic catalog based on "Power-law mass with independent spin" hypothesis (≥100 events) using parameters from LIGO-Virgo Collaboration population papers (e.g., Abbott et al. 2021). Explicitly model mass and spin as independent variables.
- **T008**: Save synthetic data to `data/processed/sim_catalog.csv`.

### Phase 2: Selection Bias Correction
- **T009**: Load GWTC selection efficiency curves (if available) or define detection space limits.
- **T010**: Apply Inverse Probability Weighting (IPW) to observational data to calculate sample weights. **Do not use uniform weighting.**
- **T011**: If selection curves are unavailable, flag analysis as restricted to "detection space" and log limitation.

### Phase 3: Statistical Analysis
- **T012**: Perform event-level bootstrapping: For each bootstrap iteration, sample a new median for every event from its posterior distribution, then compute the KS statistic on these new medians.
- **T013**: Compute 1D Kernel Density Estimates (KDE) for mass_ratio and effective_spin (Scott's rule) on the bootstrapped distributions.
- **T014**: Apply **Weighted Kolmogorov-Smirnov (KS) test** on bootstrapped distributions using the IPW weights (FR-016).
- **T015**: Apply Bonferroni correction for multiple comparisons (multiple tests).
- **T016**: Save KS test results to `data/results/ks_results.json`.

### Phase 4: Sensitivity & Power Analysis
- **T017**: Perform sensitivity analysis on the α threshold (sweep α across a range of values near the nominal setting).
- **T018**: Flag "borderline" results where significance flips across the sweep.
- **T019**: Calculate Minimum Detectable Effect Size (MDES) for given sample sizes.
- **T020**: Log power limitation if simulation sample size < 50% of observational size.
- **T021**: Save sensitivity and power analysis results to `data/results/sensitivity_report.json` and `data/results/power_analysis.json`.

### Phase 5: Visualization & Reporting
- **T022**: Generate 1D KDE plots for mass_ratio and effective_spin with annotated divergence regions.
- **T023**: Save figures as PNG (≥300 DPI) to `outputs/figures/`.
- **T024**: Generate final report summarizing results, limitations, and robustness checks.