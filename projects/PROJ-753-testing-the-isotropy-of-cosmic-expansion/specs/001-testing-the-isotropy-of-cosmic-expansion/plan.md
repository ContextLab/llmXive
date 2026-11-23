# Implementation Plan: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Branch**: `001-testing-isotropy-cosmic-expansion` | **Date**: 2026-10-21 | **Spec**: `specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`  
**Input**: Feature specification from `/specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`

## Summary
The pipeline will (1) download the Pantheon+ Type Ia supernova compilation, (2) compute flat‑ΛCDM distance‑modulus residuals, (3) project residuals onto a HEALPix grid (Nside = 32), (4) estimate dipole and quadrupole amplitudes using a mask‑aware weighted‑least‑squares fit (primary) and a pseudo‑\(C_\ell\) MASTER‑corrected estimator (secondary), (5) generate a null distribution by mask‑aware random rotations that preserve the survey‑depth mask, (6) assess statistical significance, and (7) produce a deterministic power‑analysis report that quantifies the detectable dipole amplitude for the given sample size. All steps are deterministic, reproducible, and run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `astropy`, `healpy`, `matplotlib`, `tqdm`  
- **Storage**: Local filesystem under `data/` (raw, processed, reports)  
- **Testing**: `pytest` unit‑ and integration‑tests, plus schema validation with `jsonschema`  
- **Target Platform**: Linux runner in GitHub Actions (2 CPU cores, ~7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: Fixed random seed (`seed=42`), early‑stop convergence criterion for simulations, memory‑friendly streaming of the Pantheon+ file if needed.  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Fixed seeds, deterministic scripts, dataset fetched from a canonical URL on every run. |
| II. Verified Accuracy | **Pending** – the Pantheon+ URL used is not a verified citation (no verified DOI available). The plan flags this for resolution; a Zenodo‑mirrored DOI will be adopted when available. |
| III. Data Hygiene | Raw file stored under `data/raw/` with SHA‑256 checksum; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | All figures, tables, and the final JSON report are generated programmatically from the processed artifacts. |
| V. Versioning Discipline | Content hashes of all output files are recorded in the project state YAML by the advancement evaluator. |
| VI. Anisotropy Signal Quantification | Dipole and quadrupole amplitudes are the sole anisotropy metrics (FR‑004, VI). |
| VII. Pantheon+ Data Versioning | Dataset tag is recorded in `metadata.json` and included in the final `analysis_result.json`. |

## Project Structure
```text
specs/001-testing-the-isotropy-of-cosmic-expansion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── residuals.schema.yaml
│   ├── healpix_map.schema.yaml
│   ├── simulation_results.schema.yaml
│   ├── analysis_result.schema.yaml
│   ├── final_report.schema.yaml
│   └── power_analysis_results.schema.yaml   # new
└── tasks.md   # generated later
```

## Phase Breakdown & Mapping to FR/SC

| Phase | Tasks (≈12 substantive) | FR addressed | SC addressed |
|-------|--------------------------|--------------|--------------|
| **Phase 0 – Power‑Analysis Feasibility** | 0.1 Compute an analytic detection limit for a dipole given \(N\approx1500\) SNe using a **heteroscedastic** error model: each SN’s \(\sigma_i = \sqrt{\mu_{\text{err},i}^2 + \sigma_{\text{sys}}^2}\) with \(\sigma_{\text{sys}}=0.02\) mag. 0.2 Run a **Monte‑Carlo** pilot (10 000 isotropic mocks) that *samples each SN’s individual σ_i* and preserves the observed redshift distribution, recording dipole amplitudes. 0.3 Write `power_analysis_results.csv` (schema: `power_analysis_results.schema.yaml`). This satisfies SC‑004 (runtime budgeting) and provides a transparent power justification. | – | SC‑004 (runtime budgeting) & implicit power‑analysis requirement |
| **Phase 1 – Data Model & Contracts** | Create JSON/YAML schemas for all output files, including the new power‑analysis schema. Update `data-model.md`. | – | – |
| **Phase 2 – Ingestion & Residuals** | T001 – Download Pantheon+ release, verify SHA‑256. T002 – Parse, filter rows missing RA/Dec/z/μ/σ, log exclusions. T003 – Extract H₀, Ωₘ, Ω_Λ from metadata (fallback to Planck 2018 if absent). T004 – Apply Milky Way extinction (Schlegel 1998) and 2M++ peculiar‑velocity corrections. T005 – Numerically integrate \(d_L(z)\) with `scipy.integrate.quad` (tol = 1e‑6) to obtain μ_th. T006 – Compute residuals Δμ = μ_obs − μ_th and write `data/processed/residuals.csv`. | FR‑001, FR‑002 | – |
| **Phase 3 – HEALPix Projection** | T007 – Convert (RA, Dec) → HEALPix pixel (`healpy.ang2pix`, Nside = 32). T008 – Compute **inverse‑variance‑weighted** mean residual per pixel, build mask, write `healpix_map.fits`. | FR‑003 | SC‑001 (fraction of SNe mapped) |
| **Phase 4 – Anisotropy Estimation** | T009 – **Primary estimator**: Perform a **mask‑aware weighted‑least‑squares** fit. Construct a design matrix **X** that maps each SN to the three dipole basis vectors and five quadrupole basis vectors; build a full covariance matrix **C = diag(σ_i²) + σ_sys²·1·1ᵀ** (σ_sys=0.02 mag) to capture correlated systematic error; apply the HEALPix mask **M** (pixels with no data receive zero weight). Solve \((X^\top C^{-1} M X) \beta = X^\top C^{-1} M y\) where \(y\) are the residuals. This explicitly accounts for uneven sky coverage, heteroscedastic uncertainties, and a common systematic term. T010 – **Secondary estimator**: pseudo‑\(C_\ell\) up to ℓ = 3 with MASTER mask correction (Hivon et al. 2002). T011 – Extract scalar amplitudes \(A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_m |a_{\ell m}|^2}\). | FR‑004 | SC‑002 (reproducibility against healpy reference) |
| **Phase 5 – Null Distribution via Mask‑Aware Rotations** | T012 – Generate isotropic mocks by applying a random 3‑D rotation matrix (seed = 42) **to both** the RA/Dec positions **and** the survey‑depth (magnitude‑limit) mask derived from the observed sky‑density map. After rotation, re‑apply the same magnitude cut to enforce the original sky‑dependent selection function while preserving redshift and uncertainty distributions. T013 – For each mock repeat Phase 3 & 4, record dipole/quadrupole amplitudes in `simulation_results.csv`. T014 – **Simulation count**: Enforce a **minimum of 5 000 simulations**. After this floor, continue until **both** (a) the running mean of dipole amplitude changes by < 0.001 mag over the last 1 000 sims **and** (b) the 95 % binomial confidence interval for the estimated p‑value has width ≤ 0.01. If either condition is not met, run up to a hard cap of **20 000 simulations**. This satisfies SC‑003 and guarantees adequate tail sampling for a 0.05 significance test. | FR‑005 | SC‑003 |
| **Phase 6 – Significance Assessment & Reporting** | T015 – Compute p‑values as the fraction of simulations with amplitude ≥ observed, and report the 95 % binomial confidence interval. T016 – Flag “statistically significant anisotropy” if \(p_{\rm dipole}<0.05\) (FR‑006, SC‑004). T017 – Write `final_report.txt` and validate against `final_report.schema.yaml`. T018 – Write `analysis_result.json` and validate against `analysis_result.schema.yaml`. | FR‑006 | SC‑004 |
| **Phase 7 – Artifact Hashing & Finalisation** | Compute SHA‑256 hashes for all generated files, update project state YAML, ensure all constitution checks still pass. | – | – |

### Detailed Task List (selected)

1. **T001** – Download Pantheon+ from the official GitHub repository (`).  
2. **T002** – Filter invalid rows; log count of excluded entries (edge‑case requirement).  
3. **T003** – Parse metadata for H₀, Ωₘ, Ω_Λ; fallback to Planck 2018 if missing.  
4. **T004** – Apply extinction and peculiar‑velocity corrections (methodology‑1c7d21cb).  
5. **T005** – Numerical integration for μ_th (tolerance = 1e‑6).  
6. **T006** – Write `residuals.csv` (schema `residuals.schema.yaml`).  
7. **T007** – HEALPix mapping (Nside = 32).  
8. **T008** – Write `healpix_map.fits` (schema `healpix_map.schema.yaml`).  
9. **T009** – Mask‑aware weighted‑least‑squares dipole/quadrupole fit with full covariance (including σ_sys).  
10. **T010** – Pseudo‑\(C_\ell\) with MASTER correction (secondary estimator).  
11. **T011** – Compute amplitudes \(A_1\), \(A_2\).  
12. **T012** – Generate mask‑aware rotated mocks (seed = 42) preserving magnitude‑limit mask.  
13. **T013** – Run estimators on each mock, append to `simulation_results.csv` (schema `simulation_results.schema.yaml`).  
14. **T014** – **Power‑analysis step** (Phase 0) – analytic estimate plus pilot Monte‑Carlo preserving per‑SN σ; produces `power_analysis_results.csv` (schema `power_analysis_results.schema.yaml`).  
15. **T015** – Compute p‑values, flag significance.  
16. **T016** – Write and validate `final_report.txt`.  
17. **T017** – Write and validate `analysis_result.json`.  
18. **T018** – Hash artifacts, update state YAML.

All tasks are designed to run within the CPU limits of the free GitHub Actions runner. The pilot power analysis (Phase 0) streams the dataset; memory usage stays < 2 GB. The full simulation (Phase 5) respects the early‑stop criterion and the 5 000‑simulation floor, keeping total runtime ≈ a few hours on the free runner.

## Compute Feasibility
- **CPU‑first**: All libraries (`healpy`, `scipy`, `numpy`) have pure‑Python or lightweight compiled wheels that run on CPU.  
- **Memory**: Streaming read of the Pantheon+ CSV (≈ 200 MB) ensures peak RAM < 3 GB.  
- **Runtime**: Analytic power estimate (< 30 s). Pilot Monte‑Carlo (10 k sims) ≈ 5 min. Full simulation (≥ 5 k sims, early‑stop) ≈ 3 h on the free runner.  

## Data Availability
- Pantheon+ is openly hosted on GitHub; the download URL is programmatic and does not require authentication. A Zenodo mirror (DOI to be added when available) will be used to satisfy Principle II.  
- No gated datasets are required.  

## Success Criteria Mapping
- **SC‑001** – Measured in Phase 3 (fraction of valid SNe mapped).  
- **SC‑002** – Verified in Phase 4 by reproducing coefficients on a synthetic injected‑signal map.  
- **SC‑003** – Convergence of dipole mean across simulations (Phase 5) plus binomial‑interval check.  
- **SC‑004** – Total wall‑clock time recorded in `analysis_result.json`; must be ≤ 21600 s (6 h).  

---  
*End of Implementation Plan*===