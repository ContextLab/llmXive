# Implementation Plan: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

**Branch**: `001-cmb-defect-analysis` | **Date**: 2026-07-03 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-cmb-defect-analysis/spec.md`

## Summary
The project must (1) download the Planck 2015/2018 SMICA temperature map at Nside = 128, (2) apply a Galactic mask preserving ≥95 % sky coverage, (3) compute the three Minkowski Functionals (area, perimeter, genus) at the five specific σ‑levels (‑1.0, ‑0.5, 0.0, +0.5, +1.0 σ) with ≥6‑decimal precision, (4) generate **1 000** Gaussian random‑field simulations from the **theoretical** Planck 2015 TT power spectrum (including beam smoothing and instrumental noise), (5) estimate the covariance of the functionals across simulations, (6) perform a multivariate Hotelling’s T² test comparing observed to simulated statistics, and (7) produce a JSON‐formatted results package. All steps must complete on a GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `healpy==1.16.6`, `pyminkowski==0.1.2`, `numpy==1.26.*`, `scipy==1.12.*`, `astropy==6.*`, `pandas==2.*`, `tqdm==4.*`, `psutil==5.*`, `pytest==8.*`  
- **Storage**: File‑based (raw maps in `data/raw/`, derived products in `data/processed/`)  
- **Testing**: `pytest` with fixtures for checksum validation and reproducibility checks  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Full pipeline ≤5 h 30 min, peak RAM ≤6.5 GB  
- **Constraints**: CPU‑only, no GPU, all random seeds pinned for reproducibility  
- **Scale/Scope**: One Planck SMICA map, A substantial number of simulations will be run. 

The research question is: Can agent-based modeling reveal emergent patterns of collective behavior in swarms? The method will involve implementing a multi-agent system where individual agents follow simple rules and interact locally, then observing the global patterns that emerge from these interactions. (Kennedy, 1997) and (Reynolds, 1986)., three Minkowski Functionals  

## Constitution Check
| Principle | How the Plan Satisfies It |
|-----------|---------------------------|
| I. Reproducibility | All scripts are deterministic (fixed seeds), data fetched from the canonical Planck Legacy Archive, checksums recorded in `data/manifest.yaml`. |
| II. Verified Accuracy | Citations to Planck 2015/2018 papers and to the original Minkowski Functional literature are included in `research.md`. No unverified claims are introduced. |
| III. Data Hygiene | Raw downloads are stored unchanged under `data/raw/` with SHA‑256 checksums; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | Every figure/table in the eventual paper will be generated from the JSON/CSV artifacts in `data/processed/`. No manual copying of numbers. |
| V. Versioning Discipline | `requirements.txt` pins exact versions; each artifact’s hash is recorded in `state/projects/PROJ-352-...yaml`. |
| VI. Statistical Significance & Null Modeling | The multivariate Hotelling’s T² test directly implements the null‑model comparison required by the constitution. |
| VII. Parameter Inference Integrity | The final result is presented only as an associational constraint on non‑Gaussianity; no single‑point Gμ estimate is reported. |

## Project Structure
```
specs/001-cmb-defect-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── cmb_map.schema.yaml
    └── analysis_results.schema.yaml

src/
├── pipeline.py                # orchestrates all phases
├── data/
│   ├── download.py            # Planck download & checksum
│   ├── mask.py                # Galactic mask handling
│   ├── minkowski.py           # MF computation via pyminkowski
│   ├── simulations.py         # Gaussian realizations (theoretical Cl)
│   └── stats.py               # covariance & Hotelling test
└── utils/
    ├── logger.py
    └── resources.py           # URLs, checksums, seeds
```

## Phase‑by‑Phase Plan (mapping FR/SC)

| Phase | Description | FR(s) addressed | Key Deliverable |
|-------|-------------|-----------------|-----------------|
| **0 – Environment Setup** | Create virtualenv, install pinned dependencies, verify Python version. | — | `requirements.txt` installed; `setup.log`. |
| **1 – Data Acquisition** | Download Planck SMICA map (Nside = 128) from the Planck Legacy Archive (`https://pla.esac.esa.int/pla/aio/product-action?product=COM_CMB_SMICA_2048_R3.00_full.fits`) and validate SHA‑256 checksum, store under `data/raw/planck_smica.fits`. | FR‑001, SC‑001 | `data/raw/planck_smica.fits`, checksum record. |
| **2 – Mask Application** | Download official Galactic mask (`https://pla.esac.esa.int/pla/aio/product-action?product=COM_Mask_Galactic_2048_R3.00.fits`), apply with a 2‑pixel buffer, enforce ≥95 % sky coverage, produce masked map `data/processed/masked_smica.fits`. | FR‑002, SC‑001 | Masked map file + coverage metadata. |
| **3 – Basic Statistics** | Compute mean & std of masked map for sanity check (physically plausible range). | FR‑001 (implicit validation) | `data/processed/basic_stats.json`. |
| **4 – Minkowski Functional Computation** | Compute area, perimeter, and genus at the five σ‑levels (‑1.0, ‑0.5, 0.0, +0.5, +1.0) using the **`pyminkowski`** library. Results are rounded to 6 decimal places. | FR‑003, SC‑002 | `data/processed/minkowski_observed.json`. |
| **5 – Gaussian Simulations (Generation)** | Using `healpy.synfast`, generate **1 000** Gaussian random fields that reproduce the **theoretical** Planck 2015 TT power spectrum (`COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits`), convolve with a A Gaussian beam with a narrow waist. 

The research question is: How do variations in beam waist affect the precision of optical tweezers?
The method is: We will use a simulated optical trapping system to measure the lateral and axial trapping stiffness as a function of beam waist.
References: (DOI: 10.1039/C7SM01842J), (Smith, 2018)., add white Gaussian noise (variance = 1.1 µK²). Simulations are processed **in‑memory** in batches of 200 to keep RAM ≤6.5 GB; only the functional values are persisted. Estimated wall‑time ≈ 4.5 h on 2 CPU. | FR‑004, SC‑003 | In‑memory functional arrays; final CSV `data/processed/minkowski_sims.json`. |
| **6 – Minkowski Functionals on Simulations** | Loop over the in‑memory simulations, compute the three functionals (same thresholds), store results in a single JSON/CSV (`minkowski_sims.json`). | FR‑003 (applied to sims) | `data/processed/minkowski_sims.json`. |
| **7 – Covariance Estimation** | Compute empirical 3×3 covariance matrix of the three functionals for each threshold across the 1 000 simulations. | FR‑006, SC‑003 | `data/processed/minkowski_covariance.npy`. |
| **8 – Multivariate Hotelling’s T² Test** | Perform Hotelling’s T² test comparing observed vector to simulation mean, using the covariance from Phase 7; compute p‑value to ≥6 decimal places. | FR‑005, SC‑003 | `data/processed/hotelling_result.json`. |
| **9 – Resource Monitoring & Hard Failure** | Continuously monitor RAM via `psutil`; if usage exceeds 6.5 GB **or** any phase exceeds its allocated wall‑time, the pipeline aborts with a non‑zero exit code and no partial results are written. This guarantees compliance with the free‑tier limits and preserves statistical validity. | FR‑007, Edge Cases | Log file `pipeline_monitor.log` (only on success). |
| **10 – Reporting & Artifact Generation** | Assemble a concise Markdown summary (`report.md`), generate `analysis_results.json` conforming to `analysis_results.schema.yaml`, and produce a PNG plot of observed vs. simulation MF curves (`figures/mf_comparison.png`). | All FRs, SC‑004 | `analysis_results.json`, `report.md`, `figures/mf_comparison.png`. |
| **11 – Testing & Validation** | Run pytest suite; ensure checksum validation, reproducibility, and that acceptance criteria are met. | All FRs, SC‑001/002/003 | Test report `test_results.xml`. |

### Timing Estimate (CPU‑only, batch‑wise)
- Download & checksum: [deferred]  
- Masking & basic stats: [deferred]  
- Observed MF computation: [deferred]  
- Simulation generation (1 000 maps, batch = 200, in‑memory): **≈ 4.5 h**  
- MF on simulations: **≈ 1.0 h**  
- Covariance & Hotelling test: < 5 min  
- Reporting & plotting: [deferred]  
- Testing: [deferred]

**Total ≈ 5 h 30 min**, comfortably below the 6 h ceiling and respecting the free‑tier resource limits.

---


## projects/PROJ-352-statistical-analysis-of-early-universe-c/specs/001-statistical-analysis-of-early-universe-c/research.md===
# Research: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Research Question
*Can Minkowski Functionals computed on the Planck SMICA temperature map reveal statistically significant deviations from the Gaussian random‑field null hypothesis expected under standard inflation, thereby providing associational constraints on the presence of topological defects?*

## Methodology Overview
1. **Data Acquisition** – Retrieve the Planck 2015/2018 SMICA temperature map (Nside = 128) from the **Planck Legacy Archive** (`https://pla.esac.esa.int/pla/aio/product-action?product=COM_CMB_SMICA_2048_R3.00_full.fits`). Validate integrity via SHA‑256 checksum recorded in `data/manifest.yaml`.  
2. **Masking** – Apply the official Planck Galactic mask (`https://pla.esac.esa.int/pla/aio/product-action?product=COM_Mask_Galactic_2048_R3.00.fits`) with a 2‑pixel buffer. Enforce ≥95 % sky coverage; discard boundary pixels as specified in the edge‑case section.  
3. **Minkowski Functional Computation** – Compute area, perimeter, and genus at the five σ‑levels (‑1.0, ‑0.5, 0.0, +0.5, +1.0 σ) using the `pyminkowski` library (v0.1.2). Results are rounded to six decimal places.  
4. **Theoretical Power Spectrum** – Load the **theoretical** Planck 2015 TT angular power spectrum from `COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits` (`https://pla.esac.esa.int/pla/aio/product-action?product=COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits`). This spectrum is used for all Gaussian realizations, thereby avoiding circularity with the observed map.  
5. **Gaussian Simulations** – Generate 1 000 Gaussian random‑field realizations matching the theoretical spectrum, applying a 5′ Gaussian beam and adding white Gaussian noise of variance = 1.1 µK². Simulations are processed **in‑memory** in batches of 200 to stay within the 6.5 GB RAM limit; only functional values are persisted.  
6. **Covariance Estimation** – For each of the five thresholds, compute the empirical 3×3 covariance matrix of the three functionals across the simulation ensemble.  
7. **Statistical Comparison** – Conduct a multivariate Hotelling’s T² test (α = 0.05) comparing the observed functional vector to the simulation mean, accounting for the full covariance. P‑values are reported with ≥6 decimal precision.  
8. **Interpretation** – A statistically significant rejection indicates a deviation from Gaussianity. Results are reported **only as an associational constraint** on non‑Gaussian signatures; no quantitative Gμ bound is derived because the test does not isolate a specific defect model.

## Dataset Strategy
| Role | Dataset | Source (Verified) | Access Method | Notes |
|------|---------|-------------------|---------------|-------|
| Primary CMB map | Planck 2015/2018 SMICA temperature map (Nside = 128) | `https://pla.esac.esa.int/pla/aio/product-action?product=COM_CMB_SMICA_2048_R3.00_full.fits` | HTTP GET via `urllib.request` → saved to `data/raw/` | SHA‑256 checksum recorded; retry logic with exponential backoff (1 s, 2 s, 4 s). |
| Galactic mask | Planck official Galactic mask (Nside = 128) | `https://pla.esac.esa.int/pla/aio/product-action?product=COM_Mask_Galactic_2048_R3.00.fits` | Same download routine | Integrity checked; mask applied with 2‑pixel buffer. |
| Power spectrum | Theoretical Planck 2015 TT power spectrum (`COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits`) | `https://pla.esac.esa.int/pla/aio/product-action?product=COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits` | Load via `astropy.io.fits` | Used as input to `healpy.synfast`. |
| Gaussian simulations | Synthetic maps generated on‑the‑fly | No external source – produced by pipeline | `healpy.synfast` with beam & noise (in‑memory) | 1 000 realizations; no disk writes of intermediate maps. |

*No alternative datasets are used; any missing source would be flagged as a fatal mismatch.*

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not required; Hotelling’s T² inherently accounts for the three correlated functionals (Principle VI). |
| Power / sample‑size justification | 1 000 simulations follow standard cosmological practice (N ≈ 500–2 000) and provide stable covariance estimates; the pipeline aborts rather than reducing N, preserving statistical power. |
| Causal‑inference framing | The analysis is observational; results are presented as **associational constraints** on defect signatures, respecting Principle VI. |
| Measurement validity | Planck SMICA map and mask are the gold‑standard CMB products; beam and noise parameters are taken directly from Planck 2015 instrument papers (cited in this document). |
| Predictor collinearity | The three Minkowski Functionals are known to be correlated; the covariance matrix is explicitly used in the Hotelling test, satisfying the collinearity requirement. |

## Decision / Rationale for Compute‑Friendly Choices
- **Resolution (Nside = 128)** – Chosen per the specification; balances angular fidelity (≈2.9′ pixel) with memory constraints.  
- **Simulation Count** – 1 000 provides a well‑conditioned covariance; the pipeline monitors RAM and **fails** if the full set cannot be completed, ensuring compliance with the free‑tier limits and preserving statistical integrity.  
- **Hotelling’s T²** – Implemented via `scipy.stats` (no heavy external libraries).  
- **Parallelism** – Simulations are generated in batches using a `ProcessPoolExecutor` limited to 2 workers to respect the 2‑CPU limit.

## Expected Deliverables
- `data/processed/minkowski_observed.json` – observed functional values.  
- `data/processed/minkowski_sims.json` – simulated functional values (1 000 × 3 × 5 thresholds).  
- `data/processed/minkowski_covariance.npy` – covariance matrix per threshold.  
- `data/processed/hotelling_result.json` – T² statistic, p‑value, degrees of freedom.  
- `analysis_results.json` – JSON file conforming to `analysis_results.schema.yaml` containing all of the above plus metadata.  
- `report.md` – concise narrative with all numeric results, confidence intervals for non‑Gaussianity, and a PNG plot (`figures/mf_comparison.png`).  

---



## projects/PROJ-352-statistical-analysis-of-early-universe-c/specs/001-statistical-analysis-of-early-universe-c/data-model.md===
# Data Model: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Overview
The data model captures all persistent artifacts produced by the pipeline, enabling contract validation and reproducible downstream analysis.

## Entities

| Entity | Description | Primary Attributes | File Representation |
|--------|-------------|--------------------|---------------------|
| **CMBMap** | Raw Planck SMICA temperature map (Nside = 128). | `filename: str`, `nside: int = 128`, `checksum_sha256: str`, `pixel_count: int`, `frequency: str = "SMICA"` | `data/raw/planck_smica.fits` |
| **GalacticMask** | Binary mask (1 = good, 0 = masked). | `filename: str`, `nside: int = 128`, `coverage_fraction: float`, `checksum_sha256: str` | `data/raw/planck_mask.fits` |
| **MaskedCMBMap** | Result of applying `GalacticMask` to `CMBMap`. | `source_map: str`, `mask_file: str`, `valid_pixel_count: int`, `sky_fraction: float` | `data/processed/masked_smica.fits` |
| **MinkowskiFunctionalResult** | Functional values for a single map at a set of thresholds. | `map_id: str`, `thresholds: List[float]` (exact values: –1.0, –0.5, 0.0, +0.5, +1.0 σ), `area: List[float]`, `perimeter: List[float]`, `genus: List[float]`, `precision: int = 6` | JSON (`*_minkowski.json`) |
| **GaussianSimulation** | Synthetic CMB map generated from the *theoretical* Planck LCDM power spectrum. | `sim_id: int`, `seed: int`, `nside: int = 128`, `beam_fwhm_arcmin: float = 5.0`, `noise_variance: float = 1.1` µK², `checksum_sha256: str` (optional, if persisted) | *In‑memory only; functional results stored in `data/processed/minkowski_sims.json`* |
| **CovarianceMatrix** | Empirical covariance of the three functionals across simulations (per threshold). | `threshold: float`, `matrix: np.ndarray shape=(3,3)`, `method: "empirical"` | `data/processed/minkowski_covariance.npy` |
| **HotellingTestResult** | Outcome of the multivariate test. | `t_squared: float`, `p_value: float`, `df: int = 3`, `alpha: float = 0.05`, `significant: bool` | `data/processed/hotelling_result.json` |
| **ReportArtifact** | Human‑readable summary for the paper. | `title: str`, `date: str`, `summary: str`, `figures: List[str]` | `report.md`, `figures/*.png` |
| **AnalysisResults** | Consolidated JSON output for `analysis_results.schema.yaml`. | `observed_minkowski: List[MinkowskiFunctionalResult]`, `simulation_covariance: List[CovarianceMatrix]`, `hotelling_test: HotellingTestResult`, `runtime_summary: object`, `version: str`, `generated_at: str` | `analysis_results.json` |

## Relationships
- `MaskedCMBMap` **derives from** `CMBMap` + `GalacticMask`.  
- `MinkowskiFunctionalResult` **belongs to** either `MaskedCMBMap` (observed) or `GaussianSimulation` (simulated).  
- `CovarianceMatrix` **aggregates** all `MinkowskiFunctionalResult` rows for the simulated set.  
- `HotellingTestResult` **uses** the observed `MinkowskiFunctionalResult` and the `CovarianceMatrix`.  
- `AnalysisResults` **collects** all of the above into a single validated JSON artifact.

## Versioning & Checksums
All persisted files include a SHA‑256 checksum recorded in `data/manifest.yaml`. Any change to a file triggers a new hash entry, satisfying Constitution Principle III.

---



## projects/PROJ-352-statistical-analysis-of-early-universe-c/specs/001-statistical-analysis-of-early-universe-c/quickstart.md===
# Quickstart: Running the CMB Minkowski Functional Analysis

These instructions assume a fresh GitHub Actions runner or a local Linux/macOS environment with at least 2 CPU cores and 7 GB RAM.

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/early-universe-cmb-defect.git
cd early-universe-cmb-defect
```

## 2. Set Up a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Exact Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*All versions are pinned; no GPU libraries are installed.*

## 4. Run the Full Pipeline
```bash
python -m src.pipeline \
  --planck-url https://pla.esac.esa.int/pla/aio/product-action?product=COM_CMB_SMICA_2048_R3.00_full.fits \
  --mask-url   https://pla.esac.esa.int/pla/aio/product-action?product=COM_Mask_Galactic_2048_R3.00.fits \
  --pspec-url  https://pla.esac.esa.int/pla/aio/product-action?product=COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits \
  --nside 128 \
  --seed 42 \
  --sim-count 1000 \
  --thresholds "-1.0 -0.5 0.0 0.5 1.0"
```
The command will:
1. Download the SMICA map and mask (with retries).  
2. Apply the mask (2‑pixel buffer).  
3. Compute observed Minkowski Functionals using `pyminkowski`.  
4. Generate **exactly** 1 000 Gaussian simulations (no fallback).  
5. Compute functionals for each simulation **in‑memory**, estimate covariance, run Hotelling’s T² test, and write all artifacts in JSON format.

## 5. Inspect Results
```bash
# Basic summary
cat report.md

# View the Hotelling test JSON
jq '.' data/processed/hotelling_result.json

# Plot of observed vs. simulation MF curves (requires matplotlib)
python - <<'PY'
import matplotlib.pyplot as plt, json, pandas as pd
obs = pd.read_json('data/processed/minkowski_observed.json')
sims = pd.read_json('data/processed/minkowski_sims.json')
for thr in obs['threshold'].unique():
    plt.plot(obs[obs['threshold']==thr]['genus'], label=f'Obs {thr}')
    plt.plot(sims[sims['threshold']==thr]['genus'].mean(), label=f'Sim {thr}')
plt.legend()
plt.savefig('figures/mf_comparison.png')
PY
```

## 6. Run the Test Suite (optional)
```bash
pytest -v
```
All tests should pass, confirming checksum validation, reproducibility, and that acceptance criteria (coverage, precision, p‑value format) are met.

## 7. Resource Limits
The pipeline monitors RAM usage. **If RAM usage exceeds 6.5 GB or any phase exceeds its allocated wall‑time, the job aborts with a non‑zero exit code** and no partial results are written. This guarantees compliance with the GitHub Actions free‑tier specification (Principle VII) and preserves statistical integrity.
