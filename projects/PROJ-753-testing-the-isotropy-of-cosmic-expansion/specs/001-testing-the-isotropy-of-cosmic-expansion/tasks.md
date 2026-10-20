# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data  

**Inputs**: `specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`  

The tasks below implement the complete end‑to‑end analysis required by the specification, repair the missing or malformed artifacts identified by the verifier, and respect all constitutional and scientific requirements.

---

## Phase 1 – Project scaffolding, data acquisition, and first end‑to‑end run  

- [X] T001 [P] Create the required project directory tree  
  - `data/raw/` – will hold the Pantheon+ release file (read‑only)  
  - `data/processed/` – filtered residuals, HEALPix map, simulation results  
  - `code/` – source modules (`ingest.py`, `utils.py`, `spherical_harmonics.py`, `simulations.py`, `analysis.py`, `visualize.py`, `models.py`)  
  - `tests/unit/`, `tests/integration/`, `tests/contract/` – pytest test suites  
  - `docs/` – quick‑start and methodological notes  
  - `reports/` – final analysis report and supporting markdown  
  - `figures/` – generated plots  
  - `scripts/` – helper scripts (linting, verification)  
  - **Verification**: Run `tree -L 2 .` and confirm all listed directories exist.

- [X] T002 [P] Initialise a Python 3.11 project with a fully‑pinned `requirements.txt`  
  - Run `pip‑compile` (or manually pin) to produce exact versions, e.g.:  
    ```text
    astropy>=6.0,<7.0
    healpy>=1.16.0,<2.0
    numpy>=1.26.0,<2.0
    scipy>=1.11.0,<2.0
    pandas>=2.1.0,<3.0
    matplotlib>=3.8.0,<4.0
    pytest>=7.4.0,<8.0
    ```  
  - Commit the file at `requirements.txt`.  
  - **Verification**: `pip install -r requirements.txt` succeeds without version conflicts.

- [ ] T003 [P] Configure code quality tools (Ruff + Black)
  - Add `pyproject.toml` with sections `[tool.black]` (line‑length = 88) and `[tool.ruff]` (select = ["E", "F", "W", "C90"]).  
  - Add a CI helper script `scripts/lint.sh` that runs `black --check . && ruff .`.  
  - **Verification**: `bash scripts/lint.sh` exits with status 0 on the current code base.

- [ ] T004 [US1] Download the Pantheon+ “full” sample, verify checksum, and record provenance   <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_pantheon.py exit=1 -->
  - URL: `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PantheonPlusDataRelease/PantheonPlusDataRelease/main/data/Pantheon%2B_SH0ES.dat` — HTTP 404] (the canonical release).  
  - Save to `data/raw/pantheon_plus_SH0ES.dat`.  
  - Compute SHA‑256, write `data/metadata.json` with fields `dataset_version`, `source_url`, `sha256`.  
  - **Verification**: The file exists, checksum matches the value published on the Pantheon+ release page, and `metadata.json` contains the same hash.

- [ ] T006 [US2] Provide a fully‑featured utility module (`code/utils.py`)  
  - Functions: `luminosity_distance(z, H0, Omega_m, Omega_lambda)`, `theoretical_mu(z, ...)`, `read_csv(path)`, `write_csv(df, path)`, `read_fits(path)`, `write_fits(data, header, path)`.  
  - Include proper docstrings, type hints, and raise explicit errors on I/O failure (no synthetic fallback).  
  - **Verification**: `tests/unit/test_utils.py` imports each function and runs a sanity check (e.g., `luminosity_distance(0.5,…)` returns a positive float).

- [ ] T005 [US1] Implement ingestion and residual calculation (`code/ingest.py`)  
  - Parse the raw file, keep columns `ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`.  
  - Filter out rows with missing or non‑finite values; log the number excluded.  
  - Extract cosmological parameters `H0`, `Omega_m`, `Omega_lambda` from the file header; if absent, fall back to the values stated in the Pantheon+ paper (H0 = 73.04 km s⁻¹ Mpc⁻¹, Ωₘ = 0.298, Ω_Λ = 0.702).  
  - Compute the theoretical distance modulus via numerical integration of  
    \[
    d_L(z)=\frac{c(1+z)}{H_0}\int_0^{z}\frac{dz'}{E(z')},\qquad
    E(z)=\sqrt{\Omega_m(1+z)^3+\Omega_\Lambda}
    \]  
    using `scipy.integrate.quad` with `rtol=1e-8`.  
  - Residual = `MU_obs – MU_th`.  
  - Write `data/processed/residuals.csv` conforming to `contracts/residuals.schema.yaml`.  
  - **Verification**: Unit test `tests/unit/test_ingest.py` checks (i) row count equals the official full‑sample size minus excluded rows, (ii) residuals for a hand‑picked set of 10 SNe match published values within their uncertainties.

- [ ] T007 [US2] Define data models (`code/models.py`) using `@dataclass`  
  - `SupernovaRecord` (fields matching `contracts/residuals.schema.yaml`).  
  - `HealpixPixel` (fields matching `contracts/healpix_map.schema.yaml`).  
  - New `HarmonicCoefficient` with fields `ell: int`, `m: int`, `real: float`, `imag: float`, `amplitude: float`.  
  - Export `__all__` for clean imports.  
  - **Verification**: `tests/unit/test_models.py` creates an instance of each class and asserts attribute types.

- [ ] T008 [US2] Implement HEALPix projection and pseudo‑Cℓ analysis (`code/spherical_harmonics.py`)  
  - Load `data/processed/residuals.csv`.  
  - Use `healpy.ang2pix` with `nside=32` to assign each SN to a pixel; compute per‑pixel mean residual and count.  
  - Build a mask where `count>0`. Save the map as `data/processed/healpix_map.fits` complying with `contracts/healpix_map.schema.yaml`.  
  - Compute pseudo‑Cℓ coefficients up to ℓ = 3 with the MASTER correction (use `healpy.anafast` on the masked map and apply the mode‑coupling matrix).  
  - Extract dipole (ℓ = 1) and quadrupole (ℓ = 2) amplitudes and write them to `data/processed/pseudo_cl_results.json`. Also record the fraction of SNe successfully mapped (SC‑001).  
  - **Verification**: `tests/integration/test_spherical_harmonics.py` injects a synthetic dipole into a mock residual map and asserts that the recovered dipole amplitude deviates by < 1 × 10⁻³ mag (SC‑002).

- [ ] T009 [US3] Perform significance assessment and produce final result artifacts (`code/analysis.py` & `code/main.py`)  
  - Load observed amplitudes from `pseudo_cl_results.json`.  
  - Load the null distribution from `null_distribution.csv`.  
  - Compute p‑values as the fraction of simulated amplitudes ≥ observed values, report to three decimal places.  
  - Set `is_significant = (p_value_dipole < 0.05)`.  
  - Write `data/results/analysis_result.json` matching `contracts/analysis_result.schema.yaml`.  
  - Write `data/results/final_report.json` matching `contracts/final_report.schema.yaml`.  
  - Record total wall‑clock runtime (SC‑004) in the analysis JSON.  
  - **Verification**: `tests/integration/test_analysis.py` runs the full pipeline on a small synthetic dataset (10 SNe) and checks that the JSON schema is satisfied and that p‑values are computed correctly.

- [ ] T019 [US2] Compute a quantitative reproducibility metric (SC‑002)  
  - Run the canonical reference implementation (provided in `tests/fixtures/reference`) on the same residuals and capture its dipole amplitude.  
  - Compare our dipole amplitude to the reference value and compute the absolute difference as the reproducibility metric.  
  - Store the metric in `data/results/reproducibility_metric.json`.  
  - **Verification**: `scripts/verify_reproducibility.py` asserts that the metric is ≤ 0.005 mag; exits with status 0 if satisfied.

- [ ] T010 [US3] Implement rotation‑based null‑distribution simulation (`code/simulations.py`)  
  - Generate 10 000 random rotation matrices using `scipy.spatial.transform.Rotation.random` with a master seed `42`.  
  - For each iteration: rotate the RA/Dec of all SNe, keep redshift and uncertainties unchanged, re‑project onto the HEALPix grid (reuse functions from T008), recompute dipole and quadrupole amplitudes, and stream the results as CSV rows `run_id,dipole_amp,quadrupole_amp` into `data/processed/null_distribution.csv` (conforms to `contracts/simulation_results.schema.yaml`).  
  - After each 1 000 iterations compute the running mean of the dipole amplitude; when the change over the last 1 000 runs falls below 0.001 mag, record convergence in `data/processed/convergence.json` (SC‑003).  
  - **Additional SC‑003 requirement**: compute the standard deviation of all simulated dipole amplitudes and write it to `data/processed/null_distribution_stats.json` under the key `dipole_std`.  
  - **Verification**: `tests/unit/test_simulations.py` runs the simulation with `N=100` (fast mode) on an isotropic input and asserts the resulting p‑value > 0.05 and that `null_distribution_stats.json` contains a `dipole_std` field.

- [ ] T011 [US3] Execute the complete end‑to‑end workflow on the real Pantheon+ data (`code/main.py`)  
  - Command: `python -m code.main --seed 42`.  
  - Pipeline: ingestion → residuals → HEALPix → pseudo‑Cℓ → simulations → significance → result JSONs.  
  - If the full 10 000 simulations exceed the 6‑hour CPU budget, automatically reduce to `N=5000` and add a field `note` in `analysis_result.json` describing the reduced statistical power.  
  - **Verification**: After the run, confirm existence of all expected output files and that `analysis_result.json.runtime_seconds` ≤ 21600 s (6 h).  

- [ ] T012 [US2] Generate publication‑ready figures (`code/visualize.py`)  
  - `figures/sky_map.png` – Mollweide plot of mean residuals (Nside = 32, down‑sampled for display).  
  - `figures/dipole_direction.png` – Vector overlay showing dipole orientation on the sky map.  
  - `figures/null_distributions.png` – Histograms of dipole and quadrupole amplitudes from the null distribution with observed values marked.  
  - All figures must be saved at 300 dpi PNGs.  
  - **Verification**: `tests/unit/test_visualize.py` calls each plotting function and asserts that the output file exists and has non‑zero file size.

- [ ] T013 [US3] Conduct sensitivity analyses (systematic checks)  
  - (i) Re‑run the pipeline excluding low‑z SNe (`z < 0.02`).  
  - (ii) Re‑run with a stricter mask (pixels with `count ≥ 2`).  
  - Store each variant’s dipole/quadrupole amplitudes in `data/results/sensitivity_checks.json`.  
  - Compare the variants to the baseline; record the absolute differences.  
  - **Verification**: `tests/contract/test_sensitivity.yaml` (executed via a custom pytest plugin) validates that the JSON contains keys `baseline`, `no_low_z`, `strict_mask` and that all amplitude differences are ≤ 0.02 mag.

- [ ] T018 [US3] Verify null‑distribution statistics  
  - Load `data/processed/null_distribution_stats.json`.  
  - Assert the presence of the key `dipole_std` and that its value is a finite positive number.  
  - Optionally check that `dipole_std` is consistent with the empirical standard deviation computed directly from `null_distribution.csv`.  
  - **Verification**: `scripts/verify_null_stats.py` exits with status 0 if the checks pass; CI will fail otherwise.

## Phase 3 – Reproducibility, reporting, and hand‑off  

- [ ] T014 Write the final analysis report (`reports/analysis_report.md`)  
  - Include: dataset version, cosmological parameters, number of SNe used, HEALPix resolution, observed dipole & quadrupole amplitudes, p‑values, significance flag, convergence diagnostics, sensitivity‑check outcomes, runtime, and limitations.  
  - Every numeric statement must be linked to its source artifact (e.g., `[dipole amplitude](/data/results/analysis_result.json#observed_dipole_amplitude)`).  
  - **Verification**: Automated script `scripts/verify_report_links.py` parses the markdown, extracts all `(/data/**/*.json#*)` links, loads the referenced JSON files, and confirms the fields exist; exits with status 0 if all checks pass.

- [ ] T015 Perform a reproducibility audit  
  - Re‑run the entire workflow from a clean checkout using only `requirements.txt` and the raw data file.  
  - Verify that all output artifacts (`*.csv`, `*.fits`, `*.json`, `*.png`) are bit‑identical to the previously generated ones (use `sha256sum`).  
  - Record the hashes in `state/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml` under the key `artifact_hashes`.  
  - **Verification**: CI step runs `python -m code.main --seed 42` and then `scripts/verify_hashes.py` which exits with status 0 only if all hashes match.

- [ ] T016 Update documentation (`docs/quickstart.md` and `README.md`)  
  - Provide a concise command sequence:  
    ```bash
    pip install -r requirements.txt
    python -m code.main --seed 42
    ```  
  - Explain the directory layout, how to change the number of simulations, and how to interpret the JSON results.  
  - Mention the resolved conflicts (flat ΛCDM residuals, Nside = 32, MASTER correction).  
  - **Verification**: Build the docs locally (`mkdocs build` or simple markdown render) and confirm that the quick‑start section renders without broken links.

- [ ] T017 Archive the complete, validated artifact set for downstream paper‑stage hand‑off  
  - Create a zip archive `artifact_bundle.zip` containing `data/processed/`, `data/results/`, `figures/`, `reports/analysis_report.md`, and the `requirements.txt`.  
  - Place the zip in `artifacts/`.  
  - Record its SHA‑256 in `state/projects/...yaml` under `bundle_hash`.  
  - **Verification**: The zip exists, size > 0, and the recorded hash matches the computed hash.

---  

*All tasks above remain unchecked; the runtime will mark them complete only after the corresponding implementation, test, and verification steps succeed.*  