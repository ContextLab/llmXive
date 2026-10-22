# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Inputs**: `specs/001-testing-the-isotropy-cosmic-expansion/spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`

The tasks below implement the complete end‑to‑end analysis required by the specification, respect all constitutional and scientific requirements, and address the reviewer‑identified gaps (broken download URL, missing systematic‑error handling, and the failing power‑analysis task). Tasks are ordered to respect data flow; each task lists its verification steps.

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] **T001** [P] Download Pantheon+ dataset and verify provenance  
  - Fetch the official Pantheon+ release from the Zenodo DOI `https://doi.org/10.5281/zenodo.7968445` (raw file `Pantheon+_SH0ES.dat`).  
  - Store it as `data/raw/pantheon_plus.dat`.  
  - Compute its SHA‑256 checksum and write `data/raw/metadata.json` containing fields `dataset_version`, `source_url`, and `sha256`.  
  - **Verification**:  
    1. HTTP 200 for the URL; file exists at the path above.  
    2. Checksum in `metadata.json` matches the computed hash.  
    3. Header contains the required columns (`ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`).

- [ ] **T002** [P] Ingest data, apply systematics, and compute residuals  
  - Parse `data/raw/pantheon_plus.dat`, keep columns `ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`.  
  - Filter out rows with missing or non‑finite values; log the count of excluded supernovae.  
  - Extract cosmological parameters (`H0`, `Ω_m`, `Ω_Λ`) from the file header; if absent, fall back to Planck 2018 values (`H0=67.4`, `Ω_m=0.315`, `Ω_Λ=0.685`).  
  - Apply Milky Way extinction correction using the Schlegel 1998 dust map (via `astropy.coordinates`).  
  - Apply a 2M++ peculiar‑velocity correction to the redshifts.  
  - Compute the theoretical distance modulus by numerically integrating \(d_L(z) = (1+z) \frac{c}{H_0}\int_0^z \frac{dz'}{E(z')}\) with `scipy.integrate.quad` (tolerance = 1e‑6).  
  - Calculate residuals \(\Delta\mu = \mu_{\text{obs}} - \mu_{\text{th}}\).  
  - Write `data/processed/residuals.csv` conforming to `contracts/residuals.schema.yaml`.  
  - **Verification**:  
    1. Row count equals the official “full” sample size minus excluded rows.  
    2. For the 10‑supernova subset listed in the spec, residuals match published values within their reported uncertainties.

- [ ] **T003** [P] Project residuals onto a HEALPix grid (Nside = 32)  
  - Load `data/processed/residuals.csv`.  
  - Convert each (RA, Dec) to HEALPix pixel index using `healpy.ang2pix` (Nside = 32).  
  - Compute the inverse‑variance‑weighted mean residual and the number of contributors per pixel.  
  - Build a mask (`mask_value = 1` for pixels with ≥ 1 supernova, else 0).  
  - Write the map to `data/processed/healpix_map.fits` adhering to `contracts/healpix_map.schema.yaml`.  
  - Record the fraction of valid supernovae successfully mapped in `data/processed/mapping_metrics.json`.  
  - **Verification**: FITS file validates against its schema and `mapping_metrics.json` contains a `mapped_fraction` field ≥ 0.95.

- [ ] **T004** [P] Primary estimator – weighted least‑squares dipole/quadrupole fit (cross‑check)  
  - Construct a design matrix that maps each supernova to the three dipole basis vectors and the five quadrupole basis vectors on the sphere.  
  - Build the full covariance matrix \(C = \mathrm{diag}(\sigma_i^2) + \sigma_{\text{sys}}^2 \mathbf{1}\mathbf{1}^\top\) with systematic floor \(\sigma_{\text{sys}} = 0.02\) mag.  
  - Apply the HEALPix mask (pixels with `mask_value = 0` receive zero weight).  
  - Solve \((X^\top C^{-1} M X)\beta = X^\top C^{-1} M y\) for the coefficient vector \(\beta\).  
  - Extract scalar dipole and quadrupole amplitudes (units mag) and write them to `data/processed/primary_fit.json`.  
  - **Verification**: On a synthetic dataset with an injected dipole of 0.04 mag, the recovered dipole amplitude differs by < 1 × 10⁻³ mag.

- [ ] **T005** [P] Official estimator – pseudo‑\(C_\ell\) analysis with MASTER mask correction  
  - Using the HEALPix map from **T003**, compute pseudo‑\(C_\ell\) coefficients up to \(\ell = 3\) with `healpy.anafast`.  
  - Apply the MASTER mode‑coupling matrix derived from the mask to obtain unbiased \(C_\ell\).  
  - Convert the corrected \(C_\ell\) to scalar amplitudes \(A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_m |a_{\ell m}|^2}\).  
  - Write dipole and quadrupole amplitudes to `data/processed/pseudo_cl_results.json`.  
  - **Verification**: For a synthetic full‑sky map containing a known dipole of 0.05 mag, the recovered amplitude deviates by < 1 × 10⁻³ mag.

- [ ] **T006** [P] Power‑analysis (analytic estimate + pilot Monte‑Carlo)  
  - **Analytic component**: Using the heteroscedastic per‑SN uncertainties from `residuals.csv` and a systematic floor of 0.02 mag, compute the minimum dipole amplitude detectable at \(p < 0.05\) with ≥ 80 % power (formula based on non‑central chi‑square).  
  - **Pilot Monte‑Carlo**: Generate 1 000 isotropic mock catalogs (same procedure as **T007**, but only a small sample) and inject dipoles at the analytic threshold; compute detection rate.  
  - Write both analytic and empirical results to `data/processed/power_analysis_results.csv` conforming to `contracts/power_analysis_results.schema.yaml`.  
  - **Verification**:  
    1. CSV contains rows for `scenario = analytic` and `scenario = pilot_mc`.  
    2. Empirical detection power for the analytic threshold lies within 0.10 of the target 0.80 (i.e., 0.70 – 0.90).  

---

## Phase 2 – Null simulations, significance, and robustness

- [ ] **T007** [P] Generate isotropic mock catalogs via mask‑aware random rotations  
  - Create random 3‑D rotation matrices with `scipy.spatial.transform.Rotation.random` (fixed seed = 42).  
  - For each iteration: rotate all supernova RA/Dec, keep redshift and uncertainties unchanged, re‑project onto the HEALPix grid (reuse code from **T003**), and compute dipole/quadrupole amplitudes using the official estimator (**T005**).  
  - Stream results to `data/processed/simulation_results.csv` (columns `run_id`, `dipole_amp`, `quadrupole_amp`) conforming to `contracts/simulation_results.schema.yaml`.  
  - **Convergence criteria**:  
    1. Minimum of 5 000 simulations.  
    2. After every 1 000 runs, compute the running mean of the dipole amplitude; stop when the change over the last 1 000 runs is < 0.001 mag **and** the 95 % binomial confidence interval on the p‑value width ≤ 0.01, up to a hard cap of 20 000 runs.  
  - Record final number of simulations and dipole standard deviation in `data/processed/null_distribution_stats.json`.  
  - **Verification**: CSV contains at least the required number of rows, `null_distribution_stats.json` reports finite `dipole_std`, and the convergence flag `converged: true` is present.

- [ ] **T008** [P] Significance assessment and final result artifacts  
  - Load observed amplitudes from `data/processed/pseudo_cl_results.json`.  
  - Compute p‑values as the fraction of simulated amplitudes ≥ the observed values (both dipole and quadrupole).  
  - Set `is_significant = (p_value_dipole < 0.05)`.  
  - Compare the observed dipole amplitude to the detectable threshold from **T006**; if the observed amplitude is below that threshold, flag the result as “informative null”.  
  - Write `data/processed/analysis_result.json` matching `contracts/analysis_result.schema.yaml` (including runtime, `n_simulations`, `n_supernovae_used`, cosmological parameters, observed amplitudes, p‑values, and significance flag).  
  - Write a human‑readable summary `data/reports/final_report.txt` that conforms to `contracts/final_report.schema.yaml`.  
  - **Verification**: Both JSON and TXT files validate against their schemas; `runtime_seconds` < 21600 s; `is_significant` follows the 0.05 rule.

- [ ] **T009** [P] Systematics robustness checks (sensitivity analysis)  
  - **Variant A**: Exclude low‑z supernovae (`z < 0.02`).  
  - **Variant B**: Apply a stricter mask (`count ≥ 2` supernovae per HEALPix pixel).  
  - **Variant C**: Use an alternative extinction law (Cardelli 1989 with \(R_V = 3.1\)) instead of Schlegel 1998.  
  - For each variant, re‑run the official estimator (**T005**) and record dipole/quadrupole amplitudes.  
  - Store results in `data/processed/sensitivity_checks.json` with keys `baseline`, `no_low_z`, `strict_mask`, `alt_extinction`.  
  - Compute absolute differences relative to the baseline; each difference must be ≤ 0.02 mag.  
  - **Verification**: JSON contains all required keys and all differences satisfy the tolerance check.

- [ ] **T010** [P] Generate publication‑ready figures  
  - `figures/sky_map.png`: Mollweide projection of the inverse‑variance‑weighted mean residuals from the HEALPix map.  
  - `figures/dipole_vector.png`: Same sky map with the best‑fit dipole direction vector overlaid (arrow length proportional to amplitude).  
  - `figures/null_distributions.png`: Overlaid histograms of dipole and quadrupole amplitudes from `simulation_results.csv` with vertical lines marking the observed values.  
  - All PNGs saved at 300 dpi, colour‑blind‑friendly palette.  
  - **Verification**: Each PNG exists, file size > 0 bytes, and can be opened without error (checked by `tests/unit/test_visualize.py`).

---

## Phase 3 – Reproducibility, documentation, and hand‑off

- [ ] **T011** [P] Reproducibility audit  
  - Starting from a clean checkout (only `requirements.txt` and the raw Pantheon+ file), run the full pipeline via `python -m code.main --seed 42`.  
  - Compute SHA‑256 hashes of every output artifact (`*.csv`, `*.fits`, `*.json`, `*.txt`, `*.png`) and record them in `state/projects/PROJ-753-testing-the-isotropy-cosmic-expansion.yaml` under `artifact_hashes`.  
  - **Verification**: `scripts/verify_hashes.py` exits with status 0 only if all recorded hashes match freshly generated ones.

- [ ] **T012** [P] Update documentation and quick‑start guide with full measurement protocol  
  - Revise `docs/quickstart.md` and `README.md` to include:  
    1. Exact number of supernovae used after filtering (value taken from `analysis_result.json`).  
    2. Redshift range covered (e.g., 0.01 – 2.3).  
    3. Photometric system(s) and light‑curve fitter (SALT2) employed in the Pantheon+ release.  
    4. Description of systematic‑error handling (Milky Way extinction, 2M++ peculiar‑velocity correction, systematic floor).  
    5. Command to run the pipeline reproducibly (`pip install -r requirements.txt && python -m code.main --seed 42`).  
    6. How to adjust the number of simulations (`MAX_SIMULATIONS` in `code/simulations.py`).  
    7. Interpretation of the JSON results and the significance flag.  
  - Ensure all internal links resolve and the markdown renders without warnings.  
  - **Verification**: Running `markdownlint` on the docs yields no errors; the quick‑start command reproduces the full analysis on a fresh environment.

- [ ] **T013** [P] Verify Pantheon+ citation and record in metadata  
  - Run the Reference‑Validator Agent on the DOI `10.5281/zenodo.7968445`.  
  - If the citation is verified, set `citation_verified: true` in `data/raw/metadata.json`; otherwise replace the URL with a verified alternative (e.g., the arXiv paper describing the release).  
  - **Verification**: Agent output reports the citation as verified and the metadata field reflects the result.

---  

*All tasks are initially unchecked; the runtime will mark them complete once their implementation, tests, and verification steps succeed.*
