# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Inputs**: `specs/001-testing-the-isotropy-cosmic-expansion/spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`

The tasks below implement the full end‑to‑end analysis required by the specification, respect all constitutional and scientific requirements, and address the reviewer‑identified gaps (download‑URL verification, systematic‑error handling, power‑analysis ordering, and citation validation). Tasks are ordered to respect data flow; each task lists its verification steps.

---

## Phase 1 – Data acquisition & preprocessing

- [ ] T002 **[FR‑001] [P] Download Pantheon+ dataset & record provenance**   <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 -->
  *Creates*: `data/raw/pantheon_plus.fits`, `data/raw/metadata.json`, and updates `state/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml` with the SHA‑256 checksum.  
  - Fetch the official Pantheon+ release from the verified Zenodo DOI `[UNRESOLVED-CLAIM: https://doi.org/10.5281/zenodo.7968445` — HTTP 404] (the DOI resolves to a tarball containing `Pantheon+_Data.fits`).  
  - Store the FITS file at `data/raw/pantheon_plus.fits`.  
  - Compute its SHA‑256 checksum, write `metadata.json` with fields `dataset_version`, `source_url`, `sha256`, and `"citation_verified": false`.  
  - **State update**: add the checksum entry to the project's `artifact_hashes` map in the state YAML.  
  **Verification**:  
  1. HTTP 200 on the DOI URL; file exists at the expected path.  
  2. Checksum in `metadata.json` matches the computed hash and is recorded in the state YAML.  
  3. Header of the FITS file contains the required columns (`ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`).  

- [ ] T003 **[FR‑001][FR‑002] Ingest data, apply systematics, and compute residuals**  
  *Creates*: `data/processed/residuals.csv` (schema `contracts/residuals.schema.yaml`).  
  - Load `data/raw/pantheon_plus.fits`.  
  - Keep columns `ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`.  
  - Filter rows with missing or non‑finite values; log the number of excluded supernovae to `data/processed/ingestion_log.json`.  
  - Extract cosmological parameters (`H0`, `Omega_m`, `Omega_lambda`) from the FITS header; if absent, fall back to Planck 2018 values (`H0=67.4`, `Omega_m=0.315`, `Omega_lambda=0.685`).  
  - Apply Milky Way extinction correction using the Schlegel 1998 dust map (`astropy`).  
  - Apply 2M++ peculiar‑velocity correction to the redshifts.  
  - Compute theoretical distance modulus μ_th via numerical integration of \(d_L(z) = (1+z)\frac{c}{H_0}\int_0^z \frac{dz'}{E(z')}\) with `scipy.integrate.quad` (tolerance = 1e‑6).  
  - Compute residuals Δμ = μ_obs − μ_th and set `valid=True`.  
  - Write the table to `data/processed/residuals.csv`.  
  **Verification**:  
  1. Row count equals the official “full” sample size minus the excluded rows.  
  2. For the 10‑supernova subset listed in the spec, residuals match published values within their uncertainties.  

---

## Phase 2 – HEALPix projection

- [ ] T004 **[FR‑003] Project residuals onto HEALPix grid (Nside = 32)**  
  *Creates*: `data/processed/healpix_map.fits` (schema `contracts/healpix_map.schema.yaml`) and `data/processed/mapping_metrics.json`.  
  - Load `data/processed/residuals.csv`.  
  - Convert each (RA, Dec) to a HEALPix pixel index using `healpy.ang2pix` (Nside = 32).  
  - For each pixel, compute the inverse‑variance‑weighted mean residual and the number of contributing supernovae.  
  - Build a mask: `mask_value = 1` if pixel has ≥ 1 supernova, else 0.  
  - Write the map to a FITS binary table at `data/processed/healpix_map.fits`.  
  - Record the fraction of valid supernovae successfully mapped in `mapping_metrics.json` (`mapped_fraction`).  
  **Verification**:  
  1. FITS file validates against its schema.  
  2. `mapped_fraction` ≥ 0.95.  

---

## Phase 3 – Anisotropy estimators

- [ ] T005 **[FR‑004] Primary estimator – mask‑aware weighted least‑squares dipole/quadrupole fit**  
  *Creates*: `data/processed/primary_fit.json`.  
  - **Depends on** the HEALPix mask produced by T004.  
  - Build a design matrix **X** that maps each supernova to the three dipole basis vectors and the five quadrupole basis vectors on the sphere.  
  - Assemble the full covariance matrix \(C = \mathrm{diag}(\sigma_i^2) + \sigma_{\text{sys}}^2 \mathbf{1}\mathbf{1}^\top\) with systematic floor σ_sys = 0.02 mag.  
  - Apply the HEALPix mask (pixels with `mask_value = 0` receive zero weight).  
  - Solve \((X^\top C^{-1} M X)\beta = X^\top C^{-1} M y\) for the coefficient vector β.  
  - Convert β to scalar dipole amplitude \(A_1\) and quadrupole amplitude \(A_2\) (units mag) and store them in `primary_fit.json`.  
  **Verification**:  
  1. On a synthetic dataset with an injected dipole of 0.04 mag, the recovered dipole amplitude differs by < 1 × 10⁻³ mag.  

- [ ] T006 **[FR‑004] Secondary estimator – pseudo‑\(C_\ell\) analysis with MASTER correction**  
  *Creates*: `data/processed/pseudo_cl_results.json`.  
  - Use `healpy.anafast` on `data/processed/healpix_map.fits` to compute pseudo‑\(C_\ell\) up to ℓ = 3.  
  - Derive the mode‑coupling (MASTER) matrix from the mask and de‑bias the coefficients.  
  - Convert the corrected \(C_\ell\) to scalar amplitudes \(A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_m |a_{\ell m}|^2}\).  
  - Write the dipole (`A_1`) and quadrupole (`A_2`) amplitudes to `pseudo_cl_results.json`.  
  **Verification**:  
  1. On a synthetic full‑sky map with a known dipole of 0.05 mag, the recovered amplitude deviates by < 1 × 10⁻³ mag.  

---

## Phase 4 – Null‑distribution simulations

- [ ] T007 **[FR‑005] Generate isotropic mock catalogs via mask‑aware random rotations**  
  *Creates*: `data/processed/simulation_results.csv` (schema `contracts/simulation_results.schema.yaml`) and `data/processed/null_distribution_stats.json`.  
  - Create random 3‑D rotation matrices with `scipy.spatial.transform.Rotation.random` (fixed seed = 42).  
  - For each iteration: rotate all supernova RA/Dec, keep redshift and uncertainties unchanged, re‑project onto the HEALPix grid (reuse code from T004), and compute dipole/quadrupole amplitudes using the secondary estimator (T006).  
  - Stream each result (`run_id`, `dipole_amp`, `quadrupole_amp`) to `simulation_results.csv`.  
  - **Convergence criteria**:  
    1. Minimum 5 000 simulations.  
    2. After every 1 000 runs, compute the running mean of the dipole amplitude; stop when the change over the last 1 000 runs is < 0.001 mag **and** the 95 % binomial confidence interval on the p‑value has width ≤ 0.01, up to a hard cap of 20 000 runs.  
  - Record the final number of simulations, dipole standard deviation, and a `"converged": true` flag in `null_distribution_stats.json`.  
  **Verification**:  
  1. CSV contains at least the required number of rows and validates against its schema.  
  2. `null_distribution_stats.json` reports finite `dipole_std` and `"converged": true`.  

---

## Phase 5 – Significance assessment & final reporting

- [ ] T008 **[FR‑006] Significance assessment & creation of final result artifacts**  
  *Creates*: `data/processed/analysis_result.json` (schema `contracts/analysis_result.schema.yaml`) and `data/reports/final_report.txt` (schema `contracts/final_report.schema.yaml`).  
  - Load observed amplitudes from `pseudo_cl_results.json`.  
  - Compute p‑values as the fraction of simulated amplitudes ≥ the observed values (both dipole and quadrupole).  
  - Set `is_significant = (p_value_dipole < 0.05)`.  
  - Compare the observed dipole amplitude to the detectable threshold from T001; if below, add a note “informative null” in the report.  
  - Populate `analysis_result.json` with all required fields (dataset version, cosmological parameters, observed amplitudes, p‑values, significance flag, number of simulations, number of supernovae used, total runtime).  
  - Write a human‑readable summary `final_report.txt` containing the observed amplitudes, p‑values, significance flag, dataset metadata, and a brief interpretation.  
  **Verification**:  
  1. Both JSON and TXT files validate against their respective schemas.  
  2. `runtime_seconds` < 21600 s.  
  3. `is_significant` follows the 0.05 rule.  

---

## Phase 6 – Power‑analysis feasibility (executed after full analysis)

- [ ] T001 **[P] Compute analytic detection limit & pilot Monte‑Carlo**  
  *Creates*: `data/processed/power_analysis_results.csv` (schema `contracts/power_analysis_results.schema.yaml`).  
  - **Depends on** `data/processed/residuals.csv` and `data/processed/primary_fit.json`.  
  - Analytic component: using per‑SN uncertainties from `residuals.csv` and a systematic floor σ_sys = 0.02 mag, evaluate the minimum dipole amplitude detectable at p < 0.05 with ≥ 80 % power (non‑central χ² formula).  
  - Pilot Monte‑Carlo: generate **1 000** isotropic mock catalogs (same rotation routine as T007) **injecting** a dipole at the analytic threshold, run the primary estimator (T005) on each, and record the detection rate.  
  - Write two rows to `power_analysis_results.csv`: one with `scenario=analytic`, the other with `scenario=pilot_mc`.  
  **Verification**:  
  1. CSV contains exactly the two required rows and validates against its schema.  
  2. Detection power from the pilot MC lies within 0.70–0.90 (i.e., within 0.10 of the target 0.80).  

- [ ] T014 **[P] Revise and test `code/power_analysis.py`**  
  *Creates*: `code/power_analysis.py` (executable script) and `tests/unit/test_power_analysis.py`.  
  - Refactor the script to (a) load `data/processed/residuals.csv` safely, (b) compute the analytic detection limit using the same formulas as T001, (c) run the pilot Monte‑Carlo with **1 000** isotropic mocks (re‑using the rotation routine from T007), (d) write `power_analysis_results.csv` exactly as required, and (e) exit with status 0 on success.  
  - Add a unit test `tests/unit/test_power_analysis.py` that checks: the script returns exit 0, the output CSV exists, contains the two rows, and the detection power lies within the 0.70–0.90 window.  
  **Verification**:  
  1. `python code/power_analysis.py` completes with exit code 0.  
  2. `data/processed/power_analysis_results.csv` passes schema validation and the power‑range check.  

---

## Phase 7 – Systematics robustness checks (sensitivity analysis)

- [ ] T009 **[FR‑004] Systematics robustness checks**  
  *Creates*: `data/processed/sensitivity_checks.json`.  
  - Variant A: Exclude low‑z supernovae (`z < 0.02`).  
  - Variant B: Apply a stricter mask (`count ≥ 2` supernovae per HEALPix pixel).  
  - Variant C: Use the Cardelli 1989 extinction law (R_V = 3.1) instead of Schlegel 1998.  
  - For each variant, re‑run the secondary estimator (T006) and record dipole/quadrupole amplitudes.  
  - Store results under keys `baseline`, `no_low_z`, `strict_mask`, `alt_extinction`.  
  - Compute absolute differences relative to the baseline; each must be ≤ 0.02 mag.  
  **Verification**:  
  1. JSON contains all four keys and conforms to a simple schema (validated by unit tests).  
  2. All differences satisfy the ≤ 0.02 mag tolerance.  

---

## Phase 8 – Publication‑ready figures

- [ ] T010 **[FR‑004] Generate figures**  
  *Creates*: `figures/sky_map.png`, `figures/dipole_vector.png`, `figures/null_distributions.png`.  
  - `sky_map.png`: Mollweide projection of the inverse‑variance‑weighted mean residuals from `healpix_map.fits`.  
  - `dipole_vector.png`: Same sky map with the best‑fit dipole direction vector overlaid (arrow length proportional to amplitude).  
  - `null_distributions.png`: Overlaid histograms of dipole and quadrupole amplitudes from `simulation_results.csv` with vertical lines marking the observed values.  
  - All PNGs saved at 300 dpi, using a colour‑blind‑friendly palette.  
  **Verification**:  
  1. Each PNG exists, file size > 0 bytes, and can be opened without error (checked by `tests/unit/test_visualize.py`).  

---

## Phase 9 – Reproducibility audit

- [ ] T011 **Reproducibility audit**  
  *Creates*: `data/reports/reproducibility_audit.json` and script `scripts/verify_hashes.py`.  
  - Starting from a clean checkout (only `requirements.txt` and the raw Pantheon+ file), run the full pipeline via `python -m code.main --seed 42`.  
  - After completion, compute SHA‑256 hashes of every output artifact (`*.csv`, `*.fits`, `*.json`, `*.txt`, `*.png`) and record them together with the total wall‑clock time in `reproducibility_audit.json`.  
  - Provide `scripts/verify_hashes.py` that recomputes the hashes and exits with status 0 only if all match.  
  **Verification**:  
  1. Running `scripts/verify_hashes.py` returns exit code 0.  
  2. `reproducibility_audit.json` includes a `runtime_seconds` field matching the value in `analysis_result.json`.  

---

## Phase 10 – Documentation & quick‑start guide

- [ ] T012 **Update documentation & quick‑start guide**  
  *Modifies*: `docs/quickstart.md`, `README.md`.  
  - Add the exact number of supernovae used (`n_supernovae_used` from `analysis_result.json`).  
  - State the redshift range covered (derived from `residuals.csv`).  
  - Document the photometric system and light‑curve fitter employed by the Pantheon+ release (SALT2).  
  - Explain systematic‑error handling (Milky Way extinction, 2M++ peculiar‑velocity correction, σ_sys = 0.02 mag).  
  - Provide the reproducible command line: `pip install -r requirements.txt && python -m code.main --seed 42`.  
  - Describe how to adjust the simulation budget via the `MAX_SIMULATIONS` constant in `code/simulations.py`.  
  - Summarise interpretation of `analysis_result.json` (dipole amplitude, p‑value, significance flag).  
  **Verification**:  
  1. `markdownlint` run on the docs yields no errors.  
  2. The quick‑start command reproduces the full analysis on a fresh environment (checked by CI).  

---

## Phase 11 – Citation verification

- [ ] T013 **Verify Pantheon+ citation and record in metadata**  
  *Modifies*: `data/raw/metadata.json`.  
  - Run the Reference‑Validator Agent on the DOI `10.5281/zenodo.7968445`.  
  - If the citation is verified, set `"citation_verified": true` in `metadata.json`; otherwise replace the URL with a verified alternative (e.g., the arXiv paper describing the release).  
  **Verification**:  
  1. Agent output reports the citation as verified.  
  2. `metadata.json` contains `"citation_verified": true`.  

---

*All tasks are initially unchecked; the runtime will mark them complete once their implementation, tests, and verification steps succeed.*  