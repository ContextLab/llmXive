# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Inputs**: `specs/001-testing-the-isotropy-cosmic-expansion/spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`

The tasks below implement the full end‑to‑end analysis required by the specification, respect all constitutional and scientific requirements, and address the reviewer‑identified gaps (download URL verification, systematic‑error handling, and a robust power‑analysis). Tasks are ordered to respect data flow; each task lists its verification steps.

---

## Phase 0 – Power‑analysis feasibility (pre‑study)

- [ ] T001 **Compute analytic detection limit & pilot Monte‑Carlo**  
  *Creates*: `data/processed/power_analysis_results.csv` (schema `contracts/power_analysis_results.schema.yaml`).  
  - Analytic component: using the per‑SN uncertainties from `data/processed/residuals.csv` and a systematic floor σ_sys = 0.02 mag, evaluate the minimum dipole amplitude detectable at p < 0.05 with ≥ 80 % power (non‑central χ² formula).  
  - Pilot Monte‑Carlo: generate **1 000** isotropic mock catalogs (same procedure as T007 but only 1 000 runs), inject a dipole at the analytic threshold, run the official estimator (T005), and record the detection rate.  
  - Write two rows to `power_analysis_results.csv`: one with `scenario=analytic`, the other with `scenario=pilot_mc`.  
  **Verification**:  
  1. CSV contains exactly the two required rows and conforms to the schema.  
  2. Detection power from the pilot MC lies within 0.70–0.90 (i.e., within 0.10 of the target 0.80).  

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T002 **[P] Download Pantheon+ dataset & record provenance**  
  *Creates*: `data/raw/pantheon_plus.dat`, `data/raw/metadata.json`.  
  - Fetch the official Pantheon+ release from the Zenodo DOI `[UNRESOLVED-CLAIM: https://doi.org/10.5281/zenodo.7968445` — HTTP 404].  
  - Store the file at `data/raw/pantheon_plus.dat`.  
  - Compute its SHA‑256 checksum and write `metadata.json` with fields `dataset_version`, `source_url`, `sha256`.  
  **Verification**:  
  1. HTTP 200 on the DOI URL; file exists at the expected path.  
  2. Checksum in `metadata.json` matches the computed hash.  
  3. Header contains the required columns (`ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`).  

- [ ] T003 **Ingest data, apply systematics, and compute residuals**  
  *Creates*: `data/processed/residuals.csv` (schema `contracts/residuals.schema.yaml`).  
  - Parse `data/raw/pantheon_plus.dat`, keep columns `ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`.  
  - Filter rows with missing or non‑finite values; log the number of excluded supernovae to `data/processed/ingestion_log.json`.  
  - Extract cosmological parameters (`H0`, `Ω_m`, `Ω_Λ`) from the file header; if absent, fall back to Planck 2018 (`H0=67.4`, `Ω_m=0.315`, `Ω_Λ=0.685`).  
  - Apply Milky Way extinction correction using the Schlegel 1998 dust map (`astropy`).  
  - Apply 2M++ peculiar‑velocity correction to the redshifts.  
  - Compute theoretical distance modulus μ_th via numerical integration of \(d_L(z) = (1+z)\frac{c}{H_0}\int_0^z \frac{dz'}{E(z')}\) with `scipy.integrate.quad` (tolerance = 1e‑6).  
  - Compute residuals Δμ = μ_obs − μ_th and set `valid=True`.  
  - Write the resulting table to `data/processed/residuals.csv`.  
  **Verification**:  
  1. Row count equals the official “full” sample size minus the excluded rows.  
  2. For the 10‑supernova subset listed in the spec, residuals match published values within their uncertainties.  

- [ ] T004 **Project residuals onto HEALPix grid (Nside = 32)**  
  *Creates*: `data/processed/healpix_map.fits` (schema `contracts/healpix_map.schema.yaml`), `data/processed/mapping_metrics.json`.  
  - Load `data/processed/residuals.csv`.  
  - Convert each (RA, Dec) to a HEALPix pixel index using `healpy.ang2pix` (Nside = 32).  
  - For each pixel, compute the inverse‑variance‑weighted mean residual and the number of contributing supernovae.  
  - Build a mask: `mask_value = 1` if pixel has ≥ 1 supernova, else 0.  
  - Write the map to a FITS binary table at `data/processed/healpix_map.fits`.  
  - Record the fraction of valid supernovae successfully mapped in `mapping_metrics.json` (`mapped_fraction`).  
  **Verification**:  
  1. FITS file validates against its schema.  
  2. `mapped_fraction` ≥ 0.95.  

- [ ] T005 **Primary estimator – mask‑aware weighted least‑squares dipole/quadrupole fit**  
  *Creates*: `data/processed/primary_fit.json`.  
  - Build a design matrix **X** that maps each supernova to the three dipole basis vectors and the five quadrupole basis vectors on the sphere.  
  - Assemble the full covariance matrix \(C = \mathrm{diag}(\sigma_i^2) + \sigma_{\text{sys}}^2 \mathbf{1}\mathbf{1}^\top\) with systematic floor σ_sys = 0.02 mag.  
  - Apply the HEALPix mask (pixels with `mask_value = 0` receive zero weight).  
  - Solve \((X^\top C^{-1} M X)\beta = X^\top C^{-1} M y\) for the coefficient vector β.  
  - Convert β to scalar dipole amplitude \(A_1\) and quadrupole amplitude \(A_2\) (units mag) and store them in `primary_fit.json`.  
  **Verification**:  
  1. On a synthetic dataset with an injected dipole of 0.04 mag, the recovered dipole amplitude differs by < 1 × 10⁻³ mag.  

- [ ] T006 **Official estimator – pseudo‑\(C_\ell\) analysis with MASTER correction**  
  *Creates*: `data/processed/pseudo_cl_results.json`.  
  - Use `healpy.anafast` on `data/processed/healpix_map.fits` to compute pseudo‑\(C_\ell\) up to ℓ = 3.  
  - Derive the mode‑coupling (MASTER) matrix from the mask and de‑bias the coefficients.  
  - Convert the corrected \(C_\ell\) to scalar amplitudes \(A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_m |a_{\ell m}|^2}\).  
  - Write the dipole (\(A_1\)) and quadrupole (\(A_2\)) amplitudes to `pseudo_cl_results.json`.  
  **Verification**:  
  1. On a synthetic full‑sky map with a known dipole of 0.05 mag, the recovered amplitude deviates by < 1 × 10⁻³ mag.  

---

## Phase 2 – Full null‑simulation study, significance, and robustness

- [ ] T007 **Generate isotropic mock catalogs via mask‑aware random rotations**  
  *Creates*: `data/processed/simulation_results.csv` (schema `contracts/simulation_results.schema.yaml`), `data/processed/null_distribution_stats.json`.  
  - Create random 3‑D rotation matrices with `scipy.spatial.transform.Rotation.random` (fixed seed = 42).  
  - For each iteration: rotate all supernova RA/Dec, keep redshift and uncertainties unchanged, re‑project onto the HEALPix grid (reuse code from T004), and compute dipole/quadrupole amplitudes using the official estimator (T006).  
  - Stream each result (`run_id`, `dipole_amp`, `quadrupole_amp`) to `simulation_results.csv`.  
  - **Convergence criteria**:  
    1. Minimum 5 000 simulations.  
    2. After every 1 000 runs, compute the running mean of the dipole amplitude; stop when the change over the last 1 000 runs is < 0.001 mag **and** the 95 % binomial confidence interval on the p‑value has width ≤ 0.01, up to a hard cap of 20 000 runs.  
  - Record the final number of simulations, dipole standard deviation, and a `converged` flag in `null_distribution_stats.json`.  
  **Verification**:  
  1. CSV contains at least the required number of rows and conforms to its schema.  
  2. `null_distribution_stats.json` reports finite `dipole_std` and `"converged": true`.  

- [ ] T008 **Significance assessment & final result artifacts**  
  *Creates*: `data/processed/analysis_result.json` (schema `contracts/analysis_result.schema.yaml`), `data/reports/final_report.txt` (schema `contracts/final_report.schema.yaml`).  
  - Load observed amplitudes from `pseudo_cl_results.json`.  
  - Compute p‑values as the fraction of simulated amplitudes ≥ the observed values (both dipole and quadrupole).  
  - Set `is_significant = (p_value_dipole < 0.05)`.  
  - Compare the observed dipole amplitude to the detectable threshold from T001; if below, add a note “informative null” in the report.  
  - Populate `analysis_result.json` with all required fields (dataset version, cosmological parameters, observed amplitudes, p‑values, significance flag, number of simulations, number of supernovae used, total runtime).  
  - Write a human‑readable summary `final_report.txt` containing the observed amplitudes, p‑values, significance flag, and dataset metadata.  
  **Verification**:  
  1. Both JSON and TXT files validate against their respective schemas.  
  2. `runtime_seconds` < 21600 s.  
  3. `is_significant` follows the 0.05 rule.  

- [ ] T009 **Systematics robustness checks (sensitivity analysis)**  
  *Creates*: `data/processed/sensitivity_checks.json`.  
  - Variant A: Exclude low‑z supernovae (`z < 0.02`).  
  - Variant B: Apply a stricter mask (`count ≥ 2` supernovae per HEALPix pixel).  
  - Variant C: Use the Cardelli 1989 extinction law (R_V = 3.1) instead of Schlegel 1998.  
  - For each variant, re‑run the official estimator (T006) and record dipole/quadrupole amplitudes.  
  - Store results under keys `baseline`, `no_low_z`, `strict_mask`, `alt_extinction`.  
  - Compute absolute differences relative to the baseline; each must be ≤ 0.02 mag.  
  **Verification**:  
  1. JSON contains all four keys and conforms to a simple schema (validated by a custom test).  
  2. All differences satisfy the ≤ 0.02 mag tolerance.  

- [ ] T010 **Generate publication‑ready figures**  
  *Creates*: `figures/sky_map.png`, `figures/dipole_vector.png`, `figures/null_distributions.png`.  
  - `sky_map.png`: Mollweide projection of the inverse‑variance‑weighted mean residuals from `healpix_map.fits`.  
  - `dipole_vector.png`: Same sky map with the best‑fit dipole direction vector overlaid (arrow length proportional to amplitude).  
  - `null_distributions.png`: Overlaid histograms of dipole and quadrupole amplitudes from `simulation_results.csv` with vertical lines marking the observed values.  
  - All PNGs saved at 300 dpi, using a colour‑blind‑friendly palette.  
  **Verification**:  
  1. Each PNG exists, file size > 0 bytes, and can be opened without error (checked by `tests/unit/test_visualize.py`).  

---

## Phase 3 – Reproducibility, documentation, and hand‑off

- [ ] T011 **Reproducibility audit**  
  *Creates*: `data/reports/reproducibility_audit.json`.  
  - Starting from a clean checkout (only `requirements.txt` and the raw Pantheon+ file), run the full pipeline via `python -m code.main --seed 42`.  
  - After completion, compute SHA‑256 hashes of every output artifact (`*.csv`, `*.fits`, `*.json`, `*.txt`, `*.png`) and record them in `reproducibility_audit.json` together with the total wall‑clock time.  
  - Provide a script `scripts/verify_hashes.py` that exits with status 0 only if all recorded hashes match freshly recomputed ones.  
  **Verification**:  
  1. Running `scripts/verify_hashes.py` returns exit code 0.  
  2. `reproducibility_audit.json` includes a `runtime_seconds` field matching the value in `analysis_result.json`.  

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

- [ ] T013 **Verify Pantheon+ citation and record in metadata**  
  *Modifies*: `data/raw/metadata.json`.  
  - Run the Reference‑Validator Agent on the DOI `10.5281/zenodo.7968445`.  
  - If the citation is verified, set `"citation_verified": true` in `metadata.json`; otherwise replace the URL with a verified alternative (e.g., the arXiv paper describing the release).  
  **Verification**:  
  1. Agent output reports the citation as verified.  
  2. `metadata.json` contains `"citation_verified": true`.  

---  

*All tasks are initially unchecked; the runtime will mark them complete once their implementation, tests, and verification steps succeed.*
