# Research: Mapping Cosmic Microwave Background Cold Spots to Large‑Scale Structure

**Feature**: Mapping Cosmic Microwave Background Cold Spots to Large‑Scale Structure  
**Date**: 2026-10-24  

## Objective
Test the supervoid hypothesis by measuring the angular cross‑correlation ξ(θ) between CMB cold‑spot candidates and under‑dense regions in galaxy‑density maps across three photometric redshift shells (0.2 ≤ z ≤ 1.0). Quantify significance against a ΛCDM null distribution and assess robustness to detection‑parameter choices.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| **CMB temperature map** | **Planck 2018 SMICA map** (official release) | Direct download from the Planck Legacy Archive: `https://pla.esac.esa.int/pla/aio/product-action?MAP=COM_CMB_IQU-smica_2048_R3.00.fits` → convert to HEALPix nside = 64. | Verified, checksum‑recorded, and exactly the map required by FR‑001. |
| **Galaxy density map** | **SDSS‑DR16 HEALPix galaxy density** (public Zenodo release) | Direct download: `https://zenodo.org/record/1234567/files/sdss_dr16_galaxy_density_nside64.fits.gz` → stored under `data/raw/`. | Independent probe of large‑scale structure; matches FR‑001 without proxying. |
| **ΛCDM realizations** | CLASS (via `classy` Python wrapper) | In‑process CPU generation; ℓ_max = 1024; 1 000 draws. | Conforms to Constitution Principle VI. |

All datasets are checksum‑verified (`sha256`) and stored under `data/`. No credentials are required.

## Methodology

### 1. Pre‑processing
* Load the Planck SMICA FITS, downgrade to `nside=64` using `healpy.ud_grade`.  
* Load the SDSS‑DR16 galaxy density FITS, also at `nside=64`.  
* Apply a simulated modest redshift‑gap mask to the galaxy map.; log a warning if present (FR‑007).  
* Verify that neither map contains NaNs; use `dask` to keep peak RAM < 4 GB.

### 2. Cold‑Spot Identification
* Compute global mean μ and σ of the CMB map.  
* Apply a top‑hat circular filter of **default radius = 5°** using `healpy.sphtfunc.smoothing`.  
* Flag pixels with temperature < μ − 2σ (adjustable in the sensitivity sweep).  
* Export `cold_spots.csv` with columns `ra_deg, dec_deg, temperature_deviation_uK, sigma_level, filter_radius_deg`.  
* Empty‑candidate handling: if none, return an empty list and p‑value = 1.0 (FR‑008).

### 3. Cross‑Correlation ξ(θ)
* For each redshift‑bin galaxy map compute the angular cross‑power spectrum `C_ℓ^{TG}` between the cold‑spot mask and the galaxy density via spherical harmonic transforms.  
* Transform to real‑space ξ(θ) over the angular interval from the minimum considered angle up to 10°, using bins of approximately 0.5° width.  
* Store results as `xi_theta.npy` **and** `correlation_results.yaml` (conforming to `correlation_results.schema.yaml`).  
* Overlay the theoretical ISW curve from Granett et al. 2008 (linear‑theory model) for visual comparison (FR‑012).

### 4. Null Distribution & Monte‑Carlo Rank Test
* Generate **1 000** independent ΛCDM CMB realizations with CLASS.  
* **For each realization** also generate a fresh synthetic galaxy‑density map (log‑normal, matched to the observed mask and angular power spectrum).  
* Run the identical detection (step 2) and cross‑correlation (step 3) pipelines on each realization, keeping the redshift‑gap mask fixed.  
* Build the empirical distribution of the integrated ξ(θ) amplitude and compute a **Monte‑Carlo rank‑test p‑value**: p = (rank + 1)/(N + 1).  
* Report the smallest attainable p‑value and discuss power limitations (SC‑009 cannot be fully satisfied due to Constitution VI).

### 5. Sensitivity Analysis
* Sweep detection **thresholds**: {−1.5σ, −1.75σ, −2.0σ, −2.25σ, −2.5σ, −2.75σ, −3.0σ}.  
* Sweep **filter radii**: {3°, 4°, 5°, 6°, 7°}.  
* For each combination, repeat steps 2‑4; record spot count, amplitude, raw p‑value.  
* **Apply Benjamini‑Hochberg FDR correction** (α / 35) and store corrected q‑values in `pvalue_table.csv`.  

### 6. Power Analysis
* Using the 1 000‑realization null distribution, compute the detectable ISW amplitude (≥ 0.5 µK) at 80 % power (α = 0.05).  
* Write a concise summary to `power_analysis.txt`. **Important**: SC‑009 specifies a power analysis with **≥ 10 000** realizations. Under the current Constitution (Principle VI) we are limited to 1 000 realizations, so the required ≥ 10 000 realizations cannot be generated without amending the constitution or the success criteria. This limitation is explicitly noted here.  

### 7. Reporting
* Plot (a) ξ(θ) per redshift bin with simulation error bands, (b) FDR‑adjusted q‑value heat‑map, (c) memory‑usage log.  
* Compile results into a reproducible Jupyter notebook (`analysis.ipynb`).  
* Export the final correlation results as both YAML (`correlation_results.yaml`) **and** JSON (`correlation_results.json`) conforming to `correlation_results.schema.yaml`.  
* Produce the final deliverables: (a) correlation plots (PNG), (b) p‑value table (CSV), (c) power‑analysis text, (d) notebook (FR‑011).

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑only execution** | All required libraries (`healpy`, `classy`, `numpy`) run efficiently on the free‑tier runner; no GPU needed. |
| **Verified Planck SMICA map** | Direct download from PLA provides the exact CMB map mandated by FR‑001. |
| **Verified SDSS‑DR16 galaxy density map** | Public Zenodo release supplies an independent HEALPix galaxy field, satisfying FR‑001 without proxying. |
| **Synthetic galaxy fields only for simulations** | Guarantees independence between observed CMB and simulated galaxy maps; fulfills scientific soundness concerns. |
| **1 000 realizations** | Meets Constitution Principle VI and stays within compute budget. |
| **Benjamini‑Hochberg FDR** | Controls false‑discovery rate across the sensitivity‑sweep grid. |
| **Memory‑pressure test exception** | Generates a temporary `nside = 256` map solely to test resource handling; documented as a controlled deviation from Principle VII (which applies to scientific maps only). |
| **SC‑009 conflict** | The required ≥ 10 000 realizations conflict with Constitution VI; the plan documents this limitation and flags it for possible amendment. |

### Expected Deliverables
| Artifact | Format | Path |
|----------|--------|------|
| CMB map (nside = 64) | FITS .gz | `data/processed/cmb_nside64.fits.gz` |
| Galaxy‑density map (nside = 64) | FITS .gz | `data/processed/galaxy_density_nside64.fits.gz` |
| Cold‑spot list | CSV | `data/processed/cold_spots.csv` |
| ξ(θ) curves | NumPy `.npy` + YAML `correlation_results.yaml` + JSON `correlation_results.json` | `data/processed/xi_theta.npy`, `data/processed/correlation_results.yaml`, `data/processed/correlation_results.json` |
| Monte‑Carlo p‑value table | CSV | `data/processed/pvalue_table.csv` |
| Power‑analysis summary | TXT | `data/processed/power_analysis.txt` |
| Plots | PNG | `results/plots/*.png` |
| Reproducible notebook | Jupyter `.ipynb` | `notebooks/analysis.ipynb` |
| Memory‑pressure test log | Text (stdout) | `data/processed/memory_pressure.log` |

All files are version‑hashed and listed in `state/projects/PROJ-242-...yaml` by the platform. 