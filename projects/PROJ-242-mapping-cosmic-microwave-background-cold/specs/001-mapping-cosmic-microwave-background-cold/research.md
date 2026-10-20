# Research: Mapping Cosmic Microwave Background Cold Spots to Large‑Scale Structure

**Feature**: Mapping Cosmic Microwave Background Cold Spots to Large‑Scale Structure  
**Date**: 2026‑10‑20  

## Objective
Test the supervoid hypothesis by measuring the angular cross‑correlation ξ(θ) between CMB cold‑spot candidates and under‑dense regions in galaxy density maps across three photometric redshift shells (0.2 ≤ z ≤ 1.0). Quantify significance against a ΛCDM null distribution and assess robustness to detection‑parameter choices.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| **CMB temperature map** | **Planck 2018 SMICA map** (full‑sky) | Direct download from the Planck Legacy Archive: `https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP=COM_CMB_IQU-smica_2048_R3.00_full.fits` → convert to HEALPix FITS, downsample to nside = 64. | Verified open URL; matches the construct required for ISW studies. |
| **Galaxy density** | **SDSS‑DR16 photometric galaxy catalog** | Programmatic download via `datasets.load_dataset("sdss/dr16_photoobj")` or direct HTTP fetch from `https://data.sdss.org/sas/dr16/eboss/photoObj/`. The catalog is masked, redshift‑binned (0.2‑0.4, 0.4‑0.6, 0.6‑1.0) and projected to HEALPix nside = 64. | Verified open dataset; provides real large‑scale structure and photometric redshifts. |
| **ΛCDM realizations** | CLASS (via `classy` Python wrapper) | In‑process CPU generation; ℓ_max = 1024; 2 000 draws. | Conforms to Constitution Principle VI. |

All datasets are checksum‑verified (`sha256`) and stored under `data/`. No credentials are required.

## Methodology

### 1. Pre‑processing
* Convert the Planck SMICA FITS to HEALPix nside = 64 (`healpy.ud_grade`).  
* Ingest the SDSS‑DR16 catalog, apply the official SDSS mask, and bin galaxies into three redshift shells, creating HEALPix density maps (`galaxy_density_z*.fits.gz`).  
* Simulate a 5 % redshift‑gap mask; log a warning if present (FR‑007).  

### 2. Cold‑Spot Identification
* Compute global mean μ and σ of the CMB map.  
* Apply a top‑hat circular filter of **default radius = 5°** using `healpy.sphtfunc.smoothing`.  
* Flag pixels with temperature < μ − 2σ (adjustable in the sensitivity sweep).  
* Export `cold_spots.csv` with columns `ra_deg, dec_deg, temperature_deviation_uK, sigma_level, filter_radius_deg`.  
* Empty‑candidate handling: if none, return empty list and p‑value = 1.0 (FR‑008).

### 3. Cross‑Correlation ξ(θ)
* For each redshift bin, compute the angular cross‑power spectrum `C_ℓ^{TG}` between the cold‑spot mask and the galaxy overdensity map via spherical harmonic transforms.  
* Transform to real‑space ξ(θ) for θ ∈ [0°, 10°] in 0.5° bins.  
* Store results as `xi_theta.npy` **and** `correlation_results.yaml` (conforming to `correlation_results.schema.yaml`).  
* Overlay the theoretical ISW curve from Granett et al. 2008 (linear‑theory model) for visual comparison (FR‑012).

### 4. Null Distribution & Monte‑Carlo Rank Test
* Generate **2 000** independent ΛCDM CMB realizations with CLASS.  
* **For each realization** also generate a fresh random galaxy density field (Gaussian with the observed angular power spectrum) to capture variance in the galaxy probe.  
* Run identical detection (step 2) and cross‑correlation (step 3) pipelines on each realization, keeping the redshift‑gap mask fixed.  
* Build the empirical distribution of the integrated ξ(θ) amplitude and compute a **Monte‑Carlo rank‑test p‑value**: p = (rank + 1)/(N + 1).  
* Report the smallest attainable p-value and discuss power limitations.

### 5. Sensitivity Analysis
* Sweep detection **thresholds**: {−1.5σ, −1.75σ, −2.0σ, −2.25σ, −2.5σ, −2.75σ, −3.0σ}.  
* Sweep **filter radii**: {3°, 4°, 5°, 6°, 7°}.  
* For each of the combos, repeat steps 2‑4; record spot count, amplitude, raw p‑value.  
* **Apply Bonferroni correction** (α / 35) and store corrected p‑values in `pvalue_table.csv`.  

### 6. Statistical Rigor Checklist
* **Multiple‑comparison** – Bonferroni correction applied to the 35 sensitivity‑sweep tests.  
* **Power** – Monte-Carlo draws are used to obtain a minimal p-value, which is bounded by the number of draws; this floor is reported.  
* **Causal inference** – Observational correlation only; claims remain associational.  
* **Measurement validity** – Planck SMICA map validated against Planck low‑ℓ variance; SDSS‑DR16 catalog calibrated to published clustering amplitudes (Zehavi et al. 2011).  
* **Collinearity** – Cold‑spot mask and galaxy density are distinct fields; no predictor collinearity concerns.

### 7. Reporting
* Plot (a) ξ(θ) per redshift bin with simulation error bands, (b) Bonferroni‑corrected p‑value heat‑map, (c) memory‑usage log.  
* Compile results into a reproducible Jupyter notebook (`analysis.ipynb`).  
* Export final artifacts: PNG plots, CSV p‑value table, YAML correlation results, and the notebook (FR‑011).

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑only execution** | All required libraries (`healpy`, `classy`, `numpy`) run efficiently on the free‑tier runner; no GPU needed. |
| **Real SDSS‑DR16 galaxy catalog** | Provides authentic large‑scale structure, masks, and redshift information, satisfying construct validity. |
| **Planck SMICA CMB map** | Publicly verified source matching the hypothesis construct. |
| **Randomized galaxy field in simulations** | Prevents confounding and fulfills Constitution Principle VI. |
| **2 000 Monte‑Carlo draws** | Improves p‑value resolution while staying within compute budget. |
| **Bonferroni correction** | Controls family‑wise error across the sensitivity‑sweep grid. |
| **Memory‑pressure test exception** | Generates a temporary `nside = 256` map solely to test resource handling; documented as a controlled deviation from Principle VII (which applies to scientific maps only). |

### Expected Deliverables
| Artifact | Format | Path |
|----------|--------|------|
| CMB map (nside = 64) | FITS .gz | `data/processed/cmb_nside64.fits.gz` |
| Galaxy density maps (3 redshift bins) | FITS .gz | `data/processed/galaxy_density_z{bin}_nside64.fits.gz` |
| Cold‑spot list | CSV | `data/processed/cold_spots.csv` |
| ξ(θ) curves | NumPy `.npy` + YAML `correlation_results.yaml` | `data/processed/xi_theta.npy`, `data/processed/correlation_results.yaml` |
| Monte‑Carlo p‑value table | CSV | `data/processed/pvalue_table.csv` |
| Plots | PNG | `results/plots/*.png` |
| Reproducible notebook | Jupyter `.ipynb` | `notebooks/analysis.ipynb` |
| Memory‑pressure test log | Text (stdout) | `data/processed/memory_pressure.log` |

All files are version‑hashed and listed in `state/projects/PROJ-242-...yaml` by the platform.  
