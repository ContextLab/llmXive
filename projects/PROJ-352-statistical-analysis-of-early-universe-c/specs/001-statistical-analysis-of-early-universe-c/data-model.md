# Data Model: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Overview
The data model captures all persistent artifacts produced by the pipeline, enabling contract validation and reproducible downstream analysis.

## Entities

| Entity | Description | Primary Attributes | File Representation |
|--------|-------------|--------------------|---------------------|
| **CMBMap** | Raw Planck SMICA temperature map (Nside = 128). | `filename: str`, `nside: int = 128`, `checksum_sha256: str`, `pixel_count: int`, `frequency: str = "SMICA"` | `data/raw/planck_smica.fits` |
| **GalacticMask** | Binary mask (1 = good, 0 = masked). | `filename: str`, `nside: int = 128`, `coverage_fraction: float`, `checksum_sha256: str` | `data/raw/planck_mask.fits` |
| **MaskedCMBMap** | Result of applying `GalacticMask` to `CMBMap`. | `source_map: str`, `mask_file: str`, `valid_pixel_count: int`, `sky_fraction: float` | `data/processed/masked_smica.fits` |
| **MinkowskiFunctionalResult** | Functional values for a single map at a set of thresholds. | `map_id: str`, `thresholds: List[float]` (exact values: –1.0, –0.5, 0.0, +0.5, +1.0 σ), `area: List[float]`, `perimeter: List[float]`, `genus: List[float]`, `precision: int = 6` | CSV (`*_minkowski.csv`) |
| **GaussianSimulation** | Synthetic CMB map generated from the *theoretical* Planck LCDM power spectrum. | `sim_id: int`, `seed: int`, `nside: int = 128`, `beam_fwhm_arcmin: float = 5.0`, `noise_variance: float = 1.1` µK², `checksum_sha256: str` | `data/processed/sims/sim_{sim_id}.fits` |
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

