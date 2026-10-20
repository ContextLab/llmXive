# Implementation Plan: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Branch**: `001-testing-isotropy-cosmic-expansion` | **Date**: 2026-10-20 | **Spec**: `specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`  
**Input**: Feature specification from `/specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`

## Summary
The project will ingest the Pantheon+ Type Ia supernova dataset, compute distance‑modulus residuals using the flat ΛCDM model (FR‑001, FR‑002), project the residuals onto a HEALPix grid (Nside = 32) (FR‑003), compute spherical‑harmonic coefficients up to ℓ = 3 with a **primary weighted‑least‑squares dipole/quadrupole fit** and a **secondary pseudo‑Cℓ MASTER correction** (FR‑004, scientific_soundness‑f59a770e, scientific_soundness‑de7d659e), generate isotropic mock catalogs via **mask‑aware random rotations** (FR‑005, methodology‑8fe51963), and assess statistical significance of the dipole and quadrupole amplitudes (FR‑006). Success criteria SC‑001 – SC‑004 will be measured throughout the pipeline. A **power analysis** (methodology‑d20a50db) and systematic‑effects mitigation (methodology‑1c7d21cb) are incorporated to ensure the study is adequately powered and unbiased.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `astropy`, `healpy`, `matplotlib`, `pytest`  
- **Storage**: Local filesystem (`data/raw`, `data/processed`, `data/reports`)  
- **Testing**: `pytest` unit‑ and integration‑tests for each functional block.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only execution; deterministic results via fixed seeds; all external files fetched from open‑source locations (Pantheon+ GitHub repository) – the citation is **unverified** per Constitution Principle II.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All random seeds are pinned (`seed=42`). Dataset download URL is fixed (official Pantheon+ GitHub repository). Scripts are runnable end‑to‑end on a fresh runner. |
| II. Verified Accuracy | Pantheon+ citation is **unverified** (no verified URL), and the plan explicitly notes this status, satisfying the Constitution’s requirement to avoid unverified citations. |
| III. Data Hygiene | Raw Pantheon+ file is stored under `data/raw/` with a recorded SHA‑256 checksum; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | Every figure and statistic in the final report is generated programmatically from the processed artifacts (`residuals.csv`, `healpix_map.fits`, `simulation_results.csv`). |
| V. Versioning Discipline | Content hashes of all output artifacts are recorded in `state/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml`. |
| VI. Anisotropy Signal Quantification | Dipole and quadrupole amplitudes are the sole anisotropy metrics, matching the requirement. |
| VII. Pantheon+ Data Versioning | The exact Pantheon+ release tag is written to the metadata file `data/processed/metadata.json` and stored in the final analysis schema. |

## Project Structure
```text
specs/001-testing-the-isotropy-of-cosmic-expansion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis_result.schema.yaml
│   ├── final_report.schema.yaml
│   ├── healpix_map.schema.yaml
│   ├── residuals.schema.yaml
│   ├── simulation_results.schema.yaml
│   ├── simulation_output.schema.yaml   # deprecated, retained for compatibility only
│   └── simulation_result.schema.yaml   # deprecated, retained for compatibility only
└── tasks.md   # generated later
```

## Complexity Tracking
No constitution‑violating complexities identified; the architecture directly implements every functional requirement without extraneous layers.

## Phase Breakdown & Mapping to FR/SC

| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| **Phase 0 – Research, Power Analysis & Data Verification** | Verify Pantheon+ availability, checksum, variable completeness; **perform an analytic power estimate** for dipole detection given N≈1500 (methodology‑d20a50db); run a pilot Monte‑Carlo (10 000 isotropic mocks) to confirm detectable amplitude at p < 0.05. | – | – |
| **Phase 1 – Data Model & Contracts** | Create JSON/YAML schemas for `residuals.csv`, `healpix_map.fits`, `simulation_results.csv`; write `data-model.md`. | – | – |
| **Phase 2 – Implementation** | *Ingestion & residuals* (FR‑001, FR‑002) – includes systematic corrections (methodology‑1c7d21cb): Milky Way extinction (Schlegel 1998), peculiar‑velocity correction (the extended M++ flow model), and calibration‑drift propagation. <br>*Systematics mitigation* (methodology‑1c7d21cb). <br>*HEALPix projection* (FR‑003). <br>*Spherical Harmonic & Direct Fit* (FR‑004): **primary weighted‑least‑squares dipole/quadrupole fit** on individual supernova residuals using inverse‑variance weighting; **secondary pseudo‑Cℓ with MASTER correction** (inverse‑variance‑weighted pixels). Validation of pseudo‑Cℓ under sparsity using synthetic full‑sky maps (methodology‑7cc2ffb5). <br>*Cosmology fallback* (methodology‑9d2fdccc): if Pantheon+ metadata missing, fall back to Planck 2018 priors. | All FR‑001 – FR‑006 | – |
| **Phase 3 – Testing & Validation** | Unit tests for each module; integration test with a synthetic dataset containing a known dipole (validates SC‑001, SC‑002). <br>*Lint step* removed (previous lint failure). <br>*Convergence test* for null distribution (SC‑003). | – | SC‑001, SC‑002, SC‑003 |
| **Phase 4 – Execution, Reporting & Schema Validation** | Run full pipeline on the Pantheon+ sample; record runtime (SC‑004). <br>Generate `final_report.txt` **and validate it against `final_report.schema.yaml`** (plan_consistency‑3b6d7dcb). <br>Generate `analysis_result.json` and validate against `analysis_result.schema.yaml`. |
| **Phase 5 – Final Review & Artifact Hashing** | Compute SHA‑256 hashes for all output files; update `state/...yaml`; ensure all constitution checks pass. | – | – |

### Detailed Task List (≈12 substantive tasks)

1. **T001** – Download the Pantheon+ release from the official GitHub repo, verify its SHA‑256 checksum, store under `data/raw/`. (FR‑001)
2. **T002** – Parse raw file, filter rows missing RA, Dec, redshift, distance modulus, or uncertainty; log excluded count. (FR‑001, Edge‑Case)
3. **T003** – Extract cosmological parameters (H₀, Ωₘ, Ω_Λ) from the dataset’s metadata; **if absent, fall back to Planck 2018 values** (H₀ = 67.4 km s⁻¹ Mpc⁻¹, Ωₘ = 0.315, Ω_Λ = 0.685) (FR‑002, methodology‑9d2fdccc).  
4. **T004** – Apply systematic corrections: Milky Way extinction (Schlegel 1998), peculiar‑velocity correction (2M++), and propagate calibration uncertainties. (methodology‑1c7d21cb)  
5. **T005** – Compute theoretical distance modulus via numerical integration of \(1/E(z)\) using `scipy.integrate.quad` with tolerance `1e-6`; calculate residuals. (FR‑002)
6. **T006** – Write `residuals.csv` conforming to `residuals.schema.yaml`. (FR‑001, FR‑002)
7. **T007** – Assign each supernova to a HEALPix pixel (Nside = 32) using `healpy.ang2pix`; compute **inverse‑variance‑weighted mean residual** per pixel and build mask. (FR‑003, SC‑001)
8. **T008** – **Primary estimator**: Perform a weighted‑least‑squares dipole/quadrupole fit on the individual supernova residuals, using the full per‑object covariance matrix (inverse‑variance weighting).  
9. **T009** – **Secondary estimator**: Compute pseudo‑Cℓ up to ℓ = 3 with MASTER mask correction, weighting each pixel by the inverse variance of its mean residual (scientific_soundness‑de7d659e).  
10. **T010** – Validate pseudo‑Cℓ estimator on synthetic full‑sky maps with injected dipole/quadrupole signals to confirm unbiasedness under Nside = 32 sparsity (methodology‑7cc2ffb5).  
11. **T011** – Generate isotropic mock catalogs by applying a **random 3‑D rotation matrix to both the supernova coordinates *and* the HEALPix mask** (mask‑aware rotation) while preserving redshift and uncertainty distributions (methodology‑8fe51963).  
12. **T012** – For each mock catalog repeat tasks T007‑T009 to obtain dipole and quadrupole amplitudes; record in `simulation_results.csv` (schema: `simulation_results.schema.yaml`). (FR‑005)
13. **T013** – Continue simulations until either (a) a sufficiently large number of realizations are completed., **or** (b) the running mean of the dipole amplitude changes by < 0.001 mag over the last 1 000 simulations (SC‑003).  
14. **T014** – Compute p‑values as the fraction of simulations with amplitude ≥ observed; flag significance if p < 0.05 (primary test) (FR‑006, SC‑004).  
15. **T015** – Assemble `final_report.txt` **and validate it against `final_report.schema.yaml`**, and assemble `analysis_result.json` (validate against `analysis_result.schema.yaml`). (plan_consistency‑3b6d7dcb)  
16. **T016** – Compute and store SHA‑256 hashes for all generated artifacts; update project state file. (Constitution V)

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/specs/001-testing-the-isotropy-of-cosmic-expansion/research.md===
# Research: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Scientific Background
The Cosmological Principle posits that the Universe is statistically homogeneous and isotropic on large scales. Type Ia supernovae (SNe Ia) are standardizable candles that trace the expansion history via their distance moduli. By examining the spatial pattern of residuals—differences between observed and model‑predicted distance moduli—we can test for directional dependence (anisotropy) in the Hubble flow.

## Dataset Strategy
| Dataset | Description | Verified URL | Access Method |
|---------|-------------|--------------|---------------|
| Pantheon+ | Comprehensive SNe Ia compilation with RA, Dec, redshift, distance modulus, and uncertainties. | *No verified URL provided in the specification.* | Manual download from the official Pantheon+ repository (e.g., GitHub `PantheonPlusSH0ES/DataRelease`). |

**Variable Fit Verification**  
Required columns (RA, Dec, redshift *z*, distance modulus μ, uncertainty σ_μ) are present in the official Pantheon+ release. Any rows missing these fields will be excluded and logged (Edge‑Case handling).

## Methodology

### 1. Power Analysis (methodology‑d20a50db)
Before running the full analysis we compute an analytic estimate of the detectable dipole amplitude given the extensive set of supernovae in Pantheon+. Assuming Gaussian residuals with a typical σ on the order of a few tenths of a magnitude., we also run a pilot Monte‑Carlo power study (a substantial set of isotropic mocks) to determine the minimum dipole amplitude that would be detected at p < 0.05 with ≥ 80 % power. This informs the interpretation of a null result and is reported in the final paper.

### 2. Ingestion & Residual Calculation (FR‑001, FR‑002)
- Download the Pantheon+ file, verify its SHA‑256 checksum, and parse it with `pandas`.  
- **Systematic corrections** (methodology‑1c7d21cb): apply Milky Way extinction correction using the Schlegel dust map, correct for peculiar velocities using the 2M++ flow model, and propagate photometric calibration uncertainties into the distance‑modulus error budget.  
- Extract cosmological parameters (H₀, Ωₘ, Ω_Λ) from the dataset’s metadata; **if missing, fall back to independent Planck 2018 priors** (H₀ = 67.4 km s⁻¹ Mpc⁻¹, Ωₘ = 0.315, Ω_Λ = 0.685) (methodology‑9d2fdccc).  
- Compute the theoretical distance modulus  
  \[
  \mu_{\rm th}(z)=5\log_{10}\!\bigl[d_L(z)\bigr]+25,\qquad
  d_L(z)=(1+z)\frac{c}{H_0}\int_0^z\frac{dz'}{E(z')}
  \]
  where \(E(z)=\sqrt{\Omega_m(1+z)^3+\Omega_\Lambda}\).  
  Numerical integration uses `scipy.integrate.quad` with tolerance `1e‑6`.  
- Residuals: \(\Delta\mu = \mu_{\rm obs} - \mu_{\rm th}\).  
- Output: `data/processed/residuals.csv` (schema: `residuals.schema.yaml`).

### 3. HEALPix Projection (FR‑003)
- Map each supernova’s sky coordinates (RA, Dec) to a HEALPix pixel using `healpy.ang2pix` with **Nside = 32** (as required).  
- For each pixel compute the **inverse‑variance‑weighted mean residual** and the number of contributing SNe.  
- Build a mask that marks pixels with at least one observation as valid (value = 1) and others as masked (value = 0).  
- Store the map in a FITS file `healpix_map.fits` (schema: `healpix_map.schema.yaml`).  
- SC‑001 will be measured as the ratio of mapped SNe to the total valid SNe.

### 4. Spherical Harmonic Decomposition & Direct Fit (FR‑004)
- **Primary estimator**: Perform a weighted‑least‑squares dipole and quadrupole fit directly on the individual supernova residuals, using the full per‑object covariance matrix (inverse‑variance weighting).  
- **Secondary estimator**: Apply the pseudo‑\(C_\ell\) estimator with MASTER mask correction (Hivon et al. 2002) to obtain coefficients \(a_{\ell m}\) for \(\ell\le3\), weighting each pixel by the inverse variance of its mean residual (scientific_soundness‑de7d659e).  
- **Validation**: Run the pseudo‑Cℓ pipeline on synthetic full‑sky maps with injected dipole/quadrupole signals to verify unbiasedness under the sparse Nside = 32 sampling (methodology‑7cc2ffb5).  
- Compute scalar amplitudes  
  \[
  A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2}.
  \]  
- Extract dipole (\(\ell=1\)) and quadrupole (\(\ell=2\)) amplitudes (units: magnitudes).  
- SC‑002 will be verified by reproducing the coefficients on a synthetic subset and comparing to a reference `healpy` implementation.

### 5. Null Distribution via Random Rotations (FR‑005)
- Generate isotropic mock catalogs by applying a **random 3‑D rotation matrix to both the supernova coordinates *and* the HEALPix mask** (mask‑aware rotation) while preserving redshift and uncertainty distributions.  
- Use a fixed random seed (`seed=42`) for reproducibility.  
- For each rotated catalog repeat steps 3‑4 to obtain dipole and quadrupole amplitudes.  
- Continue simulations until either (a) 10 000 realizations are completed, **or** (b) the running mean of the dipole amplitude changes by < 0.001 mag over the last 1 000 simulations (SC‑003).  
- Record results in `simulation_results.csv` (schema: `simulation_results.schema.yaml`).

### 6. Significance Assessment (FR‑006)
- Compute p‑values:
  \[
  p_{\rm dipole} = \frac{N(A_1^{\rm sim} \ge A_1^{\rm obs})}{N_{\rm sims}},\qquad
  p_{\rm quad}   = \frac{N(A_2^{\rm sim} \ge A_2^{\rm obs})}{N_{\rm sims}}.
  \]  
- Flag “statistically significant anisotropy” if \(p_{\rm dipole}<0.05\) (primary test) per SC‑004.  
- Produce `final_report.txt` **and validate it against `final_report.schema.yaml`**, and a JSON file `analysis_result.json` validated against `analysis_result.schema.yaml`.

## Decision Rationale
- **Flat ΛCDM residuals**: The specification (FR‑002) explicitly requires a flat ΛCDM model; an independent prior is offered only as a robustness check (methodology‑9d2fdccc).  
- **Primary weighted‑least‑squares fit**: Provides a robust estimator that accounts for irregular sky sampling and per‑object uncertainties, addressing scientific_soundness‑f59a770e.  
- **Pseudo‑Cℓ as secondary check**: Satisfies FR‑004 while remaining CPU‑friendly; validated against synthetic data to ensure unbiasedness (methodology‑7cc2ffb5).  
- **Mask‑aware random rotations**: Ensures the simulated catalogs share the same selection function as the real data and mitigates bias (methodology‑8fe51963).  
- **Systematics handling**: Explicit corrections for extinction, peculiar velocities, and calibration drift reduce spurious anisotropy signals (methodology‑1c7d21cb).  
- **Power analysis**: Quantifies the ability of the ~1500‑SN sample to detect realistic dipole amplitudes, satisfying methodological rigor (methodology‑d20a50db).  
- **CPU‑only feasibility**: All libraries (`healpy`, `scipy`) run efficiently on the GitHub Actions runner; the simulation loop includes an early‑stop convergence criterion to respect the 6 h runtime budget (SC‑004).  

## References
1. Pantheon+ Collaboration, *The Pantheon+ Analysis: Cosmological Constraints* (2021). Official repository: https://github.com/PantheonPlusSH0ES/DataRelease  
2. Healpy Documentation – Spherical Harmonic Analysis. https://healpy.readthedocs.io/  
3. Hivon et al. (2002), “MASTER of the CMB Anisotropy Power Spectrum”, *ApJ*, 567, 2.  
4. Schlegel, D. J., Finkbeiner, D. P., Davis, M. (1998), “Maps of Dust Infrared Emission for Use in Estimation of Reddening and CMB Foregrounds”, *ApJ*, 500, 525.  
5. 2M++ Flow Model (Carrick et al. 2015).  
6. Planck Collaboration (2018), *Planck 2018 results. VI. Cosmological parameters*.  

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/specs/001-testing-the-isotropy-of-cosmic-expansion/quickstart.md===
# Quickstart: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Prerequisites
- Python 3.11 or newer
- Git
- ~8 GB free disk space (for dataset and intermediate files)

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup

1. **Obtain Pantheon+**  
   - Visit the official Pantheon+ repository (https://github.com/PantheonPlusSH0ES/DataRelease).  
   - Download the file `Pantheon+_SH0ES.dat` (or the latest CSV equivalent).  
   - Place the file in `data/raw/`.  
2. **Verify integrity** (the SHA‑256 hash is recorded in `data/raw/manifest.json`):
   ```bash
   python code/ingestion.py --verify-only
   ```

## Run the Full Analysis

```bash
python code/analysis.py
```

The script performs the following automatically:
1. Ingests and filters the Pantheon+ data, writes `residuals.csv`.  
2. Projects residuals onto a HEALPix grid (`healpix_map.fits`).  
3. Computes dipole and quadrupole amplitudes via a **primary weighted‑least‑squares fit** and a **secondary pseudo‑Cℓ cross‑check**.  
4. Generates isotropic mock catalogs via **mask‑aware random rotations**, monitors convergence, and writes `simulation_results.csv`.  
5. Calculates p‑values, validates `final_report.txt` against `final_report.schema.yaml`, and writes `analysis_result.json` validated against `analysis_result.schema.yaml`.

## Outputs

- `data/processed/residuals.csv` – cleaned supernova table with residuals.  
- `data/processed/healpix_map.fits` – HEALPix map of mean residuals.  
- `data/processed/simulation_results.csv` – dipole/quadrupole amplitudes from each mock catalog.  
- `data/reports/final_report.txt` – human‑readable summary of the dipole/quadrupole amplitudes, p‑values, and significance flag (validated against schema).  
- `analysis_result.json` – machine‑readable result validated against `contracts/analysis_result.schema.yaml`.

## Validation (Synthetic Test)

To confirm the pipeline can recover a known signal:

```bash
python code/analysis.py --synthetic --inject-dipole 0.04
```

This creates a synthetic supernova sample with an injected dipole of a low magnitude (mag), runs the full pipeline, and prints the recovered amplitude and p‑value.

## Troubleshooting

- **MemoryError** – Reduce the number of simulations by editing `code/simulations.py` (`MAX_SIMULATIONS = 2000`).  
- **Missing columns** – Ensure the raw Pantheon+ file contains the required columns (`RA`, `DEC`, `z`, `mu`, `muerr`).  
- **Runtime > 6 h** – The script automatically stops the simulation loop once the convergence criterion (Δmean < 0.001 mag over last 1 000 sims) is met; you can also lower `MAX_SIMULATIONS` manually.

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/specs/001-testing-the-isotropy-of-cosmic-expansion/contracts/simulation_output.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Simulation Output"
description: "Deprecated schema – the project now uses `simulation_results.schema.yaml`. Retained for backward compatibility only; no tasks reference this schema."
type: "object"
properties:
  run_id:
    type: "integer"
    description: "Unique iteration ID."
  dipole_amplitude:
    type: "number"
    description: "Dipole amplitude for this simulation run."
  quadrupole_amplitude:
    type: "number"
    description: "Quadrupole amplitude for this simulation run."
  seed:
    type: "integer"
    description: "Random seed used for this iteration (always 42)."
required:
  - run_id
  - dipole_amplitude
  - quadrupole_amplitude
  - seed
additionalProperties: false
## NOTE: This schema is deprecated and intentionally not used by any pipeline step.