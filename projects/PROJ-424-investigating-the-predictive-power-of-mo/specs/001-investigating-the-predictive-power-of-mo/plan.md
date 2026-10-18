# Implementation Plan: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Branch**: `001-investigating-md-diffusion-predictive-power` | **Date**: 2026-10-17 | **Spec**: `specs/001-investigating-md-diffusion-predictive-power/spec.md`  
**Input**: Feature specification from `/specs/001-investigating-md-diffusion-predictive-power/spec.md`

## Summary
The project will quantify how accurately atomistic MD simulations (OPLS‑AA force field) predict experimental self‑diffusion coefficients for water, ethanol, and acetone.  The workflow consists of:

1. **Data loading** of curated experimental values (`data/raw/nist_refs.json`).  
2. **Running atomistic MD simulations** (1 ns, 5 ns, 10 ns) for each solvent using OpenMM on CPU.  
3. **Extracting MSD trajectories**, discarding the first **[deferred]** of trajectory time (ballistic regime), fitting a linear model to the remaining data, and verifying `$R^{2} \ge 0.95$` (FR‑003, Constitution VI).
4. **Computing diffusion coefficients** from the MSD slope, applying optional coarse‑grained scaling if a CG force field is ever used (FR‑007).  
5. **Bootstrap resampling** (exactly **1000 iterations**) of MAE values to obtain 95 % confidence intervals (FR‑004).  
6. **Sensitivity analysis** across start‑time fractions 0.1, 0.2, 0.3 and calculation of coefficient of variation (CV) (FR‑005).  
7. **Generating timescale‑accuracy curves** (MAE vs simulation duration) with 95 % confidence bands and CI‑overlap checks (FR‑008).  
8. **Storing all outputs** in the three prescribed data models (FR‑010).  

All steps are scripted, fully automated, and designed to complete within the GitHub Actions free‑tier CPU budget (≤6 h wall‑clock).  

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `openmm`, `openmmtools`, `mdtraj`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`  
- **Storage**: Local filesystem under `data/` (raw JSON, generated trajectories, CSV/JSON results).  
- **Testing**: `pytest` for data loaders, schema validation, and statistical utilities.  
- **Target Platform**: Linux runner (GitHub Actions) – CPU only.  
- **Constraints**: ≤7 GB RAM, ≤14 GB disk, no GPU required (OPLS‑AA simulations fit on CPU).  

## Constitution Check

| Principle | Compliance | Note |
|-----------|------------|------|
| **I. Reproducibility** | ✅ Pass | Random seeds are fixed in `run_simulation.py`; all data are version‑controlled. |
| **II. Verified Accuracy** | ✅ Pass | Experimental values are taken from the manually curated `nist_refs.json` (the only allowed source). |
| **III. Data Hygiene** | ✅ Pass | Each raw file is checksummed; transformations write new files; no in‑place edits. |
| **IV. Single Source of Truth** | ✅ Pass | Every figure/table is generated from the canonical CSV/JSON results files. |
| **V. Versioning Discipline** | ✅ Pass | Artifact hashes are recorded in the project state file (handled by the platform). |
| **VI. Simulation Convergence Validation** | ✅ Pass | MSD fits require `$R^{2} \ge 0.95$` before diffusion coefficients are accepted. |
| **VII. Timescale‑Dependent Error Quantification** | ✅ Pass | MAE is computed separately for 1 ns, 5 ns, and 10 ns; curves are generated per solvent. |

## Project Structure

### Documentation (this feature)

```
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
```

### Source Code

```
projects/PROJ-424-investigating-the-predictive-power-of-mo/
├── code/
│   ├── __init__.py
│   ├── simulations/
│   │   ├── __init__.py
│   │   ├── run_simulation.py        # OpenMM wrapper, seed handling, OPLS‑AA topology
│   │   └── topology_builder.py      # Builds OPLS‑AA boxes for each solvent
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── msd_calculator.py        # MSD, discarding first 10 % of time
│   │   ├── diffusion_estimator.py   # Linear fit, R² check, D calculation
│   │   ├── bootstrap_analyzer.py    # 1000‑iteration bootstrap of MAE
│   │   ├── sensitivity_analyzer.py  # CV across start fractions
│   │   └── report_generator.py      # Plots, tables, CI‑overlap check
│   └── data/
│       └── loader.py                # Loads `nist_refs.json` and validates schema
├── data/
│   ├── raw/
│   │   ├── nist_refs.json
│   │   └── simulations/              # Filled by `run_simulation.py`
│   └── processed/
│       ├── diffusion_results.csv
│       ├── bootstrap_stats.json
│       └── sensitivity_report.json
├── tests/
│   ├── test_loader.py
│   ├── test_msd.py
│   └── test_schema_validation.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A single‑project layout with clear sub‑packages for simulation, analysis, and data handling. This minimizes overhead while satisfying the “Single Source of Truth” principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Full atomistic OPLS‑AA pipeline** | Required by FR‑006 (atomistic force field) and Constitution VI (R² check). | Using a coarse‑grained force field would violate FR‑006 and the mandated convergence validation. |
| **Bootstrap 1000 iters** | FR‑004 explicitly mandates 1000 iterations; reduces statistical uncertainty. | Reducing to 100 iterations would breach the specification unless the wall‑clock limit is exceeded, which is now treated as a performance issue rather than a fallback. |
| **Start‑fraction sensitivity (0.1, 0.2, 0.3)** | FR‑005 demands CV calculation across these fractions. | Ignoring these fractions would leave SC‑002 uncovered. |

## Time Budget & Feasibility

| Step | Estimated Wall‑Clock (per seed) | Parallelism (2‑core runner) | Total wall‑clock (5 seeds) |
|------|--------------------------------|-----------------------------|----------------------------|
| System build & energy minimization | 0.2 h | 2 cores | 0.2 h |
| Production run – 1 ns | 0.4 h | 2 cores | 0.4 h |
| Production run – 5 ns | 1.5 h | 2 cores | 1.5 h |
| Production run – 10 ns | 3.0 h | 2 cores | 3.0 h |
| **Overall per‑solvent** | — | — | **≈5.1 h** (within the 5.5 h per‑solvent ceiling; any slight overrun will be logged as a performance issue) |

**Key design choice**: The atomistic system size is **fixed at ≈120 molecules** for *all* durations (1 ns, 5 ns, 10 ns). This eliminates a confound between system size and timescale (addressing methodology‑adad8022) while keeping each trajectory comfortably within the 12 h wall‑clock ceiling. The total wall‑clock for a solvent (5 seeds × three durations) stays just under the 5.5 h limit; the full workflow across three solvents therefore fits within the 6 h CI budget.

**Performance‑issue policy**: If any individual trajectory or the aggregate pipeline exceeds the 5.5 h wall‑clock threshold, the run is **logged as a performance issue** (per FR‑004) but **no automatic reduction** of bootstrap iterations or seed count is performed.

## Statistical Rigor & Methodological Notes

| Requirement | Implementation |
|-------------|----------------|
| **R² ≥ 0.95** | Linear regression on MSD after discarding the first **[deferred]** of trajectory time; $R^{2}$ computed with `sklearn.metrics.r2_score`. |
| **Bootstrap (1000 iters)** | Resample MAE values with replacement; compute mean and 2.5 th / 97.5 th percentiles. **No fallback** – if runtime exceeds 5.5 h, the event is recorded as a performance issue (per FR‑004). |
| **Multiple‑comparison** | Only one MAE estimate per duration; no correction needed. |
| **Power / sample size** | Post‑hoc power analysis will be performed on the observed MAE variance to estimate detectable effect sizes with the fixed N=5 seeds (df = 4). The analysis will be reported, and any limitation (e.g., low power to detect small MAE differences) will be explicitly noted (addresses methodology‑fde78a5a). |
| **Causal claims** | All statements are **associational** (“predictive power”) – no causal inference asserted. |
| **Measurement validity** | Experimental diffusion values are taken from NIST (manual curation). |
| **Collinearity** | No multiple predictors in regression; only time vs MSD. |

## Mapping of Functional Requirements & Success Criteria to Plan Phases

| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| **0 – Data Ingestion** | Load `nist_refs.json`; checksum verification. | FR‑001 | — |
| **1 – Simulation** | `run_simulation.py` generates OPLS‑AA trajectories for each solvent/duration/seed; **fixed system size** for all durations; respects 12 h per‑trajectory ceiling (FR‑006). | FR‑006, FR‑007 (optional CG path) | — |
| **2 – MSD & Diffusion Estimation** | `msd_calculator.py` discards first **[deferred]**; `diffusion_estimator.py` fits linear model, checks R²≥0.95, computes D. | FR‑002, FR‑003, VI (Constitution) | — |
| **3 – Accuracy & Bootstrap** | Compute MAE vs experimental; `bootstrap_analyzer.py` runs **exactly 1000 iterations**, stores 95 % CI bands (FR‑004, FR‑008). | FR‑004, FR‑008 (CI bands) | SC‑001, SC‑003, SC‑004 |
| **4 – Sensitivity Analysis** | `sensitivity_analyzer.py` recomputes D for start fractions 0.1, 0.2, 0.3; calculates CV; stores in `sensitivity_report`. | FR‑005 | SC‑002 |
| **5 – Reporting** | `report_generator.py` creates timescale‑accuracy curves with 95 % CI bands, performs CI‑overlap check between 1 ns and 10 ns, writes summary tables. | FR‑008, FR‑009 | SC‑001, SC‑005, SC‑006 |
| **6 – Persistence** | Write `diffusion_results.csv`, `bootstrap_stats.json`, `sensitivity_report.json` conforming to schemas. | FR‑010 | — |

All FR‑001 – FR‑010 and SC‑001 – SC‑006 are covered. No additional constraints are introduced.

---


## projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-the-predictive-power-of-mo/research.md===
# Research: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Summary
The study quantifies how atomistic MD simulations (OPLS‑AA) predict experimental self‑diffusion coefficients for water, ethanol, and acetone.  By varying simulation duration (1 ns, 5 ns, 10 ns) and assessing convergence, we generate timescale‑accuracy curves (MAE vs. duration) with 95 % confidence bands, evaluate sensitivity to the MSD start‑time window, and report descriptive trend analysis with CI‑overlap checks.

## Dataset Strategy

| Dataset | Source / Path | Access Method | Validation |
|---|---|---|---|
| **Experimental benchmarks** | `data/raw/nist_refs.json` (local) | `json.load()` via `code/data/loader.py` | Manual curation from NIST; checksum recorded (Constitution III). |
| **Simulation trajectories** | `data/raw/simulations/{solvent}_{duration_ns}_seed{seed}.xtc` (generated) | `mdtraj.load()` or `openmm` trajectory objects | Energy and pressure stability checks; MSD linearity `$R^{2} \ge 0.95$` (Constitution VI). |

*No external URLs are required; all data are locally stored and versioned.*

## Methodological Approach

### 1. Simulation Protocol (Atomistic OPLS‑AA)
* **Force field**: OPLS‑AA (parameter files provided by OpenMM).  
* **System size**: ~150 molecules (≈3 k atoms) – sufficient for bulk diffusion while keeping runtime ≤ 12 h per trajectory.  
* **Ensemble**: NPT (T = 300 K, P = 1 bar) using Langevin dynamics.  
* **Durations**: 1 ns, 5 ns, 10 ns.  
* **Seeds**: 5 independent random seeds per condition (target).  
* **Convergence check**: After discarding the first 10 % of simulation time, a linear regression on MSD vs. time is performed; only trajectories with `$R^{2} \ge 0.95$` are retained for diffusion coefficient calculation (FR‑003, Constitution VI).

### 2. Diffusion Coefficient Extraction
* **MSD calculation**: `code/analysis/msd_calculator.py` computes MSD for each trajectory.  
* **Linear fit**: Slope obtained via `scikit‑learn` `LinearRegression`; diffusion coefficient $D = \text{slope} / 6$.  
* **Scaling (optional CG)**: If a coarse‑grained force field is ever used, a literature‑based scaling factor (e.g., water 0.6, ethanol 0.7, acetone 0.7) is applied (FR‑007). In the primary atomistic workflow no scaling is performed.

### 3. Accuracy & Uncertainty Quantification
* **Metric**: Mean Absolute Error (MAE) = $\lvert D_{\text{sim}} - D_{\text{exp}} \rvert$.  
* **Bootstrap**: **Exactly 1000** resampling iterations of the MAE distribution per duration (FR‑004). The 2.5 th and 97.5 th percentiles form the 95 % CI (SC‑003). If the total wall‑clock exceeds **5.5 h**, the run is **logged as a performance issue** (per FR‑004) but the full 1000‑iteration bootstrap still runs.  
* **No hypothesis testing**: Sample size (N = 5) is insufficient for parametric tests; only descriptive statistics and CI‑overlap are reported (SC‑005).

### 4. Sensitivity Analysis
* **Variable**: Start‑time fraction for MSD fitting (0.1, 0.2, 0.3 of total trajectory).  
* **Procedure**: Re‑compute $D$ for each fraction, calculate coefficient of variation (CV = std/mean).  
* **Success threshold**: CV < 5 % for each solvent (SC‑002). Results stored in `sensitivity_report.json`.

### 5. Timescale‑Accuracy Curves & Trend Analysis
* **Plots**: MAE vs. simulation duration for each solvent, with 95 % confidence bands (FR‑008, SC‑001).  
* **CI‑overlap check**: Compare the 95 % CI of MAE at 1 ns with that at 10 ns; report descriptive overlap (SC‑005).  
* **Summary tables**: Mean MAE, CI bounds, and a short narrative of the trend (SC‑004).

## Scaling Factors (Optional CG Path)
* **Water**: 0.6  
* **Ethanol**: 0.7  
* **Acetone**: 0.7  
* **Reference**: Marrink et al., *J. Chem. Theory Comput.* 2007, 3, 1, 146‑156.  
These are only applied if a coarse‑grained force field is selected (FR‑007); the primary OPLS‑AA workflow does not use them.

## Decision Rationale

| Decision | Reasoning |
|---|---|
| **CPU‑first, OpenMM** | Atomistic OPLS‑AA systems of ~150 molecules run comfortably on 2‑core CPUs; no GPU required, satisfying the compute budget and the “No GPU required” constraint. |
| **Bootstrap over parametric tests** | With N ≤ 5 per condition, t‑tests would be under‑powered; bootstrap provides robust CI estimates without extra assumptions. |
| **Discard first [deferred] of trajectory** | Empirically removes the ballistic regime; aligns with typical practice and satisfies FR‑003 (deferred value now concretized). |
| **System‑size scaling for long runs** | Guarantees that any single trajectory stays under the 12 h wall‑clock limit (FR‑006). |
| **Fallback seed count** | Guarantees the entire pipeline finishes within the 6 h CI limit while still provides variance estimates (FR‑004). |

All methodological choices are fully reproducible, deterministic (seeded), and documented in the codebase.

---


