# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Inputs**: `specs/001-testing-the-isotropy-cosmic-expansion/spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`

The tasks below implement the complete end-to-end analysis required by the specification, respect all constitutional and scientific requirements, and address the reviewer-identified failures (lint task and broken download URL). Tasks are ordered to respect data flow; each task lists its verification steps.

---

## Phase 1 – Setup and first end-to-end analysis

- [ ] **T014** Power analysis and data verification (plan Phase 0) <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis_execution.yaml exit=-1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis_execution.yaml exit=-1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 -->
  - **Data verification**: fetch the Pantheon+ file from the verified URL `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon+_SH0ES.dat` — HTTP 404], compute its SHA-256 checksum, and record `dataset_version`, `source_url`, `sha256` in `data/raw/metadata.json`. Confirm HTTP 200 reachability and that the required columns (`ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`) are present in the header.
  - **Analytic power estimate**: given the Pantheon+ sample size (N ≈ 1500) and typical per-SN distance-modulus uncertainty, compute the minimum dipole amplitude detectable at p < 0.05 with ≥ 80 % power; write the estimate and derivation to `data/processed/power_analysis.json`.
  - **Pilot Monte-Carlo power study**: generate a modest set (≥ 500) of pilot isotropic mock catalogs using the shared rotation utilities defined for T006 (implemented in `code/rotations.py` independently of T006's execution — this task does not depend on T006 having run) plus injected-dipole catalogs at the analytic threshold, and empirically confirm the detection power; append `empirical_power` and `min_detectable_dipole_mag` to `power_analysis.json`.
  - **Verification**: `data/raw/metadata.json` contains a checksum matching the computed SHA-256; `power_analysis.json` exists with finite analytic and empirical power estimates; the empirical power at the analytic threshold is within 0.15 of 0.80 (or the discrepancy is documented in the JSON with an explanation).

- [ ] **T001** Download Pantheon+ dataset and verify provenance
  - Fetch the official Pantheon+ file from a verified URL
    `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon+_SH0ES.dat` — HTTP 404]
    and store it as `data/raw/pantheon_plus.dat`.
  - Compute its SHA-256 checksum, write a provenance file `data/raw/metadata.json` containing the fields `dataset_version`, `source_url`, and `sha256` (reusing/confirming the verification performed in T014).
  - **Verification**: `data/raw/pantheon_plus.dat` exists, the checksum in `metadata.json` matches the computed hash, and the URL is reachable (HTTP 200).

- [ ] **T002** Ingest data, apply systematics, and compute residuals
  - Parse `data/raw/pantheon_plus.dat`, keep required columns (`ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`).
  - Filter out rows with missing or non-finite values; log the number of excluded supernovae.
  - Extract cosmological parameters (`H0`, `Ω_m`, `Ω_Λ`) from the file header; if absent, fall back to Planck 2018 priors (`H0 = 67.4`, `Ω_m = 0.315`, `Ω_Λ = 0.685`).
  - Compute the theoretical distance modulus using numerical integration of \(1/E(z)\) (`scipy.integrate.quad`, tolerance 1e-6) and calculate residuals \(\Delta\mu = \mu_{\rm obs} - \mu_{\rm th}\).
  - Write `data/processed/residuals.csv` conforming to `contracts/residuals.schema.yaml`.
  - **Verification**:
    1. Row count equals the official Pantheon+ “full” sample size minus the excluded rows.
    2. For the 10-supernova subset listed in the spec, residuals match published values within the reported uncertainties.

- [ ] **T003** Project residuals onto a HEALPix grid (Nside = 32)
  - Load `data/processed/residuals.csv`.
  - Use `healpy.ang2pix` to assign each supernova to a pixel; compute the inverse-variance-weighted mean residual and the number of contributors per pixel.
  - Build a mask (`mask_value = 1` for pixels with ≥ 1 supernova, else 0).
  - Write the map to `data/processed/healpix_map.fits` adhering to `contracts/healpix_map.schema.yaml`.
  - Record the fraction of valid supernovae successfully mapped (SC-001).
  - **Verification**: The FITS file validates against its schema and the recorded mapping fraction is stored in `data/processed/mapping_metrics.json`.

- [ ] **T004** Cross-check estimator – weighted least-squares dipole/quadrupole fit
  - Perform a weighted least-squares fit directly on the individual residuals using the full inverse-variance covariance matrix. This is a *cross-check* estimator; the official FR-004 result is the pseudo-\(C_\ell\) MASTER analysis in T005.
  - Extract dipole (\(\ell=1\)) and quadrupole (\(\ell=2\)) amplitudes (units mag) and write them to `data/processed/primary_fit.json`.
  - **Verification**: On a synthetic dataset with an injected dipole of 0.04 mag, the recovered dipole amplitude differs by < 1 × 10⁻³ mag.

- [ ] **T005** Official FR-004 estimator – pseudo-\(C_\ell\) analysis with MASTER mask correction
  - Using the HEALPix map from **T003**, compute pseudo-\(C_\ell\) coefficients up to \(\ell=3\) with `healpy.anafast` and apply the MASTER mode-coupling correction.
  - Convert the coefficients to scalar amplitudes \(A_\ell\) and write dipole/quadrupole amplitudes to `data/processed/pseudo_cl_results.json`.
  - **Verification**: For a synthetic full-sky map containing a known dipole, the recovered amplitude deviates by < 1 × 10⁻³ mag.

---

## Phase 2 – Complete the study and validate its evidence

- [ ] **T006** Generate isotropic mock catalogs via mask-aware random rotations
  - Create random 3-D rotation matrices with `scipy.spatial.transform.Rotation.random` (fixed seed 42), using the shared rotation utilities in `code/rotations.py` (also exercised by the T014 pilot study).
  - For each iteration: rotate all supernova RA/Dec, keep redshift and uncertainties unchanged, re-project onto the HEALPix grid (reuse code from **T003**), and compute dipole/quadrupole amplitudes using the official **T005** estimator, cross-checked against **T004**.
  - Stream results to `data/processed/simulation_results.csv` with columns `run_id`, `dipole_amp`, `quadrupole_amp` (conforming to `contracts/simulation_results.schema.yaml`).
  - After every 1 000 iterations compute the running mean of the dipole amplitude; stop when the change over the last 1 000 iterations is < 0.001 mag (SC-003).
  - Record the final number of simulations and the standard deviation of dipole amplitudes in `data/processed/null_distribution_stats.json`.
  - **Verification**: The CSV file contains at least the convergence-required number of rows, and the stats file reports a finite `dipole_std`.

- [ ] **T007** Significance assessment and final result artifacts
  - Load observed amplitudes from `data/processed/pseudo_cl_results.json` (the official FR-004 result; `primary_fit.json` from T004 is reported alongside as a cross-check).
  - Compute p-values as the fraction of simulated amplitudes ≥ the observed values.
  - Set `is_significant = (p_value_dipole < 0.05)`.
  - Interpret the outcome against the minimum detectable dipole amplitude from **T014**'s `power_analysis.json` (a null result is only claimed as informative if the observed amplitude is below the detectable threshold); record this comparison in `analysis_result.json` and the final report.
  - Write `data/processed/analysis_result.json` matching `contracts/analysis_result.schema.yaml` (including runtime, number of simulations, number of supernovae used, cosmological parameters, observed amplitudes, p-values, and significance flag).
  - Write a human-readable summary `data/reports/final_report.txt` that conforms to `contracts/final_report.schema.yaml`.
  - **Verification**: `analysis_result.json` validates against its schema; `runtime_seconds` < 21600 (6 h); `is_significant` follows the 0.05 threshold rule.

- [ ] **T008** Generate publication-ready figures
  - `figures/sky_map.png`: Mollweide plot of the mean residuals from the HEALPix map.
  - `figures/dipole_vector.png`: Same sky map with the dipole direction vector overlaid.
  - `figures/null_distributions.png`: Histograms of dipole and quadrupole amplitudes from the null distribution, with observed values marked.
  - All PNGs saved at 300 dpi.
  - **Verification**: Each PNG file exists, size > 0 bytes, and can be opened without error (checked by `tests/unit/test_visualize.py`).

- [ ] **T009** Sensitivity and systematic robustness checks
  - Variant A: Exclude low-z supernovae (`z < 0.02`).
  - Variant B: Apply a stricter mask (`count ≥ 2` per pixel).
  - For each variant re-run the official estimator (**T005**) and record dipole/quadrupole amplitudes.
  - Store results in `data/processed/sensitivity_checks.json` with keys `baseline`, `no_low_z`, `strict_mask`.
  - Compute absolute differences relative to the baseline; ensure each difference ≤ 0.02 mag.
  - **Verification**: The JSON file contains the required keys and all differences satisfy the tolerance check.

- [ ] **T010** Reproducibility audit
  - Starting from a clean checkout (only `requirements.txt` and the raw Pantheon+ file), run the full pipeline via `python -m code.main --seed 42`.
  - Compute SHA-256 hashes of every output artifact (`*.csv`, `*.fits`, `*.json`, `*.txt`, `*.png`) and record them in `state/projects/PROJ-753-testing-the-isotropy-cosmic-expansion.yaml` under `artifact_hashes`.
  - **Verification**: A verification script (`scripts/verify_hashes.py`) exits with status 0 only if all recorded hashes match the freshly generated ones.

---

## Phase 3 – Reproducible results and handoff

- [ ] **T011** Update documentation and quick-start guide
  - Revise `docs/quickstart.md` and `README.md` to include:
    ```bash
    pip install -r requirements.txt
    python -m code.main --seed 42
    ```
    - Explanation of directory layout.
    - How to adjust the number of simulations (`MAX_SIMULATIONS` in `code/simulations.py`).
    - Interpretation of the JSON results and the significance flag.
    - Note on systematic corrections applied (extinction, peculiar-velocity, calibration drift).
  - Ensure all internal links resolve.
  - **Verification**: Rendering the markdown locally succeeds without broken links.

- [ ] **T012** Bundle artifacts for downstream hand-off
  - Create `artifacts/artifact_bundle.zip` containing:
    `data/processed/`, `figures/`, `data/reports/final_report.txt`, `data/processed/analysis_result.json`, and `requirements.txt`.
  - Compute the bundle's SHA-256 hash and store it in the same state file used by **T010** (`bundle_hash`).
  - **Verification**: The zip file exists, size > 0, and the stored hash matches a freshly computed hash.

- [ ] **T013** Verify Pantheon+ citation (Constitution Principle II)
  - Run the Reference-Validator Agent on the Pantheon+ citation URL used in the spec.
  - If the citation is unverified, replace it with an alternative verified source (e.g., a DOI link to the official data release).
  - Record the validation outcome in `data/raw/metadata.json` (`citation_verified: true/false`).
  - **Verification**: Agent output reports the citation as verified; task fails otherwise.

---

*All tasks are unchecked; the runtime will mark them complete once their implementation, tests, and verification steps succeed.*