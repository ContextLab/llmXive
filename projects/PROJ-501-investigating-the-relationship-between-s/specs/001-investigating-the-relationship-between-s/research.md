# Research: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

## 1. Dataset Strategy

This project relies on two primary data sources: stellar flare events and exoplanet physical parameters. The strategy involves programmatic retrieval from verified sources, followed by strict filtering to ensure dataset-variable fit.

### Verified Datasets

| Source | Description | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **MAST (TESS)** | Stellar flare event catalogs. | **Loader**: `astroquery.mast.Mast` with `collection='TESS'` and `service='flare'` (or specific dataset ID `tess_flare_catalog_v2` if available via MAST). **Note**: The provided "Verified datasets" block contains URLs to unrelated datasets. The implementation MUST use the specific MAST collection identifier for the TESS Stellar Flare Catalog. | **Action**: Use `astroquery.mast` to query the specific TESS Flare Catalog. If the specific collection is not directly accessible as a table, the plan will query the MAST service for 'TESS' objects and filter for 'Flare' event types, logging the exact query URI. |
| **NASA Exoplanet Archive** | Planetary physical parameters (radius, mass, semi-major axis, host type, age, rotation). | **Loader**: `astroquery.nasa_exoplanet_archive.NasaExoplanetArchive`. **Note**: The provided "Verified datasets" block contains URLs to unrelated datasets. The implementation MUST use the official NASA Exoplanet Archive API. | **Action**: Use `astroquery.nasa_exoplanet_archive` to query the 'planets' table. Explicitly request columns: `pl_name`, `pl_massj`, `pl_radj`, `pl_orbsmax`, `st_mass`, `st_rad`, `st_teff`, `st_age`, `st_rot`. |

**Dataset Variable Fit Analysis**:
- **Required Variables**: Star ID, Flare Energy, Flare Count, Host Luminosity ($L_{bol}$), Host Rotation (optional), Planet Radius ($R_p$), Planet Mass ($M_p$), Semi-major Axis ($a$), System Age, Host X-ray Luminosity ($L_X$).
- **MAST/TESS**: Contains Flare Energy, Star ID, Timestamp. May lack explicit Host Rotation or $L_X$.
- **NASA Exoplanet Archive**: Contains $R_p$, $M_p$, $a$, Host Type, $L_{bol}$ (derived). System Age and Rotation are often missing.
- **Fit Strategy**:
  - **Age**: If `st_age` is missing, attempt to derive from `st_rot` using gyrochronology. If both are missing, assign a default M-dwarf age (e.g., 5 Gyr) but flag the record as `age_uncertain=True`. These flagged records will be excluded from the primary time-integrated analysis but included in a sensitivity test.
  - **Quiescent XUV**: If direct $L_X$ is missing, use the Wright et al. (2018) relation with `st_rot`. If `st_rot` is also missing, use a fixed proxy ($10^{-4} L_{bol}$) but flag the record as `flux_uncertain=True`.
  - **Filtering**: Exclude records with missing $R_p$, $M_p$, or $a$. Include records with missing age/rotation only if they can be imputed or flagged for sensitivity analysis.

## 2. Methodological Approach

### 2.1 Data Ingestion & Filtering (FR-001, FR-002, FR-008)
- **Retrieval**:
  - **Flares**: Use `astroquery.mast` to query the specific TESS Flare Catalog. Filter for M-dwarf hosts.
  - **Planets**: Use `astroquery.nasa_exoplanet_archive` to query the 'planets' table for M-dwarf hosts.
- **Merging**: Join on `host_star_id` (TIC ID or HD ID).
- **Filtering**:
  - Host type == "M" (or spectral type M).
  - Flare count $\ge$ 10.
  - Exclude records with missing $R_p$, $M_p$, $a$.
  - Flag records with missing age or rotation for sensitivity analysis (see 2.2).
- **Rate Limiting**: Implement exponential backoff with a base interval and max 3 retries. Log all query parameters to `data/logs/` (schema in `contracts/api_log.schema.yaml`).

### 2.2 Physics Calculations (FR-003, FR-004, FR-005, FR-009)
- **Cumulative XUV Flux ($F_{XUV}$)**:
  - $F_{quiescent}$: Prioritize direct $L_X$ from archive. If missing, use Wright et al. (2018) relation with `st_rot`. If `st_rot` missing, use proxy $10^{-4} L_{bol}$ with `flux_uncertain=True` flag.
  - Flare Contribution: $\sum (E_{flare} \times 0.1 / (4 \pi a^2))$.
  - Units: erg/s/cm².
- **Mass Loss Rate ($\dot{M}$)**:
  - $\dot{M} = \frac{\epsilon \pi R_p^3 F_{XUV}}{G M_p K_{tide}}$ with $\epsilon=0.15$, $K_{tide}=1.0$.
  - **Validity Check**: If $\dot{M} \times 1 \text{ Gyr} > 0.1 M_p$, flag as "unphysical" and exclude from correlation (FR-009).
- **Atmospheric Erosion Index (AEI)**:
  - **New Metric**: Instead of 'Retention Fraction' (which depends on an assumed initial mass), calculate AEI.
  - $AEI = \frac{\int \dot{M} dt}{E_{binding}}$, where $E_{binding} \approx \frac{G M_p^2}{R_p}$.
  - **Rationale**: This normalizes the total mass lost by the planet's gravitational binding energy. A higher AEI indicates greater erosion relative to the planet's ability to hold its atmosphere, independent of an assumed initial atmosphere mass fraction.
  - **Time Integration**: $\int \dot{M} dt = \dot{M} \times \text{Age}$. If `age_uncertain=True`, use the default age but flag the AEI as `aei_uncertain=True`.

### 2.3 Statistical Analysis (FR-006, FR-010, SC-001, SC-005)
- **Primary Test**: **Residual-based Correlation**.
  - Step 1: Regress AEI against $M_p$ and $a$ (log-log scale) to remove the gravitational/distance baseline: $AEI_{resid} = AEI - \hat{AEI}(M_p, a)$.
  - Step 2: Perform Spearman rank correlation between $F_{XUV}$ and $AEI_{resid}$.
  - **Rationale**: This isolates the effect of flare flux on erosion *after* accounting for the planet's gravity and distance, avoiding the spurious correlation created by partial correlation on derived variables.
- **Associational Framing**: Explicitly state that the study is observational; no causal claims are made (SC-005).
- **Sensitivity Analysis**:
  - Re-run correlation excluding records with `age_uncertain=True`.
  - Re-run correlation excluding records with `flux_uncertain=True`.
  - Re-run correlation with different $\epsilon$ values (0.1, 0.15, 0.2) to test robustness.
- **Multiple Comparisons**: Not required for the single primary test (SC-008). If sub-group analyses are performed (e.g., by planetary class), Bonferroni correction will be applied.

## 3. Compute Feasibility
- **Hardware**: 2 CPU cores, 7 GB RAM.
- **Method**: Pure Python with `numpy`/`scipy`. No GPU. No deep learning.
- **Data Size**: The filtered dataset (M-dwarfs with $\ge$10 flares) is expected to be small (< 1000 rows), fitting easily in RAM.
- **Runtime**: Target < 60 seconds for processing and analysis.
- **Libraries**: `astropy` (constants), `scipy` (stats), `pandas` (dataframes), `requests` (API), `matplotlib` (plots), `astroquery`. All have CPU wheels.

## 4. Decision Rationale
- **Why AEI?** The 'Retention Fraction' metric was flawed because it depended on an assumed initial atmosphere mass (0.01 $M_p$), which varies by orders of magnitude across planet types. AEI normalizes by binding energy, making it a physically meaningful measure of erosion relative to planetary gravity.
- **Why Residual Correlation?** Partial correlation on variables that are algebraic components of the dependent variable creates a mathematical artifact. Regressing out the gravitational/distance baseline first isolates the specific effect of flare flux.
- **Why Age Imputation?** System age is often missing. Using a default value with a flag allows inclusion of more data while acknowledging the uncertainty. Records with high uncertainty are excluded from the primary analysis to ensure robustness.
- **Why Specific MAST Collection?** The generic API call was insufficient. The specific `collection='TESS'` and `service='flare'` (or dataset ID) ensures retrieval of the correct flare event data.