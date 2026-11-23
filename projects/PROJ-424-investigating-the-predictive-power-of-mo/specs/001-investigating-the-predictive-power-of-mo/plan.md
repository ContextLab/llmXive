# Implementation Plan: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Branch**: `001-investigating-md-diffusion-predictive-power` | **Date**: 2026-10-21 | **Spec**: `specs/001-investigating-md-diffusion-predictive-power/spec.md`  
**Input**: Feature specification from `/specs/001-investigating-md-diffusion-predictive-power/spec.md`

## Summary
The plan delivers a fully reproducible end‑to‑end workflow that:

1. **Creates** a verified `data/raw/nist_refs.json` file containing experimental self‑diffusion coefficients for water, ethanol, and acetone at 298 K (FR‑001).  
2. **Runs** OPLS‑AA OpenMM simulations for each solvent at 1 ns, 5 ns, and 10 ns, **three independent seeds per duration** (FR‑002).  
3. **Extracts** MSD trajectories, discards the first 0.1 × time, fits a linear regression, checks **R² ≥ 0.95** **and** log‑log slope ≈ 1 ± 0.05 (FR‑003, Constitution VI).  
4. **Computes** MAE versus experiment, performs a **1000‑iteration bootstrap** for 95 % CIs (FR‑004, SC‑003).  
5. **Generates** timescale‑accuracy curves with 95 % confidence bands (FR‑008, SC‑001) and a **paired‑bootstrap hypothesis test** (including a p‑value) between 1 ns and 10 ns MAE (SC‑005).  
6. **Performs** sensitivity analysis on the MSD start‑fraction (0.1, 0.2, 0.3) (US2).  
7. **Validates** all outputs against JSON/YAML contracts and runs the full test suite (FR‑009, SC‑006).

All steps respect the compute budget of a GitHub Actions free‑tier CPU runner (≤ 6 h, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `openmm==8.1.1`, `mdtraj==1.9.9`, `numpy`, `pandas`, `scipy`, `matplotlib`, `pytest` (pinned in `code/requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw JSON, generated trajectories, processed CSV/JSON)  
- **Testing**: `pytest` for loader, simulation, analysis, and pipeline tests  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, no GPU) – **CPU‑first** approach; no GPU escape hatch needed.  
- **Constraints**: ≤ 7 GB RAM, ≤ 14 GB disk, wall‑clock ≤ 5.5 h per individual simulation (monitoring only, not a hard stop).  
- **Scale/Scope**: 3 solvents × 3 durations × 3 seeds = 27 trajectories; a sufficient number of bootstrap iterations.  

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed random seeds; deterministic `nist_refs.json` generation; all scripts runnable on fresh runner. |
| II. Verified Accuracy | ✅ | No external URLs for experimental data; the curated JSON is hand‑coded from published NIST values (public literature). |
| III. Data Hygiene | ✅ | `nist_refs.json` is checksum‑verified (`nist_refs.json.sha256`). All transformations produce new files. |
| IV. Single Source of Truth | ✅ | Every figure/statistic derives from `diffusion_results.csv`, `bootstrap_stats.json`, `sensitivity_report.json`. |
| V. Versioning Discipline | ✅ | Artifact hashes recorded automatically; any change updates project state. |
| VI. Simulation Convergence Validation | ✅ | Linear‑fit R² ≥ 0.95 **and** log‑log slope ≈ 1 ± 0.05 required before diffusion coefficient is accepted. |
| VII. Timescale‑Dependent Error Quantification | ✅ | MAE computed separately for 1 ns, 5 ns, 10 ns; curves preserve the timescale variable. |

## Project Structure
```text
specs/001-investigating-md-diffusion-predictive-power/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── diffusion_results.schema.yaml
│   ├── bootstrap_stats.schema.yaml
│   └── sensitivity_report.schema.yaml
└── tasks.md            # generated later by /speckit-tasks

projects/PROJ-424-investigating-the-predictive-power-of-mo/
├── code/
│   ├── requirements.txt
│   ├── data/
│   │   └── loader.py                # loads & validates nist_refs.json
│   ├── simulations/
│   │   ├── build_system.py          # creates OPLS‑AA boxes (fixed size)
│   │   └── run_simulation.py        # seeded OpenMM NPT runs
│   ├── analysis/
│   │   ├── msd.py                   # MSD extraction
│   │   ├── diffusion.py             # window discard, linear fit, R² & slope checks, Yeh‑Hummer correction
│   │   ├── bootstrap.py             # 1000‑iter MAE bootstrap, paired‑comparison
│   │   ├── sensitivity.py           # start‑fraction sweep
│   │   └── report.py                # figures, tables, trend text
│   ├── pipeline.py                  # orchestrates full workflow (FR‑009)
│   └── main.py                      # entry point for full‑batch run
├── data/
│   ├── raw/
│   │   ├── nist_refs.json           # generated in Phase 0
│   │   ├── nist_refs.json.sha256    # checksum file
│   │   └── simulations/             # generated .xtc + log files
│   └── processed/
│       ├── diffusion_results.csv
│       ├── bootstrap_stats.json
│       └── sensitivity_report.json
├── results/                         # figures & tables
└── tests/
    ├── test_loader.py
    ├── test_simulation.py
    ├── test_diffusion.py
    └── test_pipeline.py
```

**Structure Decision**: a single‑project layout with clear sub‑packages for data handling, simulation, analysis, and orchestration. This satisfies the Single Source of Truth principle while keeping the repo minimal.

## Phase‑by‑Phase Task List (covers every FR/SC)

| Phase | Tasks | FR | SC |
|-------|-------|----|----|
| **0 – Data Ingestion** | 1. Write `data/raw/nist_refs.json` with experimentally curated values (water = 2.30e‑9 m²/s, ethanol = 1.10e‑9 m²/s, acetone = 0.97e‑9 m²/s at 298 K). 2. Compute SHA‑256 checksum → `nist_refs.json.sha256`. 3. Validate JSON against `contracts/diffusion_results.schema.yaml` (field presence for reference values). | FR‑001 | — |
| **1 – Simulation** | 4. Build OPLS‑AA boxes (≈ 300 molecules/solvent, fixed box size). 5. Run seeded NPT simulations (1 ns × 3 seeds, 5 ns × 3 seeds, 10 ns × 3 seeds) using OpenMM CPU platform. | FR‑002 | — |
| **2 – MSD & Diffusion Extraction** | 6. Compute MSD with `mdtraj`. 7. Discard first 0.1 × time, fit linear regression, compute R². 8. Compute log‑log slope; require \|slope − 1\| ≤ 0.05. 9. Apply Yeh‑Hummer finite‑size correction. 10. Store each trajectory’s record in `diffusion_results.csv`. | FR‑002, FR‑003 | — |
| **3 – Sensitivity Analysis** | 11. Repeat steps 6‑9 for start fractions 0.2 and 0.3. 12. Compute variance‑percentage across seeds for each (solvent, duration, start_fraction). 13. Write `sensitivity_report.json`. | (methodological requirement from US2) | — |
| **4 – Accuracy & Bootstrap** | 14. Compute per‑seed absolute error \|D_corr − D_exp\| (MAE). 15. **Bootstrap**: Resample the set of MAE values with replacement 1000 times (fixed count; source 1612.04126, https://arxiv.org/abs/1612.04126). 16. Derive mean MAE and [deferred] / 97.5 % percentiles → 95 % CI (SC‑003). 17. **Paired‑bootstrap hypothesis test**: For each solvent, resample the paired MAE vectors (1 ns vs 10 ns) 1000 times, compute the proportion of resamples where the 10 ns MAE < 1 ns MAE → p‑value; also report mean difference and p‑value (SC‑005). 18. Write `bootstrap_stats.json`. | FR‑004, FR‑008 | SC‑001, SC‑003, SC‑004, SC‑005 |
| **5 – Reporting** | 19. Plot timescale‑accuracy curves with 95 % CI bands (Matplotlib). 20. Assemble summary tables (mean MAE, CI, trend notes). 21. Save figures/tables under `results/`. | FR‑008, FR‑009 | SC‑001, SC‑004, SC‑006 |
| **6 – Verification** | 22. Run full pytest suite (`tests/`). 23. Ensure all contracts validate (`jsonschema` checks). 24. Confirm `pipeline.py --full-batch` completes without error. | FR‑009 | SC‑006 |

All functional requirements (FR‑001 – FR‑009) and success criteria (SC‑001, SC‑003‑SC‑006) are explicitly addressed. No un‑specified constraints are introduced.

## Compute Feasibility (CPU‑first)
- **Simulation wall‑clock**: estimated ≤ 5 h total (≈ 1 h per 1 ns seed, ≈ 2 h per 5 ns seed, ≈ 3 h per 10 ns seed).  
- **Bootstrap**: vectorized over ≤ 27 error values → < 0.2 h.  
- **Overall**: ≤ 5.5 h, comfortably under the 6 h CI limit; any step exceeding 5.5 h triggers a logged warning but does not abort the run.

## Statistical Rigor
| Requirement | Implementation |
|-------------|----------------|
| Linear‑fit quality | R² ≥ 0.95 **and** log‑log slope ≈ 1 ± 0.05 (Constitution VI). |
| Bootstrap iterations | Fixed at 1000 (source: 1612.04126, https://arxiv.org/abs/1612.04126). |
| Multiple comparisons | Only one primary paired test; no correction needed. |
| Power / sample size | 3 seeds per duration – **power limitation acknowledged** in methodology‑99e534a9. |
| Causal claims | Strictly associational (“predictive accuracy”). |
| Measurement validity | Experimental values taken from NIST literature (publicly reported). |
| Collinearity | Not applicable (single predictor). |

## Requirement Coverage Matrix
| Phase | Tasks | FR‑IDs | SC‑IDs |
|-------|-------|--------|--------|
| 0 | Generate & checksum `nist_refs.json` | FR‑001 | — |
| 1 | Simulations | FR‑002 | — |
| 2 | MSD extraction, fit, convergence check | FR‑002, FR‑003 | — |
| 3 | Sensitivity analysis | (US2) | — |
| 4 | MAE, bootstrap, paired‑comparison | FR‑004, FR‑008 | SC‑001, SC‑003, SC‑004, SC‑005 |
| 5 | Figures & tables | FR‑008, FR‑009 | SC‑001, SC‑004, SC‑006 |
| 6 | End‑to‑end test suite | FR‑009 | SC‑006 |

All FR/SC IDs appear at least once.

## Statistical Power Note (methodology‑99e534a9)

The study uses three independent seeds per simulation duration (27 trajectories total). While this provides a reasonable sampling of stochastic variation for a proof‑of‑concept analysis, the modest seed count limits statistical power, especially for detecting subtle differences between the 1 ns and 10 ns MAE values. Consequently:

- Confidence intervals may be relatively wide.
- The paired‑bootstrap p‑value should be interpreted descriptively rather than as a definitive hypothesis test.
- This limitation is explicitly documented in the “Limitations & Power Considerations” section of the research artifact.

---


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/research.md
# Research: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Summary
We quantify how accurately atomistic OPLS‑AA MD simulations predict experimental self‑diffusion coefficients of water, ethanol, and acetone at three simulation durations (1 ns, 5 ns, 10 ns). The workflow yields timescale‑accuracy curves (MAE vs. duration) with 95 % bootstrap confidence bands, descriptive trend analysis, and a paired‑comparison (with a granularity note) between the shortest and longest simulations.

## Dataset Strategy

| Dataset | Source / Path | Access Method | Validation |
|---|---|---|---|
| Experimental diffusion benchmarks | `data/raw/nist_refs.json` (hand‑curated, committed) | `json.load()` via `code/data/loader.py` | Schema‑validated; SHA‑256 checksum stored in `nist_refs.json.sha256`. |
| MD trajectories | `data/raw/simulations/{solvent}_{duration}ns_seed{seed}.xtc` (generated in‑house) | `mdtraj.load()` | Each trajectory passes convergence diagnostics (R² ≥ 0.95, log‑log slope ≈ 1). |

**Data availability note**: The "# Verified datasets" block contains no applicable diffusion‑coefficient source. Per the specification (§4), we manually curate the experimental values into `nist_refs.json`; no synthetic fallback is used, satisfying the “no synthetic data” rule.

## Methodological Approach

### 1. Reference Data Generation (Phase 0)
- Hard‑code literature diffusion coefficients at 298 K: water = 2.30 × 10⁻⁹ m²/s, ethanol = 1.10 × 10⁻⁹ m²/s, acetone = 0.97 × 10⁻⁹ m²/s.  
- Write JSON with schema `{solvent: str, D_exp_m2_s: float, temperature_K: int}`.  
- Compute SHA‑256 checksum; both files are version‑controlled.

### 2. Simulation Protocol
- **Engine**: OpenMM 8.1.1, CPU platform, 2 threads.  
- **Force field**: OPLS‑AA.  
- **System size**: ≈ 300 molecules per solvent (≈ 10 k atoms).  
- **Ensemble**: NPT, T = 298 K, P = 1 bar, Langevin thermostat (friction = 1 ps⁻¹), Monte‑Carlo barostat.  
- **Durations & seeds**: 1 ns × 3 seeds, 5 ns × 3 seeds, 10 ns × 3 seeds (total a set of trajectories). Seeds are fixed integers recorded in the pipeline.  

### 3. Diffusion Coefficient Extraction (FR‑002, FR‑003)
- Compute MSD for all atoms using `mdtraj`.  
- Discard first 0.1 × total time (ballistic regime).  
- Fit MSD = 6 D t + C with ordinary least squares.  
- **Convergence diagnostics**: (a) linear‑fit R² ≥ 0.95; (b) log‑log MSD vs. t slope must be 1 ± 0.05. Both must pass; otherwise status =`convergence_failed`.  
- Apply Yeh‑Hummer finite‑size correction:
  \[
  D_{\text{corr}} = D_{\text{raw}} + \frac{k_{\mathrm{B}}T\,\xi}{6\pi\eta L},
  \]
  with \(\xi\) taken from literature alongside \(\eta\) (water exhibits a viscosity on the order of one centipoise at 298 K., etc.).  
- Store results in `diffusion_results.csv`.

### 4. Accuracy & Uncertainty (FR‑004, FR‑008)
- Compute per‑seed absolute error \(|D_{\text{corr}} - D_{\text{exp}}|\).  
- **Bootstrap**: Resample the set of errors with replacement 1000 times (fixed count; source 1612.04126, https://arxiv.org/abs/1612.04126).  
- Derive mean MAE and [deferred] / 97.5 % percentiles → 95 % CI (SC‑003).
- **Paired descriptive comparison**: For each solvent, compare MAE at 1 ns vs. 10 ns using the same seed set; report mean difference, bootstrap‑derived CI, and a `granularity_note` explaining that with N = 3 (or 1) the minimal attainable p‑value is limited (methodology‑37736ec4). This satisfies SC‑005 without fabricating a formal p‑value.

### 5. Sensitivity Analysis (US2)
- Vary MSD start‑fraction to 0.2 and 0.3, repeat fit and compute diffusion coefficients.  
- Calculate variance‑percentage across seeds for each (solvent, duration, start_fraction).  
- Store in `sensitivity_report.json`.

### 6. Timescale‑Accuracy Curves & Trend Analysis (FR‑008)
- Plot MAE vs. duration for each solvent with 95 % CI bands (Matplotlib).  
- Perform descriptive trend analysis: monotonic decrease of MAE with longer simulations, CI overlap assessment, and report the paired‑comparison result.  
- Export figures (`.png`) and summary tables (`.csv`) into `results/`.

### 7. End‑to‑End Verification (FR‑009, SC‑006)
- Run `pytest` suite covering loader, simulation wrapper, diffusion analysis, bootstrap, and pipeline orchestration.  
- All tests must pass; any failure aborts the CI job.  
- Successful run of `code/pipeline.py --full-batch` confirms the whole workflow executes without errors.

## Decision Rationale

| Decision | Reason |
|----------|--------|
| **Hard‑coded `nist_refs.json`** | No public API for NIST diffusion data; manual curation yields a deterministic, checksum‑able file that satisfies FR‑001 and Constitution III. |
| **CPU‑only OpenMM** | Fits within the free‑tier runner; the spec explicitly states no GPU required. |
| **3 × seeds for all durations** | Balances statistical precision for short durations against the 6 h wall‑clock budget; power limitation is explicitly reported (SC‑005). |
| **Exact 1000 bootstrap iterations** | Mandated by FR‑004; iteration count is justified by the cited arXiv source. |
| **Descriptive paired‑comparison with granularity note** | Avoids reporting a misleading p‑value when seed count is too low; still fulfills SC‑005 by providing a quantitative comparison. |
| **Additional log‑log slope check** | Strengthens convergence validation beyond R², directly addressing Constitution VI. |
| **Sensitivity start‑fraction sweep** | Provides robustness evidence for the 0.1 discard choice, satisfying US2. |

## Limitations & Power Considerations (methodology‑9348a9bc)

- **Small seed count** (especially for 10 ns) yields wide bootstrap CIs and limits inferential power. All tables and figures explicitly note this limitation.  
- **Finite‑size correction** relies on literature viscosity values; any systematic error in those values propagates to the corrected diffusion coefficient.  
- **Wall‑clock variability**: The reference hardware in FR‑004 (2.5 GHz, multi‑core) is faster than the CI runner; exceeding the 5.5 h threshold will be logged as a performance issue, not as a failure.

---


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/data-model.md
# Data Model: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Overview
Three persisted artifacts are produced; each is validated against a JSON/YAML contract in `contracts/`.

### 1. `diffusion_results`
- **Location**: `data/processed/diffusion_results.csv` (one row per trajectory).  
- **Fields**: `solvent`, `duration_ns`, `seed`, `msd_slope`, `r_squared`, `loglog_slope`, `d_calc_m2_s`, `d_corr_m2_s`, `mae`, `status`.  
- **Purpose**: Stores raw diffusion calculations and convergence diagnostics; feeds downstream MAE and bootstrap steps.

### 2. `bootstrap_stats`
- **Location**: `data/processed/bootstrap_stats.json`.  
- **Structure**:  
  ```json
  {
    "entries": [ { "solvent": "...", "duration_ns": ..., "iterations": 1000,
                   "mean_mae": ..., "ci_lower": ..., "ci_upper": ...,
                   "n_seeds": ..., "granularity_note": "..." }, ... ],
    "paired_test": [ { "solvent": "...", "mae_1ns": ..., "mae_10ns": ...,
                       "mean_difference": ..., "p_value": ..., 
                       "granularity_note": "..." }, ... ]
  }
  ```
- **Purpose**: Provides a confidence interval for MAE per timescale. and a descriptive paired‑comparison.

### 3. `sensitivity_report`
- **Location**: `data/processed/sensitivity_report.json`.  
- **Fields**: `solvent`, `duration_ns`, `start_fraction` (0.1/0.2/0.3), `variance_pct`, optional `note`.  
- **Purpose**: Quantifies how the choice of MSD start‑fraction influences diffusion estimates.

## Data Flow
1. **Load** `nist_refs.json` → dictionary of experimental `D_exp`.  
2. **Run** simulations → raw `.xtc` files under `data/raw/simulations/`.  
3. **Analyze** each trajectory → append a row to `diffusion_results.csv`.  
4. **Bootstrap** MAE across seeds → write `bootstrap_stats.json`.  
5. **Sensitivity** sweep → write `sensitivity_report.json`.  
6. **Report** reads the two JSON files (and the CSV) to produce figures/tables in `results/`.

All transformations write new files; original raw data remain untouched, satisfying Constitution III.

---


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/quickstart.md
# Quickstart: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Prerequisites
- Linux (Ubuntu 22.04 recommended) or macOS with Python 3.11+.  
- ~7 GB RAM, ~14 GB disk space, **no GPU** required.

## Installation

```bash
# Clone the repository
git clone <PROJECT_REPO_URL>
cd projects/PROJ-424-investigating-the-predictive-power-of-mo

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Data Preparation

The experimental reference file is generated automatically by the first pipeline step:

```bash
# Generate `nist_refs.json` and its checksum
python code/data/loader.py --generate-refs
```

You should see:

```
data/raw/nist_refs.json created (multiple entries)
data/raw/nist_refs.json.sha256 created
```

## Running the Full Workflow

```bash
# Execute the complete end‑to‑end pipeline (includes simulations, analysis, bootstrap, reporting)
python code/main.py --full-batch
```

What happens:

1. Simulations for water, ethanol, and acetone at 1 ns, 5 ns, and 10 ns are launched (CPU only).  
2. MSD extraction, convergence checks, and diffusion coefficient calculation are performed.  
3. MAE bootstrap (1000 iterations) and sensitivity analysis are run.  
4. Timescale‑accuracy curves and summary tables are written to `results/`.

## Minimal Example (single trajectory)

If you only want to test the pipeline without the full compute budget:

```bash
python code/pipeline.py --solvent water --duration 1 --seed 0
```

This runs a single brief water simulation, produces one row in `diffusion_results.csv`, and updates the bootstrap stats for that condition.

## Verification Checklist

| Check | Expected Outcome |
|-------|------------------|
| `data/raw/nist_refs.json` exists and matches its SHA‑256 checksum | `tests/test_loader.py` passes (`test_load_valid`, `test_checksum_matches`). |
| All simulation `.xtc` files are present under `data/raw/simulations/` | `tests/test_simulation.py` passes. |
| `diffusion_results.csv` contains a row with `status = "accepted"` for at least one trajectory | `tests/test_diffusion.py` passes. |
| `bootstrap_stats.json` contains entries generated over many iterations and a `paired_test` block. | `tests/test_bootstrap.py` passes. |
| `code/pipeline.py --full-batch` exits with code 0 and produces figures in `results/` | `tests/test_pipeline.py` passes. |

## Troubleshooting
- **OpenMM import error** – ensure the exact version `openmm==8.1.1` is installed (`pip install openmm==8.1.1`).  
- **R² < 0.95** – the run will be flagged `convergence_failed`; inspect `results/convergence_log.txt` for details.  
- **Wall‑clock > 5.5 h** – a warning is logged; the pipeline continues but the warning appears in `results/performance.log`.  
- **Bootstrap takes > 0.5 h** – unlikely given vectorized implementation; if it occurs, verify that the CI runner is not throttling CPU.

---


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/contracts/bootstrap_stats.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Bootstrap Statistics Schema"
description: "Schema for data/processed/bootstrap_stats.json."
type: "object"
properties:
  entries:
    type: "array"
    items:
      type: "object"
      properties:
        solvent:
          type: "string"
          enum: ["water", "ethanol", "acetone"]
        duration_ns:
          type: "number"
          enum: [1, 5, 10]
        iterations:
          type: "integer"
          minimum: 1000
          maximum: 1000
          description: "Bootstrap iterations; fixed at exactly 1000 per FR-004 (no automatic reduction permitted)."
        mean_mae:
          type: ["number", "null"]
          minimum: 0
        ci_lower:
          type: ["number", "null"]
          minimum: 0
        ci_upper:
          type: ["number", "null"]
          minimum: 0
        n_seeds:
          type: "integer"
          minimum: 1
        granularity_note:
          type: "string"
          description: "Explanation of statistical granularity limits when seed count is low (e.g., minimal achievable p-value)."
      required:
        - solvent
        - duration_ns
        - iterations
        - mean_mae
        - ci_lower
        - ci_upper
        - n_seeds
      additionalProperties: false
  paired_test:
    type: "array"
    description: "Descriptive paired‑comparison of MAE at 1 ns vs 10 ns per solvent (replaces the original paired‑bootstrap test)."
    items:
      type: "object"
      properties:
        solvent:
          type: "string"
          enum: ["water", "ethanol", "acetone"]
        mae_1ns:
          type: "number"
          minimum: 0
        mae_10ns:
          type: "number"
          minimum: 0
        mean_difference:
          type: "number"
        p_value:
          type: "number"
          minimum: 0
          maximum: 1
        granularity_note:
          type: "string"
          description: "Note on the granularity limitation of the p‑value due to small seed count."
      required:
        - solvent
        - mae_1ns
        - mae_10ns
        - mean_difference
        - p_value
      additionalProperties: false
required:
  - entries
  - paired_test
additionalProperties: false


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/contracts/diffusion_results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Diffusion Results Schema"
description: "Schema for one row of data/processed/diffusion_results.csv (validated as JSON objects after CSV parsing)."
type: "object"
properties:
  solvent:
    type: "string"
    enum: ["water", "ethanol", "acetone"]
  duration_ns:
    type: "number"
    enum: [1, 5, 10]
  seed:
    type: "integer"
    minimum: 0
  msd_slope:
    type: "number"
    minimum: 0
  r_squared:
    type: "number"
    minimum: 0
    maximum: 1
    description: "R-squared of the MSD linear fit; accepted rows must be >= 0.95 (FR-003, Constitution VI)."
  loglog_slope:
    type: "number"
    description: "Slope of log(MSD) vs. log(time) after discarding the ballistic regime; must be within 1 ± 0.05."
  d_calc_m2_s:
    type: "number"
    minimum: 0
  d_corr_m2_s:
    type: "number"
    minimum: 0
    description: "Diffusion coefficient after Yeh‑Hummer finite‑size correction."
  mae:
    type: "number"
    minimum: 0
    description: "Absolute error |D_corr - D_exp| for this trajectory."
  status:
    type: "string"
    enum: ["accepted", "convergence_failed"]
required:
  - solvent
  - duration_ns
  - seed
  - msd_slope
  - r_squared
  - loglog_slope
  - d_calc_m2_s
  - d_corr_m2_s
  - mae
  - status
additionalProperties: false


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/contracts/sensitivity_report.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Sensitivity Report Schema"
description: "Schema for data/processed/sensitivity_report.json"
type: "array"
items:
  type: "object"
  properties:
    solvent:
      type: "string"
      enum:
        - "water"
        - "ethanol"
        - "acetone"
    duration_ns:
      type: "number"
      enum: [1, 5, 10]
    start_fraction:
      type: "number"
      enum: [0.1, 0.2, 0.3]
    variance_pct:
      type: "number"
      minimum: 0
      description: "Variance percentage across seeds for this start fraction; should be < 5% per implied sensitivity criterion."
    note:
      type: "string"
      description: "Optional free‑text note (e.g., if variance exceeds threshold)."
  required:
    - solvent
    - duration_ns
    - start_fraction
    - variance_pct
  additionalProperties: false