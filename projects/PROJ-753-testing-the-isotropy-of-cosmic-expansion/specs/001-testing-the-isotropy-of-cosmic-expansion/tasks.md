# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data  

**Inputs**: `specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`  

The tasks below implement the complete end‑to‑end analysis required by the specification, respect all constitutional and scientific requirements, and fix the previously‑failed items (lint configuration and dataset download).  

---  

## Phase 1 – Project scaffolding, data acquisition, and first end‑to‑end run  

- [ ] T001 **Create project directory tree** [FR-001]  
  - Create `data/raw/`, `data/processed/`, `data/reports/`, `figures/`, `code/`, `scripts/`, and `docs/`.  
  - **Verification**: After execution, each of the above directories exists on disk.

- [ ] T016 **Configure linting tools and fix lint errors** [FR-004]  
  - Add `pyproject.toml` with `[tool.black] line-length = 88` and `[tool.ruff] select = ["E","F","W","C90"]`.  
  - Create `scripts/lint.sh` that runs `black --check . && ruff .`.  
  - Run `black .` and `ruff . --fix` to auto‑format the codebase.  
  - **Verification**: `bash scripts/lint.sh` exits with status 0.

- [ ] T004 **Download Pantheon+ dataset and verify checksum** [FR-001]  
  - Implement `code/download_pantheon.py` that fetches `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/data/Pantheon%2B_SH0ES.dat` — HTTP 404].  
  - Compute SHA‑256, write `data/raw/pantheon_plus_SH0ES.dat` and a provenance file `data/raw/metadata.json` containing `dataset_version`, `source_url`, and `sha256`.  
  - **Verification**: File exists, checksum matches the published value, and `metadata.json` records the same hash.

- [ ] T006 **Utility module with core cosmology functions** [FR-004]  
  - Create `code/utils.py` providing `luminosity_distance(z, H0, Ω_m, Ω_Λ)`, `theoretical_mu(z, …)`, CSV/FITS I/O helpers, and robust error handling (no synthetic fall‑backs).  
  - **Verification**: `tests/unit/test_utils.py` imports each function and confirms correct basic behavior (e.g., positive return for `luminosity_distance(0.5,…)`).

- [ ] T005 **Ingest Pantheon+ data and compute residuals** [FR-002]  
  - Parse `data/raw/pantheon_plus_SH0ES.dat`, keep columns `ID`, `RA`, `DEC`, `ZHD`, `MU`, `MUERR`.  
  - Filter rows with missing or non‑finite values; log the number excluded.  
  - Extract cosmological parameters `H0`, `Ω_m`, `Ω_Λ` from the file header; if absent, fall back to Planck 2018 priors (`H0 = 67.4`, `Ω_m = 0.315`, `Ω_Λ = 0.685`).  
  - Compute theoretical distance modulus via numerical integration (SciPy `quad`, `rtol=1e-6`).  
  - Calculate residuals `Δμ = MU_obs − MU_th`.  
  - Write `data/processed/residuals.csv` conforming to `contracts/residuals.schema.yaml`.  
  - **Verification**: Unit test checks that the row count matches the official full‑sample size minus excluded rows and that residuals for a known subset of 10 SNe match published values within uncertainties.

- [ ] T007 **Define data‑model classes** [FR-004]  
  - Implement `code/models.py` with `@dataclass` definitions for `SupernovaRecord`, `HealpixPixel`, and `HarmonicCoefficient` matching the respective JSON/YAML schemas.  
  - Export `__all__` for clean imports.  
  - **Verification**: `tests/unit/test_models.py` instantiates each class and verifies attribute types.

- [ ] T008 **HEALPix projection and pseudo‑Cℓ analysis** [FR-003][SC-001]  
  - Load `data/processed/residuals.csv`.  
  - Use `healpy.ang2pix` (Nside = 32) to assign each SN to a pixel; compute per‑pixel inverse‑variance‑weighted mean residual and count.  
  - Build a mask (`mask_value = 1` for pixels with `count > 0`, else `0`).  
  - Save the map to `data/processed/healpix_map.fits` complying with `contracts/healpix_map.schema.yaml`.  
  - Compute pseudo‑Cℓ coefficients up to ℓ = 3 with MASTER mask correction (`healpy.anafast` + mode‑coupling matrix).  
  - Extract dipole (ℓ = 1) and quadrupole (ℓ = 2) amplitudes and write them to `data/processed/pseudo_cl_results.json`.  
  - Record the fraction of supernovae successfully mapped; store this metric in the report (fulfills SC‑001).  
  - **Verification**: `tests/integration/test_spherical_harmonics.py` injects a synthetic dipole into a mock residual map and asserts recovered dipole amplitude deviates by < 1 × 10⁻³ mag.

- [ ] T018 **Validate dipole reproducibility against canonical implementation** [SC-002]  
  - Run a reference implementation (e.g., using `healpy` directly on a small subset) and compare the dipole amplitude to that produced by Task T008.  
  - **Verification**: Difference ≤ 1 × 10⁻³ mag.

- [ ] T009 **Generate isotropic mock catalogs via mask‑aware random rotations** [FR-005]  
  - Implement `code/simulations.py` that creates random 3‑D rotation matrices using `scipy.spatial.transform.Rotation.random` with master seed 42.  
  - For each iteration: rotate all SN RA/Dec, keep redshift and uncertainties unchanged, re‑project onto the HEALPix grid (reuse functions from T008), recompute dipole and quadrupole amplitudes.  
  - Stream results to `data/processed/simulation_results.csv` with columns `run_id`, `dipole_amp`, `quadrupole_amp` (conforms to `contracts/simulation_results.schema.yaml`).  
  - After every 1 000 iterations compute the running mean of dipole amplitude; stop when the change over the last 1 000 runs is < 0.001 mag (SC‑003).  
  - Also compute and store the standard deviation of all simulated dipole amplitudes in `data/processed/null_distribution_stats.json` under key `dipole_std`.  
  - **Verification**: `tests/unit/test_simulations.py` runs a fast mode (`N=100`) on an isotropic input and checks that the resulting p‑value > 0.05 and that `null_distribution_stats.json` contains a finite `dipole_std`.

- [ ] T010 **Significance assessment and final result artifacts** [FR-006][SC-004]  
  - Implement `code/analysis.py` (called by `code/main.py`).  
  - Load observed dipole/quadrupole amplitudes from `data/processed/pseudo_cl_results.json` and the null distribution from `data/processed/simulation_results.csv`.  
  - Compute p‑values as the fraction of simulated amplitudes ≥ observed values; report to three decimal places.  
  - Set `is_significant = (p_value_dipole < 0.05)`.  
  - Write `data/processed/analysis_result.json` matching `contracts/analysis_result.schema.yaml` (including runtime, number of simulations, number of supernovae used, cosmological parameters, etc.).  
  - Write `data/processed/final_report.txt` matching `contracts/final_report.schema.yaml`.  
  - **Verification**: Ensure `analysis_result.json` contains `runtime_seconds < 21600` (6 h) and that `is_significant` follows the 0.05 threshold rule.

- [ ] T011 **Generate publication‑ready figures** [FR-004]  
  - Implement `code/visualize.py` to produce:  
    1. `figures/sky_map.png` – Mollweide plot of mean residuals (Nside = 32).  
    2. `figures/dipole_direction.png` – Vector overlay showing dipole orientation on the sky map.  
    3. `figures/null_distributions.png` – Histograms of dipole and quadrupole amplitudes from the null distribution with observed values marked.  
  - Save all PNGs at 300 dpi.  
  - **Verification**: `tests/unit/test_visualize.py` calls each plotting function and asserts that the output file exists and has non‑zero size.

- [ ] T012 **Sensitivity and systematic checks** [FR-004]  
  - Perform two variant runs:  
    1. Exclude low‑z supernovae (`z < 0.02`).  
    2. Apply a stricter mask (`count ≥ 2` per pixel).  
  - Store dipole/quadrupole amplitudes for each variant in `data/processed/sensitivity_checks.json`.  
  - Compute absolute differences relative to the baseline and record them.  
  - **Verification**: `tests/contract/test_sensitivity.yaml` validates that the JSON contains keys `baseline`, `no_low_z`, `strict_mask` and that all amplitude differences are ≤ 0.02 mag.

- [ ] T013 **Reproducibility audit** [FR-004]  
  - Re‑run the entire workflow from a clean checkout using only `requirements.txt` and the raw Pantheon+ file.  
  - Compute SHA‑256 hashes of all output artifacts (`*.csv`, `*.fits`, `*.json`, `*.txt`, `*.png`) and record them in `state/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml` under `artifact_hashes`.  
  - **Verification**: CI step runs `python -m code.main --seed 42` then `scripts/verify_hashes.py`; the script exits with status 0 only if all recorded hashes match the freshly generated ones.

- [ ] T014 **Documentation and quick‑start guide** [FR-004]  
  - Update `docs/quickstart.md` and `README.md` with a concise command sequence:  
    ```bash
    pip install -r requirements.txt
    python -m code.main --seed 42
    ```  
  - Explain directory layout, how to change the number of simulations, and how to interpret the JSON results.  
  - Mention resolved conflicts (flat ΛCDM residuals, Nside = 32, MASTER correction).  
  - **Verification**: Render the markdown locally (`markdown` or `mkdocs build`) and confirm that all internal links resolve.

- [ ] T015 **Artifact bundle for downstream hand‑off**  
  - Create `artifacts/artifact_bundle.zip` containing `data/processed/`, `figures/`, `data/processed/final_report.txt`, and `requirements.txt`.  
  - Compute its SHA‑256 and store the hash in `state/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml` under `bundle_hash`.  
  - **Verification**: Zip exists, size > 0, and recorded hash matches the computed hash.

- [ ] T017 **Verify Pantheon+ citation (Constitution Principle II)**  
  - Run the Reference‑Validator Agent on the Pantheon+ citation in the spec and ensure its status is “verified”.  
  - **Verification**: Agent output reports the citation as verified; task fails otherwise.

---  

### Phase 2 – Validation, reporting, and hand‑off (continued)

The tasks above already cover validation (unit, integration, contract checks), result generation, sensitivity analysis, reproducibility, documentation, and artifact bundling. No additional tasks are required beyond those listed.

---  

*All unchecked tasks will be marked complete by the runtime once their implementation, tests, and verification steps succeed.*  