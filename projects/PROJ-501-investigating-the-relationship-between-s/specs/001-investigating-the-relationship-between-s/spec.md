# Feature Specification: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

**Feature Branch**: `001-stellar-flare-atmospheric-retention`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention"

## User Scenarios & Testing

### User Story 1 - Retrieve and Filter Multi-Source Astrophysical Data (Priority: P1)

The researcher needs to automatically retrieve stellar flare event catalogs from MAST (TESS data) and exoplanet physical parameters from the NASA Exoplanet Archive, then filter this combined dataset to include only valid targets (M-dwarf hosts with ≥10 flare events) to establish the foundation for analysis.

**Why this priority**: Without a clean, filtered dataset linking specific flare histories to specific planetary parameters, no statistical analysis can be performed. This is the prerequisite for all subsequent modeling and correlation testing.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV contains exactly the expected columns (star ID, flare count, planet radius, planet mass, semi-major axis, host density) and that the row count matches the expected number of M-dwarf systems with sufficient flare history, without running any statistical models.

**Acceptance Scenarios**:

1. **Given** the MAST and NASA Exoplanet Archive APIs are accessible, **When** the script executes the retrieval and filtering logic, **Then** the output CSV contains only planets orbiting M-dwarf hosts with ≥10 recorded flare events, and all required physical parameters (radius, mass, semi-major axis, density) are populated with no null values.
2. **Given** a star in the TESS catalog has <10 flare events, **When** the filtering logic runs, **Then** that star and any associated planets are excluded from the final dataset.
3. **Given** the NASA Exoplanet Archive returns a planet with missing mass or radius data, **When** the script processes the record, **Then** that specific planet entry is excluded or flagged as invalid to prevent division-by-zero errors in the density calculation.

---

### User Story 2 - Compute Cumulative XUV Flux and Model Mass Loss (Priority: P2)

The researcher needs to calculate the cumulative high-energy (XUV) flux received by each filtered planet based on flare frequency and host luminosity (including quiescent emission), then apply the energy-limited escape model to derive an estimated atmospheric mass loss rate. This rate is integrated over the system's age to compute a "Retention Fraction" proxy, which serves as the dependent variable for the primary hypothesis test.

**Why this priority**: This transforms raw observational data into the specific physical quantities required to test the research hypothesis. The calculated mass loss rate is the **core driver** of the primary hypothesis test (US-3). The 'internal validation' mentioned in the acceptance criteria refers strictly to verifying the mathematical implementation of the escape formula against known synthetic values, ensuring the scientific output is accurate before it is used for the correlation test.

**Independent Test**: Can be fully tested by running the calculation module on a small, hardcoded subset of known values (e.g., a synthetic planet with defined flare rate, quiescent luminosity, and distance) and verifying the output matches the manually calculated mass loss rate and retention fraction using the standard energy-limited escape formula (with K_tide=1.0, f_XUV=0.1) within a 1% tolerance. This validation step is a prerequisite for the primary hypothesis test to ensure the derived Retention Fraction is physically meaningful.

**Acceptance Scenarios**:

1. **Given** a planet with known flare frequency, host star luminosity, quiescent XUV luminosity, and orbital distance, **When** the flux calculation module runs, **Then** the cumulative XUV flux (flare + quiescent) is computed and stored with units of erg/s/cm².
2. **Given** the cumulative XUV flux and planetary parameters, **When** the energy-limited escape model runs, **Then** the atmospheric mass loss rate (kg/s) is calculated using the standard efficiency factor (η = 0.15) and K_tide = 1.0, and stored.
3. **Given** a dataset with 100 planets, **When** the computation completes, **Then** the output CSV contains a new column `retention_fraction` (derived from time-integrated mass loss) with no NaN values for valid inputs.

---

### User Story 3 - Perform Statistical Correlation and Visualization (Priority: P3)

The researcher needs to perform a Spearman rank correlation test between cumulative flare flux and the modeled "Atmospheric Retention Fraction" (derived from density and age), determine statistical significance (p-value), and generate a scatter plot with a regression line to visualize the relationship.

**Why this priority**: This delivers the final scientific answer to the research question. It validates whether the observed data supports the theoretical hypothesis of a negative correlation between high-energy flux and atmospheric retention, using a physically meaningful proxy rather than static density alone.

**Independent Test**: Can be fully tested by running the analysis script on the generated dataset and verifying that the output includes a correlation coefficient (ρ) and p-value for the relationship between XUV flux and Retention Fraction, and that a PNG plot file is generated showing the data points and a trend line.

**Acceptance Scenarios**:

1. **Given** the final dataset with flux and Retention Fraction columns, **When** the statistical test runs, **Then** the Spearman rank correlation coefficient (ρ) and p-value are calculated and printed to the console and saved to a results JSON file.
2. **Given** the correlation results, **When** the visualization module runs, **Then** a scatter plot is generated with Cumulative XUV Flux on the X-axis and Retention Fraction on the Y-axis, including a regression line and axis labels.
3. **Given** the p-value is < 0.05, **When** the results are summarized, **Then** the output explicitly states "Significant negative correlation detected: High cumulative XUV flux is associated with lower atmospheric retention" if ρ < 0, or "Significant positive correlation detected: High cumulative XUV flux is associated with higher atmospheric retention" if ρ > 0.

### Edge Cases

- What happens if the MAST API returns no flare events for a known M-dwarf? (System must exclude the star to avoid division by zero in flux calculation).
- How does the system handle planets with extremely high eccentricity where the "semi-major axis" approximation for flux fails? (System must flag or exclude these to maintain model validity).
- What if the energy-limited model yields a mass loss rate exceeding 10% of the planet's total mass per Gyr? (System must flag the result as "unphysical" and exclude that data point from the statistical analysis to prevent skewing the correlation).
- How does the system handle API rate limits from NASA Exoplanet Archive during bulk retrieval? (System must implement a retry mechanism with exponential backoff, max 3 attempts).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve stellar flare catalogs from MAST and exoplanet parameters from the NASA Exoplanet Archive via API or `wget` and merge them by host star ID. (See US-1)
- **FR-002**: System MUST filter the merged dataset to include only systems where the host star is an M-dwarf and has ≥10 recorded flare events. (See US-1)
- **FR-003**: System MUST calculate cumulative XUV flux for each planet using the formula $F_{XUV} = F_{quiescent} + \sum (E_{flare} \times f_{XUV} / (4 \pi a^2))$, where $F_{quiescent}$ is the host star's quiescent XUV luminosity estimated using the **Wright et al. (2018) L_X/L_bol vs. Rotation Period relation** (or a fixed proxy of $10^{-4} L_{bol}$ if rotation is unknown), $E_{flare}$ is the bolometric flare energy in ergs, $f_{XUV}$ is a fixed conversion factor of 0.1, and $a$ is the semi-major axis in cm. The output MUST be in erg/s/cm². (See US-2)
- **FR-004**: System MUST estimate instantaneous atmospheric mass loss rates using the energy-limited escape model $\dot{M} = \frac{\epsilon \pi R_p^3 F_{XUV}}{G M_p K_{tide}}$ with a fixed efficiency $\epsilon = 0.15$, $K_{tide} = 1.0$, and $G$ as the gravitational constant. (See US-2)
- **FR-005**: System MUST calculate the "Atmospheric Retention Fraction" for each planet by integrating the mass loss rate over the system's age (estimated from host star rotation or isochrones) and computing $Retention = 1 - (\frac{\int \dot{M} dt}{M_{atm, initial}})$, where $M_{atm, initial}$ is defined as **[deferred] of the planetary mass ($0.01 \times M_p$)**, representing a standard terrestrial atmospheric baseline independent of the planet's measured bulk density. (See US-2)
- **FR-006**: System MUST perform a Spearman rank correlation test between cumulative XUV flux and the calculated Atmospheric Retention Fraction and report the coefficient (ρ) and p-value. (See US-3)
- **FR-007**: System MUST generate a scatter plot visualizing the relationship between flux and Atmospheric Retention Fraction with a regression line. (See US-3)
- **FR-008**: System MUST handle API rate limiting by implementing a retry mechanism with exponential backoff (max 3 attempts, initial delay 1s) before failing. (See US-1)
- **FR-009**: System MUST flag and exclude any data point where the calculated mass loss rate exceeds 10% of the planet's total mass per Gyr, marking it as "unphysical" in the output log. (See US-2)

### Key Entities

- **FlareEvent**: Represents a single stellar flare detection (attributes: star_id, timestamp, energy [erg], duration).
- **ExoplanetSystem**: Represents a planet orbiting a host star (attributes: planet_id, star_id, radius [cm], mass [g], semi_major_axis [cm], host_type, density [g/cm³], system_age [Gyr]).
- **AnalysisResult**: Represents the computed metrics for a single system (attributes: star_id, cumulative_flux, mass_loss_rate, retention_fraction, is_valid).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman rank correlation coefficient (ρ) and p-value between XUV flux and Atmospheric Retention Fraction are measured and reported. The methodological validity is measured against the requirement that the correlation uses a time-integrated retention proxy rather than static density alone. (See US-3)
- **SC-002**: The dataset completeness is measured against the requirement that every retained planet has non-null values for radius, mass, semi-major axis, flare count, and density. (See US-1)
- **SC-003**: The mass loss rate calculation accuracy is measured against a manual verification of the energy-limited escape formula using a synthetic test case (with K_tide=1.0, f_XUV=0.1) as a unit/integration validation step, distinct from the primary hypothesis test. (See US-2)
- **SC-004**: The algorithmic complexity of the data processing pipeline is measured against O(N log N) to ensure scalability for datasets up to 100,000 records. (See US-2, US-3)

### Methodological Soundness & Compute Feasibility

- **SC-005**: The analysis frames findings as **associational** only, explicitly avoiding causal language in the final report, as the design is observational (no random assignment). (See US-3)
- **SC-006**: The system MUST validate the presence of required columns (flare energy, star luminosity, planet radius, planet mass, semi-major axis, system age) in the raw API response. **If 'system_age' is missing, the system MUST assign a default value of 4.5 Gyr (median M-dwarf age) and log a warning. For any other missing required column, the system MUST exclude the affected record and log a warning with the specific missing variable name.** This ensures no records with incomplete physics data (other than age) enter the correlation analysis. (See US-1)
- **SC-007**: The analysis uses only CPU-tractable methods (Python `scipy`, `numpy`, `astropy`) without GPU acceleration, quantization, or large-model inference to ensure execution on 2 CPU cores / 7 GB RAM. (See US-2, US-3)
- **SC-008**: No multiple-comparison correction is required as the primary hypothesis is a single correlation test; if sub-group analyses are added, a family-wise error correction (e.g., Bonferroni) MUST be applied. (See US-3)
- **SC-009**: The correlation test (FR-006) must utilize the Atmospheric Retention Fraction (derived from a fixed [deferred] mass baseline) as the dependent variable to ensure the hypothesis test measures atmospheric erosion rather than static bulk composition. (See US-3)

## Assumptions

- The MAST archive and NASA Exoplanet Archive APIs will remain accessible and stable during the CI runtime window.
- The energy-limited escape model with a fixed efficiency factor ($\epsilon = 0.15$) and a fixed tidal efficiency factor ($K_{tide} = 1.0$) is a sufficient approximation for the initial empirical correlation study.
- The sample size of M-dwarf exoplanets with ≥10 recorded flares in the TESS catalog is sufficient (>30) to perform a meaningful Spearman correlation test.
- The "cumulative XUV flux" can be reasonably approximated by summing the bolometric energy of detected flares, applying a fixed conversion factor ($f_{XUV} = 0.1$), **and adding the quiescent XUV emission estimated using the Wright et al. (2018) L_X/L_bol relation.**
- The GitHub Actions runner provides at least 7 GB of RAM and 14 GB of disk space, and the entire dataset (flares + planets) fits within this memory footprint without requiring chunked processing.
- The efficiency factor $\epsilon = 0.15$ and tidal factor $K_{tide} = 1.0$ are treated as community-standard defaults for this initial study; sensitivity analysis on these parameters is out of scope for the initial correlation but noted as a future work.
- The initial atmosphere mass ($M_{atm, initial}$) is assumed to be a fixed fraction of the planet's total mass for all targets, providing a consistent baseline for calculating retention fractions independent of measured bulk density.