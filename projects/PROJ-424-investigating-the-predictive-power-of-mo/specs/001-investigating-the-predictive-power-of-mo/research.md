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
- **Durations & seeds**: a brief nanosecond‑scale interval × 3 seeds, a brief nanosecond interval × 3 seeds, a brief nanosecond‑scale duration × 1 seed (total a set of trajectories). Seeds are fixed integers recorded in the pipeline.  
- **Wall‑clock monitoring**: Any simulation exceeding 5.5 h logs a performance‑issue warning (FR‑004).

### 3. Diffusion Coefficient Extraction (FR‑002, FR‑003)
- Compute MSD for all atoms using `mdtraj`.  
- Discard first 0.1 × total time (ballistic regime).  
- Fit MSD = 6 D t + C with ordinary least squares.  
- **Convergence diagnostics**: (a) linear‑fit R² ≥ 0.95; (b) log‑log MSD vs. t slope must be 1 ± 0.05. Both must pass; otherwise status =`convergence_failed`.  
- Apply Yeh‑Hummer finite‑size correction:
  \[
  D_{\text{corr}} = D_{\text{raw}} + \frac{k_{\mathrm{B}}T\,\xi}{6\pi\eta L},
  \]
  with \(\xi≈2.837297\), \(\eta\) taken from literature (water exhibits a viscosity on the order of one centipoise at 298 K., etc.).  
- Store results in `diffusion_results.csv`.

### 4. Accuracy & Uncertainty (FR‑004, FR‑008)
- Compute per‑seed absolute error \(|D_{\text{corr}} - D_{\text{exp}}|\).  
- **Bootstrap**: Resample the set of errors with replacement 1000 times (fixed count; source 1612.04126, https://arxiv.org/abs/1612.04126).  
- Derive mean MAE and [deferred] / 97.5 % percentiles → 95 % CI (SC‑003).
- **Paired descriptive comparison**: For each solvent, compare MAE at 1 ns vs. 10 ns using the same seed set; report mean difference, bootstrap‑derived CI, and a `granularity_note` explaining that with N = 3 (or 1) the minimal attainable p‑value is limited (methodology‑37736ec4). This satisfies SC‑005 without fabricating a formal p‑value.

### 5. Sensitivity Analysis (US2)
- Vary MSD start‑fraction to 0.2 and 0.3, repeat fit and compute diffusion coefficients.  
- Calculate variance‑percentage across seeds for each (solvent, duration, start_fraction).  
- Store in `sensitivity_report.json`; all variance % < 5 % is considered acceptable (implicit SC‑002, though not explicitly listed).

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
| **3 × 1 ns & 5 ns seeds, 1 × 10 ns seed** | Balances statistical precision for short durations against the 6 h wall‑clock budget; power limitation is explicitly reported (SC‑005). |
| **Exact 1000 bootstrap iterations** | Mandated by FR‑004; iteration count is justified by the cited arXiv source. |
| **Descriptive paired‑comparison with granularity note** | Avoids reporting a misleading p‑value when seed count is too low; still fulfills SC‑005 by providing a quantitative comparison. |
| **Additional log‑log slope check** | Strengthens convergence validation beyond R², directly addressing Constitution VI. |
| **Sensitivity start‑fraction sweep** | Provides robustness evidence for the 0.1 discard choice, satisfying US2. |

## Limitations & Power Considerations (methodology‑9348a9bc)

- **Small seed count** (especially for 10 ns) yields wide bootstrap CIs and limits inferential power. All tables and figures explicitly note this limitation.  
- **Finite‑size correction** relies on literature viscosity values; any systematic error in those values propagates to the corrected diffusion coefficient.  
- **Wall‑clock variability**: The reference hardware in FR‑004 (2.5 GHz, multi‑core) is faster than the CI runner; exceeding the 5.5 h threshold will be logged as a performance issue, not as a failure.

---
